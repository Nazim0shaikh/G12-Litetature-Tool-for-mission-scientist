import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  FlaskConical,
  GitMerge,
  ListFilter,
  MessageSquareText,
  Search,
  ShieldCheck,
  Sigma,
} from "lucide-react";

type LandingPageProps = {
  onOpenChat: () => void;
};

export function LandingPage({ onOpenChat }: LandingPageProps) {
  const scrollToHowItWorks = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="landing-page">
      <header className="landing-nav">
        <a className="landing-brand" href="/" aria-label="Fieldwork home">
          <span className="landing-brand-mark"><FlaskConical size={18} strokeWidth={2.5} /></span>
          <span>Fieldwork</span>
        </a>
        <nav className="landing-links" aria-label="Landing page navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#pipeline-title">Pipeline</a>
          <a href="#architecture">Architecture</a>
          <a href="#evidence">Evidence</a>
        </nav>
        <button className="landing-nav-action" onClick={onOpenChat}>
          Open research chat <ArrowUpRight size={16} />
        </button>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-copy">
            <div className="landing-eyebrow">
              <span className="landing-eyebrow-dot" />
              AI research assistant for scientific literature
            </div>
            <h1>Trace every answer<br />to the research.</h1>
            <p>
              Search the QASPER corpus, receive clear explanations, and inspect
              the exact passages that support every conclusion.
            </p>
            <div className="landing-actions">
              <button className="landing-primary" onClick={onOpenChat}>
                Start a research question <ArrowRight size={17} />
              </button>
              <button className="landing-secondary" onClick={scrollToHowItWorks}>
                See how it works
              </button>
            </div>
            <div className="landing-proof">
              <ShieldCheck size={15} />
              <span>Evidence grounded</span>
              <span className="proof-divider" />
              <span>81,550 indexed passages</span>
            </div>
          </div>

          <div className="landing-product" id="evidence" aria-label="Product preview">
            <div className="preview-window">
              <div className="preview-topbar">
                <div className="preview-brand">
                  <span className="preview-mark"><FlaskConical size={14} /></span>
                  Fieldwork
                </div>
                <span className="preview-status"><span /> Grounded mode</span>
              </div>
              <div className="preview-body">
                <div className="preview-question">
                  <span>RESEARCH QUESTION</span>
                  <p>What is the role of seed lexicons?</p>
                </div>
                <div className="preview-answer">
                  <div className="preview-answer-label">
                    <span className="preview-check"><ShieldCheck size={13} /></span>
                    Supported answer
                  </div>
                  <p>
                    Seed lexicons provide starting sentiment information that
                    helps assign polarity to affective events.
                  </p>
                  <div className="preview-citations">
                    <span>1909.00694_00012</span>
                    <span>1909.00694_00013</span>
                  </div>
                </div>
                <div className="preview-evidence">
                  <div className="preview-evidence-heading">
                    <span>SUPPORTING EVIDENCE</span>
                    <span>02 sources</span>
                  </div>
                  <div className="preview-source">
                    <span className="source-number">01</span>
                    <div>
                      <strong>Minimally Supervised Learning</strong>
                      <small>Proposed Method · passage 00012</small>
                    </div>
                    <ArrowUpRight size={14} />
                  </div>
                  <div className="preview-source">
                    <span className="source-number">02</span>
                    <div>
                      <strong>Discourse Relation Based Pairs</strong>
                      <small>Methodology · passage 00013</small>
                    </div>
                    <ArrowUpRight size={14} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-method" id="how-it-works">
          <div className="method-heading">
            <span className="landing-section-label">HOW IT WORKS</span>
            <h2>From question<br />to verifiable source.</h2>
            <p>
              A hybrid retrieval and reranking pipeline finds candidate passages.
              A guarded generation stage answers only when the selected evidence supports a claim.
            </p>
          </div>
          <div className="method-grid">
            <article>
              <span className="method-number">01</span>
              <Search size={20} />
              <h3>Search two ways</h3>
              <p>MiniLM embeddings find semantic matches in ChromaDB while SQLite FTS5 finds exact keyword matches.</p>
            </article>
            <article>
              <span className="method-number">02</span>
              <GitMerge size={20} />
              <h3>Fuse rankings</h3>
              <p>Reciprocal Rank Fusion combines both rankings, giving passages from one or both methods a unified score.</p>
            </article>
            <article>
              <span className="method-number">03</span>
              <ListFilter size={20} />
              <h3>Rerank evidence</h3>
              <p>A MiniLM cross encoder reads each question passage pair and prioritizes the passages most relevant to the question.</p>
            </article>
          </div>
        </section>

        <section className="landing-pipeline" aria-labelledby="pipeline-title">
          <div className="pipeline-heading">
            <div>
              <span className="landing-section-label">RETRIEVAL AND GENERATION</span>
              <h2 id="pipeline-title">The full pipeline</h2>
            </div>
            <p>
              Fieldwork keeps retrieval, reranking, generation, citation checking,
              and refusal as separate stages. Each stage can be tested and changed independently.
            </p>
          </div>

          <div className="pipeline-flow" aria-label="System workflow">
            <div className="pipeline-stage">
              <span className="pipeline-index">01</span>
              <Search size={18} />
              <h3>Question</h3>
              <p>Validate and normalize the research question without rewriting technical terms.</p>
            </div>
            <ArrowRight className="pipeline-arrow" size={16} />
            <div className="pipeline-stage">
              <span className="pipeline-index">02</span>
              <Sigma size={18} />
              <h3>Hybrid retrieval</h3>
              <p>Retrieve semantic and keyword candidates, then fuse rankings with RRF.</p>
            </div>
            <ArrowRight className="pipeline-arrow" size={16} />
            <div className="pipeline-stage">
              <span className="pipeline-index">03</span>
              <ListFilter size={18} />
              <h3>Reranking</h3>
              <p>Score candidate passage pairs with a cross encoder and retain the strongest evidence.</p>
            </div>
            <ArrowRight className="pipeline-arrow" size={16} />
            <div className="pipeline-stage">
              <span className="pipeline-index">04</span>
              <MessageSquareText size={18} />
              <h3>Grounded answer</h3>
              <p>Construct a bounded context and generate a structured answer with exact passage IDs.</p>
            </div>
            <ArrowRight className="pipeline-arrow" size={16} />
            <div className="pipeline-stage">
              <span className="pipeline-index">05</span>
              <ShieldCheck size={18} />
              <h3>Validate and refuse</h3>
              <p>Check citation structure and evidence support. Refuse or explain limitations when evidence is weak.</p>
            </div>
          </div>
        </section>

        <section className="landing-architecture" id="architecture">
          <div className="architecture-heading">
            <span className="landing-section-label">SYSTEM STRUCTURE</span>
            <h2>Modular by design.</h2>
          </div>
          <div className="architecture-grid">
            <article className="architecture-card">
              <div className="architecture-card-top">
                <Search size={18} />
                <span>01 / INDEXES</span>
              </div>
              <h3>Existing research indexes</h3>
              <p>
                81,550 passages are indexed in ChromaDB and SQLite FTS5.
                Normal startup does not rebuild or reembed the corpus.
              </p>
              <div className="architecture-tags">
                <span>ChromaDB</span>
                <span>Cosine search</span>
                <span>SQLite FTS5</span>
              </div>
            </article>
            <article className="architecture-card">
              <div className="architecture-card-top">
                <GitMerge size={18} />
                <span>02 / SERVICE LAYER</span>
              </div>
              <h3>Independent RAG services</h3>
              <p>
                Retrieval, reranking, context building, answer generation, citation
                validation, and refusal handling are separate reusable services.
              </p>
              <div className="architecture-tags">
                <span>RRF k = 60</span>
                <span>Cross encoder</span>
                <span>Structured JSON</span>
              </div>
            </article>
            <article className="architecture-card">
              <div className="architecture-card-top">
                <ShieldCheck size={18} />
                <span>03 / RELIABILITY</span>
              </div>
              <h3>Evidence before fluency</h3>
              <p>
                Passage IDs are checked against supplied evidence and the original
                corpus. Weak claims do not silently become supported sources.
              </p>
              <div className="architecture-tags">
                <span>Refusal</span>
                <span>Citation checks</span>
                <span>Structured errors</span>
              </div>
            </article>
          </div>
        </section>

        <section className="landing-coverage" id="coverage">
          <span className="landing-section-label">BUILT FOR RESEARCH</span>
          <p>Ask with confidence. Refuse when evidence is incomplete. Follow every answer back to the source.</p>
          <button className="landing-primary" onClick={onOpenChat}>
            Open the research workspace <ArrowRight size={17} />
          </button>
        </section>
      </main>
    </div>
  );
}
