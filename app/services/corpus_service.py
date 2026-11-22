"""Lazy access to original QASPER corpus passages."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import os


class CorpusService:
    """Load the corpus only when a paper lookup is requested."""

    def __init__(self, corpus_path: str | Path = "data/corpus") -> None:
        if str(corpus_path) == "data/corpus":
            runtime = os.getenv("RUNTIME_ASSETS_DIR", "/var/data" if os.getenv("RENDER") else "runtime-assets")
            corpus_path = Path(runtime) / "data" / "corpus"
        self.corpus_path = str(corpus_path)
        self._dataset: Any = None

    def get_paper(self, paper_id: str) -> dict[str, Any] | None:
        if not paper_id.strip():
            raise ValueError("paper_id must not be empty")
        if self._dataset is None:
            if not Path(self.corpus_path).is_dir():
                from app.assets import ensure_runtime_assets

                ensure_runtime_assets()
            from datasets import load_from_disk

            self._dataset = load_from_disk(self.corpus_path)["train"]

        passages: list[dict[str, Any]] = []
        title: str | None = None
        for row in self._dataset:
            passage_id = str(row["id"])
            if passage_id.rsplit("_", 1)[0] != paper_id:
                continue
            title = title or row.get("title")
            passages.append(
                {
                    "passage_id": passage_id,
                    "paper_id": paper_id,
                    "title": row.get("title") or "",
                    "section_name": row.get("section_name") or "",
                    "text": row.get("text") or "",
                }
            )
        if not passages:
            return None
        return {"paper_id": paper_id, "title": title or "", "passages": passages}
