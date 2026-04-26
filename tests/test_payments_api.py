from uuid import UUID, uuid4
import pytest
from httpx import ASGITransport, AsyncClient
# from sqlalchemy import select

from app.main import app
# from app.core.models import OutboxEvent
# from app.core.models import Payment


API_KEY = "super-secret-test-api-key"


@pytest.mark.asyncio
async def test_create_payment_success() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/payments",
            headers={
                "X-API-Key": API_KEY,
                "Idempotency-Key": "test-create-payment-success",
            },
            json={
                "amount": "1500.50",
                "currency": "RUB",
                "description": "Test payment",
                "metadata": {
                    "order_id": "test-order-1",
                },
                "webhook_url": "https://webhook.site/test",
            },
        )

    assert response.status_code == 202

    data = response.json()

    assert UUID(data["payment_id"])
    assert data["status"] == "pending"
    assert data["created_at"] is not None


@pytest.mark.asyncio
async def test_create_payment_requires_api_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/payments",
            headers={
                "Idempotency-Key": "test-without-api-key",
            },
            json={
                "amount": "100.00",
                "currency": "RUB",
                "description": "No api key",
                "metadata": {},
                "webhook_url": "https://webhook.site/test",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payment_requires_idempotency_key() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/payments",
            headers={
                "X-API-Key": API_KEY,
            },
            json={
                "amount": "100.00",
                "currency": "RUB",
                "description": "No idempotency key",
                "metadata": {},
                "webhook_url": "https://webhook.site/test",
            },
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_payment_idempotency() -> None:
    idempotency_key = f"test-idempotency-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first_response = await client.post(
            "/api/v1/payments",
            headers={
                "X-API-Key": API_KEY,
                "Idempotency-Key": idempotency_key,
            },
            json={
                "amount": "100.00",
                "currency": "RUB",
                "description": "First request",
                "metadata": {
                    "order_id": "first",
                },
                "webhook_url": "https://webhook.site/test",
            },
        )

        second_response = await client.post(
            "/api/v1/payments",
            headers={
                "X-API-Key": API_KEY,
                "Idempotency-Key": idempotency_key,
            },
            json={
                "amount": "999.00",
                "currency": "USD",
                "description": "Second request should not create new payment",
                "metadata": {
                    "order_id": "second",
                },
                "webhook_url": "https://webhook.site/another",
            },
        )

    assert first_response.status_code == 202
    assert second_response.status_code == 202

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data["payment_id"] == second_data["payment_id"]
    assert first_data["status"] == second_data["status"]


@pytest.mark.asyncio
async def test_get_payment_success() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/payments",
            headers={
                "X-API-Key": API_KEY,
                "Idempotency-Key": "test-get-payment-success",
            },
            json={
                "amount": "250.00",
                "currency": "EUR",
                "description": "Payment for get test",
                "metadata": {
                    "order_id": "get-test",
                },
                "webhook_url": "https://webhook.site/test",
            },
        )

        payment_id = create_response.json()["payment_id"]

        get_response = await client.get(
            f"/api/v1/payments/{payment_id}",
            headers={
                "X-API-Key": API_KEY,
            },
        )

    assert get_response.status_code == 200

    data = get_response.json()

    assert data["id"] == payment_id
    assert data["amount"] == "250.00"
    assert data["currency"] == "EUR"
    assert data["description"] == "Payment for get test"
    assert data["status"] == "pending"
    assert data["idempotency_key"] == "test-get-payment-success"


@pytest.mark.asyncio
async def test_get_payment_not_found() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/payments/00000000-0000-0000-0000-000000000000",
            headers={
                "X-API-Key": API_KEY,
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"