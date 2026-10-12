import re
from collections.abc import Iterable

from deobfuscate import scorer
from deobfuscate.transforms.base import Candidate, Transform
from deobfuscate.transforms.runs import chunks, foreign_runs, reads_as_english


# A long unbroken token may be another encoding written backwards; base64 padding then comes first.
ENCODED = re.compile(r"(?<![A-Za-z0-9+/=_-])={0,2}(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z0-9])[A-Za-z0-9+/_-]{16,}(?![A-Za-z0-9+/=_-])")


# How many words that read both ways may sit between two parts of one reversed run.
MAX_GAP = 2
# A run joined across such words rests on less, so it must be longer. With ten letters,
# two misspelt words around "is" ("waht is rael") read as English backwards by chance.
MIN_JOINED_LETTERS = 12


class Reverse(Transform):
    """Text written backwards, as a whole or for a run of words."""

    name = "reverse"
    # A short unknown word can read as English backwards by chance.
    min_letters = 10

    def propose(self, text: str) -> Iterable[Candidate]:
        for match in ENCODED.finditer(text):
            yield Candidate(match.start(), match.end(), match.group()[::-1])
        # Reversed text still contains the odd word that reads as English ("saw", "no"),
        # so the whole text is always tried; the engine keeps it only if it reads better.
        covered, total = scorer.word_coverage(text[::-1])
        whole = bool(total) and covered / total >= 0.6
        if whole:
            yield Candidate(0, len(text), text[::-1])
        found = chunks(text)
        runs = foreign_runs(found)
        # "no", "was" and "I" are words in both directions, and cut a reversed run in two.
        # The run across them is tried as well, unless the whole text may be reversed:
        # a run of nearly all of it would then win and leave the words at the ends behind.
        joined: list[tuple[int, int]] = []
        for first, last in [] if whole else runs:
            if joined and first - joined[-1][1] - 1 <= MAX_GAP and all(
                reads_as_english(chunk.text[::-1]) for chunk in found[joined[-1][1] + 1 : first]
            ):
                joined[-1] = (joined[-1][0], last)
            else:
                joined.append((first, last))
        for first, last in [*runs, *(run for run in joined if run not in runs)]:
            # A word that is English as it stands may sit inside the run, not at its ends.
            while first <= last and (found[first].plain or not reads_as_english(found[first].text[::-1])):
                first += 1
            while last >= first and (found[last].plain or not reads_as_english(found[last].text[::-1])):
                last -= 1
            if first > last:
                continue
            start, end = found[first].start, found[last].end
            span = text[start:end][::-1]
            if (first, last) not in runs and any(chunk.plain for chunk in found[first : last + 1]):
                if scorer.letter_count(span) < MIN_JOINED_LETTERS:
                    continue
            covered, total = scorer.word_coverage(span)
            if total and covered / total >= 0.6:
                yield Candidate(start, end, span)
