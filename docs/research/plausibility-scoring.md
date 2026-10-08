# Plausibility scoring and its data

Read 2026-10-08. Licences verified from each source unless marked.

## Signals used by others

- **Byte or letter frequency, chi-squared against English** (CyberChef). Weak on short text.
- **Shannon entropy** (CyberChef): random-looking output is probably a wrong decode.
- **Valid UTF-8 and printable characters**: free, and rejects most wrong decodes.
- **Dictionary or "is it gibberish" check** (Ciphey).
- **Characters per token** (Broken-Token paper): encoded text does not split into known units.
- **Character quadgram log-probability**: sum the log-probability of each four-letter window,
  with a floor for unseen ones. Standard in classical cipher solving. From memory; the usual
  reference page was unreachable.

## Data sources and licences

| Source | What | Licence | Usable |
|---|---|---|---|
| SCOWL / English Speller Database, github.com/en-wl/wordlist | Word lists by commonness, sizes 35 to 85 | MIT-like; keep the copyright notice. Lists above size 80 add a second notice | Yes, at size 80 or below |
| wordfreq, github.com/rspeer/wordfreq | Word frequencies | Code Apache; data CC BY-SA 4.0. Frozen at about 2021. Needs msgpack, langcodes, regex | No: share-alike data, and three extra packages |
| norvig.com/ngrams | Word counts, letter bigram and trigram counts from the Google web corpus | Code MIT; no licence stated for data | No, licence unclear |
| John Burkardt's NGRAMS | Letter n-gram counts | Pages disagree (MIT vs LGPL); not opened | Not without checking |
| Unicode `confusables.txt` | Lookalike table | Unicode License V3 | Yes, vendored |

## What it changes for us

- **Word list:** ship one generated from SCOWL at size 70 or below, with its notice.
  Size 60 is its "default spell-checking size, vetted for errors"; start there and let the dev
  set say whether 70 helps.
- **Character n-grams:** no ready-made table with a clear permissive licence was found. Build
  counts ourselves from public-domain English text and commit the build script and the table.
  The corpus is still to be chosen; old books skew formal, so check the fit on modern samples.
- **Order of checks, cheapest first:** valid and printable, then word-hit rate, then n-gram score.
- **Known weak spot:** short spans. Score per word for visual tricks, where a dictionary hit is
  strong evidence, and require more length before trusting a decoded encoding.
- A word list has no frequencies, so `suml` vs `sumi` vs `sum1` cannot be ranked by it alone.
  If ranking candidates matters, derive word frequencies from the same public-domain corpus.
