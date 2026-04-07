poetry run python ensure_db.py

poetry run alembic upgrade head

poetry run uvicorn app.main:app --reload

Default credentials:

Admin:
email: admin@example.com
password: admin12345
hashed_password: $2b$12$E8yWZJ3/1R4v91l/xgZObOm68Uk4KXVaPDLbxljSFKTYE6gND.96S

User:
email: user@example.com
password: user12345
hashed_password: $2b$12$z1Dm78Di/1kOPfM6titrCupzEZRH7NQlZ.z747HxwYAxjlgRtijBq
