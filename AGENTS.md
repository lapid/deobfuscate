# deobfuscate: guide for agents

Python library and CLI that takes a text and returns the deobfuscated text plus a record of the
transforms applied. This file is the current state. The reasons are in `JOURNAL.md`.

## Start here

1. Read this file to the end. It is the current state of the project and its rules.
2. Read "Current status" below, then the unticked items of the current phase in `PLAN.md`.
3. Read the document for the area you will touch (table below) before changing anything.
4. Open `JOURNAL.md` only when you need the reason behind a decision; search it by keyword.

## Current status (updated 2026-10-09)

- **Done:** scope and decisions (Phase 0), research (Phase 0.5), evaluation harness (Phase 1),
  core engine and scorer (Phase 2), and two of three groups of Phase 3.
- **Phase 3 so far:** the fourteen transforms that run at `conservative` exist: invisible
  characters, hidden text, styled and fullwidth letters, HTML, URL and backslash escapes, base64,
  hex, binary, decimal codes, rot13, Caesar shifts, reversal.
- **Next:** the third group of Phase 3, the ambiguous visual tricks: `homoglyph`,
  `accent-substitution`, `combining-marks`, `leetspeak`, `separator`, `repeated-chars`. These
  decide on one word of evidence each, which the scorer has not been tested on. Then Phase 4
  (tune the presets, error analysis, final run on test), Phase 5, Phase 6.
- **Numbers on dev, `conservative`:** 1 of 7,442 clean texts changed; 95.5% of obfuscated texts
  recovered; 0.1% made worse. The real phishing set (0 of 3,000) waits on the third group.
- **Known problems:** shifted or reversed words inside clean text recover poorly (28% to 68%);
  texts under 20 characters recover 80%; the presets have not had a tuning pass; no recogniser
  yet for key-like tokens or code.
- **Waiting on the owner:** checking the test half of `data/human/to_disguise.txt` for answers
  typed under the wrong sentence.
- **Deferred to version 2:** see "Version 2" in `PLAN.md` (evaluation gaps, public demo site).

## How we work with the owner

- The owner decides goals and anything about scope, licences, publishing and risk. Ask, with a
  recommendation, and keep going on whatever does not depend on the answer.
- The owner starts each phase. Do not begin the next phase unasked.
- Decisions made by the agent alone are allowed for technical detail, and are logged as
  "decided by Claude" so the owner can overrule them.
- Report results plainly, including what failed, what was not checked, and what is assumed.
- The agent may commit and push to `master` for work the owner asked for.

## Documents

Each document has one job. Update it in the same commit as the change it describes.

| Document | What it is for | Update it when |
|---|---|---|
| `AGENTS.md` (this file; `CLAUDE.md` imports it) | Current state: status, rules, settled constraints, map of the repo | Status changes, a constraint is settled or changed, a document or folder is added |
| `JOURNAL.md` | The log of every decision, in order, with why, what was rejected, and who decided. Open questions at the bottom | A decision is made, changed or confirmed. Never delete an entry; mark it superseded |
| `PLAN.md` | The phased to-do list with checkboxes, including "Version 2" | An item is finished (tick it) or new work is discovered (add it) |
| `README.md` | The public front page: what the tool does and its honest status | The status or the user-facing behaviour changes |
| `docs/taxonomy.md` | Every trick: example, strictness level, main guard; and what is out of scope | A trick is added, moved between levels, or ruled out |
| `docs/architecture.md` | How the engine works and how to add a transform | The engine, limits, presets or transform interface change |
| `docs/scorer.md` | The plausibility scorer and the experiment behind it | The scorer or its data changes, or a new experiment is run |
| `docs/evaluation.md` | The evaluation sets, the measures, the commands, baseline numbers, known limits | The sets, metrics or baselines change |
| `docs/research/README.md` | Numbered conclusions from research and from real data; index of the notes | Something is learned that changes the design |
| `docs/research/*.md` | One note per topic, with sources and what was and was not verified | A source is read or checked |
| `data/eval/README.md` | Sources, licences and credits of the evaluation sets | A source is added or the sets are rebuilt differently |
| `data/samples/README.md`, `data/human/README.md`, `data/reference/README.md`, `src/deobfuscate/data/NOTICE.md` | What each data folder holds and under which licence | Files there change |

