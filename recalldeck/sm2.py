"""SM-2 spaced-repetition scheduling (SuperMemo 2).

Each card carries a repetition count, an interval in days, and an ease
factor. After a review the grader scores recall from 0 (total blackout)
to 5 (perfect recall). Scores below 3 restart the card; scores of 3 and
above grow the interval, roughly multiplying it by the ease factor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

MIN_EASE = 1.3
DEFAULT_EASE = 2.5


@dataclass
class CardState:
    """Scheduling state for one flashcard."""

    repetitions: int = 0
    interval_days: int = 0
    ease_factor: float = DEFAULT_EASE
    due: date | None = None

    def is_new(self) -> bool:
        return self.repetitions == 0 and self.interval_days == 0


def review(state: CardState, quality: int, today: date | None = None) -> CardState:
    """Return the new scheduling state after a review graded 0-5.

    Raises ValueError for grades outside 0-5.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"quality must be 0-5, got {quality}")
    today = today or date.today()

    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        if state.repetitions == 0:
            interval = 1
        elif state.repetitions == 1:
            interval = 6
        else:
            interval = max(1, round(state.interval_days * state.ease_factor))
        repetitions = state.repetitions + 1

    ease = state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(MIN_EASE, ease)

    return CardState(
        repetitions=repetitions,
        interval_days=interval,
        ease_factor=round(ease, 2),
        due=today + timedelta(days=interval),
    )
