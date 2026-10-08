# deobfuscate: guide for agents

Python library and CLI that takes a text and returns the deobfuscated text plus a record of the
transforms applied. This file is the current state. The reasons are in `JOURNAL.md`.

## Where things are

- `JOURNAL.md`: every decision with its reason, in order. Open questions are at the bottom.
- `PLAN.md`: phased plan with checkboxes. Tick items as they are completed.
- `docs/research/README.md`: research conclusions and index of notes. Read before designing a transform.
- `docs/taxonomy.md`: every obfuscation type, its strictness level, and what is out of scope.
- `docs/evaluation.md`: how the tool is measured, the commands, and the baseline numbers.
- `src/deobfuscate/`: the package. `evaluation/`: the test-set generator, metrics and runner. `tests/`: unit tests.
- `data/eval/`: evaluation sets, dev and test, with per-row licences (not MIT). Do not edit by hand.
- `data/local/`: git-ignored real-world set (BitCore) built by `uv run python -m evaluation.local_sets`. Never commit it.
- `data/human/`: sentences disguised by hand by the owner. Do not read the answers in the sheet; half are test data.
- `data/samples/`: small hand-made seed samples as JSONL; format and licences in its README.
- `data/reference/`: third-party data files, unmodified, with their own licences.

## Settled constraints

- **Scope:** encodings (base64, hex, rot13, URL and HTML escapes) and visual tricks (homoglyphs,
  leetspeak, invisible characters, inserted separators). Code obfuscation is out.
- **Both causes:** accidental mess and deliberate evasion. The tool never claims completeness.
- **English only.** Other languages and scripts pass through unchanged.
- **Worst mistake is changing clean text.** A transform is applied only when a plausibility score
  improves. False-change rate on the clean set is the headline metric.
- **Output:** the text plus an ordered record of the transforms applied.
- **No LLM** in the tool.
- **Dependencies:** n-gram and word-list resources are allowed. No other deobfuscation tool or
  library may be imported; all detection and decoding logic is ours. Standard-library codecs are fine.
- **Python 3.14 or newer.**
- **MIT licence.** Every dependency and committed data file must be MIT-compatible.
- **Public project:** `github.com/lapid/deobfuscate` and PyPI package `deobfuscate`, branch
  `master`, version 0.x. Everything committed must be safe to publish.
- **Owners:** Lapid Harel and the LLM coding agent. Lapid is the sole human maintainer.
- **Outside contributions:** by pull request; tests and the evaluation must pass; the false-change rate
  on the clean set may not rise; new transforms come with samples; one maintainer approves.
- **Strictness levels:** `conservative` (default; lossless transforms and encodings),
  `balanced` (adds ambiguous visual tricks), `aggressive` (lower acceptance margin).
- **One best guess** is returned, with a confidence on each recorded step.
- **Minimal edit:** only characters inside an accepted transform change. No whole-text Unicode
  normalisation.
- **Offsets:** each step records its span in the text as it stood before that step.
- **Samples:** commit only those whose licence allows redistribution; otherwise a fetch script
  and labels. No abusive content. The obfuscator ships as evaluation tooling.
- **Homoglyphs:** use only the non-ASCII-to-ASCII entries of `data/reference/confusables.txt`.
  Never apply the table directly; it maps `m` to `rn` and `1` to `l`.
- **Shorthand is not obfuscation:** `l8r`, `sum1`, `4` for "for" stay as written. Leetspeak
  decoding requires the result to be a known word.
- **Hidden text in invisible characters** is removed from the output and shown in the step record.
- **Wrong-encoding damage** (`Ã©` for `é`) is out of v1 and must come back unchanged.
- **Scorer data:** word list from SCOWL; character n-gram table built by our own script from
  public-domain text. Not `wordfreq`, not Norvig's files (licences).
- **Third-party data keeps its own licence** and credit; MIT covers our own work. CC BY and
  CC BY-SA data may be committed, with source, address and licence on every row.
- **Provisional v1 targets:** at most 1% of clean texts changed; 90% exact recovery for lossless
  transforms and encodings; 70% for ambiguous visual tricks.
- **Evaluation before implementation.** Test sets and metrics come first.

Proposals not yet confirmed by the user are marked as such in `JOURNAL.md`. Do not treat them as settled.

## Commands

- Tests: `uv run python -m unittest discover -s tests`
- Evaluation: `uv run python -m evaluation.run` (add `--detail` for per-category tables)

## Working rules

- Record every decision or change of decision in `JOURNAL.md`, with the reason, and mark
  proposals the user has not confirmed. Mark superseded entries rather than deleting them.
- Update this file in the same change whenever a settled constraint changes.
- Tick `PLAN.md` items when done; add new items rather than working off-plan.
- Run the evaluation after adding or changing a transform. Keep the change only if the clean set
  stays clean.
- Never read `split: "test"` samples or `data/eval/test/` to get ideas for rules, and do not tune against the test split.
- Transform names come from `evaluation/tricks.py`; use exactly those in `Step.transform`.
- The n-gram table must not be built from the ten books used for the evaluation corpus.
- Never execute input text. Decode only, within size and depth limits.
- Research notes hold conclusions and a source link, not copies of articles.
- Verify claims about external tools, datasets, and licences from the source before relying on them.
