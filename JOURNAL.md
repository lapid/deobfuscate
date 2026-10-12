# Decision journal

Running log of goals and decisions for the text deobfuscator. Newest entries at the bottom.
Each decision records what we chose, why, and what we rejected.

This file is history, and it is long. The current state of every settled decision is
summarised in `AGENTS.md`; come here for the reasoning. Entries marked "superseded" no longer hold.
Each heading says who decided: "confirmed" means the owner agreed, "decided by Claude" means the
agent chose and the owner may overrule, "proposed" means not yet agreed.

## Goal

A Python script that takes a text and returns a text, attempting to undo obfuscation.

## Decisions

### 2026-10-08 — Keep a decision journal
- **Decision:** Record goals and decisions in this file as we go.
- **Why:** Requested at project start, so the reasoning behind the design stays recoverable.

### 2026-10-08 — Scope: encodings and visual tricks
- **Decision:** Handle encodings (base64, hex, rot13, URL/HTML escapes) and visual tricks
  (homoglyphs, leetspeak, invisible characters, inserted separators).
- **Rejected:** Code obfuscation (minified/packed scripts). Different problem, different tools.

### 2026-10-08 — Output carries a record of transformations
- **Decision:** Return the deobfuscated text together with an ordered list of the transforms applied.
- **Why:** Requested. It also makes every change auditable and lets the evaluation score each
  transform separately.

### 2026-10-08 — Worst mistake: changing clean text (confirmed)
- **Decision:** Treat a false change to clean text as worse than a missed obfuscation.
- **Why:** Most input will be clean, so even a small false-change rate damages more text than the
  tool repairs. A miss leaves the user no worse off than without the tool; a false change silently
  destroys correct information.
- **Consequence:** A transform is applied only when the result scores as more plausible than the
  input. False-change rate on clean text is the headline metric.
- **Would change if:** the main use is catching filter evasion, where a miss is the costly error.

### 2026-10-08 — Evaluation before implementation
- **Decision:** Build the test sets and scoring first, then the deobfuscator. Plan is in `PLAN.md`.
- **Why:** Rules for ambiguous tricks trade one error for another; only a score shows which way.
- **How:** Generate obfuscated/original pairs with our own obfuscator, add a clean set of hard
  negatives, and add a small hand-collected real-world set.

### 2026-10-08 — No LLM in v1 (confirmed)
- **Decision:** Rules plus a plausibility score. LLM kept as a later fallback or baseline.
- **Why:** Deterministic, fast, free to run, and each step is explainable in the record.

### 2026-10-08 — Research and sample collection before coding (confirmed)
- **Decision:** Add a time-boxed research phase (Phase 0.5 in `PLAN.md`): read prior art, collect
  real samples, and store both as small files in the repo.
- **Why:** Existing tools and Unicode standards already answer parts of this problem, and real
  samples expose tricks a synthetic generator would never produce.
- **How it stays usable by an LLM:** short notes per source with a "what it changes for us"
  section, an index file, samples as JSONL with provenance, and `CLAUDE.md` pointing to all of it
  so each session starts with the map. Notes hold conclusions, not copies of articles.
- **Guard:** part of the real samples is set aside as test-only before being read for rule ideas.

### 2026-10-08 — The project will be published as a public git repo
- **Decision:** Publish for anyone to use.
- **Consequences:** needs a licence; everything committed (samples, vendored data, notes, this
  journal) must be legally and reputationally safe to publish; users are unknown, so the
  worst-mistake choice and the Python version floor matter more; install and usage must be simple.

### 2026-10-08 — English only
- **Decision:** Deobfuscate English text only.
- **Consequence:** Text in other languages or scripts must pass through unchanged; the clean set
  keeps non-English negatives to enforce this.

### 2026-10-08 — No third-party dependencies (superseded, see "Dependencies: language data allowed")
- **Decision:** Standard library only at runtime.
- **Consequence:** The plausibility scorer's data (n-gram table, word list) must be built by our
  own script and shipped in the repo, from sources whose licence allows redistribution.

### 2026-10-08 — Plausibility scorer is in
- **Decision:** A candidate is accepted only if a language-plausibility score improves.
- **Open:** which signal and which data (see design proposals below).

### 2026-10-08 — Both kinds of obfuscation: accidental and deliberate
- **Decision:** Handle accidental mess (encoding leftovers, copy-paste artefacts) and deliberate evasion.
- **Consequence:** Deliberate obfuscators adapt, so the tool cannot claim completeness. Transforms
  must be easy to add, and the evaluation must include stacked and partial cases.

### 2026-10-08 — Python 3.14 or newer stays
- **Decision:** Keep `requires-python = ">=3.14"`.
- **Accepted cost:** users on older Python cannot install it.

### 2026-10-08 — Completely free to use
- **Decision:** No restrictions on use.
- **Resolved:** MIT, see the licence entry below.

### 2026-10-08 — Design proposals (confirmed)
Method: sort each question into decide by principle now, decide by experiment on the dev set, or
defer by keeping the choice cheap to reverse.

- **Scorer (by experiment):** build both a character n-gram model and a word-list hit rate, since
  each is small in pure Python, and let the dev set choose one or a combination. N-grams handle
  fragments and unknown words; a word list is the stronger signal for leetspeak and homoglyphs.
