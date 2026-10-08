# Unicode confusables and mixed-script detection

- **Sources:** UTS #39 "Unicode Security Mechanisms", version 18.0.0, https://www.unicode.org/reports/tr39/ ;
  `confusables.txt`, https://www.unicode.org/Public/security/latest/confusables.txt
- **Read:** 2026-10-08. Verified. The table figures below were measured on the file in `data/reference/`.

## Key points

- `confusables.txt` maps a source character to a "prototype". Format per line:
  `source ; target ; MA # comment`. 6,712 entries in version 18.0.0.
- The **skeleton** of a string: decompose (NFD), drop default-ignorable characters, replace each
  character by its prototype, decompose again. Two strings are confusable when skeletons match.
- The standard says skeletons are for comparison only: not for display, not stable across
  versions, not a normalisation. It also says confusability "cannot be an exact science".
- **Mixed-script detection:** take each character's script set (Common and Inherited count as
  all scripts), intersect across the string. Empty intersection means mixed-script.
- The standard warns that whole-script and mixed-script checks flag many legitimate strings.

## Measured on the table

- 8 entries have an ASCII source: `` ` `` to `'`, `"` to `''`, `%`, `|` to `l`, `1` to `l`,
  `I` to `l`, `0` to `O`, `m` to `rn`.
- 2,262 entries go from a non-ASCII source to an all-ASCII target; 1,656 of those targets are
  letters only; 405 targets are longer than one character.
- NFKC produces the same result for 1,027 of the 2,262.

## What it changes for us

- Build our homoglyph map from the non-ASCII-to-ASCII subset. Never apply an ASCII-source entry.
- Because prototypes are arbitrary (`l` stands for `1`, `I`, `|`), a target of `l`, `I`, `O` or
  `rn` is a candidate set, not an answer. The scorer picks among `l`/`I`/`1` and `O`/`0`.
- Gate homoglyph replacement per word on mixed script. Whole-script lookalike words go through
  the scorer and only at `balanced` strictness or above.
- Vendoring is allowed: Unicode License V3 permits redistribution with the notice kept.
  See `data/reference/README.md`.

## Open

- Python's `unicodedata` has no script property. We need a script lookup: derive a small table
  from Unicode's `Scripts.txt`, or approximate from character names.
