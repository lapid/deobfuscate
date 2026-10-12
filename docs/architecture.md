# Architecture

How the deobfuscator works inside. Read this before adding or changing a transform.

## The pieces

| Module | Job |
|---|---|
| `core.py` | The public `deobfuscate()` function. Contains errors unless `raise_errors=True` |
| `engine.py` | Runs transforms, judges their proposals, records steps. Holds the limits and the strictness presets |
| `transforms/` | One class per trick. A transform only proposes replacements |
| `scorer.py` | How much a text looks like English, from 0 to 1 |
| `protect.py` | Finds spans to leave alone: URLs, emails, file paths, UUIDs, hashes, colour codes |
| `scripts.py` | Which writing system a character belongs to, and whether a word mixes several |
| `resources.py` | Loads the data files in `data/` on first use |
| `types.py` | `Result` and `Step` |

## How a text is processed

1. Every enabled transform looks at the text and proposes candidates: "replace characters
   `start` to `end` with this".
2. A candidate that overlaps a protected span is dropped, unless its transform opts out.
3. **Certain transforms go first.** Transforms marked `judged = False` (invisible characters,
   styled letters, escapes, lookalikes, combining marks) are applied until none has anything
   left to propose. Only then are the judged transforms asked. Otherwise an invisible character
   inside a word would split it and mislead the transforms that read words.
   **All proposals of one certain transform are applied in the same round.** Some of them decide
   on evidence from the whole text; applied one at a time, the words rewritten first would no
   longer be there as evidence for the rest.
4. For a judged candidate, the engine deobfuscates the replacement **itself**, by running the
   whole process on it one layer deeper. This is what handles layers: base64 inside base64, or
   base64 inside rot13. The candidate is judged by what it finally turns into.
5. The engine judges: the final text must have enough letters, score high enough as English,
   and beat the text it replaces by a margin.
6. Among accepted candidates, the one with the largest **gain times number of letters** is
   applied. Weighting by size makes a rewrite of the whole text win over the same rewrite of a
   part of it. Its step is recorded, followed by the steps found inside it, with their positions
   shifted to where the replacement now sits.
7. Repeat from 1 until no candidate is accepted.

Because every accepted judged step must raise the score, the loop cannot go round in circles,
and a second run over the output finds nothing more to do.

## Strictness

A level does two things: it enables the transforms whose `level` is at or below it, and it
picks a `Policy` in `engine.py`:

| Level | Minimum score | Minimum gain | Minimum letters |
|---|---|---|---|
| conservative | 0.50 | 0.30 | 10 |
| balanced | 0.50 | 0.30 | 10 |
| aggressive | 0.45 | 0.25 | 6 |

A transform can ask for more letters than the level does (`min_letters`); Caesar shifts and
reversal require 10 at every level, because a short unknown word can become an English word
under some shift by chance. One-letter words never count as letters of evidence.

The values were set while building the transforms and still need a proper tuning pass.

## Transforms

| Transform | File | Judged | Notes |
|---|---|---|---|
| `zero-width` | `invisible.py` | no | Keeps joiners next to emoji and non-Latin letters |
| `tag-characters` | `invisible.py` | no | Removes hidden text and reports it in `Step.hidden`; works inside URLs too |
| `styled-alphabet` | `styled.py` | no | Needs two styled letters in a run; one alone is a maths variable |
| `fullwidth` | `styled.py` | no | Needs a fullwidth letter or digit; skipped in East Asian text |
| `html-entity` | `escapes.py` | no | Skipped when the text contains real HTML tags |
| `url-percent` | `escapes.py` | no | Needs two escapes in a word, or one joined to a letter |
| `backslash-escape` | `escapes.py` | no | Needs three escapes in a row |
| `homoglyph`, `accent-substitution` | `lookalike.py` | no | Balanced and up. Decided word by word; rules below |
| `combining-marks` | `marks.py` | no | Balanced and up. Decided word by word; rules below |
| `leetspeak` | `leet.py` | no | Balanced and up. Decided token by token; rules below |
| `base64` | `base64.py` | yes | Both alphabets; reported as `base64` |
| `hex`, `binary`, `decimal-codes` | `bytes.py` | yes | Must decode to readable UTF-8 |
| `rot13`, `caesar` | `caesar.py` | yes | Whole text, or runs of words that are not English as they stand |
| `reverse` | `reverse.py` | yes | Whole text, or runs of words |

`runs.py` holds the shared code that finds runs of words that are not English.

## Limits

- Inputs over 100,000 characters are returned unchanged.
- Layers are followed at most 4 deep.
- At most 200 replacements per text or layer.
- Input is only ever decoded, never executed.

