"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  CloudUpload,
  Crosshair,
  Database,
  FileText,
  Filter,
  Globe2,
  LockKeyhole,
  MapPin,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
  UserRound,
  Users,
  X,
  Zap,
} from "lucide-react";

type Candidate = {
  id: number;
  name: string;
  role: string;
  score: number;
  location: string;
  experience: number;
  initials: string;
  tone: string;
  headline: string;
  raw: string;
  fit: string;
  signals: {
    label: string;
    value: string;
    type: "good" | "warn" | "neutral";
  }[];
  timeline: {
    company: string;
    title: string;
    period: string;
    impact: string;
  }[];
  skills: { name: string; level: string; value: number }[];
};



function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="logo-mark">
        <ShieldCheck size={20} />
      </div>
      {!compact && (
        <div>
          <div className="font-semibold tracking-tight text-foreground">
            RecruitShield <span className="text-cyan-300">AI</span>
          </div>
          <div className="micro-label text-muted-foreground">
            AGENTIC RECRUITMENT INTELLIGENCE
          </div>
        </div>
      )}
    </div>
  );
}
function GlowButton({
  children,
  onClick,
  secondary = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  secondary?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={secondary ? "button-secondary" : "button-glow"}
    >
      {children}
      <ArrowRight size={16} />
    </button>
  );
}

