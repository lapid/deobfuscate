# Research notes

Read this file first. It holds the conclusions; open a note only when you need the detail.
All notes were written on 2026-10-08. "Verified" means read from the source that day;
"from memory" means not checked and not to be relied on.

## Notes

| Note | Covers |
|---|---|
| [unicode-confusables.md](unicode-confusables.md) | UTS #39, the confusables table, mixed-script detection |
| [existing-tools.md](existing-tools.md) | Ciphey, CyberChef Magic, ftfy, decancer, disarm |
| [papers.md](papers.md) | Research on adversarial text and on obfuscated prompts |
| [plausibility-scoring.md](plausibility-scoring.md) | How to score "looks like English", and licensed data for it |
| [sample-sources.md](sample-sources.md) | Where samples can come from, licences, what the first real data showed |

## Conclusions

Each one changed the plan or the journal. Numbers are from the sources in the notes.

1. **The confusables table cannot be applied as it stands.** It is built for comparing two
   strings, not for restoring text. It maps `m` to `rn`, `1` and `I` to `l`, and `0` to `O`, so
   running it over clean English damages it. We use only the entries that go from a non-ASCII
   character to ASCII (2,262 of 6,712), and never an ASCII-to-ASCII entry.
2. **Unicode NFKC is not a substitute.** It covers 1,027 of those 2,262 entries (styled
   alphabets, fullwidth) and none of the cross-script lookalikes such as Cyrillic `а`.
3. **Mixed-script words are the cheap, safe signal for homoglyphs.** A word whose characters
   share no script is suspicious; a word wholly in one script is not, so real Russian or Greek is
   left alone. Words made entirely of lookalikes (`сосо`) carry no such signal and need the
   plausibility score.
4. **Every comparable tool is "search plus a checker".** Decoders propose, a plausibility check
   disposes, with a depth limit for nested layers. Our planned engine matches this; no redesign.
5. **Plausibility checks are weak on short text.** Both Ciphey and CyberChef say so. The
   evaluation must report results by text length, and the engine must be able to decline to act
   on short spans.
6. **Table lookup alone recovers little in real text.** One cited study reports about 35% of
   words restored by table lookup against about 96% with context. Context here means our
   word-level plausibility score. The 70% target for ambiguous tricks is unproven until measured.
7. **Preserve case, and normalise toward the surrounding script.** A benchmark found case-folding
   cost 3.4 points downstream, and that mapping Cyrillic-native text to Latin wrecked it.
   Confirms the minimal-edit and English-only pass-through decisions.
8. **Our niche is real.** The closest tool, decancer, lowercases by default and does not report
   what it changed. Nothing we found combines precision-first behaviour with a step record.
9. **Text-message shorthand is the hardest negative for leetspeak.** In real messages `sum1`
   means "someone", `l8r` "later", `4` "for", `2` "to". These digits stand for sounds, not shapes.
   A visual leetspeak decoder would turn `sum1` into `suml`. Leetspeak decoding must require the
   result to be a known word, and shorthand is not something we expand.
10. **Scorer data must be chosen for licence, not convenience.** `wordfreq` data is CC BY-SA 4.0
    and the project is frozen; Norvig's n-gram files state no data licence. The SCOWL word list
    has an MIT-like licence and can be shipped. Character n-gram counts we build ourselves from
    public-domain text.
11. **Obfuscations seen in the wild match the plan, with two additions:** hidden text in Unicode
    tag characters and other invisible carriers, and combining-mark overlays (strikethrough,
    "zalgo"). Both added to the taxonomy.

12. **Real phishing mail disguises words mostly with letters from other alphabets, one letter
    for one letter.** In 3,000 real sentences (BitCore, dev half): 47% contain Greek letters,
    44% accented Latin letters, 37% Cyrillic, 18% other Latin letters, 9% Armenian; 96% have the
    same length as their answer. Leetspeak, spacing and encodings are almost absent there.
    Accented Latin (`yōũr`) was not in our taxonomy at all and is now `accent-substitution`.
    It collides with the rule that real accents stay, so it must be decided per word.
13. **Our generator's lookalike table was too narrow.** It had no Greek lowercase letters such as
    `η` for n and `τ` for t, which real senders use heavily; they are added. Armenian, Cherokee
    and Runic lookalikes also occur and are not generated yet.

14. **A person disguising text by hand goes well beyond our taxonomy.** In the 25 hand-disguised
    dev sentences (`data/eval/human_dev.jsonl`):
    - About a third use lookalike generators that mix many alphabets and accents in one word
      (Cherokee, Armenian, Greek with accents, symbols such as `¢` for c and `₫` for d). A
      single-alphabet lookalike table will not cover these.
    - Some use heavy symbol leetspeak where one letter becomes several characters (`|-|` for H,
      `|\/|` for M). Our generator only swaps one character for one.
    - Some are stacked combining marks ("zalgo") that include ordinary accents.
    - Several are not character tricks at all: misspellings (`pirze`), dropped letters (`gol`),
      shorthand (`ur`, `TY`), and emoji standing for a word. These are out of scope by our own
      rules, so exact recovery on this set has a ceiling well below 100%. Character error is the
      fairer measure there.
    - Plain base64, URL escapes, reversal and dotted letters also appear, as the taxonomy expects.

15. **For lookalikes, the table is the easy part and the decision is the hard part.** On the
    dev half of the real phishing set, accent stripping covers 17% of substituted letters and
    Unicode's table 63%; a short hand list of loose resemblances (`τ`, `η`, `κ` and others)
    covers most of the rest. What limits recovery is deciding when a word may be touched:
    a lone accented word (`õn`) or a lone Greek `α` for "a" looks exactly like correct foreign
    spelling or a scientific symbol. Being strict about those gives 57% exact recovery with no
    clean text harmed; being loose gives 85% and harms 8 clean texts in 7,442.

## Not done

- No samples were produced with independent obfuscator tools; those are interactive web pages.
- SpamAssassin, Enron-Spam, Jigsaw, PhishTank, and the jailbreak datasets were not opened; their
  licences are unverified.
- The quadgram reference page (practicalcryptography.com) was unreachable.
- No test-only split exists yet. Every sample so far has been read by the agent, so all are `dev`.
