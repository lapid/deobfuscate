# Evaluation

How the deobfuscator is measured. Build this understanding before changing a transform:
a change is kept only if the clean set stays clean.

## Commands

Run from the repository root.

| Command | What it does |
|---|---|
| `uv run python -m evaluation.run` | Scores the deobfuscator at all three strictness levels on the dev split |
| `uv run python -m evaluation.run --detail` | Adds tables per category, per trick, and for the step record |
| `uv run python -m evaluation.run --system identity` | Scores a baseline (`identity` or `nfkc`) |
| `uv run python -m evaluation.run --split test` | Scores on the test split. For reporting only |
| `uv run python -m unittest discover -s tests` | Unit tests |
| `uv run python -m evaluation.local_sets` | Downloads and builds the local-only real-world set (BitCore). Needs network |
| `uv run python -m evaluation.build` | Rebuilds the sets from the corpus. Output is identical for the same seed |
| `uv run python -m evaluation.corpus` | Re-downloads the books and rebuilds the corpus |

## The sets

Each split has two files in `data/eval/<split>/`.

- **`clean.jsonl`** (7,442 texts): must come back unchanged.
  - 7,000 real texts: 2,000 from Wikipedia, 1,500 from Stack Exchange questions, 1,500 personal
    text messages, 1,000 from Wikinews, 1,000 from public-domain books.
  - 442 generated hard negatives in 21 categories such as hashes, tokens, URLs, paths, code,
    other languages, shorthand and spaced headings.
- **`obfuscated.jsonl`** (about 5,910 texts): a trick applied to corpus text, with the original
  as `expected`. Four kinds:
  - **whole:** one trick over the whole text, 150 per trick.
  - **partial:** one trick on a run of words inside clean text, 60 per trick.
  - **stacked:** two tricks layered, 50 for each of 16 recipes.
  - **real:** about 135 real text messages containing HTML entities. The only samples not made
    by our generator.

Dev and test never share a document or a text: books are assigned by title, the rest by a hash
of the document address. Sources, licences and credits are in `data/eval/README.md`. The
generator is `evaluation/obfuscator.py`; the hard negatives are in `evaluation/negatives.py`.

Every result is also reported by origin, so a problem confined to one kind of text is visible.

### Hand-disguised set

`data/eval/human_<split>.jsonl` holds sentences written for this project and disguised by hand
by the project owner: 25 in dev, 22 in test, MIT-licensed. They are built from
`data/human/to_disguise.txt` by `uv run python -m evaluation.human` and split by sentence number.
The tricks are not labelled and the samples count from `balanced` up. Several use disguises that
are out of scope or covered only narrowly (misspelling, shorthand, emoji, symbol pictures), so
read the character error for this origin as well as exact recovery. With so few samples, one sentence is 4 points.

### Local-only real-world set

`data/local/bitcore_<split>.jsonl` holds 3,000 real sentences per split from phishing emails,
disguised by their senders, with the restored text from the dataset's authors (BitCore, Lee et
al. 2025). The dataset states no licence, so it is downloaded by script and never committed;
`data/local/` is git-ignored. The runner includes it when present and says so when it is not.

- Every version of a sentence goes to the same split, because the same sentence was sent many
  times with different disguises.
- The answers are lowercased by the dataset's authors, so these samples are compared ignoring case.
- The tricks used are not labelled. The samples count from the `balanced` level up and are left
  out of the step-record precision and recall.

## The measures

- **Clean texts changed:** share of the clean set whose output differs from the input. The
  headline number. Target: at most 1%.
- **Obfuscated texts recovered:** output equals the original, ignoring capital letters (decided
  2026-10-12: a capital hidden by a disguise is often not recoverable, and a reader loses nothing).
  The strict count, "with every capital letter right", is printed under it. An answer from a real
  message that keeps its shorthand (`u`) is also met by the written-out form (`you`).
- **Informal clean texts rewritten on purpose:** clean text messages and shorthand or emoji
  samples changed only by `shorthand`, `misspelling` or `emoji-word`. That is what those
  transforms are for, so these are not counted as clean texts changed. In every other clean text
  (Wikipedia, news, books, Stack Exchange) such a rewrite does count as a change.
- **Obfuscated texts made worse:** output is further from the original than the input was.
- **Mean character error:** edit distance to the original divided by its length, capped at 100%
  per text, before and after.
