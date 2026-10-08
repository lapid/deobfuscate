# Research papers

Found by search on 2026-10-08. Unless marked "read", only the search summary or abstract was
seen, so treat details as leads, not facts.

## Adversarial text and its normalisation

- **"Shielding Google's language toxicity model against adversarial attacks"** (arXiv 1801.01828).
  Early study: homoglyph substitution, bogus word segmentation, letter repetition.
- **"The Lies Characters Tell"** (Findings of ACL 2025, aclanthology 2025.findings-acl.969).
  LLMs undoing homoglyphs in offensive tweets. Repo: github.com/pcoopercoder/The-Lies-Characters-Tell,
  which states no licence (checked), so its data is not usable by us. Content is offensive.
- **Baszta** (arXiv 2609.29266). A canonicaliser in front of a classifier: folds Cyrillic and
  Greek lookalikes, repairs spacing, collapses repeats, reverses leetspeak. Improved robustness.
- **KOTOX** (arXiv 2510.10961, Korean) and **SinoGlyphBench** (arXiv 2609.05843, Chinese):
  benchmarks pairing clean and obfuscated text. Out of language scope; the paired design matches ours.
- **BitAbuse** (arXiv 2502.05225). Real phishing text; see the disarm entry in `existing-tools.md`.

## Obfuscated prompts

- **Broken-Token** (arXiv 2510.26847; abstract read). Flags encoded prompts by average characters
  per token: tokenisers trained on natural language split encoded text into many short tokens.
  Evaluation set built by applying Caesar, leetspeak, reversal, binary and base64 to public prompts.
- **"What Features in Prompts Jailbreak LLMs?"** (arXiv 2411.03343). 35 styles including
  leetspeak with `a` to `@`, `e` to `3`, `i` to `!`.
- **BELLS-O** (arXiv 2606.20668). Taxonomy includes ROT13 and base64 as cheap transformations.
- Gated or custom-licence datasets exist (Mindgard, PointGuardAI); not usable without review.

## What it changes for us

- The obfuscations used in practice are the ones in the plan: base64, ROT13/Caesar, leetspeak,
  reversal, binary, spacing, repetition, homoglyphs.
- Additions to the taxonomy: `!` as a leetspeak form of `i`; text hidden in invisible carriers
  (Unicode tag characters; this detail is from memory, not from these papers).
- "Characters per token" is the same idea as our word-hit rate: encoded text does not break
  into known units. Cheap detection signal before any decoding.
- Researchers build evaluation sets exactly as planned: clean text plus programmatic obfuscation.
