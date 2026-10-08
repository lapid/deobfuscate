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
- [x] Result shape: `Result(text, steps)`, each `Step(transform, start, end, before, after, confidence, hidden)`
- [x] Interface: `deobfuscate(text, strictness=...) -> Result`, and a `deobfuscate` command (`--json` for the record)

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

How to run and read it: `docs/evaluation.md`.

- [x] Clean source corpus: 7,000 real texts per split from Wikipedia, Wikinews, Stack Exchange,
      text messages and public-domain books (`evaluation/sources.py`, `evaluation/corpus.py`)
- [x] **Obfuscator** (`evaluation/obfuscator.py`): all 21 tricks in the taxonomy
  - [x] Single-trick cases
  - [x] Stacked cases (16 two-layer recipes)
  - [x] Partial cases (a run of words inside clean text)
- [x] **Clean set** of hard negatives (`evaluation/negatives.py`), 21 categories
  - [x] Numbers and units
  - [x] Text-message shorthand (self-written; real SMS sampling still open below)
  - [x] Hashes, UUIDs, key-like tokens
  - [x] URLs, emails, file paths, code snippets
  - [x] Other languages and mixed-script text
  - [x] Emoji, accented names, symbols, spaced headings, emphasis
  - [x] Wrong-encoding damage, which must come back unchanged
- [x] Dev and test splits share no document and no text
- [x] Metrics (`evaluation/metrics.py`)
  - [x] False-change rate on the clean set
  - [x] Exact-match recovery rate
  - [x] Character error rate, and share of texts made worse
  - [x] Per-transform precision and recall from the step record
  - [x] Idempotence
  - [x] Runtime per input
  - [x] Breakdown by text length
- [x] One command runs the evaluation, for each strictness level
- [x] Baselines: return the input, and Unicode NFKC. Numbers in `docs/evaluation.md`
- [x] Unit tests for the obfuscator, metrics and package interface
- [x] Real informal clean text: text messages and Stack Exchange questions
- [x] First real obfuscated samples: about 135 text messages per split with HTML entities
- [x] More short texts: 200 clean and 86 obfuscated under 20 characters in dev
- [x] Real deliberate obfuscation, local only: BitCore, 3,000 phishing sentences per split (`evaluation/local_sets.py`)
- [x] `accent-substitution` trick and Greek lowercase lookalikes added to the generator, after BitCore showed real senders use them
- [ ] Hand-disguised sentences: 50 waiting in `data/human/to_disguise.txt`; then a loader
- [ ] Ask the BitCore authors to add a licence
- [ ] Real samples of encodings (base64 and so on): none yet
- [ ] Inspect the Zenodo leetspeak spam set (CC BY 4.0) as an independent-generator category
- [ ] Lookalikes from Armenian, Cherokee and Runic in the generator
- [ ] Test-only trick variants, so the test split checks generalisation
- [ ] Larger hand-written categories, or generators for them
- [ ] Three-layer stacks
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
  - [ ] Accent substitution: per word, only when removing the accent turns a non-word into a word
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
- [ ] Unit tests per transform, plus the evaluation as a regression check (harness tests exist)
- [ ] README: usage, what is handled, known limits, current scores

## Phase 6 — Publishing

- [x] Rename the project in `pyproject.toml`; add description and licence
- [x] `deobfuscate` package under `src/`, with URLs and a build backend in `pyproject.toml`
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
