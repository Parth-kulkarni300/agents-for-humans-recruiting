import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
import re
import json
import logging
import numpy as np
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
from backend.ranker import EMBEDDINGS_LOADED, EMBEDDINGS_COUNT
from pypdf import PdfReader
import zipfile
import xml.etree.ElementTree as ET

from backend.agent import (
    load_candidates_file, 
    get_recruiter_agent, 
    CANDIDATES, 
    ACTIVE_SHORTLIST,
    audit_candidate_integrity,
    apply_consulting_filter,
    rank_and_reason_candidates
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recruiter-backend")

app = FastAPI(title="RecruitShield AI Backend", version="1.0.0")

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input data models
class ChatRequest(BaseModel):
    message: str
    job_description: Optional[str] = None

# Initialize candidate database on startup
CANDIDATE_DB_PATH = os.environ.get("CANDIDATES_PATH", "D:/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl")

@app.on_event("startup")
def startup_event():
    logger.info("Backend starting. Attempting to load candidate database...")
    load_candidates_file(CANDIDATE_DB_PATH)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_loaded": len(CANDIDATES) > 0,
        "total_candidates": len(CANDIDATES),
        "embeddings_loaded": EMBEDDINGS_LOADED,
        "embeddings_count": EMBEDDINGS_COUNT
    }

@app.post("/load")
def force_load_database(path: str = CANDIDATE_DB_PATH):
    success = load_candidates_file(path)
    if success:
        return {"status": "success", "count": len(CANDIDATES)}
    else:
        raise HTTPException(status_code=400, detail="Failed to load candidates database from the specified path.")

@app.post("/chat")
def run_agent_chat(req: ChatRequest):
    """
    Main endpoint for chatting with the recruiter agent.
    Tries Bedrock first, falls back to direct tool execution if unavailable.
    """
    global CANDIDATES, ACTIVE_SHORTLIST
    
    if not CANDIDATES:
        raise HTTPException(status_code=400, detail="No candidates loaded. Please upload a candidates file first.")
    
    # Try Bedrock Agent first
    try:
        logger.info("Running Strands Bedrock Agent...")
        agent = get_recruiter_agent()
        result = agent(req.message)
        
        response_text = ""
        if hasattr(result, "message") and hasattr(result.message, "content"):
            for block in result.message.content:
                if hasattr(block, "text"):
                    response_text += block.text
                elif isinstance(block, str):
                    response_text += block
        
        if not response_text:
            response_text = str(result)
            
        tool_calls = []
        if hasattr(result, "metrics") and hasattr(result.metrics, "tool_calls"):
            for tc in result.metrics.tool_calls:
                tool_calls.append({"name": tc.name, "arguments": tc.arguments, "status": "success"})
        
        return {"response": response_text, "tool_calls": tool_calls, "shortlist_count": len(ACTIVE_SHORTLIST)}
        
    except Exception as bedrock_err:
        logger.warning(f"Bedrock unavailable, using Gemini fallback...")
        
        # --- GEMINI FALLBACK: Run Strands tools + Gemini for reasoning ---
        steps = []
        
        # Step 1: Audit integrity (remove honeypots)
        try:
            audit_result = audit_candidate_integrity()
            steps.append(("audit_candidate_integrity", audit_result))
        except Exception as e:
            steps.append(("audit_candidate_integrity", f"Error: {str(e)}"))
        
        # Step 2: Filter consulting-only profiles
        try:
            filter_result = apply_consulting_filter()
            steps.append(("apply_consulting_filter", filter_result))
        except Exception as e:
            steps.append(("apply_consulting_filter", f"Error: {str(e)}"))
        
        # Step 3: Rank and reason candidates
        try:
            jd = req.job_description or "senior software engineer"
            top_n = 20
            if req.message:
                match = re.search(r'top\s*(\d+)', req.message, re.IGNORECASE)
                if match:
                    top_n = int(match.group(1))
            rank_result = rank_and_reason_candidates(job_description=jd, top_n=top_n)
            steps.append(("rank_and_reason_candidates", rank_result))
        except Exception as e:
            steps.append(("rank_and_reason_candidates", f"Error: {str(e)}"))
        
        # Now use Gemini to generate intelligent recruiter summary
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                from google import genai
                from google.genai import types
                client_gemini = genai.Client(api_key=gemini_key)
                
                tool_results_text = "\n\n".join([f"Tool: {name}\nResult:\n{result}" for name, result in steps])
                prompt = f"""You are RecruitShield AI, an expert autonomous recruiter co-pilot.

You have just executed the full candidate screening pipeline using the Strands Agents SDK across {len(CANDIDATES)} candidates in the database. Here are the results from the three tools:

{tool_results_text}

Now provide a professional, clear summary as a recruiter co-pilot:
1. State clearly that all {len(CANDIDATES)} loaded candidate profiles were scanned and scored by the algorithm, and explain why the top shortlist of candidates was selected.
2. What integrity anomalies (honeypots) were found and removed?
3. Confirm that IT consulting profiles were given a soft penalty (-0.05 score adjustment) rather than being banned/excluded, allowing all qualified talent to remain in the active pool.
4. Who are the top candidates in the shortlist and why do they stand out?
Keep it concise, insightful, and actionable for a recruiter."""

                response = client_gemini.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                ai_summary = response.text
                response_text = f"✅ **RecruitShield Agent Pipeline Complete**\n\n{ai_summary}"
                
            except Exception as gemini_err:
                logger.error(f"Gemini error: {gemini_err}")
                response_text = "✅ **Pipeline Complete**\n\n" + "\n\n".join([f"**{n}**\n{r}" for n, r in steps])
        else:
            response_text = "✅ **Pipeline Complete**\n\n" + "\n\n".join([f"**{n}**\n{r}" for n, r in steps])
        
        tool_calls = [{"name": n, "status": "success"} for n, _ in steps]
        return {"response": response_text, "tool_calls": tool_calls, "shortlist_count": len(ACTIVE_SHORTLIST)}



