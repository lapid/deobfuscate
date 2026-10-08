# Existing tools

Read for ideas only. None of these may be imported by the tool (see journal). They may be used
as comparison baselines in evaluation. Read 2026-10-08; verified from each project's own page
unless marked.

## Ciphey

- **Source:** https://github.com/bee-san/Ciphey . MIT.
- The repository is now a Rust program (the page says the earlier Python Ciphey 5.x is still on PyPI).
- A* search over chains of decoders, most promising first; stops at the first result a checker
  accepts; 5-second default timeout.
- Checkers: an English checker ("gibberish-or-not"), a format identifier for things like IP
  addresses and tokens, a word list, or a user regex.
- By default it asks the human to confirm each hit. Its page says detection is imperfect for
  short phrases, non-English text, and JSON.
- 24 decoders, including base64/32/58/91, hex, binary, URL, Morse, Caesar, ROT47, Atbash,
  Vigenere, reversed text.
- **For us:** same architecture as planned. "Stop at first accepted" plus a human prompt shows
  the checker is not trusted; we need a margin, not a pass/fail. A format identifier is a good
  idea in reverse: recognise hashes, UUIDs and keys so we leave them alone.

## CyberChef "Magic"

- **Source:** https://github.com/gchq/CyberChef/wiki/Automatic-detection-of-encoded-data-using-CyberChef-Magic
- Each operation has regular expressions describing input it could decode. Matches are run
  speculatively, each result is scored and searched again, up to a depth limit.
- Scoring signals: recognised file signature, valid UTF-8, Shannon entropy (lower is better),
  and a chi-squared fit of byte frequencies against English Wikipedia.
- Stated limit: the English check is reliable only when a good share of the data is English.
- **For us:** cheap pre-filters before the scorer: is the decoded result valid UTF-8, is it
  printable, did entropy drop. These reject most wrong decodes of hashes and keys at no cost.

## ftfy

- **Source:** https://ftfy.readthedocs.io/ (heuristic and explanation pages). Licence not checked.
- Repairs text decoded with the wrong character encoding, plus entities, ligatures, fullwidth.
- Detection is by context: about 400 characters typical of mis-decoded UTF-8, flagged only in
  sequences far more likely to be damage than intent. The same test says when to stop fixing.
- The docs warn that longer strings are more likely to trigger a false positive.
- `fix_and_explain()` returns the steps applied, and a plan that can be replayed on similar text.
- **For us:** the model for our step record. Detect by context, never by one character.
  Wrong-encoding repair is ftfy's whole subject; we treat it as out of v1 scope (open question).

## decancer

- **Source:** https://github.com/null8626/decancer . MIT. Rust, with bindings.
- Table lookup over 222,634 code points: homoglyphs, most leetspeak, diacritics, "zalgo", bidi.
- Output appears lowercased unless an option is set; the page describes no change record.
- **For us:** the closest existing tool, built for matching (is this word in my blocklist?), not
  for restoring readable text. Useful as a comparison baseline.

## disarm benchmark

- **Source:** https://translit.readthedocs.io/en/latest/security/adversarial-defense.html
  (documentation of the disarm project; benchmark results appear to be the project's own).
- 8 preprocessing tools, 6 attack types, 435,864 observations on sentiment, toxicity and news models.
- ftfy was statistically equivalent to no preprocessing against these attacks.
- NFC/NFKC/NFKD/casefold gave no meaningful defence against homoglyphs.
- `unidecode` significantly degraded accuracy on invisible-character attacks.
- Case-folding cost 3.4 points on cased models. Mapping Cyrillic-native text to Latin dropped
  the model to near chance.
- Cites Lee et al. 2025, "BitAbuse" (arXiv 2502.05225): table lookup restored about 35% of
  perturbed words in real phishing text, a context-aware model about 96%. Not read at source.
- **For us:** preserve case; never map text that is natively non-Latin; expect table lookup
  alone to fall short on real data.
