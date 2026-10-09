"""Each transform recovers what the project's own generator produced, and leaves clean text alone."""

import random
import unittest

from deobfuscate import deobfuscate
from evaluation import obfuscator

SENTENCES = (
    "The meeting is moved to the second floor.",
    "Please send the report before Friday morning.",
    "Our neighbours painted their fence green last summer.",
)

CONSERVATIVE = (
    "zero-width", "styled-alphabet", "fullwidth", "html-entity", "url-percent", "backslash-escape",
    "base64", "base64url", "hex", "binary", "decimal-codes", "rot13", "caesar", "reverse",
)

# Names the step record uses where they differ from the generator's.
RECORDED = {"base64url": "base64"}


def run(text: str, level: str = "conservative"):
    return deobfuscate(text, strictness=level, raise_errors=True)


class RecoveryTest(unittest.TestCase):
    def test_whole_text(self):
        for trick in CONSERVATIVE:
            for seed in range(6):
                for sentence in SENTENCES:
                    disguised = obfuscator.apply(trick, sentence, random.Random(seed))
                    if disguised == sentence:
                        continue
                    result = run(disguised)
                    self.assertEqual(result.text, sentence, (trick, disguised))
                    self.assertEqual({step.transform for step in result.steps}, {RECORDED.get(trick, trick)}, trick)

    def test_part_of_a_text(self):
        # Shifted or reversed words that are also English as they stand cannot be told apart
        # at the edges of a span, so those three tricks are only checked on whole text.
        for trick in set(CONSERVATIVE) - {"rot13", "caesar", "reverse"}:
            for seed in range(6):
                sentence = " ".join(SENTENCES)
                disguised = obfuscator.apply_partial(trick, sentence, random.Random(seed))
                self.assertEqual(run(disguised).text, sentence, (trick, disguised))

    def test_layers(self):
        for stack in (("base64", "base64"), ("rot13", "base64"), ("hex", "base64"), ("base64", "hex"),
                      ("reverse", "base64"), ("base64", "reverse"), ("url-percent", "html-entity"),
                      ("zero-width", "base64")):
            for seed in range(4):
                disguised = obfuscator.apply_stack(stack, SENTENCES[0], random.Random(seed))
                result = run(disguised)
                self.assertEqual(result.text, SENTENCES[0], (stack, disguised))
                self.assertEqual([step.transform for step in result.steps][: len(stack)], list(stack), stack)

    def test_hidden_text_is_removed_and_reported(self):
        disguised, phrase = obfuscator.tag_characters(SENTENCES[0], random.Random(1))
        result = run(disguised)
        self.assertEqual(result.text, SENTENCES[0])
        self.assertEqual([(step.transform, step.hidden) for step in result.steps], [("tag-characters", phrase)])

    def test_result_is_stable(self):
        for trick in CONSERVATIVE:
            once = run(obfuscator.apply(trick, SENTENCES[1], random.Random(2))).text
            self.assertEqual(run(once).text, once, trick)


class LookalikeTest(unittest.TestCase):
    """Letters from other alphabets and added accents, decided word by word."""

    CYRILLIC = str.maketrans("aeopc", "аеорс")
    GREEK = str.maketrans("ntk", "ητκ")

    def test_letters_from_other_alphabets(self):
        sentence = "Please confirm your account password today"
        for table in (self.CYRILLIC, self.GREEK):
            result = run(sentence.translate(table), "balanced")
            self.assertEqual(result.text, sentence)
            self.assertEqual({step.transform for step in result.steps}, {"homoglyph"})

    def test_odd_accents(self):
        result = run("Please confirm y\u014d\u0169r acc\u014funt today", "balanced")
        self.assertEqual(result.text, "Please confirm your account today")
        self.assertEqual({step.transform for step in result.steps}, {"accent-substitution"})

    def test_not_at_the_conservative_level(self):
        text = "Please confirm your account".translate(self.CYRILLIC)
        self.assertEqual(run(text).text, text)

    def test_real_accents_and_other_languages_stay(self):
        for level in ("balanced", "aggressive"):
            for text in (
                "Привет, как дела? Сегодня хорошая погода.",
                "Η Ελλάδα είναι όμορφη το καλοκαίρι.",
                "I visited Москва and Αθήνα last year.",
                "Bonjour, comment ça va aujourd'hui ?",
            ):
                self.assertEqual(run(text, level).text, text, (level, text))
        for text in ("naïve café résumé", "The Cyrillic letter а looks like the Latin a.", "Señor Núñez lives in São Paulo."):
            self.assertEqual(run(text, "balanced").text, text)

    def test_aggressive_level_reads_a_lone_accented_word(self):
        text = "Dolores is survived by three children and her h\u00fcsband."
        self.assertEqual(run(text, "balanced").text, text)
        self.assertEqual(run(text, "aggressive").text, text.replace("\u00fc", "u"))


class LeaveAloneTest(unittest.TestCase):
    def untouched(self, *texts: str) -> None:
        for level in ("conservative", "balanced"):
            for text in texts:
                result = run(text, level)
                self.assertEqual((result.text, result.steps), (text, ()), (level, text))

    def test_numbers_and_codes(self):
        self.untouched(
            "Take route 66 west for 3 miles, then exit 4B.",
            "The scores were 68, 105, 100 and 32.",
            "Set the mask to 11111111 00000000 and retry.",
            "Colours #ff00aa and #361876 clash.",
            "id: 00000000-0000-4000-8000-000000000000",
        )

    def test_addresses_and_paths(self):
        self.untouched(
            "Visit https://example.com/a%20b?q=1&r=2 for details.",
            r"Open C:\temp\x64\update\notes.txt first.",
            "Mail first.last@example.co.uk today.",
        )

    def test_mentions_and_code(self):
        self.untouched(
            "A space becomes %20 in a URL.",
            "The string \\u00e9 is the escape for an accented e.",
            "<p>Fish &amp; chips &lt; 5 &gt; 3</p>",
            "The area is 100% natural, 0% fat.",
        )

    def test_other_languages_symbols_and_emoji(self):
        self.untouched(
            "Привет, как дела? Сегодня хорошая погода.",
            "こんにちは、ＡＢＣ今日はいい天気ですね。",
            "E = mc², H₂O, 10 µm, ½ cup, 25 °C",
            "Let 𝑥 be the unknown.",
            "naïve café résumé",
            "Great job 👍🏽 see you soon",
        )

    def test_words_that_look_encoded(self):
        self.untouched(
            "deadbeef cafe babe face",
            "The words ant and nag are a rot13 pair, like bar and one.",
            "level, radar, and stressed/desserts",
            "internationalization and characteristically",
            "ok",
        )


if __name__ == "__main__":
    unittest.main()
