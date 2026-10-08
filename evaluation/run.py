"""Runs a system over an evaluation split and prints the scores.

    python -m evaluation.run                      # the deobfuscator, all levels, dev split
    python -m evaluation.run --system identity    # a baseline
    python -m evaluation.run --detail             # add the per-category tables

The test split is for reporting only: do not tune against it.
"""

import argparse
import json
import statistics
import time
from pathlib import Path

from evaluation import metrics, systems
from evaluation.tricks import LEVELS

EVAL = Path(__file__).resolve().parent.parent / "data" / "eval"


def load(split: str) -> list[dict]:
    rows: list[dict] = []
    for name in ("clean", "obfuscated"):
        with (EVAL / split / f"{name}.jsonl").open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle)
    return rows


def run(system: systems.System, samples: list[dict]) -> list[metrics.Outcome]:
    outcomes = []
    for sample in samples:
        started = time.perf_counter()
        output, transforms = system(sample["text"])
        seconds = time.perf_counter() - started
        outcomes.append(metrics.Outcome(sample, output, transforms, system(output)[0], seconds))
    return outcomes


def pct(value: float | None) -> str:
    return "    n/a" if value is None else f"{value * 100:6.1f}%"


def tally(item: metrics.Tally) -> str:
    return f"{pct(item.rate)}  ({item.hits}/{item.total})"


def print_report(title: str, report: metrics.Report, detail: bool) -> None:
    print(f"\n=== {title} ===")
    print(f"Clean texts changed (lower is better)   {tally(report.false_change)}")
    print(f"Obfuscated texts recovered exactly      {tally(report.recovered)}")
    print(f"Obfuscated texts made worse             {tally(report.made_worse)}")
    print(f"Mean character error, before -> after   {pct(report.mean_error_rate(False))} -> {pct(report.mean_error_rate(True))}")
    print(f"Above this level: recovered / worse     {tally(report.out_of_scope_recovered)} / {tally(report.out_of_scope_made_worse)}")
    print(f"Same result when run twice              {tally(report.idempotent)}")
    millis = sorted(second * 1000 for second in report.seconds)
    print(f"Time per text, median / 95th / max      {statistics.median(millis):.3f} / {millis[int(len(millis) * 0.95)]:.3f} / {millis[-1]:.3f} ms")

    print("\nBy text length          clean changed          recovered")
    for name, _, _ in metrics.LENGTH_BUCKETS:
        print(f"  {name:<20}  {tally(report.false_change_by_length[name]):<21}  {tally(report.recovered_by_length[name])}")
    print("\nBy kind of sample       recovered")
    for mode in ("whole", "partial", "stacked"):
        print(f"  {mode:<20}  {tally(report.recovered_by_mode[mode])}")
    if not detail:
        return

    print("\nClean texts changed, by category")
    for category, item in sorted(report.false_change_by_category.items()):
        print(f"  {category:<28}  {tally(item)}")
    print("\nRecovered, by trick")
    for (mode, category), item in sorted(report.recovered_by_category.items()):
        print(f"  {mode:<8} {category:<28}  {tally(item)}")
    names = sorted(set(report.transform_true) | set(report.transform_false) | set(report.transform_missed))
    print("\nStep record against tricks used    precision   recall")
    for name in names:
        print(f"  {name:<28}  {pct(report.precision(name))}    {pct(report.recall(name))}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--system", choices=("deobfuscate", "identity", "nfkc"), default="deobfuscate")
    parser.add_argument("--level", choices=LEVELS, action="append", help="strictness level; repeat for several (default: all)")
    parser.add_argument("--detail", action="store_true", help="also print per-category tables")
    args = parser.parse_args()

    samples = load(args.split)
    for level in args.level or LEVELS:
        system = systems.ours(level) if args.system == "deobfuscate" else getattr(systems, args.system)
        report = metrics.score(run(system, samples), level)
        print_report(f"{args.system}, scored at {level}, {args.split} split ({len(samples)} texts)", report, args.detail)


if __name__ == "__main__":
    main()
