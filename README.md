# deobfuscate

Takes a text and returns the deobfuscated text, plus a record of which transforms were applied.

**Status: in development. Encodings, escapes, invisible characters and styled letters are undone, including when layered. Lookalike letters, added accents, overlaid marks, leetspeak and spaced-out words are undone at the `balanced` level, and stretched words, texting shorthand, common misspellings and emoji standing for a word at `aggressive`. On the held-out test set, 0.04% of clean texts are changed at the default level, 0.17% at `balanced` and 0.51% at `aggressive`, and 96.6%, 91.3% and 88.9% of disguised texts come back exactly (ignoring capitals); details and weak spots in `docs/evaluation.md`. Not yet packaged or released.**

## What it will handle

- **Encodings:** base64, hex, rot13, URL and HTML escapes, including nested layers.
- **Visual tricks:** homoglyphs, leetspeak, invisible characters, inserted separators.

English text only. Code obfuscation is out of scope.

## Design in brief

- Changing clean text is treated as the worst mistake, so a transform is applied only when the
  result scores as more plausible English than the input.
- Every change is recorded: the output is the text plus an ordered list of steps.
- A strictness setting chooses how aggressive it is; `conservative` is the default.
- No LLM. Requires Python 3.14 or newer.

## How the project is run

- [`docs/architecture.md`](docs/architecture.md): how it works inside.
- [`docs/evaluation.md`](docs/evaluation.md): how the tool is measured, and the baseline numbers.
- [`PLAN.md`](PLAN.md): the phased plan and current progress.
- [`JOURNAL.md`](JOURNAL.md): every decision and its reason.
- [`AGENTS.md`](AGENTS.md): the settled constraints and working rules, for AI coding agents and people alike.

## Licence

MIT. See [`LICENSE`](LICENSE).
