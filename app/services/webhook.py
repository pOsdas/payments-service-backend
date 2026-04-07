import hashlib
from decimal import Decimal


def format_amount_for_signature(amount: Decimal) -> str:
    normalized = amount.normalize()
    as_string = format(normalized, "f")

    if "." in as_string:
        as_string = as_string.rstrip("0").rstrip(".")
        if not as_string:
            as_string = "0"

    return as_string


def build_webhook_signature(
    account_id: int,
    amount: Decimal,
    transaction_id: str,
    user_id: int,
    secret_key: str,
) -> str:
    amount_str = format_amount_for_signature(amount)
    raw = f"{account_id}{amount_str}{transaction_id}{user_id}{secret_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_valid_webhook_signature(
    account_id: int,
    amount: Decimal,
    transaction_id: str,
    user_id: int,
    secret_key: str,
    signature: str,
) -> bool:
    expected_signature = build_webhook_signature(
        account_id=account_id,
        amount=amount,
        transaction_id=transaction_id,
        user_id=user_id,
        secret_key=secret_key,
    )
    return expected_signature == signature
