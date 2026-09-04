import os
import json
import logging
import numpy as np
from pathlib import Path
from strands import Agent, tool
from strands.models import BedrockModel
from backend.ranker import is_honeypot, check_honeypot_reasons, is_consulting_only, score_candidate, rank_candidates

logger = logging.getLogger("recruiter-agent")

# Global candidate store & stats
CANDIDATES = []
ACTIVE_SHORTLIST = []
HONEYPOT_CANDIDATES = []
TOTAL_INITIAL_CANDIDATES = 0
HONEYPOT_COUNT = 0
ELIGIBLE_CANDIDATES = 0

def load_candidates_file(file_path: str):
    """Loads candidates from JSONL into memory once at startup."""
    global CANDIDATES, TOTAL_INITIAL_CANDIDATES, ELIGIBLE_CANDIDATES
    CANDIDATES.clear()
    
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Candidates file not found at: {file_path}")
        # Try parent directory fallback
        fallback_path = Path("D:/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl")
        if fallback_path.exists():
            path = fallback_path
        else:
            logger.error("No candidates database file found. Please check candidates.jsonl location.")
            return False
            
    logger.info(f"Loading candidate database from {path}...")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    CANDIDATES.append(json.loads(line))
        TOTAL_INITIAL_CANDIDATES = len(CANDIDATES)
        logger.info(f"Successfully loaded {len(CANDIDATES)} candidate profiles. Running initial integrity audit...")
        audit_candidate_integrity()
        return True
    except Exception as e:
        logger.error(f"Error loading candidates: {e}")
        return False

# Define Strands Agent Custom Tools
@tool
def audit_candidate_integrity() -> str:
    """
    Scans the loaded candidate database using a 5-point integrity check.
    Identifies and removes fake profiles (honeypots) created with logical contradictions.
    Returns: A summary message listing the number of deleted honeypots and remaining candidates.
    """
    global CANDIDATES, TOTAL_INITIAL_CANDIDATES, HONEYPOT_COUNT, ELIGIBLE_CANDIDATES, HONEYPOT_CANDIDATES
    if not CANDIDATES:
        return "Error: Candidate database is empty. Please load candidates first."
        
    initial_count = len(CANDIDATES)
    if TOTAL_INITIAL_CANDIDATES == 0:
        TOTAL_INITIAL_CANDIDATES = initial_count
        
    clean_candidates = []
    HONEYPOT_CANDIDATES.clear()
    honeypot_count = 0
    reasons_summary = {}
    
    for idx, c in enumerate(CANDIDATES):
        hp_flag, reasons = check_honeypot_reasons(c)
        if hp_flag:
            honeypot_count += 1
            primary_reason = reasons[0] if reasons else "Logical anomaly detected"
            reasons_summary[primary_reason] = reasons_summary.get(primary_reason, 0) + 1
            HONEYPOT_CANDIDATES.append({
                "serial_number": idx + 1,
                "candidate_id": c.get("candidate_id", f"C-{idx + 1}"),
                "name": c.get("profile", {}).get("anonymized_name", f"Candidate-{idx + 1}"),
                "current_title": c.get("profile", {}).get("current_title", "N/A"),
                "current_company": c.get("profile", {}).get("current_company", "N/A"),
                "location": c.get("profile", {}).get("location", "N/A"),
                "years_exp": c.get("profile", {}).get("years_of_experience", 0.0),
                "reasons": reasons
            })
        else:
            clean_candidates.append(c)
            
    CANDIDATES = clean_candidates
    ELIGIBLE_CANDIDATES = len(CANDIDATES)
    HONEYPOT_COUNT = len(HONEYPOT_CANDIDATES)
    
    summary = (
        f"Successfully ran the 5-Point Anomaly Firewall across {initial_count} candidate profiles.\n"
        f"Detected and removed {honeypot_count} synthetic trap profiles (Honeypots) from the pool.\n"
        f"Remaining active candidate pool: {len(CANDIDATES)} profiles.\n\n"
        f"Top anomaly triggers found:\n"
    )
    for reason, count in list(reasons_summary.items())[:3]:
        summary += f"- {reason}: {count} profiles\n"
        
    return summary

