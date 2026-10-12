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
are out of scope (misspelling, shorthand, emoji), so read the character error for this origin
rather than exact recovery. With so few samples, one sentence is 4 points.

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

## Current results on the dev split (2026-10-12)

All twenty-three transforms are built. The test split has not been run. Recovery ignores capital
letters (see "The measures").

| Scored at | Clean texts changed | Recovered | With every capital right | Made worse | Real phishing set |
|---|---|---|---|---|---|
| conservative | 0.01% (1/7442) | 95.5% (3461/3625) | 95.5% | 0.1% (2/3625) | not at this level |
| balanced | 0.01% (1/7442) | 88.0% (7124/8099) | 87.7% | 0.0% (3/8099) | 81.1% (2433/3000) |
| aggressive | 0.35% (26/7442) | 87.9% (7855/8939) | 87.2% | 0.2% (16/8939) | 89.5% (2684/3000) |

The `aggressive` row covers 840 more samples than before (the three informal-writing tricks),
which is why its recovery is lower than the 91% reported earlier the same day; on the samples it
shared with that run nothing was lost.

On the real phishing set the mean character error falls from 20.4% to 1.5% at `balanced` and to
0.6% at `aggressive`.

By trick, whole text and inside clean text:

| Trick | Level | Whole text | Inside clean text |
|---|---|---|---|
| homoglyph | balanced | 93.3% | 91.7% |
| accent substitution | balanced | 73.8% | 61.7% |
| combining marks | balanced | 96.7% | 98.3% |
| leetspeak | balanced | 84.7% | 90.0% |
| separators | balanced | 87.3% | 85.0% |
| repeated letters | aggressive | 86.7% | 68.3% |
| misspelling | aggressive | 54.0% | 50.0% |
| emoji for a word | aggressive | 50.7% | 56.7% |
| shorthand | aggressive | 24.0% | 38.3% |

The three informal-writing rows are low on purpose-built hard samples: the generator has its own,
longer lists and makes random typing slips, and a text counts only if every word comes back. Their
step precision is 94% to 100%. On the 1,518 clean informal texts (mostly real text messages),
`aggressive` rewrites 25.4%; a reading of the commonest rewrites found them correct (`u` to
"you" 219 times, `dont` to "don't" 32 times) with a few wrong ones, since fixed.

The 26 clean texts changed at `aggressive`: 8 correct foreign spellings (`coupé`), 3 with a
stretched word, the HTML sentence, and 14 from the informal-writing transforms. Of those 14, 11
are real typos in Stack Exchange posts being corrected (`accross`, `avaliable`, `doesnt`) and 3
are the old spelling `waggon` in a book.

The hand-disguised set is at 7 of 25 at `balanced` and 9 of 25 at `aggressive`.

At `conservative`, by kind of sample: whole text 98.2%, part of a text 87.9%, two layers 94.8%,
real text messages with HTML entities 100% (136/136). By length: under 20 characters 80.3%,
20 and over 95% to 97%.

Weak spots:

- **Shorthand, misspellings and emoji are covered narrowly by design**: forms outside the short
  lists, uncommon misspellings and dropped letters are left as written.
- **The informal-writing samples share an author with the transforms.** The generator's lists
  are separate and longer, but they were written by the same hand, so these numbers flatter the
  tool less than real data would only by accident. The text-message corpus is the better check.
- **Repeated letters inside clean text: 68%.** One short stretched word is left alone, because
  that is what emphasis looks like.
- **Leetspeak, whole text: 76%.** Most misses are a capital letter hidden behind a digit
  (`@rmy` for "Army" comes back as "army") and names that are not in the word list.
- **Accent substitution inside otherwise clean text: 62%** at `balanced` (whole text 74%). A
  single word with everyday accents, or a name, is left alone without more evidence.
- Shifted or reversed words inside otherwise clean text: Caesar 65%, rot13 68%, reversal 28%.
- Reversed base64: 66%.
- Texts under 20 characters: too little evidence to judge.
- The one clean text changed at `conservative` and `balanced` is a sentence that mentions HTML
  entities ("write `&amp;` to show an ampersand").
- The 8 extra clean texts changed at `aggressive` are correct foreign spellings read as
  disguises (`coupé`, `françoise`, `crème`).

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
