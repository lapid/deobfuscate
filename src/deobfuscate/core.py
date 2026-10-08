from deobfuscate.types import Result

STRICTNESS_LEVELS = ("conservative", "balanced", "aggressive")


def deobfuscate(text: str, *, strictness: str = "conservative") -> Result:
    """Return ``text`` with obfuscation undone, plus the steps applied.

    No transforms are implemented yet, so the text is returned unchanged.
    """
    if strictness not in STRICTNESS_LEVELS:
        raise ValueError(f"strictness must be one of {STRICTNESS_LEVELS}, got {strictness!r}")
    return Result(text=text)
