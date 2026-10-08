# Sample sources

Checked 2026-10-08. A source is "verified" only if its licence page was read that day.

| Source | Licence | Status |
|---|---|---|
| Self-written, generated with standard-library encoders | Ours, MIT | In `data/samples/` |
| SMS Spam Collection v.1, archive.ics.uci.edu/dataset/228 | CC BY 4.0 (verified); 5,574 messages | 10 messages in `data/samples/`, with credit |
| Wikipedia | CC BY-SA 4.0 (verified) | 2,000 texts per split in `data/eval/` |
| Wikinews | CC BY 2.5, CC BY 4.0 after 2024 (verified) | 1,000 texts per split in `data/eval/` |
| Stack Exchange | CC BY-SA, version reported per post by its API | 1,500 texts per split in `data/eval/` |
| Reddit, mainstream news | No open licence | Not usable |
| SCOWL word lists | MIT-like (verified) | For the scorer, not samples |
| "The Lies Characters Tell" repo | None stated (verified) | Not usable; offensive content |
| Mindgard evasion samples | Gated (per search) | Not usable |
| PointGuardAI OWASP benchmark | "other" (per search) | Not usable without review |
| SpamAssassin corpus, Enron-Spam, Jigsaw, PhishTank, JailbreakBench | Not checked | Open |
| Independent obfuscator web tools | n/a | Not done; interactive pages |

## Sources of real deliberate obfuscation (checked 2026-10-08)

| Source | What | Licence | Verdict |
|---|---|---|---|
| BitCore, huggingface.co/datasets/AutoML/bitcore (paper: arXiv 2502.05225, Findings of NAACL 2025) | 26,591 real sentences from phishing emails with visual perturbations, each paired with its restored text | None stated on the dataset or on github.com/CAU-AutoML/Bitabuse (both checked) | The best match found. Cannot be committed. Local evaluation only, unless the authors add a licence |
| BitViper, same authors | 298,989 synthetically perturbed sentences | None stated | Synthetic; lower value |
| "Set of obfuscated spam dataset by using LeetSpeak transformations", zenodo.org/records/6373653 | Public spam corpora with leetspeak applied by the authors' tool | CC BY 4.0 (verified on Zenodo) | Not real obfuscation, but made by a generator we did not write. Contents not inspected |
| Offensive-tweet homoglyph data ("The Lies Characters Tell") | Real homoglyph use in tweets | None stated | Not usable; offensive |
| Email spam corpora (SpamAssassin, Enron-Spam, TREC) | Real spam with leetspeak, separators, entities | Not checked | Would need candidate mining and hand labelling |

The core difficulty is ground truth, not volume: real obfuscated text has no known original.
Only three routes give labels: a dataset that ships restorations (BitCore), people obfuscating
text we chose (labels known by construction), or labelling by hand.

## What the SMS data showed

It was expected to supply obfuscated spam. It supplied something more useful: hard negatives.

- **Digits standing for sounds:** `sum1` (someone), `l8r` (later), `4` (for), `2` (to),
  `MobileUpd8`. Visual leetspeak rules give wrong answers on all of them.
- **Digits glued to words:** `goin2bed`, `Only1more`, `get4an18th`, `the4th`.
- **Codes inside prose:** claim codes (`KL341`), short codes, postcodes, premium phone numbers.
- **Real HTML entities:** 309 of 5,574 messages contain `&amp;`, `&lt;` or `&gt;`. Many are
  `&lt;#&gt;`, an anonymisation placeholder that correctly decodes to `<#>`.
- **One wrong-encoding case:** `ú1.20` where `£1.20` was meant.
- Very little deliberate letter-for-digit leetspeak, and almost no spaced-out words.

## What it changes for us

- Add a "shorthand" group to the clean set. Leetspeak decoding must not fire on it.
- HTML entity decoding is confirmed as common, real and safe.
- Spam of this era hides little; deliberate obfuscation samples must come from elsewhere.

## Attribution

Almeida, T. and Hidalgo, J. (2011). SMS Spam Collection [Dataset]. UCI Machine Learning
Repository. https://doi.org/10.24432/C5CC84. Licensed CC BY 4.0.