function DropZone({
  title,
  description,
  icon,
  files,
  onFiles,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  files: string[];
  onFiles: (x: FileList | null) => void;
}) {
  return (
    <div className="ingest-card">
      <div className="card-heading">
        <span className="drop-icon">{icon}</span>
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>
      </div>
      <label className="drop-zone">
        <input
          type="file"
          multiple
          accept=".csv,.jsonl,.pdf"
          onChange={(e: any) => onFiles(e.target.files)}
        />
        <span className="upload-circle">
          <CloudUpload size={20} />
        </span>
        <strong>
          Drop files here or <u>browse</u>
        </strong>
        <small>
          CSV, JSONL, PDF <span>/</span> MAX 50MB
        </small>
      </label>
      {files.length > 0 && (
        <div className="file-list">
          {files.slice(-3).map((f) => (
            <div key={f}>
              <Check size={13} />
              {f}
              <X size={13} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatusDot() {
  return <span className="status-dot" aria-label="System online" />;
}

export default function RecruitShieldApp() {

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState({
    total_candidates: 0,
    eligible_candidates: 0,
    honeypot_count: 0,
    total_ranked: 0
  });

  // API: Fetch shortlist
  const fetchShortlist = async (p = 1) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/shortlist?page=${p}&limit=50`);
      const data = await res.json();
      
      if (data.stats) {
        setStats(data.stats);
      }
      if (data.page) setPage(data.page);
      if (data.total_pages) setTotalPages(data.total_pages);

      const mapped = (data.shortlist || []).map((c: any) => {
        const tones = ["cyan", "violet", "blue", "orange", "green"];
        
        // Map backend skills to v0 format — use real proficiency and duration
        const proficiencyToLevel = (p: string) => {
          const lp = (p || "").toLowerCase();
          if (lp === "expert" || lp === "advanced") return "Expert";
          if (lp === "intermediate") return "Advanced";
          return "Intermediate";
        };
        const proficiencyToValue = (p: string, months: number) => {
          const lp = (p || "").toLowerCase();
          const base = lp === "expert" ? 88 : lp === "advanced" ? 78 : lp === "intermediate" ? 65 : 55;
          return Math.min(99, base + Math.floor((months || 0) / 12));
        };
        const uiSkills = (c.skills || []).map((s: any) => ({
          name: typeof s === "string" ? s : s.name,
          level: typeof s === "string" ? "Advanced" : proficiencyToLevel(s.proficiency),
          value: typeof s === "string" ? 75 : proficiencyToValue(s.proficiency, s.duration_months)
        }));
        
        // Map backend timeline to v0 format — use real date info
        const uiTimeline = c.career_history ? c.career_history.map((h: any) => ({
           company: h.company || "Unknown",
           title: h.title || "Role",
           period: h.start_date ? `${h.start_date}${h.end_date ? " → " + h.end_date : " → Present"}` : "Past",
           impact: h.description || h.responsibilities || "Contributed to company growth and product development."
        })) : [];
        
        // Map signals
        const signals = [];
        if (c.signals) {
           if (c.signals.flight_risk_score > 70) signals.push({ label: "High Flight Risk", value: "Alert", type: "warn" });
           else signals.push({ label: "Retention", value: "Stable", type: "good" });
           
           if (c.signals.github_open_source_score) signals.push({ label: "GitHub Score", value: `${c.signals.github_open_source_score}/100`, type: "good" });
        }
        
        return {
          id: c.candidate_id || c.rank,
          rank: c.rank,
          name: c.name,
          role: c.current_title,
          score: Math.round(c.score * 100), // convert 0-1 score to 0-100
          location: c.location,
          experience: c.years_exp,
          initials: (c.name || "CN").split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase(),
          tone: tones[(c.rank || 1) % tones.length],
          headline: c.headline,
          raw: c.score ? c.score.toFixed(4) : "0.0000",
          fit: c.reasoning,
          signals: signals.length > 0 ? signals : [
            { label: 'Open-to-work', value: 'Active', type: 'good' },
            { label: 'Verified', value: 'Yes', type: 'good' }
          ],
          timeline: uiTimeline.length > 0 ? uiTimeline : [
            { company: c.current_company, title: c.current_title, period: "Current", impact: "Current role" }
          ],
          skills: uiSkills.length > 0 ? uiSkills : [
            { name: "Python", level: "Expert", value: 90 }
          ]
        };
      });
      setCandidates(mapped);
      if (mapped.length > 0) setSelected(mapped[0]);
    } catch (e) {
      console.error("Failed to fetch shortlist", e);
    }
  };

  useEffect(() => {
    fetchShortlist(1);
  }, []);

  const [screen, setScreen] = useState<
    "landing" | "ingest" | "pipeline" | "deepdive"
  >("landing");
  const [selected, setSelected] = useState<Candidate>(candidates[0]);
  const [query, setQuery] = useState("");
  const [threshold, setThreshold] = useState(0);
  const [minExp, setMinExp] = useState(0);
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [jd, setJd] = useState("");
  const [jdSkills, setJdSkills] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);

  const filtered = useMemo(
    () =>
      candidates.filter(
        (c) =>
          c.score >= threshold &&
          c.experience >= minExp &&
          (locations.length === 0 || locations.some((l) => c.location.includes(l))) &&
          (selectedSkills.length === 0 || selectedSkills.every(s => c.skills.some((cs: any) => cs.name.toLowerCase() === s.toLowerCase()))) &&
          `${c.name} ${c.role} ${c.location}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [query, threshold, minExp, locations, selectedSkills, candidates],
  );

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "rank top candidates", job_description: jd })
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(`Agent Execution Failed: ${err.detail || res.statusText}`);
        return;
      }
      
      await fetchShortlist(1);
      setScreen("pipeline");
    } catch (e) {
      console.error(e);
      alert("Network Error: Could not reach the backend agent.");
    } finally {
      setLoading(false);
    }
  };

  if (screen === "landing")
    return <Landing onLaunch={() => setScreen("ingest")} />;
  if (screen === "ingest")
    return (
      <Ingest
        files={files}
        setFiles={setFiles}
        jd={jd}
        setJd={setJd}
        setJdSkills={setJdSkills}
        loading={loading}
        onBack={() => setScreen("landing")}
        onAnalyze={analyze}
      />
    );
  if (screen === "deepdive")
    return (
      <DeepDive candidate={selected} onBack={() => setScreen("pipeline")} />
    );
  return (
    <Pipeline
      candidates={candidates}
      filtered={filtered}
      stats={stats}
      page={page}
      totalPages={totalPages}
      onPageChange={(p) => fetchShortlist(p)}
      query={query}
      setQuery={setQuery}
      threshold={threshold}
      setThreshold={setThreshold}
      minExp={minExp}
      setMinExp={setMinExp}
      locations={locations}
      setLocations={setLocations}
      jdSkills={jdSkills}
      selectedSkills={selectedSkills}
      setSelectedSkills={setSelectedSkills}
      onBack={() => setScreen("ingest")}
      onSelect={(c) => {
        setSelected(c);
        setScreen("deepdive");
      }}
    />
  );
}

function Landing({ onLaunch }: { onLaunch: () => void }) {
  return (
    <main className="min-h-screen overflow-hidden">
      <header className="site-header">
        <Logo />
        <nav className="hidden items-center gap-8 text-sm text-muted-foreground md:flex">
          <a href="#signal">Platform</a>
          <a href="#how">How it works</a>
          <a href="#security">Security</a>
        </nav>
        <div className="flex items-center gap-4">
          <span className="hidden micro-label text-muted-foreground sm:block">
            V 1.4.0 / BETA
          </span>
          <button className="icon-button" aria-label="Help">
            <CircleHelp size={17} />
          </button>
        </div>
      </header>
      <section className="hero-shell">
        <div className="hero-copy">
          <div className="eyebrow">
            <StatusDot /> SYSTEM ONLINE{" "}
            <span className="text-muted-foreground">/</span> AUTONOMOUS AGENTS
            READY
          </div>
          <h1>
            The future of
            <br />
            <span className="hero-gradient">AI recruiting.</span>
          </h1>
          <p className="hero-sub">
            Automated candidate sourcing, semantic matching, and threat anomaly
            detection powered by autonomous agents.
          </p>
          <div className="flex flex-wrap items-center gap-4">
            <GlowButton onClick={onLaunch}>Launch workspace</GlowButton>
            <button className="text-button">
              <PlayIcon /> See how it works
            </button>
          </div>
          <div className="flex items-center gap-5 pt-8 text-xs text-muted-foreground">
            <div className="flex -space-x-2">
              <span className="avatar-chip">MC</span>
              <span className="avatar-chip violet">JW</span>
              <span className="avatar-chip blue">PS</span>
              <span className="avatar-chip more">+2k</span>
            </div>
            <span>
              Trusted by the next generation
              <br />
              of technical teams
            </span>
          </div>
        </div>
        <div className="hero-visual">
          <div className="visual-orbit orbit-one" />
          <div className="visual-orbit orbit-two" />
          <div className="float-card top-card">
            <div className="flex items-center justify-between">
              <span className="micro-label">LIVE SIGNAL</span>
              <span className="signal-live">
                <StatusDot /> LIVE
              </span>
            </div>
            <div className="signal-big">
              94.8<span>%</span>
            </div>
            <div className="text-xs text-muted-foreground">
              candidate fit confidence
            </div>
            <div className="mini-bars">
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
          </div>
          <div className="dashboard-window">
            <div className="window-top">
              <span className="window-dot red" />
              <span className="window-dot yellow" />
              <span className="window-dot green" />
              <span className="micro-label ml-3">
                RECRUITSHIELD / MATCH ENGINE
              </span>
            </div>
            <div className="window-body">
              <div className="flex items-center justify-between">
                <div>
                  <div className="micro-label text-cyan-300">
                    ACTIVE PIPELINE
                  </div>
                  <div className="mt-1 text-lg font-semibold">
                    Candidate intelligence
                  </div>
                </div>
                <div className="mini-pill">
                  <Zap size={12} /> AGENT ACTIVE
                </div>
              </div>
              <div className="mock-stats">
                <div>
                  <span className="micro-label">PROCESSED</span>
                  <b>2,481</b>
                  <em>+18.4%</em>
                </div>
                <div>
                  <span className="micro-label">AVG. MATCH</span>
                  <b>87.6</b>
                  <em>+4.2%</em>
                </div>
                <div>
                  <span className="micro-label">ANOMALIES</span>
                  <b>03</b>
                  <em className="orange-text">-12.8%</em>
                </div>
              </div>
              <div className="mock-table">
                <div className="mock-row mock-head">
                  <span>CANDIDATE</span>
                  <span>ROLE</span>
                  <span>SCORE</span>
                </div>
                {[{id:1, tone:"violet", initials:"RS", name:"Rowan Smith", role:"Backend Engineer", score:94}, {id:2, tone:"cyan", initials:"ET", name:"Elias Torres", role:"ML Engineer", score:91}, {id:3, tone:"blue", initials:"MC", name:"Mia Chen", role:"Frontend Engineer", score:89}].map((c: any) => (
                  <div className="mock-row" key={c.id}>
                    <span className="flex items-center gap-2">
                      <span className={`tiny-avatar ${c.tone}`}>
                        {c.initials}
                      </span>
                      {c.name}
                    </span>
                    <span className="text-muted-foreground">{c.role}</span>
                    <span className="score-text">{c.score}.0</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="float-card bottom-card">
            <div className="flex items-center gap-2 text-xs">
              <span className="pulse-ring">
                <Sparkles size={13} />
              </span>{" "}
              <span className="text-muted-foreground">AGENT REASONING</span>
            </div>
            <div className="mt-3 text-xs text-foreground">
              Semantic match complete
            </div>
            <div className="mt-2 loading-line">
              <span />
            </div>
          </div>
        </div>
      </section>
      <div className="logo-ribbon">
        <span className="micro-label">BUILT FOR TEAMS AT</span>
        <b>northstar</b>
        <b>vertex</b>
        <b>orbital</b>
        <b>momentum</b>
        <b>
          signal<span className="text-cyan-300">/</span>works
        </b>
      </div>
      <section id="signal" className="feature-strip">
        <div>
          <div className="feature-icon">
            <Crosshair size={18} />
          </div>
          <h3>Semantic precision</h3>
          <p>
            Find the signal beyond keywords with embeddings built for technical
            talent.
          </p>
        </div>
        <div>
          <div className="feature-icon">
            <ShieldCheck size={18} />
          </div>
          <h3>Threat-aware by design</h3>
          <p>
            Surface anomalies and protect your hiring funnel before they become
            risk.
          </p>
        </div>
        <div>
          <div className="feature-icon">
            <BarChart3 size={18} />
          </div>
          <h3>Decisions, accelerated</h3>
          <p>
            Move from thousands of profiles to a confident shortlist in minutes.
          </p>
        </div>
      </section>
    </main>
  );
}
function PlayIcon() {
  return <span className="play-icon">▶</span>;
}

function Ingest({
  files,
  setFiles,
  jd,
  setJd,
  setJdSkills,
  loading,
  onBack,
  onAnalyze,
}: {
  files: string[];
  setFiles: (x: string[]) => void;
  jd: string;
  setJd: (x: string) => void;
  setJdSkills: (x: string[]) => void;
  loading: boolean;
  onBack: () => void;
  onAnalyze: () => void;
}) {
  const addFiles = async (list: FileList | null, type: 'jd' | 'candidates') => {
    if (!list || list.length === 0) return;
    const file = list[0];
    
    // Optimistic UI update
    if (type === 'candidates') setFiles([...files, ...Array.from(list).map(f => f.name)]);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const endpoint = type === 'jd' ? '/upload_jd' : '/upload_candidates';
      const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      
      if (type === 'jd') {
         if (data.text) setJd(data.text);
         if (data.metadata && data.metadata.skills_found) setJdSkills(data.metadata.skills_found);
      }
    } catch (e) {
      console.error(e);
    }
  };
  return (
    <main className="workspace min-h-screen">
      <WorkspaceHeader step="01 / INGEST" onBack={onBack} />
      <section className="workspace-content narrow">
        <div className="section-kicker">
          <Database size={15} /> DATA INGESTION
        </div>
        <h1 className="page-title">
          Give the agents
          <br />
          <span>something to think about.</span>
        </h1>
        <p className="page-intro">
          Upload your talent pool and the role you&apos;re hiring for.
          RecruitShield will normalize, embed, and map the entire candidate
          graph.
        </p>
        <div className="ingest-grid">
          <DropZone
            title="Upload candidates database"
            description="CSV, JSONL, or bulk PDF resumes"
            icon={<Users size={22} />}
            files={files}
            onFiles={(list: any) => addFiles(list, 'candidates')}
          />
          <div className="ingest-card">
            <div className="card-heading">
              <span className="drop-icon">
                <FileText size={22} />
              </span>
              <div>
                <h3>
                  Job description <span className="required">REQUIRED</span>
                </h3>
                <p>Upload a PDF or paste manually</p>
              </div>
            </div>
            <label className="drop-zone compact">
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => addFiles(e.target.files, 'jd')}
              />
              <Upload size={18} />
              <span>
                Drop JD PDF or <u>browse</u>
              </span>
              <small>PDF up to 10MB</small>
            </label>
            <div className="or-line">
              <span /> OR PASTE TEXT <span />
            </div>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste the job description here..."
            />
          </div>
        </div>
        <div className="ingest-footer">
          <div className="privacy-note">
            <LockKeyhole size={15} />
            <span>
              <b>Your data stays yours.</b> Encrypted in transit and never used
              to train models.
            </span>
          </div>
          <GlowButton onClick={onAnalyze}>
            {loading ? (
              <>
                <span className="spinner" /> Agents are reasoning...
              </>
            ) : (
              <>Analyze & match candidates</>
            )}
          </GlowButton>
        </div>
      </section>
    </main>
  );
}

function WorkspaceHeader({
  step,
  onBack,
}: {
  step: string;
  onBack: () => void;
}) {
  return (
    <header className="workspace-header">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={16} /> <span className="hidden sm:inline">Back</span>
      </button>
      <Logo compact />
      <div className="flex items-center gap-4">
        <span className="micro-label text-muted-foreground">{step}</span>
        <StatusDot />
        <button className="icon-button">
          <Bell size={16} />
        </button>
        <div className="user-badge">RS</div>
      </div>
    </header>
  );
}

function Pipeline({
  candidates,
  filtered,
  stats,
  page,
  totalPages,
  onPageChange,
  query,
  setQuery,
  threshold,
  setThreshold,
  minExp,
  setMinExp,
  locations,
  setLocations,
  jdSkills,
  selectedSkills,
  setSelectedSkills,
  onBack,
  onSelect,
}: {
  candidates: Candidate[];
  filtered: Candidate[];
  stats: { total_candidates: number; eligible_candidates: number; honeypot_count: number; total_ranked: number };
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
  query: string;
  setQuery: (x: string) => void;
  threshold: number;
  setThreshold: (x: number) => void;
  minExp: number;
  setMinExp: (x: number) => void;
  locations: string[];
  setLocations: (x: string[]) => void;
  jdSkills: string[];
  selectedSkills: string[];
  setSelectedSkills: (s: string[]) => void;
  onBack: () => void;
  onSelect: (c: Candidate) => void;
}) {
  const toggle = (v: string) =>
    setLocations(
      locations.includes(v)
        ? locations.filter((x) => x !== v)
        : [...locations, v],
    );
  return (
    <main className="workspace min-h-screen">
      <WorkspaceHeader step="02 / MATCH" onBack={onBack} />
      <div className="pipeline-layout">
        <aside className="filter-sidebar">
          <div className="flex items-center justify-between">
            <div className="section-kicker">
              <Filter size={14} /> FILTERS
            </div>
            <button
              className="clear-button"
              onClick={() => {
                setThreshold(0);
                setMinExp(0);
                setLocations([]);
              }}
            >
              Clear all
            </button>
          </div>
          <FilterBlock title="Required Skills (JD)">
            {jdSkills.length > 0 ? jdSkills.map((s) => (
              <label key={s}>
                <input 
                  type="checkbox" 
                  checked={selectedSkills.includes(s)}
                  onChange={(e) => {
                    if (e.target.checked) setSelectedSkills([...selectedSkills, s]);
                    else setSelectedSkills(selectedSkills.filter(x => x !== s));
                  }}
                />
                {s}
              </label>
            )) : <span style={{fontSize:'12px', color:'#7d899c'}}>Upload JD to extract skills</span>}
          </FilterBlock>
          <FilterBlock title="Experience">
            <input
              className="range"
              type="range"
              min="0"
              max="12"
              value={minExp}
              onChange={(e) => setMinExp(+e.target.value)}
            />
            <div className="range-labels">
              <span>{minExp}+ years</span>
              <span>12 years</span>
            </div>
          </FilterBlock>
          <FilterBlock title="Location">
            {Array.from(new Set(candidates.map(c => c.location))).map((loc) => {
              const count = candidates.filter(c => c.location === loc).length;
              return (
                <label key={loc}>
                  <input
                    type="checkbox"
                    checked={locations.includes(loc)}
                    onChange={() => toggle(loc)}
                  />
                  <span>{loc}</span>
                  <em>{count}</em>
                </label>
              );
            })}
          </FilterBlock>
          <FilterBlock title="Match score">
            <input
              className="range"
              type="range"
              min="0"
              max="95"
              value={threshold}
              onChange={(e) => setThreshold(+e.target.value)}
            />
            <div className="range-labels">
              <span>{threshold}+ score</span>
              <span>95</span>
            </div>
          </FilterBlock>
          <div className="filter-foot">
            <ShieldCheck size={16} />
            <span>
              Threat screening
              <br />
              <b>Active & monitoring</b>
            </span>
            <StatusDot />
          </div>
        </aside>
        <section className="pipeline-main">
          <div className="pipeline-top">
            <div className="breadcrumbs">
              <span onClick={onBack}>Workspace</span>
              <span>/</span>
              <b>Active pipeline</b>
            </div>
            <div className="pipeline-actions">
              <label className="search-box">
                <Search size={16} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search candidates..."
                />
                <kbd>⌘ K</kbd>
              </label>
              <button className="icon-button">
                <Bell size={16} />
              </button>
              <div className="user-badge">RS</div>
            </div>
          </div>
          <div className="pipeline-heading">
            <div>
              <div className="section-kicker">
                <span className="pulse-ring">
                  <Sparkles size={12} />
                </span>{" "}
                AGENT COMPLETE
              </div>
              <h1>Candidate intelligence</h1>
              <p>Ranked by semantic fit, experience, and verified signals.</p>
            </div>
            <button className="sort-button">
              Ranked by <b>Match score</b>
              <ChevronDown size={14} />
            </button>
          </div>
          <div className="metrics-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <Metric
              label="TOTAL CANDIDATES"
              value={stats.total_candidates > 0 ? stats.total_candidates.toLocaleString() : "Loading…"}
              change="Total in dataset"
            />
            <Metric
              label="ELIGIBLE CANDIDATES"
              value={stats.eligible_candidates > 0 ? stats.eligible_candidates.toLocaleString() : "Loading…"}
              change="Active screening pool"
            />
            <Metric 
              label="HONEYPOT PROFILES" 
              value={stats.total_candidates > 0 ? stats.honeypot_count.toLocaleString() : "Loading…"} 
              change="Fake profiles caught" 
            />
          </div>
          <div className="candidate-table">
            <div className="table-head">
              <span>RANK / CANDIDATE</span>
              <span>ROLE</span>
              <span>LOCATION</span>
              <span>MATCH SCORE</span>
              <span>STATUS</span>
              <span />
            </div>
            {filtered.length === 0 ? (
              <div className="empty-state">
                <Search size={24} />
                <b>No candidates match these filters</b>
                <span>Try widening the experience or score threshold.</span>
              </div>
            ) : (
              filtered.map((c, i) => (
                <button
                  className="candidate-row"
                  key={c.id || i}
                  onClick={() => onSelect(c)}
                >
                  <span className="candidate-cell">
                    <i className="rank">#{String((c as any).rank || i + 1).padStart(2, "0")}</i>
                    <span className={`tiny-avatar ${c.tone}`}>
                      {c.initials}
                    </span>
                    <strong>{c.name}</strong>
                  </span>
                  <span className="role-cell">{c.role}</span>
                  <span className="location-cell">
                    <MapPin size={14} />
                    {c.location}
                  </span>
                  <span className="match-cell">
                    <b>{c.score}</b>
                    <span className="score-bar">
                      <i style={{ width: `${c.score}%` }} />
                    </span>
                  </span>
                  <span className="verified-badge">
                    <Check size={12} /> Verified
                  </span>
                  <ArrowRight className="row-arrow" size={16} />
                </button>
              ))
            )}
          </div>
          <div className="table-footer flex items-center justify-between" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8' }}>
              Showing candidates {((page - 1) * 50) + 1} – {Math.min(page * 50, stats.total_ranked)} of {(stats.total_ranked || 100000).toLocaleString()} ranked
            </span>
            <div className="flex items-center gap-3" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <button
                disabled={page <= 1}
                onClick={() => onPageChange(page - 1)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  background: page <= 1 ? 'rgba(255,255,255,0.03)' : 'rgba(0, 242, 254, 0.15)',
                  color: page <= 1 ? '#555' : '#00f2fe',
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                  cursor: page <= 1 ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <ArrowLeft size={14} /> Previous 50
              </button>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>
                Page {page} of {totalPages || 1}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => onPageChange(page + 1)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '6px',
                  background: page >= totalPages ? 'rgba(255,255,255,0.03)' : 'rgba(0, 242, 254, 0.15)',
                  color: page >= totalPages ? '#555' : '#00f2fe',
                  border: '1px solid rgba(0, 242, 254, 0.3)',
                  cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                Next 50 <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
function FilterBlock({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="filter-block">
      <h3>{title}</h3>
      <div className="filter-options">{children}</div>
    </div>
  );
}
function Metric({
  label,
  value,
  change,
}: {
  label: string;
  value: string;
  change: string;
}) {
  return (
    <div className="metric">
      <span className="micro-label">{label}</span>
      <div>
        <b>{value}</b>
        <em>{change}</em>
      </div>
    </div>
  );
}

function DeepDive({
  candidate,
  onBack,
}: {
  candidate: Candidate;
  onBack: () => void;
}) {
  return (
    <main className="workspace min-h-screen">
      <WorkspaceHeader step="03 / DEEP DIVE" onBack={onBack} />
      <section className="deepdive-content">
        <div className="deep-top">
          <button className="back-button" onClick={onBack}>
            <ArrowLeft size={16} /> Back to pipeline
          </button>
          <div className="deep-meta">
            <span className="verified-badge">
              <Check size={12} /> Profile verified
            </span>
            <span className="micro-label">
              ID: RS-{candidate.id.toString().padStart(4, "0")}
            </span>
          </div>
        </div>
        <div className="candidate-hero">
          <div className="candidate-identity">
            <span className={`hero-avatar ${candidate.tone}`}>
              {candidate.initials}
            </span>
            <div>
              <div className="section-kicker">
                <StatusDot /> TOP MATCH / RANK 01
              </div>
              <h1>{candidate.name}</h1>
              <p>{candidate.headline}</p>
              <div className="identity-meta">
                <span>
                  <UserRound size={14} />
                  {candidate.role}
                </span>
                <span>
                  <MapPin size={14} />
                  {candidate.location}
                </span>
                <span>
                  <Clock3 size={14} />
                  {candidate.experience} years experience
                </span>
              </div>
            </div>
          </div>
          <div className="score-panel">
            <span className="micro-label">NORMALIZED FIT SCORE</span>
            <div className="huge-score">
              {candidate.score}
              <small>/100</small>
            </div>
            <div className="raw-score">
              RAW SCORE <b>{candidate.raw}</b>
              <span>↗</span>
            </div>
          </div>
        </div>
        <div className="deep-grid">
          <div className="deep-main">
            <section className="analysis-card">
              <div className="card-topline">
                <div className="section-kicker">
                  <Sparkles size={14} /> AI RECRUITER FIT ANALYSIS
                </div>
                <span className="micro-label">CONFIDENCE: HIGH</span>
              </div>
              <p>{candidate.fit}</p>
              <div className="analysis-tags">
                <span>
                  <Check size={13} /> Skills aligned
                </span>
                <span>
                  <Check size={13} /> Seniority aligned
                </span>
                <span>
                  <Check size={13} /> Domain relevant
                </span>
              </div>
            </section>
            
            <section className="timeline-section">
              <div className="section-title">
                <div>
                  <div className="section-kicker">
                    <Clock3 size={14} /> PROFESSIONAL TIMELINE
                  </div>
                  <h2>Career journey</h2>
                </div>
                <span className="micro-label">
                  {candidate.timeline.length} EVENTS
                </span>
              </div>
              <div className="timeline">
                {candidate.timeline.map((t) => (
                  <div className="timeline-item" key={t.company}>
                    <div className="timeline-line">
                      <span />
                    </div>
                    <div>
                      <div className="timeline-meta">
                        <b>{t.company}</b>
                        <span>{t.period}</span>
                      </div>
                      <h3>{t.title}</h3>
                      <p>{t.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <aside className="deep-aside">
            <section className="signals-section">
              <div className="section-title">
                <div>
                  <div className="section-kicker">
                    <Globe2 size={14} /> PLATFORM AVAILABILITY ENVELOPE
                  </div>
                  <h2>Verified signals</h2>
                </div>
                <span className="micro-label">LIVE / ENCRYPTED</span>
              </div>
              <div className="signal-grid">
                {candidate.signals.map((s) => (
                  <div className={`signal-card ${s.type}`} key={s.label}>
                    <span className="signal-status">
                      <StatusDot />
                      {s.type === "good"
                        ? "VERIFIED"
                        : s.type === "warn"
                          ? "ATTENTION"
                          : "AVAILABLE"}
                    </span>
                    <b>{s.value}</b>
                    <span>{s.label}</span>
                  </div>
                ))}
              </div>
            </section>
            <section className="skills-card">
              <div className="section-kicker">
                <BarChart3 size={14} /> SKILL SET MATRIX
              </div>
              <h2>Technical proficiency</h2>
              
              <div style={{display:'flex', justifyContent:'flex-end', gap:'12px', fontSize:'11px', marginBottom:'16px', color:'#7d899c', marginTop:'8px'}}>
                 <span style={{display:'flex', alignItems:'center', gap:'4px'}}><i style={{width:'8px', height:'8px', backgroundColor:'#126c7c', display:'inline-block'}}></i> Intermediate</span>
                 <span style={{display:'flex', alignItems:'center', gap:'4px'}}><i style={{width:'8px', height:'8px', backgroundColor:'#12d9e8', display:'inline-block'}}></i> Advanced</span>
                 <span style={{display:'flex', alignItems:'center', gap:'4px'}}><i style={{width:'8px', height:'8px', backgroundColor:'#5ce7dc', display:'inline-block'}}></i> Expert</span>
              </div>
              <div className="skills-list">

                {candidate.skills.map((s) => (
                  <div className="skill-row" key={s.name}>
                    <div>
                      <span>{s.name}</span>
                      <em>{s.level}</em>
                    </div>
                    <div className="skill-track">
                      <i style={{ width: `${s.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </section>
    </main>
  );
}
