# Plan

Mark items done by changing `[ ]` to `[x]`. Decisions and their reasons go in `JOURNAL.md`.

## Guiding notes

- **Evaluation comes before the deobfuscator.** Without a test set and a score we cannot tell
  whether a new rule helps or just moves errors around.
- **First, do no harm.** Changing clean text is the worst mistake (see journal). Every
  transform must justify itself: apply it only when the result is measurably more plausible.
- **Every change is recorded.** The output is the text plus an ordered list of the transforms applied.
- **Small independent transforms.** Each one detects, decodes, and reports; a shared scorer decides.
- **Never execute input.** Decoding only, with limits on input size and nesting depth.
- **Tune on dev, report on test.** Rules written while staring at the test set will overfit it.

## Phase 0 — Scope and contract

- [x] Scope: encodings and visual tricks; code obfuscation is out
- [x] Output includes a record of the transforms applied
- [x] Languages: English only; other languages pass through unchanged
- [x] No LLM, Python 3.14 or newer
- [x] Dependencies: n-gram and word-list resources allowed; no other deobfuscators
- [x] Licence: MIT
- [x] Add the `LICENSE` file
- [x] Name: `deobfuscate`; hosting: `github.com/lapid/deobfuscate`
- [ ] Write the obfuscation taxonomy: each type, one example, in or out of v1
- [ ] Define the result shape: `text`, plus `steps` of `{transform, span, before, after, confidence}`
- [ ] Define the interface: `deobfuscate(text) -> Result`, and a CLI (stdin to stdout, `--json` for the record)

## Phase 0.5 — Research and samples

Time-boxed. The aim is to borrow known answers and find cases we would not have thought of,
not to survey the field. Each source gets a short note, not a copy of the article.

- [ ] Set up the knowledge layout
  - [ ] `docs/research/README.md`: index, one line per note, plus a running "conclusions" list
  - [ ] `docs/research/<topic>.md`: one note per source or topic (template below)
  - [ ] `data/samples/*.jsonl`: collected samples, one JSON object per line
  - [ ] `data/reference/`: vendored data files (e.g. Unicode confusables), with version and licence
- [ ] Read prior art (verify each from the source, not from memory)
  - [ ] Unicode security: UTS #39 confusables and mixed-script detection, UTR #36
  - [ ] Existing tools and how they decide: Ciphey, CyberChef "Magic", ftfy, confusable_homoglyphs
  - [ ] Research on adversarial text perturbation and its normalisation (leetspeak, visual attacks)
  - [ ] Research on obfuscated prompts and filter evasion (encodings, ciphers, spacing tricks)
  - [ ] How language-plausibility scoring is done in practice (n-grams, dictionary, entropy)
- [ ] Collect samples
  - [ ] Verify the candidate sources listed in the journal (content and licence)
  - [ ] Run our own clean sentences through independent obfuscator tools
  - [ ] Real obfuscated text, with source and the trick(s) used
  - [ ] Hard clean negatives found in the wild
  - [ ] Decide what is safe to store (real samples are often spam or abusive) and check licences
  - [ ] Set aside part of the real samples as test-only before anyone reads them for rule ideas
- [ ] Write conclusions: what each finding changes in this plan; log decisions in the journal
- [ ] Revise the taxonomy and phases 1 to 3 in light of the findings

**Note template:** source and URL, date read, key points (five lines at most), what it changes
for us, open questions.

**Sample format:** `{"id", "text", "expected", "tricks": [...], "source", "split": "dev|test", "notes"}`.
`expected` is null when the correct answer is unknown.

## Things to settle before coding

- [x] **Who obfuscates:** both accidental mess and deliberate evasion. No fixed rule list is ever
      complete, so transforms must be easy to add.
- [x] **Ambiguous inversions:** one best guess, confidence on each step.
- [x] **What counts as the "original":** minimal edit; nothing outside an accepted transform changes.
- [x] **Offsets:** each step records its span in the text as it stood before that step.
- [x] **Done criteria for v1 (provisional):** at most 1% clean texts changed; 90% recovery for
      lossless and encodings; 70% for ambiguous tricks. Final numbers after baselines.
- [x] **Non-English input:** detected and returned unchanged.
- [x] **Samples:** commit only redistributable ones; otherwise a fetch script and labels. No abusive content.

## Phase 1 — Evaluation harness

