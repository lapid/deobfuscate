import re
from collections.abc import Iterable
from dataclasses import dataclass

# A run of anything but whitespace. Invisible characters are not whitespace, so
# they stay attached to the word they were hidden in.
CHUNK = re.compile(r"\S+")


def is_readable(text: str) -> bool:
    """No control or invisible characters other than ordinary line breaks and tabs."""
    return all(char.isprintable() or char in "\n\r\t" for char in text)


@dataclass(frozen=True, slots=True)
class Candidate:
    """A proposal to replace ``text[start:end]`` with ``replacement``."""

    start: int
    end: int
    replacement: str
    hidden: str | None = None


class Transform:
    """Undoes one obfuscation trick.

    A transform only proposes. Whether a proposal is applied is decided by the
    engine, which checks that the result reads more like English than what was
    there before.
    """

    # The name recorded in ``Step.transform``; must be one from docs/taxonomy.md.
    name: str
    # The lowest strictness level at which the transform runs.
    level: str = "conservative"
    # False for transforms whose proposals are certain and need no plausibility check.
    judged: bool = True
    # True if proposals may touch spans the engine protects (URLs, paths, hashes).
    ignores_protection: bool = False
    # The fewest letters a result must contain to be judged, if more than the level asks for.
    min_letters: int = 0

    def propose(self, text: str) -> Iterable[Candidate]:
        raise NotImplementedError
