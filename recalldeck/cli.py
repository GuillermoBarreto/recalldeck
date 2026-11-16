"""Command-line interface for recalldeck.

Commands:
  import <notes.md> [--deck NAME]   add cards from a Markdown notes file
  review [--deck NAME] [--limit N]  quiz due cards, grade 0-5 after each
  due [--deck NAME]                 list cards due for review
  list [--deck NAME]                list all cards
  stats [--deck NAME]               show deck counts

Grades: 0 = total blackout, 3 = correct with effort, 5 = perfect recall.
"""

from __future__ import annotations

import argparse
import sys

from .cards import parse_file
from .store import connect, due_cards, list_cards, record_review, stats, upsert_card

GRADE_HELP = "0 blackout, 1 wrong but familiar, 2 wrong, 3 right with effort, 4 right, 5 perfect"


def _db(args: argparse.Namespace):
    return connect(args.db)


def cmd_import(args: argparse.Namespace) -> int:
    cards = parse_file(args.notes)
    conn = _db(args)
    for card in cards:
        upsert_card(conn, args.deck, card)
    print(f"imported {len(cards)} card(s) into deck '{args.deck}'")
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    conn = _db(args)
    due = due_cards(conn, args.deck)
    if args.limit:
        due = due[: args.limit]
    if not due:
        print("nothing due — you're all caught up")
        return 0
    print(f"{len(due)} card(s) due\n")
    for card in due:
        print(f"Q: {card.question}\n")
        input("press Enter to see the answer ...")
        print(f"A: {card.answer}\n")
        while True:
            try:
                grade = int(input(f"grade 0-5 ({GRADE_HELP}): ").strip())
            except ValueError:
                print("enter a number 0-5")
                continue
            if 0 <= grade <= 5:
                break
            print("grade must be 0-5")
        updated = record_review(conn, card.id, grade)
        due_date = updated.state.due.isoformat() if updated.state.due else "?"
        print(f"next review in {updated.state.interval_days} day(s), due {due_date}\n")
    return 0


def cmd_due(args: argparse.Namespace) -> int:
    conn = _db(args)
    due = due_cards(conn, args.deck)
    if not due:
        print("nothing due")
        return 0
    for card in due:
        due_date = card.state.due.isoformat() if card.state.due else "new"
        print(f"[{card.id}] ({card.deck}) {card.question} — due {due_date}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = _db(args)
    cards = list_cards(conn, args.deck)
    if not cards:
        print("no cards yet — import a notes file first")
        return 0
    for card in cards:
        due_date = card.state.due.isoformat() if card.state.due else "new"
        print(f"[{card.id}] ({card.deck}) {card.question} — due {due_date}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    conn = _db(args)
    result = stats(conn, args.deck)
    label = f"deck '{args.deck}'" if args.deck else "all decks"
    print(f"{label}: {result['total']} total, {result['new']} new, "
          f"{result['due']} due, {result['learned']} learned")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recalldeck",
        description="Spaced-repetition flashcards from Markdown study notes.",
    )
    parser.add_argument("--db", default=None, help="path to the SQLite database")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="add cards from a Markdown notes file")
    p_import.add_argument("notes", help="path to a .md file with ## headings as cards")
    p_import.add_argument("--deck", default="default", help="deck name (default: default)")
    p_import.set_defaults(func=cmd_import)

    p_review = sub.add_parser("review", help="quiz due cards")
    p_review.add_argument("--deck", default=None, help="only review this deck")
    p_review.add_argument("--limit", type=int, default=None, help="max cards this session")
    p_review.set_defaults(func=cmd_review)

    p_due = sub.add_parser("due", help="list cards due for review")
    p_due.add_argument("--deck", default=None)
    p_due.set_defaults(func=cmd_due)

    p_list = sub.add_parser("list", help="list all cards")
    p_list.add_argument("--deck", default=None)
    p_list.set_defaults(func=cmd_list)

    p_stats = sub.add_parser("stats", help="show deck counts")
    p_stats.add_argument("--deck", default=None)
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
