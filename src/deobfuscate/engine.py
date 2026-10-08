"""Applies transforms until nothing more improves the text.

Transforms propose replacements; the engine decides. For each proposal it first
deobfuscates the replacement itself, so layered obfuscation is judged by what it
finally turns into, then applies the proposal only if that result reads more
like English than the text it replaces.
"""

from dataclasses import dataclass

from deobfuscate import scorer
from deobfuscate.protect import overlaps, protected_spans
from deobfuscate.transforms import ALL, Candidate, Transform
from deobfuscate.types import Step

LEVELS = ("conservative", "balanced", "aggressive")

# Longer inputs are returned unchanged.
MAX_INPUT_CHARS = 100_000
# How many layers deep a replacement may itself be deobfuscated.
MAX_DEPTH = 4
# How many replacements one text, or one layer of it, may receive.
MAX_STEPS = 200


@dataclass(frozen=True, slots=True)
class Policy:
    """What it takes for a judged proposal to be accepted."""

    # The result must score at least this much as English (0 to 1).
    min_score: float
    # The result must beat what it replaces by at least this much.
    min_gain: float
    # The result must contain at least this many letters to be judged at all.
    min_letters: int


# Starting values; tuned on the dev split in Phase 4.
POLICIES = {
    "conservative": Policy(min_score=0.70, min_gain=0.30, min_letters=10),
    "balanced": Policy(min_score=0.60, min_gain=0.25, min_letters=6),
    "aggressive": Policy(min_score=0.50, min_gain=0.15, min_letters=4),
}


@dataclass(frozen=True, slots=True)
class Accepted:
    transform: Transform
    candidate: Candidate
    final: str
    inner_steps: tuple[Step, ...]
    confidence: float
    gain: float


class Engine:
    def __init__(self, level: str, transforms: tuple[Transform, ...] = ALL) -> None:
        self.policy = POLICIES[level]
        limit = LEVELS.index(level)
        self.transforms = tuple(t for t in transforms if LEVELS.index(t.level) <= limit)
        # Verdicts depend only on the transform and the two texts, and the same
        # proposals come up again after every accepted step.
        self.verdicts: dict[tuple[str, str, str], Accepted | None] = {}

    def run(self, text: str, depth: int = 0) -> tuple[str, tuple[Step, ...]]:
        if len(text) > MAX_INPUT_CHARS:
            return text, ()
        steps: list[Step] = []
        for _ in range(MAX_STEPS):
            best = self.best_proposal(text, depth)
            if best is None:
                break
            candidate = best.candidate
            steps.append(Step(best.transform.name, candidate.start, candidate.end, text[candidate.start : candidate.end],
                              candidate.replacement, round(best.confidence, 3), candidate.hidden))
            # Inner steps were found on the replacement alone; move them to where it now sits.
            steps.extend(Step(s.transform, s.start + candidate.start, s.end + candidate.start, s.before, s.after,
                              s.confidence, s.hidden) for s in best.inner_steps)
            text = text[: candidate.start] + best.final + text[candidate.end :]
        return text, tuple(steps)

    def best_proposal(self, text: str, depth: int) -> Accepted | None:
        protected = protected_spans(text)
        best: Accepted | None = None
        for transform in self.transforms:
            for candidate in transform.propose(text):
                before = text[candidate.start : candidate.end]
                if candidate.replacement == before:
                    continue
                if not transform.ignores_protection and overlaps(candidate.start, candidate.end, protected):
                    continue
                verdict = self.judge(transform, candidate, before, depth)
                if verdict is not None and (best is None or verdict.gain > best.gain):
                    best = verdict
        return best

    def judge(self, transform: Transform, candidate: Candidate, before: str, depth: int) -> Accepted | None:
        key = (transform.name, before, candidate.replacement)
        if key not in self.verdicts:
            self.verdicts[key] = self.decide(transform, candidate, before, depth)
        found = self.verdicts[key]
        # The cached verdict was reached for the same texts, possibly at another position.
        return None if found is None else Accepted(found.transform, candidate, found.final, found.inner_steps,
                                                   found.confidence, found.gain)

    def decide(self, transform: Transform, candidate: Candidate, before: str, depth: int) -> Accepted | None:
        final, inner_steps = candidate.replacement, ()
        if depth < MAX_DEPTH:
            final, inner_steps = self.run(candidate.replacement, depth + 1)
        if not transform.judged:
            return Accepted(transform, candidate, final, inner_steps, 1.0, 1.0)
        if scorer.letter_count(final) < self.policy.min_letters:
            return None
        after_score = scorer.english_score(final)
        gain = after_score - scorer.english_score(before)
        if after_score < self.policy.min_score or gain < self.policy.min_gain:
            return None
        return Accepted(transform, candidate, final, inner_steps, after_score, gain)
