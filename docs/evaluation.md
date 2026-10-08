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
| `uv run python -m evaluation.build` | Rebuilds the sets from the corpus. Output is identical for the same seed |
| `uv run python -m evaluation.corpus` | Re-downloads the books and rebuilds the corpus |

## The sets

Each split has two files in `data/eval/<split>/`.

- **`clean.jsonl`** (2,442 texts): must come back unchanged. 2,000 are prose from public-domain
  books; 442 are generated hard negatives in 21 categories such as hashes, tokens, URLs, paths,
  code, other languages, shorthand and spaced headings.
- **`obfuscated.jsonl`** (about 3,360 texts): prose with a trick applied, and the original as
  `expected`. Three kinds:
  - **whole:** one trick over the whole text, 100 per trick.
  - **partial:** one trick on a run of words inside clean text, 40 per trick.
  - **stacked:** two tricks layered, 40 for each of 15 recipes.

Dev and test are drawn from different books. The generator is `evaluation/obfuscator.py`; the
hard negatives are in `evaluation/negatives.py`.

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

| System | Scored at | Clean texts changed | Recovered exactly | Made worse |
|---|---|---|---|---|
| Return the input | conservative | 0.0% (0/2442) | 0.0% (0/2378) | 0.0% |
| Return the input | balanced | 0.0% (0/2442) | 0.0% (0/3217) | 0.0% |
| Return the input | aggressive | 0.0% (0/2442) | 0.0% (0/3357) | 0.0% |
| Unicode NFKC | conservative | 0.5% (11/2442) | 11.7% (278/2378) | 0.1% |
| Unicode NFKC | balanced | 0.5% (11/2442) | 8.6% (278/3217) | 0.1% |
| Unicode NFKC | aggressive | 0.5% (11/2442) | 8.3% (278/3357) | 0.1% |

NFKC recovers only the styled-alphabet and fullwidth samples, and nothing stacked. Its 11 false
changes are mostly legitimate symbols (5 of 7 texts in the `symbols` category), which is why the
tool does not normalise whole texts.

The deobfuscator itself has no transforms yet and scores the same as "return the input".

## Known limits

- **The obfuscated set is synthetic.** It tests the tricks we thought of, written by the same
  hands as the decoder will be. A real-world set is still to be collected.
- **The prose is from books published before 1929.** Modern informal text is represented only
  by the small generated categories.
- **Hand-written categories are small** (5 to 22 distinct texts each) and appear in both splits.
  Only the prose and the randomly generated categories are truly unseen in test.
- **Few very short texts:** 31 clean texts under 20 characters, and no obfuscated ones.
- **Test-split discipline is by convention.** Nothing stops a run on it; do not tune against it.
