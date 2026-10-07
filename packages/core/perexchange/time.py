import re

from datetime import datetime, timedelta, timezone, tzinfo


PERU_TZ = timezone(timedelta(hours=-5))

_TIMESTAMP = re.compile(r"^(.*?)(\.\d+)?(Z|[+-]\d\d:\d\d)?$")


def parse_source_timestamp(
    value: object, fallback: datetime, naive_tz: tzinfo = timezone.utc
) -> datetime:
    """Parse source timestamps across Python versions and use `fallback` on bad data.

    A timestamp without an offset is read in `naive_tz`.
    """
    if not isinstance(value, str) or not value:
        return fallback

    match = _TIMESTAMP.fullmatch(value)
    if match is None:
        return fallback
    prefix, fraction, suffix = match.groups()
    normalized = prefix
    if fraction:
        normalized += f".{fraction[1:7]}"
    if suffix == "Z":
        normalized += "+00:00"
    elif suffix:
        normalized += suffix

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return fallback
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=naive_tz)
    return parsed.astimezone(timezone.utc)
