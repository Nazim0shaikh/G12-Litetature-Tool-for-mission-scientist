# G12 AI Research Assistant

An evidence grounded research assistant for the QASPER corpus. The pipeline
uses the existing Chroma dense index, SQLite FTS5 BM25 index, reciprocal rank
fusion, cross encoder reranking, bounded context construction, and an
OpenAI compatible LLM endpoint.

## Run locally

The project uses the existing Windows virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The first ask or retrieve request loads the embedding and reranker models.
This keeps API startup responsive and avoids model downloads during imports.

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`. Configure the LLM
variables in `.env` before using `/api/v1/ask`. Retrieval and paper lookup can
be exercised without LLM credentials.

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests -q
Set-Location frontend
npm run build
```

## API

- `POST /api/v1/ask` generates an evidence grounded answer.
- `POST /api/v1/retrieve` returns reranked evidence without generation.
- `GET /api/v1/health` reports API and LLM configuration status.
- `GET /api/v1/config` returns safe non secret settings.
- `GET /api/v1/paper/{paper_id}` returns original corpus passages.

The frontend displays passage IDs, source metadata, and the exact supporting
text. Citation existence and semantic support are reported separately.

See [architecture.md](architecture.md) for system boundaries and component
details. See [evaluation/README.md](evaluation/README.md) for metric definitions
and the development/test split policy.

## Deploy runtime assets

Runtime indexes are downloaded from a private Hugging Face Dataset instead of
being stored in Git.

Set these backend environment variables:

```env
HF_DATASET_REPO=nazim001/Corpus_for_fieldSearch
HF_ASSET_FILE=qasper-runtime-assets.zip
HF_TOKEN=your_hugging_face_read_token
RUNTIME_ASSETS_DIR=/var/data
RENDER=1
```

The first backend request downloads the archive, extracts it into the persistent
directory, and normalizes the corpus path. Subsequent requests reuse extracted
files. Keep both Hugging Face and OpenRouter tokens as hosting secrets, never in
Git or the frontend.
