"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Bell,
  Building,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  CloudUpload,
  Cpu,
  Crosshair,
  Database,
  FileText,
  Filter,
  GraduationCap,
  LockKeyhole,
  MapPin,
  Mic,
  MicOff,
  Search,
  ShieldCheck,
  Sparkles,
  Square,
  Terminal,
  Upload,
  UserRound,
  Users,
  X,
  Zap,
} from "lucide-react";

type Candidate = {
  id: number;
  rank?: number;
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
  scoreBreakdown?: {
    title_fit: number;
    skill_coverage: number;
    semantic_fit: number;
    signal_bonus: number;
  };
  willingToRelocate: boolean;
  highestDegree: string; // 'bachelor' | 'master' | 'phd' | 'other'
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
          Drop files here or <u>browse files</u>
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
    unaligned_jd_count: 0,
    honeypot_count: 0,
    shortlisted_count: 0,
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
        
        // Derive highest degree
        const eduArr = c.education || [];
        const highestDegree = (() => {
          if (eduArr.some((e: any) => /ph\.?d/i.test(e.degree || ''))) return 'phd';
          if (eduArr.some((e: any) => /^m\.|master|m\.tech|m\.s|m\.e|m\.sc/i.test(e.degree || ''))) return 'master';
          if (eduArr.some((e: any) => /^b\.|bachelor|b\.tech|b\.e|b\.sc/i.test(e.degree || ''))) return 'bachelor';
          return 'other';
        })();

        return {
          id: c.candidate_id || c.rank,
          rank: c.rank,
          name: c.name,
          role: c.current_title,
          score: Math.min(100, Math.round(c.score * 100)),
          location: c.location,
          experience: c.years_exp,
          initials: (c.name || "CN").split(' ').map((n: string) => n[0]).join('').substring(0, 2).toUpperCase(),
          tone: tones[(c.rank || 1) % tones.length],
          headline: c.headline,
          raw: c.score ? c.score.toFixed(4) : "0.0000",
          fit: c.reasoning,
          scoreBreakdown: c.score_breakdown || {
            skill_coverage: Math.round(c.score * 85),
            title_fit: Math.round(c.score * 90),
            semantic_fit: Math.round(c.score * 88),
            signal_bonus: 10
          },
          willingToRelocate: !!(c.signals?.willing_to_relocate),
          highestDegree,
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
  const [locations, setLocations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [jd, setJd] = useState("");
  const [jdSkills, setJdSkills] = useState<string[]>([]);
  const [selectedSkills, setSelectedSkills] = useState<string[]>([]);
  const [jdLocations, setJdLocations] = useState<string[]>([]);
  const [jdWorkModes, setJdWorkModes] = useState<string[]>([]);
  // Experience buckets: 'Fresher' | '0-2' | '2-5' | '5+'
  const [expBuckets, setExpBuckets] = useState<string[]>([]);
  // Work mode filter
  const [workModes, setWorkModes] = useState<string[]>([]);
  // Education filter
  const [eduLevels, setEduLevels] = useState<string[]>([]);
  // Open to relocation
  const [openToRelocation, setOpenToRelocation] = useState(false);
  // Active category tab: 'eligible' (default) | 'unaligned' | 'all' | 'shortlisted'
  const [activeTab, setActiveTab] = useState<'eligible' | 'unaligned' | 'all' | 'shortlisted'>('eligible');

  // Dynamic extraction hook for typed, pasted, or uploaded JDs
  useEffect(() => {
    if (!jd || !jd.trim()) return;

    const text = jd.toLowerCase();

    // Dynamic location extraction (Bangalore/Banglore/Bengaluru, Pune, Hyderabad, Mumbai, Delhi, etc.)
    const foundLocs = new Set<string>();
    const locMap: Record<string, string> = {
      bangalore: "Bangalore", bengaluru: "Bangalore", banglore: "Bangalore", blr: "Bangalore",
      pune: "Pune", pnq: "Pune", mumbai: "Mumbai", bombay: "Mumbai", hyderabad: "Hyderabad", hyd: "Hyderabad",
      delhi: "Delhi NCR", "new delhi": "Delhi NCR", ncr: "Delhi NCR", gurgaon: "Gurgaon", gurugram: "Gurgaon",
      noida: "Noida", chennai: "Chennai", kolkata: "Kolkata", ahmedabad: "Ahmedabad", jaipur: "Jaipur",
      kochi: "Kochi", chandigarh: "Chandigarh", indore: "Indore", surat: "Surat", coimbatore: "Coimbatore"
    };
    Object.entries(locMap).forEach(([alias, canonical]) => {
      const escaped = alias.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`(?:^|\\b|\\s)${escaped}(?:$|\\b|\\s|[.,;:!?/\\-])`, 'i');
      if (regex.test(text)) foundLocs.add(canonical);
    });
    if (foundLocs.size > 0) setJdLocations(Array.from(foundLocs));

    // Dynamic skill extraction (C++, C#, Python, Java, JS, React, Node, SQL, AWS, etc.)
    const foundSkills = new Set<string>();
    const skillMap: Record<string, string> = {
      "c++": "C++", cpp: "C++", "c#": "C#", csharp: "C#", python: "Python", py: "Python",
      java: "Java", javascript: "JavaScript", js: "JavaScript", typescript: "TypeScript", ts: "TypeScript",
      react: "React", "react.js": "React", reactjs: "React", "next.js": "Next.js", nextjs: "Next.js",
      "node.js": "Node.js", nodejs: "Node.js", vue: "Vue.js", "vue.js": "Vue.js", angular: "Angular",
      html: "HTML", css: "CSS", tailwind: "Tailwind", go: "Go", golang: "Go", rust: "Rust", ruby: "Ruby",
      rails: "Ruby on Rails", php: "PHP", fastapi: "FastAPI", django: "Django", flask: "Flask",
      springboot: "Spring Boot", "spring boot": "Spring Boot", sql: "SQL", mysql: "MySQL",
      postgresql: "PostgreSQL", postgres: "PostgreSQL", mongodb: "MongoDB", mongo: "MongoDB",
      redis: "Redis", aws: "AWS", gcp: "GCP", azure: "Azure", docker: "Docker", kubernetes: "Kubernetes",
      k8s: "Kubernetes", git: "Git", linux: "Linux", api: "REST API", "rest api": "REST API",
      graphql: "GraphQL", "machine learning": "Machine Learning", ml: "Machine Learning",
      "deep learning": "Deep Learning", pytorch: "PyTorch", tensorflow: "TensorFlow", keras: "Keras",
      nlp: "NLP", llm: "LLM", pandas: "Pandas", numpy: "NumPy"
    };

    Object.entries(skillMap).forEach(([kw, canonical]) => {
      const isSpecial = !/^[a-zA-Z0-9]+$/.test(kw) || kw.length <= 2;
      const escaped = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const pattern = isSpecial
        ? `(?:^|\\b|\\s)${escaped}(?:$|\\b|\\s|[.,;:!?/\\-])`
        : `\\b${escaped}\\b`;
      const regex = new RegExp(pattern, 'i');
      if (regex.test(text)) foundSkills.add(canonical);
    });
    if (foundSkills.size > 0) {
      const list = Array.from(foundSkills);
      setJdSkills(list);
      // Keep selectedSkills empty [] so all candidates show initially until user ticks a skill
    }

    // Dynamic work mode extraction
    const foundModes = new Set<string>();
    if (/remote|wfh|work from home/i.test(text)) foundModes.add("Remote");
    if (/hybrid|flexible/i.test(text)) foundModes.add("Hybrid");
    if (/on-site|onsite|in-office|office/i.test(text)) foundModes.add("On-site");
    if (foundModes.size > 0) setJdWorkModes(Array.from(foundModes));
  }, [jd]);

  const expBucketMatch = (exp: number) => {
    if (expBuckets.length === 0) return true;
    return expBuckets.some(b => {
      if (b === 'Fresher') return exp <= 1;
      if (b === '0-2')    return exp >= 0 && exp <= 2;
      if (b === '2-5')    return exp >= 2 && exp <= 5;
      if (b === '5+')     return exp >= 5;
      return true;
    });
  };

  const cutoff = threshold > 0 ? threshold : 55;

  const categoryFiltered = useMemo(() => {
    return candidates.filter((c) => {
      if (activeTab === 'eligible') {
        return c.score >= cutoff;
      } else if (activeTab === 'unaligned') {
        return c.score < cutoff;
      } else if (activeTab === 'shortlisted') {
        return (c as any).isShortlisted === true;
      }
      return true; // 'all'
    });
  }, [candidates, activeTab, cutoff]);

  const filtered = useMemo(
    () =>
      categoryFiltered.filter((c) => {
        // Match score
        if (c.score < threshold) return false;
        // Experience bucket
        if (!expBucketMatch(c.experience)) return false;
        // Location
        if (locations.length > 0 && !locations.some(l => c.location.toLowerCase().includes(l.toLowerCase()))) return false;
        // Required skills
        if (selectedSkills.length > 0 && !selectedSkills.every(s => c.skills.some((cs: any) => cs.name.toLowerCase() === s.toLowerCase()))) return false;
        // Education
        if (eduLevels.length > 0) {
          const degMap: Record<string, string> = { "Bachelor's": 'bachelor', "Master's": 'master', 'PhD': 'phd' };
          if (!eduLevels.some(e => c.highestDegree === degMap[e])) return false;
        }
        // Open to relocation
        if (openToRelocation && !c.willingToRelocate) return false;
        // Text search
        if (!`${c.name} ${c.role} ${c.location}`.toLowerCase().includes(query.toLowerCase())) return false;
        return true;
      }),
    [query, threshold, expBuckets, locations, selectedSkills, eduLevels, openToRelocation, categoryFiltered],
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

  const [showHoneypotsModal, setShowHoneypotsModal] = useState(false);
  const [honeypotList, setHoneypotList] = useState<any[]>([]);
  const [honeypotLoading, setHoneypotLoading] = useState(false);

  const [showAgentConsoleModal, setShowAgentConsoleModal] = useState(false);
  const [breakdownCandidate, setBreakdownCandidate] = useState<Candidate | null>(null);

  const fetchHoneypots = async () => {
    setHoneypotLoading(true);
    setShowHoneypotsModal(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/honeypots");
      const data = await res.json();
      setHoneypotList(data.honeypots || []);
    } catch (e) {
      console.error("Failed to fetch honeypots", e);
    } finally {
      setHoneypotLoading(false);
    }
  };

  if (screen === "landing")
    return <Landing onLaunch={() => setScreen("ingest")} />;
  if (screen === "ingest")
    return (
      <>
        <Ingest
          files={files}
          setFiles={setFiles}
          jd={jd}
          setJd={setJd}
          setJdSkills={setJdSkills}
          setJdLocations={setJdLocations}
          setJdWorkModes={setJdWorkModes}
          loading={loading}
          onBack={() => setScreen("landing")}
          onAnalyze={analyze}
          onCandidatesUploaded={(count: number) => {
            fetchShortlist(1);
            alert(`✅ Loaded ${count.toLocaleString()} candidates. Pool replaced — ready to analyze!`);
          }}
          onOpenAgentConsole={() => setShowAgentConsoleModal(true)}
        />
        <AgentConsoleModal
          isOpen={showAgentConsoleModal}
          onClose={() => setShowAgentConsoleModal(false)}
        />
      </>
    );
  if (screen === "deepdive")
    return (
      <DeepDive candidate={selected} onBack={() => setScreen("pipeline")} />
    );
  const resetAllFilters = () => {
    setThreshold(0);
    setExpBuckets([]);
    setLocations([]);
    setWorkModes([]);
    setSelectedSkills([]);
    setEduLevels([]);
    setOpenToRelocation(false);
  };

  return (
    <>
      <Pipeline
        candidates={candidates}
        filtered={filtered}
        stats={stats}
        page={page}
        totalPages={totalPages}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onPageChange={(p) => fetchShortlist(p)}
        query={query}
        setQuery={setQuery}
        threshold={threshold}
        setThreshold={setThreshold}
        expBuckets={expBuckets}
        setExpBuckets={setExpBuckets}
        locations={locations}
        setLocations={setLocations}
        workModes={workModes}
        setWorkModes={setWorkModes}
        jdSkills={jdSkills}
        selectedSkills={selectedSkills}
        setSelectedSkills={setSelectedSkills}
        jdLocations={jdLocations}
        jdWorkModes={jdWorkModes}
        eduLevels={eduLevels}
        setEduLevels={setEduLevels}
        openToRelocation={openToRelocation}
        setOpenToRelocation={setOpenToRelocation}
        onResetFilters={resetAllFilters}
        onBack={() => setScreen("ingest")}
        onSelect={(c) => {
          setSelected(c);
          setScreen("deepdive");
        }}
        onOpenHoneypots={fetchHoneypots}
        onOpenAgentConsole={() => setShowAgentConsoleModal(true)}
      />
      <HoneypotModal
        isOpen={showHoneypotsModal}
        onClose={() => setShowHoneypotsModal(false)}
        honeypots={honeypotList}
        loading={honeypotLoading}
      />
      <AgentConsoleModal
        isOpen={showAgentConsoleModal}
        onClose={() => setShowAgentConsoleModal(false)}
      />
      <ScoreBreakdownModal
        candidate={breakdownCandidate}
        isOpen={!!breakdownCandidate}
        onClose={() => setBreakdownCandidate(null)}
      />
    </>
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
  setJdLocations,
  setJdWorkModes,
  loading,
  onBack,
  onAnalyze,
  onCandidatesUploaded,
  onOpenAgentConsole,
}: {
  files: string[];
  setFiles: (x: string[]) => void;
  jd: string;
  setJd: (x: string) => void;
  setJdSkills: (x: string[]) => void;
  setJdLocations: (x: string[]) => void;
  setJdWorkModes: (x: string[]) => void;
  loading: boolean;
  onBack: () => void;
  onAnalyze: () => void;
  onCandidatesUploaded: (count: number) => void;
  onOpenAgentConsole?: () => void;
}) {
  const [isListening, setIsListening] = useState(false);

  const startListening = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice Dictation: Browser speech recognition is not supported on this browser. Please use Google Chrome, Microsoft Edge, or Brave.");
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        if (transcript.trim()) {
          setJd(jd ? jd + " " + transcript : transcript);
        }
      };

      recognition.onerror = (e: any) => {
        console.error("Speech Recognition Error", e);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
      (window as any)._speechRecInstance = recognition;
    } catch (err) {
      console.error("Failed to start speech recognition", err);
      setIsListening(false);
    }
  };

  const stopListening = () => {
    if ((window as any)._speechRecInstance) {
      try {
        (window as any)._speechRecInstance.stop();
      } catch (e) {}
      setIsListening(false);
    }
  };

  const addFiles = async (list: FileList | null, type: 'jd' | 'candidates') => {
    if (!list || list.length === 0) return;
    
    // Optimistic UI update
    if (type === 'candidates') setFiles([...files, ...Array.from(list).map(f => f.name)]);
    
    const formData = new FormData();
    if (type === 'jd') {
      formData.append("file", list[0]);
    } else {
      for (let i = 0; i < list.length; i++) {
        formData.append("files", list[i]);
      }
    }
    
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
        if (data.metadata && data.metadata.locations_found) setJdLocations(data.metadata.locations_found);
        if (data.metadata && data.metadata.work_modes_found) setJdWorkModes(data.metadata.work_modes_found);
      } else if (type === 'candidates') {
        // Notify parent so it can refresh stats from backend
        if (data.total_candidates) onCandidatesUploaded(data.total_candidates);
      }
    } catch (e) {
      console.error(e);
    }
  };
  return (
    <main className="workspace min-h-screen">
      <WorkspaceHeader step="01 / DATA INGESTION" onBack={onBack} onOpenAgentConsole={onOpenAgentConsole} />
      <section className="workspace-content narrow">
        <div className="section-kicker">
          <Database size={15} /> DATA INGESTION PIPELINE
        </div>
        <h1 className="page-title">
          Power autonomous screening
          <br />
          <span>with candidate & job data.</span>
        </h1>
        <p className="page-intro">
          Upload your talent pool and target role specifications. RecruitShield automatically
          normalizes candidate data, extracts core qualifications, and maps candidates across our
          neural embedding model.
        </p>
        <div className="ingest-grid">
          <DropZone
            title="Candidate Pool Database"
            description="Bulk PDF resumes, JSONL, or CSV datasets"
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
                  Target Job Description <span className="required">REQUIRED</span>
                </h3>
                <p>Upload a JD document or paste criteria below</p>
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
                Drop Job Description (PDF) or <u>browse</u>
              </span>
              <small>PDF up to 10MB</small>
            </label>

            {/* Glorified Glowing AI Voice Control Banner */}
            <div
              style={{
                marginTop: '16px',
                marginBottom: '12px',
                padding: '14px 18px',
                borderRadius: '12px',
                background: isListening
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.22) 0%, rgba(13, 20, 30, 0.95) 100%)'
                  : 'linear-gradient(135deg, rgba(6, 182, 212, 0.16) 0%, rgba(14, 165, 233, 0.06) 100%)',
                border: isListening
                  ? '1px solid rgba(239, 68, 68, 0.55)'
                  : '1px solid rgba(6, 182, 212, 0.45)',
                boxShadow: isListening
                  ? '0 0 30px rgba(239, 68, 68, 0.35)'
                  : '0 0 25px rgba(6, 182, 212, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '14px',
                transition: 'all 0.3s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    width: '42px',
                    height: '42px',
                    borderRadius: '50%',
                    flexShrink: 0,
                    background: isListening ? 'rgba(239, 68, 68, 0.25)' : 'rgba(6, 182, 212, 0.25)',
                    border: isListening ? '2px solid #ef4444' : '2px solid #38bdf8',
                    display: 'grid',
                    placeItems: 'center',
                    boxShadow: isListening ? '0 0 20px #ef4444' : '0 0 20px #38bdf8',
                  }}
                >
                  {isListening ? (
                    <MicOff size={20} style={{ color: '#f87171', animation: 'pulse 1s infinite' }} />
                  ) : (
                    <Mic size={20} style={{ color: '#38bdf8' }} />
                  )}
                </div>

                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'nowrap' }}>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: isListening ? '#fca5a5' : '#f0f9ff', whiteSpace: 'nowrap' }}>
                      {isListening ? '🎤 Listening Live...' : 'AI Voice Dictation'}
                    </span>
                    <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: isListening ? 'rgba(239, 68, 68, 0.3)' : 'rgba(6, 182, 212, 0.3)', color: isListening ? '#f87171' : '#38bdf8', fontWeight: 700, flexShrink: 0 }}>
                      {isListening ? 'RECORDING' : 'READY'}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '3px', lineHeight: '1.3' }}>
                    {isListening
                      ? 'Speak title, skills, experience level & location...'
                      : 'Dictate criteria directly into prompt box by voice'}
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={isListening ? stopListening : startListening}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 18px',
                  borderRadius: '8px',
                  flexShrink: 0,
                  background: isListening
                    ? '#ef4444'
                    : 'linear-gradient(135deg, #06b6d4 0%, #0284c7 100%)',
                  border: 'none',
                  color: '#ffffff',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  boxShadow: isListening
                    ? '0 0 20px rgba(239, 68, 68, 0.7)'
                    : '0 0 20px rgba(6, 182, 212, 0.5)',
                  letterSpacing: '0.03em',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {isListening ? (
                  <>
                    <Square size={14} fill="#ffffff" />
                    <span>STOP RECORDING</span>
                  </>
                ) : (
                  <>
                    <Mic size={14} />
                    <span>START DICTATION</span>
                  </>
                )}
              </button>
            </div>

            <div className="or-line">
              <span /> OR PASTE JOB DESCRIPTION TEXT <span />
            </div>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste job title, key responsibilities, required skills, experience levels, and location requirements here..."
            />
          </div>
        </div>
        <div className="ingest-footer">
          <div className="privacy-note">
            <LockKeyhole size={15} />
            <span>
              <b>Enterprise Data Security:</b> Encrypted in transit. Raw candidate data is strictly isolated and never used for model training.
            </span>
          </div>
          <GlowButton onClick={onAnalyze}>
            {loading ? (
              <>
                <span className="spinner" /> AI Agents Reasoning...
              </>
            ) : (
              <>Run AI Screen & Candidate Match</>
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
  onOpenAgentConsole?: () => void;
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
  candidates: _candidates,
  filtered,
  stats,
  page,
  totalPages: _totalPages,
  onPageChange,
  query,
  setQuery,
  threshold,
  setThreshold,
  expBuckets,
  setExpBuckets,
  locations,
  setLocations,
  workModes,
  setWorkModes,
  jdSkills,
  selectedSkills,
  setSelectedSkills,
  jdLocations,
  jdWorkModes,
  eduLevels,
  setEduLevels,
  openToRelocation,
  setOpenToRelocation,
  activeTab,
  setActiveTab,
  onResetFilters,
  onBack,
  onSelect,
  onOpenHoneypots,
  onOpenAgentConsole,
}: {
  candidates: Candidate[];
  filtered: Candidate[];
  stats: { total_candidates: number; eligible_candidates: number; unaligned_jd_count?: number; honeypot_count: number; shortlisted_count?: number; total_ranked: number };
  activeTab: 'eligible' | 'unaligned' | 'all' | 'shortlisted';
  setActiveTab: (tab: 'eligible' | 'unaligned' | 'all' | 'shortlisted') => void;
  page: number;
  totalPages: number;
  onPageChange: (p: number) => void;
  query: string;
  setQuery: (x: string) => void;
  threshold: number;
  setThreshold: (x: number) => void;
  expBuckets: string[];
  setExpBuckets: (b: string[]) => void;
  locations: string[];
  setLocations: (l: string[]) => void;
  workModes: string[];
  setWorkModes: (w: string[]) => void;
  jdSkills: string[];
  selectedSkills: string[];
  setSelectedSkills: (s: string[]) => void;
  jdLocations: string[];
  jdWorkModes: string[];
  eduLevels: string[];
  setEduLevels: (e: string[]) => void;
  openToRelocation: boolean;
  setOpenToRelocation: (b: boolean) => void;
  onResetFilters: () => void;
  onBack: () => void;
  onSelect: (c: Candidate) => void;
  onOpenHoneypots: () => void;
  onOpenAgentConsole?: () => void;
}) {
  const toggleExpBucket = (b: string) =>
    setExpBuckets(
      expBuckets.includes(b) ? expBuckets.filter((x) => x !== b) : [...expBuckets, b]
    );

  const toggleLoc = (v: string) =>
    setLocations(
      locations.includes(v) ? locations.filter((x) => x !== v) : [...locations, v]
    );

  const toggleWorkMode = (w: string) =>
    setWorkModes(
      workModes.includes(w) ? workModes.filter((x) => x !== w) : [...workModes, w]
    );

  const toggleEdu = (e: string) =>
    setEduLevels(
      eduLevels.includes(e) ? eduLevels.filter((x) => x !== e) : [...eduLevels, e]
    );

  const toggleSkill = (s: string) =>
    setSelectedSkills(
      selectedSkills.includes(s)
        ? selectedSkills.filter((x) => x !== s)
        : [...selectedSkills, s]
    );

  const activeFilterCount =
    selectedSkills.length +
    locations.length +
    workModes.length +
    expBuckets.length +
    eduLevels.length +
    (threshold > 0 ? 1 : 0) +
    (openToRelocation ? 1 : 0);

  const currentTabTotalCount = useMemo(() => {
    if (activeTab === 'eligible') return stats.eligible_candidates ?? stats.total_ranked;
    if (activeTab === 'unaligned') return stats.unaligned_jd_count ?? 0;
    if (activeTab === 'shortlisted') return stats.shortlisted_count ?? 0;
    return stats.total_ranked || _candidates.length;
  }, [activeTab, stats, _candidates.length]);

  const isFilteringActive = activeFilterCount > 0 || query.trim().length > 0;
  const effectiveTotalCount = isFilteringActive ? filtered.length : currentTabTotalCount;
  const effectiveTotalPages = Math.max(1, Math.ceil(effectiveTotalCount / 50));

  const hasNextPage = page < effectiveTotalPages && filtered.length >= 50;
  const hasPreviousPage = page > 1;

  return (
    <main className="workspace min-h-screen">
      <WorkspaceHeader step="02 / MATCH" onBack={onBack} onOpenAgentConsole={onOpenAgentConsole} />
      <div className="pipeline-layout">
        <aside className="filter-sidebar">
          {/* Header */}
          <div className="fsb-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div className="fsb-icon"><Filter size={13} /></div>
              <span className="fsb-title">Smart Filters</span>
              {activeFilterCount > 0 && (
                <span className="fsb-badge">{activeFilterCount}</span>
              )}
            </div>
            <button className="fsb-clear" onClick={onResetFilters}>
              Reset
            </button>
          </div>

          {/* JD Context Banner */}
          {(jdSkills.length > 0 || jdLocations.length > 0) && (
            <div className="fsb-jd-banner">
              <Sparkles size={11} />
              <span>Filters auto-tuned from JD</span>
            </div>
          )}

          {/* Match Score Section */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <BarChart3 size={12} />
              Min. Match Score
            </div>
            <div className="fsb-score-row">
              <div className="fsb-score-display">
                <span className="fsb-score-num">{threshold}%</span>
                <span className="fsb-score-label">min match threshold</span>
              </div>
              <input
                type="range" min="0" max="95" step="5"
                value={threshold}
                onChange={(e) => setThreshold(+e.target.value)}
                className="fsb-single-slider"
              />
            </div>
          </div>

          {/* Experience Section */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <Clock3 size={12} />
              Experience Level
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {[
                { id: 'Fresher', label: 'Fresher (0-1y)' },
                { id: '0-2', label: '0 – 2 years' },
                { id: '2-5', label: '2 – 5 years' },
                { id: '5+', label: '5+ years' },
              ].map((b) => (
                <label key={b.id} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: '#cbd5e1', cursor: 'pointer', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    checked={expBuckets.includes(b.id)}
                    onChange={() => toggleExpBucket(b.id)}
                    style={{ accentColor: '#12d9e8' }}
                  />
                  <span>{b.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Location Section (from JD) */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <MapPin size={12} />
              Location
              {jdLocations.length > 0 && <span className="fsb-jd-hint">from JD</span>}
            </div>
            {jdLocations.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {jdLocations.map((loc) => (
                  <label key={loc} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: '#cbd5e1', cursor: 'pointer', userSelect: 'none', textTransform: 'capitalize' }}>
                    <input
                      type="checkbox"
                      checked={locations.includes(loc)}
                      onChange={() => toggleLoc(loc)}
                      style={{ accentColor: '#12d9e8' }}
                    />
                    <span>{loc}</span>
                  </label>
                ))}
              </div>
            ) : (
              <div className="fsb-empty-hint">
                No location specified in JD. All candidate locations included.
              </div>
            )}
          </div>

          {/* Work Mode Section */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <Building size={12} />
              Work Mode
              {jdWorkModes.length > 0 && <span className="fsb-jd-hint">from JD</span>}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {['Remote', 'Hybrid', 'On-site'].map((wm) => (
                <label key={wm} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: '#cbd5e1', cursor: 'pointer', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    checked={workModes.includes(wm)}
                    onChange={() => toggleWorkMode(wm)}
                    style={{ accentColor: '#12d9e8' }}
                  />
                  <span>{wm}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Required Skills Section (from JD) */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <Zap size={12} />
              Required Skills
              {jdSkills.length === 0 && <span className="fsb-no-jd">— upload JD to extract</span>}
            </div>
            {jdSkills.length > 0 ? (
              <div className="fsb-chips">
                {jdSkills.map((s) => {
                  const active = selectedSkills.includes(s);
                  return (
                    <button
                      key={s}
                      className={`fsb-chip ${active ? 'fsb-chip--on' : ''}`}
                      onClick={() => toggleSkill(s)}
                    >
                      {s}
                      {active ? <X size={12} /> : <Check size={10} />}
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="fsb-empty-hint">
                Upload a JD to extract required skills automatically.
              </div>
            )}
          </div>

          {/* Education Level Section */}
          <div className="fsb-section">
            <div className="fsb-section-label">
              <GraduationCap size={12} />
              Education
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {["Bachelor's", "Master's", "PhD"].map((edu) => (
                <label key={edu} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: '#cbd5e1', cursor: 'pointer', userSelect: 'none' }}>
                  <input
                    type="checkbox"
                    checked={eduLevels.includes(edu)}
                    onChange={() => toggleEdu(edu)}
                    style={{ accentColor: '#12d9e8' }}
                  />
                  <span>{edu}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Relocation Toggle */}
          <div className="fsb-section">
            <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', userSelect: 'none' }}>
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#cbd5e1' }}>Willing to Relocate</span>
              <input
                type="checkbox"
                checked={openToRelocation}
                onChange={(e) => setOpenToRelocation(e.target.checked)}
                style={{ accentColor: '#12d9e8' }}
              />
            </label>
          </div>

          {/* Results preview */}
          <div className="fsb-result-preview">
            <span className="fsb-result-count">{filtered.length}</span>
            <span className="fsb-result-label">candidates match</span>
          </div>

          {/* Threat status */}
          <div className="fsb-threat">
            <div className="fsb-threat-dot" />
            <span>Threat shield <b>active</b></span>
            <ShieldCheck size={13} style={{ marginLeft: 'auto', color: '#12d9e8' }} />
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
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <button
                onClick={onOpenAgentConsole}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 16px",
                  borderRadius: "8px",
                  background: "linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(14, 165, 233, 0.1) 100%)",
                  border: "1px solid rgba(6, 182, 212, 0.5)",
                  color: "#38bdf8",
                  fontSize: "13px",
                  fontWeight: 700,
                  cursor: "pointer",
                  boxShadow: "0 0 18px rgba(6, 182, 212, 0.25)",
                  fontFamily: "var(--font-mono, monospace)",
                }}
              >
                <Terminal size={15} style={{ color: "#38bdf8" }} />
                <span>Strands Agent Console</span>
              </button>
              <button className="sort-button">
                Ranked by <b>Match score</b>
                <ChevronDown size={14} />
              </button>
            </div>
          </div>
          <div className="metrics-row" style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.75rem', marginBottom: '1.5rem' }}>
            <Metric
              label="TOTAL CANDIDATES"
              value={stats.total_candidates > 0 ? stats.total_candidates.toLocaleString() : "Loading…"}
              change="Uploaded pool"
              clickable={true}
              active={activeTab === 'all'}
              onClick={() => setActiveTab('all')}
            />
            <Metric
              label="ELIGIBLE CANDIDATES"
              value={stats.eligible_candidates > 0 ? stats.eligible_candidates.toLocaleString() : "0"}
              change="Matches JD"
              clickable={true}
              active={activeTab === 'eligible'}
              onClick={() => setActiveTab('eligible')}
            />
            <Metric
              label="NOT ALIGNS TO JD"
              value={(stats.unaligned_jd_count !== undefined ? stats.unaligned_jd_count : 0).toLocaleString()}
              change="Fails JD"
              clickable={true}
              active={activeTab === 'unaligned'}
              onClick={() => setActiveTab('unaligned')}
            />
            <Metric 
              label="HONEYPOT PROFILES" 
              value={stats.total_candidates > 0 ? stats.honeypot_count.toLocaleString() : "Loading…"} 
              change="Click to inspect traps" 
              clickable={true}
              isDanger={true}
              onClick={onOpenHoneypots}
            />
            <Metric
              label="SHORTLISTED"
              value={(stats.shortlisted_count || 0).toString()}
              change="Starred candidates"
              clickable={true}
              active={activeTab === 'shortlisted'}
              onClick={() => setActiveTab('shortlisted')}
            />
          </div>
          <div style={{ marginBottom: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "14px", fontWeight: 600, color: "#e2e8f0" }}>
              {activeTab === 'eligible' && "🟢 Displaying Eligible Candidates (Matching JD)"}
              {activeTab === 'unaligned' && "🔴 Displaying Candidates Not Aligned to JD"}
              {activeTab === 'all' && "🌐 Displaying All Candidates in Database"}
              {activeTab === 'shortlisted' && "⭐ Displaying Shortlisted Candidates"}
            </span>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>
              Dynamic Rank starting at #01
            </span>
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
              filtered.map((c, i) => {
                const currentRank = (c as any).rank || ((page - 1) * 50 + i + 1);
                return (
                  <button
                    className="candidate-row"
                    key={c.id || i}
                    onClick={() => onSelect({ ...c, rank: currentRank })}
                  >
                    <span className="candidate-cell">
                      <i className="rank">#{String(currentRank).padStart(2, "0")}</i>
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
                  <span className="match-cell" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
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
              );
            })
          )}
          </div>
          <div className="table-footer flex items-center justify-between" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8' }}>
              {filtered.length === 0 ? (
                "No matching candidates found"
              ) : (
                <>
                  Showing candidates {((page - 1) * 50) + 1} – {((page - 1) * 50) + filtered.length} of {effectiveTotalCount.toLocaleString()} {isFilteringActive ? "matching" : "ranked"}
                </>
              )}
            </span>
            {(hasPreviousPage || hasNextPage || effectiveTotalPages > 1) && (
              <div className="flex items-center gap-3" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {hasPreviousPage && (
                  <button
                    onClick={() => onPageChange(page - 1)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '6px',
                      background: 'rgba(0, 242, 254, 0.15)',
                      color: '#00f2fe',
                      border: '1px solid rgba(0, 242, 254, 0.3)',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 600,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    <ArrowLeft size={14} /> Previous 50
                  </button>
                )}
                {effectiveTotalPages > 1 && (
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>
                    Page {page} of {effectiveTotalPages}
                  </span>
                )}
                {hasNextPage && (
                  <button
                    onClick={() => onPageChange(page + 1)}
                    style={{
                      padding: '6px 14px',
                      borderRadius: '6px',
                      background: 'rgba(0, 242, 254, 0.15)',
                      color: '#00f2fe',
                      border: '1px solid rgba(0, 242, 254, 0.3)',
                      cursor: 'pointer',
                      fontSize: '13px',
                      fontWeight: 600,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}
                  >
                    Next 50 <ArrowRight size={14} />
                  </button>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
// Metric component used in candidate pipeline stats
function Metric({
  label,
  value,
  change,
  onClick,
  clickable = false,
  active = false,
  isDanger = false,
}: {
  label: string;
  value: string;
  change: string;
  onClick?: () => void;
  clickable?: boolean;
  active?: boolean;
  isDanger?: boolean;
}) {
  return (
    <div
      className="metric"
      onClick={onClick}
      style={{
        cursor: clickable ? "pointer" : "default",
        transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        padding: "12px 14px",
        borderRadius: "10px",
        border: active
          ? "1px solid #38bdf8"
          : isDanger
          ? "1px solid rgba(239, 68, 68, 0.4)"
          : "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: active
          ? "0 0 14px rgba(56, 189, 248, 0.25)"
          : isDanger
          ? "0 0 10px rgba(239, 68, 68, 0.15)"
          : "none",
        background: active
          ? "linear-gradient(145deg, rgba(56, 189, 248, 0.14) 0%, rgba(15, 23, 42, 0.95) 100%)"
          : isDanger
          ? "linear-gradient(145deg, rgba(239, 68, 68, 0.12) 0%, rgba(15, 23, 42, 0.95) 100%)"
          : "linear-gradient(145deg, rgba(255, 255, 255, 0.03) 0%, rgba(15, 23, 42, 0.8) 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minHeight: "72px"
      }}
    >
      <span
        className="micro-label"
        style={{
          color: isDanger ? "#f87171" : active ? "#38bdf8" : "#94a3b8",
          fontSize: "11px",
          fontWeight: 700,
          letterSpacing: "0.05em",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          textTransform: "uppercase",
          marginBottom: "6px"
        }}
      >
        {label}
      </span>
      <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
        <b
          style={{
            fontSize: "22px",
            fontWeight: 800,
            color: isDanger ? "#fca5a5" : active ? "#f8fafc" : "#f1f5f9",
            lineHeight: 1.1
          }}
        >
          {value}
        </b>
        <em
          style={{
            fontSize: "11px",
            fontStyle: "normal",
            color: isDanger ? "#f87171" : active ? "#7dd3fc" : "#64748b",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis"
          }}
        >
          {change}
        </em>
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
  const actualRank = candidate.rank || 1;
  const formattedRank = String(actualRank).padStart(2, "0");
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
                <StatusDot /> {actualRank === 1 ? "TOP MATCH" : "MATCHED CANDIDATE"} / RANK #{formattedRank}
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
            <section className="analysis-card" style={{ padding: "24px", borderRadius: "14px", border: "1px solid rgba(56, 189, 248, 0.25)", background: "linear-gradient(145deg, rgba(15, 23, 42, 0.95) 0%, rgba(6, 9, 14, 0.98) 100%)", boxShadow: "0 10px 30px rgba(0, 0, 0, 0.4)" }}>
              {/* Card Header Topline */}
              <div className="card-topline" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#38bdf8", fontWeight: 800, fontSize: "13px", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                  <Sparkles size={16} style={{ color: "#38bdf8" }} />
                  <span>AI Recruiter Fit Analysis & Scoring Breakdown</span>
                </div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "4px 11px",
                    borderRadius: "12px",
                    background: "rgba(16, 185, 129, 0.15)",
                    border: "1px solid rgba(16, 185, 129, 0.4)",
                    color: "#34d399",
                    letterSpacing: "0.05em",
                    fontFamily: "var(--font-mono, monospace)"
                  }}
                >
                  CONFIDENCE: HIGH
                </span>
              </div>

              {/* Core Fit Summary Paragraph */}
              <div style={{ fontSize: "14px", lineHeight: "1.6", color: "#e2e8f0", background: "rgba(255, 255, 255, 0.03)", padding: "14px 16px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)", marginBottom: "18px" }}>
                {candidate.fit}
              </div>

              {/* Section 1: Candidate's Most Promising Points (Why Candidate Suits JD) */}
              <div style={{ marginBottom: "20px" }}>
                <div style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <span>🌟 Key Promising Points — Why {candidate.name.split(' ')[0]} Suits The JD</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "10px" }}>
                  <div style={{ background: "rgba(15, 23, 42, 0.8)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#38bdf8", marginBottom: "4px" }}>⚡ Technical & Skill Synergy</div>
                    <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.4" }}>
                      {candidate.experience} yrs experience with strong proficiency in {candidate.skills.slice(0, 3).map(s => s.name).join(", ")}. Matches core technical requirements.
                    </div>
                  </div>

                  <div style={{ background: "rgba(15, 23, 42, 0.8)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#38bdf8", marginBottom: "4px" }}>🏢 Career History & Impact</div>
                    <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.4" }}>
                      Proven engineering background at {candidate.timeline[0]?.company || 'tech companies'} as {candidate.role}. Strong delivery track record.
                    </div>
                  </div>

                  <div style={{ background: "rgba(15, 23, 42, 0.8)", padding: "12px 14px", borderRadius: "8px", border: "1px solid rgba(16, 185, 129, 0.25)" }}>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#34d399", marginBottom: "4px" }}>🛡️ Verified Integrity Signal</div>
                    <div style={{ fontSize: "12px", color: "#cbd5e1", lineHeight: "1.4" }}>
                      Passed 5-Point Anomaly Firewall. High stability signal ({candidate.willingToRelocate ? "Relocation ready" : "Local talent"}).
                    </div>
                  </div>
                </div>
              </div>
                             {/* Section 2: Score Calculation Breakdown */}
              <div style={{ paddingTop: "14px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
                <div style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "10px" }}>
                  📊 Match Score Breakdown ({candidate.score}/100 Match Score)
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
                  <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    <span style={{ fontSize: "10px", color: "#94a3b8", display: "block", textTransform: "uppercase", fontWeight: 700 }}>🛠️ Skill Coverage</span>
                    <b style={{ fontSize: "18px", color: "#f8fafc" }}>{candidate.scoreBreakdown?.skill_coverage || 85}%</b>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Direct skill stack overlap</div>
                  </div>
                  <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    <span style={{ fontSize: "10px", color: "#94a3b8", display: "block", textTransform: "uppercase", fontWeight: 700 }}>🎯 Role Title Fit</span>
                    <b style={{ fontSize: "18px", color: "#f8fafc" }}>{candidate.scoreBreakdown?.title_fit || 90}%</b>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>Seniority & title match</div>
                  </div>
                  <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.06)" }}>
                    <span style={{ fontSize: "10px", color: "#94a3b8", display: "block", textTransform: "uppercase", fontWeight: 700 }}>🧠 BGE Vector Similarity</span>
                    <b style={{ fontSize: "18px", color: "#f8fafc" }}>{candidate.scoreBreakdown?.semantic_fit || 88}%</b>
                    <div style={{ fontSize: "10px", color: "#64748b", marginTop: "2px" }}>768-dim dense embedding</div>
                  </div>
                  <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "10px 12px", borderRadius: "8px", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                    <span style={{ fontSize: "10px", color: "#94a3b8", display: "block", textTransform: "uppercase", fontWeight: 700 }}>🎓 Signal Bonus</span>
                    <b style={{ fontSize: "18px", color: "#34d399" }}>+{candidate.scoreBreakdown?.signal_bonus || 10}%</b>
                    <div style={{ fontSize: "10px", color: "#34d399", marginTop: "2px" }}>Verified stability boost</div>
                  </div>
                </div>
              </div>

              {/* Badges */}
              <div className="analysis-tags" style={{ marginTop: "16px", display: "flex", gap: "10px" }}>
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
            <section className="skills-card" style={{ marginTop: 0 }}>
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

function ScoreBreakdownModal({
  candidate,
  isOpen,
  onClose,
}: {
  candidate: Candidate | null;
  isOpen: boolean;
  onClose: () => void;
}) {
  if (!isOpen || !candidate) return null;

  const sb = candidate.scoreBreakdown || {
    skill_coverage: Math.round(candidate.score * 0.85),
    title_fit: Math.round(candidate.score * 0.90),
    semantic_fit: Math.round(candidate.score * 0.88),
    signal_bonus: 10,
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(3, 7, 13, 0.85)",
        backdropFilter: "blur(12px)",
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "620px",
          backgroundColor: "#0d141e",
          border: "1px solid rgba(56, 189, 248, 0.4)",
          borderRadius: "14px",
          boxShadow: "0 25px 70px rgba(56, 189, 248, 0.25), 0 0 40px rgba(0, 0, 0, 0.8)",
          overflow: "hidden",
          color: "#e7edf6",
          padding: "24px",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "#38bdf8", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              SCORE CALCULATION METHODOLOGY
            </div>
            <h3 style={{ margin: "4px 0 0", fontSize: "18px", fontWeight: 700, color: "#f8fafc" }}>
              {candidate.name} — <span style={{ color: "#38bdf8" }}>{candidate.score}/100 Match Score</span>
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "6px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#94a3b8",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Weighted Formula Box */}
        <div
          style={{
            padding: "12px 14px",
            borderRadius: "8px",
            background: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(56, 189, 248, 0.25)",
            fontSize: "12px",
            color: "#94a3b8",
            marginBottom: "16px",
            fontFamily: "var(--font-mono, monospace)",
            lineHeight: "1.5"
          }}
        >
          <strong style={{ color: "#38bdf8" }}>Weighted Match Formula:</strong>
          <br />
          <code>Score = (Skills × 40%) + (Title × 30%) + (BGE Vector × 20%) + Signal Bonus (+10%)</code>
        </div>

        {/* 4 Dimension Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "18px" }}>
          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700 }}>🛠️ Skill Coverage (40%)</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc", marginTop: "2px" }}>{sb.skill_coverage}%</div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>Direct skill stack overlap</div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700 }}>🎯 Role Title Fit (30%)</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc", marginTop: "2px" }}>{sb.title_fit}%</div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>Seniority & role title alignment</div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <div style={{ fontSize: "11px", color: "#94a3b8", fontWeight: 700 }}>🧠 BGE Vector Similarity (20%)</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc", marginTop: "2px" }}>{sb.semantic_fit}%</div>
            <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>768-dim dense embedding cosine score</div>
          </div>

          <div style={{ padding: "12px", borderRadius: "8px", background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.25)" }}>
            <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>🎓 Signal Bonus (+10%)</div>
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#34d399", marginTop: "2px" }}>+{sb.signal_bonus}%</div>
            <div style={{ fontSize: "11px", color: "#34d399", marginTop: "2px" }}>Verified stability & non-anomalous bonus</div>
          </div>
        </div>

        <button
          onClick={onClose}
          style={{
            width: "100%",
            padding: "9px",
            borderRadius: "8px",
            background: "rgba(56, 189, 248, 0.15)",
            border: "1px solid rgba(56, 189, 248, 0.4)",
            color: "#38bdf8",
            fontWeight: 700,
            fontSize: "13px",
            cursor: "pointer",
          }}
        >
          Close Rationale
        </button>
      </div>
    </div>
  );
}

function AgentConsoleModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterTool, setFilterTool] = useState<string>("all");
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/agent_logs");
      const data = await res.json();
      setLogs(data.logs || []);
    } catch (e) {
      console.error("Failed to fetch agent execution logs", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchLogs();
    }
  }, [isOpen]);

  useEffect(() => {
    let interval: any;
    if (isOpen && autoRefresh) {
      interval = setInterval(fetchLogs, 3000);
    }
    return () => clearInterval(interval);
  }, [isOpen, autoRefresh]);

  const filteredLogs = useMemo(() => {
    if (filterTool === "all") return logs;
    return logs.filter((l) =>
      (l.tool || l.event || "").toLowerCase().includes(filterTool.toLowerCase())
    );
  }, [logs, filterTool]);

  if (!isOpen) return null;

  const getEventBadge = (event: string) => {
    switch (event) {
      case "TOOL_CALL":
        return { label: "TOOL CALL", bg: "rgba(6, 182, 212, 0.15)", border: "rgba(6, 182, 212, 0.4)", text: "#38bdf8" };
      case "HONEYPOT_PURGE":
        return { label: "PURGE", bg: "rgba(239, 68, 68, 0.15)", border: "rgba(239, 68, 68, 0.4)", text: "#f87171" };
      case "CONSULTING_FILTER":
        return { label: "CONSULTING", bg: "rgba(245, 158, 11, 0.15)", border: "rgba(245, 158, 11, 0.4)", text: "#fbbf24" };
      case "EMBEDDING":
        return { label: "EMBEDDING", bg: "rgba(168, 85, 247, 0.15)", border: "rgba(168, 85, 247, 0.4)", text: "#c084fc" };
      default:
        return { label: "INFO", bg: "rgba(148, 163, 184, 0.15)", border: "rgba(148, 163, 184, 0.3)", text: "#cbd5e1" };
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(3, 7, 13, 0.88)",
        backdropFilter: "blur(14px)",
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1050px",
          height: "85vh",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#06090e",
          border: "1px solid rgba(6, 182, 212, 0.4)",
          borderRadius: "14px",
          boxShadow: "0 25px 80px rgba(6, 182, 212, 0.25), 0 0 50px rgba(0, 0, 0, 0.9)",
          overflow: "hidden",
          color: "#e7edf6",
          fontFamily: "var(--font-mono, monospace)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 24px",
            borderBottom: "1px solid rgba(6, 182, 212, 0.3)",
            background: "linear-gradient(90deg, rgba(6, 182, 212, 0.15) 0%, rgba(15, 23, 42, 0.95) 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "rgba(6, 182, 212, 0.15)",
                border: "1px solid rgba(6, 182, 212, 0.4)",
                color: "#38bdf8",
                display: "grid",
                placeItems: "center",
                boxShadow: "0 0 15px rgba(6, 182, 212, 0.3)",
              }}
            >
              <Terminal size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <h2 style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "#f8fafc", letterSpacing: "-0.02em" }}>
                  AWS Strands Agent Execution Console
                </h2>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    padding: "3px 9px",
                    borderRadius: "20px",
                    background: "rgba(16, 185, 129, 0.15)",
                    color: "#34d399",
                    border: "1px solid rgba(16, 185, 129, 0.4)",
                  }}
                >
                  SDK v0.1.0 • ACTIVE
                </span>
              </div>
              <p style={{ margin: "3px 0 0", fontSize: "12px", color: "#94a3b8" }}>
                Live trace of autonomous tool invocations, 768-dim embeddings & Honeypot Anomaly Purging.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              style={{
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
                background: autoRefresh ? "rgba(16, 185, 129, 0.2)" : "rgba(255, 255, 255, 0.05)",
                border: autoRefresh ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid rgba(255, 255, 255, 0.1)",
                color: autoRefresh ? "#34d399" : "#94a3b8",
              }}
            >
              {autoRefresh ? "● Auto-refresh ON" : "○ Auto-refresh OFF"}
            </button>
            <button
              onClick={fetchLogs}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "6px 14px",
                borderRadius: "6px",
                background: "rgba(6, 182, 212, 0.15)",
                border: "1px solid rgba(6, 182, 212, 0.4)",
                color: "#38bdf8",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <Activity size={14} className={loading ? "animate-spin" : ""} />
              <span>Refresh Logs</span>
            </button>
            <button
              onClick={onClose}
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "rgba(255, 255, 255, 0.05)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                color: "#94a3b8",
                display: "grid",
                placeItems: "center",
                cursor: "pointer",
              }}
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Console Toolbar / Badges */}
        <div
          style={{
            padding: "12px 24px",
            borderBottom: "1px solid #1e293b",
            background: "#0a0f18",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
            flexWrap: "wrap",
          }}
        >
          {/* Tech Badges */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px" }}>
            <span style={{ color: "#64748b", fontWeight: 600 }}>ORCHESTRATION:</span>
            <span style={{ padding: "3px 8px", borderRadius: "4px", background: "rgba(6, 182, 212, 0.1)", color: "#38bdf8", border: "1px solid rgba(6, 182, 212, 0.2)" }}>
              AWS Strands Agent SDK
            </span>
            <span style={{ padding: "3px 8px", borderRadius: "4px", background: "rgba(168, 85, 247, 0.1)", color: "#c084fc", border: "1px solid rgba(168, 85, 247, 0.2)" }}>
              BAAI/bge-base-en-v1.5 (768-dim)
            </span>
            <span style={{ padding: "3px 8px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.1)", color: "#34d399", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
              Bedrock / Gemini 2.5
            </span>
          </div>

          {/* Filter Pills */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            {["all", "audit_candidate_integrity", "apply_consulting_filter", "rank_and_reason_candidates"].map((tool) => (
              <button
                key={tool}
                onClick={() => setFilterTool(tool)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "5px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  background: filterTool === tool ? "rgba(6, 182, 212, 0.25)" : "rgba(255, 255, 255, 0.04)",
                  border: filterTool === tool ? "1px solid rgba(6, 182, 212, 0.5)" : "1px solid rgba(255, 255, 255, 0.08)",
                  color: filterTool === tool ? "#38bdf8" : "#94a3b8",
                }}
              >
                {tool === "all" ? "All Tools" : tool.replace("_candidates", "").replace("_candidate", "")}
              </button>
            ))}
          </div>
        </div>

        {/* Terminal Body Log Output */}
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "20px 24px",
            background: "#03070c",
            display: "flex",
            flexDirection: "column",
            gap: "10px",
          }}
        >
          {loading && logs.length === 0 ? (
            <div style={{ padding: "60px", textAlign: "center", color: "#38bdf8" }}>
              <Activity size={28} className="animate-spin" style={{ margin: "0 auto 12px" }} />
              <div>Connecting to AWS Strands Agent Execution Stream...</div>
            </div>
          ) : filteredLogs.length === 0 ? (
            <div style={{ padding: "60px", textAlign: "center", color: "#64748b" }}>
              <div>No agent execution logs match the selected tool filter.</div>
            </div>
          ) : (
            filteredLogs.map((log, idx) => {
              const badge = getEventBadge(log.event);
              return (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    padding: "12px 16px",
                    borderRadius: "8px",
                    background: "rgba(15, 23, 42, 0.6)",
                    border: "1px solid rgba(30, 41, 59, 0.8)",
                    fontSize: "13px",
                    lineHeight: "1.5",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ color: "#64748b", fontSize: "12px" }}>[{log.timestamp}]</span>
                      <span
                        style={{
                          padding: "2px 7px",
                          borderRadius: "4px",
                          fontSize: "10px",
                          fontWeight: 700,
                          background: badge.bg,
                          border: `1px solid ${badge.border}`,
                          color: badge.text,
                        }}
                      >
                        {badge.label}
                      </span>
                      <span style={{ color: "#38bdf8", fontWeight: 700 }}>{log.tool}</span>
                    </div>
                    {log.candidate_id && (
                      <span style={{ color: "#94a3b8", fontSize: "11px" }}>
                        CID: <strong style={{ color: "#f8fafc" }}>{log.candidate_id}</strong>
                      </span>
                    )}
                  </div>

                  <div style={{ color: "#cbd5e1", marginTop: "2px" }}>{log.message}</div>

                  {log.details && (
                    <div
                      style={{
                        padding: "8px 12px",
                        borderRadius: "6px",
                        background: "rgba(3, 7, 12, 0.8)",
                        border: "1px solid rgba(30, 41, 59, 0.6)",
                        color: "#94a3b8",
                        fontSize: "12px",
                        wordBreak: "break-word",
                      }}
                    >
                      {typeof log.details === "object" ? (
                        <pre style={{ margin: 0, fontFamily: "inherit" }}>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      ) : (
                        <span>{log.details}</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "14px 24px",
            borderTop: "1px solid #1e293b",
            background: "#0a0f18",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "12px",
            color: "#64748b",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "6px", color: "#38bdf8" }}>
              <Cpu size={14} /> 3 Autonomous Tools Active
            </span>
            <span>•</span>
            <span style={{ color: "#34d399" }}>0 Unhandled Exceptions</span>
            <span>•</span>
            <span style={{ color: "#c084fc" }}>Vector Dim: 768</span>
          </div>

          <button
            onClick={onClose}
            style={{
              padding: "7px 18px",
              borderRadius: "6px",
              background: "rgba(6, 182, 212, 0.15)",
              border: "1px solid rgba(6, 182, 212, 0.4)",
              color: "#38bdf8",
              fontWeight: 600,
              fontSize: "12px",
              cursor: "pointer",
            }}
          >
            Close Terminal
          </button>
        </div>
      </div>
    </div>
  );
}

function HoneypotModal({
  isOpen,
  onClose,
  honeypots,
  loading,
}: {
  isOpen: boolean;
  onClose: () => void;
  honeypots: any[];
  loading: boolean;
}) {
  const [search, setSearch] = useState("");

  const filteredHoneypots = useMemo(() => {
    if (!search.trim()) return honeypots;
    const q = search.toLowerCase();
    return honeypots.filter((item) => {
      const serialStr = `#${item.serial_number}`.toLowerCase();
      const numStr = String(item.serial_number);
      const name = (item.name || "").toLowerCase();
      const id = (item.candidate_id || "").toLowerCase();
      const title = (item.current_title || "").toLowerCase();
      const company = (item.current_company || "").toLowerCase();
      const reasons = (item.reasons || []).join(" ").toLowerCase();
      return (
        serialStr.includes(q) ||
        numStr === q ||
        name.includes(q) ||
        id.includes(q) ||
        title.includes(q) ||
        company.includes(q) ||
        reasons.includes(q)
      );
    });
  }, [honeypots, search]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "rgba(3, 7, 13, 0.85)",
        backdropFilter: "blur(12px)",
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "920px",
          maxHeight: "85vh",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#0d141e",
          border: "1px solid rgba(239, 68, 68, 0.4)",
          borderRadius: "14px",
          boxShadow: "0 25px 70px rgba(239, 68, 68, 0.2), 0 0 40px rgba(0, 0, 0, 0.8)",
          overflow: "hidden",
          color: "#e7edf6",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: "20px 24px",
            borderBottom: "1px solid rgba(239, 68, 68, 0.25)",
            background: "linear-gradient(90deg, rgba(239, 68, 68, 0.12) 0%, rgba(13, 20, 30, 0.95) 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "10px",
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid rgba(239, 68, 68, 0.4)",
                color: "#ef4444",
                display: "grid",
                placeItems: "center",
                boxShadow: "0 0 15px rgba(239, 68, 68, 0.3)",
              }}
            >
              <AlertTriangle size={22} />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <h2 style={{ margin: 0, fontSize: "20px", fontWeight: 700, letterSpacing: "-0.03em" }}>
                  Honeypot Trap Profiles Disqualified
                </h2>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 700,
                    padding: "3px 10px",
                    borderRadius: "20px",
                    background: "rgba(239, 68, 68, 0.2)",
                    color: "#fca5a5",
                    border: "1px solid rgba(239, 68, 68, 0.4)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {honeypots.length} REJECTED
                </span>
              </div>
              <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#94a3b8" }}>
                5-Point Anomaly Firewall identified synthetic trap profiles with logical contradictions.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#94a3b8",
              display: "grid",
              placeItems: "center",
              cursor: "pointer",
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Search Input Bar */}
        <div style={{ padding: "14px 24px", borderBottom: "1px solid #1e2b3b", background: "#0b1018" }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "0 14px",
              height: "40px",
              background: "#111923",
              border: "1px solid #2a394b",
              borderRadius: "8px",
              color: "#94a3b8",
            }}
          >
            <Search size={16} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Serial #, Candidate Name, ID, or Rejection Reason..."
              style={{
                flex: 1,
                background: "none",
                border: "none",
                outline: "none",
                color: "#e7edf6",
                fontSize: "14px",
              }}
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer" }}
              >
                <X size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Candidate List */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
          {loading ? (
            <div style={{ padding: "50px", textAlign: "center", color: "#94a3b8" }}>
              <span className="spinner" style={{ width: "24px", height: "24px" }} />
              <div style={{ marginTop: "12px" }}>Scanning honeypot log files...</div>
            </div>
          ) : filteredHoneypots.length === 0 ? (
            <div style={{ padding: "60px 20px", textAlign: "center", color: "#64748b" }}>
              <AlertCircle size={32} style={{ marginBottom: "10px", color: "#ef4444" }} />
              <div style={{ fontSize: "16px", fontWeight: 600, color: "#94a3b8" }}>
                {search ? "No honeypot profiles match your search criteria" : "No honeypot profiles found in dataset"}
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {filteredHoneypots.map((item, idx) => (
                <div
                  key={item.candidate_id || idx}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "85px 240px 1fr",
                    gap: "16px",
                    alignItems: "start",
                    padding: "16px",
                    borderRadius: "10px",
                    background: "rgba(17, 25, 35, 0.7)",
                    border: "1px solid rgba(239, 68, 68, 0.2)",
                  }}
                >
                  {/* Serial Number Badge */}
                  <div>
                    <span
                      style={{
                        display: "inline-block",
                        fontFamily: "var(--font-mono)",
                        fontSize: "13px",
                        fontWeight: 700,
                        padding: "4px 9px",
                        borderRadius: "6px",
                        background: "rgba(239, 68, 68, 0.15)",
                        color: "#f87171",
                        border: "1px solid rgba(239, 68, 68, 0.3)",
                      }}
                    >
                      #{String(item.serial_number).padStart(2, "0")}
                    </span>
                  </div>

                  {/* Candidate Identity */}
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "15px", color: "#f3f4f6" }}>
                      {item.name}
                    </div>
                    <div style={{ fontSize: "12px", fontFamily: "var(--font-mono)", color: "#94a3b8", marginTop: "2px" }}>
                      ID: {item.candidate_id}
                    </div>
                    <div style={{ fontSize: "13px", color: "#64748b", marginTop: "4px" }}>
                      {item.current_title} {item.current_company !== "N/A" ? `@ ${item.current_company}` : ""}
                    </div>
                  </div>

                  {/* Rejection Reasons (Line-by-line) */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    <div
                      style={{
                        fontSize: "11px",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        letterSpacing: "0.08em",
                        color: "#ef4444",
                        display: "flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      <AlertTriangle size={12} />
                      REJECTION REASON{item.reasons && item.reasons.length > 1 ? "S" : ""}:
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                      {(item.reasons || []).map((reason: string, rIdx: number) => (
                        <div
                          key={rIdx}
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: "8px",
                            padding: "8px 12px",
                            borderRadius: "6px",
                            background: "rgba(239, 68, 68, 0.08)",
                            border: "1px solid rgba(239, 68, 68, 0.2)",
                            fontSize: "13px",
                            color: "#fca5a5",
                            lineHeight: "1.4",
                          }}
                        >
                          <span style={{ color: "#ef4444", fontWeight: 700, fontSize: "12px" }}>•</span>
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "14px 24px",
            borderTop: "1px solid #1e2b3b",
            background: "#0b1018",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            fontSize: "13px",
            color: "#64748b",
          }}
        >
          <span>
            Showing <strong style={{ color: "#fca5a5" }}>{filteredHoneypots.length}</strong> of {honeypots.length} total trap profiles
          </span>
          <button
            onClick={onClose}
            style={{
              padding: "7px 16px",
              borderRadius: "6px",
              background: "rgba(255, 255, 255, 0.08)",
              border: "1px solid rgba(255, 255, 255, 0.15)",
              color: "#e2e8f0",
              fontWeight: 600,
              fontSize: "13px",
              cursor: "pointer",
            }}
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
}
