# recalldeck

Spaced-repetition flashcards from Markdown study notes — a small CLI that schedules reviews with SM-2.

Write your study notes as Markdown, one card per `##` heading. recalldeck imports them into a local SQLite database, quizzes you on the cards that are due, and spaces the next review further out each time you remember a card (and pulls it back in when you don't).

No accounts, no servers, no paid APIs. Your notes and your schedule stay on your machine.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/GuillermoBarreto/recalldeck.git
cd recalldeck
pip install -e .
```

## Usage

Write notes like this (`notes.md`):

```markdown
# Networking

## What does TCP guarantee?
Ordered, reliable delivery — lost segments are retransmitted.

## What does UDP trade away for speed?
Reliability and ordering; the application handles what it needs.
```

Then:

```bash
# import cards into a deck (re-importing updates answers, keeps schedules)
recalldeck import notes.md --deck networks

# see what's due
recalldeck due --deck networks

# review — press Enter to reveal the answer, then grade yourself 0-5
recalldeck review --deck networks

# counts across all decks
recalldeck stats
```

Grades: `0` total blackout, `1` wrong but familiar, `2` wrong, `3` right with effort, `4` right, `5` perfect recall. Scores below 3 restart the card; 3 and up grow the interval (1 day, then 6 days, then interval × ease factor).

The database lives at `~/.recalldeck/cards.db` by default; set `RECALLDECK_DB` or pass `--db <path>` to use another location.

## How it works

- `recalldeck/cards.py` — parses `##` headings into question/answer cards.
- `recalldeck/sm2.py` — the SM-2 scheduling algorithm (repetitions, interval, ease factor).
- `recalldeck/store.py` — SQLite storage; cards are keyed by deck + question.
- `recalldeck/cli.py` — the `import`, `review`, `due`, `list`, and `stats` commands.

## Tests

```bash
python -m unittest discover -s tests
```

## Roadmap

- Import from Anki `.apkg` exports.
- Per-card review history and retention stats over time.
- A `--shuffle` review mode and a daily review reminder.
- Optional sync of the SQLite file to a private repo (notes stay local by default).
