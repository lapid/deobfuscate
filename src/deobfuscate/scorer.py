"""How much a piece of text looks like English."""

import re

from deobfuscate import resources

# A word: letters, with apostrophes or hyphens allowed inside.
TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")
SINGLE_LETTER_WORDS = frozenset("aiAI")
NOT_LETTERS = re.compile(r"[^a-z]+")


def is_word(token: str) -> bool:
    """Whether ``token`` is a known English word, in any usual capitalisation."""
    if len(token) == 1:
        return token in SINGLE_LETTER_WORDS
    known = resources.words()
    token = token.replace("’", "'")
    for form in (token, token.removesuffix("'s")):
        if form in known or form.lower() in known or form.capitalize() in known:
            return True
    return False


def word_coverage(text: str) -> tuple[int, int]:
    """(letters inside known words, letters in all words).

    One-letter words are left out of both: "a" and "I" are words, but a text of
    single letters is no evidence of English.
    """
    covered = total = 0
    for match in TOKEN.finditer(text):
        token = match.group()
        if len(token) == 1:
            continue
        letters = sum(char.isalpha() for char in token)
        total += letters
        if is_word(token):
            covered += letters
    return covered, total


def ngram_fit(text: str) -> float | None:
    """Mean log10 probability of the text's letter sequences; None if it has too few letters."""
    table, unseen, size = resources.ngrams()
    letters = " " + " ".join(NOT_LETTERS.sub(" ", text.lower()).split()) + " "
    count = len(letters) - size + 1
    if count < 1 or len(letters.strip()) < 2:
        return None
    return sum(table.get(letters[i : i + size], unseen) for i in range(count)) / count


# Typical n-gram fit of wrong decodes and of clean English, measured on the dev
# split (docs/scorer.md). The fit is rescaled so those map to 0 and 1.
NGRAM_GIBBERISH, NGRAM_ENGLISH = -6.5, -4.0


def english_score(text: str) -> float:
    """0 for text with no sign of English, 1 for text that reads as English.

    The mean of two signals: the share of letters that sit in known words, and
    how usual the letter sequences are.
    """
    covered, total = word_coverage(text)
    fit = ngram_fit(text)
    if not total or fit is None:
        return 0.0
    usual = min(1.0, max(0.0, (fit - NGRAM_GIBBERISH) / (NGRAM_ENGLISH - NGRAM_GIBBERISH)))
    return 0.5 * covered / total + 0.5 * usual


def letter_count(text: str) -> int:
    """How many letters the text offers as evidence. One-letter words do not count."""
    return sum(len(match.group()) for match in TOKEN.finditer(text) if len(match.group()) > 1)