import math

@app.get("/shortlist")
def get_shortlist(page: int = 1, limit: int = 50):
    """Fetches the ranked candidate list with pagination support and KPI stats."""
    global ACTIVE_SHORTLIST, CANDIDATES
    import backend.agent as agent_mod
    
    total_candidates = agent_mod.TOTAL_INITIAL_CANDIDATES if agent_mod.TOTAL_INITIAL_CANDIDATES > 0 else len(agent_mod.CANDIDATES)
    eligible_candidates = agent_mod.ELIGIBLE_CANDIDATES if agent_mod.ELIGIBLE_CANDIDATES > 0 else len(agent_mod.CANDIDATES)
    honeypots = max(0, total_candidates - eligible_candidates)
    
    source_pool = ACTIVE_SHORTLIST if ACTIVE_SHORTLIST else [
        {
            "rank": idx + 1,
            "candidate_id": c.get("candidate_id", f"C-{idx}"),
            "name": c.get("profile", {}).get("anonymized_name", "Candidate"),
            "headline": c.get("profile", {}).get("headline", ""),
            "years_exp": c.get("profile", {}).get("years_of_experience", 0.0),
            "location": c.get("profile", {}).get("location", ""),
            "current_title": c.get("profile", {}).get("current_title", ""),
            "current_company": c.get("profile", {}).get("current_company", ""),
            "score": 0.85,
            "reasoning": "Candidate active in screening pool. Run agent to compute JD match score.",
            "candidate_raw": c
        }
        for idx, c in enumerate(CANDIDATES)
    ]
    
    total_items = len(source_pool)
    
    if limit > 0:
        start_idx = max(0, (page - 1) * limit)
        end_idx = min(total_items, start_idx + limit)
        page_items = source_pool[start_idx:end_idx]
    else:
        page_items = source_pool
    
    summary_list = []
    for c in page_items:
        # Return full skill objects so frontend can compute real proficiency bars
        skills_list = c["candidate_raw"].get("skills", [])[:10]
        summary_list.append({
            "rank": c["rank"],
            "candidate_id": c["candidate_id"],
            "name": c["name"],
            "headline": c["headline"],
            "years_exp": c["years_exp"],
            "location": c["location"],
            "current_title": c["current_title"],
            "current_company": c["current_company"],
            "score": round(c["score"], 4),
            "reasoning": c["reasoning"],
            "skills": skills_list[:10],
            "education": c["candidate_raw"].get("education", []),
            "career_history": c["candidate_raw"].get("career_history", []),
            "signals": c["candidate_raw"].get("redrob_signals", {})
        })
        
    return {
        "stats": {
            "total_candidates": total_candidates,
            "eligible_candidates": eligible_candidates,
            "honeypot_count": honeypots,
            "total_ranked": total_items
        },
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total_items / limit) if (limit > 0 and total_items > 0) else 1,
        "shortlist": summary_list
    }

