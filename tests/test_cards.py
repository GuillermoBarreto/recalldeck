"""Tests for Markdown card parsing."""

import unittest

from recalldeck.cards import parse_markdown


class TestParseMarkdown(unittest.TestCase):
    def test_heading_and_body_become_card(self):
        cards = parse_markdown("## What is a closure?\nA function that keeps its scope.\n")
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].question, "What is a closure?")
        self.assertEqual(cards[0].answer, "A function that keeps its scope.")

    def test_multiple_cards(self):
        text = "## Q1\nA1\n\n## Q2\nA2 line 1\nA2 line 2\n"
        cards = parse_markdown(text)
        self.assertEqual([c.question for c in cards], ["Q1", "Q2"])
        self.assertEqual(cards[1].answer, "A2 line 1\nA2 line 2")

    def test_intro_before_first_heading_ignored(self):
        text = "# Python notes\nSome intro text.\n\n## Q1\nA1\n"
        cards = parse_markdown(text)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0].question, "Q1")

    def test_empty_answer_skipped(self):
        cards = parse_markdown("## Q1\n\n## Q2\nA2\n")
        self.assertEqual([c.question for c in cards], ["Q2"])

    def test_no_cards_returns_empty(self):
        self.assertEqual(parse_markdown("# Just a title\nSome text.\n"), [])


if __name__ == "__main__":
    unittest.main()
