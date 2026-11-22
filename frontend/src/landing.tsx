import { ArrowRight, ArrowUpRight, BookOpen, FlaskConical, Search, ShieldCheck } from "lucide-react";

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
          <a href="#evidence">Evidence</a>
          <a href="#coverage">Coverage</a>
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
          </div>
          <div className="method-grid">
            <article>
              <span className="method-number">01</span>
              <Search size={20} />
              <h3>Retrieve</h3>
              <p>Dense and keyword search find relevant passages across the scientific corpus.</p>
            </article>
            <article>
              <span className="method-number">02</span>
              <ShieldCheck size={20} />
              <h3>Ground</h3>
              <p>The answer is generated only from reranked evidence selected for the question.</p>
            </article>
            <article>
              <span className="method-number">03</span>
              <BookOpen size={20} />
              <h3>Trace</h3>
              <p>Every claim leads to an exact passage, paper title, section, and citation ID.</p>
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
