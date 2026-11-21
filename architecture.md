# Architecture

## Runtime flow

```text
User question
  -> question validation and whitespace normalization
  -> dense retrieval through ChromaDB
  -> BM25 retrieval through SQLite FTS5
  -> reciprocal rank fusion
  -> cross encoder reranking
  -> evidence selection and bounded context construction
  -> OpenAI-compatible LLM generation
  -> citation and evidence validation
  -> refusal or sufficiency assessment
  -> structured API response
```

## Core components

### Existing retrieval indexes

- `vector_db/` contains the prebuilt ChromaDB collection.
- `bm25_database.db` contains the prebuilt SQLite FTS5 table.
- The embedding model is
  `sentence-transformers/all-MiniLM-L6-v2`.
- The reranker is
  `cross-encoder/ms-marco-MiniLM-L-6-v2`.

These indexes are treated as existing infrastructure. Normal API startup does
not rebuild or reembed them.

### Backend services

- `app/services/query_processor.py`: validates and normalizes questions.
- `app/services/retrieval_service.py`: dense, BM25, and RRF retrieval.
- `app/services/reranker.py`: cross encoder reranking.
- `app/services/context_builder.py`: evidence deduplication and context limits.
- `app/services/llm_service.py`: OpenAI-compatible provider transport.
- `app/services/answer_generator.py`: strict structured answer parsing.
- `app/services/citation_validator.py`: structural and semantic citation checks.
- `app/services/refusal_handler.py`: answerability classification.
- `app/services/rag_pipeline.py`: end-to-end orchestration.

### API

FastAPI exposes the ask, retrieve, health, configuration, and paper endpoints.
CPU-bound model work is performed synchronously. The pipeline is initialized
on the first retrieval or answer request to keep API startup lightweight.

### Frontend

The Vite and React frontend uses a restrained research workspace layout. It
shows loading, answer, refusal, and source evidence states and does not expose
API keys or backend configuration secrets.

## Security boundaries

- LLM secrets are read from environment variables.
- `.env` is excluded from Git.
- Research passages are evidence, not instructions to the model.
- API responses do not expose credentials or provider secrets.
- Citation IDs must belong to selected evidence before they are accepted.

## Known limitations

- A semantic citation verifier is optional and is not assumed to be perfect.
- Structural citation validity and claim support are separate concepts.
- Raw reranker scores are not calibrated probabilities.
- Token-overlap answer relevance is a diagnostic, not semantic correctness.
- The test suite uses mocks for external providers and model behavior.
