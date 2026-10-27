"""Named errors of the streaming assistant."""

from __future__ import annotations


class ProviderError(RuntimeError):
    """The model provider failed (a server error or a dropped connection)."""


class RateLimitedError(RuntimeError):
    """The model provider answered 429."""


class RefusedError(RuntimeError):
    """The model declined to answer."""


class ReviewRejectedError(ValueError):
    """A reviewer's answer is not allowed (empty, ungrounded, or the run is not waiting)."""


class UnknownRunError(LookupError):
    """No run with this id."""
