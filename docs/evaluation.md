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
- **`obfuscated.jsonl`** (about 5,280 texts): a trick applied to corpus text, with the original
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
- **Obfuscated texts recovered exactly:** output equals the original, character for character.
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

NFKC recovers only the styled-alphabet and fullwidth samples, and nothing stacked or real. Its
false changes are spread over every real source (16 of 7,000 real texts) and hit 5 of the 7
texts in the `symbols` category, which is why the tool does not normalise whole texts.

The deobfuscator itself has no transforms yet and scores the same as "return the input".

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