- **Ambiguous inversions (by principle):** return one best guess as the text, with a confidence on
  each recorded step. Rank candidates internally. No list of alternatives in the v1 output.
- **What counts as the original (by principle):** minimal edit. Only characters inside an accepted
  transform change; case, whitespace, punctuation, and accents elsewhere are preserved. So no
  blanket Unicode normalisation of the whole text. Ground truth is the text before obfuscation.
- **Offsets (by principle):** each step records its span in the text as it stood before that step.
  The ordered steps are enough to reconstruct a mapping to the input; we do not compute it in v1.
- **Done criteria (by experiment):** set real targets after the baselines are measured.
  Provisional: at most 1% of clean texts changed; at least 90% exact recovery for lossless
  transforms and encodings; at least 70% for ambiguous visual tricks.

### 2026-10-08 — Dependencies: language data allowed, deobfuscators not
- **Decision:** N-gram and word-list resources may be used as dependencies. Other deobfuscation
  tools or libraries may not; all detection and decoding logic is our own.
- **Supersedes:** "No third-party dependencies" above, for language data only.
- **Confirmed interpretation:** this covers both data files and packages that supply
  n-grams or word lists. Python's standard-library codecs (`base64`, `html`, `urllib.parse`,
  `unicodedata`) are still used, since they are primitives rather than deobfuscators.
- **Consequence:** existing deobfuscators can be read for ideas and compared against as
  baselines in evaluation, but never imported by the tool.

### 2026-10-08 — MIT licence
- **Decision:** MIT.
- **Consequence:** every dependency and every committed data file must be MIT-compatible.

### 2026-10-08 — Process files are kept, generously, and published
- **Decision:** Ship `JOURNAL.md`, `PLAN.md`, `CLAUDE.md`, research notes, and similar files, and
  add more wherever they help.

### 2026-10-08 — Branch stays `master`
- **Decision:** Publish from `master`.

### 2026-10-08 — Candidate sources for real samples (proposed by Claude, to verify in research)
Listed from memory; existence, content, and licence of each must be checked before use.

- **Spam and phishing corpora:** SpamAssassin public corpus, Enron-Spam, SMS Spam Collection.
  Expected tricks: leetspeak, inserted separators, HTML entities, base64 mail parts.
- **Toxic-comment datasets:** e.g. Jigsaw Toxic Comment. Expected: masked profanity, leetspeak,
  repeated characters. Content is abusive.
- **Jailbreak and prompt-injection collections:** in-the-wild prompt datasets. Expected: base64,
  rot13, spacing tricks, stacked encodings.
- **Phishing and lookalike-domain feeds:** e.g. PhishTank. Expected: homoglyphs, mixed script.
- **CTF write-ups and puzzle sites:** nested encodings with known answers.
- **Social media text:** styled Unicode alphabets, zero-width characters, "algospeak".
- **Independent obfuscator tools:** fancy-text generators, leetspeak converters, online encoders.
  Run our own clean sentences through them. Gives known answers, no licence problem, and tricks
  implemented by someone other than us.
- **Mojibake and encoding-bug reports:** issue trackers and forum posts, for accidental mess.
- **Clean negatives:** Wikipedia, public-domain books, READMEs, log files, lists of names,
  product codes, hashes.

Handling rule (confirmed): commit a sample only if its licence clearly allows redistribution.
Otherwise commit a fetch script and the labels, not the text. Abusive content is not committed.

### 2026-10-08 — Publish on PyPI as well as git
- **Decision:** Distribute through PyPI in addition to the public repo.
- **Consequence:** needs a real package name, a filled-in `pyproject.toml`, a build backend, and a
  release process.

