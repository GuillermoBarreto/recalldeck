"""Tests for the CLI import/list/stats flow (non-interactive commands)."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from recalldeck.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "cards.db")
        self.notes = Path(self.tmp.name) / "notes.md"
        self.notes.write_text("## What is TCP?\nA reliable transport protocol.\n\n## What is UDP?\nA fast, connectionless protocol.\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["--db", self.db, *argv])
        return code, out.getvalue()

    def test_import_then_list_then_stats(self):
        code, out = self.run_cli("import", str(self.notes), "--deck", "networks")
        self.assertEqual(code, 0)
        self.assertIn("imported 2 card(s)", out)

        code, out = self.run_cli("list", "--deck", "networks")
        self.assertIn("What is TCP?", out)
        self.assertIn("What is UDP?", out)

        code, out = self.run_cli("stats", "--deck", "networks")
        self.assertIn("2 total", out)
        self.assertIn("2 new", out)

    def test_due_lists_new_cards(self):
        self.run_cli("import", str(self.notes), "--deck", "networks")
        code, out = self.run_cli("due", "--deck", "networks")
        self.assertIn("What is TCP?", out)

    def test_review_with_no_due_cards(self):
        code, out = self.run_cli("review")
        self.assertIn("nothing due", out)

    def test_interactive_review_grades_and_reschedules(self):
        self.run_cli("import", str(self.notes), "--deck", "networks")
        # Two cards: Enter to reveal, then grade 5, for each.
        answers = iter(["", "5", "", "5"])
        with patch("builtins.input", side_effect=lambda *a: next(answers)):
            code, out = self.run_cli("review", "--deck", "networks")
        self.assertEqual(code, 0)
        self.assertIn("next review in 1 day(s)", out)
        code, out = self.run_cli("due", "--deck", "networks")
        self.assertIn("nothing due", out)


if __name__ == "__main__":
    unittest.main()