- **Above this level:** samples whose tricks need a higher strictness level. Leaving them alone
  is correct, so they are counted apart; the "worse" number still matters.
- **Same result when run twice:** running the output through again changes nothing.
- **Step record:** for each transform name, precision (when it was reported, was that trick
  really used?) and recall (when the trick was used, was it reported?).
- All of these are also split by text length, because scorers are weakest on short text.

A sample counts for a strictness level when every trick in it is handled at that level or
below (`evaluation/tricks.py`).

## Baselines on the dev split (2026-10-08)

Committed sets:

| System | Scored at | Clean texts changed | Recovered exactly | Made worse |
|---|---|---|---|---|
| Return the input | any level | 0.0% (0/7442) | 0.0% | 0.0% |
| Unicode NFKC | conservative | 0.3% (24/7442) | 11.6% (420/3625) | 0.1% |
| Unicode NFKC | balanced | 0.3% (24/7442) | 8.3% (420/5074) | 0.1% |
| Unicode NFKC | aggressive | 0.3% (24/7442) | 7.9% (420/5284) | 0.1% |

Local-only real-world set (BitCore, 3,000 sentences): both baselines recover 0.0%.
Hand-disguised set (25 sentences): both baselines recover 0.0%.

NFKC recovers only the styled-alphabet and fullwidth samples, and nothing stacked or real. Its
false changes are spread over every real source (16 of 7,000 real texts) and hit 5 of the 7
texts in the `symbols` category, which is why the tool does not normalise whole texts.

The deobfuscator itself has no transforms yet and scores the same as "return the input".

## Current results on the dev split (2026-10-12, after the Phase 4 error analysis and sweep)

All twenty-three transforms are built and the thresholds are chosen. The test split has not been
run. Recovery ignores capital letters (see "The measures").

| Scored at | Clean texts changed | Recovered | With every capital right | Made worse | Real phishing set | Hand-disguised |
|---|---|---|---|---|---|---|
| conservative | 0.01% (1/7442) | 96.1% (3482/3625) | 96.1% | 0.1% (2/3625) | not at this level | not at this level |
| balanced | 0.01% (1/7442) | 92.3% (7474/8099) | 92.0% | 0.0% (2/8099) | 90.8% (2725/3000) | 15 of 25 |
| aggressive | 0.32% (24/7442) | 90.0% (8046/8939) | 89.3% | 0.2% (17/8939) | 94.5% (2834/3000) | 17 of 25 |

Before Phase 4 the same table read: recovered 95.5%, 88.0% and 87.9%; real phishing set 81.1% and
89.5%; hand-disguised 7 and 9 of 25; clean texts changed 1, 1 and 26.

On the real phishing set the mean character error falls from 20.4% to 0.6% at `balanced` and to
0.1% at `aggressive`.

By trick, whole text and inside clean text:

| Trick | Level | Whole text | Inside clean text |
|---|---|---|---|
| homoglyph | balanced | 94.7% | 93.3% |
| accent substitution | balanced | 76.5% | 61.7% |
| combining marks | balanced | 96.7% | 98.3% |
| leetspeak | balanced | 86.7% | 90.0% |
| separators | balanced | 87.3% | 85.0% |
| reversal | conservative | 95.3% | 41.7% |
| Caesar shift | conservative | 96.0% | 65.0% |
| rot13 | conservative | 94.7% | 68.3% |
| repeated letters | aggressive | 86.7% | 68.3% |
| misspelling | aggressive | 54.0% | 50.0% |
| emoji for a word | aggressive | 50.7% | 56.7% |
| shorthand | aggressive | 24.0% | 38.3% |

Every other encoding is at 95% or more in both columns.

At `conservative`, by kind of sample: whole text 98.4%, part of a text 89.9%, two layers 94.8%,
real text messages with HTML entities 100% (136/136). By length: under 20 characters 85.5%,
20 and over 95.6% to 97.1%.

The three informal-writing rows are low on purpose-built hard samples: the generator has its own,
longer lists and makes random typing slips, and a text counts only if every word comes back. Their
step precision is 94% to 100%. On the 1,518 clean informal texts (mostly real text messages),
`aggressive` rewrites 25.4%.

The 24 clean texts changed at `aggressive`:

