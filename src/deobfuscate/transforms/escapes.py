"""Escape notations: HTML entities, URL percent-escapes and backslash escapes."""

import html
import re
import urllib.parse
from collections.abc import Iterable

from deobfuscate.transforms.base import CHUNK, Candidate, Transform, is_readable

ENTITIES = re.compile(r"(?:&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});)+")
# Text that contains real HTML tags is source code, where entities are correct as
# written. Placeholders such as "<URL>" are not tags.
TAG = re.compile(
    r"</?(?:a|b|i|u|p|br|hr|div|span|img|html|head|body|title|meta|link|script|style|table|tr|td|th|ul|ol|li|"
    r"h[1-6]|em|strong|code|pre|form|input|button|label|select|option|iframe|svg|font|center|small|sup|sub)\b[^<>]*>",
    re.I,
)

PERCENT = re.compile(r"%[0-9A-Fa-f]{2}")
# A percent-escape joined to a letter or digit, as in "free%20prize".
PERCENT_IN_WORD = re.compile(r"[A-Za-z0-9]%[0-9A-Fa-f]{2}|%[0-9A-Fa-f]{2}[A-Za-z]")

BACKSLASH_RUN = re.compile(r"(?:\\x[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8}){3,}")
BACKSLASH = re.compile(r"\\x([0-9A-Fa-f]{2})|\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{8})")


class HtmlEntity(Transform):
    name = "html-entity"
    judged = False

    def propose(self, text: str) -> Iterable[Candidate]:
        if TAG.search(text):
            return
        for match in ENTITIES.finditer(text):
            decoded = html.unescape(match.group())
            if decoded != match.group() and is_readable(decoded):
                yield Candidate(match.start(), match.end(), decoded)


class UrlPercent(Transform):
    name = "url-percent"
    judged = False

    def propose(self, text: str) -> Iterable[Candidate]:
        for match in CHUNK.finditer(text):
            chunk = match.group()
            # One escape standing alone is more likely a mention ("a space becomes %20").
            if len(PERCENT.findall(chunk)) < 2 and not PERCENT_IN_WORD.search(chunk):
                continue
            try:
                decoded = urllib.parse.unquote(chunk, errors="strict")
            except UnicodeDecodeError:
                continue
            if decoded != chunk and is_readable(decoded):
                yield Candidate(match.start(), match.end(), decoded)


def decode_backslashes(run: str) -> str | None:
    hex_only = all(match.group(1) is not None for match in BACKSLASH.finditer(run))
    numbers = [int(next(group for group in match.groups() if group is not None), 16) for match in BACKSLASH.finditer(run)]
    try:
        if hex_only:
            # \\xNN usually spells out the bytes of UTF-8 text; failing that, one character each.
            try:
                return bytes(numbers).decode("utf-8")
            except UnicodeDecodeError:
                return bytes(numbers).decode("latin-1")
        # \\uD83D\\uDE00 is one character written as a surrogate pair.
        return "".join(map(chr, numbers)).encode("utf-16", "surrogatepass").decode("utf-16")
    except (ValueError, UnicodeError):
        return None


class BackslashEscape(Transform):
    """Runs of three or more escapes. Fewer is more likely code or a mention."""

    name = "backslash-escape"
    judged = False

    def propose(self, text: str) -> Iterable[Candidate]:
        for match in BACKSLASH_RUN.finditer(text):
            decoded = decode_backslashes(match.group())
            if decoded and is_readable(decoded):
                yield Candidate(match.start(), match.end(), decoded)
