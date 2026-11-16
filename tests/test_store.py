"""Tests for the SQLite card store."""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from recalldeck.cards import Card
from recalldeck.store import connect, due_cards, list_cards, record_review, stats, upsert_card


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.conn = connect(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_upsert_and_list(self):
        upsert_card(self.conn, "python", Card("Q1", "A1"))
        upsert_card(self.conn, "python", Card("Q2", "A2"))
        cards = list_cards(self.conn, "python")
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].question, "Q1")

    def test_reimport_updates_answer_keeps_schedule(self):
        upsert_card(self.conn, "python", Card("Q1", "A1"))
        card = list_cards(self.conn)[0]
        record_review(self.conn, card.id, 5, today=date(2026, 11, 16))
        upsert_card(self.conn, "python", Card("Q1", "A1 improved"))
        updated = list_cards(self.conn)[0]
        self.assertEqual(updated.answer, "A1 improved")
        self.assertEqual(updated.state.repetitions, 1)

    def test_new_cards_are_due(self):
        upsert_card(self.conn, "python", Card("Q1", "A1"))
        self.assertEqual(len(due_cards(self.conn, today=date(2026, 11, 16))), 1)

    def test_reviewed_card_not_due_until_due_date(self):
        upsert_card(self.conn, "python", Card("Q1", "A1"))
        card = list_cards(self.conn)[0]
        record_review(self.conn, card.id, 5, today=date(2026, 11, 16))
        self.assertEqual(due_cards(self.conn, today=date(2026, 11, 16)), [])
        self.assertEqual(len(due_cards(self.conn, today=date(2026, 11, 17))), 1)

    def test_stats_counts(self):
        upsert_card(self.conn, "python", Card("Q1", "A1"))
        upsert_card(self.conn, "python", Card("Q2", "A2"))
        card = list_cards(self.conn)[0]
        record_review(self.conn, card.id, 5, today=date(2026, 11, 16))
        result = stats(self.conn, "python")
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["new"], 1)
        self.assertEqual(result["learned"], 1)

    def test_unknown_card_review_raises(self):
        with self.assertRaises(KeyError):
            record_review(self.conn, 999, 5)


if __name__ == "__main__":
    unittest.main()
