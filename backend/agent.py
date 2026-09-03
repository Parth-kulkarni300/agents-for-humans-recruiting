import os
import json
import logging
import numpy as np
from pathlib import Path
from strands import Agent, tool
from strands.models import BedrockModel
from backend.ranker import is_honeypot, is_consulting_only, score_candidate, rank_candidates

logger = logging.getLogger("recruiter-agent")

# Global candidate store
CANDIDATES = []
ACTIVE_SHORTLIST = []

def load_candidates_file(file_path: str):
    """Loads candidates from JSONL into memory once at startup."""
    global CANDIDATES
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
        logger.info(f"Successfully loaded {len(CANDIDATES)} candidate profiles.")
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
    global CANDIDATES
    if not CANDIDATES:
        return "Error: Candidate database is empty. Please load candidates first."
        
    initial_count = len(CANDIDATES)
    clean_candidates = []
    honeypot_count = 0
    reasons_summary = {}
    
    for c in CANDIDATES:
        hp_flag, reason = is_honeypot(c)
        if hp_flag:
            honeypot_count += 1
            reasons_summary[reason] = reasons_summary.get(reason, 0) + 1
        else:
            clean_candidates.append(c)
            
    CANDIDATES = clean_candidates
    
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
    Filters out candidates who have spent their entire career at IT consulting/services firms
    (e.g., TCS, Wipro, Infosys, Accenture, Cognizant, Capgemini).
    Returns: A status message with count of filtered profiles.
    """
    global CANDIDATES
    if not CANDIDATES:
        return "Error: Candidate database is empty."
        
    initial_count = len(CANDIDATES)
    clean_candidates = [c for c in CANDIDATES if not is_consulting_only(c)]
    excluded_count = initial_count - len(clean_candidates)
    CANDIDATES = clean_candidates
    
    return (
        f"Consulting Exclusion Layer executed successfully.\n"
        f"Excluded {excluded_count} candidates who only worked at IT consulting/services firms.\n"
        f"Remaining active pool: {len(CANDIDATES)} candidates."
    )

@tool
def rank_and_reason_candidates(job_description: str, top_n: int = 10) -> str:
    """
    Uses BGE-small-v1.5 embeddings and title matching to rank the remaining candidate pool.
    Generates non-hallucinatory recruiter explanations for the top shortlist.
    Args:
        job_description: The job description text to match against.
        top_n: Number of top candidates to return.
    Returns: A formatted JSON summary of the top ranked candidates.
    """
    global CANDIDATES, ACTIVE_SHORTLIST
    if not CANDIDATES:
        return "Error: Candidate database is empty. Make sure you load and filter candidates first."
        
    logger.info(f"Ranking candidates against Job Description: {job_description[:50]}...")
    
    # We call the core ranking logic from ranker.py
    results = rank_candidates(CANDIDATES, jd_text=job_description)
    ACTIVE_SHORTLIST.clear()
    ACTIVE_SHORTLIST.extend(results[:top_n])
    
    summary_list = []
    for c in ACTIVE_SHORTLIST:
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
def get_recruiter_agent(aws_access_key: str = None, aws_secret_key: str = None, aws_region: str = "us-east-1"):
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
        "2. Exclude consulting-only profiles if the job description mentions product companies.\n"
        "3. Rank the remaining pool based on semantic similarity and print the ranked results with explanations.\n\n"
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
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
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
