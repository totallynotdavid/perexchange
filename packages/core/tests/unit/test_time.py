from datetime import UTC, datetime

from perexchange.time import PERU_TZ, parse_source_timestamp


def test_parse_source_timestamp_truncates_excess_fractional_digits():
    parsed = parse_source_timestamp("2025-11-18T22:14:18.8783083", datetime.now(UTC))

    assert parsed == datetime(2025, 11, 18, 22, 14, 18, 878308, tzinfo=UTC)


def test_parse_source_timestamp_normalizes_offsets_to_utc():
    parsed = parse_source_timestamp("2026-01-01T03:00:00-05:00", datetime.now(UTC))

    assert parsed == datetime(2026, 1, 1, 8, tzinfo=UTC)


def test_parse_source_timestamp_reads_naive_values_in_the_given_zone():
    parsed = parse_source_timestamp("2026-01-01T03:00:00", datetime.now(UTC), PERU_TZ)

    assert parsed == datetime(2026, 1, 1, 8, tzinfo=UTC)


def test_parse_source_timestamp_uses_fallback_for_invalid_data():
    fallback = datetime.now(UTC)

    assert parse_source_timestamp("not a timestamp", fallback) is fallback
