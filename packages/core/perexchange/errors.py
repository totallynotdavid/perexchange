__all__ = [
    "ConfigurationError",
    "PerexchangeError",
    "SourceError",
    "SourceParseError",
]


class PerexchangeError(Exception):
    """Base class for errors raised by perexchange."""


class SourceError(PerexchangeError):
    """An expected failure while fetching one source."""


class SourceParseError(SourceError):
    """A source response did not match the parser's contract."""


class ConfigurationError(PerexchangeError, ValueError):
    """The fetch settings are invalid."""
