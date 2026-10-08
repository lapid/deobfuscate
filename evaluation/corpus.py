"""Builds the clean sentence corpus from public-domain books.

Run ``python -m evaluation.corpus`` to download the books into ``data/cache/``
and write ``data/eval/corpus_dev.txt`` and ``data/eval/corpus_test.txt``.
Dev and test use different books, so no sentence or author is shared.
"""

import re
import urllib.request
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "gutenberg"
EVAL = ROOT / "data" / "eval"

# Project Gutenberg book numbers. All were published before 1929 and are in the
# public domain in the United States.
BOOKS = {
    "dev": {
        1342: "Pride and Prejudice",
        1661: "The Adventures of Sherlock Holmes",
        64317: "The Great Gatsby",
        55: "The Wonderful Wizard of Oz",
        20203: "Autobiography of Benjamin Franklin",
    },
    "test": {
        11: "Alice's Adventures in Wonderland",
        84: "Frankenstein",
        35: "The Time Machine",
        2814: "Dubliners",
        541: "The Age of Innocence",
    },
}

UNITS_PER_SPLIT = 2000
SEED = 20261008

SENTENCE = re.compile(r"[^.!?]+[.!?]+[\"”’')\]]*")
STARTS_WELL = re.compile(r"[\"“‘']?[A-Z]")


def fetch(book: int) -> str:
    path = CACHE / f"pg{book}.txt"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://www.gutenberg.org/cache/epub/{book}/pg{book}.txt"
        with urllib.request.urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    return path.read_text(encoding="utf-8-sig")


def body(raw: str) -> str:
    """The book text without Project Gutenberg's own header and footer."""
    start = re.search(r"\*\*\* ?START OF.*?\*\*\*", raw)
    end = re.search(r"\*\*\* ?END OF", raw)
    return raw[start.end() if start else 0 : end.start() if end else len(raw)]


def paragraphs(text: str) -> list[str]:
    out = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        # Underscores mark italics in these files; they are markup, not the author's text.
        para = " ".join(block.replace("_", "").split())
        if not para or "[" in para or "Gutenberg" in para or not any(char.islower() for char in para):
            continue
        out.append(para)
    return out


def sentences(para: str) -> list[str]:
    out = []
    for match in SENTENCE.finditer(para):
        sentence = match.group().strip()
        if 20 <= len(sentence) <= 240 and len(sentence.split()) >= 4 and STARTS_WELL.match(sentence):
            out.append(sentence)
    return out


def units(book_ids: dict[int, str], rng: Random) -> list[str]:
    """Single sentences, plus some runs of two or three, for a spread of lengths."""
    pool: list[str] = []
    for book in sorted(book_ids):
        candidates: list[str] = []
        for para in paragraphs(body(fetch(book))):
            found = sentences(para)
            candidates.extend(found)
            for size in (2, 3):
                if len(found) >= size and rng.random() < 0.3:
                    start = rng.randint(0, len(found) - size)
                    candidates.append(" ".join(found[start : start + size]))
        candidates = sorted(set(candidates))
        pool.extend(rng.sample(candidates, k=min(len(candidates), UNITS_PER_SPLIT // len(book_ids))))
    rng.shuffle(pool)
    return pool


def main() -> None:
    EVAL.mkdir(parents=True, exist_ok=True)
    for split, books in BOOKS.items():
        lines = units(books, Random(f"{SEED}-{split}"))
        (EVAL / f"corpus_{split}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{split}: {len(lines)} texts from {len(books)} books")


if __name__ == "__main__":
    main()
