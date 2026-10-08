"""Builds the evaluation sets from the clean corpus.

Run ``python -m evaluation.build``. Output, per split, in ``data/eval/<split>/``:

- ``clean.jsonl``: text that must come back unchanged.
- ``obfuscated.jsonl``: obfuscated text with the clean original as ``expected``,
  plus the real messages from ``real_<split>.jsonl``.

Everything is derived from a fixed seed, so rebuilding gives identical files.
"""

import json
from pathlib import Path
from random import Random

from evaluation import negatives, obfuscator
from evaluation.tricks import TRICK_LEVEL

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "data" / "eval"
SPLITS = ("dev", "test")
SEED = 20261008

WHOLE_PER_TRICK = 150
PARTIAL_PER_TRICK = 60
PER_STACK = 50

# Encodings that grow the text several times over are made from shorter sources.
BULKY = {"binary", "decimal-codes", "html-entity", "backslash-escape"}


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


CREDIT = ("origin", "source", "url", "licence")
OURS = {"origin": "generated", "source": "generated", "url": "", "licence": "MIT"}


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def clean_rows(split: str, corpus: list[dict], rng: Random) -> list[dict]:
    rows = [{"category": "prose", **row} for row in corpus]
    rows += [{"category": category, "text": text, **OURS} for category, text in negatives.generate(rng)]
    return [
        {"id": f"{split}-clean-{n:05d}", "text": row["text"], "expected": row["text"], "tricks": [], "mode": "clean",
         "category": row["category"], **{key: row[key] for key in CREDIT}, "split": split}
        for n, row in enumerate(rows, 1)
    ]


def obfuscated_rows(split: str, corpus: list[dict], real: list[dict], rng: Random) -> list[dict]:
    rows: list[dict] = []

    def add(text: str, expected: str, tricks: list[str], mode: str, credit: dict, **extra: str) -> None:
        if text == expected:
            return
        rows.append({"id": f"{split}-obf-{len(rows) + 1:05d}", "text": text, "expected": expected, "tricks": tricks,
                     "mode": mode, "category": "+".join(tricks), **{key: credit[key] for key in CREDIT},
                     "split": split, **extra})

    def sources(count: int, *, short: bool = False) -> list[dict]:
        pool = [row for row in corpus if len(row["text"]) <= 120] if short else corpus
        return rng.sample(pool, k=count)

    for trick in TRICK_LEVEL:
        if trick == "tag-characters":
            for row in sources(WHOLE_PER_TRICK):
                text, hidden = obfuscator.tag_characters(row["text"], rng)
                add(text, row["text"], [trick], "whole", row, hidden=hidden)
            continue
        for row in sources(WHOLE_PER_TRICK, short=trick in BULKY):
            add(obfuscator.apply(trick, row["text"], rng), row["text"], [trick], "whole", row)
        made = 0
        for row in sources(PARTIAL_PER_TRICK * 6):
            if made == PARTIAL_PER_TRICK:
                break
            text = obfuscator.apply_partial(trick, row["text"], rng)
            if text is not None:
                add(text, row["text"], [trick], "partial", row)
                made += 1

    for stack in obfuscator.STACKS:
        for row in sources(PER_STACK, short=True):
            add(obfuscator.apply_stack(stack, row["text"], rng), row["text"], list(stack), "stacked", row)

    # Real messages, not produced by our obfuscator.
    for row in real:
        add(row["text"], row["expected"], row["tricks"], "real", row)
    return rows


def main() -> None:
    for split in SPLITS:
        corpus = read(EVAL / f"corpus_{split}.jsonl")
        rng = Random(f"{SEED}-{split}")
        clean = clean_rows(split, corpus, rng)
        obfuscated = obfuscated_rows(split, corpus, read(EVAL / f"real_{split}.jsonl"), rng)
        write(EVAL / split / "clean.jsonl", clean)
        write(EVAL / split / "obfuscated.jsonl", obfuscated)
        print(f"{split}: {len(clean)} clean, {len(obfuscated)} obfuscated")


if __name__ == "__main__":
    main()
