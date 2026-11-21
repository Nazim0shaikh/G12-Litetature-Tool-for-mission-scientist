"""Evidence selection and traceable LLM context construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.services.retrieval_service import RetrievedPassage


@dataclass(frozen=True)
class ContextConfig:
    """Limits applied while selecting evidence for a model request."""

    max_context_chars: int = 12000
    max_passages: int = 8
    max_passages_per_paper: int = 3

    def __post_init__(self) -> None:
        if any(
            value <= 0
            for value in (
                self.max_context_chars,
                self.max_passages,
                self.max_passages_per_paper,
            )
        ):
            raise ValueError("context limits must be positive")


@dataclass(frozen=True)
class ContextResult:
    """Selected evidence, rendered context, and explicit omissions."""

    question: str
    passages: tuple[RetrievedPassage, ...]
    context: str
    omitted_passage_ids: tuple[str, ...]


class ContextBuilder:
    """Select ranked evidence and render it without partial passages."""

    def __init__(self, config: ContextConfig | None = None) -> None:
        self.config = config or ContextConfig()

    def build(
        self,
        question: str,
        passages: Sequence[RetrievedPassage],
    ) -> ContextResult:
        """Build a bounded context from ranked passages.

        A passage is either included in full or listed in
        ``omitted_passage_ids``. This prevents accidental loss of evidence
        caused by character-level truncation.
        """

        if not question.strip():
            raise ValueError("question must not be empty")

        selected: list[RetrievedPassage] = []
        omitted: list[str] = []
        seen_ids: set[str] = set()
        paper_counts: dict[str, int] = {}
        blocks: list[str] = [f"RESEARCH QUESTION:\n{question.strip()}\n\nAVAILABLE EVIDENCE:"]
        current_length = len(blocks[0])

        for passage in passages:
            passage_id = passage.passage_id
            if passage_id in seen_ids:
                omitted.append(passage_id)
                continue
            seen_ids.add(passage_id)

            if len(selected) >= self.config.max_passages:
                omitted.append(passage_id)
                continue
            if paper_counts.get(passage.paper_id, 0) >= self.config.max_passages_per_paper:
                omitted.append(passage_id)
                continue

            block = self._format_passage(len(selected) + 1, passage)
            separator_length = 2 if selected else 2
            if current_length + separator_length + len(block) > self.config.max_context_chars:
                omitted.append(passage_id)
                continue

            selected.append(passage)
            paper_counts[passage.paper_id] = paper_counts.get(passage.paper_id, 0) + 1
            blocks.append(block)
            current_length += separator_length + len(block)

        return ContextResult(
            question=question.strip(),
            passages=tuple(selected),
            context="\n\n".join(blocks),
            omitted_passage_ids=tuple(omitted),
        )

    @staticmethod
    def _format_passage(index: int, passage: RetrievedPassage) -> str:
        return (
            f"[PASSAGE {index}]\n"
            f"Passage ID: {passage.passage_id}\n"
            f"Paper ID: {passage.paper_id}\n"
            f"Paper Title: {passage.title}\n"
            f"Section: {passage.section_name}\n"
            f"Text: {passage.text}"
        )
