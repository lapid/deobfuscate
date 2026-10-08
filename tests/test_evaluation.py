import base64
import codecs
import html
import random
import unicodedata
import unittest
import urllib.parse

from evaluation import metrics, negatives, obfuscator
from evaluation.tricks import TRICK_LEVEL, in_scope

TEXTS = (
    "The quick brown fox jumps over the lazy dog.",
    "“Old sport, the dance is unimportant,” she said — twice.",
    "Meet me at the station at five; bring Zoë's café receipts.",
)


def slow_edit_distance(a: str, b: str) -> int:
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        new = [i]
        for j, y in enumerate(b, 1):
            new.append(min(row[j] + 1, new[j - 1] + 1, row[j - 1] + (x != y)))
        row = new
    return row[-1]


class EditDistanceTest(unittest.TestCase):
    def test_matches_reference_on_random_strings(self):
        rng = random.Random(1)
        for _ in range(500):
            a = "".join(rng.choice("abcé ") for _ in range(rng.randint(0, 90)))
            b = "".join(rng.choice("abcé ") for _ in range(rng.randint(0, 90)))
            self.assertEqual(metrics.edit_distance(a, b), slow_edit_distance(a, b), (a, b))


class ObfuscatorTest(unittest.TestCase):
    """Each trick must be undone exactly by an independent inverse."""

    def each(self, trick):
        for seed in range(25):
            for text in TEXTS:
                yield text, obfuscator.apply(trick, text, random.Random(seed))

    def test_every_trick_has_a_generator(self):
        self.assertEqual(set(obfuscator.TRICKS) | {"tag-characters"}, set(TRICK_LEVEL))

    def test_encodings_decode_with_the_standard_library(self):
        def from_hex(s):
            return bytes.fromhex(s.replace("0x", "").replace(" ", "")).decode()

        def from_backslash(s):
            return s.encode("ascii").decode("unicode_escape")

        def unpad(s):
            return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)).decode()

        inverses = {
            "base64": lambda s: base64.b64decode(s).decode(),
            "base64url": unpad,
            "hex": from_hex,
            "binary": lambda s: bytes(int(s.replace(" ", "")[i : i + 8], 2) for i in range(0, len(s.replace(" ", "")), 8)).decode(),
            "decimal-codes": lambda s: bytes(int(n) for n in s.replace(",", " ").split()).decode(),
            "rot13": lambda s: codecs.decode(s, "rot13"),
            "reverse": lambda s: s[::-1],
            "html-entity": html.unescape,
            "url-percent": urllib.parse.unquote,
            "backslash-escape": from_backslash,
            "fullwidth": lambda s: unicodedata.normalize("NFKC", s),
            "styled-alphabet": lambda s: unicodedata.normalize("NFKC", s),
        }
        for trick, inverse in inverses.items():
            for text, changed in self.each(trick):
                if trick in ("fullwidth", "styled-alphabet"):
                    # NFKC also rewrites characters the trick never touched; compare on the same footing.
                    text = unicodedata.normalize("NFKC", text)
                self.assertEqual(inverse(changed), text, trick)

    def test_caesar_is_a_rotation(self):
        for text, changed in self.each("caesar"):
            first = next(i for i, c in enumerate(text) if c.isascii() and c.isalpha())
            shift = (ord(changed[first]) - ord(text[first])) % 26
            back = "".join(
                chr((ord(c) - base - shift) % 26 + base) if c.isascii() and c.isalpha() else c
                for c in changed
                for base in [65 if c.isupper() else 97]
            )
            self.assertEqual(back, text)
            self.assertNotEqual(changed, text)

    def test_invisible_and_mark_tricks_only_add_characters(self):
        for trick, added in (("zero-width", set(obfuscator.ZERO_WIDTH)), ("combining-marks", set(obfuscator.OVERLAY_MARKS))):
            for text, changed in self.each(trick):
                self.assertEqual("".join(c for c in changed if c not in added), text)
                self.assertNotEqual(changed, text)

    def test_tag_characters_hide_the_phrase(self):
        for seed in range(25):
            for text in TEXTS:
                changed, phrase = obfuscator.tag_characters(text, random.Random(seed))
                visible = "".join(c for c in changed if not 0xE0000 <= ord(c) <= 0xE007F)
                hidden = "".join(chr(ord(c) - 0xE0000) for c in changed if 0xE0000 <= ord(c) <= 0xE007F)
                self.assertEqual((visible, hidden), (text, phrase))

    def test_substitution_tricks_map_back(self):
        back = {glyph: letter for letter, glyphs in obfuscator.HOMOGLYPHS.items() for glyph in glyphs}
        for text, changed in self.each("homoglyph"):
            self.assertEqual("".join(back.get(c, c) for c in changed), text)
            self.assertNotEqual(changed, text)
        for text, changed in self.each("leetspeak"):
            self.assertEqual(len(changed), len(text))
            for original, new in zip(text, changed):
                self.assertTrue(new == original or new in obfuscator.LEET[original.lower()])
            self.assertNotEqual(changed, text)

    def test_separator_and_repetition_keep_the_letters_in_order(self):
        for text, changed in self.each("separator"):
            self.assertEqual([c for c in changed if c.isalpha()], [c for c in text if c.isalpha()])
        for text, changed in self.each("repeated-chars"):
            squeezed = [c for i, c in enumerate(changed) if i == 0 or c != changed[i - 1]]
            original = [c for i, c in enumerate(text) if i == 0 or c != text[i - 1]]
            self.assertEqual(squeezed, original)
            self.assertGreater(len(changed), len(text))

    def test_partial_keeps_the_rest_of_the_text(self):
        text = "one two three four five six seven eight nine ten eleven twelve"
        for trick in obfuscator.TRICKS:
            for seed in range(10):
                changed = obfuscator.apply_partial(trick, text, random.Random(seed))
                self.assertIsNotNone(changed, trick)
                self.assertNotEqual(changed, text)
                kept = set(text.split()) & set(changed.split())
                self.assertGreaterEqual(len(kept), 6, (trick, changed))