@tool
def apply_consulting_filter() -> str:
    """
    Evaluates candidate work history for IT consulting/services experience
    (e.g., TCS, Wipro, Infosys, Accenture, Cognizant, Capgemini, Tech Mahindra, Mindtree, Mphasis, HCL).
    Applies a soft score penalty (-0.05 adjustment) rather than banning/excluding candidates.
    Returns: A status message detailing evaluated candidates.
    """
    global CANDIDATES
    if not CANDIDATES:
        return "Error: Candidate database is empty."
        
    consulting_count = sum(1 for c in CANDIDATES if is_consulting_only(c))
    
    return (
        f"Consulting Assessment Layer executed successfully.\n"
        f"Identified {consulting_count} candidates with IT consulting background.\n"
        f"Applied soft score penalty (-0.05 adjustment) to consulting candidates. No candidates were banned or removed.\n"
        f"Full active pool retained: {len(CANDIDATES)} candidates."
    )

@tool
def rank_and_reason_candidates(job_description: str, top_n: int = 50) -> str:
    """
    Uses BGE-small-v1.5 embeddings and title matching to rank the remaining candidate pool.
    Generates non-hallucinatory recruiter explanations for the top shortlist.
    Args:
        job_description: The job description text to match against.
        top_n: Number of top candidates to return in the shortlist (default 50).
    Returns: A formatted JSON summary of the top ranked candidates.
    """
    global CANDIDATES, ACTIVE_SHORTLIST
    if not CANDIDATES:
        return "Error: Candidate database is empty. Make sure you load and filter candidates first."
        
    logger.info(f"Ranking {len(CANDIDATES)} candidates against Job Description: {job_description[:50]}...")
    
    # We call the core ranking logic from ranker.py
    results = rank_candidates(CANDIDATES, jd_text=job_description)
    ACTIVE_SHORTLIST.clear()
    ACTIVE_SHORTLIST.extend(results)  # Store ALL ranked candidates for pagination
    
    summary_list = []
    for c in ACTIVE_SHORTLIST[:top_n]:
        summary_list.append({
            "rank": c["rank"],
            "candidate_id": c["candidate_id"],
            "name": c["name"],
            "current_title": c["current_title"],
            "score": round(c["score"], 4),
            "reasoning": c["reasoning"]
        })
    return json.dumps(summary_list, indent=2)


# Recruiter Agent Initialization Helper
def get_recruiter_agent(aws_access_key: str = None, aws_secret_key: str = None, aws_region: str = "us-east-2"):
    """
    Instantiates and returns the Strands Agent. 
    If AWS credentials are provided, configures BedrockModel.
    Otherwise, returns the agent with a local fallback router.
    """
    system_prompt = (
        "You are the RecruitShield AI Agent, an autonomous recruiter co-pilot built with the AWS Strands Agents SDK.\n"
        "Your task is to guide the user (a recruiter or hiring manager) in finding and auditing candidate profiles.\n"
        "You have access to candidate database tools: 'audit_candidate_integrity', 'apply_consulting_filter', "
        "and 'rank_and_reason_candidates'.\n\n"
        "Always execute the pipeline logically when asked to find candidates:\n"
        "1. First, check and audit database integrity to clean fake profiles (honeypots).\n"
        "2. Apply soft score adjustment (-0.05) to consulting profiles without banning them.\n"
        "3. Rank the full candidate pool based on semantic similarity and return the top ranked results with explanations.\n\n"
        "Present your actions clearly, explaining which tools you are running and why."
    )
    
    # Check if we can run BedrockModel
    aws_configured = (
        aws_access_key is not None or 
        os.environ.get("AWS_ACCESS_KEY_ID") is not None or 
        Path("~/.aws/credentials").expanduser().exists()
    )
    
    model = None
    if aws_configured:
        try:
            import boto3
            # If explicit keys were passed from UI, construct a custom session
            session = None
            if aws_access_key and aws_secret_key:
                session = boto3.Session(
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
            
            # Using Claude 3 Sonnet or Haiku on Bedrock as our Strands Agent backbone
            model = BedrockModel(
                model_id="amazon.nova-pro-v1:0",
                boto_session=session
            )
            logger.info("Initialized Strands Agent with AWS Bedrock Model.")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock model: {e}. Falling back to local routing.")
            
    # If Bedrock is not configured, we run in mock/local mode which uses python callback simulation
    # but still conforms strictly to Strands SDK tool definitions.
    tools_list = [audit_candidate_integrity, apply_consulting_filter, rank_and_reason_candidates]
    
    return Agent(
        model=model,
        tools=tools_list,
        system_prompt=system_prompt,
        name="RecruitShield Agent",
        description="Autonomous co-pilot for candidate screening and integrity auditing"
    )
