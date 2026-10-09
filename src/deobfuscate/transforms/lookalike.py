"""Letters swapped for look-alikes: from other alphabets, or with accents added.

Both tricks are decided one word at a time. A word is rewritten when it is not
English as written and its plain-letter reading is, or when the rest of the
text shows the same trick clearly enough that a name or typo should follow suit.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import islice, product

from deobfuscate import resources, scorer
from deobfuscate.scripts import script_of
from deobfuscate.transforms.base import Candidate, Transform

# Letters of any alphabet, with apostrophes allowed inside.
WORD = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
LATIN_NAME = re.compile(
    r"LATIN (?:SMALL|CAPITAL) LETTER (?:SCRIPT )?([A-Z])(?: WITH .+)?$|LATIN LETTER SMALL CAPITAL ([A-Z])$"
)

# Look-alikes used in real phishing mail that Unicode's table does not list,
# because the resemblance is loose. Found in the dev half of the BitCore set.
LOOSE = {
    "τ": "t", "η": "n", "κ": "k", "ᴨ": "n", "ң": "h", "п": "n", "ʍ": "m", "β": "b", "ŉ": "n", "ҥ": "h", "к": "k",
    "ω": "w", "ĸ": "k", "Ƿ": "p", "щ": "w", "ᚱ": "r", "ժ": "d", "в": "b", "μ": "u", "н": "h", "Ի": "r", "қ": "k",
    "џ": "u", "Ա": "u", "м": "m", "т": "t", "г": "r", "ш": "w", "ρ": "p", "ν": "v", "χ": "x", "ε": "e", "σ": "o",
    "ᴦ": "r",
}
# Unicode files every upright stroke under "l". Which letter is meant depends on the word.
STROKES = frozenset("lIi")
MAX_READINGS = 32


def readings(char: str) -> tuple[list[str], str] | None:
    """Plain letters a character may stand for, and whether it is "accent" or "foreign".

    None if it has no plain reading.
    """
    base = unicodedata.normalize("NFD", char)[0]
    if base.isascii():
        found, kind = (base, "accent") if base.isalpha() else (None, "")
    else:
        strict = resources.lookalikes()
        found = strict.get(char) or strict.get(base) or LOOSE.get(char) or LOOSE.get(base)
        if found is None and (named := LATIN_NAME.match(unicodedata.name(base, ""))):
            found = (named.group(1) or named.group(2)).lower()
        if found == "rn":
            found = "m"
        kind = "accent" if script_of(base) == "Latin" else "foreign"
    if not found or len(found) != 1:
        # Ligatures such as "œ" are ordinary spelling, not a disguise.
        return None
    if found in STROKES:
        # Capitals are read as "I" first, small letters as "i" or "l" as listed.
        first = "I" if char.isupper() else found.lower()
        return [first, "i" if first == "l" else "l"], kind
    if char.isupper() and found.islower():
        found = found.upper()
    return [found], kind


@dataclass(frozen=True, slots=True)
class Reading:
    start: int
    end: int
    plain: str
    # The plain reading is a known English word.
    known: bool
    # The word contains letters of another alphabet / only accents on Latin letters.
    foreign: bool
    # Every letter is from another alphabet, so it could be a real foreign word.
    wholly_foreign: bool
    # Its accents are ones English and its neighbours do not use (as in "yōũr"),
    # sitting on plain letters. Such a word is suspicious on its own.
    odd_accents: bool


def read_word(match: re.Match) -> Reading | None:
    """The plain-letter reading of a word with non-ASCII letters, if it has one."""
    word = match.group()
    options: list[list[str]] = []
    kinds: set[str] = set()
    for char in word:
        if char.isascii():
            options.append([char])
            continue
        found = readings(char)
        if found is None:
            return None
        options.append(found[0])
        kinds.add(found[1])
    if not kinds:
        return None
    plain = "".join(choice[0] for choice in options)
    known = False
    for combo in islice(product(*options), MAX_READINGS):
        if scorer.is_word("".join(combo)):
            plain, known = "".join(combo), True
            break
    letters = [char for char in word if char.isalpha()]
    return Reading(
        match.start(), match.end(), plain, known, "foreign" in kinds,
        all(not char.isascii() and script_of(unicodedata.normalize("NFD", char)[0]) != "Latin" for char in letters),
        all(unicodedata.normalize("NFD", char)[0].isascii() for char in word) and any(ord(char) > 0xFF for char in word),
    )


def decide(text: str, loose: bool = False) -> list[tuple[Reading, str]]:
    """The words to rewrite, each with the name of the trick.

    ``loose`` also rewrites a lone word with everyday accents, and a lone "a" or "I"
    in another alphabet, when the plain reading is English. That catches more real
    disguises and also changes some correct foreign spellings.
    """
    plain_words: list[str] = []
    found: list[tuple[Reading, str]] = []
    unreadable_foreign = 0
    for match in WORD.finditer(text):
        word = match.group()
        if word.isascii():
            plain_words.append(word)
            continue
        if scorer.is_word(word):
            continue
        reading = read_word(match)
        if reading is None or (reading.wholly_foreign and not reading.known):
            if all(script_of(char) != "Latin" for char in word if char.isalpha()):
                unreadable_foreign += 1
        if reading is not None:
            found.append((reading, word))
    if not found:
        return []

    # The text must be English around the suspicious words, or have no plain words at all.
    multi = [word for word in plain_words if len(word) > 1]
    # The loose rules act on less evidence, so they ask for more English around it.
    needed = 0.7 if loose else 0.5
    english = sum(scorer.is_word(word) for word in multi)
    if multi and english < len(multi) * needed:
        return decide(text) if loose else []

    def strong(item: tuple[Reading, str]) -> bool:
        return item[0].known and len(item[1]) > 1

    # How clearly the text shows each trick: words that become English once read plainly.
    foreign_evidence = sum(strong(item) and item[0].foreign for item in found)
    odd_accent_evidence = sum(
        strong(item) and not item[0].foreign and item[0].odd_accents and item[1][0].islower() for item in found
    )
    evidence = foreign_evidence + odd_accent_evidence
    # A text in another language has words in its alphabet that have no English reading.
    another_language = unreadable_foreign >= max(1, foreign_evidence)

    out = []
    for reading, word in found:
        if reading.foreign:
            if reading.wholly_foreign and len(word) == 1:
                # "a" and "I" written in another alphabet; too little to act on alone.
                ok = reading.known and (foreign_evidence >= 1 or loose) and not another_language
            elif reading.wholly_foreign:
                ok = not another_language and (reading.known or foreign_evidence >= 2)
            else:
                ok = reading.known or foreign_evidence >= 1
            name = "homoglyph"
        else:
            if reading.known and reading.odd_accents:
                ok = word[0].islower() or evidence >= 1
            elif reading.known:
                # Everyday accents ("café", "à") and letters such as "ł" are normal
                # spelling unless the text shows the trick elsewhere.
                ok = evidence >= 1 and (len(word) > 1 or evidence >= 2)
                ok = ok or (loose and len(word) > 1 and word[0].islower())
            else:
                ok = evidence >= 3
            name = "accent-substitution"
        if ok and reading.plain != word:
            out.append((reading, name))
    return out


class Lookalike(Transform):
    # The decision is made here, word by word; the scorer has nothing to add for one word.
    judged = False

    def __init__(self, name: str, level: str = "balanced", loose: bool = False) -> None:
        self.name = name
        self.level = level
        self.loose = loose

    def propose(self, text: str) -> Iterable[Candidate]:
        if text.isascii():
            return
        for reading, name in decide(text, self.loose):
            if name == self.name:
                yield Candidate(reading.start, reading.end, reading.plain)