- [ ] Pick a clean source corpus (ordinary sentences, varied length)
- [ ] Write an **obfuscator**: applies each trick to clean text, giving `(obfuscated, original, tricks used)` pairs
  - [ ] Single-trick cases
  - [ ] Stacked cases (e.g. leetspeak inside base64, double base64)
  - [ ] Partial cases (one obfuscated word or span inside clean text)
- [ ] Build the **clean set** of hard negatives that must come back unchanged
  - [ ] Numbers and units (`route 66`, `3 apples`, `v2.0`)
  - [ ] Hashes, UUIDs, API-key-like strings (look like hex/base64 but are not text)
  - [ ] URLs, emails, file paths, code snippets
  - [ ] Real non-Latin text (Russian, Greek, Hebrew) and mixed-script text
  - [ ] Emoji, accented names, intentional spacing and punctuation
- [ ] Collect a small **real-world set** by hand (synthetic data only tests what we thought of)
- [ ] Split into dev and test; keep test untouched until reporting
- [ ] Metrics
  - [ ] False-change rate on the clean set (headline metric, target near zero)
  - [ ] Exact-match recovery rate on the obfuscated set
  - [ ] Character error rate (normalised edit distance) for partial credit
  - [ ] Per-transform precision and recall, from the recorded steps vs. tricks used
  - [ ] Idempotence: `deobfuscate(deobfuscate(x)) == deobfuscate(x)`
  - [ ] Runtime per input
- [ ] One command runs the evaluation and prints a per-category table, for each strictness level
- [ ] Baselines: identity (return input) and Unicode NFKC only

## Phase 2 — Core engine

- [ ] Transform interface: find candidate spans, propose decoded text, name itself
- [ ] Plausibility scorer (how much does this look like real language?)
  - [ ] Decide the signal: dictionary hit rate, character n-gram model, or both
  - [ ] Decide the data source for it
- [ ] Acceptance rule: apply a candidate only if the score improves by a margin
- [ ] Strictness levels as presets of margin and enabled transform groups; `conservative` is the default
- [ ] Loop to a fixed point for nested layers, with a depth limit
- [ ] Record each accepted step with its span and before/after text
- [ ] Input size limit and safe failure (return input unchanged on any error)

## Phase 3 — Transforms, safest first

Run the evaluation after each one; keep it only if the clean set stays clean.

- [ ] **Lossless, low risk**
  - [ ] Zero-width and invisible characters
  - [ ] Unicode compatibility forms (fullwidth, mathematical alphabets, enclosed letters)
  - [ ] HTML entities
  - [ ] URL percent-encoding
  - [ ] Backslash escapes (`\x41`, `A`)
- [ ] **Encodings that need detection**
  - [ ] Base64 (and URL-safe variant)
  - [ ] Hex, binary, decimal character codes
  - [ ] ROT13 and other Caesar shifts
  - [ ] Reversed text
- [ ] **Ambiguous, high risk**
  - [ ] Homoglyphs (cross-script lookalikes), per word and only in mixed-script words
  - [ ] Leetspeak
  - [ ] Separator insertion (`s p a c e d`, `s.p.l.i.t`)
  - [ ] Repeated characters (`heeellooo`)

## Phase 4 — Error analysis loop

- [ ] Review the worst dev failures by category after each phase 3 group
- [ ] Add each real failure as a test case before fixing it
- [ ] Tune acceptance margins on dev; check the trade-off between false changes and recovery
- [ ] Final run on the test set and the real-world set

## Phase 5 — Packaging

- [ ] CLI and importable function
- [ ] Unit tests per transform, plus the evaluation as a regression check
- [ ] README: usage, what is handled, known limits, current scores

## Phase 6 — Publishing

- [x] Rename the project in `pyproject.toml`; add description and licence
- [ ] Turn `main.py` into a `deobfuscate` package; add URLs and a build backend to `pyproject.toml`
- [x] `LICENSE` (MIT)
- [ ] `CONTRIBUTING.md`: how to add a transform, required samples, evaluation gate, data licence rule
- [ ] Pull-request template, `SECURITY.md`, code of conduct
- [ ] Continuous integration: unit tests and the evaluation gate on every pull request
- [ ] Protect `master`: pull requests only, passing checks, one maintainer approval
- [ ] Release process: version tag builds and uploads to PyPI from CI
- [ ] Check that nothing committed is unsafe or unlicensed to publish (samples, vendored data)
- [x] First commit and push to `github.com/lapid/deobfuscate` (public)
- [ ] Register the PyPI name

## Later, not in v1

- LLM as a fallback or as a comparison baseline
- Code obfuscation
- Ciphers needing a key (Vigenère, XOR)
