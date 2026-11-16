"""Tests for the SM-2 scheduling rules."""

import unittest
from datetime import date

from recalldeck.sm2 import CardState, review


class TestSM2(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 11, 16)

    def test_first_good_review_due_tomorrow(self):
        state = review(CardState(), 4, today=self.today)
        self.assertEqual(state.repetitions, 1)
        self.assertEqual(state.interval_days, 1)
        self.assertEqual(state.due, date(2026, 11, 17))

    def test_second_good_review_due_in_six_days(self):
        state = review(CardState(), 4, today=self.today)
        state = review(state, 4, today=self.today)
        self.assertEqual(state.repetitions, 2)
        self.assertEqual(state.interval_days, 6)

    def test_third_review_grows_by_ease_factor(self):
        state = review(CardState(), 5, today=self.today)
        state = review(state, 5, today=self.today)
        state = review(state, 5, today=self.today)
        self.assertEqual(state.repetitions, 3)
        self.assertGreaterEqual(state.interval_days, 15)

    def test_failed_review_restarts_card(self):
        state = review(CardState(), 5, today=self.today)
        state = review(state, 5, today=self.today)
        state = review(state, 1, today=self.today)
        self.assertEqual(state.repetitions, 0)
        self.assertEqual(state.interval_days, 1)

    def test_ease_factor_never_below_minimum(self):
        state = CardState(repetitions=3, interval_days=10, ease_factor=1.35)
        state = review(state, 3, today=self.today)
        self.assertGreaterEqual(state.ease_factor, 1.3)

    def test_perfect_recall_raises_ease(self):
        state = review(CardState(), 5, today=self.today)
        self.assertGreater(state.ease_factor, 2.5)

    def test_invalid_grade_rejected(self):
        with self.assertRaises(ValueError):
            review(CardState(), 6, today=self.today)
        with self.assertRaises(ValueError):
            review(CardState(), -1, today=self.today)


if __name__ == "__main__":
    unittest.main()
