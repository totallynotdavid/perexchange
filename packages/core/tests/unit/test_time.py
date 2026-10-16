from datetime import UTC, datetime

import pytest

from perexchange.time import PERU_TZ, parse_source_timestamp


@pytest.mark.parametrize(
    ("value", "zone", "expected"),
    [
        (
            "2025-11-18T22:14:18.8783083",
            UTC,
            datetime(2025, 11, 18, 22, 14, 18, 878308, tzinfo=UTC),
        ),
        ("2026-01-01T03:00:00-05:00", UTC, datetime(2026, 1, 1, 8, tzinfo=UTC)),
        ("2026-01-01T03:00:00", PERU_TZ, datetime(2026, 1, 1, 8, tzinfo=UTC)),
    ],
    ids=["excess fractional digits", "offset", "naive value in a zone"],
)
def test_parse_source_timestamp_returns_utc(value, zone, expected):
    assert parse_source_timestamp(value, datetime.now(UTC), zone) == expected


def test_parse_source_timestamp_uses_fallback_for_invalid_data():
    fallback = datetime.now(UTC)

    assert parse_source_timestamp("not a timestamp", fallback) is fallback
