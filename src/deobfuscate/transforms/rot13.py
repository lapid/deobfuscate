import codecs
import re
from collections.abc import Iterable

from deobfuscate import scorer
from deobfuscate.transforms.base import Candidate, Transform

WORD = re.compile(r"[A-Za-z]+")
# A long unbroken token of letters and digits may be another encoding, rotated.
ENCODED = re.compile(
    r"(?<![A-Za-z0-9+/=_-])(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z0-9])[A-Za-z0-9+/_-]{16,}={0,2}(?![A-Za-z0-9+/=_-])"
)


def kind(word: str) -> str:
    """How a word reads before and after rotation.

    "rotated": English only after rotation. "plain": English only as it stands.
    "either": English both ways, like "be" and "or". "neither": a name or other
    unknown word, which says nothing.
    """
    now, then = scorer.is_word(word), scorer.is_word(codecs.encode(word, "rot13"))
    return "either" if now and then else "plain" if now else "rotated" if then else "neither"


class Rot13(Transform):
    name = "rot13"

    def propose(self, text: str) -> Iterable[Candidate]:
        for match in ENCODED.finditer(text):
            yield Candidate(match.start(), match.end(), codecs.encode(match.group(), "rot13"))

        words = [(match, kind(match.group())) for match in WORD.finditer(text)]
        kinds = {found for _, found in words}
        if "rotated" not in kinds:
            return
        if "plain" not in kinds:
            # Nothing reads as English as it stands, so the whole text is rotated,
            # names and punctuation included.
            yield Candidate(0, len(text), codecs.encode(text, "rot13"))
            return
        # Otherwise only runs of words between plain English are rotated. A run
        # starts and ends on a word that is English only after rotation.
        run: list[tuple[re.Match, str]] = []
        for match, found in [*words, (None, "plain")]:
            if found != "plain" and (run or found == "rotated"):
                run.append((match, found))
                continue
            while run and run[-1][1] != "rotated":
                run.pop()
            if run:
                start, end = run[0][0].start(), run[-1][0].end()
                yield Candidate(start, end, codecs.encode(text[start:end], "rot13"))
            run = []
