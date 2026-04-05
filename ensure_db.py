import asyncio
import logging
import os
import re
import sys
import urllib.parse
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

RETRY_COUNT = int(os.environ.get("DB_CREATE_RETRIES", 10))
RETRY_DELAY = float(os.environ.get("DB_CREATE_RETRY_DELAY", 2))
ALLOW_DB_CREATE = os.environ.get("ALLOW_DB_CREATE", "1")
POSTGRES_MAINTENANCE_DB = os.environ.get("POSTGRES_MAINTENANCE_DB", "postgres")


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")
    return url


def normalize_database_url_for_asyncpg(url: str) -> dict:
    if not url.startswith("postgresql+asyncpg://"):
        raise RuntimeError(
            "DATABASE_URL must start with 'postgresql+asyncpg://'"
        )

    parsed = urllib.parse.urlparse(url)

    username = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    db_name = parsed.path.lstrip("/")

    if not db_name:
        raise RuntimeError("Database name is missing in DATABASE_URL")

    if not re.fullmatch(r"[A-Za-z0-9_]+", db_name):
        raise RuntimeError(
            f"Invalid database name '{db_name}'. "
            "Only letters, digits and underscore are allowed"
        )

    return {
        "user": username,
        "password": password,
        "host": host,
        "port": port,
        "db_name": db_name,
    }


async def ensure_db_exists(db_url_info: dict) -> bool:
    user = db_url_info["user"]
    password = db_url_info["password"]
    host = db_url_info["host"]
    port = db_url_info["port"]
    db_name = db_url_info["db_name"]

    for attempt in range(1, RETRY_COUNT + 1):
        conn = None
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=POSTGRES_MAINTENANCE_DB,
            )

            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1;",
                db_name,
            )

            if exists:
                logger.info("[ensure_db] Database '%s' already exists.", db_name)
                return False

            if ALLOW_DB_CREATE != "1":
                raise RuntimeError(
                    f"Database '{db_name}' does not exist and ALLOW_DB_CREATE != 1. "
                    "Set ALLOW_DB_CREATE=1 for local/dev/docker usage."
                )

            logger.info("[ensure_db] Creating database '%s'...", db_name)
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            logger.info("[ensure_db] Database '%s' created successfully.", db_name)
            return True

        except asyncpg.DuplicateDatabaseError:
            logger.warning(
                "[ensure_db] Database '%s' was created by another process.",
                db_name,
            )
            return False

        except (
            asyncpg.CannotConnectNowError,
            asyncpg.PostgresConnectionError,
            ConnectionError,
            OSError,
        ) as exc:
            logger.warning(
                "[ensure_db] PostgreSQL is not ready yet "
                "(attempt %s/%s): %s",
                attempt,
                RETRY_COUNT,
                exc,
            )
            if attempt < RETRY_COUNT:
                await asyncio.sleep(RETRY_DELAY)
                continue
            raise

        except Exception as exc:
            logger.warning(
                "[ensure_db] Failed to ensure database on attempt %s/%s: %s",
                attempt,
                RETRY_COUNT,
                exc,
            )
            if attempt < RETRY_COUNT:
                await asyncio.sleep(RETRY_DELAY)
                continue
            raise

        finally:
            if conn is not None:
                await conn.close()

    raise RuntimeError("Could not connect to PostgreSQL to create database.")


async def wait_until_target_db_ready(db_url_info: dict) -> None:
    user = db_url_info["user"]
    password = db_url_info["password"]
    host = db_url_info["host"]
    port = db_url_info["port"]
    db_name = db_url_info["db_name"]

    for attempt in range(1, RETRY_COUNT + 1):
        conn = None
        try:
            conn = await asyncpg.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database=db_name,
            )
            await conn.execute("SELECT 1;")
            logger.info("[ensure_db] Target database '%s' is ready.", db_name)
            return

        except Exception as exc:
            logger.warning(
                "[ensure_db] Target DB is not ready "
                "(attempt %s/%s): %s",
                attempt,
                RETRY_COUNT,
                exc,
            )
            if attempt < RETRY_COUNT:
                await asyncio.sleep(RETRY_DELAY)
                continue
            raise

        finally:
            if conn is not None:
                await conn.close()

    raise RuntimeError(f"Target database '{db_name}' is not available.")


async def run_migrations() -> None:
    logger.info("[ensure_db] Running Alembic migrations...")

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "alembic",
        "upgrade",
        "head",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(Path(__file__).resolve().parent),
    )

    stdout, stderr = await process.communicate()

    if stdout:
        logger.info(stdout.decode().strip())

    if stderr:
        stderr_text = stderr.decode().strip()
        if process.returncode == 0:
            logger.info(stderr_text)
        else:
            logger.error(stderr_text)

    if process.returncode != 0:
        raise RuntimeError(
            f"Alembic migrations failed with exit code {process.returncode}."
        )

    logger.info("[ensure_db] Alembic migrations finished successfully.")


async def main() -> None:
    db_url = get_database_url()
    db_url_info = normalize_database_url_for_asyncpg(db_url)

    created = await ensure_db_exists(db_url_info)

    if created:
        logger.info(
            "[ensure_db] Database '%s' was created and will now be migrated.",
            db_url_info["db_name"],
        )

    await wait_until_target_db_ready(db_url_info)
    await run_migrations()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        logger.error("[ensure_db] Error: %s", exc)
        sys.exit(1)