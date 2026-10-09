"""The transforms the engine runs, in no particular order."""

from deobfuscate.transforms.base import Candidate, Transform
from deobfuscate.transforms.base64 import Base64
from deobfuscate.transforms.bytes import Binary, DecimalCodes, Hex
from deobfuscate.transforms.caesar import Caesar
from deobfuscate.transforms.escapes import BackslashEscape, HtmlEntity, UrlPercent
from deobfuscate.transforms.invisible import TagCharacters, ZeroWidth
from deobfuscate.transforms.lookalike import Lookalike
from deobfuscate.transforms.reverse import Reverse
from deobfuscate.transforms.styled import Fullwidth, StyledAlphabet

ALL: tuple[Transform, ...] = (
    ZeroWidth(),
    TagCharacters(),
    StyledAlphabet(),
    Fullwidth(),
    HtmlEntity(),
    UrlPercent(),
    BackslashEscape(),
    Lookalike("homoglyph"),
    Lookalike("accent-substitution"),
    Lookalike("homoglyph", level="aggressive", loose=True),
    Lookalike("accent-substitution", level="aggressive", loose=True),
    Base64(),
    Hex(),
    Binary(),
    DecimalCodes(),
    Caesar("rot13", (13,), encoded_tokens=True),
    Caesar("caesar", tuple(shift for shift in range(1, 26) if shift != 13)),
    Reverse(),
)

__all__ = ["ALL", "Candidate", "Transform"]
