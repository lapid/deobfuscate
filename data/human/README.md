# Hand-disguised sentences

`to_disguise.txt` lists 50 clean sentences written for this project, each followed by a
disguised version typed by the project owner. Because the original is known, each pair is a
human-made obfuscation sample with a certain answer. MIT-licensed.

`uv run python -m evaluation.human` turns the sheet into `data/eval/human_<split>.jsonl`.
Sentences are assigned to dev or test by their number.

**Agents: do not read the answers in `to_disguise.txt` or `human_test.jsonl`.** Half of them are
test data. Read `data/eval/human_dev.jsonl` instead.

Two answers in the dev half were typed under the wrong sentence and are re-paired in
`evaluation/human.py`. The test half has not been checked for the same slip.
