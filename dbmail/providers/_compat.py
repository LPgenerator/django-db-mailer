"""Shared helpers for dbmail providers.

The module name is historical (``_compat``); it is **not** Python 2/3
compatibility code. Helpers live here so individual providers can be
patched, deprecated, or removed without breaking unrelated providers
that share a tiny utility (notably ``from_unicode``).

Public surface (stable across 3.x):

- :func:`from_unicode` — coerce text to ``str``, optionally
  truncate to a byte length. Originally lived in
  ``dbmail.providers.prowl.push``.
"""

from __future__ import annotations


def from_unicode(text: str | bytes | None, text_length: int | None = None) -> str:
    """Coerce ``text`` to ``str``, with optional UTF-8-byte truncation.

    Provider payloads are JSON / form-data — they require ``str``, not
    ``bytes``. ``text_length`` (when given) truncates by UTF-8 byte
    length to honour the per-API limits that prowl/smsbliss enforce.

    Args:
        text: ``str``, ``bytes`` or ``None``.
        text_length: optional truncation length, in UTF-8 bytes.

    Returns:
        ``str``. ``None`` becomes an empty string.
    """
    if text is None:
        return ""
    decoded = text.decode("utf-8") if isinstance(text, bytes) else text
    if text_length is None:
        return decoded
    encoded = decoded.encode("utf-8")[:text_length]
    return encoded.decode("utf-8", errors="ignore")
