"""Names of the obfuscation tricks and the strictness level that undoes each.

These names are the contract between the samples (``tricks``), the obfuscator,
and the deobfuscator's step record (``Step.transform``). See docs/taxonomy.md.
"""

LEVELS = ("conservative", "balanced", "aggressive")

TRICK_LEVEL = {
    "zero-width": "conservative",
    "tag-characters": "conservative",
    "styled-alphabet": "conservative",
    "fullwidth": "conservative",
    "html-entity": "conservative",
    "url-percent": "conservative",
    "backslash-escape": "conservative",
    "base64": "conservative",
    "base64url": "conservative",
    "hex": "conservative",
    "binary": "conservative",
    "decimal-codes": "conservative",
    "rot13": "conservative",
    "caesar": "conservative",
    "reverse": "conservative",
    "combining-marks": "balanced",
    "homoglyph": "balanced",
    "accent-substitution": "balanced",
    "leetspeak": "balanced",
    "separator": "balanced",
    "repeated-chars": "aggressive",
}

# Tricks that replace a span with an opaque token. In a partial sample they
# need a span long enough to be recognisable.
ENCODINGS = frozenset(
    {"html-entity", "url-percent", "backslash-escape", "base64", "base64url", "hex", "binary",
     "decimal-codes", "rot13", "caesar", "reverse"}
)


def in_scope(tricks: list[str], level: str) -> bool:
    """Whether a deobfuscator at ``level`` is expected to undo all of ``tricks``."""
    limit = LEVELS.index(level)
    return all(LEVELS.index(TRICK_LEVEL[trick]) <= limit for trick in tricks)


# Tricks the step record cannot tell apart, mapped to the name it reports.
RECORDED_AS = {"base64url": "base64"}
