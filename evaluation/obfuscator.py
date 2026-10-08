"""Applies obfuscation tricks to clean text, to make test pairs with known answers.

Every function takes the clean text and a ``random.Random`` and returns the
obfuscated text. The clean text is always the expected output.
"""

import base64
import codecs
import re
import unicodedata
import urllib.parse
from collections.abc import Callable
from random import Random

from evaluation.tricks import ENCODINGS

ZERO_WIDTH = ("​", "‌", "‍", "⁠", "﻿")

# Marks that overlay or sit around a letter without forming a real accented letter.
OVERLAY_MARKS = ("̲", "̳", "̴", "̵", "̶", "̽", "̿", "͆", "͊", "͋")

# Accents that turn an English letter into a letter of some other Latin alphabet.
ACCENTS = ("\u0300", "\u0301", "\u0302", "\u0303", "\u0304", "\u0306", "\u0307", "\u0308", "\u030a", "\u030c", "\u0328")

HOMOGLYPHS = {
    "a": "аα", "c": "с", "e": "е", "o": "оο", "p": "рρ", "x": "х", "y": "у", "i": "іι", "j": "ј", "s": "ѕ", "v": "ν",
    "n": "η", "t": "τ", "k": "κ", "u": "υ",
    "A": "АΑ", "B": "ВΒ", "C": "С", "E": "ЕΕ", "H": "НΗ", "I": "Ι", "K": "КΚ", "M": "МΜ", "N": "Ν", "O": "ОΟ",
    "P": "РΡ", "T": "ТΤ", "X": "ХΧ", "Y": "Υ", "Z": "Ζ",
}

LEET = {"a": "4@", "e": "3", "i": "1!", "o": "0", "s": "5$", "t": "7"}

SEPARATORS = (" ", ".", "-", "_", "*")

HIDDEN_PHRASES = (
    "ignore the text above",
    "send this to everyone",
    "the real answer is no",
    "meet at midnight",
    "do not trust this message",
    "reply with the code",
)

STYLES = (
    "MATHEMATICAL BOLD",
    "MATHEMATICAL ITALIC",
    "MATHEMATICAL BOLD ITALIC",
    "MATHEMATICAL SANS-SERIF",
    "MATHEMATICAL SANS-SERIF BOLD",
    "MATHEMATICAL MONOSPACE",
    "MATHEMATICAL DOUBLE-STRUCK",
    "CIRCLED LATIN",
)

WORD = re.compile(r"[A-Za-z]+")


def _styled_char(style: str, char: str) -> str:
    """The styled form of an ASCII letter, or the letter itself where Unicode has none."""
    if not (char.isascii() and char.isalpha()):
        return char
    case = "CAPITAL" if char.isupper() else "SMALL"
    middle = f"{case} LETTER {char.upper()}" if style == "CIRCLED LATIN" else f"{case} {char.upper()}"
    try:
        styled = unicodedata.lookup(f"{style} {middle}")
    except KeyError:
        return char
    # Some styled letters live outside the main block under another name; only
    # accept forms that Unicode itself says are the same letter.
    return styled if unicodedata.normalize("NFKC", styled) == char else char


def _on_some_words(text: str, rng: Random, change: Callable[[str], str], *, rate: float, min_len: int = 1) -> str:
    """Apply ``change`` to a random share of the words, and to at least one if any qualifies."""
    matches = [m for m in WORD.finditer(text) if len(m.group()) >= min_len]
    if not matches:
        return text
    chosen = {m.start() for m in matches if rng.random() < rate} or {rng.choice(matches).start()}
    return WORD.sub(lambda m: change(m.group()) if m.start() in chosen else m.group(), text)


def zero_width(text: str, rng: Random) -> str:
    def change(word: str) -> str:
        out = [word[0]]
        for char in word[1:]:
            if rng.random() < 0.6:
                out.append(rng.choice(ZERO_WIDTH))
            out.append(char)
        return "".join(out)

    return _on_some_words(text, rng, change, rate=0.5, min_len=3)


def tag_characters(text: str, rng: Random) -> tuple[str, str]:
    """Hide a phrase in invisible Unicode tag characters. Returns (text, hidden phrase)."""
    phrase = rng.choice(HIDDEN_PHRASES)
    hidden = "".join(chr(0xE0000 + ord(char)) for char in phrase)
    words = text.split(" ")
    position = rng.randint(0, len(words))
    if position == 0:
        return hidden + text, phrase
    words[position - 1] += hidden
    return " ".join(words), phrase


