"""Builds the evaluation sets from the clean corpus.

Run ``python -m evaluation.build``. Output, per split, in ``data/eval/<split>/``:

- ``clean.jsonl``: text that must come back unchanged.
- ``obfuscated.jsonl``: obfuscated text with the clean original as ``expected``.

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

WHOLE_PER_TRICK = 100
PARTIAL_PER_TRICK = 40
PER_STACK = 40

# Encodings that grow the text several times over are made from shorter sources.
BULKY = {"binary", "decimal-codes", "html-entity", "backslash-escape"}


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def clean_rows(split: str, corpus: list[str], rng: Random) -> list[dict]:
    rows = [{"category": "prose", "text": text, "source": "public-domain books"} for text in corpus]
    rows += [{"category": category, "text": text, "source": "generated"} for category, text in negatives.generate(rng)]
    return [
        {"id": f"{split}-clean-{n:05d}", "text": row["text"], "expected": row["text"], "tricks": [],
         "mode": "clean", "category": row["category"], "source": row["source"], "split": split}
        for n, row in enumerate(rows, 1)
    ]


def obfuscated_rows(split: str, corpus: list[str], rng: Random) -> list[dict]:
    rows: list[dict] = []

    def add(text: str, expected: str, tricks: list[str], mode: str, **extra: str) -> None:
        if text == expected:
            return
        rows.append({"id": f"{split}-obf-{len(rows) + 1:05d}", "text": text, "expected": expected, "tricks": tricks,
                     "mode": mode, "category": "+".join(tricks), "source": "generated", "split": split, **extra})

    def sources(count: int, *, short: bool = False) -> list[str]:
        pool = [text for text in corpus if len(text) <= 120] if short else corpus
        return rng.sample(pool, k=count)

    for trick in TRICK_LEVEL:
        if trick == "tag-characters":
            for clean in sources(WHOLE_PER_TRICK):
                text, hidden = obfuscator.tag_characters(clean, rng)
                add(text, clean, [trick], "whole", hidden=hidden)
            continue
        for clean in sources(WHOLE_PER_TRICK, short=trick in BULKY):
            add(obfuscator.apply(trick, clean, rng), clean, [trick], "whole")
        made = 0
        for clean in sources(PARTIAL_PER_TRICK * 4):
            if made == PARTIAL_PER_TRICK:
                break
            text = obfuscator.apply_partial(trick, clean, rng)
            if text is not None:
                add(text, clean, [trick], "partial")
                made += 1

    for stack in obfuscator.STACKS:
        for clean in sources(PER_STACK, short=True):
            add(obfuscator.apply_stack(stack, clean, rng), clean, list(stack), "stacked")
    return rows


def main() -> None:
    for split in SPLITS:
        corpus = (EVAL / f"corpus_{split}.txt").read_text(encoding="utf-8").splitlines()
        rng = Random(f"{SEED}-{split}")
        clean = clean_rows(split, corpus, rng)
        obfuscated = obfuscated_rows(split, corpus, rng)
        write(EVAL / split / "clean.jsonl", clean)
        write(EVAL / split / "obfuscated.jsonl", obfuscated)
        print(f"{split}: {len(clean)} clean, {len(obfuscated)} obfuscated")


if __name__ == "__main__":
    main()
