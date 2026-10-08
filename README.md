# deobfuscate

Takes a text and returns the deobfuscated text, plus a record of which transforms were applied.

**Status: planning. There is no working deobfuscator yet.**

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

- [`PLAN.md`](PLAN.md): the phased plan and current progress.
- [`JOURNAL.md`](JOURNAL.md): every decision and its reason.
- [`AGENTS.md`](AGENTS.md): the settled constraints and working rules, for AI coding agents and people alike.

## Licence

MIT. See [`LICENSE`](LICENSE).