- 12 by `misspelling`: 10 real typos in Stack Exchange and Wikinews posts being corrected
  (`accross`, `avaliable`, `doesnt`) and 2 with the old spelling `waggon` in a book.
- 2 by `shorthand` in Wikipedia text that quotes it (`u`, `R U`).
- 3 with a stretched word (`Helloooo`).
- 5 correct foreign spellings read as accent disguises (`coupé`, `façade`, `sław`), and a lone
  Cyrillic "а" in a sentence about that letter.
- The HTML sentence.

A 25th, a pinyin phrase rewritten by a Caesar shift, was found in this reading and fixed.

### Hand-disguised sentences: what the ten failures are

At `balanced`:

- Two are written in symbol pictures (`|-|` for "H"). Not attempted in version 1.
- Two need spelling correction beyond the short lists (`kongratulations`, `pirze`, `gol`, `bes`).
- Two use `l` for `i` in plain letters (`vlslt`, `lt`), which no transform reads; one of them
  also has stray commas and a colon added between words.
- One has `4` for "for" before a word outside the shorthand list, and `_` between two words.
- One uses an emoji for a word that cannot be guessed (a sparkle for "wonderful").
- Two use shorthand or an emoji that only `aggressive` reads (`ur`, a pill for "medicine");
  both come back at that level.

### Threshold sweep (2026-10-12)

One threshold varied at a time around the starting values, on the dev split, before the last
lookalike and reversal fixes. Each cell: clean texts changed / recovered / made worse.

| Level | Setting | Values tried and result |
|---|---|---|
| conservative (3,625 samples) | `min_score` | 0.40: 2 / 3467 / 2 · 0.45: 2 / 3465 / 2 · **0.50: 1 / 3461 / 2** · 0.55: 1 / 3452 / 2 · 0.60: 1 / 3439 / 2 |
| | `min_gain` | 0.15: 1 / 3462 / 2 · 0.20: 1 / 3462 / 2 · 0.25: 1 / 3461 / 2 · **0.30: 1 / 3461 / 2** · 0.35: 1 / 3458 / 2 · 0.40: 1 / 3457 / 2 |
| | `min_letters` | 6: 1 / 3474 / 2 · **8: 1 / 3474 / 2** · 10: 1 / 3461 / 2 · 12: 1 / 3425 / 2 · 14: 1 / 3362 / 1 |
| balanced (8,099 samples) | `min_score` | 0.40: 2 / 7393 / 4 · 0.45: 2 / 7390 / 4 · **0.50: 1 / 7386 / 3** · 0.55: 1 / 7377 / 2 · 0.60: 1 / 7364 / 2 |
| | `min_gain` | 0.15: 1 / 7389 / 3 · 0.20: 1 / 7389 / 3 · 0.25: 1 / 7388 / 3 · **0.30: 1 / 7386 / 3** · 0.35: 1 / 7383 / 3 · 0.40: 1 / 7382 / 2 |
| | `min_letters` | 6: 1 / 7399 / 3 · **8: 1 / 7399 / 3** · 10: 1 / 7386 / 3 · 12: 1 / 7350 / 3 · 14: 1 / 7287 / 2 |
| aggressive (8,939 samples) | `min_score` | 0.40: 26 / 7973 / 16 · **0.45: 26 / 7970 / 16** · 0.50: 25 / 7966 / 16 · 0.55: 25 / 7957 / 16 |
| | `min_gain` | 0.15: 26 / 7971 / 16 · 0.20: 26 / 7971 / 16 · **0.25: 26 / 7970 / 16** · 0.30: 26 / 7970 / 16 · 0.35: 26 / 7967 / 16 |
| | `min_letters` | 4: 26 / 7973 / 16 · **6: 26 / 7970 / 16** · 8: 26 / 7970 / 16 · 10: 26 / 7957 / 16 |

Chosen values are in bold. What the sweep shows:

- **The results barely depend on the thresholds.** Across the whole range recovery moves by
  about one point. The word-level rules and the guards do the deciding, not the margins.
- **`min_score` stays at 0.50** below `aggressive`: lower values change one more clean text.
- **`min_gain` stays** where it was: nothing to gain either way.
- **`min_letters` goes from 10 to 8** at `conservative` and `balanced`: 13 more samples
  recovered at each level, no clean text changed, nothing made worse. 6 adds nothing over 8.
- `aggressive` is unchanged. At 0.50 it would change one clean text fewer and recover four
  fewer; it keeps the lower margin, which is what the level is for.

