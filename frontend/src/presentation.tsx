import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Check,
  Code2,
  Database,
  FileText,
  FlaskConical,
  GitMerge,
  HardDrive,
  KeyRound,
  ListFilter,
  MessageSquareText,
  Network,
  Search,
  Server,
  ShieldCheck,
  Sigma,
  Sparkles,
  Target,
  Terminal,
  TestTube,
  Workflow,
} from "lucide-react";

type PresentationPageProps = {
  onBack: () => void;
  onOpenChat: () => void;
};

const scoreRows = [
  { metric: "Recall@5", dense: 0.0498, bm25: 0.0795, hybrid: 0.085, reranked: 0.132 },
  { metric: "Recall@10", dense: 0.0763, bm25: 0.1221, hybrid: 0.1249, reranked: 0.1776 },
  { metric: "MRR@10", dense: 0.0513, bm25: 0.0744, hybrid: 0.0791, reranked: 0.1254 },
  { metric: "nDCG@10", dense: 0.048, bm25: 0.0747, hybrid: 0.0763, reranked: 0.1198 },
];

export function PresentationPage({ onBack, onOpenChat }: PresentationPageProps) {
  return (
    <main className="teach-page">
      <header className="teach-nav">
        <button className="teach-back" onClick={onBack}>
          <ArrowLeft size={16} /> Fieldwork
        </button>
        <div className="teach-nav-center">
          <span className="teach-nav-mark"><FlaskConical size={14} /></span>
          <span>THE RAG TEACHING ROOM</span>
        </div>
        <button className="teach-demo-button" onClick={onOpenChat}>
          Try the live demo <ArrowUpRight size={15} />
        </button>
      </header>

      <section className="teach-hero">
        <div className="teach-hero-copy">
          <span className="teach-eyebrow"><span /> FULL SYSTEM WALKTHROUGH · ABOUT 15 MINUTES</span>
          <h1>How does a research question become a <em>traceable answer?</em></h1>
          <p>
            Learn the whole application journey: how the corpus is indexed,
            how the backend answers a question, and how the UI traces claims
            back to the original paper passage.
          </p>
          <div className="teach-hero-actions">
            <a className="teach-primary" href="#teach-why">Start the walkthrough <ArrowDown size={16} /></a>
            <button className="teach-secondary" onClick={onOpenChat}>Ask a question <ArrowRight size={15} /></button>
          </div>
          <div className="teach-hero-stats">
            <span><strong>81,550</strong> indexed passages</span>
            <span><strong>2</strong> persisted search indexes</span>
            <span><strong>5</strong> versioned API routes</span>
          </div>
        </div>

        <div className="teach-hero-visual" role="group" aria-label="Diagram showing a question moving through retrieval, ranking, evidence, and answer">
          <div className="teach-visual-caption"><span>ONE QUESTION. A TRACEABLE JOURNEY.</span><span>01 — 05</span></div>
          <div className="teach-visual-question"><span>RESEARCH QUESTION</span><strong>Compare dense and sparse retrieval</strong></div>
          <div className="teach-visual-branches">
            <div className="teach-branch teach-branch-green"><Search size={16} /><span><b>Meaning search</b><small>Finds related ideas</small></span><strong>100</strong></div>
            <div className="teach-branch teach-branch-blue"><FileText size={16} /><span><b>Keyword search</b><small>Finds exact terms</small></span><strong>100</strong></div>
          </div>
          <div className="teach-visual-merge"><GitMerge size={16} /><span>RRF combines ranks</span><strong>TOP 50</strong></div>
          <div className="teach-visual-result"><span className="teach-result-icon"><ShieldCheck size={15} /></span><span><b>Answer with sources</b><small>Claims ↔ passage IDs</small></span><ArrowUpRight size={15} /></div>
          <div className="teach-visual-foot"><span>Search broadly</span><i /><span>Rank carefully</span><i /><span>Show the evidence</span></div>
        </div>
      </section>

      <nav className="teach-toc" aria-label="Presentation sections">
        <a href="#teach-why">The idea</a>
        <a href="#teach-data">Data + indexes</a>
        <a href="#teach-algorithm">Retrieval</a>
        <a href="#teach-evidence">Answer + sources</a>
        <a href="#teach-architecture">Backend + API</a>
        <a href="#teach-results">Evaluation</a>
        <a href="#teach-operations">Run + deploy</a>
        <a href="#teach-limits">Limitations</a>
      </nav>

      <section className="teach-section teach-why" id="teach-why">
        <div className="teach-section-heading">
          <span className="teach-section-label">01 / THE IDEA</span>
          <h2>Think of it as a research librarian and a careful writer.</h2>
          <p>RAG means Retrieval-Augmented Generation: retrieve relevant evidence first, then generate an answer from that evidence.</p>
        </div>
        <div className="teach-analogy-grid">
          <article className="teach-analogy-card">
            <span className="teach-card-number">A</span><Search size={20} />
            <h3>Find the right pages</h3>
            <p>A librarian searches a large collection and brings back a short list—not every book in the building.</p>
            <span className="teach-analogy-tag">RETRIEVE</span>
          </article>
          <article className="teach-analogy-card">
            <span className="teach-card-number">B</span><ListFilter size={20} />
            <h3>Put the best evidence first</h3>
            <p>A specialist compares each passage with the exact question and moves the closest matches to the top.</p>
            <span className="teach-analogy-tag">RERANK</span>
          </article>
          <article className="teach-analogy-card">
            <span className="teach-card-number">C</span><MessageSquareText size={20} />
            <h3>Write with receipts</h3>
            <p>The writer summarizes only the selected evidence and gives the reader a path back to each source.</p>
            <span className="teach-analogy-tag">GENERATE + TRACE</span>
          </article>
        </div>
        <div className="teach-callout"><Sparkles size={17} /><p><strong>The big idea:</strong> the LLM is not the search engine and it does not read all 81,550 passages. Retrieval chooses a small evidence set; generation works from that set.</p></div>
      </section>

      <section className="teach-section teach-data" id="teach-data">
        <div className="teach-section-heading">
          <span className="teach-section-label">02 / DATA PREPARATION + INDEXES</span>
          <h2>Prepare the library once; search it many times.</h2>
          <p>
            Dataset preparation and question-time retrieval are separate jobs.
            The corpus is downloaded and indexed offline; the running app reuses
            those saved assets instead of rebuilding them for every question.
          </p>
        </div>

        <div className="teach-dataset-workflow">
          <article className="teach-data-stage">
            <span className="teach-data-step">01 · DOWNLOAD</span>
            <div className="teach-data-icon"><Database size={18} /></div>
            <h3>Get the six dataset components</h3>
            <p>The downloader saves the QASPER-RAG corpus and its evaluation companions under <code>data/</code>.</p>
            <code className="teach-command">python download_dataset.py</code>
            <div className="teach-chip-list">
              {["corpus", "queries", "qrels", "answers", "top_ranked", "retrieved_docs"].map((item) => <span key={item}>{item}</span>)}
            </div>
          </article>
          <div className="teach-data-arrow"><ArrowRight size={19} /></div>
          <article className="teach-data-stage">
            <span className="teach-data-step">02 · BUILD INDEXES</span>
            <div className="teach-data-icon"><Database size={18} /></div>
            <h3>Create two complementary indexes</h3>
            <p>Separate build scripts prepare semantic vectors and a lexical FTS5 table. Both preserve passage IDs and source metadata.</p>
            <code className="teach-command">python build_index.py<br />python build_bm25.py</code>
            <div className="teach-chip-list"><span>ChromaDB</span><span>SQLite FTS5</span><span>81,550 passages</span></div>
          </article>
          <div className="teach-data-arrow"><ArrowRight size={19} /></div>
          <article className="teach-data-stage">
            <span className="teach-data-step">03 · SERVE</span>
            <div className="teach-data-icon"><HardDrive size={18} /></div>
            <h3>Reuse persisted runtime assets</h3>
            <p>At startup, the app checks for the vector index, FTS database, and corpus. It downloads the private archive only when required.</p>
            <div className="teach-chip-list"><span>vector_db/</span><span>bm25_database.db</span><span>data/corpus/</span></div>
          </article>
        </div>

        <div className="teach-index-details">
          <article className="teach-index-card teach-index-dense">
            <div className="teach-index-heading"><Search size={17} /><span>SEMANTIC INDEX · build_index.py</span></div>
            <p>Loads corpus passages, encodes text with <code>sentence-transformers/all-MiniLM-L6-v2</code>, normalizes vectors, then upserts them into Chroma's <code>qasper_passages</code> collection using cosine distance.</p>
            <div className="teach-index-facts"><span><b>256</b> passages per outer batch</span><span><b>32</b> texts per embedding batch</span><span>Stores text + title + section + paper ID</span></div>
          </article>
          <article className="teach-index-card teach-index-lexical">
            <div className="teach-index-heading"><FileText size={17} /><span>KEYWORD INDEX · build_bm25.py</span></div>
            <p>Creates SQLite's <code>corpus_fts</code> virtual table with FTS5 and the <code>porter unicode61</code> tokenizer. Passage IDs are unindexed; title, section, and text are searchable.</p>
            <div className="teach-index-facts"><span><b>1,000</b> records per insert batch</span><span>Title weight <b>2</b></span><span>Section + text weight <b>1</b></span></div>
          </article>
        </div>

        <div className="teach-callout teach-runtime-callout">
          <Workflow size={18} />
          <p><strong>First-request lifecycle:</strong> FastAPI starts without loading the ML models. The first ask/retrieve request ensures assets exist, builds the service graph, and loads the embedding and reranker models. That request can be slower; subsequent requests reuse the initialized pipeline and saved indexes.</p>
        </div>
      </section>

      <section className="teach-section teach-algorithm" id="teach-algorithm">
        <div className="teach-section-heading">
          <span className="teach-section-label">03 / QUESTION-TIME RETRIEVAL</span>
          <h2>Watch the search funnel shrink.</h2>
          <p>Each stage has a different job. The pipeline narrows the corpus before asking the LLM to write.</p>
        </div>

        <div className="teach-funnel">
          <article className="teach-funnel-stage teach-funnel-corpus">
            <span className="teach-stage-step">START</span><Database size={19} />
            <div><strong>81,550</strong><span>paper passages in the corpus</span></div>
          </article>
          <div className="teach-funnel-connector"><ArrowDown size={16} /><span>Search two ways</span></div>
          <div className="teach-funnel-pair">
            <article className="teach-funnel-stage teach-funnel-dense">
              <span className="teach-stage-step">PATH 01</span><Search size={18} />
              <div><strong>Top 100</strong><span>dense / semantic candidates</span></div>
            </article>
            <article className="teach-funnel-stage teach-funnel-sparse">
              <span className="teach-stage-step">PATH 02</span><FileText size={18} />
              <div><strong>Top 100</strong><span>BM25 / keyword candidates</span></div>
            </article>
          </div>
          <div className="teach-funnel-connector"><ArrowDown size={16} /><span>Fuse ranks with RRF, k = 60</span></div>
          <article className="teach-funnel-stage teach-funnel-fused">
            <span className="teach-stage-step">MERGE</span><GitMerge size={18} />
            <div><strong>Top 50</strong><span>unique hybrid candidates</span></div>
          </article>
          <div className="teach-funnel-connector"><ArrowDown size={16} /><span>Score each question–passage pair</span></div>
          <article className="teach-funnel-stage teach-funnel-reranked">
            <span className="teach-stage-step">RERANK</span><Sigma size={18} />
            <div><strong>Top 10</strong><span>cross-encoder ranked</span></div>
          </article>
          <div className="teach-funnel-connector"><ArrowDown size={16} /><span>Choose complete passages, not chopped text</span></div>
          <article className="teach-funnel-stage teach-funnel-context">
            <span className="teach-stage-step">CONTEXT</span><BookOpen size={18} />
            <div><strong>Up to 8</strong><span>passages · max 12,000 characters</span></div>
          </article>
        </div>

        <div className="teach-search-grid">
          <article className="teach-search-card">
            <div className="teach-search-icon teach-icon-green"><Search size={18} /><span>SEMANTIC</span></div>
            <h3>Dense search understands “similar meaning.”</h3>
            <p>A MiniLM embedding turns the question into a normalized vector. Chroma finds nearby passage vectors with cosine distance.</p>
            <div className="teach-example"><span>Question says</span><b>“find related concepts”</b><span>Passage says</span><b>“semantically similar items”</b></div>
            <code>cosine(q, p) = (q · p) / (||q|| ||p||)</code>
          </article>
          <article className="teach-search-card">
            <div className="teach-search-icon teach-icon-blue"><FileText size={18} /><span>KEYWORD</span></div>
            <h3>Sparse search catches exact words.</h3>
            <p>SQLite FTS5 with BM25 is useful for technical terms, acronyms, names, and rare phrases. Title gets weight 2; section and text get weight 1.</p>
            <div className="teach-example"><span>Question contains</span><b>“BM25”, “MiniLM”, a paper ID</b><span>Search matches</span><b>those exact indexed terms</b></div>
            <code>unique lowercase terms → FTS5 OR query</code>
          </article>
        </div>

        <div className="teach-rrf-card">
          <div className="teach-rrf-heading"><span className="teach-section-label">THE FUSION TRICK</span><h3>RRF compares rank, not incompatible scores.</h3><p>Cosine similarity and BM25 scores live on different scales. Reciprocal Rank Fusion uses where each method placed a passage.</p></div>
          <div className="teach-rrf-equation"><span>RRF score</span><code>Σ 1 / (60 + rank)</code><small>one contribution from each search where the passage appears</small></div>
          <div className="teach-rank-example"><span>Example candidate</span><div><span className="teach-rank-pill">Dense rank <b>#2</b></span><span className="teach-rank-pill">BM25 rank <b>#5</b></span></div><code>1/62 + 1/65 ≈ 0.03151</code><small>Higher fused score ranks ahead.</small></div>
        </div>

        <div className="teach-rerank-note">
          <div className="teach-rerank-icon"><Target size={19} /></div>
          <div><span className="teach-section-label">SECOND-STAGE RELEVANCE</span><h3>Why rerank after retrieval?</h3><p>Fast embedding search finds candidates across a large index. A cross-encoder then reads <em>the question and one passage together</em> and scores their match. Its score is for ordering—not a probability of truth.</p></div>
          <div className="teach-pair-visual"><span>QUESTION</span><b>Compare methods</b><i>+</i><span>PASSAGE</span><b>“Dense vectors…”</b><ArrowRight size={17} /><strong>relevance score</strong></div>
        </div>
      </section>

      <section className="teach-section teach-evidence" id="teach-evidence">
        <div className="teach-section-heading">
          <span className="teach-section-label">04 / ANSWER + EVIDENCE</span>
          <h2>Give the model a small, well-labelled reading packet.</h2>
          <p>Context is capped and traceable. The model is told to use the evidence—not instructions that happen to appear inside a paper passage.</p>
        </div>
        <div className="teach-evidence-layout">
          <div className="teach-context-card">
            <div className="teach-context-top"><span><BookOpen size={15} /> THE MODEL RECEIVES</span><span>MAX 8 PASSAGES</span></div>
            <div className="teach-context-question"><small>RESEARCH QUESTION</small><strong>Compare dense and sparse retrieval</strong></div>
            {[1, 2, 3].map((number) => (
              <div className="teach-context-passage" key={number}>
                <span>[PASSAGE 0{number}]</span><b>Passage ID: paper_0000{number}</b><small>Paper title · section</small><p>Original passage text, included in full when it fits the context budget.</p>
              </div>
            ))}
            <div className="teach-context-footer">Selected passages are capped at 12,000 characters; omitted IDs are tracked.</div>
          </div>
          <div className="teach-generation">
            <span className="teach-section-label">STRUCTURED GENERATION</span>
            <h3>Ask for an answer the API can validate.</h3>
            <p>The NVIDIA Build model receives a JSON Schema request. The app expects an answer, status, citation claims, and a concise evidence summary.</p>
            <pre><code>{`{
  "status": "answered",
  "answer": "Evidence-based explanation",
  "citations": [
    { "passage_id": "paper_00001",
      "claim": "Supported claim" }
  ],
  "reasoning_summary": "Brief evidence summary",
  "insufficient_evidence": false
}`}</code></pre>
            <div className="teach-model-chip"><Sparkles size={14} /><span>NVIDIA Nemotron 3.5 Super VL</span><small>JSON Schema · thinking disabled for concise output</small></div>
          </div>
        </div>

        <div className="teach-trace-card">
          <div className="teach-trace-heading"><ShieldCheck size={20} /><div><span className="teach-section-label">SOURCE TRACEABILITY</span><h3>Every citation can lead back to a passage.</h3></div></div>
          <div className="teach-trace-flow">
            <div><small>GENERATED CLAIM</small><strong>“Dense retrieval can match similar meaning.”</strong></div>
            <ArrowRight size={18} />
            <div><small>PASSAGE ID</small><code>1903.00058_00017</code></div>
            <ArrowRight size={18} />
            <div><small>ORIGINAL SOURCE</small><strong>Paper title · section · passage text</strong></div>
          </div>
          <p>The UI shows cited claims and source IDs; clicking a citation opens the exact passage. Current validation guarantees membership in selected evidence, not independent proof of semantic entailment.</p>
        </div>
      </section>

      <section className="teach-section teach-results" id="teach-results">
        <div className="teach-section-heading">
          <span className="teach-section-label">05 / EVALUATION</span>
          <h2>Measure whether the right passages rise to the top.</h2>
          <p>These are retrieval metrics, not LLM answer-accuracy scores. They compare ranked passage IDs against the dataset’s human relevance judgments.</p>
        </div>
        <div className="teach-metric-cards">
          <article><span>RECALL@K</span><strong>Did we find relevant passages?</strong><p>Fraction of judged-relevant passages present in the top K.</p></article>
          <article><span>MRR@10</span><strong>How early is the first good hit?</strong><p>Rewards a relevant result near the top of the ranking.</p></article>
          <article><span>nDCG@10</span><strong>Are the best results ordered well?</strong><p>Accounts for graded relevance and position in the list.</p></article>
          <article><span>CANDIDATE RECALL@50</span><strong>What can reranking possibly recover?</strong><p>Relevant-passage coverage before the cross-encoder reorders candidates.</p></article>
        </div>
        <div className="teach-results-panel">
          <div className="teach-results-title"><div><span className="teach-section-label">RECORDED DEVELOPMENT BASELINE</span><h3>Reranking improved the retrieval ranking.</h3></div><span>QASPER dev split · 890 queries in project brief</span></div>
          <div className="teach-chart-legend"><span><i className="legend-dense" /> Dense</span><span><i className="legend-bm25" /> BM25</span><span><i className="legend-hybrid" /> Hybrid</span><span><i className="legend-reranked" /> Reranked</span></div>
          <div className="teach-chart">
            {scoreRows.map((row) => {
              const max = Math.max(row.dense, row.bm25, row.hybrid, row.reranked);
              return (
                <div className="teach-chart-row" key={row.metric}>
                  <strong className="teach-chart-label">{row.metric}</strong>
                  {(["dense", "bm25", "hybrid", "reranked"] as const).map((system) => (
                    <div className="teach-chart-value" key={system}>
                      <span className={`teach-chart-bar teach-bar-${system}`} style={{ width: `${(row[system] / max) * 100}%` }} />
                      <code>{row[system].toFixed(4)}</code>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
          <p className="teach-chart-footnote">Bars are scaled within each metric row (they are not percentages). Scores are the historical values recorded in <code>masterprompt.txt</code>, not a fresh run or a test-set result. The brief records Candidate Recall@50 = 0.2489 for reranking.</p>
        </div>
        <div className="teach-dataset-strip">
          <div><Database size={18} /><span><strong>81,550</strong><small>corpus passages</small></span></div>
          <div><Search size={18} /><span><strong>890</strong><small>dev queries</small></span></div>
          <div><FileText size={18} /><span><strong>1,913</strong><small>dev relevance judgments</small></span></div>
          <div><ShieldCheck size={18} /><span><strong>Test split</strong><small>reserved for final reporting</small></span></div>
        </div>
      </section>

      <section className="teach-section teach-architecture" id="teach-architecture">
        <div className="teach-section-heading">
          <span className="teach-section-label">06 / APPLICATION ARCHITECTURE + API</span>
          <h2>Follow the request through the real application.</h2>
          <p>
            The browser, API, retrieval services, model adapter, and source
            drawer have separate responsibilities. This makes the live user
            journey easier to debug and explain.
          </p>
        </div>

        <div className="teach-request-flow" aria-label="Request flow from browser to evidence drawer">
          <article><span>01 · PRESENTATION</span><Code2 size={18} /><strong>React + Vite</strong><small>Question form, loading/error states, answer and source drawer</small></article>
          <ArrowRight size={17} />
          <article><span>02 · HTTP API</span><Server size={18} /><strong>FastAPI</strong><small><code>POST /api/v1/ask</code> validates a 1–2,000 character question</small></article>
          <ArrowRight size={17} />
          <article><span>03 · ORCHESTRATION</span><Workflow size={18} /><strong>RAGPipeline</strong><small>Calls retrieval → reranking → context → generation → validation</small></article>
          <ArrowRight size={17} />
          <article><span>04 · RESPONSE</span><ShieldCheck size={18} /><strong>Structured JSON</strong><small>Answer, status, citations, evidence, and timing metadata</small></article>
        </div>

        <div className="teach-service-map">
          <div className="teach-service-map-title">
            <span className="teach-section-label">BACKEND SERVICE MAP</span>
            <p><code>app/bootstrap.py</code> connects these services when the pipeline is first needed.</p>
          </div>
          <div className="teach-service-grid">
            <article><b>Query processor</b><code>query_processor.py</code><span>Validates, trims, and normalizes whitespace.</span></article>
            <article><b>Retrieval service</b><code>retrieval_service.py</code><span>Calls Chroma + FTS5, fuses ranks with RRF.</span></article>
            <article><b>Passage reranker</b><code>reranker.py</code><span>Scores question/passage pairs with the cross-encoder.</span></article>
            <article><b>Context builder</b><code>context_builder.py</code><span>Deduplicates and applies passage and character caps.</span></article>
            <article><b>LLM adapter</b><code>llm_service.py</code><span>OpenAI-compatible HTTP, timeout, retry, and response handling.</span></article>
            <article><b>Answer generator</b><code>answer_generator.py</code><span>Evidence-only prompt, JSON Schema, parse and bounded retry.</span></article>
            <article><b>Citation + refusal</b><code>citation_validator.py · refusal_handler.py</code><span>Checks selected IDs and assesses insufficient evidence.</span></article>
            <article><b>Corpus service</b><code>corpus_service.py</code><span>Loads original passages when a paper source is opened.</span></article>
          </div>
        </div>

        <div className="teach-api-panel">
          <div className="teach-api-heading"><Network size={18} /><div><span className="teach-section-label">VERSIONED HTTP INTERFACE</span><h3>Five routes, two ways to ask.</h3></div></div>
          <div className="teach-endpoint-list">
            <div><code>POST /api/v1/ask</code><span>Full RAG answer, citations, evidence, metadata</span></div>
            <div><code>POST /api/v1/retrieve</code><span>Ranked evidence only—useful without an LLM call</span></div>
            <div><code>GET /api/v1/paper/{`{paper_id}`}</code><span>Original passages for the source drawer</span></div>
            <div><code>GET /api/v1/health</code><span>API status + whether required LLM settings are present</span></div>
            <div><code>GET /api/v1/config</code><span>Safe provider/model settings; never returns the API key</span></div>
          </div>
          <div className="teach-api-foot">
            <span><b>422</b> invalid question</span>
            <span><b>503</b> pipeline/assets unavailable</span>
            <span><b>502</b> unusable provider response</span>
            <span><b>404</b> paper not found</span>
          </div>
          <p className="teach-api-note">The UI keeps these outcomes visible: invalid input is rejected, initialization/provider failures show an error, and an insufficient-evidence result is returned as a cautious answer rather than hidden.</p>
        </div>

        <div className="teach-response-card">
          <div><span className="teach-section-label">WHAT COMES BACK</span><h3>A result plus enough data to inspect it.</h3><p>Response schemas keep the UI independent from internal model calls while preserving a source trail.</p></div>
          <pre><code>{`{
  "status": "answered",
  "answer": "...",
  "citations": [{ "passage_id": "...", "claim": "..." }],
  "evidence": [{ "title": "...", "section_name": "...", "text": "..." }],
  "retrieval_metadata": { "hybrid_candidates": 50 },
  "processing_metadata": { "retrieval_time": 0.0, "total_time": 0.0 }
}`}</code></pre>
        </div>
      </section>

      <section className="teach-section teach-operations" id="teach-operations">
        <div className="teach-section-heading">
          <span className="teach-section-label">07 / RUN, CONFIGURE, TEST + DEPLOY</span>
          <h2>What it takes to run the application responsibly.</h2>
          <p>
            A working demo has two local processes. Hosted operation adds
            persistent runtime storage and secrets; it does not turn the
            backend container into a bundled frontend.
          </p>
        </div>

        <div className="teach-ops-grid">
          <article className="teach-ops-card">
            <div className="teach-ops-title"><Terminal size={18} /><span>LOCAL DEVELOPMENT</span></div>
            <p>Prepare Python dependencies and local settings, then run the backend and Vite frontend in separate terminals.</p>
            <pre><code>{`# repository root (PowerShell)
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000

# second terminal
Set-Location frontend
npm install   # first setup only
npm run dev`}</code></pre>
            <div className="teach-ops-foot"><span>Frontend: <code>localhost:5173</code></span><span>Backend: <code>localhost:8000</code></span></div>
          </article>
          <article className="teach-ops-card">
            <div className="teach-ops-title"><KeyRound size={18} /><span>CONFIGURATION + SECRETS</span></div>
            <p>Backend reads settings from environment variables. Provider credentials stay server-side; never put them in React/Vite variables.</p>
            <div className="teach-env-list">
              <div><code>LLM_BASE_URL · LLM_MODEL</code><span>OpenAI-compatible endpoint and model name</span></div>
              <div><code>LLM_API_KEY</code><span>Private provider secret; stored in local .env or host secrets</span></div>
              <div><code>HF_DATASET_REPO · HF_ASSET_FILE · HF_TOKEN</code><span>Only needed to fetch the private runtime archive</span></div>
              <div><code>RUNTIME_ASSETS_DIR · CORS_ORIGINS</code><span>Persistent files location and allowed frontend origins</span></div>
            </div>
            <div className="teach-safe-note"><Check size={15} /> <span><code>.env</code> is git-ignored; <code>/health</code> checks configuration, not remote model reachability.</span></div>
          </article>
          <article className="teach-ops-card">
            <div className="teach-ops-title"><TestTube size={18} /><span>TESTING + QUALITY CHECKS</span></div>
            <p>Tests focus on application behavior and service boundaries. External provider/model behavior is mocked, so a passing suite is not scientific validation.</p>
            <pre><code>{`python -m pytest tests -q

Set-Location frontend
npm run build`}</code></pre>
            <div className="teach-ops-foot"><span>Recorded backend run: <b>50 passed</b></span><span>Frontend production build: verified</span></div>
            <small className="teach-ops-caveat">The recorded 50-test result is a project baseline, not a fresh run of every test during this presentation update.</small>
          </article>
          <article className="teach-ops-card">
            <div className="teach-ops-title"><Server size={18} /><span>HOSTED RUNTIME</span></div>
            <p>The Dockerfile packages the Python/FastAPI backend only and listens on port <code>7860</code>. Serve the built frontend separately.</p>
            <div className="teach-deploy-steps">
              <span><b>1</b> Configure host secrets</span>
              <span><b>2</b> Attach persistent disk (for example <code>/data</code>)</span>
              <span><b>3</b> First ask/retrieve may download + extract indexes</span>
              <span><b>4</b> Check health, then test a cited answer</span>
            </div>
            <div className="teach-safe-note"><ShieldCheck size={15} /> <span>Deployment configuration exists; do not claim a public production deployment unless it has been independently verified.</span></div>
          </article>
        </div>
      </section>

      <section className="teach-section teach-limits" id="teach-limits">
        <div className="teach-section-heading">
          <span className="teach-section-label">08 / HONEST LIMITATIONS</span>
          <h2>Good research tools explain what they cannot prove.</h2>
          <p>Traceability is a major step—but it is not the same as scientific verification.</p>
        </div>
        <div className="teach-limit-grid">
          <article><span>01</span><h3>Retrieval can miss</h3><p>If relevant passages never enter the candidate set, the answer stage cannot cite them.</p></article>
          <article><span>02</span><h3>A citation can be structurally valid but weak</h3><p>The default validator confirms the passage ID is in the selected evidence. A semantic verifier is not configured.</p></article>
          <article><span>03</span><h3>Scores are not confidence</h3><p>Embedding, BM25, RRF, and cross-encoder scores rank items; none is a calibrated probability of truth.</p></article>
          <article><span>04</span><h3>The provider is external</h3><p>LLM output depends on NVIDIA API availability, limits, and network access. The health endpoint only checks configuration.</p></article>
        </div>
        <div className="teach-next-step"><div><span className="teach-section-label">NEXT RESEARCH STEPS</span><strong>Evaluate semantic support · report held-out test results · monitor refusal quality · validate deployment</strong></div><ShieldCheck size={20} /></div>
      </section>

      <section className="teach-speaking">
        <div className="teach-speaking-inner">
          <span className="teach-section-label">PRESENTER NOTES</span>
          <h2>A simple way to teach the whole application.</h2>
          <p>“We prepare and persist two indexes over 81,550 research passages. The API retrieves and reranks candidates, gives a bounded evidence packet to the model, validates its cited passage IDs, and returns both the answer and source text to the browser. We measure retrieval separately, keep secrets on the backend, and test the service boundaries.”</p>
          <div className="teach-speaking-steps">
            <span><b>1</b> Prepare indexes</span><span><b>2</b> Retrieve + rank</span><span><b>3</b> Generate safely</span><span><b>4</b> Trace + evaluate</span><span><b>5</b> Run + monitor</span>
          </div>
        </div>
      </section>

      <footer className="teach-footer">
        <div><span className="teach-section-label">FIELDWORK · G12 RESEARCH ASSISTANT</span><p>Ask a question. Follow the evidence.</p></div>
        <button className="teach-primary" onClick={onOpenChat}>Open the live research workspace <ArrowUpRight size={16} /></button>
      </footer>
    </main>
  );
}
