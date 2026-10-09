import re
from collections.abc import Iterable

from deobfuscate import scorer
from deobfuscate.transforms.base import Candidate, Transform
from deobfuscate.transforms.runs import chunks, foreign_runs, reads_as_english

# A long unbroken token of letters and digits may be another encoding, rotated.
ENCODED = re.compile(
    r"(?<![A-Za-z0-9+/=_-])(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z0-9])[A-Za-z0-9+/_-]{16,}={0,2}(?![A-Za-z0-9+/=_-])"
)
LOWER = "abcdefghijklmnopqrstuvwxyz"


def table(shift: int) -> dict[int, int]:
    """Translation table that moves each letter ``shift`` places back through the alphabet."""
    moved = LOWER[-shift:] + LOWER[:-shift]
    return str.maketrans(LOWER + LOWER.upper(), moved + moved.upper())


class Caesar(Transform):
    """Letters shifted along the alphabet. Rot13 is the shift by 13."""

    # A short unknown word can turn into an English word under some shift by chance.
    min_letters = 10

    def __init__(self, name: str, shifts: tuple[int, ...], encoded_tokens: bool = False) -> None:
        self.name = name
        self.tables = [table(shift) for shift in shifts]
        self.encoded_tokens = encoded_tokens

    def propose(self, text: str) -> Iterable[Candidate]:
        if self.encoded_tokens:
            for match in ENCODED.finditer(text):
                yield Candidate(match.start(), match.end(), match.group().translate(self.tables[0]))

        found = chunks(text)
        runs = foreign_runs(found)
        if not runs:
            return
        # When most of the text is not English, the whole of it may be shifted,
        # including stray words that happen to read as English either way.
        foreign = sum(found[i].letters for first, last in runs for i in range(first, last + 1))
        mostly_foreign = foreign * 2 >= sum(chunk.letters for chunk in found)
        for moved in self.tables:
            if mostly_foreign:
                whole = text.translate(moved)
                covered, total = scorer.word_coverage(whole)
                if total and covered / total >= 0.6:
                    yield Candidate(0, len(text), whole)
            english = [reads_as_english(chunk.text.translate(moved)) for chunk in found]
            # Shifted text can contain words that are also English as they stand
            # ("or" for "be"). Join runs that have only such words between them.
            joined: list[list[int]] = []
            for first, last in runs:
                if joined and all(english[i] or not found[i].letters for i in range(joined[-1][1] + 1, first)):
                    joined[-1][1] = last
                else:
                    joined.append([first, last])
            for first, last in joined:
                # Names stay unknown under any shift, so they cannot mark where a run ends.
                while first <= last and not english[first]:
                    first += 1
                while last >= first and not english[last]:
                    last -= 1
                if first > last:
                    continue
                outside = [i for i in range(len(found)) if (i < first or i > last) and found[i].letters]
                if all(english[i] or not found[i].plain for i in outside):
                    # Everything else fits the same shift: the whole text was shifted.
                    start, end = 0, len(text)
                else:
                    start, end = found[first].start, found[last].end
                span = text[start:end].translate(moved)
                covered, total = scorer.word_coverage(span)
                if total and covered / total >= 0.6:
                    yield Candidate(start, end, span)