## Adding a transform

1. Create `transforms/<name>.py` with a `Transform` subclass. Set `name` to the trick's name in
   `evaluation/tricks.py`, and `level` as `docs/taxonomy.md` says.
2. In `propose`, yield a `Candidate` for each span the trick may have been applied to. Propose
   generously where it is cheap; the engine does the judging. Keep spans aligned to whole words
   or tokens so the scorer has something to read.
3. Set `judged = False` only when a proposal cannot be wrong.
4. Add it to `ALL` in `transforms/__init__.py`.
5. Add unit tests, then run the evaluation. Keep the transform only if the clean set stays clean.

## Lookalike letters and accents

`lookalike.py` handles letters from other alphabets (`homoglyph`) and accents added to plain
letters (`accent-substitution`). The scorer cannot judge one word, so the transform decides
itself, word by word:

1. **Read the word plainly.** Each non-ASCII letter is mapped to the ASCII letter it resembles:
   accents are stripped; other letters are looked up in Unicode's table
   (`data/lookalikes.txt`), then in a short list of loose resemblances seen in real phishing
   mail (`τ` for t, `η` for n), then by Unicode name (`ø` is "o with stroke"). Upright strokes
   are tried as both `i` and `l`. A word with a letter that has no plain reading is left alone.
2. **Count the evidence in the whole text:** words that become known English words once read
   plainly, through foreign letters or through accents English does not use.
3. **Decide per word:**

| Word | Rewritten when |
|---|---|
| Mixes Latin with another alphabet | Its plain reading is a known word, or one other word in the text is evidence |
| Wholly in another alphabet | Plain reading is a known word (or two words of evidence), and the text is not in that language |
| A lone "a" or "I" in another alphabet | Only with evidence elsewhere |
| Accents English does not use (`yōũr`) | Plain reading is a known word and the word is lowercase, or there is evidence |
| Everyday accents or letters (`café`, `à`, `ł`) | Only with evidence elsewhere |
| Plain reading is not a known word | Only with three words of evidence |

Two guards apply to the whole text: at least half the plain ASCII words must be English, and a
text whose foreign-alphabet words mostly have no English reading is treated as that language
and left alone.

At `aggressive`, a looser variant also rewrites a lone lowercase word with everyday accents and
a lone "a" or "I", if 70% of the plain words are English. That is the main difference between
the two levels today: on the real phishing set it lifts recovery from 57% to 85%, and it costs
8 more clean texts out of 7,442 (correct foreign spellings such as `coupé`).

## Combining marks

`marks.py` removes marks laid over letters (strike-through, underline, stacked marks). An accent
typed as a separate mark is ordinary spelling, and phonetic notation uses rarer marks (`t͡s`),
so marks are removed only from a word that shows the trick:

- a letter carries three or more marks; or
- two or more letters carry a mark no alphabet spells with (one that Unicode never composes
  into a letter), and the word without marks is a known English word; or
- every letter of a word of three or more letters carries such a mark.

A word with such a mark that meets none of these (a one-letter word, a name, one marked letter)
is stripped only when another word in the text qualified. Marks of other scripts (Thai,
Devanagari) and emoji variation selectors are never touched.

## Leetspeak

`leet.py` reads `0 1 3 4 5 7 @ $ !` as the letters they resemble (`1` as `i` or `l`). `8` and
`2` are not read: they are used for their sound (`l8r`, `2day`), which is shorthand, not
disguise. A token is rewritten only if every digit and symbol in it has a reading:

| Token | Rewritten when |
|---|---|
| Reading is a known word, four or more characters, or three with the digit in the middle (`y0u`) | Always |
| Reading is a known word, but the token is short, or is a known word with a number or symbol at the edge (`test5`, `5ale`, `@mark`, `print$`) | Another token in the text was rewritten outright |
| Reading is not a known word (a name) | Three other tokens were rewritten outright |
| Money (`$5m`), number with a unit or ending (`5am`, `1st`), one or two letters with a number (`G5`, `b4`), `4` or `2` before a word (`4my`) | Never |

A reading known only as a name is capitalised (`@pril`), and a token at the start of a sentence
gets a capital. Elsewhere a capital hidden behind a digit cannot be recovered (`@rmy` for
"Army" comes back as "army").

`lookalike.py` asks `leet.py` when a word is joined to digits, so `аcc0unt` with a Cyrillic `а`
is recognised although neither transform alone sees a known word.

## State on 2026-10-12

Eighteen transforms exist: the fourteen at `conservative`, plus `homoglyph`,
`accent-substitution`, `combining-marks` and `leetspeak`. Not built yet: `separator`,
`repeated-chars`.
