import React, { useState, useEffect, useRef } from "react";

interface Message {
  sender: "user" | "agent";
  text: string;
  toolCalls?: Array<{ name: string; status: string; result?: string }>;
}

interface Candidate {
  rank: number;
  candidate_id: string;
  name: string;
  headline: string;
  years_exp: number;
  location: string;
  current_title: string;
  current_company: string;
  score: number;
  reasoning: string;
  skills: string[];
}

interface DbStats {
  status: string;
  database_loaded: boolean;
  total_candidates: number;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "agent",
      text: "Hi! I am the RecruitShield AI co-pilot. I can help you search, filter, and audit your candidate pool. Ask me to:\n1. **Audit candidate integrity** (detects and removes fake resume honeypots).\n2. **Exclude consulting companies** (exludes services-only profiles).\n3. **Rank and search candidates** (semantic similarity search)."
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [awsAccessKey, setAwsAccessKey] = useState("");
  const [awsSecretKey, setAwsSecretKey] = useState("");
  const [awsRegion, setAwsRegion] = useState("us-east-1");
  const [showCredentials, setShowCredentials] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [uploading, setUploading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [dbStats, setDbStats] = useState<DbStats>({ status: "unknown", database_loaded: false, total_candidates: 0 });
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch database status on load
  useEffect(() => {
    fetchStats();
  }, []);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, chatLoading]);

  const fetchStats = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/health");
      const data = await res.json();
      setDbStats(data);
    } catch (e) {
      console.error("Backend offline: ", e);
    }
  };

  const fetchShortlist = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/shortlist");
      const data = await res.json();
      setCandidates(data.shortlist || []);
      if (data.shortlist && data.shortlist.length > 0) {
        setSelectedCandidate(data.shortlist[0]);
      }
    } catch (e) {
      console.error("Failed to fetch shortlist: ", e);
    }
  };

  const sendAgentCommand = async (command: string, customJd?: string) => {
    if (chatLoading) return;
    setChatLoading(true);
    
    // Add user message to console
    setMessages(prev => [...prev, { sender: "user", text: command }]);
    setInputText("");

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: command,
          aws_access_key: awsAccessKey || null,
          aws_secret_key: awsSecretKey || null,
          aws_region: awsRegion,
          job_description: customJd || jobDescription || null
        })
      });

      if (!res.ok) throw new Error("Failed to communicate with agent.");

      const data = await res.json();
      
      // Add agent response
      setMessages(prev => [...prev, {
        sender: "agent",
        text: data.response,
        toolCalls: data.tool_calls
      }]);

      // Refresh candidate table and stats
      fetchStats();
      fetchShortlist();
    } catch (err: any) {
      setMessages(prev => [...prev, {
        sender: "agent",
        text: `Error: ${err.message || "Failed to reach backend recruiter brain server."}`
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    sendAgentCommand(inputText);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", files[0]);

    try {
      const res = await fetch("http://127.0.0.1:8000/upload_jd", {
        method: "POST",
        body: formData
      });

      if (!res.ok) throw new Error("Failed to parse file.");

      const data = await res.json();
      setJobDescription(data.text);
      
      // Notify chat
      setMessages(prev => [...prev, {
        sender: "agent",
        text: `Uploaded job description file **${data.filename}** successfully.\nFound skills: **${data.metadata.skills_found.join(", ")}**\nExperience required: **${data.metadata.experience_range}**`
      }]);
    } catch (err: any) {
      alert(`Error uploading file: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleExportExcel = () => {
    if (candidates.length === 0) {
      alert("No candidates ranked yet! Please ask the agent to rank candidates first.");
      return;
    }
    window.open("http://127.0.0.1:8000/export", "_blank");
  };

  return (
    <div className="app-container">
      {/* Top Header Panel */}
      <header className="app-header glass-panel">
        <div className="header-logo">
          <div className="logo-badge">AWS</div>
          <div className="header-title">
            <h1>RecruitShield AI</h1>
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              Strands Agentic Talent Matching Co-Pilot
            </span>
          </div>
        </div>
        
        <div className="header-actions">
          {/* Database load banner */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginRight: "16px" }}>
            <span className={`spinner`} style={{ animationPlayState: dbStats.database_loaded ? "paused" : "running", borderColor: dbStats.database_loaded ? "var(--accent-emerald)" : "rgba(255,255,255,0.1)" }}></span>
            <span style={{ fontSize: "0.85rem", color: dbStats.database_loaded ? "var(--accent-emerald)" : "var(--accent-amber)" }}>
              {dbStats.database_loaded ? `DB Ready: ${dbStats.total_candidates} Profiles` : "Loading Database..."}
            </span>
          </div>

          <button className="btn" onClick={() => setShowCredentials(!showCredentials)}>
            🔐 Bedrock Config
          </button>
          <button className="btn btn-primary" onClick={handleExportExcel}>
            📥 Export XLSX
          </button>
        </div>
      </header>

      {/* Bedrock Credential Overlay */}
      {showCredentials && (
        <div className="credentials-overlay glass-panel">
          <h4 style={{ marginBottom: "12px", borderBottom: "1px solid var(--border-glass)", paddingBottom: "6px" }}>AWS Configuration</h4>
          <div className="form-group">
            <label>Access Key ID</label>
            <input 
              type="password" 
              className="form-control" 
              placeholder="AKIA..." 
              value={awsAccessKey}
              onChange={(e) => setAwsAccessKey(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Secret Access Key</label>
            <input 
              type="password" 
              className="form-control" 
              placeholder="wJalrXUtnFEMI..." 
              value={awsSecretKey}
              onChange={(e) => setAwsSecretKey(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Bedrock Region</label>
            <input 
              type="text" 
              className="form-control" 
              value={awsRegion}
              onChange={(e) => setAwsRegion(e.target.value)}
            />
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginTop: "8px" }}>
            AWS Bedrock Claude Sonnet model access is required. If left empty, agent runs in local simulator mode.
          </p>
          <button className="btn btn-primary" style={{ width: "100%", marginTop: "12px" }} onClick={() => setShowCredentials(false)}>
            Save Configuration
          </button>
        </div>
      )}

      {/* Main Workspace Layout */}
      <main className="main-grid">
        {/* Left Side: Job Details & Chat Console */}
        <section className="sidebar">
          {/* Job Description / Search Criteria Panel */}
          <div className="glass-panel" style={{ padding: "20px" }}>
            <h3 style={{ marginBottom: "12px", fontSize: "1.1rem" }}>📋 Search Context</h3>
            
            {/* Upload Zone */}
            <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
              <input 
                type="file" 
                ref={fileInputRef} 
                style={{ display: "none" }} 
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
              />
              <span style={{ fontSize: "1.5rem" }}>📄</span>
              <p style={{ fontSize: "0.85rem", fontWeight: 600, marginTop: "4px" }}>
                {uploading ? "Parsing File..." : "Upload Job Description"}
              </p>
              <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Supports PDF, DOCX, TXT
              </span>
            </div>

            <div className="form-group" style={{ marginTop: "16px" }}>
              <label>Search Query / Job Description</label>
              <textarea 
                className="form-control" 
                style={{ height: "100px", resize: "none", fontFamily: "var(--font-body)", fontSize: "0.85rem" }}
                placeholder="Paste Job Description text or use uploaded details..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
              />
            </div>
          </div>

          {/* Recruiter Agent Chat Cockpit */}
          <div className="glass-panel chat-section" style={{ flex: 1 }}>
            <div className="chat-messages">
              {messages.map((m, idx) => (
                <div key={idx} className={`chat-bubble ${m.sender}`}>
                  <p style={{ whiteSpace: "pre-line" }}>{m.text}</p>
                  
                  {/* Visual Tool call Log list */}
                  {m.toolCalls && m.toolCalls.length > 0 && (
                    <div className="agent-thought-container">
                      <p style={{ fontWeight: 700, fontSize: "0.8rem", marginBottom: "6px", textTransform: "uppercase", color: "var(--accent-teal)" }}>
                        ⚙️ Strands Agent Event Logs:
                      </p>
                      {m.toolCalls.map((tc, tIdx) => (
                        <div key={tIdx} className="thought-log-item">
                          <span className="spinner" style={{ animationPlayState: tc.status === "completed" ? "paused" : "running", width: "12px", height: "12px" }}></span>
                          <span>Tool Call: **{tc.name}** ({tc.status})</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {chatLoading && (
                <div className="chat-bubble agent" style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span className="spinner"></span>
                  <span>RecruitShield Agent is thinking...</span>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Quick Actions Shortcuts */}
            <div style={{ display: "flex", gap: "6px", padding: "0 16px", flexWrap: "wrap" }}>
              <button className="btn btn-danger" style={{ fontSize: "0.75rem", padding: "6px 10px" }} onClick={() => sendAgentCommand("Run candidate database anomaly audit check to remove honeypots")}>
                🛡️ Audit Integrity
              </button>
              <button className="btn btn-success" style={{ fontSize: "0.75rem", padding: "6px 10px" }} onClick={() => sendAgentCommand("Exclude consulting services companies from candidates pool")}>
                🏢 Consulting Filter
              </button>
              <button className="btn btn-primary" style={{ fontSize: "0.75rem", padding: "6px 10px" }} onClick={() => sendAgentCommand("Rank candidate database semantic fit against active job description")}>
                🔍 Rank Semantic Fit
              </button>
            </div>

            {/* Chat Input form */}
            <form onSubmit={handleSendChat} className="chat-input-container">
              <input 
                type="text" 
                className="chat-input" 
                placeholder="Ask agent to audit, filter, or rank candidate pool..." 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={chatLoading}
              />
              <button type="submit" className="btn btn-primary" disabled={chatLoading}>
                Send
              </button>
            </form>
          </div>
        </section>

        {/* Right Side: Dashboard Details & Shortlist */}
        <section className="dashboard-panel glass-panel" style={{ height: "100%", overflow: "hidden" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", height: "100%", overflow: "hidden" }}>
            {/* Candidate Table List */}
            <div className="table-container" style={{ borderRight: "1px solid var(--border-glass)" }}>
              <h2 style={{ fontSize: "1.2rem", marginBottom: "16px", fontFamily: "var(--font-heading)" }}>🏆 Ranked Talent Shortlist</h2>
              
              {candidates.length === 0 ? (
                <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-secondary)" }}>
                  <span style={{ fontSize: "2.5rem" }}>🕵️‍♂️</span>
                  <p style={{ marginTop: "12px", fontWeight: 600 }}>No candidates ranked yet.</p>
                  <p style={{ fontSize: "0.85rem" }}>Use the Chat Cockpit or shortcuts on the left to ask the Strands Agent to rank matching candidates.</p>
                </div>
              ) : (
                <table className="candidate-table">
                  <thead>
                    <tr>
                      <th style={{ width: "60px" }}>Rank</th>
                      <th>Candidate Details</th>
                      <th>Location</th>
                      <th>Experience</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidates.map((c) => (
                      <tr 
                        key={c.candidate_id} 
                        style={{ cursor: "pointer", background: selectedCandidate?.candidate_id === c.candidate_id ? "rgba(255,255,255,0.03)" : "transparent" }}
                        onClick={() => setSelectedCandidate(c)}
                      >
                        <td>
                          <span className={`rank-badge ${c.rank <= 3 ? "top-3" : ""}`}>
                            #{c.rank}
                          </span>
                        </td>
                        <td>
                          <div style={{ fontWeight: 600 }}>{c.name}</div>
                          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>{c.current_title} at **{c.current_company || "Unknown"}**</div>
                          <div className="tag-list" style={{ marginTop: "4px" }}>
                            {c.skills.map((s, idx) => (
                              <span key={idx} className="tag">{s}</span>
                            ))}
                          </div>
                        </td>
                        <td style={{ fontSize: "0.85rem" }}>{c.location || "N/A"}</td>
                        <td style={{ fontSize: "0.85rem" }}>{c.years_exp} Years</td>
                        <td>
                          <span className="score-text">{c.score}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Candidate Audit Reasoning Details */}
            <div className="details-sidebar">
              <h2 style={{ fontSize: "1.2rem", borderBottom: "1px solid var(--border-glass)", paddingBottom: "10px", fontFamily: "var(--font-heading)" }}>🔍 Deep Audit Reasoning</h2>
              
              {selectedCandidate ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  <div>
                    <h3 style={{ fontSize: "1.4rem", fontWeight: 700 }}>{selectedCandidate.name}</h3>
                    <p style={{ color: "var(--accent-teal)", fontSize: "0.9rem", fontWeight: 600 }}>{selectedCandidate.current_title}</p>
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Company: {selectedCandidate.current_company || "N/A"}</p>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                    <div style={{ background: "rgba(255,255,255,0.02)", padding: "10px", borderRadius: "6px" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Match Score</span>
                      <div style={{ fontSize: "1.3rem", fontWeight: 800, color: "var(--accent-emerald)" }}>{selectedCandidate.score}</div>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.02)", padding: "10px", borderRadius: "6px" }}>
                      <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase" }}>Experience</span>
                      <div style={{ fontSize: "1.3rem", fontWeight: 800, color: "white" }}>{selectedCandidate.years_exp} Yrs</div>
                    </div>
                  </div>

                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 700 }}>Recruiter Reasoning (Factual Summary)</span>
                    <p style={{ background: "rgba(14, 165, 233, 0.05)", border: "1px solid rgba(14, 165, 233, 0.1)", padding: "14px", borderRadius: "8px", fontSize: "0.9rem", lineHeight: 1.5, marginTop: "6px" }}>
                      {selectedCandidate.reasoning}
                    </p>
                  </div>

                  <div>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", fontWeight: 700, display: "block", marginBottom: "8px" }}>Verified Skill Set</span>
                    <div className="tag-list">
                      {selectedCandidate.skills.map((s, idx) => (
                        <span key={idx} className="tag" style={{ padding: "4px 8px" }}>{s}</span>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: "40px 10px", textAlign: "center", color: "var(--text-secondary)" }}>
                  <p>Select a candidate from the table list to see their detailed audit reasoning logs.</p>
                </div>
              )}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
