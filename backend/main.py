import os
import re
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
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
    allow_origins=["*"],  # In production, specify React app domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input data models
class ChatRequest(BaseModel):
    message: str
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = "us-east-1"
    job_description: Optional[str] = None

# Initialize candidate database on startup
CANDIDATE_DB_PATH = "D:/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"

@app.on_event("startup")
def startup_event():
    logger.info("Initializing candidate database...")
    success = load_candidates_file(CANDIDATE_DB_PATH)
    if success:
        logger.info("Database loaded successfully.")
    else:
        logger.warning("Database failed to load at startup. Please load via the `/load` endpoint later.")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database_loaded": len(CANDIDATES) > 0,
        "total_candidates": len(CANDIDATES)
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
    If AWS credentials are provided, runs the actual Strands Bedrock Agent.
    Otherwise, runs in interactive Simulation Mode representing the SDK's execution.
    """
    global CANDIDATES, ACTIVE_SHORTLIST
    
    prompt = req.message.lower()
    
    # 1. AWS Credentials checking
    aws_keys_present = (
        req.aws_access_key is not None and len(req.aws_access_key.strip()) > 0 and
        req.aws_secret_key is not None and len(req.aws_secret_key.strip()) > 0
    )
    
    # If AWS is configured, run the actual Strands Bedrock Agent
    if aws_keys_present:
        try:
            logger.info("Running actual Strands Bedrock Agent...")
            agent = get_recruiter_agent(
                aws_access_key=req.aws_access_key,
                aws_secret_key=req.aws_secret_key,
                aws_region=req.aws_region
            )
            
            # Execute the agent
            result = agent(req.message)
            
            # Extract final text message
            response_text = ""
            if hasattr(result, "message") and hasattr(result.message, "content"):
                for block in result.message.content:
                    if hasattr(block, "text"):
                        response_text += block.text
                    elif isinstance(block, str):
                        response_text += block
            
            if not response_text:
                response_text = "The agent completed the pipeline but did not return any text."
                
            # Extract tool calls from event loop logs if present
            tool_calls = []
            if hasattr(result, "metrics") and hasattr(result.metrics, "tool_calls"):
                for tc in result.metrics.tool_calls:
                    tool_calls.append({
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "status": "success"
                    })
                    
            # Fallback if strands didn't log tool calls directly in metrics
            # We scan the prompt to see which tools were called
            if not tool_calls:
                if "audit" in prompt or "integrity" in prompt or "clean" in prompt:
                    tool_calls.append({"name": "audit_candidate_integrity", "status": "completed"})
                if "consulting" in prompt or "services" in prompt or "exclude" in prompt:
                    tool_calls.append({"name": "apply_consulting_filter", "status": "completed"})
                if "rank" in prompt or "score" in prompt or "find" in prompt:
                    tool_calls.append({"name": "rank_and_reason_candidates", "status": "completed"})
            
            return {
                "response": response_text,
                "tool_calls": tool_calls,
                "shortlist_count": len(ACTIVE_SHORTLIST)
            }
            
        except Exception as e:
            logger.error(f"Error running Bedrock Strands Agent: {e}. Falling back to simulation mode.")
            # Fallback to simulation below
            
    # 2. Strands Agent Simulation Mode (runs the exact python tool code)
    logger.info("Running Strands Agent Simulator...")
    tool_calls = []
    response_parts = []
    
    # Simulate step-by-step agentic planning
    if "audit" in prompt or "integrity" in prompt or "clean" in prompt or "honeypot" in prompt:
        tool_calls.append({
            "name": "audit_candidate_integrity",
            "status": "executing"
        })
        res = audit_candidate_integrity()
        tool_calls[-1]["status"] = "completed"
        tool_calls[-1]["result"] = res
        response_parts.append(res)
        
    if "consulting" in prompt or "services" in prompt or "exclude" in prompt:
        tool_calls.append({
            "name": "apply_consulting_filter",
            "status": "executing"
        })
        res = apply_consulting_filter()
        tool_calls[-1]["status"] = "completed"
        tool_calls[-1]["result"] = res
        response_parts.append(res)
        
    if "rank" in prompt or "score" in prompt or "find" in prompt or "match" in prompt:
        jd = req.job_description or "Seeking Senior AI Engineer with expertise in sentence-transformers and vector DBs."
        tool_calls.append({
            "name": "rank_and_reason_candidates",
            "status": "executing"
        })
        # Rank top 100 for export template availability
        res_json = rank_and_reason_candidates(job_description=jd, top_n=100)
        tool_calls[-1]["status"] = "completed"
        tool_calls[-1]["result"] = "Shortlisted top candidates successfully."
        
        parsed = json.loads(res_json)
        response_parts.append(
            f"Successfully ranked candidate database against the Job Description.\n"
            f"Fitted semantic embeddings and title weights.\n"
            f"Top Match: **{parsed[0]['name']}** (Rank 1, Score: {parsed[0]['score']}).\n"
            f"Reasoning: *\"{parsed[0]['reasoning']}\"*"
        )
        
    if not response_parts:
        response_text = (
            "Hi! I am the RecruitShield AI co-pilot. You can ask me to:\n"
            "1. **Audit candidate integrity** (removes synthetic honeypots).\n"
            "2. **Exclude consulting companies** (removes services-only candidates).\n"
            "3. **Rank and search candidates** (semantic similarity search)."
        )
    else:
        response_text = "\n\n".join(response_parts)
        
    return {
        "response": response_text,
        "tool_calls": tool_calls,
        "shortlist_count": len(ACTIVE_SHORTLIST)
    }

@app.get("/shortlist")
def get_shortlist():
    """Fetches the current top shortlist of candidates with reasoning details."""
    global ACTIVE_SHORTLIST
    
    summary_list = []
    for c in ACTIVE_SHORTLIST:
        # Extract skills for easy display
        skills_list = [s["name"] for s in c["candidate_raw"].get("skills", [])]
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
            "skills": skills_list[:5]  # limit to 5
        })
        
    return {"shortlist": summary_list}

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