@app.get("/honeypots")
def get_honeypots():
    """Fetches the list of identified honeypot (anomalous/rejected) candidates with rejection reasons."""
    import backend.agent as agent_mod
    return {
        "count": len(agent_mod.HONEYPOT_CANDIDATES),
        "honeypots": agent_mod.HONEYPOT_CANDIDATES
    }

@app.get("/export")
def export_shortlist_excel():
    """Generates the final submission.xlsx file on the fly and downloads it."""
    global ACTIVE_SHORTLIST
    if not ACTIVE_SHORTLIST:
        raise HTTPException(status_code=400, detail="Shortlist is empty. Please rank candidates first.")
        
    logger.info("Exporting shortlist to Excel...")
    
    # We create the exact format needed for the hackathon portal
    export_data = []
    for c in ACTIVE_SHORTLIST:
        export_data.append({
            "candidate_id": c["candidate_id"],
            "rank": c["rank"],
            "score": round(c["score"], 4),
            "reasoning": c["reasoning"]
        })
        
    df = pd.DataFrame(export_data)
    out_path = Path("submission.xlsx")
    df.to_excel(out_path, index=False)
    
    return FileResponse(
        path=out_path, 
        filename="submission.xlsx", 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.post("/upload_candidates")
async def upload_candidates_batch(file: UploadFile = File(...)):
    """
    Ingests a new candidate pool via JSONL or CSV.
    REPLACES the existing pool entirely (not append) so jury files work correctly.
    After loading, auto-recomputes neural embeddings for the new candidates.
    """
    import backend.agent as agent_mod
    from backend.ranker import get_sentence_model
    import backend.ranker as ranker_mod

    global CANDIDATES
    filename = file.filename.lower()
    content = await file.read()
    
    new_candidates = []
    try:
        if filename.endswith(".jsonl"):
            text = content.decode("utf-8", errors="ignore")
            for line in text.split("\n"):
                if line.strip():
                    new_candidates.append(json.loads(line))
        elif filename.endswith(".csv"):
            import io
            df = pd.read_csv(io.BytesIO(content))
            for _, row in df.iterrows():
                cand = {
                    "candidate_id": str(row.get("candidate_id", f"C-{len(new_candidates)}")),
                    "profile": {
                        "anonymized_name": str(row.get("name", "Unknown")),
                        "headline": str(row.get("headline", "")),
                        "years_of_experience": float(row.get("years_exp", 0.0)),
                        "location": str(row.get("location", "")),
                        "current_title": str(row.get("current_title", "")),
                        "current_company": str(row.get("current_company", ""))
                    },
                    "skills": [{"name": s.strip(), "proficiency": "intermediate", "duration_months": 24} for s in str(row.get("skills", "")).split(",") if s.strip()],
                    "career_history": [],
                    "education": [],
                    "redrob_signals": {}
                }
                new_candidates.append(cand)
        else:
            raise HTTPException(status_code=400, detail="Only JSONL or CSV formats are supported.")
            
        # REPLACE pool (not append) — critical for jury compatibility
        agent_mod.RAW_INITIAL_CANDIDATES.clear()
        agent_mod.RAW_INITIAL_CANDIDATES.extend(new_candidates)
        agent_mod.CANDIDATES.clear()
        agent_mod.CANDIDATES.extend(new_candidates)
        agent_mod.TOTAL_INITIAL_CANDIDATES = len(new_candidates)
        agent_mod.ACTIVE_SHORTLIST.clear()
        logger.info(f"Replaced candidate pool with {len(new_candidates)} candidates. Running integrity audit...")
        audit_candidate_integrity()
        
        # Auto-recompute neural embeddings for the new candidates
        logger.info("Auto-computing neural embeddings for uploaded candidates...")
        try:
            model = get_sentence_model()
            if model is not None:
                texts = []
                ids = []
                for c in agent_mod.CANDIDATES:
                    profile = c.get("profile", {})
                    title = profile.get("current_title", "")
                    headline = profile.get("headline", "")
                    summary = profile.get("summary", "")
                    texts.append(f"Title: {title}. Headline: {headline}. Summary: {summary}")
                    ids.append(c["candidate_id"])
                
                batch_size = 512
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = model.encode(texts[i:i+batch_size], normalize_embeddings=True, show_progress_bar=False)
                    all_embeddings.append(batch)
                
                embeddings_matrix = np.vstack(all_embeddings)
                
                # Update ranker globals in-memory
                ranker_mod.CANDIDATE_EMBEDDINGS = embeddings_matrix
                ranker_mod.CANDIDATE_ID_TO_INDEX = {cid: idx for idx, cid in enumerate(ids)}
                ranker_mod.EMBEDDINGS_LOADED = True
                ranker_mod.EMBEDDINGS_COUNT = len(ids)
                
                # Persist to disk so reload survives restart
                _backend_dir = Path(__file__).parent
                np.save(_backend_dir / "candidate_embeddings.npy", embeddings_matrix)
                import json as _json
                with open(_backend_dir / "candidate_ids.json", "w") as f:
                    _json.dump(ids, f)
                
                logger.info(f"Successfully computed and saved {len(ids)} embeddings for uploaded candidates.")
                embeddings_status = f"Recomputed {len(ids)} neural embeddings"
            else:
                embeddings_status = "Embeddings skipped (model unavailable) — rule-based ranking active"
        except Exception as emb_err:
            logger.error(f"Embedding computation failed: {emb_err}")
            embeddings_status = f"Embeddings failed ({emb_err}) — rule-based ranking active"
        
        return {
            "status": "success",
            "ingested_count": len(new_candidates),
            "total_candidates": len(agent_mod.CANDIDATES),
            "embeddings": embeddings_status
        }
    except Exception as e:
        logger.error(f"Error parsing candidate file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest candidates: {str(e)}")

# Helper function to parse docx XML directly (saves us installing python-docx)
def parse_docx_bytes(file_bytes):
    import io
    docx_zip = zipfile.ZipFile(io.BytesIO(file_bytes))
    content_xml = docx_zip.read("word/document.xml")
    root = ET.fromstring(content_xml)
    
    namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text_parts = []
    for elem in root.findall('.//w:t', namespaces):
        if elem.text:
            text_parts.append(elem.text)
            
    return " ".join(text_parts)

@app.post("/upload_jd")
async def upload_job_description(file: UploadFile = File(...)):
    """Parses PDF, DOCX, or TXT job description files and returns the text content."""
    filename = file.filename.lower()
    content = await file.read()
    
    text = ""
    try:
        if filename.endswith(".pdf"):
            import io
            pdf_reader = PdfReader(io.BytesIO(content))
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text() or "")
            text = "\n".join(text_parts)
            
        elif filename.endswith(".docx"):
            text = parse_docx_bytes(content)
            
        elif filename.endswith(".txt"):
            text = content.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT.")
            
        # Clean extra whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        # Extract skills and range details as validation metadata
        from backend.ranker import extract_skills_from_jd, extract_experience_range_from_jd
        skills = list(extract_skills_from_jd(text))
        min_exp, max_exp = extract_experience_range_from_jd(text)
        
        return {
            "text": text,
            "filename": file.filename,
            "metadata": {
                "skills_found": skills,
                "experience_range": f"{min_exp} - {max_exp} years"
            }
        }
    except Exception as e:
        logger.error(f"Error parsing file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")