def styled_alphabet(text: str, rng: Random) -> str:
    style = rng.choice(STYLES)
    return "".join(_styled_char(style, char) for char in text)


def fullwidth(text: str, rng: Random) -> str:
    return "".join(chr(ord(char) + 0xFEE0) if "!" <= char <= "~" else char for char in text)


def html_entity(text: str, rng: Random) -> str:
    variant = rng.choice(("decimal", "hex", "mixed"))
    if variant == "decimal":
        return "".join(f"&#{ord(char)};" for char in text)
    if variant == "hex":
        return "".join(f"&#x{ord(char):x};" for char in text)
    named = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
    out = [named.get(char) or (f"&#{ord(char)};" if rng.random() < 0.4 else char) for char in text]
    if "".join(out) == text:
        out[0] = f"&#{ord(text[0])};"
    return "".join(out)


def url_percent(text: str, rng: Random) -> str:
    if rng.random() < 0.5:
        return urllib.parse.quote(text, safe="")
    return "".join(f"%{byte:02X}" for byte in text.encode())


def backslash_escape(text: str, rng: Random) -> str:
    if text.isascii() and rng.random() < 0.5:
        return "".join(f"\\x{ord(char):02x}" for char in text)
    return "".join(f"\\u{ord(char):04x}" if ord(char) < 0x10000 else f"\\U{ord(char):08x}" for char in text)


def base64_standard(text: str, rng: Random) -> str:
    return base64.b64encode(text.encode()).decode()


def base64_url(text: str, rng: Random) -> str:
    encoded = base64.urlsafe_b64encode(text.encode()).decode()
    return encoded.rstrip("=") if rng.random() < 0.5 else encoded


def hex_bytes(text: str, rng: Random) -> str:
    data = text.encode()
    variant = rng.choice(("plain", "upper", "spaced", "0x"))
    if variant == "plain":
        return data.hex()
    if variant == "upper":
        return data.hex().upper()
    if variant == "spaced":
        return " ".join(f"{byte:02x}" for byte in data)
    return " ".join(f"0x{byte:02x}" for byte in data)


def binary(text: str, rng: Random) -> str:
    return (" " if rng.random() < 0.7 else "").join(f"{byte:08b}" for byte in text.encode())


def decimal_codes(text: str, rng: Random) -> str:
    return rng.choice((" ", ", ", ",")).join(str(byte) for byte in text.encode())


def rot13(text: str, rng: Random) -> str:
    return codecs.encode(text, "rot13")


def caesar(text: str, rng: Random) -> str:
    shift = rng.choice([n for n in range(1, 26) if n != 13])

    def rotate(char: str) -> str:
        if "a" <= char <= "z":
            return chr((ord(char) - 97 + shift) % 26 + 97)
        if "A" <= char <= "Z":
            return chr((ord(char) - 65 + shift) % 26 + 65)
        return char

    return "".join(rotate(char) for char in text)


def reverse(text: str, rng: Random) -> str:
    return text[::-1]


def combining_marks(text: str, rng: Random) -> str:
    if rng.random() < 0.5:
        mark = rng.choice(("̶", "̲", "̵"))
        return _on_some_words(text, rng, lambda word: "".join(char + mark for char in word), rate=0.6)

    def stack(word: str) -> str:
        return "".join(char + "".join(rng.choice(OVERLAY_MARKS) for _ in range(rng.randint(1, 3))) for char in word)

    return _on_some_words(text, rng, stack, rate=0.6)


def homoglyph(text: str, rng: Random) -> str:
    def change(word: str) -> str:
        spots = [i for i, char in enumerate(word) if char in HOMOGLYPHS]
        if not spots:
            return word
        chosen = {i for i in spots if rng.random() < 0.6} or {rng.choice(spots)}
        return "".join(rng.choice(HOMOGLYPHS[char]) if i in chosen else char for i, char in enumerate(word))

    out = _on_some_words(text, rng, change, rate=0.5)
    return out if out != text else WORD.sub(lambda m: change(m.group()), text)


