from __future__ import annotations


class StopSendingException(Exception):
    """Raised in pre_send signal handlers to abort sending silently."""
