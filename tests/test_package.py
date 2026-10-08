import io
import json
import unittest
from contextlib import redirect_stdout

from deobfuscate import Result, Step, deobfuscate
from deobfuscate.cli import main


class InterfaceTest(unittest.TestCase):
    def test_returns_a_result(self):
        result = deobfuscate("plain text")
        self.assertIsInstance(result, Result)
        self.assertEqual(result.text, "plain text")
        self.assertFalse(result.changed)

    def test_rejects_unknown_strictness(self):
        with self.assertRaises(ValueError):
            deobfuscate("x", strictness="reckless")

    def test_result_serialises_steps(self):
        step = Step("base64", 0, 4, "aGk=", "hi", 0.9)
        data = Result("hi", (step,)).to_dict()
        self.assertEqual(data["steps"][0]["transform"], "base64")
        json.dumps(data)

    def test_cli_prints_json(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["hello", "--json"]), 0)
        self.assertEqual(json.loads(out.getvalue()), {"text": "hello", "steps": []})


if __name__ == "__main__":
    unittest.main()
