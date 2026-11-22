"""Download and extract deployed runtime assets on a persistent host."""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import zipfile

from huggingface_hub import hf_hub_download


def ensure_runtime_assets() -> Path:
    """Ensure the corpus assets exist and return their deployment root."""

    runtime_root = Path(
        os.getenv("RUNTIME_ASSETS_DIR", "/var/data")
        if os.getenv("RENDER", "")
        else os.getenv("RUNTIME_ASSETS_DIR", "runtime-assets")
    )
    runtime_root.mkdir(parents=True, exist_ok=True)

    bm25_path = runtime_root / "bm25_database.db"
    vector_path = runtime_root / "vector_db"
    corpus_path = runtime_root / "data" / "corpus"

    if bm25_path.is_file() and vector_path.is_dir() and corpus_path.is_dir():
        return runtime_root

    repo_id = os.getenv("HF_DATASET_REPO")
    asset_file = os.getenv("HF_ASSET_FILE", "qasper-runtime-assets.zip")
    token = os.getenv("HF_TOKEN")
    if not repo_id:
        raise RuntimeError("HF_DATASET_REPO is required to download runtime assets")

    archive = hf_hub_download(
        repo_id=repo_id,
        repo_type="dataset",
        filename=asset_file,
        token=token,
        cache_dir=str(runtime_root / ".hf-cache"),
    )

    with zipfile.ZipFile(archive, "r") as zipped:
        for member in zipped.infolist():
            target = (runtime_root / member.filename).resolve()
            if runtime_root.resolve() not in target.parents:
                raise RuntimeError("asset archive contains an invalid path")
        zipped.extractall(runtime_root)

    archive_corpus = runtime_root / "corpus"
    corpus_path = runtime_root / "data" / "corpus"
    if archive_corpus.is_dir() and not corpus_path.is_dir():
        corpus_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(archive_corpus), str(corpus_path))

    if not bm25_path.is_file() or not vector_path.is_dir() or not corpus_path.is_dir():
        raise RuntimeError("runtime asset archive did not contain the required directories")

    return runtime_root