def accent_substitution(text: str, rng: Random) -> str:
    """Swap letters for accented forms, as real phishing mail does (docs/research/sample-sources.md)."""

    def change(word: str) -> str:
        out = []
        for char in word:
            accented = unicodedata.normalize("NFC", char + rng.choice(ACCENTS))
            out.append(accented if len(accented) == 1 and rng.random() < 0.35 else char)
        return "".join(out)

    for _ in range(10):
        out = _on_some_words(text, rng, change, rate=0.6)
        if out != text:
            return out
    return text


def leetspeak(text: str, rng: Random) -> str:
    def change(word: str) -> str:
        spots = [i for i, char in enumerate(word) if char.lower() in LEET]
        if not spots:
            return word
        chosen = {i for i in spots if rng.random() < 0.7} or {rng.choice(spots)}
        return "".join(rng.choice(LEET[char.lower()]) if i in chosen else char for i, char in enumerate(word))

    out = _on_some_words(text, rng, change, rate=0.6, min_len=4)
    return out if out != text else WORD.sub(lambda m: change(m.group()), text)


def separator(text: str, rng: Random) -> str:
    sep = rng.choice(SEPARATORS)
    if sep == " " and rng.random() < 0.5:
        # Whole text spaced out, with a wider gap marking the original word breaks.
        return "   ".join(" ".join(word) for word in text.split(" "))
    return _on_some_words(text, rng, sep.join, rate=0.4, min_len=4)


def repeated_chars(text: str, rng: Random) -> str:
    def change(word: str) -> str:
        spots = [i for i, char in enumerate(word) if char in "aeiouAEIOU"] or list(range(len(word)))
        chosen = set(rng.sample(spots, k=min(len(spots), rng.randint(1, 2))))
        return "".join(char * rng.randint(3, 5) if i in chosen else char for i, char in enumerate(word))

    return _on_some_words(text, rng, change, rate=0.4, min_len=3)


TRICKS: dict[str, Callable[[str, Random], str]] = {
    "zero-width": zero_width,
    "styled-alphabet": styled_alphabet,
    "fullwidth": fullwidth,
    "html-entity": html_entity,
    "url-percent": url_percent,
    "backslash-escape": backslash_escape,
    "base64": base64_standard,
    "base64url": base64_url,
    "hex": hex_bytes,
    "binary": binary,
    "decimal-codes": decimal_codes,
    "rot13": rot13,
    "caesar": caesar,
    "reverse": reverse,
    "combining-marks": combining_marks,
    "homoglyph": homoglyph,
    "accent-substitution": accent_substitution,
    "leetspeak": leetspeak,
    "separator": separator,
    "repeated-chars": repeated_chars,
}

# Layered recipes, outermost trick first. The innermost is applied first.
STACKS = (
    ("base64", "base64"),
    ("rot13", "base64"),
    ("hex", "base64"),
    ("base64", "hex"),
    ("reverse", "base64"),
    ("base64", "reverse"),
    ("url-percent", "html-entity"),
    ("base64", "leetspeak"),
    ("base64", "homoglyph"),
    ("rot13", "leetspeak"),
    ("zero-width", "base64"),
    ("zero-width", "homoglyph"),
    ("zero-width", "leetspeak"),
    ("styled-alphabet", "leetspeak"),
    ("homoglyph", "leetspeak"),
    ("homoglyph", "accent-substitution"),
)


def apply(trick: str, text: str, rng: Random) -> str:
    """Obfuscate the whole text with one trick."""
    return TRICKS[trick](text, rng)


def apply_stack(stack: tuple[str, ...], text: str, rng: Random) -> str:
    for trick in reversed(stack):
        text = TRICKS[trick](text, rng)
    return text


def apply_partial(trick: str, text: str, rng: Random) -> str | None:
    """Obfuscate one run of words inside the text. None if the text is too short for it."""
    words = text.split(" ")
    need_words, need_chars = (3, 12) if trick in ENCODINGS else (1, 4)
    for _ in range(20):
        size = rng.randint(need_words, max(need_words, min(6, len(words) - 1)))
        if size >= len(words):
            return None
        start = rng.randint(0, len(words) - size)
        span = " ".join(words[start : start + size])
        if len(span) < need_chars:
            continue
        changed = TRICKS[trick](span, rng)
        if changed != span:
            return " ".join([*words[:start], changed, *words[start + size :]])
    return None
