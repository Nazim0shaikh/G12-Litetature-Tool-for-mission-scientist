import { useState } from "react";
import {
  ArrowUpRight,
  BookOpen,
  ChevronDown,
  Clock3,
  Copy,
  FileText,
  FlaskConical,
  History,
  Menu,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { LandingPage } from "./landing";

type Citation = {
  passage_id: string;
  paper_title: string;
  section_name: string;
  supporting_text: string;
  claim: string;
  citation_valid: boolean;
};

type Evidence = {
  passage_id: string;
  paper_id: string;
  title: string;
  section_name: string;
  text: string;
  reranker_score?: number | null;
};

type AnswerResponse = {
  question: string;
  status: string;
  answer: string;
  citations: Citation[];
  evidence: Evidence[];
  evidence_reasons?: string[];
};

const recentQuestions = [
  "How does retrieval augmentation improve factuality?",
  "What is the role of seed lexicons?",
  "Compare dense and sparse retrieval methods",
];

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AnswerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const askQuestion = async (value = question) => {
    const trimmed = value.trim();
    if (!trimmed || loading) return;
    setQuestion(trimmed);
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      if (!response.ok) {
        const message = response.status === 503
          ? "The research service is not ready yet."
          : response.status === 502
            ? "The answer provider returned an unusable response. Please try again."
            : "We could not answer that question.";
        throw new Error(message);
      }
      setAnswer((await response.json()) as AnswerResponse);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const copyAnswer = async () => {
    if (!answer) return;
    const sources = getTraceableCitations(answer).map(
      ({ citation }, index) =>
        `[${index + 1}] ${citation.claim} — ${citation.paper_title}, ${citation.section_name}, ${citation.passage_id}`,
    );
    const copiedAnswer = [
      answer.answer,
      sources.length > 0 ? `Supporting citations:\n${sources.join("\n")}` : "",
    ].filter(Boolean).join("\n\n");
    await navigator.clipboard.writeText(copiedAnswer);
  };

  if (!chatOpen) {
    return <LandingPage onOpenChat={() => setChatOpen(true)} />;
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? "sidebar-open" : ""}`}>
        <button className="brand-row" onClick={() => setChatOpen(false)} aria-label="Return to landing page">
          <div className="brand-mark"><FlaskConical size={18} strokeWidth={2.5} /></div>
          <span>Fieldwork</span>
        </button>
        <button className="sidebar-close" onClick={() => setMobileNavOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        <button className="new-query" onClick={() => { setAnswer(null); setQuestion(""); setError(""); setMobileNavOpen(false); }}>
          <Sparkles size={16} /> New research query
        </button>
        <nav className="primary-nav" aria-label="Primary navigation">
          <a className="nav-item active" href="#workspace"><Search size={16} /> Workspace</a>
          <a className="nav-item" href="#history"><History size={16} /> Research history</a>
          <a className="nav-item" href="#sources"><BookOpen size={16} /> Source library</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="system-card">
            <div className="system-title"><span className="status-dot" /> System ready</div>
            <p>Evidence index connected</p>
            <span className="mono-label">81,550 passages</span>
          </div>
          <a className="nav-item" href="#settings"><Settings2 size={16} /> Settings</a>
          <div className="user-row"><div className="avatar">N</div><div><strong>Nazim</strong><span>Researcher</span></div><ChevronDown size={14} /></div>
        </div>
      </aside>

      <main className="main-content" id="workspace">
        <header className="topbar">
          <button className="icon-button menu-button" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
          <div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><strong>New query</strong></div>
          <div className="topbar-actions"><span className="topbar-label"><ShieldCheck size={14} /> Grounded mode</span><div className="avatar small">N</div></div>
        </header>

        <section className="workspace">
          <div className="intro">
            <div className="eyebrow"><span className="eyebrow-line" /> SCIENTIFIC LITERATURE, MADE TRACEABLE</div>
            <h1>Ask better questions.<br /><span>Find the evidence.</span></h1>
            <p className="intro-copy">A research assistant that searches the QASPER corpus, explains what the literature supports, and shows you exactly where it came from.</p>
          </div>

          <section className="query-card" aria-label="Research question">
            <div className="query-card-header"><span>Research question</span><span className="char-count">{question.length} / 2000</span></div>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) askQuestion(); }} placeholder="What would you like to understand from the research?" rows={3} />
            <div className="query-card-footer"><span className="hint"><span className="key">⌘</span> + <span className="key">↵</span> to ask</span><button className="ask-button" onClick={() => askQuestion()} disabled={!question.trim() || loading}>{loading ? "Researching..." : "Ask the literature"} <ArrowUpRight size={17} /></button></div>
          </section>

          {error && <div className="error-banner"><span>{error}</span><button onClick={() => setError("")}><X size={15} /></button></div>}

          {!answer && !loading && !error && (
            <section className="starter-grid">
              <div className="starter-intro"><span className="section-label">START HERE</span><h2>Questions worth<br />following up.</h2><p>Try one of these prompts or start with your own.</p></div>
              <div className="question-list">{recentQuestions.map((item, index) => <button className="suggestion" key={item} onClick={() => askQuestion(item)}><span className="suggestion-number">0{index + 1}</span><span>{item}</span><ArrowUpRight size={16} /></button>)}</div>
            </section>
          )}

          {loading && <LoadingState />}
          {answer && !loading && <AnswerView answer={answer} onCopy={copyAnswer} onSelectEvidence={setSelectedEvidence} />}
        </section>
        <footer className="footer-note"><span>Fieldwork is an evidence retrieval tool, not a substitute for expert review.</span><span className="footer-links"><a href="#methodology">Methodology</a><a href="#limitations">Limitations</a></span></footer>
      </main>
      {selectedEvidence && <EvidenceDrawer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} />}
    </div>
  );
}

function LoadingState() {
  return <section className="loading-card"><div className="loading-orbit"><div className="brand-mark"><FlaskConical size={20} /></div></div><div><span className="section-label">WORKING THROUGH THE LITERATURE</span><h2>Retrieving and reranking evidence<span className="loading-dots">...</span></h2><p>Searching dense and keyword indexes, then checking the strongest passages.</p></div></section>;
}

function AnswerView({ answer, onCopy, onSelectEvidence }: { answer: AnswerResponse; onCopy: () => void; onSelectEvidence: (evidence: Evidence) => void }) {
  const statusLabel = answer.status === "answered" ? "Supported answer" : answer.status.replaceAll("_", " ");
  const citations = getTraceableCitations(answer);
  return <section className="answer-section">
    <div className="answer-header"><div><span className="section-label">RESEARCH RESULT</span><h2>{statusLabel}</h2></div><button className="copy-button" onClick={onCopy}><Copy size={15} /> Copy answer</button></div>
    <div className={`answer-card ${answer.status !== "answered" ? "answer-card-caution" : ""}`}><div className="answer-status"><span className="status-dot" /> {answer.status === "answered" ? "Evidence supports this response" : "Evidence is limited"}</div><p>{answer.answer}</p><div className="answer-meta"><span><Clock3 size={14} /> Retrieved just now</span><span><FileText size={14} /> {answer.evidence.length} passages reviewed</span></div></div>
    {citations.length > 0 && <section className="citation-section" aria-label="Supporting citations"><div className="evidence-heading"><div><span className="section-label">SUPPORTING CITATIONS</span><h3>Claims linked to source passages</h3></div><span className="evidence-count">{citations.length} citations</span></div><div className="citation-list">{citations.map(({ citation, evidence }, index) => <button className="citation-row" key={`${citation.passage_id}-${index}`} onClick={() => onSelectEvidence(evidence)}><span className="citation-number">[{index + 1}]</span><span className="citation-content"><span className="citation-claim">{citation.claim}</span><strong>{citation.paper_title}</strong><span className="citation-source">{citation.section_name} <span className="bullet">·</span> {citation.passage_id} <span className="citation-open">View passage</span></span></span><ArrowUpRight size={16} /></button>)}</div></section>}
    <div className="evidence-heading"><div><span className="section-label">SUPPORTING EVIDENCE</span><h3>Passages behind this answer</h3></div><span className="evidence-count">{answer.evidence.length} sources</span></div>
    <div className="evidence-list">{answer.evidence.map((evidence, index) => <button className="evidence-row" key={evidence.passage_id} onClick={() => onSelectEvidence(evidence)}><span className="evidence-index">0{index + 1}</span><span className="evidence-main"><strong>{evidence.title}</strong><span>{evidence.section_name} <span className="bullet">·</span> {evidence.passage_id}</span><p>{evidence.text}</p></span><ArrowUpRight size={17} /></button>)}</div>
  </section>;
}

function getTraceableCitations(answer: AnswerResponse) {
  return answer.citations.flatMap((citation) => {
    if (!citation.citation_valid) return [];
    const evidence = answer.evidence.find((item) => item.passage_id === citation.passage_id);
    return evidence ? [{ citation, evidence }] : [];
  });
}

function EvidenceDrawer({ evidence, onClose }: { evidence: Evidence; onClose: () => void }) {
  return <div className="drawer-backdrop" onClick={onClose}><aside className="evidence-drawer" onClick={(event) => event.stopPropagation()}><div className="drawer-header"><span className="section-label">SOURCE PASSAGE</span><button className="icon-button" onClick={onClose} aria-label="Close evidence"><X size={18} /></button></div><div className="drawer-number">Evidence</div><h2>{evidence.title}</h2><div className="drawer-meta"><span>{evidence.section_name}</span><span>{evidence.passage_id}</span></div><blockquote>{evidence.text}</blockquote><div className="drawer-detail"><span className="section-label">TRACEABILITY</span><p>This passage was selected from the ranked evidence set for your question. Passage IDs are preserved from the original corpus.</p></div></aside></div>;
}

export default App;
