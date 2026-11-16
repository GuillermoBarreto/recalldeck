"""SQLite storage for cards and their review schedules.

One table, stdlib only. The database file defaults to
``~/.recalldeck/cards.db`` and can be overridden with RECALLDECK_DB.
Cards are keyed by (deck, question) so re-importing notes updates the
answer without duplicating the card or resetting its schedule.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .cards import Card
from .sm2 import DEFAULT_EASE, CardState, review

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    repetitions INTEGER NOT NULL DEFAULT 0,
    interval_days INTEGER NOT NULL DEFAULT 0,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (date('now')),
    updated_at TEXT NOT NULL DEFAULT (date('now')),
    UNIQUE (deck, question)
);
"""


@dataclass
class StoredCard:
    id: int
    deck: str
    question: str
    answer: str
    state: CardState


def default_db_path() -> Path:
    override = os.environ.get("RECALLDECK_DB")
    if override:
        return Path(override)
    return Path.home() / ".recalldeck" / "cards.db"


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path else default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _row_to_card(row: sqlite3.Row) -> StoredCard:
    due = date.fromisoformat(row["due_date"]) if row["due_date"] else None
    return StoredCard(
        id=row["id"],
        deck=row["deck"],
        question=row["question"],
        answer=row["answer"],
        state=CardState(
            repetitions=row["repetitions"],
            interval_days=row["interval_days"],
            ease_factor=row["ease_factor"],
            due=due,
        ),
    )


def upsert_card(conn: sqlite3.Connection, deck: str, card: Card) -> int:
    """Insert a card or update its answer, keeping any existing schedule."""
    cursor = conn.execute(
        """
        INSERT INTO cards (deck, question, answer)
        VALUES (?, ?, ?)
        ON CONFLICT(deck, question) DO UPDATE SET
            answer = excluded.answer,
            updated_at = date('now')
        """,
        (deck, card.question, card.answer),
    )
    conn.commit()
    return cursor.lastrowid


def list_cards(conn: sqlite3.Connection, deck: str | None = None) -> list[StoredCard]:
    query = "SELECT * FROM cards"
    params: list[str] = []
    if deck:
        query += " WHERE deck = ?"
        params.append(deck)
    query += " ORDER BY deck, question"
    return [_row_to_card(row) for row in conn.execute(query, params)]


def due_cards(
    conn: sqlite3.Connection, deck: str | None = None, today: date | None = None
) -> list[StoredCard]:
    """Cards due for review: never reviewed, or due date reached."""
    today = today or date.today()
    query = "SELECT * FROM cards WHERE due_date IS NULL OR due_date <= ?"
    params: list[str] = [today.isoformat()]
    if deck:
        query += " AND deck = ?"
        params.append(deck)
    query += " ORDER BY due_date IS NOT NULL, due_date, id"
    return [_row_to_card(row) for row in conn.execute(query, params)]


def record_review(
    conn: sqlite3.Connection,
    card_id: int,
    quality: int,
    today: date | None = None,
) -> StoredCard:
    """Grade a review and persist the new SM-2 schedule."""
    row = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if row is None:
        raise KeyError(f"no card with id {card_id}")
    card = _row_to_card(row)
    new_state = review(card.state, quality, today=today)
    conn.execute(
        """
        UPDATE cards SET repetitions = ?, interval_days = ?,
            ease_factor = ?, due_date = ?, updated_at = date('now')
        WHERE id = ?
        """,
        (
            new_state.repetitions,
            new_state.interval_days,
            new_state.ease_factor,
            new_state.due.isoformat() if new_state.due else None,
            card_id,
        ),
    )
    conn.commit()
    card.state = new_state
    return card


def stats(conn: sqlite3.Connection, deck: str | None = None) -> dict[str, int]:
    """Counts: total, new, due today, and learned (reviewed at least once)."""
    cards = list_cards(conn, deck)
    today = date.today()
    return {
        "total": len(cards),
        "new": sum(1 for c in cards if c.state.is_new()),
        "due": sum(1 for c in cards if c.state.due is None or c.state.due <= today),
        "learned": sum(1 for c in cards if c.state.repetitions > 0),
    }
