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


class CombiningMarksTest(unittest.TestCase):
    def test_overlays_and_stacks(self):
        for seed in range(8):
            for sentence in SENTENCES:
                disguised = obfuscator.apply("combining-marks", sentence, random.Random(seed))
                if disguised == sentence:
                    continue
                result = run(disguised, "balanced")
                self.assertEqual(result.text, sentence, disguised)
                self.assertEqual({step.transform for step in result.steps}, {"combining-marks"})
                self.assertEqual(run(disguised).text, disguised)

    def test_a_one_letter_word_follows_the_rest(self):
        strike = "\u0336"
        text = f"I{strike} sent t{strike}h{strike}e{strike} report"
        self.assertEqual(run(text, "balanced").text, "I sent the report")
        alone = f"I{strike} sent the report"
        self.assertEqual(run(alone, "balanced").text, alone)

    def test_spelling_and_phonetic_marks_stay(self):
        for text in (
            "A cafe\u0301 on the corner, nai\u0308ve as ever.",
            "The village of Z\u0304ara\u0304t is written t\u0361s in the notes.",
            "Tie\u0302\u0301ng Vie\u0323\u0302t is the Vietnamese language.",
        ):
            for level in ("balanced", "aggressive"):
                self.assertEqual(run(text, level).text, text, (level, text))


class LeetspeakTest(unittest.TestCase):
    def test_digits_and_symbols_for_letters(self):
        for text, plain in (
            ("Please c0nfirm your acc0unt p@ssw0rd today", "Please confirm your account password today"),
            ("7h3 m33ting is m0v3d to the s3c0nd fl00r.", "The meeting is moved to the second floor."),
            ("Send the rep0rt bef0re FR1DAY m0rning", "Send the report before FRIDAY morning"),
            ("See you in @pril, y0u will l1ke it", "See you in April, you will like it"),
        ):
            result = run(text, "balanced")
            self.assertEqual(result.text, plain)
            self.assertEqual({step.transform for step in result.steps}, {"leetspeak"})
            self.assertEqual(run(text).text, text)

    def test_together_with_lookalike_letters(self):
        # The first letter of each disguised word is Cyrillic.
        text = "Please confirm your \u0430cc0unt and \u0440assw0rd"
        self.assertEqual(run(text, "balanced").text, "Please confirm your account and password")

    def test_shorthand_numbers_and_codes_stay(self):
        for text in (
            "c u l8r, gr8 2 see u b4 2day, sum1 will w8 4 u",
            "Meet at 5am or 3pm, it costs $5m, the 1st and 3rd are free.",
            "Runs on win7 and python3, see test5, the MP3 and the sha1 of level5.",
            "Ask @mark or @rose about the print$ share and the HP G5 or the M14.",
        ):
            for level in ("balanced", "aggressive"):
                self.assertEqual(run(text, level).text, text, (level, text))

    def test_shorthand_next_to_leetspeak_stays(self):
        result = run("It was gr8, thx 4ever, the c0d3 word is next", "balanced")
        self.assertEqual(result.text, "It was gr8, thx 4ever, the code word is next")


class SeparatorTest(unittest.TestCase):
    def test_symbols_between_letters(self):
        for symbol in ".-_*,":
            text = f"Please {symbol.join('send')} the {symbol.join('report')} today"
            result = run(text, "balanced")
            self.assertEqual(result.text, "Please send the report today", symbol)
            self.assertEqual({step.transform for step in result.steps}, {"separator"})
            self.assertEqual(run(text).text, text)

    def test_spaced_letters(self):
        self.assertEqual(run("Get a f r e e g i f t now", "balanced").text, "Get a free gift now")
        self.assertEqual(
            run("t h e   m e e t i n g   i s   m o v e d", "balanced").text, "the meeting is moved"
        )

    def test_initials_abbreviations_and_headings_stay(self):
        for text in (
            "J. R. R. Tolkien and C. S. Lewis",
            "The U.S.A and the W.H.O met at 5 p.m., i.e. late.",
            "N.B. the R.S.V.P. date is a.s.a.p. or a.k.a. now.",
            "C H A P T E R   O N E",
            "W E L C O M E",
            "Options a b c d and x-y-z, or one_two_three.",
            "T-shirt, X-ray, U-turn and e-mail",
        ):
            for level in ("balanced", "aggressive"):
                self.assertEqual(run(text, level).text, text, (level, text))


class RepeatedCharsTest(unittest.TestCase):
    def test_stretched_words(self):
        text = "Pleeease seeend the repoooort befoooore Friiiiday"
        result = run(text, "aggressive")
        self.assertEqual(result.text, "Please send the report before Friday")
        self.assertEqual({step.transform for step in result.steps}, {"repeated-chars"})
        self.assertEqual(run(text, "balanced").text, text)

    def test_the_commoner_reading_wins(self):
        self.assertEqual(run("Seeend theee files nooow", "aggressive").text, "Send the files now")

    def test_one_short_stretched_word_is_emphasis(self):
        for text in ("Hmmm, that is odd.", "It was sooooo good.", "Yessss we won", "See www.example.com or page III"):
            self.assertEqual(run(text, "aggressive").text, text)


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
