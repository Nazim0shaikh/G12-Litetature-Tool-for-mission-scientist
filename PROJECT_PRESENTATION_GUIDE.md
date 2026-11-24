# Fieldwork / G12 AI Research Assistant
## Project and presentation guide

This guide describes the repository's implemented system as it stands now. It
also marks the difference between what is implemented, what is a recorded
baseline, and what remains a limitation. Use it as a presentation script and a
technical reference; do not describe optional or future work as completed.

## 1. One-minute project summary

**Fieldwork** is a retrieval-augmented generation (RAG) research assistant for
scientific literature. It searches the QASPER-RAG corpus, combines semantic and
keyword retrieval, reranks candidate passages, and asks an LLM to answer from a
small, traceable evidence set. The result includes cited claims, passage IDs,
source metadata, and the original supporting passages. The goal is not to make
the LLM know the entire corpus; it is to find relevant evidence first and
constrain generation to that evidence.

The key design decision is to keep the system in separate, testable stages:

```text
Question
  -> validate and normalize
  -> dense retrieval + sparse keyword retrieval
  -> Reciprocal Rank Fusion (RRF)
  -> cross-encoder reranking
  -> bounded, traceable evidence context
  -> schema-constrained LLM answer
  -> citation-ID validation and sufficiency/refusal handling
  -> API response and clickable sources in the UI
```

**Short value statement:** Fieldwork makes scientific answers easier to inspect
by connecting generated claims to the exact retrieved passage IDs and source
text that informed them.

## 2. Problem and motivation

Scientific papers are long, terminology-heavy, and distributed across many
documents. Ordinary keyword search can miss conceptually similar wording, while
semantic search can miss exact technical terms, acronyms, or names. A
standalone LLM can produce fluent answers without showing where claims came
from.

Fieldwork addresses these problems by:

1. Searching an indexed scientific-paper corpus rather than sending the whole
   corpus to an LLM.
2. Combining semantic search with keyword search.
3. Reranking the combined candidates for the specific question.
4. Giving the model only a bounded set of selected passages.
5. Requiring structured output, validating cited passage IDs, and showing the
   corresponding source text.
6. Returning an insufficient-evidence response when the system decides the
   selected evidence is not adequate.

RAG improves traceability and can reduce unsupported answers; it does **not**
guarantee factual correctness. Retrieval quality, model behavior, and citation
support still need evaluation.

## 3. Dataset and indexed assets

