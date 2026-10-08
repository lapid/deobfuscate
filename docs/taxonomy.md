# Obfuscation taxonomy

What the tool undoes, at which strictness level, and what it leaves alone. Names in the first
column are the `tricks` labels used in `data/samples/`. Reasons are in `docs/research/README.md`.

## In v1

| Trick | Example | Level | Risk and main guard |
|---|---|---|---|
| `zero-width` | `p​a​s​s` with invisible characters between letters | conservative | Low. Keep joiners inside emoji sequences and in non-Latin text |
| `styled-alphabet`, `fullwidth` | `𝐇𝐞𝐥𝐥𝐨`, `Ｈｅｌｌｏ` | conservative | Low. Leave lone symbols such as `²`, `½`, `µ` |
| `html-entity` | `Tom &amp; Jerry` | conservative | Low. Not inside text that is about HTML |
| `url-percent` | `free%20prize` | conservative | Low to medium. Not inside a URL |
| `backslash-escape` | `\x48\x65`, `\u0048` | conservative | Medium. Not file paths; not `\n` in prose |
| `base64`, `base64url` | `SGVsbG8gd29ybGQ=` | conservative | Medium. Result must be valid, printable, and score as English; tokens and keys do not |
| `hex`, `binary`, `decimal-codes` | `48 65 6c 6c 6f` | conservative | Medium. Hashes, UUIDs and colour codes decode to noise and are rejected |
| `rot13`, `caesar` | `Uryyb jbeyq` | conservative | Medium. Needs enough words; short real words can be rot13 pairs |
| `reverse` | `dlrow olleH` | conservative | Medium. Needs enough words; palindromes |
| `combining-marks` | `H̶e̶l̶l̶o̶` | balanced | Medium. Accents on real letters stay |
| `homoglyph` | `аccount` with a Cyrillic `а` | balanced | High. Only in mixed-script words, or when the result is a known word |
| `leetspeak` | `h3ll0`, `p@$$w0rd` | balanced | High. Result must be a known word; shorthand such as `l8r`, `sum1` is left alone |
| `separator` | `f r e e`, `c.l.i.c.k` | balanced | High. Initials, abbreviations, spaced headings |
| `repeated-chars` | `heeellooo` | aggressive | High. Emphasis is often intended; several valid collapses |

Stacked and partial cases are in scope for all of the above: several layers on one span, and an
obfuscated span inside clean text.

## Undecided

| Trick | Example | Question |
|---|---|---|
| `tag-characters` | Invisible Unicode tag characters carrying hidden text | Remove silently, or reveal the hidden text in the output or the record? |
| Wrong-encoding damage | `ú1.20` for `£1.20`, `Ã©` for `é` | In scope as "accidental mess", or left to tools built for it? Proposed: not in v1 |

## Out of scope

| Thing | Example | Why |
|---|---|---|
| Text-message shorthand | `l8r`, `sum1`, `4` for "for" | Abbreviation, not obfuscation; expanding it rewrites the author's words |
| Spelling mistakes and slang | `recieve`, `gonna` | Not obfuscation |
| Keyed ciphers | Vigenere, XOR | Needs key search; later |
| Code obfuscation | Minified or packed scripts | Different problem |
| Languages other than English | | Returned unchanged |
| Compression, encryption, file formats | gzip, PGP | Not text obfuscation |
