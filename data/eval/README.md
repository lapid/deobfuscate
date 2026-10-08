# Evaluation sets

Built by `evaluation/corpus.py` and `evaluation/build.py`; do not edit by hand. Described in
`docs/evaluation.md`.

- `corpus_dev.txt`, `corpus_test.txt`: 2,000 clean texts each, one per line, taken from books
  in the public domain in the United States (published before 1929) as distributed by Project
  Gutenberg. Dev: Pride and Prejudice, The Adventures of Sherlock Holmes, The Great Gatsby,
  The Wonderful Wizard of Oz, Autobiography of Benjamin Franklin. Test: Alice's Adventures in
  Wonderland, Frankenstein, The Time Machine, Dubliners, The Age of Innocence.
- `dev/`, `test/`: `clean.jsonl` and `obfuscated.jsonl`, generated from the corpus with a fixed seed.

**Do not read the `test` files to get ideas for rules.**
