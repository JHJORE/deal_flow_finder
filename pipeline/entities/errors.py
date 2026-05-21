"""Domain errors.

Every external-library exception caught by an adapter is converted into one of
these. Use cases catch only ``DomainError`` and below — never an ``httpx`` or
``firecrawl`` exception. This is how the dependency rule survives contact with
real APIs.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error that crosses an adapter boundary."""


class ValidationError(DomainError):
    """A value object or entity rejected its inputs."""


class FetchError(DomainError):
    """Network or remote-service failure while fetching a resource."""


class ParseError(DomainError):
    """A remote response was reachable but could not be parsed into a domain type."""


class RateLimitError(FetchError):
    """The remote service signalled a rate limit. Caller may back off and retry later."""


class NotFoundError(DomainError):
    """The requested resource does not exist upstream. Distinct from a fetch failure."""
