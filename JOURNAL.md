# Decision journal

Running log of goals and decisions for the text deobfuscator. Newest entries at the bottom.
Each decision records what we chose, why, and what we rejected.

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

### 2026-10-08 — Text-message shorthand is not obfuscation (decided by Claude from research, to confirm)
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

## Open questions

Needs an answer:

1. **Hidden text in invisible characters** (Unicode tag characters and similar): remove it
   silently, or reveal the hidden text in the output or the record? Proposed: remove from the
   text and show the hidden content in the step record.
2. **Wrong-encoding damage** (`Ã©` for `é`): in scope as accidental mess, or out? Proposed: out
   of v1; it is a large separate problem that existing tools handle.
3. **Shorthand left alone:** confirm the entry above.

Settled later by experiment:

4. **Public-domain corpus** for the n-gram table.
5. **Resource limits:** maximum input size and nesting depth.
6. **Final v1 targets:** after baselines are measured.