## Code and data

- `src/deobfuscate/`: the package. `engine.py` judges, `transforms/` propose, `scorer.py` scores,
  `protect.py` and `scripts.py` support, `data/` holds the word list, four-gram table and script table.
- `evaluation/`: test-set generator (`obfuscator.py`, `negatives.py`), corpus builders
  (`sources.py`, `corpus.py`, `build.py`, `local_sets.py`, `human.py`), `metrics.py`, `run.py`.
  Not part of the installed package.
- `tests/`: unit tests, standard-library `unittest`.
- `tools/build_data.py`: rebuilds the data files shipped in `src/deobfuscate/data/`.
- `data/eval/`: evaluation sets, dev and test, with per-row licences (not MIT). Do not edit by hand.
- `data/local/`: git-ignored real-world set (BitCore) built by `uv run python -m evaluation.local_sets`. Never commit it.
- `data/human/`: sentences disguised by hand by the owner. Do not read the answers in the sheet; half are test data.
- `data/samples/`: small hand-made seed samples for debugging.
- `data/reference/`: third-party data files, unmodified, with their own licences.
- `data/cache/`: git-ignored downloads.

## Settled constraints

- **Scope:** encodings (base64, hex, rot13, URL and HTML escapes) and visual tricks (homoglyphs,
  accent substitution, leetspeak, invisible characters, inserted separators). The full list is
  `docs/taxonomy.md`. Code obfuscation is out.
- **No spelling correction** in v1: misspellings, dropped letters, shorthand and emoji standing
  for a word are left as written.
- **Both causes:** accidental mess and deliberate evasion. The tool never claims completeness.
- **English only.** Other languages and scripts pass through unchanged.
- **Worst mistake is changing clean text.** A transform is applied only when a plausibility score
  improves. False-change rate on the clean set is the headline metric.
- **Output:** the text plus an ordered record of the transforms applied.
- **No LLM** in the tool.
- **Dependencies:** n-gram and word-list resources are allowed. No other deobfuscation tool or
  library may be imported; all detection and decoding logic is ours. Standard-library codecs are fine.
- **Python 3.14 or newer.**
- **MIT licence** for our code and our own data. Third-party data may be committed under its own
  licence if that licence allows redistribution.
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
- **Real-world data without a licence** (BitCore) is used locally only and never committed.
- **Limits:** inputs over 100,000 characters are returned unchanged; layers are followed 4 deep.
- **Provisional v1 targets:** at most 1% of clean texts changed; 90% exact recovery for lossless
  transforms and encodings; 70% for ambiguous visual tricks.
- **Evaluation before implementation.** Test sets and metrics come first.

Proposals not yet confirmed by the user are marked as such in `JOURNAL.md`. Do not treat them as settled.

## Commands

- Tests: `uv run python -m unittest discover -s tests`
- Evaluation: `uv run python -m evaluation.run` (add `--detail` for per-category tables,
  `--level conservative` for one level, `--system identity` or `nfkc` for a baseline)
- Real-world set, once per machine: `uv run python -m evaluation.local_sets`
- Try it: `uv run deobfuscate --json "some text"`

## Working rules

- Record every decision or change of decision in `JOURNAL.md`, with the reason, and mark
  proposals the user has not confirmed. Mark superseded entries rather than deleting them.
- Update this file in the same change whenever a settled constraint changes, and refresh
  "Current status" at the end of every piece of work.
- Tick `PLAN.md` items when done; add new items rather than working off-plan.
- Run the evaluation after adding or changing a transform. Keep the change only if the clean set
  stays clean.
- Never read `split: "test"` samples or `data/eval/test/` to get ideas for rules, and do not tune against the test split.
- Transform names come from `evaluation/tricks.py`; use exactly those in `Step.transform`.
- The n-gram table must not be built from the ten books used for the evaluation corpus.
- Never execute input text. Decode only, within size and depth limits.
- Research notes hold conclusions and a source link, not copies of articles.
- Verify claims about external tools, datasets, and licences from the source before relying on them.
