import asyncio
import logging
import math

from collections.abc import Sequence
from dataclasses import dataclass

import httpx

from perexchange.errors import ConfigurationError, SourceError
from perexchange.models import ExchangeRate, FetchReport, SourceFailure
from perexchange.scrapers.registry import Source, get_sources, source_for_name
from perexchange.transport import get_http_client


logger = logging.getLogger("perexchange")

__all__ = ["fetch_rates", "fetch_rates_report"]


async def fetch_rates(
    sources: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_attempts: int = 3,
    total_timeout: float | None = 30.0,
    client: httpx.AsyncClient | None = None,
) -> list[ExchangeRate]:
    """Fetch rates and omit sources that fail.

    Use `fetch_rates_report()` when callers need source failure details.
    """
    report = await fetch_rates_report(
        sources,
        timeout=timeout,
        max_attempts=max_attempts,
        total_timeout=total_timeout,
        client=client,
    )
    return list(report.rates)


async def fetch_rates_report(
    sources: Sequence[str] | None = None,
    *,
    timeout: float = 10.0,
    max_attempts: int = 3,
    total_timeout: float | None = 30.0,
    client: httpx.AsyncClient | None = None,
) -> FetchReport:
    """Fetch rates and report expected failures by source.

    `timeout` applies to each HTTP request. `total_timeout` limits the complete
    operation for each source, including retries and backoff. A passed client stays
    open; a client created here is closed before returning.
    """
    timeout, max_attempts, total_timeout = _validate_settings(
        timeout, max_attempts, total_timeout
    )
    selected_sources = get_sources(sources)

    if client is not None:
        results = await _fetch_all(
            selected_sources, client, timeout, max_attempts, total_timeout
        )
    else:
        async with get_http_client() as owned_client:
            results = await _fetch_all(
                selected_sources, owned_client, timeout, max_attempts, total_timeout
            )

    all_rates = [rate for result in results for rate in result.rates]
    aggregator_sources = {
        source.id for source in selected_sources if source.is_aggregator
    }
    rates = _deduplicate_rates(all_rates, aggregator_sources)
    failures = tuple(result.failure for result in results if result.failure is not None)
    return FetchReport(rates=tuple(rates), failures=failures)


def _validate_settings(
    timeout: object, max_attempts: object, total_timeout: object
) -> tuple[float, int, float | None]:
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        msg = "timeout must be a positive finite number"
        raise ConfigurationError(msg)
    if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
        msg = "max_attempts must be an integer"
        raise ConfigurationError(msg)
    if max_attempts < 1:
        msg = "max_attempts must be at least 1"
        raise ConfigurationError(msg)
    if total_timeout is None:
        return float(timeout), int(max_attempts), None
    if (
        isinstance(total_timeout, bool)
        or not isinstance(total_timeout, (int, float))
        or not math.isfinite(total_timeout)
        or total_timeout <= 0
    ):
        msg = "total_timeout must be a positive finite number or None"
        raise ConfigurationError(msg)
    return float(timeout), int(max_attempts), float(total_timeout)


@dataclass(frozen=True, slots=True)
class _SourceResult:
    rates: list[ExchangeRate]
    failure: SourceFailure | None


async def _fetch_all(
    sources: list[Source],
    client: httpx.AsyncClient,
    timeout: float,
    max_attempts: int,
    total_timeout: float | None,
) -> list[_SourceResult]:
    tasks = [
        _safe_fetch(source, client, timeout, max_attempts, total_timeout)
        for source in sources
    ]
    return list(await asyncio.gather(*tasks))


async def _safe_fetch(
    source: Source,
    client: httpx.AsyncClient,
    timeout: float,
    max_attempts: int,
    total_timeout: float | None,
) -> _SourceResult:
    try:
        operation = source.fetcher(client, timeout=timeout, max_attempts=max_attempts)
        if total_timeout is not None:
            rates = await asyncio.wait_for(operation, timeout=total_timeout)
        else:
            rates = await operation
        _validate_source_rates(source, rates)
        return _SourceResult(rates=rates, failure=None)
    except (
        httpx.HTTPError,
        SourceError,
        TimeoutError,
        asyncio.TimeoutError,
    ) as error:
        logger.warning("source %s failed: %s", source.id, error)
        return _SourceResult(
            rates=[],
            failure=SourceFailure(
                source=source.id,
                error_type=type(error).__name__,
                message=_failure_message(error, total_timeout),
            ),
        )


def _validate_source_rates(source: Source, rates: list[ExchangeRate]) -> None:
    if any(rate.source != source.id for rate in rates):
        msg = f"source {source.id} returned a rate with the wrong source ID"
        raise SourceError(msg)


def _failure_message(error: Exception, total_timeout: float | None) -> str:
    message = str(error)
    if message:
        return message
    if isinstance(error, (TimeoutError, asyncio.TimeoutError)) and total_timeout:
        return f"source exceeded total timeout of {total_timeout:g} seconds"
    return type(error).__name__


def _deduplicate_rates(
    rates: list[ExchangeRate], aggregator_sources: set[str]
) -> list[ExchangeRate]:
    seen: set[tuple[str, str]] = set()
    unique: list[ExchangeRate] = []
    for rate in rates:
        if rate.source in aggregator_sources and _is_covered_source(rate.name):
            continue
        key = (rate.source, rate.name)
        if key not in seen:
            seen.add(key)
            unique.append(rate)
    return unique


def _is_covered_source(name: str) -> bool:
    return source_for_name(name) is not None