class NegativesTest(unittest.TestCase):
    def test_generation_is_repeatable_and_distinct(self):
        first = negatives.generate(random.Random(3))
        self.assertEqual(first, negatives.generate(random.Random(3)))
        self.assertEqual(len(first), len(set(first)))
        self.assertEqual({category for category, _ in first}, set(negatives.CATEGORIES))


class ScoringTest(unittest.TestCase):
    def outcome(self, text, expected, tricks, output, transforms=(), mode="whole"):
        sample = {"text": text, "expected": expected, "tricks": list(tricks), "mode": mode, "category": "+".join(tricks) or "prose"}
        return metrics.Outcome(sample, output, list(transforms), output, 0.001)

    def test_scope_follows_the_strictness_level(self):
        self.assertTrue(in_scope(["base64"], "conservative"))
        self.assertFalse(in_scope(["base64", "leetspeak"], "conservative"))
        self.assertTrue(in_scope(["base64", "leetspeak"], "balanced"))
        self.assertFalse(in_scope(["repeated-chars"], "balanced"))

    def test_report_counts(self):
        outcomes = [
            self.outcome("clean text", "clean text", [], "clean text"),
            self.outcome("route 66", "route 66", [], "route bb", ["leetspeak"]),
            self.outcome("aGk=", "hi", ["base64"], "hi", ["base64"]),
            self.outcome("aGV5", "hey", ["base64"], "aGV5"),
            self.outcome("h3y", "hey", ["leetspeak"], "h3y"),
            self.outcome("uryyb", "hello", ["rot13"], "xxxxxxxx", ["caesar"]),
        ]
        report = metrics.score(outcomes, "conservative")
        self.assertEqual((report.false_change.hits, report.false_change.total), (1, 2))
        self.assertEqual((report.recovered.hits, report.recovered.total), (1, 3))
        self.assertEqual((report.made_worse.hits, report.made_worse.total), (1, 3))
        self.assertEqual(report.out_of_scope_recovered.total, 1)
        self.assertEqual(report.precision("base64"), 1.0)
        self.assertEqual(report.recall("base64"), 0.5)
        self.assertEqual(report.precision("leetspeak"), 0.0)
        self.assertEqual(report.recall("rot13"), 0.0)
        self.assertEqual(report.idempotent.rate, 1.0)
        balanced = metrics.score(outcomes, "balanced")
        self.assertEqual(balanced.recovered.total, 4)


if __name__ == "__main__":
    unittest.main()
