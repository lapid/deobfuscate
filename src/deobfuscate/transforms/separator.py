"""Separators put between the letters of a word: "f r e e", "c.l.i.c.k", "f-r-e-e".

Decided one run at a time. Letters are joined only when they then spell known
English words. Initials and abbreviations ("J. R. R.", "U.S.A", "W.H.O") do not:
they are either not words, or known only in capitals, and are left alone.
"""

import re
from collections.abc import Iterable

from deobfuscate import resources, scorer
from deobfuscate.transforms.base import Candidate, Transform

SYMBOLS = ".-_*,"
SYMBOL_RUNS = tuple(
    re.compile(rf"(?<![\w{re.escape(symbol)}])[A-Za-z](?:{re.escape(symbol)}[A-Za-z]){{2,}}(?!\w)(?!{re.escape(symbol)}\w)")
    for symbol in SYMBOLS
)
SPACED_RUN = re.compile(r"(?<![\w'’.])(?:[A-Za-z] ){3,}[A-Za-z](?![\w'’])")
# A whole text written one character at a time, with wider gaps between the words.
SPACED_TEXT = re.compile(r"\S(?: \S)*(?: {2,}\S(?: \S)*)+")
ONE_LETTER_WORDS = frozenset("aI")
MIN_WORD = 3
MIN_COVERAGE = 0.5
MIN_GROUPS = 3
# Runs rewritten outright that a run must have beside it when its letters are not a
# known word (a name). "_" and "*" are not used between letters in ordinary writing.
EVIDENCE_FOR_NAME = {"_": 1, "*": 1, ".": 2, "-": 2, ",": 2}


def is_plain_word(word: str) -> bool:
    """A known word that is not only an abbreviation: "free" and "John", not "USA"."""
    known = resources.words()
    return len(word) >= MIN_WORD and (word.lower() in known or (not word.isupper() and word.capitalize() in known))


def split_words(letters: str) -> list[str] | None:
    """The fewest known words the letters spell in order, or None.

    A run can hold several words ("f r e e g i f t"), or begin or end with an
    ordinary one-letter word ("a f r e e").
    """
    best: list[list[str] | None] = [[]] + [None] * len(letters)
    for end in range(1, len(letters) + 1):
        for start in range(end):
            before = best[start]
            piece = letters[start:end]
            if before is None or not (is_plain_word(piece) or piece in ONE_LETTER_WORDS):
                continue
            if best[end] is None or len(before) + 1 < len(best[end]):
                best[end] = before + [piece]
    words = best[-1]
    if words is None or all(len(word) == 1 for word in words):
        return None
    return words


class Separator(Transform):
    name = "separator"
    level = "balanced"
    # The decision is made here, run by run; the scorer has nothing to add for one word.
    judged = False

    def propose(self, text: str) -> Iterable[Candidate]:
        whole = SPACED_TEXT.fullmatch(text.strip())
        # Spaced-out capitals are how headings are set ("C H A P T E R   O N E").
        if whole and not text.isupper():
            groups = re.split(r" {2,}", text.strip())
            joined = " ".join(group.replace(" ", "") for group in groups)
            covered, total = scorer.word_coverage(joined)
            if len(groups) >= MIN_GROUPS and total and covered >= total * MIN_COVERAGE:
                start = len(text) - len(text.lstrip())
                yield Candidate(start, start + len(text.strip()), joined)
                return
        strong: list[Candidate] = []
        weak: list[Candidate] = []
        names: list[tuple[int, Candidate]] = []
        for symbol, pattern in zip(SYMBOLS, SYMBOL_RUNS):
            for match in pattern.finditer(text):
                word = match.group()[::2]
                candidate = Candidate(match.start(), match.end(), word)
                if not is_plain_word(word):
                    if len(word) > MIN_WORD and not word.isupper():
                        names.append((EVIDENCE_FOR_NAME[symbol], candidate))
                elif word.isupper() or (symbol == "." and text[match.end() : match.end() + 1] == "."):
                    # Abbreviations are written in capitals, or with a dot after every letter ("a.k.a.").
                    weak.append(candidate)
                else:
                    strong.append(candidate)
        for match in SPACED_RUN.finditer(text):
            letters = match.group()[::2]
            words = split_words(letters)
            if words is not None:
                (weak if letters.isupper() else strong).append(Candidate(match.start(), match.end(), " ".join(words)))
        yield from strong
        if strong:
            yield from weak
        yield from (candidate for needed, candidate in names if len(strong) >= needed)
