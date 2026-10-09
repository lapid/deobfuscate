# Architecture

How the deobfuscator works inside. Read this before adding or changing a transform.

## The pieces

| Module | Job |
|---|---|
| `core.py` | The public `deobfuscate()` function. Contains errors unless `raise_errors=True` |
| `engine.py` | Runs transforms, judges their proposals, records steps. Holds the limits and the strictness presets |
| `transforms/` | One class per trick. A transform only proposes replacements |
| `scorer.py` | How much a text looks like English, from 0 to 1 |
| `protect.py` | Finds spans to leave alone: URLs, emails, file paths, UUIDs, hashes, colour codes |
| `scripts.py` | Which writing system a character belongs to, and whether a word mixes several |
| `resources.py` | Loads the data files in `data/` on first use |
| `types.py` | `Result` and `Step` |

## How a text is processed

1. Every enabled transform looks at the text and proposes candidates: "replace characters
   `start` to `end` with this".
2. A candidate that overlaps a protected span is dropped, unless its transform opts out.
3. **Certain transforms go first.** Transforms marked `judged = False` (invisible characters,
   styled letters, escapes) are applied until none has anything left to propose. Only then are
   the judged transforms asked. Otherwise an invisible character inside a word would split it
   and mislead the transforms that read words.
4. For a judged candidate, the engine deobfuscates the replacement **itself**, by running the
   whole process on it one layer deeper. This is what handles layers: base64 inside base64, or
   base64 inside rot13. The candidate is judged by what it finally turns into.
5. The engine judges: the final text must have enough letters, score high enough as English,
   and beat the text it replaces by a margin.
6. Among accepted candidates, the one with the largest **gain times number of letters** is
   applied. Weighting by size makes a rewrite of the whole text win over the same rewrite of a
   part of it. Its step is recorded, followed by the steps found inside it, with their positions
   shifted to where the replacement now sits.
7. Repeat from 1 until no candidate is accepted.

Because every accepted judged step must raise the score, the loop cannot go round in circles,
and a second run over the output finds nothing more to do.

## Strictness

A level does two things: it enables the transforms whose `level` is at or below it, and it
picks a `Policy` in `engine.py`:

| Level | Minimum score | Minimum gain | Minimum letters |
|---|---|---|---|
| conservative | 0.50 | 0.30 | 10 |
| balanced | 0.45 | 0.25 | 6 |
| aggressive | 0.40 | 0.15 | 4 |

A transform can ask for more letters than the level does (`min_letters`); Caesar shifts and
reversal require 10 at every level, because a short unknown word can become an English word
under some shift by chance. One-letter words never count as letters of evidence.

The values were set while building the transforms and still need a proper tuning pass.

## Transforms

| Transform | File | Judged | Notes |
|---|---|---|---|
| `zero-width` | `invisible.py` | no | Keeps joiners next to emoji and non-Latin letters |
| `tag-characters` | `invisible.py` | no | Removes hidden text and reports it in `Step.hidden`; works inside URLs too |
| `styled-alphabet` | `styled.py` | no | Needs two styled letters in a run; one alone is a maths variable |
| `fullwidth` | `styled.py` | no | Needs a fullwidth letter or digit; skipped in East Asian text |
| `html-entity` | `escapes.py` | no | Skipped when the text contains real HTML tags |
| `url-percent` | `escapes.py` | no | Needs two escapes in a word, or one joined to a letter |
| `backslash-escape` | `escapes.py` | no | Needs three escapes in a row |
| `base64` | `base64.py` | yes | Both alphabets; reported as `base64` |
| `hex`, `binary`, `decimal-codes` | `bytes.py` | yes | Must decode to readable UTF-8 |
| `rot13`, `caesar` | `caesar.py` | yes | Whole text, or runs of words that are not English as they stand |
| `reverse` | `reverse.py` | yes | Whole text, or runs of words |

`runs.py` holds the shared code that finds runs of words that are not English.

## Limits

- Inputs over 100,000 characters are returned unchanged.
- Layers are followed at most 4 deep.
- At most 200 replacements per text or layer.
- Input is only ever decoded, never executed.

## Adding a transform

1. Create `transforms/<name>.py` with a `Transform` subclass. Set `name` to the trick's name in
   `evaluation/tricks.py`, and `level` as `docs/taxonomy.md` says.
2. In `propose`, yield a `Candidate` for each span the trick may have been applied to. Propose
   generously where it is cheap; the engine does the judging. Keep spans aligned to whole words
   or tokens so the scorer has something to read.
3. Set `judged = False` only when a proposal cannot be wrong.
4. Add it to `ALL` in `transforms/__init__.py`.
5. Add unit tests, then run the evaluation. Keep the transform only if the clean set stays clean.

## State on 2026-10-09

The fourteen transforms above exist: every trick handled at the `conservative` level. The six
ambiguous visual tricks (`homoglyph`, `accent-substitution`, `combining-marks`, `leetspeak`,
`separator`, `repeated-chars`) are not built yet.