### 2026-10-08 — A new name will be chosen
- **Decision:** Replace the placeholder `deobfuscation-6`.
- **Candidates (checked against PyPI on 2026-10-08, all unregistered then):** `deobfuscate`
  (Claude's first choice: says what it does, easiest to find), `textunmask`, `unobscure`,
  `deobtext`. `unveil` and `plainsight` are taken.
- **Caveat:** PyPI can still refuse a name that is too similar to an existing one; only
  registering it settles that.

### 2026-10-08 — Outside contributions are accepted
- **Decision:** Accept contributions from anyone.
- **Approval process (confirmed):**
  - `master` is protected: no direct pushes, changes arrive by pull request.
  - Continuous integration must pass: unit tests plus the evaluation run.
  - Evaluation gate: a pull request may not raise the false-change rate on the clean set, and
    must report its effect on recovery rate.
  - A new or changed transform must come with samples: obfuscated cases it fixes and clean cases
    it must leave alone.
  - Contributed data must state its source and licence; nothing that is not MIT-compatible.
  - At least one maintainer approves before merge. Only maintainers cut releases.
  - Contributions are licensed under MIT (stated in `CONTRIBUTING.md`).
  - Releases to PyPI are built by CI from a version tag, not from a laptop.
  - Supporting files: `CONTRIBUTING.md`, pull-request template, `SECURITY.md`, code of conduct.

### 2026-10-08 — Strictness setting
- **Decision:** The user can choose how aggressive deobfuscation is.
- **Design (confirmed):** three named levels. `conservative` is
  the default: lossless transforms and encodings, high acceptance margin. `balanced` adds the
  ambiguous visual tricks with a high margin. `aggressive` lowers the margin. A level is a preset
  of acceptance margin and enabled transform groups, and the evaluation reports every level.

### 2026-10-08 — Agent-facing documentation (proposed by Claude, done)
- **Decision:** `AGENTS.md` holds the current state of all settled constraints and the working
  rules, so an agent does not have to replay this journal. `CLAUDE.md` imports it.
- **Rule:** when a decision changes, update the journal entry (mark the old one superseded) and
  `AGENTS.md` in the same change.

### 2026-10-08 — All outstanding proposals confirmed
- **Decision:** The user accepted every proposal then open: the design proposals, packages allowed
  for n-grams and word lists, the sample handling rule, the contribution approval process, and
  the three strictness levels. Also:
  - **The obfuscator ships** as part of the evaluation tooling.
  - **Versioning:** 0.x; the result format may change until 1.0.
  - **Non-English input** is detected and returned unchanged.

### 2026-10-08 — Name: `deobfuscate`
- **Decision:** Project, PyPI package, and import name are `deobfuscate`. The user delegated the
  choice to Claude.
- **Why:** says what it does and is the easiest to find.
- **Checked on 2026-10-08:** not registered on PyPI; `lapid/deobfuscate` does not exist on GitHub.
- **Fallback if PyPI refuses the name:** `textunmask`.
- **Not renamed:** the local folder `deobfuscation-6`.

### 2026-10-08 — Hosting: GitHub, personal account `lapid`
- **Decision:** The repo will be `github.com/lapid/deobfuscate`.
- **Not yet done:** the repo has not been created and nothing has been pushed.

### 2026-10-08 — Owners: Lapid Harel and the LLM agent (confirmed)
- **Decision:** Lapid Harel is the sole human maintainer, the copyright holder named in `LICENSE`,
  and the owner of the GitHub repo and the PyPI project. The only two working on the project as
  owners are Lapid and the LLM coding agent.
- **Claude's interpretation:** the agent may commit and push to `master` as part of work Lapid
  asks for. Outside contributors go through the pull-request approval process, and Lapid approves.
- **Known tension:** "one maintainer approval" cannot apply to the owners' own changes; those are
  gated by the automated checks once they exist.

### 2026-10-08 — Public GitHub repo created
- **Decision:** `github.com/lapid/deobfuscate` is public from the first commit, at the user's
  request.
- **Rejected:** Claude's suggestion to start private until the first release.
- **Consequence:** the "safe to publish" rule applies to every commit from now on, not only at release.

### 2026-10-08 — Research phase done; findings in `docs/research/`
- **Decision:** Phase 0.5 is closed apart from the sample-collection items left open in `PLAN.md`.
  Conclusions are in `docs/research/README.md`; the taxonomy is in `docs/taxonomy.md`.
- **Confirmed by research:** the planned "transforms propose, scorer disposes, depth limit"
  engine is what Ciphey and CyberChef do; preserving case and leaving non-Latin text alone is
  supported by a benchmark.

### 2026-10-08 — Homoglyph map: a subset of Unicode `confusables.txt` (decided by Claude from research)
- **Decision:** Vendor `confusables.txt` (Unicode License V3) and build our map from the entries
  that go from a non-ASCII character to ASCII. Never apply an entry with an ASCII source.
- **Why:** the table is made for comparing strings. Applied directly it turns `m` into `rn` and
  `1` into `l` in clean English.
- **Rejected:** Unicode NFKC alone; it covers under half of those entries and no cross-script lookalikes.

### 2026-10-08 — Scorer data: SCOWL word list plus our own n-gram table (decided by Claude from research)
- **Decision:** Ship a word list generated from SCOWL (MIT-like licence, notice kept). Build the
  character n-gram table ourselves from public-domain English text.
- **Rejected:** `wordfreq` (data is CC BY-SA 4.0, project frozen, three extra packages);
  Norvig's n-gram files (no licence stated for the data).
- **Open:** which public-domain corpus.
- **Resolves:** open question "scorer data source", except the corpus.

### 2026-10-08 — Text-message shorthand is not obfuscation (confirmed)
- **Decision:** `l8r`, `sum1`, `4` for "for" and similar are left unchanged, and they join the
  clean set as hard negatives.
- **Why:** real messages are full of them; the digits stand for sounds, so visual leetspeak rules
  give wrong words. Expanding them would be rewriting, not deobfuscating.
- **Consequence:** leetspeak decoding fires only when the result is a known word.

### 2026-10-08 — Evaluation reports by text length (decided by Claude from research)
- **Decision:** every metric is also broken down by input length, and the engine may decline to
  judge short spans.
- **Why:** both Ciphey and CyberChef state their plausibility checks fail on short text.

### 2026-10-08 — Third-party data is licensed separately
- **Decision:** files in `data/reference/` and `data/samples/sms_spam_collection.jsonl` keep
  their own licences (Unicode License V3, CC BY 4.0) and credits. The MIT licence covers our own work.
- **Note:** this reads "MIT-compatible" as "may be redistributed alongside MIT code with its
  notice", not "relicensed as MIT".

### 2026-10-08 — Hidden text in invisible characters is removed and reported (confirmed)
- **Decision:** Text carried by invisible characters (Unicode tag characters and similar) is
  removed from the output text, and the hidden content is shown in the step record.
- **Why:** the visible text is what the author's reader saw, so that is the output; but silently
  dropping a hidden message would discard the most interesting fact about the input.
- **Rejected:** removing silently; inserting the hidden text into the output.

### 2026-10-08 — Wrong-encoding damage is out of v1 (confirmed)
- **Decision:** Repairing text decoded with the wrong character encoding (`Ã©` for `é`) is not in v1.
- **Why:** a large separate problem that dedicated tools already handle.
- **Consequence:** such text is a clean negative: it must come back unchanged, not be made worse.

### 2026-10-08 — Evaluation harness built (Phase 1)
- **Decision:** The harness lives in `evaluation/` in the repo and is not part of the installed
  package. `docs/evaluation.md` explains the sets, the measures and the commands.
- **Baselines on dev:** returning the input changes 0% of clean texts and recovers 0%. Unicode
  NFKC changes 0.5% of clean texts (mostly legitimate symbols) and recovers 11.7% at conservative.
- **Still missing:** a real-world set. All obfuscated samples are synthetic.

### 2026-10-08 — Clean corpus: public-domain books, different books per split (decided by Claude)
- **Decision:** 2,000 texts per split from five Project Gutenberg books each, all published
  before 1929. Dev and test share no book.
- **Why:** public domain, so the sets can be committed; splitting by book prevents an author's
  phrasing leaking from dev into test.
- **Accepted cost:** the prose is old and formal. Modern informal text is under-represented.
- **Consequence:** the scorer's n-gram table must be built from other books than these ten, or
  the scorer will have seen the evaluation text.
- **Rejected:** Wikipedia (share-alike licence). Reversed the same day; see "Clean corpus widened".

### 2026-10-08 — Transform names are a shared contract (decided by Claude)
- **Decision:** the names in `evaluation/tricks.py` are used for sample labels, the obfuscator,
  and `Step.transform`. A sample counts at a strictness level when all its tricks are handled at
  that level or below.
- **Why:** per-transform precision and recall compare the step record with the tricks used, so
  the names must match exactly.

### 2026-10-08 — Tests use the standard library `unittest` (decided by Claude)
- **Decision:** no test framework dependency.
- **Why:** keeps the project dependency-free for contributors; the tests are simple.

### 2026-10-08 — Layout: `src/deobfuscate`, `uv_build` backend (decided by Claude)
- **Decision:** the package is under `src/`, built with `uv_build`; `main.py` is removed. The
  `deobfuscate` command reads an argument or standard input.
- **State:** `deobfuscate()` has the final signature and result types but no transforms; it
  returns its input unchanged.

### 2026-10-08 — Share-alike data is allowed in the repo (confirmed)
- **Decision:** CC BY-SA and CC BY data files may be committed alongside the MIT code. Each row
  carries its own source, address and licence; `data/eval/README.md` states the terms.
- **Why:** needed for modern, varied text. Third-party data already keeps its own licence.
- **Consequence:** obfuscated versions of such texts are adaptations under the same licence.
  The MIT licence covers code and our own generated data only.
- **Supersedes:** Claude's earlier rejection of Wikipedia.

### 2026-10-08 — Clean corpus widened to five real sources (confirmed approach; details by Claude)
- **Decision:** per split, 2,000 texts from Wikipedia, 1,500 from Stack Exchange questions,
  1,500 personal text messages, 1,000 from Wikinews, 1,000 from the books. Dev and test share no
  document and no text.
- **Why:** the first corpus was 82% formal prose from before 1929; false changes on modern text
  were unmeasured.
- **Licences checked:** Wikipedia and Wikinews from their own copyright pages; Stack Exchange
  from the licence the API reports for each post (its licensing page could not be fetched); the
  SMS collection from its dataset page.
- **Rejected:** Reddit (no open licence, terms restrict reuse); mainstream news (copyrighted).
  Wikinews stands in for news, Stack Exchange and text messages for informal writing.
- **Details decided by Claude:**
  - Only personal messages from the SMS collection, not the spam, to keep adult spam out.
  - Texts containing invisible or control characters are dropped as doubtful labels.
  - Real messages containing HTML entities become real obfuscated samples, with the decoded
    text as the expected output.
  - Wikinews articles from 2005 and 2024 are skipped because the licence changed in those years.
- **Result:** NFKC baseline on dev changes 0.3% of clean texts (24 of 7,442) and recovers 11.6%
  at conservative.
- **Accepted cost:** `data/eval/` is about 18 MB.

### 2026-10-08 — BitCore used as a local-only real-world set (confirmed, with a caveat)
- **Decision:** Download BitCore by script and evaluate on it locally. It is never committed.
- **What it is:** 26,591 real sentences from phishing emails, disguised by their senders, each
  with the restored text. From Lee et al., "BitAbuse", Findings of NAACL 2025.
- **Caveat told to the user:** it is public and free to download, but states no licence, so no
  permission to use or redistribute is written down. The user's go-ahead was conditional on it
  being "open and free to use"; Claude proceeded on the local-only reading and reported this.
- **Details decided by Claude:** 3,000 sentences per split; all versions of a sentence go to one
  split; compared ignoring case because the answers are lowercased; counted from `balanced` up;
  the 100 rows seen while writing the loader are dev-only.
- **Not done:** asking the authors to add a licence.

### 2026-10-08 — New trick: accent substitution (decided by Claude from real data)
- **Decision:** `accent-substitution` (`yōũr`, `taĺk`) joins the taxonomy at `balanced`, and the
  generator and evaluation sets include it. Greek lowercase lookalikes are added to the generator.
- **Why:** 44% of real phishing sentences in BitCore's dev half use accented Latin letters, and
  47% use Greek letters. Neither was generated before.
- **Tension:** this collides with "real accents stay". It must be decided per word: remove an
  accent only when the word is not a known word with it and is one without it.
- **Consequence:** the obfuscated sets were rebuilt, so earlier sample ids no longer match.

### 2026-10-08 — Hand-disguised sentences (confirmed in principle)
- **Decision:** the user will disguise sentences supplied by Claude. 50 are in
  `data/human/to_disguise.txt`. The pairs will be MIT-licensed and committed.

### 2026-10-08 — Hand-disguised set added (details decided by Claude)
- **Decision:** the owner's 50 disguised sentences are split by sentence number into 25 dev and
  22 test samples (3 were dropped as unchanged or blank) and committed under MIT.
- **Discipline:** the agent read only the dev half. The sheet itself contains both halves, so
  agents are told not to read its answers.
- **Corrections:** answers 12 and 21 sat under the wrong sentence and are re-paired with the
  sentence they disguise. An answer that was only indented is treated as unchanged.
- **Finding:** several disguises are out of scope by our rules (misspelling, shorthand, emoji).
  They stay in the set; character error, now reported per origin, is the measure to read there.
- **Open:** whether the tool should ever attempt those (it would mean spelling correction).
  Resolved below: not in v1.

### 2026-10-08 — No spelling correction, shorthand expansion or emoji-to-word in v1 (confirmed)
- **Decision:** the tool does not try to undo misspellings, dropped letters, shorthand, or emoji
  standing for a word.
- **Why:** it would require spelling correction, a larger and riskier feature that rewrites the
  author's words and would raise the false-change rate.
- **Accepted cost:** exact recovery on the hand-disguised set has a ceiling below 100%.

### 2026-10-08 — Remaining evaluation gaps move to version 2 (confirmed)
- **Decision:** the evaluation set is good enough to build v1 against. The remaining gaps are
  listed under "Version 2" in `PLAN.md` and are not worked on before v1 is released.
- **Known cost for v1:** recovery numbers for encodings rest on synthetic samples only.

### 2026-10-08 — Version 2 idea: a public demo site that collects samples (proposed by the user)
- **Idea:** host a site on Netlify or Render where people try the tool, and collect what they
  submit as evaluation samples.
- **Why:** it is the most promising source of real obfuscation across genres, including encodings.
- **Conditions noted by Claude, to settle in v2:** opt-in consent and a licence for submissions;
  a way to get the correct answer from the visitor, since text without an answer is not a sample;
  screening for personal data and abuse before anything is published; the sample will be biased
  toward odd cases.

### 2026-10-08 — Core engine built (Phase 2; design decided by Claude)
- **Decision:** transforms only propose replacements; the engine judges every proposal with the
  plausibility scorer and applies the best one, repeating until nothing is accepted.
- **Layers by recursion:** before judging, the engine deobfuscates the replacement itself, up to
  4 layers deep, and judges the final result.
  - **Why:** the first decode of layered text (base64 inside base64) is not English, so judging
    it directly would reject it.
  - **Rejected:** a separate search over chains of decoders; the recursion gives the same result
    with one mechanism.
- **Result on dev, conservative:** 0 of 7,442 clean texts changed; whole-text base64 94%
  recovered, base64 in base64 96%, rot13 over base64 98%, whole-text rot13 90%.
- **Known problem:** at `balanced` and `aggressive` the starting presets let rot13 change clean
  texts (4 and 20 of 7,442). To be tuned in Phase 4.

### 2026-10-08 — Scorer: word coverage and four-letter sequence fit, averaged (decided by experiment)
- **Decision:** use both signals with equal weight. Details and numbers in `docs/scorer.md`.
- **Why:** on dev, each separates clean text from wrong decodes almost perfectly from 20
  characters up; the combination is never worse than either; under 20 characters neither is
  reliable, which is handled by requiring a minimum number of letters.
- **Data:** SCOWL 2020.12.07 at size 60 for the word list; four-gram counts from twenty
  public-domain books that are not in the evaluation corpus.
- **Resolves:** the open questions on the public-domain corpus and on resource limits (100,000
  characters, 4 layers, 200 replacements).

### 2026-10-08 — Step-record names: `base64url` is reported as `base64` (decided by Claude)
- **Decision:** the tool reports both alphabets as `base64`; the evaluation treats the two
  labels as one when scoring the step record.
- **Why:** many URL-safe strings contain neither `-` nor `_` and cannot be told apart.

### 2026-10-09 — `AGENTS.md` is the entry point and carries the status (confirmed need; layout by Claude)
- **Decision:** `AGENTS.md` now opens with reading order, current status, how we work with the
  owner, and a table saying what each document is for and when to update it.
- **Why:** a new agent session had the rules but no recap of where the project stands or which
  document to update for which kind of change.
- **Rule:** "Current status" is refreshed at the end of every piece of work.

### 2026-10-09 — Phase 3, first two groups: fourteen conservative transforms (details by Claude)
- **Result on dev, conservative:** 1 of 7,442 clean texts changed; 95.5% of obfuscated texts
  recovered; 0.1% made worse. Details in `docs/evaluation.md`.
- **Engine changes this forced:**
  - **Certain transforms run first.** A Caesar shift was being applied to words still split by
    invisible characters, then undone by a second shift, leaving junk in the step record.
  - **Proposals are ranked by gain times letters,** not gain alone. A reversed part of a text was
    beating the reversal of the whole text.
  - **One-letter words are not evidence.** Hex written as `0x41 0x73` was "shifted" into a text
    of the letters `a` and `i`, which scored as English.
  - **Minimum score lowered** from 0.70 to 0.50 at conservative: correct decodes full of names
    were being rejected. The gain requirement still guards clean text.
  - **Caesar shifts and reversal need 10 letters at every level.**
- **Guards chosen for the certain transforms:** see the table in `docs/architecture.md`.
- **Accepted false change:** a sentence that mentions HTML entities gets them decoded. Real text
  messages contain bare entities (136 in dev, all recovered) far more often than text discusses them.
- **Rejected:** judging HTML entities and URL escapes with the scorer; decoding `&amp;` to `&`
  does not change how English a text looks, so the scorer cannot decide it.

### 2026-10-09 — Lookalike letters and accent substitution (order confirmed; design by Claude)
- **Decision:** both are decided by the transform itself, one word at a time, not by the scorer.
  A word is rewritten when it is not English as written and its plain-letter reading is, with
  extra evidence required for the cases that look like correct foreign spelling. The rule table
  is in `docs/architecture.md`.
- **Why not the scorer:** it needs about 20 characters to be reliable; this is one word.
- **Result on dev:** real phishing set 0% to 57.1% exact at `balanced` with 1 of 7,442 clean
  texts changed (the same one as before); 85.4% at `aggressive` with 9 changed.
- **Strict versus loose:** a lone word with everyday accents (`õn`, `coupé`) and a lone Greek
  `α` for "a" cannot be told from correct spelling. `balanced` leaves them; `aggressive`
  rewrites them when the surrounding text is clearly English.
  - **Rejected:** rewriting them at `balanced`. It reached 70% on the phishing set and changed
    14 clean texts, including `résumé`, `façade` and French and Swedish sentences.
- **Word list:** accented spellings from SCOWL sizes 70 and 80 were added, so a correctly
  accented word that SCOWL knows is not treated as a disguise. Few such entries exist.
- **Loose resemblances:** a hand list of about 35 letters (`τ` for t, `η` for n) was written
  from the substitutions seen in the dev half of the real phishing set. Only the letter pairs
  were taken from that data, not its text.
- **Presets:** `balanced` now uses the same thresholds as `conservative`; the looser values let
  a Caesar shift rewrite a line of romanised Chinese.

### 2026-10-11 — Combining marks, and applying a transform's proposals together (decided by Claude)
- **Combining marks:** decided by the transform, word by word, like the lookalikes. Marks are
  removed from a word when a letter carries three or more, when two or more letters carry a mark
  no alphabet spells with and the plain word is English, or when every letter of a word of three
  or more letters carries one. Other marked words (one-letter words, names) follow only if some
  word in the text qualified.
  - **Why not "strip every mark":** decomposed accents (`e` plus an acute), Vietnamese (two
    marks on a letter) and phonetic notation are ordinary text. The clean set contains all three.
  - **Rejected:** treating any known word with one odd mark as disguised. A unit test showed it
    removed the tie from phonetic `t͡s`, because "ts" is in the word list.
- **Engine change:** all proposals of one certain (`judged = False`) transform are applied in
  the same round, instead of the single largest.
  - **Why:** lookalike and combining-mark rules count evidence over the whole text. Applied one
    word at a time, the strong words were rewritten first and the weak ones (a lone "a", a name)
    then had no evidence left. This was a bug in the 2026-10-09 result, which Claude had wrongly
    put down to the generator disguising short words too often.
  - **Effect on dev at `balanced`:** real phishing set 57.1% to 81.0%; synthetic homoglyph 63%
    to 93%; accent substitution 40% to 74%. Clean texts changed: still 1 of 7,442.
  - Step offsets are unchanged in meaning: each is the span in the text as it stood before
    that step.
- **Result on dev:** combining marks 96.7% whole text, 98.3% inside clean text. Clean texts
  changed 1, 1 and 9 of 7,442 at the three levels, as before.
- **Correction:** the strictness table in `docs/architecture.md` showed the old thresholds; it
  now matches the code.

### 2026-10-12 — Leetspeak (decided by Claude)
- **Decision:** decided by the transform, token by token. A token is rewritten only when every
  digit and symbol in it reads as a letter and the result is a known word. The rule table is in
  `docs/architecture.md`.
- **Characters read:** `0 1 3 4 5 7 @ $ !`. Not `8` or `2`: they stand for a sound (`l8r`,
  `2day`), which the settled constraints call shorthand. Leaving them out keeps the whole
  shorthand family untouched without a list of exceptions.
- **Shapes that need evidence or are never touched:** found from the clean dev set, which holds
  `test5`-like identifiers, `8am`, `1st`, `$5m`, `G5`, `M14`, `b4`, handles and `print$`.
  - **Tried and pulled back:** letting one rewritten token be enough evidence for any short
    token. It changed 3 more clean texts (`b4` to "ba", `G5` to "Gs", `M14` to "Mia"). One or
    two letters followed by a number are now never read; with that guard, one token of evidence
    is enough for the other short shapes and the clean set is back to 1 of 7,442.
- **Lookalike letters joined to digits:** `lookalike.py` now asks `leet.py` whether the whole
  token is a known word once both are read. Layered homoglyph and leetspeak: 32% to 60%.
- **Result on dev at `balanced`:** leetspeak 76.0% whole text, 86.7% inside clean text; all
  obfuscated samples 81.2% to 85.4%; clean texts changed still 1, 1 and 9 of 7,442.
- **Known limit:** a capital hidden behind a digit is not recoverable except at the start of a
  sentence or for a word known only as a name.

### 2026-10-12 — Separators and repeated letters; Phase 3 transforms complete (decided by Claude)
- **Separators:** decided by the transform, run by run; letters are joined only when they spell
  known words. Rule table in `docs/architecture.md`.
  - The first version changed 4 clean texts: `a.k.a.` and `a.s.a.p.` (in the word list as "aka"
    and "asap"), and two spaced-out headings in capitals. Dotted runs followed by a dot, and all
    capitals, now need another run in the text as evidence; a whole spaced-out text in capitals
    is left alone. Clean set back to 1 of 7,442.
  - **Cost accepted:** spaced-out spam written wholly in capitals is not recovered.
- **Repeated letters (`aggressive` only):** a run of three or more is cut to two or one,
  whichever is a known word; the four-gram table picks between two valid readings (`theee` is
  "the", not "thee").
  - **Tried:** rewriting every stretched word: 88% recovered but 26 to 40 clean texts changed,
    nearly all emphasis in text messages (`Hmmm`, `sooooo`). Requiring two stretched words in
    every case: 12 clean texts changed but only 20% recovered inside clean text.
  - **Chosen:** a lone stretched word is cut back only if the result has five letters or more.
    12 clean texts changed (3 more than before); 86.7% whole text, 68.3% inside clean text.
- **Result on dev:** clean texts changed 1, 1 and 12 of 7,442; all obfuscated samples 95.5%,
  87.7% and 90.9% at the three levels; real phishing set 81.1% and 89.5%; hand-disguised 7 of 25.

### 2026-10-12 — Shorthand, misspellings and emoji-for-words join version 1 (confirmed by the owner)
- **Decision (owner):** version 1 includes "some misspellings, emojis and shorthand".
  - **Supersedes** the settled constraints "No spelling correction in v1" and "Shorthand is not
    obfuscation", and the matching rows under "Out of scope" in `docs/taxonomy.md`.
- **Level (owner, from Claude's recommendation):** `aggressive` only. At `conservative` and
  `balanced` this writing still comes back unchanged, so the default behaviour and the headline
  metric are unaffected.
- **Breadth of misspelling correction (owner):** "even narrower" than Claude's narrow proposal:
  "common spelling mistakes and common typing mistakes".
  - **Claude's reading of that:** a hand-written list of about 130 common misspellings and
    missing apostrophes, plus two typing slips (neighbouring letters swapped, a letter doubled)
    in words of six letters or more when exactly one known word results. Dropped letters and
    wrong keys are not corrected. The owner may widen or narrow this.
- **Design (Claude):** three transforms, each with its own short list, marked `late`: the engine
  asks them only when no other transform has anything left, and only on the whole text.
  - **Why last:** found by the evaluation. Run with the others, `shorthand` turned `ur` inside
    rot13 text into "your", and turned the lone `u` decoded from `&#117;` inside "Buttons" into
    "you". Both are fixed by the ordering and covered by a unit test.
- **Wrong rewrites found on dev and fixed:** `frens` to "ferns", `betta` to "beta", `immed` to
  "mimed" (typing slips now need six letters); `militaries` to "militarise" (regular endings of
  known words are now treated as words); the name `Ty` to "Thank you" (read only as `TY`).
- **Left as is:** `waggon` to "wagon" in old books (3 clean texts).

### 2026-10-12 — Evaluation: capitals ignored, informal text scored separately (owner and Claude)
- **Capitals (owner):** recovery is measured ignoring capital letters. The strict count is still
  printed. Clean texts changed stays strict: changing a capital in clean text is a change.
- **New samples (Claude):** 150 whole-text and 60 partial samples per split for each of the three
  informal tricks, appended from their own random stream so that no existing row changed
  (checked: 630 added, 0 removed, in each split).
- **Clean informal text (Claude):** a clean text message, or a shorthand or emoji sample, changed
  only by the three informal transforms is reported as "rewritten on purpose", not as a clean
  text changed. In proofread sources and Stack Exchange it still counts as a change.
- **Real answers that keep shorthand (Claude):** the phishing set's answers keep `u`. An output
  is also accepted if it equals the answer as the tool's informal transforms alone would rewrite
  it. Without this, writing out "you" counted as making the text worse.
- **Not done:** no check of these rules against data the rule-writer has not seen; that is the
  test split's job in Phase 4.

### 2026-10-12 — Phase 4 started: error analysis and thresholds (owner started it; details by Claude)
- **Owner:** go ahead with Claude's recommendation (error analysis on the hand-disguised dev
  sentences first, then thresholds, then one test run), and make sure the thresholds and the
  test set are in the plan. `PLAN.md` Phase 4 now lists the sweep, the freeze and the test run
  step by step.
- **Hand-disguised dev sentences, 7 to 15 of 25 at `balanced` (Claude):** eight failures had
  one cause, words mixing lookalike and accented letters.
  - Roman-numeral characters (`ⅼ`, `ⅴ`, `ⅿ`) were dropped when the lookalike table was built.
    Now read as letters, only inside a word that becomes a known word.
  - A Cyrillic letter with a hook or stroke (`ӷ`, `ҫ`, `ҟ`) reads as the letter without.
  - About twenty letters are read as seen in the dev sentences (`ƅ` b, `ϝ` f, Armenian `ր` n),
    some with two readings (`þ` p or b); the first that gives a known word is used.
    **Risk:** this list was learned from 25 sentences by one author. The test half will show
    whether it carries over.
  - Four symbols count as letters inside a word (`¢`, `₫`, `∨`, `¡`), known words only.
    `µm`, `5¢` and Spanish `¡Hola!` stay; covered by unit tests.
- **Engine: transforms may share a `group` (Claude).** The two lookalike tricks decide on the
  same evidence but were applied in separate rounds, so accent words lost the lookalike words
  as evidence. Grouped transforms are applied in the same round. Real phishing set at
  `balanced`: 81.1% to 89.5% from this and the readings above.
- **Lookalike, smaller changes (Claude):** disguised words that read as English count towards
  "the text is English" (a text with one plain word, a name, was skipped); `’` inside a word.
- **Tried and dropped:** two capitalised words with odd accents as evidence for each other.
  It recovered 5 more samples and changed two Vietnamese names in a clean text.
- **Leetspeak (Claude):** two small letters and a doubled `3` or `0` are read (`fr33`); other
  two-letter stems before a number are still never read (`G5`, `b4`).
- **Shorthand (Claude):** a form written in capitals comes back capitalised, not in capitals
  (`TY` to "Thank you"), unless the whole text is in capitals.
- **Reversal inside clean text, 28% to 42% (Claude):** a run may continue across a word that
  reads both ways (`eht no detubed`). Such a run needs 12 letters, after it reversed two
  misspelt words around "is" in a real message, and is not tried when the whole text may be
  reversed. Words that read both ways at the ends of a run still cannot be placed.
- **Caesar (Claude):** a span where more than a tenth of the letters are accented is not
  shifted. Found reading the clean texts changed at `aggressive`: a pinyin phrase was shifted.
- **Thresholds (Claude, by sweep on dev; table in `docs/evaluation.md`):**
  - Recovery moves by about one point across the whole swept range. The rules decide, not the
    margins.
  - `min_letters` 10 to 8 at `conservative` and `balanced`: 13 more recovered at each, no clean
    text changed, nothing made worse. `min_score` and `min_gain` unchanged.
  - `aggressive` unchanged. A score of 0.50 would change one clean text fewer and recover four
    fewer; kept at 0.45 because the level exists to accept more.
  - Per-transform: leetspeak reads an unknown name after 2 clear words instead of 3 (12 more
    recovered, no clean change). `reverse`, `caesar`, `repeated-chars` and `misspelling` limits
    kept; each lower value changed one more clean text.
- **Known and not fixed:** "No pasa nada" is reversed at every level: all three words read as
  English backwards. No guard separates it from real reversed text; recorded as a known problem.
- **Dev results after all of this:** clean texts changed 1, 1, 24; recovered 96.1%, 92.3%,
  90.0%; made worse 2, 2, 17; real phishing set 90.8% and 94.5%; hand-disguised 15 and 17 of 25.
- **Frozen (Claude):** no rule or threshold changes until the test run. The run needs the
  owner's go-ahead and, if the owner wants, their check of the test-half answers first.

### 2026-10-12 — The test split was run, once (owner's go-ahead)
- **Owner:** run it as it is, without checking the test-half answers of the hand-disguised
  sheet. The owner will also run a further set the agent has never seen.
- **Run at commit `eb26b8b`**, rules and thresholds frozen. No test sample was read.
- **Results (test / dev):** clean texts changed 3, 13, 38 / 1, 1, 24 of 7,442; recovered 96.6%,
  91.3%, 88.9% / 96.1%, 92.3%, 90.0%; real phishing set 88.6%, 92.1% / 90.8%, 94.5%;
  hand-disguised 5 of 22 at both levels / 15 and 17 of 25.
- **Reading (Claude):** recovery carries over. Clean texts changed does not: the dev clean set
  was tuned until almost nothing changed, so its figure was optimistic. The test figures are
  the ones to quote; all are under the 1% target. The hand-disguised sentences did not carry
  over, which is the risk recorded in the previous entry.
- **Nothing was fixed in response**, as planned. The cause of the 13 clean texts changed at
  `balanced` is unknown because finding it means reading test samples. Left to the owner.
- **The test split is no longer unseen.** Later changes are judged on dev.
- **Provisional targets:** met, except accent substitution inside clean text (58% against 70%).

## Open questions

None needing an answer from the user.

Settled later by experiment:

1. **Final v1 targets:** after the test run. On dev the provisional targets are met (clean
   texts changed under 1% at every level; encodings 96%; most visual tricks above 70%).
