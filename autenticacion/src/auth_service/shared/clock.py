from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time (patchable in tests via freezegun)."""
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    """Attach UTC tzinfo to a naive datetime (SQLite drops tzinfo on round-trip)."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
