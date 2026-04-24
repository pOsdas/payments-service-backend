from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
async def send_payment_webhook(
    webhook_url: str,
    payload: dict[str, Any],
) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            webhook_url,
            json=payload,
        )

        response.raise_for_status()