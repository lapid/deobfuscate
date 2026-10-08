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
3. The engine deobfuscates the candidate's replacement **itself**, by running the whole process
   on it one layer deeper. This is what handles layers: base64 inside base64, or base64 inside
   rot13. The candidate is judged by what it finally turns into, not by its first decode.
4. The engine judges: the final text must have enough letters, score high enough as English,
   and beat the text it replaces by a margin. A transform marked `judged = False` skips this.
5. The accepted candidate with the largest gain is applied. Its step is recorded, followed by
   the steps found inside it, with their positions shifted to where the replacement now sits.
6. Repeat from 1 until no candidate is accepted.

Because every accepted step must raise the score, the loop cannot go round in circles, and a
second run over the output finds nothing more to do.

## Strictness

A level does two things: it enables the transforms whose `level` is at or below it, and it
picks a `Policy` in `engine.py`:

| Level | Minimum score | Minimum gain | Minimum letters |
|---|---|---|---|
| conservative | 0.70 | 0.30 | 10 |
| balanced | 0.60 | 0.25 | 6 |
| aggressive | 0.50 | 0.15 | 4 |

These are starting values, to be tuned on the dev split.

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

## State on 2026-10-08

Two transforms exist, as proof that the engine works: `base64` (also the URL-safe alphabet)
and `rot13`. The rest are Phase 3.