Per-transform limits, tried the same way with the chosen thresholds in place:

| Limit | Values tried: clean changed / recovered | Kept |
|---|---|---|
| `reverse` fewest letters | 8: 2 / 3480 · 10: 1 / 3481 · 12: 1 / 3481 | 10 |
| `caesar` fewest letters | 8: 2 / 3481 · 10: 1 / 3481 · 12: 1 / 3470 | 10 |
| `leetspeak` words of evidence before a name is read | 2: 1 / 7473 · 3: 1 / 7461 · 4: 1 / 7453 | 2 (was 3) |
| `leetspeak` words of evidence before a short token is read | 1: 1 / 7461 · 2: 1 / 7452 | 1 |
| `repeated-chars` shortest lone word | 4: 26 / 8042 · 5: 25 / 8033 · 6: 24 / 8020 | 5 |
| `repeated-chars` words of evidence before a name is cut | 1: 25 / 8034 · 2: 25 / 8033 · 3: 25 / 8029 | 2 |
| `misspelling` shortest word for a typing slip | 5: 26 / 8059 · 6: 25 / 8033 · 7: 24 / 8020 | 6 |

Not swept: the `separator` evidence counts (a table per symbol, not one number) and the
shorthand tiers.

Weak spots:

- **The clean set constrains the thresholds weakly.** Only one clean text changes anywhere in
  the swept range below `aggressive`, so the sweep cannot show where clean text starts to
  suffer. A short Spanish sentence, "No pasa nada", is reversed at every level because all three
  words read as English backwards ("Adan", "asap", "on"); nothing in the clean set is like it.
- **Shorthand, misspellings and emoji are covered narrowly by design**: forms outside the short
  lists, uncommon misspellings and dropped letters are left as written.
- **The informal-writing samples share an author with the transforms.** The text-message corpus
  is the better check.
- **Some lookalike readings were learned from the 25 hand-disguised dev sentences** (about
  twenty letters such as `ƅ` for "b" and Armenian `ր` for "n"). The 22 test sentences will show
  whether they carry over; the dev figure of 15 of 25 flatters the tool.
- **Accent substitution inside otherwise clean text: 62%** at `balanced` (whole text 77%). A
  single word with everyday accents, or a capitalised name, is left alone without more evidence.
  Letting two capitalised words count as evidence was tried and changed two Vietnamese names in
  a clean text, so it was dropped.
- **Shifted or reversed words inside otherwise clean text:** Caesar 65%, rot13 68%, reversal 42%
  (was 28%). A short run has too few letters to judge, and words at its ends that read both
  ways ("no", "was") cannot be placed.
- **Repeated letters inside clean text: 68%.** One short stretched word is left alone, because
  that is what emphasis looks like.
- **Leetspeak with a second trick on top: 64% to 82%.** Most misses are a capital letter hidden
  behind a digit and names that are not in the word list.
- Reversed base64: 66%.
- Texts under 20 characters: 82% to 87%.
- The one clean text changed at `conservative` and `balanced` is a sentence that mentions HTML
  entities ("write `&amp;` to show an ampersand").

## Known limits

- **The committed obfuscated set is almost all synthetic.** It tests the tricks we thought of,
  written by the same hands as the decoder will be. Real deliberate obfuscation comes only from
  the local BitCore set, which covers visual tricks in one kind of text (extortion and phishing
  email) and nothing else. There is no real sample of an encoding such as base64.
- **BitCore numbers cannot be reproduced from the repository alone.** Anyone checking them must
  download the dataset, and it could be withdrawn.
- **"Clean" is an assumption for real text.** Texts containing invisible or control characters
  were dropped as doubtful (about 35 to 55 per split), but some real texts may still hold
  genuine obfuscation. Inspect dev false changes before counting them against the tool.
- **Leetspeak over text messages is ambiguous.** Messages already contain digits that stand for
  sounds, so some obfuscated samples from that source cannot be recovered exactly by anyone.
- **Hand-written categories are small** (5 to 22 distinct texts each) and appear in both splits.
- **Same generator in both splits.** Test has unseen text but no unseen trick variants.
- **The corpus is a frozen sample.** Re-downloading gives different random articles; the
  committed files are the record.
- **Test-split discipline is by convention.** Nothing stops a run on it; do not tune against it.