The repository uses the Hugging Face dataset
[`DinoStackAI/qasper-rag`](https://huggingface.co/datasets/DinoStackAI/qasper-rag).
It includes paper passages, queries, relevance judgments (qrels), reference
answers, top-ranked results, and retrieved-document data.

Counts verified from the local dataset:

| Component | Train | Dev | Test |
|---|---:|---:|---:|
| Queries | 2,101 | 890 | 1,310 |
| Qrels | 3,815 | 1,913 | 3,434 |
| Reference answers | 2,101 | 890 | 1,310 |
| Top-ranked records | 2,101 | 890 | 1,310 |
| Retrieved documents | 20,985 | 8,894 | 13,089 |

The corpus contains **81,550 passages**. A passage has an ID, paper ID, title,
section name, and text. IDs such as `1909.00694_00012` identify a particular
passage; the paper ID is the portion before the final underscore-separated
passage index.

The existing local runtime assets were measured at approximately:

| Asset | Approximate size |
|---|---:|
| Chroma vector index (`vector_db/`) | 448.8 MB |
| SQLite FTS5 index (`bm25_database.db`) | 81.3 MB |
| Saved corpus (`data/corpus/`) | 46.8 MB |
| Compressed runtime archive | 309.8 MB |

These are local on-disk sizes and can vary as the assets change. The indexes
are built offline and reused at runtime; normal startup does not re-embed the
corpus or rebuild SQLite.

### How the indexes are built

- [`download_dataset.py`](download_dataset.py) downloads the six dataset
  components into `data/`.
- [`build_index.py`](build_index.py) loads the corpus, encodes passage text
  with `sentence-transformers/all-MiniLM-L6-v2`, normalizes the embeddings,
  and upserts them with passage metadata into the Chroma collection
  `qasper_passages`. The collection uses cosine distance.
- [`build_bm25.py`](build_bm25.py) builds an SQLite FTS5 virtual table named
  `corpus_fts`. Its tokenizer is `porter unicode61`; the ID column is
  unindexed, and title, section, and passage text are indexed.
- The runtime connects to these persisted indexes instead of running the
  build scripts for each question.

## 4. Full algorithm: what happens to one question

### Stage 1 — Input validation and normalization

The API accepts a question up to 2,000 characters. The question processor
rejects non-string and all-whitespace questions, collapses repeated whitespace,
and trims the ends. It preserves the original question for display and
evaluation. It deliberately does not use an LLM to rewrite the question, so
technical terms and the user's meaning are not silently changed.

### Stage 2 — Dense semantic retrieval

The question is encoded once with `sentence-transformers/all-MiniLM-L6-v2`.
The model creates a normalized vector representation, and Chroma searches the
existing cosine index for the top **100** passages.

This path is useful when the query and passage express the same idea using
different words. It is an approximate-nearest-neighbor/vector search over
precomputed passage embeddings, not an LLM reading all papers.

Cosine similarity is:

```text
cosine(q, p) = (q · p) / (||q|| ||p||)
```

The vector index stores the passage ID, text, title, section, and paper ID
alongside the embedding.

### Stage 3 — Sparse keyword retrieval with SQLite FTS5

The question is lowercased, split into unique word-like terms, quoted safely,
and joined with `OR`. SQLite FTS5 searches the indexed title, section, and text
fields and returns up to **100** passages.

The index uses the Porter stemming and Unicode-aware `unicode61` tokenizer.
BM25 is a lexical ranking method: it rewards useful term matches while
accounting for term rarity and document length. In the actual query, title has
weight 2; section and text each have weight 1; the unindexed ID has weight 0.
SQLite's BM25 result is sorted ascending in this query because the more relevant
FTS5 BM25 result has a lower score.

This path is useful for exact terms, names, acronyms, or rare phrases that a
semantic embedding might not rank highly.

### Stage 4 — Hybrid fusion with Reciprocal Rank Fusion

Dense and BM25 produce different score scales, so the system fuses **ranks**
instead of adding their raw similarity and BM25 scores. For each passage:

```text
RRF_score(p) = Σ 1 / (k + rank_i(p))
```

Here `k = 60`; the sum includes the dense and/or BM25 rank contributions for
that passage. A passage ranked highly by both searches receives contributions
from both. A passage found by only one search still receives that search's
contribution. Duplicate passage IDs are merged. The fused list is capped at
**50**; ties are broken deterministically by passage ID.

Example: if a passage ranks 2nd in dense retrieval and 5th in BM25:

```text
1 / (60 + 2) + 1 / (60 + 5) ≈ 0.03151
```

RRF is robust to incompatible raw score scales and rewards agreement between
retrieval methods. It does not itself prove that a passage supports an answer.

### Stage 5 — Cross-encoder reranking

The system sends each of the up to 50 hybrid candidates to
`cross-encoder/ms-marco-MiniLM-L-6-v2` as a `(question, passage text)` pair.
Unlike the dense bi-encoder, which separately encodes text for fast corpus
search, a cross-encoder evaluates the question and passage together. It is more
expensive per candidate but can make a more query-specific relevance ranking.

Inference is batched (batch size **32**), candidates are sorted by descending
model score, and the top **10** are retained. The raw reranker score is only a
ranking signal; it is **not a calibrated probability** that the passage is
relevant or that a claim is true.

### Stage 6 — Evidence selection and bounded context

The context builder consumes passages in reranked order and:

- removes duplicate passage IDs;
- selects at most **8** passages total;
- selects at most **3** passages per paper;
- limits the assembled context to **12,000 characters**;
- includes a passage in full or omits it—no character-level truncation;
- records omitted passage IDs.

Each context block includes its exact passage ID, paper ID, title, section, and
text. The prompt marks this material as evidence and explicitly says not to
follow instructions embedded in retrieved passages. The model sees only the
question and this bounded evidence, not the full corpus.

### Stage 7 — Structured answer generation

The configured LLM is reached through the OpenAI-compatible chat-completions
interface. The current local configuration uses NVIDIA Build's
`nvidia/nemotron-3.5-super-vl-120b-a12b` endpoint. The app uses the model for
text generation; its vision capability is not needed for this text-only
workflow.

The generation prompt requires evidence-only answers, no invented facts or
citations, abstention when evidence is insufficient, and a concise evidence
summary rather than private chain-of-thought. The request asks for a strict JSON
Schema containing:

- `status`;
- `answer`;
- `citations` (each with `passage_id` and the claim it supports);
- `reasoning_summary`;
- `insufficient_evidence`.

The local NVIDIA setting disables the model's thinking mode for these concise
structured answers. This prevents hidden reasoning from using the output-token
budget before the visible JSON is produced. The current defaults are
temperature 0, 1,500 maximum output tokens, a 60-second timeout, and two
additional retries for transient transport/provider failures. If the generated
JSON or citations are invalid, answer generation makes one bounded regeneration
attempt and then surfaces a handled API error rather than accepting malformed
output.

Provider values and credentials are read from environment variables. `.env`
is local-only and excluded from Git; never put the NVIDIA API key in slides,
source code, or a frontend variable.

### Stage 8 — Citation validation and sufficiency/refusal

The generator checks that every generated citation ID belongs to the selected
context. The citation validator associates each accepted ID with its title,
section, and supporting passage text. The API returns both the claim and
passage-level source metadata.

Important accuracy caveat: in the production bootstrap, `CitationValidator()`
is created without a separate semantic verifier or corpus lookup. Therefore,
current `citation_valid` primarily means the ID belongs to the selected
retrieved evidence. It does **not** independently prove semantic entailment.
`semantic_support` remains unknown (`null`) unless a verifier is configured.
Do not present an existing passage ID as proof that the passage logically
supports every part of a claim.

The refusal handler considers the amount of evidence, the model's
insufficient-evidence flag, a conflicting-evidence status, and validated
citations. Defaults require at least one selected passage and one acceptable
citation; there is no configured reranker-score floor. If no evidence was
selected, the answer generator returns a fixed insufficient-evidence response
without calling the LLM.

The model can report conflicting evidence, but the current system does not run
a dedicated contradiction-detection model. Likewise, the default citation
path is structural, not a full semantic fact-checker.

### Stage 9 — API response and user-facing traceability

The RAG pipeline returns the question, final status and answer, validated
citations, selected evidence, retrieval metadata, processing timings, a concise
reasoning summary, and evidence-assessment reasons.

In the React UI, the answer is followed by a **Supporting citations** section.
Each citation row links a claim to its paper, section, and passage ID. Clicking
it opens the exact source passage in the evidence drawer. The evidence list also
shows the selected passages, and **Copy answer** includes the supporting
references. These links provide an audit path; the citation list is separate
from the answer paragraph, so do not claim that every paragraph currently has
inline citation markers.

## 5. Architecture and repository map

```text
Browser (React + Vite)
       |
       | POST /api/v1/ask or /api/v1/retrieve
       v
FastAPI
  |-- query_processor
  |-- retrieval_service ---- ChromaDB vector index
  |                    \--- SQLite FTS5 index
  |-- reranker (MiniLM cross-encoder)
  |-- context_builder
  |-- answer_generator ---- NVIDIA Build OpenAI-compatible API
  |-- citation_validator
  |-- refusal_handler
  \-- corpus_service ------ saved QASPER passages
```

Important implementation files:

| File | Responsibility |
|---|---|
| [`app/main.py`](app/main.py) | FastAPI routes, CORS, error mapping, lazy pipeline initialization |
| [`app/bootstrap.py`](app/bootstrap.py) | Builds the service graph from persisted indexes and models |
| [`app/assets.py`](app/assets.py) | Reuses local assets or downloads/extracts the configured private archive |
| [`app/services/query_processor.py`](app/services/query_processor.py) | Input validation and whitespace normalization |
| [`app/services/retrieval_service.py`](app/services/retrieval_service.py) | Dense, FTS5 BM25, and RRF hybrid retrieval |
| [`app/services/reranker.py`](app/services/reranker.py) | Cross-encoder scoring and top-10 selection |
| [`app/services/context_builder.py`](app/services/context_builder.py) | Deduplication, per-paper limits, bounded context |
| [`app/services/llm_service.py`](app/services/llm_service.py) | Provider configuration, request transport, retries, JSON response extraction |
| [`app/services/answer_generator.py`](app/services/answer_generator.py) | Prompt, strict JSON Schema, parse checks, bounded regeneration |
| [`app/services/citation_validator.py`](app/services/citation_validator.py) | Citation membership and source metadata |
| [`app/services/refusal_handler.py`](app/services/refusal_handler.py) | Sufficiency/refusal assessment |
| [`app/services/rag_pipeline.py`](app/services/rag_pipeline.py) | End-to-end orchestration and timing metadata |
| [`frontend/src/App.tsx`](frontend/src/App.tsx) | Chat flow, answer, citation links, source drawer |
| [`frontend/src/landing.tsx`](frontend/src/landing.tsx) | Landing page and visual pipeline explanation |

The pipeline is initialized lazily on the first ask/retrieve call so FastAPI can
start without immediately loading embedding and reranker models. The first
request can therefore take longer than later requests.

## 6. API and interface

| Endpoint | Purpose |
|---|---|
| `POST /api/v1/ask` | Full retrieval, reranking, generation, citation/refusal pipeline |
| `POST /api/v1/retrieve` | Retrieval and reranking without LLM generation |
| `GET /api/v1/health` | Reports API status and whether non-secret LLM configuration is present; it does not prove the remote model is reachable |
| `GET /api/v1/config` | Returns safe non-secret model/configuration details |
| `GET /api/v1/paper/{paper_id}` | Loads original corpus passages for a paper |

The question request is validated to 1–2,000 characters. Expected handled
failures include `422` for invalid input, `503` when the RAG pipeline/assets
cannot initialize, and `502` when the generation provider cannot produce a
usable answer. CORS allows the local Vite origins and configured deployment
origins.

Example request:

```json
{
  "question": "Compare dense and sparse retrieval methods"
}
```

The answer response includes the answer and status plus `citations` and
`evidence` arrays. A citation carries its claim, passage ID, source title and
section, supporting text, and validation flags. Evidence entries preserve
passage IDs and text. Retrieval metadata records candidate counts and omitted
passages; processing metadata records retrieval, reranking, generation, and
total time. This is a shortened illustrative shape, not a saved benchmark:

```json
{
  "status": "answered",
  "answer": "A concise answer grounded in the selected passages.",
  "citations": [
    {
      "passage_id": "paper_00012",
      "claim": "This passage supports one claim.",
      "citation_valid": true
    }
  ],
  "evidence": [
    {
      "passage_id": "paper_00012",
      "title": "Example paper",
      "section_name": "Method",
      "text": "The original retrieved passage text."
    }
  ]
}
```

The current functional UI path is landing page → research question → result →
cited claim/source drawer. Navigation elements for history/settings are not
implemented as persistent product features; avoid promising saved conversation
history unless that work is added separately.

## 7. Evaluation: what the metrics mean

### Retrieval metrics

The repository's evaluator uses the QASPER relevance judgments (qrels):

- **Recall@K:** fraction of all judged-relevant passages found in the top K.
- **MRR@10:** reciprocal rank of the first relevant passage, averaged across
  evaluated queries; no relevant result in the top 10 contributes zero.
- **nDCG@10:** ranking quality with graded qrels; relevant passages near the
  top score more, with the result normalized against an ideal ranking.
- **Candidate Recall@50:** fraction of relevant passages found in the 50
  candidates before reranking; this is an upper bound on what reranking can
  return.

The scripts evaluate queries that have at least one positive relevance
judgment. Development data is for iteration; keep the test split for final
reporting.

The project brief records these **development-set baselines from 890 queries**.
They are historical retrieval baselines, not fresh measurements made while
writing this guide, and they are not end-to-end LLM answer-accuracy results.
The evaluation implementation averages only over queries with at least one
positive relevance judgment, so the exact evaluated count should be checked in
the run output before quoting it as the number of scored queries.

| Metric | Dense | BM25 | Hybrid | Reranked |
|---|---:|---:|---:|---:|
| Recall@5 | 0.0498 | 0.0795 | 0.0850 | 0.1320 |
| Recall@10 | 0.0763 | 0.1221 | 0.1249 | 0.1776 |
| MRR@10 | 0.0513 | 0.0744 | 0.0791 | 0.1254 |
| nDCG@10 | 0.0480 | 0.0747 | 0.0763 | 0.1198 |

The recorded reranker Candidate Recall@50 is **0.2489**. Do not present these
as test-set scores or claim the LLM is evaluated by this table.

### Answer, citation, and refusal metrics

The answer evaluator reports answerability accuracy, token-set lexical
relevance, and unsupported-claim rate. Token overlap is a transparent
diagnostic; it does not understand paraphrases or scientific correctness.
Unsupported claims require labeled predictions.

Citation evaluation separates:

1. Existence in the available evidence.
2. Precision against reference citation IDs.
3. Recall against reference citation IDs.
4. Semantic claim support, which requires a separate evaluator/human review.

Refusal evaluation distinguishes correct refusals on unanswerable questions,
false refusals on answerable questions, and incorrect answering of
unanswerable questions. These metrics require answerability labels. The
repository has metric implementations, but do not claim a full LLM/citation
benchmark has been run unless you have a current report.

### Automated testing

The backend tests cover query processing, retrieval/RRF, reranking, context
limits, structured answer parsing, citations, refusal behavior, API behavior,
and evaluation metrics. The latest full backend run recorded for this code was
**50 passed**; the frontend production build also passed. Most tests use
controlled fakes/mocks, so they prove application logic and interfaces, not
NVIDIA uptime or scientific correctness.

## 8. Deployment and security

The Dockerfile builds a Python 3.11 backend image and serves FastAPI on
`${PORT:-7860}`. It does not bundle the Vite frontend; the frontend must be
served separately for a hosted deployment.

On a supported host, `RUNTIME_ASSETS_DIR` points to persistent storage. If the
indexes are absent, `app/assets.py` downloads the configured archive from the
private Hugging Face dataset, checks that archive paths stay inside the
runtime directory, extracts it, and normalizes the corpus directory. A first
request that downloads/extracts assets is expected to be slow. Persistent disk
availability depends on the chosen host/plan.

Security boundaries:

- Provider and Hugging Face keys are environment secrets; `.env` is ignored by
  Git.
- The frontend never receives provider keys.
- Only selected passages—not all 81,550 passages—are sent to the configured
  external LLM endpoint.
- Retrieved passage text is untrusted content, not system instructions.
- The health endpoint checks configuration presence, not provider connectivity.

The repository includes Docker/asset-bootstrap preparation. Do not describe a
public production deployment as live unless the team has independently
verified that deployment.

## 9. Condensed presentation plan (about 6 minutes)

The website's teaching room is an expanded, approximately 15-minute
walkthrough of the data preparation, retrieval algorithm, API, operations, and
limitations described here. Use this shorter talk track when presentation time
is limited.

### 0:00–0:40 — Introduce the problem

“Scientific answers need more than fluent text. A researcher needs relevant
papers, evidence for each claim, and a way to inspect the exact source. Fieldwork
is a RAG assistant that answers over the QASPER-RAG scientific-passage corpus.”

### 0:40–1:20 — Show the data and indexes

“We have 81,550 passages. Each passage retains a stable ID, paper title,
section, and text. We prebuilt two complementary indexes: a Chroma vector index
for semantic matches and an SQLite FTS5 index for lexical matches.”

### 1:20–2:45 — Explain the algorithm

Walk through the diagram in section 1. Emphasize: top 100 from each search,
RRF with `k=60` to top 50, cross-encoder scoring to top 10, and a bounded
context of at most 8 passages / 12,000 characters. Explain that RRF fuses ranks
and that the cross-encoder is a second-stage relevance model.

### 2:45–4:00 — Live demo

Ask a prepared question such as **“Compare dense and sparse retrieval
methods.”** Show the generated answer, the cited claims, and click one citation
to open its passage ID and original text. Explain that the LLM sees the selected
passages only.

### 4:00–5:00 — Discuss evaluation

Show retrieval metrics and describe the development baselines as historical
retrieval results—not as LLM accuracy. Mention the test split is reserved for
final reporting. Be explicit that lexical answer overlap is not semantic
correctness.

### 5:00–6:00 — Limitations and close

“The system improves traceability, but it does not guarantee that each cited
passage entails the claim. The default validator checks citation membership;
semantic verification and final scientific review remain important. The next
steps are stronger semantic citation evaluation, careful held-out testing, and
more robust deployment.”

## 10. Likely questions and accurate answers

**Why use both dense and BM25 search?**

Dense retrieval can match meaning across different wording. BM25/FTS5 is good
at exact terminology. Their strengths differ, so both candidate lists are
combined.

**Why RRF instead of adding the two scores?**

The scores have different scales. RRF uses rank positions, not raw values, and
can reward a passage found high in both lists.

**What does the cross-encoder add?**

It reads the question and each candidate passage together and reranks the
hybrid shortlist. It is more query-specific than comparing separately encoded
vectors, but more expensive per passage.

**Does a valid citation prove the answer is true?**

No. In the current default configuration, the validator verifies that the
passage ID is in the selected evidence and returns its source text. A semantic
entailment verifier is not configured by default.

**Can the model hallucinate?**

It can still make mistakes. Evidence-only instructions, schema output,
citation-ID checks, and refusal logic reduce some failure modes, but they are
not a proof of correctness.

**How do you know the answer is grounded?**

The user can inspect the claim/source association and open the exact passage.
This establishes traceability and structural validity, not complete semantic
proof.

**Where does the LLM run?**

Generation uses the configured NVIDIA Build API endpoint. The app's retrieval
indexes and embedding/reranker models are local to the backend runtime. The
entire corpus is not sent to NVIDIA.

**Is this fully deployed?**

The local frontend/backend flow and Docker/runtime-asset setup are implemented.
The Docker image is backend-only; a separate frontend host and verified
production configuration are required before claiming a public deployment.

**What does the number “4 datasets” mean in the demo answer?**

It came from a specific retrieved passage about dense n-gram retrieval in one
study, which reports improvement on all four of that study's datasets. It is
not a universal result for every dense retrieval system.

## 11. Live-demo checklist

- Start the backend from the repository root with the local asset path set:

  ```powershell
  $env:RUNTIME_ASSETS_DIR = (Get-Location).Path
  .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file .env
  ```

- In another terminal, start the frontend:

  ```powershell
  Set-Location frontend
  npm run dev -- --host 127.0.0.1
  ```

- Open `http://127.0.0.1:5173`.
- Confirm `/api/v1/health` reports `status: ok` and `llm_configured: true`.
- Use a prepared question and allow extra time for the first request, which
  initializes retrieval/reranker models.
- Verify a citation opens the expected passage.
- Have screenshots or a prepared example available in case of network,
  provider-rate-limit, or live-demo latency issues.
- Never display `.env` or paste an API key into slides or chat.

## 12. Source-of-truth files

- [`README.md`](README.md): local run, tests, API, and deployment notes.
- [`architecture.md`](architecture.md): runtime architecture and limitations.
- [`masterprompt.txt`](masterprompt.txt): initial project scope and recorded
  retrieval baselines.
- [`evaluation/README.md`](evaluation/README.md): metric definitions and split
  policy.
- [`evaluation/retrieval_metrics.py`](evaluation/retrieval_metrics.py):
  reusable retrieval metric calculations.
- [`evaluation/answer_metrics.py`](evaluation/answer_metrics.py): answer,
  citation-ID, and refusal metric calculations.
