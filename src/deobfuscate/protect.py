"""Finds spans that must be left alone: addresses, paths and identifiers.

Inside these, things that look like obfuscation are part of the format: a
percent escape belongs in a URL, a backslash sequence in a file path, a long
run of hex digits in a hash.
"""

import re

PATTERNS = (
    re.compile(r"\b(?:https?|ftp)://[^\s<>\"']+", re.I),
    re.compile(r"\bwww\.[^\s<>\"']+", re.I),
    re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"),
    re.compile(r"(?<![\w])(?:[A-Za-z]:\\|\\\\)[^\s\"<>|]+"),
    re.compile(r"(?<![\w])(?:~|\.{1,2})?/(?:[\w.+-]+/)+[\w.+-]*"),
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I),
    re.compile(r"(?<![0-9A-Za-z])(?:[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{56}|[0-9a-f]{64}|[0-9a-f]{96}|[0-9a-f]{128})(?![0-9A-Za-z])", re.I),
    # Not after "&": "&#115;" is an HTML entity, not a colour.
    re.compile(r"(?<![\w&])#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})\b", re.I),
)


def protected_spans(text: str) -> list[tuple[int, int]]:
    return sorted(match.span() for pattern in PATTERNS for match in pattern.finditer(text))


def overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < span_end and span_start < end for span_start, span_end in spans)
