import re
from collections.abc import Iterable

from deobfuscate import scorer
from deobfuscate.transforms.base import Candidate, Transform
from deobfuscate.transforms.runs import chunks, foreign_runs, reads_as_english


# A long unbroken token may be another encoding written backwards; base64 padding then comes first.
ENCODED = re.compile(r"(?<![A-Za-z0-9+/=_-])={0,2}(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z0-9])[A-Za-z0-9+/_-]{16,}(?![A-Za-z0-9+/=_-])")


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
        if total and covered / total >= 0.6:
            yield Candidate(0, len(text), text[::-1])
        found = chunks(text)
        for first, last in foreign_runs(found):
            while first <= last and not reads_as_english(found[first].text[::-1]):
                first += 1
            while last >= first and not reads_as_english(found[last].text[::-1]):
                last -= 1
            if first > last:
                continue
            start, end = found[first].start, found[last].end
            span = text[start:end][::-1]
            covered, total = scorer.word_coverage(span)
            if total and covered / total >= 0.6:
                yield Candidate(start, end, span)
