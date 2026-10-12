"""Leetspeak: digits and symbols standing for the letters they resemble ("fr33", "p@ssw0rd").

Decided one token at a time. A token is rewritten only when reading its digits and
symbols as letters gives a known English word. Shorthand that uses a digit for its
sound ("l8r", "b4", "2day", "4" for "for") is not leetspeak and has no such reading.
Short tokens and tokens shaped like a word with a number attached ("test5", "h1")
are rewritten only when the text shows the trick elsewhere.
"""

import re
from collections.abc import Iterable
from itertools import islice, product

from deobfuscate import resources, scorer
from deobfuscate.transforms.base import Candidate, Transform

# Only resemblances by shape. "8" and "2" are left out: they are used for their sound.
READINGS = {"0": "o", "1": "il", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"}
TOKEN = re.compile(r"(?<![\w@$.,])[A-Za-z0-9@$!]+(?:['’][A-Za-z]+)?(?![\w@$])")
# An amount of money, a number with a unit or an ending, a word or code with a number attached.
PRICE = re.compile(r"\$\d[\d.,]*(?:[kKmMbB]|bn|mm)?")
NUMBER_FIRST = re.compile(r"(\d+)([A-Za-z]+)")
NUMBER_LAST = re.compile(r"([A-Za-z]+)(\d+)")
UNITS = frozenset(
    "st nd rd th s am pm k m g h d x b bn kg km cm mm ml mg px ms hr hrs min mins sec gb mb kb tb hz mph up".split()
)
# Two small letters and a doubled "3" or "0", the commonest doubled letters: "fr33", "tr33".
DOUBLED_LAST = re.compile(r"[a-z]{2}(?:33|00)")
# "4" and "2" before a word are shorthand for "for" and "to" ("4my", "2go").
SOUND_FIRST = re.compile(r"[24]([A-Za-z]+)")
SENTENCE_START = re.compile(r"(?:^|[.!?]\s+|\n\s*)[\"'“‘(]?$")
MAX_READINGS = 32
# Words of evidence needed before a short or number-shaped token is rewritten,
# and before a token is rewritten whose reading is not a known word (a name).
EVIDENCE_FOR_WEAK = 1
EVIDENCE_FOR_UNKNOWN = 2
MIN_STRONG_LENGTH = 4


def read(token: str) -> tuple[str, bool] | None:
    """The token with digits and symbols read as letters, and whether that is a known word.

    None if some character has no reading as a letter.
    """
    options = [READINGS.get(char, char) if not char.isalpha() else char for char in token]
    if any(not choice[0].isalpha() and choice[0] not in "'’" for choice in options):
        return None
    letters = [char for char in token if char.isalpha()]
    upper = len(letters) >= 2 and all(char.isupper() for char in letters)
    for combo in islice(product(*options), MAX_READINGS):
        word = "".join(combo)
        if scorer.is_word(word):
            known = resources.words()
            if not token[0].isalpha() and word not in known and word.capitalize() in known:
                # Only known as a name: "@pril".
                word = word.capitalize()
            return (word.upper() if upper else word), True
    word = "".join(choice[0] for choice in options)
    return (word.upper() if upper else word), False


def is_weak(token: str) -> bool:
    """Too short, or shaped like something that is normally written with a number."""
    if len(token) == 3 and token[0].isalpha() and token[2].isalpha():
        # "y0u", "n0w": the digit sits inside the word.
        return False
    if len(token) < MIN_STRONG_LENGTH or not any(char.isalpha() for char in token):
        return True
    inside = token.strip("@$!")
    if inside.isalpha():
        # A symbol only at the edge: "@mark" is a handle, "print$" a share name.
        return True
    if DOUBLED_LAST.fullmatch(token):
        return False
    if match := NUMBER_LAST.fullmatch(token):
        return scorer.is_word(match.group(1))
    if match := NUMBER_FIRST.fullmatch(token):
        return len(match.group(2)) <= 2 or scorer.is_word(match.group(2))
    return False


class Leetspeak(Transform):
    name = "leetspeak"
    level = "balanced"
    # The decision is made here, word by word; the scorer has nothing to add for one word.
    judged = False

    def propose(self, text: str) -> Iterable[Candidate]:
        strong: list[Candidate] = []
        weak: list[Candidate] = []
        unknown: list[Candidate] = []
        for match in TOKEN.finditer(text):
            # A "!" at the end is punctuation.
            token = match.group().rstrip("!")
            start = match.start()
            if token.isalpha() or token.isdigit() or not token or PRICE.fullmatch(token):
                continue
            number_first = NUMBER_FIRST.fullmatch(token)
            if number_first and number_first.group(2).lower() in UNITS:
                continue
            number_last = NUMBER_LAST.fullmatch(token)
            if number_last and len(number_last.group(1)) <= 2 and not DOUBLED_LAST.fullmatch(token):
                # A model or a grade: "G5", "M14", "b4".
                continue
            sound_first = SOUND_FIRST.fullmatch(token)
            if sound_first and scorer.is_word(sound_first.group(1)):
                continue
            found = read(token)
            if found is None:
                continue
            plain, known = found
            if not token[0].isalpha() and SENTENCE_START.search(text[:start]):
                plain = plain[0].upper() + plain[1:]
            candidate = Candidate(start, start + len(token), plain)
            if is_weak(token):
                if known:
                    weak.append(candidate)
            elif known:
                strong.append(candidate)
            else:
                unknown.append(candidate)
        yield from strong
        if len(strong) >= EVIDENCE_FOR_WEAK:
            yield from weak
        if len(strong) >= EVIDENCE_FOR_UNKNOWN:
            yield from unknown
