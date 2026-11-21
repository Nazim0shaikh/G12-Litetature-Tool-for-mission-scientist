"""Validation and normalization for research questions."""

from __future__ import annotations

from dataclasses import dataclass
import re


_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class ProcessedQuestion:
    """A validated question with its original text preserved."""

    original: str
    normalized: str


def process_question(question: str) -> ProcessedQuestion:
    """Validate and normalize a research question.

    Only surrounding and repeated whitespace is normalized. The original
    question is retained so callers can use it for evaluation and display.

    Raises:
        TypeError: If ``question`` is not a string.
        ValueError: If ``question`` is empty or contains only whitespace.
    """

    if not isinstance(question, str):
        raise TypeError("question must be a string")

    if not question.strip():
        raise ValueError("question must not be empty")

    normalized = _WHITESPACE.sub(" ", question).strip()
    return ProcessedQuestion(original=question, normalized=normalized)
