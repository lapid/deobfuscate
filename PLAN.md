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
- [x] Write the obfuscation taxonomy: `docs/taxonomy.md`
- [ ] Define the result shape: `text`, plus `steps` of `{transform, span, before, after, confidence}`
- [ ] Define the interface: `deobfuscate(text) -> Result`, and a CLI (stdin to stdout, `--json` for the record)

## Phase 0.5 — Research and samples

Time-boxed. The aim is to borrow known answers and find cases we would not have thought of,
not to survey the field. Each source gets a short note, not a copy of the article.

- [x] Set up the knowledge layout
  - [x] `docs/research/README.md`: index, one line per note, plus the conclusions list
  - [x] `docs/research/<topic>.md`: one note per topic
  - [x] `data/samples/*.jsonl`: collected samples, one JSON object per line
  - [x] `data/reference/`: vendored data files, with version and licence
- [x] Read prior art
  - [x] Unicode security: UTS #39 confusables and mixed-script detection (UTR #36 not read)
  - [x] Existing tools: Ciphey, CyberChef "Magic", ftfy, decancer, disarm benchmark
  - [x] Research on adversarial text perturbation and its normalisation (abstract level)
  - [x] Research on obfuscated prompts and filter evasion (abstract level)
  - [x] How language-plausibility scoring is done, and which data is licensed for it
- [ ] Collect samples
  - [x] Seed set: 36 self-written obfuscated, 35 self-written clean negatives
  - [x] SMS Spam Collection (CC BY 4.0): 10 real messages; licence verified
  - [x] Decide what is safe to store: redistributable only, nothing abusive
  - [ ] Check licences of SpamAssassin, Enron-Spam, Jigsaw, PhishTank, JailbreakBench
  - [ ] Run our own clean sentences through independent obfuscator tools (needs a person or a browser)
  - [ ] More real deliberate obfuscation; the SMS data had very little
  - [ ] Test-only split, sampled by script and never read (moved to Phase 1)
- [x] Write conclusions: `docs/research/README.md`
- [x] Revise the taxonomy and later phases in light of the findings: `docs/taxonomy.md`

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
  - [ ] Text-message shorthand (`l8r`, `sum1`, `goin2bed`); sample from the SMS Spam Collection
  - [ ] Hashes, UUIDs, API-key-like strings (look like hex/base64 but are not text)
  - [ ] URLs, emails, file paths, code snippets
  - [ ] Real non-Latin text (Russian, Greek, Hebrew) and mixed-script text
  - [ ] Emoji, accented names, intentional spacing and punctuation
  - [ ] Wrong-encoding damage (`Ã©`), which must come back unchanged
- [ ] Collect a small **real-world set** by hand (synthetic data only tests what we thought of)
- [ ] Split into dev and test; keep test untouched until reporting
- [ ] Metrics
  - [ ] False-change rate on the clean set (headline metric, target near zero)
  - [ ] Exact-match recovery rate on the obfuscated set
  - [ ] Character error rate (normalised edit distance) for partial credit
  - [ ] Per-transform precision and recall, from the recorded steps vs. tricks used
  - [ ] Idempotence: `deobfuscate(deobfuscate(x)) == deobfuscate(x)`
  - [ ] Runtime per input
  - [ ] All of the above broken down by text length (short text is where scorers fail)
- [ ] One command runs the evaluation and prints a per-category table, for each strictness level
- [ ] Baselines: identity (return input) and Unicode NFKC only
- [ ] Optional comparison baselines, evaluation only, never imported by the tool: ftfy, decancer

## Phase 2 — Core engine

- [ ] Transform interface: find candidate spans, propose decoded text, name itself
- [ ] "Leave alone" recognisers: URLs, emails, paths, hashes, UUIDs, key-like tokens
- [ ] Script lookup for mixed-script detection (`unicodedata` has no script property)
- [ ] Plausibility scorer (how much does this look like real language?)
  - [ ] Cheap pre-checks first: valid UTF-8, printable, entropy drop
  - [ ] Word list generated from SCOWL (size 60 to start), shipped with its notice
  - [ ] Character n-gram table built by our own script from public-domain English text
  - [ ] Choose the public-domain corpus; check its fit on modern text
  - [ ] Compare word-hit rate, n-gram score, and both on the dev set
  - [ ] Minimum-length rule: decline to judge spans that are too short
- [ ] Acceptance rule: apply a candidate only if the score improves by a margin
- [ ] Strictness levels as presets of margin and enabled transform groups; `conservative` is the default
- [ ] Loop to a fixed point for nested layers, with a depth limit
- [ ] Record each accepted step with its span and before/after text
- [ ] Input size limit and safe failure (return input unchanged on any error)

## Phase 3 — Transforms, safest first

Run the evaluation after each one; keep it only if the clean set stays clean.

- [ ] **Lossless, low risk**
  - [ ] Zero-width and invisible characters
  - [ ] Hidden text in tag characters: remove, and report the hidden content in the step
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
  - [ ] Homoglyphs: map built from the non-ASCII-to-ASCII subset of `confusables.txt`; per word,
        in mixed-script words or when the result is a known word
  - [ ] Combining-mark overlays (strikethrough, stacked marks)
  - [ ] Leetspeak: only when the result is a known word; never on shorthand
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
