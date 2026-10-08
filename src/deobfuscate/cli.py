import argparse
import json
import sys

from deobfuscate.core import STRICTNESS_LEVELS, deobfuscate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="deobfuscate",
        description="Undo text obfuscation. Reads the text argument, or standard input if none is given.",
    )
    parser.add_argument("text", nargs="?", help="text to deobfuscate; standard input if omitted")
    parser.add_argument("--strictness", choices=STRICTNESS_LEVELS, default="conservative")
    parser.add_argument("--json", action="store_true", help="print the text and the steps applied as JSON")
    args = parser.parse_args(argv)

    text = args.text if args.text is not None else sys.stdin.read()
    result = deobfuscate(text, strictness=args.strictness)
    if args.json:
        json.dump(result.to_dict(), sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(result.text)
    return 0
