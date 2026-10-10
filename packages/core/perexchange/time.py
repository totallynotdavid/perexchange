from datetime import UTC, datetime, timedelta, timezone, tzinfo


PERU_TZ = timezone(timedelta(hours=-5))


def parse_source_timestamp(
    value: object, fallback: datetime, naive_tz: tzinfo = UTC
) -> datetime:
    """Parse an ISO 8601 source timestamp and use `fallback` on bad data.

    A timestamp without an offset is read in `naive_tz`.
    """
    if not isinstance(value, str) or not value:
        return fallback

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return fallback
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=naive_tz)
    return parsed.astimezone(UTC)
