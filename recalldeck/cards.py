"""Parse flashcards out of Markdown study notes.

Format: every level-2 heading (``## ...``) starts a card. The heading
text is the question; everything until the next level-2 heading (or end
of file) is the answer. Level-1 headings and other content before the
first ``##`` are ignored, so a notes file can keep its title and intro.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

HEADING_RE = re.compile(r"^##\s+(?P<question>.+?)\s*$")


@dataclass(frozen=True)
class Card:
    question: str
    answer: str


def parse_markdown(text: str) -> list[Card]:
    """Parse all flashcards from a Markdown document."""
    cards: list[Card] = []
    question: str | None = None
    answer_lines: list[str] = []

    def flush() -> None:
        nonlocal question, answer_lines
        if question is not None:
            answer = "\n".join(answer_lines).strip()
            if answer:
                cards.append(Card(question=question, answer=answer))
        question = None
        answer_lines = []

    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            flush()
            question = match.group("question")
        elif question is not None:
            answer_lines.append(line)
    flush()
    return cards


def parse_file(path: str) -> list[Card]:
    """Parse all flashcards from a Markdown file."""
    with open(path, encoding="utf-8") as handle:
        return parse_markdown(handle.read())
