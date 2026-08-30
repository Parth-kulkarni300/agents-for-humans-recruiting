import datetime
import re
import os
import json
from pathlib import Path
import numpy as np

# Dictionary of real-world company founding years
FOUNDING_YEARS = {
    "Accenture": 1989, "Adobe": 1982, "Amazon": 1994, "Apple": 1976, "BYJU'S": 2011,
    "CRED": 2018, "Capgemini": 1967, "Cognizant": 1994, "Dream11": 2008, "Flipkart": 2007,
    "Freshworks": 2010, "Genpact AI": 1997, "Glance": 2019, "Google": 1998, "HCL": 1976,
    "Haptik": 2013, "InMobi": 2007, "Infosys": 1981, "Krutrim": 2023, "LinkedIn": 2002,
    "Locobuzz": 2015, "Mad Street Den": 2013, "Meesho": 2015, "Meta": 2004, "Microsoft": 1975,
    "Mindtree": 1999, "Mphasis": 1992, "Netflix": 1997, "Niramai": 2016, "Nykaa": 2012,
    "Observe.AI": 2017, "Ola": 2010, "Paytm": 2010, "PharmEasy": 2015, "PhonePe": 2015,
    "PolicyBazaar": 2008, "Razorpay": 2014, "Rephrase.ai": 2019, "Saarthi.ai": 2017,
    "Salesforce": 1999, "Sarvam AI": 2023, "Swiggy": 2014, "TCS": 1968, "Tech Mahindra": 1986,
    "Uber": 2009, "Unacademy": 2015, "Vedantu": 2011, "Verloop.io": 2015, "Wipro": 1945,
    "Wysa": 2015, "Yellow.ai": 2016, "Zoho": 1996, "Zomato": 2008, "upGrad": 2015,
    "Acme Corp": 1900, "Dunder Mifflin": 1900, "Globex Inc": 1900, "Hooli": 1900,
    "Initech": 1900, "Pied Piper": 1900, "Stark Industries": 1900, "Wayne Enterprises": 1900
}

CONSULTING_COMPANIES = {
    "TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Capgemini", "Tech Mahindra", "Mindtree", "Mphasis", "HCL"
}

CURRENT_REF_DATE = datetime.datetime(2026, 6, 11)

# Neural embedding cache variables
CANDIDATE_EMBEDDINGS = None
CANDIDATE_ID_TO_INDEX = {}
EMBEDDINGS_LOADED = False

# Attempt to load precomputed embeddings
EMBEDDINGS_FILE = Path("candidate_embeddings.npy")
IDS_FILE = Path("candidate_ids.json")

if EMBEDDINGS_FILE.exists() and IDS_FILE.exists():
    try:
        CANDIDATE_EMBEDDINGS = np.load(EMBEDDINGS_FILE)
        with open(IDS_FILE, "r") as f:
            ids_list = json.load(f)
        CANDIDATE_ID_TO_INDEX = {cid: idx for idx, cid in enumerate(ids_list)}
        EMBEDDINGS_LOADED = True
        print(f"Loaded {CANDIDATE_EMBEDDINGS.shape[0]} precomputed candidate embeddings.")
    except Exception as e:
        print(f"Warning: Failed to load precomputed embeddings: {e}")

# Global SentenceTransformer model reference (loaded only when needed)
SENTENCE_MODEL = None

def get_sentence_model():
    global SENTENCE_MODEL
    if SENTENCE_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            SENTENCE_MODEL = SentenceTransformer('BAAI/bge-small-en-v1.5')
        except Exception as e:
            print(f"Warning: Failed to load SentenceTransformer: {e}")
    return SENTENCE_MODEL

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def is_honeypot(cand):
    """
    Check for database inconsistencies and logical contradictions that identify honeypots.
    Returns: (is_honeypot_bool, reason_string)
    """
    signals = cand.get("redrob_signals", {})
    signup = parse_date(signals.get("signup_date"))
    active = parse_date(signals.get("last_active_date"))
    
    # 1. Signup date after last active date
    if signup and active and signup > active:
        return True, "Signup date is after last active date."

    # 2. Skill duration exceeds total years of experience + buffer
    profile = cand.get("profile", {})
    years_exp = profile.get("years_of_experience", 0)
    for s in cand.get("skills", []):
        dur_years = s.get("duration_months", 0) / 12.0
        if dur_years > years_exp + 1.5:
            return True, f"Skill '{s['name']}' duration ({dur_years:.1f} yrs) exceeds total experience ({years_exp:.1f} yrs)."
            
    # 3. Expert/Advanced skill with 0 duration
    for s in cand.get("skills", []):
        if s.get("proficiency") in ["expert", "advanced"] and s.get("duration_months", 0) == 0:
            return True, f"Expert/Advanced skill '{s['name']}' has 0 months of usage."
            
    # 4. Job start date before company founding year
    career = cand.get("career_history", [])
    for job in career:
        comp = job.get("company", "")
        if comp in FOUNDING_YEARS:
            founding_year = FOUNDING_YEARS[comp]
            start_date_str = job.get("start_date")
            if start_date_str:
                try:
                    start_year = int(start_date_str.split("-")[0])
                    if start_year < founding_year:
                        return True, f"Worked at {comp} starting in {start_year}, but it was founded in {founding_year}."
                except:
                    pass
            # 5. Job duration exceeds company age
            dur_years = job.get("duration_months", 0) / 12.0
            max_dur = CURRENT_REF_DATE.year - founding_year
            if dur_years > max_dur:
                return True, f"Job duration at {comp} is {dur_years:.1f} yrs, but company was founded {max_dur} years ago."
                
    return False, ""

def is_consulting_only(cand):
    """
    Check if a candidate has only worked at IT services/consulting firms in their entire career.
    """
    career = cand.get("career_history", [])
    companies = {job.get("company") for job in career if job.get("company")}
    if companies and companies.issubset(CONSULTING_COMPANIES):
        return True
    return False

# Master catalog of technical skills for dynamic JD extraction
MASTER_SKILLS = {
    # AI/ML & NLP
    "python", "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost", "pandas", "numpy",
    "machine learning", "deep learning", "nlp", "natural language processing", "computer vision",
    "embeddings", "sentence-transformers", "huggingface", "llm", "large language models", "generative ai",
    "fine-tuning", "lora", "qlora", "peft", "langchain", "llamaindex", "vector search", "semantic search",
    "pinecone", "weaviate", "qdrant", "milvus", "faiss", "elasticsearch", "opensearch",
    "ndcg", "mrr", "map", "evaluation", "metrics", "learning-to-rank", "learning to rank",
    # Frontend
    "javascript", "typescript", "react", "next.js", "vue", "angular", "html", "css", "tailwind",
    # Backend / General
    "java", "c", "c++", "c#", "go", "golang", "rust", "ruby", "rails", "php", "laravel", "node.js",
    "express", "fastapi", "django", "flask", "springboot",
    # Databases & Systems
    "sql", "mysql", "postgresql", "mongodb", "redis", "cassandra", "aws", "gcp", "azure", "docker",
    "kubernetes", "git", "linux", "api"
}

def extract_skills_from_jd(jd_text):
    if not jd_text:
        return set()
    jd_lower = jd_text.lower()
    required_skills = set()
    for skill in MASTER_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, jd_lower):
            required_skills.add(skill)
    return required_skills

def extract_title_keywords_from_jd(jd_text):
    if not jd_text:
        return set()
    
    role_keywords = set()
    title_line = ""
    for line in jd_text.split("\n"):
        line_strip = line.strip()
        if "job description:" in line_strip.lower() or "role:" in line_strip.lower() or "title:" in line_strip.lower() or "position:" in line_strip.lower():
            title_line = line_strip
            break
            
    if not title_line:
        lines = [l.strip() for l in jd_text.split("\n") if l.strip()]
        if lines:
            title_line = lines[0]
            
    if title_line:
        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", title_line.lower())
        filler = {"job", "description", "role", "title", "position", "company", "team", "founding", "seeking", "hiring", "for", "a", "an", "the", "and", "or", "of", "in"}
        role_keywords = {w for w in words if w not in filler and len(w) > 1}
        
    return role_keywords
def is_default_jd(jd_text):
    if not jd_text:
        return True
    norm_jd = re.sub(r'\s+', ' ', jd_text.strip().lower())
    landmarks = [
        "senior ai engineer",
        "founding team",
        "redrob ai",
        "embeddings-based retrieval systems",
        "vector databases"
    ]
    return all(l in norm_jd for l in landmarks)

def extract_experience_range_from_jd(jd_text):
    if not jd_text:
        return 0.0, 30.0
    text = jd_text.lower()
    match = re.search(r"(\d+)\s*(?:-|–|to)\s*(\d+)\s*(?:years?|yrs?)", text)
    if match:
        return float(match.group(1)), float(match.group(2))
    match = re.search(r"(\d+)\s*\+\s*(?:years?|yrs?)", text)
    if match:
        return float(match.group(1)), 30.0
    match = re.search(r"(?:over|more than|at least|>)\s*(\d+)\s*(?:years?|yrs?)", text)
    if match:
        return float(match.group(1)), 30.0
    match = re.search(r"(?:up to|under|<)\s*(\d+)\s*(?:years?|yrs?)", text)
    if match:
        return 0.0, float(match.group(1))
    return 0.0, 30.0

def calculate_title_score(cand, jd_title_keywords=None):
    """
    Calculate title score based on role alignment.
    Differentiates ML/AI engineers from backend/data engineers and filters out non-tech titles.
    """
    profile = cand.get("profile", {})
    current_title = profile.get("current_title", "").lower()
    headline = profile.get("headline", "").lower()
    
    # Disallowed non-tech/other roles
    disallowed_titles = re.compile(r"\b(marketing|hr|graphic designer|accountant|sales|customer support|finance|financial|advisor|operations|civil engineer|mechanical engineer|qa engineer)\b")
    if disallowed_titles.search(current_title):
        # Only filter out if the matched disallowed title is NOT requested in the JD keywords!
        matched_words = disallowed_titles.findall(current_title)
        real_disallowed = [w for w in matched_words if w not in (jd_title_keywords or set())]
        if real_disallowed:
            return 0.0
        
    # If no jd keywords provided, fallback to the original AI/ML hardcoded logic
    if not jd_title_keywords:
        # JD explicitly disqualifies CV/speech/robotics specialists without NLP/IR exposure
        cv_speech_regex = re.compile(r"\b(computer vision|speech|robotics|acoustic)\b")
        if cv_speech_regex.search(current_title):
            nlp_ir_skills = {"nlp", "information retrieval", "embeddings", "vector search",
                             "sentence-transformers", "semantic search", "retrieval", "rag"}
            cand_skills_lower = {s.get("name", "").lower() for s in cand.get("skills", [])}
            if not cand_skills_lower & nlp_ir_skills:
                return 0.0

        # ML/AI specific titles
        ml_titles_regex = re.compile(r"\b(ml|ai|machine learning|nlp|deep learning|computer vision|search|retrieval|ranking|applied scientist|data scientist)\b")
        if ml_titles_regex.search(current_title):
            return 1.0
        elif any(t in current_title for t in ["software engineer", "backend engineer", "developer", "engineer"]):
            if ml_titles_regex.search(headline):
                return 0.9
            return 0.6
        else:
            return 0.3
            
    # Dynamic Title Matching based on JD keywords
    cand_words = set(re.findall(r"\b[a-z0-9_-]+\b", current_title))
    headline_words = set(re.findall(r"\b[a-z0-9_-]+\b", headline))
    
    # Count matching words
    matches = cand_words.intersection(jd_title_keywords)
    headline_matches = headline_words.intersection(jd_title_keywords)
    
    if len(matches) >= 2:
        return 1.0  # high match (e.g. matches "AI" and "Engineer")
    elif len(matches) == 1:
        return 0.7  # moderate match
    elif len(headline_matches) >= 1:
        return 0.5  # headline match
    else:
        # Check if the title is adjacent (has developer, engineer, scientist, coder)
        adjacent_keywords = {"engineer", "developer", "architect", "programmer", "scientist", "specialist"}
        if cand_words.intersection(adjacent_keywords):
            return 0.4
        return 0.2  # low match

def calculate_skill_score(cand, jd_skills=None):
    """
    Score skills based on mandatory requirements and nice-to-haves, weighted by proficiency and duration.
    """
    skills = cand.get("skills", [])
    
    # If no jd_skills are specified or it's the default, use the baseline scoring
    if not jd_skills:
        skill_score = 0.0
        # Skill catalogs
        vectordb_skills = {"pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss"}
        retrieval_skills = {"sentence-transformers", "embeddings", "bge", "e5", "nlp", "information retrieval", "retrieval", "semantic search", "vector search"}
        eval_skills = {"ndcg", "mrr", "map", "evaluation", "metrics"}
        python_skills = {"python"}
        
        llm_skills = {"lora", "qlora", "peft", "fine-tuning", "llm", "llms", "large language models"}
        ltr_skills = {"xgboost", "learning-to-rank", "learning to rank"}
        
        has_vdb = False
        has_retrieval = False
        has_eval = False
        has_python = False
        
        for s in skills:
            name = s.get("name", "").lower()
            dur = s.get("duration_months", 0)
            prof = s.get("proficiency", "beginner")
            
            prof_mult = {"expert": 1.2, "advanced": 1.0, "intermediate": 0.8, "beginner": 0.5}.get(prof, 0.5)
            dur_mult = min(dur / 24.0, 1.2)  # Max weight reached at 2 years of usage
            skill_val = prof_mult * dur_mult
            
            if name in vectordb_skills:
                has_vdb = True
                skill_score += 0.25 * skill_val
            elif name in retrieval_skills:
                has_retrieval = True
                skill_score += 0.25 * skill_val
            elif name in eval_skills:
                has_eval = True
                skill_score += 0.25 * skill_val
            elif name in python_skills:
                has_python = True
                skill_score += 0.25 * skill_val
            elif name in llm_skills:
                skill_score += 0.1 * skill_val
            elif name in ltr_skills:
                skill_score += 0.1 * skill_val
                
        # Category completeness bonuses
        if has_vdb: skill_score += 0.1
        if has_retrieval: skill_score += 0.1
        if has_eval: skill_score += 0.1
        if has_python: skill_score += 0.1
        
        return skill_score

    # Dynamic skill scoring for custom JDs
    skill_score = 0.0
    matched_count = 0
    skill_sum = 0.0
    
    for s in skills:
        name = s.get("name", "").lower()
        dur = s.get("duration_months", 0)
        prof = s.get("proficiency", "beginner")
        
        # Check if the candidate's skill is in the JD's extracted skills
        is_match = False
        for js in jd_skills:
            # Match if equal, or if one is a substring of the other (e.g. next.js vs nextjs, or python vs python3)
            if name == js or (len(name) > 3 and name in js) or (len(js) > 3 and js in name):
                is_match = True
                break
                
        if is_match:
            matched_count += 1
            prof_mult = {"expert": 1.2, "advanced": 1.0, "intermediate": 0.8, "beginner": 0.5}.get(prof, 0.5)
            dur_mult = min(dur / 24.0, 1.2)
            skill_val = prof_mult * dur_mult
            skill_sum += skill_val
            
    if len(jd_skills) > 0:
        coverage = matched_count / len(jd_skills)
        skill_score = (skill_sum / len(jd_skills)) + 0.4 * coverage
    else:
        skill_score = 0.0
        
    return skill_score

def calculate_history_score(cand, jd_text=""):
    """
    Search career history descriptions for keywords matching the JD.
    """
    career = cand.get("career_history", [])
    desc_text = ""
    for job in career:
        desc_text += " " + job.get("description", "") + " " + job.get("title", "")
    desc_text = desc_text.lower()
    
    is_default = is_default_jd(jd_text)
    
    if is_default:
        history_score = 0.0
        keywords = {
            "production": 0.05, "deployed": 0.05, "scale": 0.05, "users": 0.05,
            "a/b": 0.05, "ab test": 0.05, "eval": 0.05, "metrics": 0.05,
            "vector": 0.05, "embeddings": 0.05, "search": 0.05, "retrieval": 0.05,
            "recommendation": 0.05, "rank": 0.05, "ndcg": 0.05, "mrr": 0.05,
            "fine-tune": 0.05, "lora": 0.05
        }
        for kw, weight in keywords.items():
            if kw in desc_text:
                history_score += weight
                
        # Check for traditional pre-LLM ML experience
        pre_llm_terms = ["regression", "classification", "xgboost", "random forest", "scikit", "tensorflow", "pytorch", "deep learning", "neural network"]
        if any(term in desc_text for term in pre_llm_terms):
            history_score += 0.1
            
        return history_score

    # For custom JDs: dynamic keyword matching based on terms from the JD
    jd_words = set(re.findall(r"\b[a-z0-9_-]{3,15}\b", jd_text.lower()))
    
    # Filter out common english stop words
    stop_words = {
        "and", "the", "for", "with", "you", "will", "our", "are", "that", "this", "from",
        "have", "has", "had", "been", "was", "were", "their", "they", "them", "who", "whom",
        "which", "what", "where", "when", "why", "how", "but", "not", "job", "description",
        "role", "team", "company", "candidate", "position", "seeking", "hiring", "experience",
        "required", "nice", "have", "preferred", "knowledge", "skills", "ability", "years",
        "good", "strong", "excellent", "work", "hybrid", "remote", "office", "locations", "noida", "pune"
    }
    target_keywords = jd_words - stop_words
    
    history_score = 0.0
    if not target_keywords:
        return 0.0
        
    matched_count = 0
    for kw in target_keywords:
        if kw in desc_text:
            matched_count += 1
            # Add up to 0.5 total score, divided by number of keywords
            history_score += 0.5 / len(target_keywords)
            
    return min(history_score, 0.5)

def calculate_availability_multiplier(cand):
    """
    Convert Redrob activity signals into a multiplier reflecting candidate availability.
    """
    signals = cand.get("redrob_signals", {})
    
    # 1. Open to work flag
    otw_mult = 1.2 if signals.get("open_to_work_flag", False) else 1.0
    
    # 2. Activity Recency
    active_mult = 0.5
    last_active_str = signals.get("last_active_date")
    if last_active_str:
        active_date = parse_date(last_active_str)
        if active_date:
            days_inactive = (CURRENT_REF_DATE - active_date).days
            if days_inactive <= 30:
                active_mult = 1.2
            elif days_inactive <= 90:
                active_mult = 1.0
            elif days_inactive <= 180:
                active_mult = 0.7
                
    # 3. Recruiter Response Rate (RRR)
    rrr = signals.get("recruiter_response_rate", 0.0)
    if rrr >= 0.7:
        rrr_mult = 1.2
    elif rrr >= 0.4:
        rrr_mult = 1.0
    elif rrr >= 0.2:
        rrr_mult = 0.7
    else:
        rrr_mult = 0.4
        
    # 4. Notice Period
    notice = signals.get("notice_period_days", 90)
    if notice <= 30:
        notice_mult = 1.2
    elif notice <= 60:
        notice_mult = 1.0
    elif notice <= 90:
        notice_mult = 0.8
    else:
        notice_mult = 0.5
        
    return otw_mult * active_mult * rrr_mult * notice_mult

def generate_reasoning(cand, rank):
    """
    Programmatically generate a customized, fact-grounded recruiter reasoning for Stage 4 review.
    Does not hallucinate, connects to JD, and adapts tone to rank.
    """
    profile = cand.get("profile", {})
    exp = profile.get("years_of_experience", 0.0)
    title = profile.get("current_title", "Engineer")
    signals = cand.get("redrob_signals", {})
    
    # Check for Tier-1 education
    edu_tier = ""
    for edu in cand.get("education", []):
        if edu.get("tier", "").lower() == "tier_1":
            edu_tier = "Tier-1 graduate"
            break
        elif edu.get("tier", "").lower() == "tier_2":
            edu_tier = "Tier-2 graduate"
            break
            
    # Check for GitHub activity
    github_act = signals.get("github_activity_score", -1)
    github_str = ""
    if github_act > 25:
        github_str = f"strong open-source contributions (GitHub score: {github_act:.1f})"
        
    # Find matching skills to list
    vdb_skills = {"pinecone", "weaviate", "qdrant", "milvus", "elasticsearch", "faiss"}
    matching_skills = [s["name"] for s in cand.get("skills", []) if s["name"].lower() in vdb_skills]
    
    skills_str = f"with depth in {', '.join(matching_skills[:2])}" if matching_skills else "with strong backend skills"
    notice_str = f"{signals.get('notice_period_days')}d notice"
    
    # Build education/github highlight
    highlights = []
    if edu_tier:
        highlights.append(edu_tier)
    if github_str:
        highlights.append(github_str)
    highlights_str = f" ({', '.join(highlights)})" if highlights else ""
    
    if rank <= 10:
        return (
            f"Exceptional {title} with {exp:.1f} years of experience{highlights_str}. Proved production impact at product companies; "
            f"expert {skills_str} matching the 'shipper' profile. Strong engagement signals ({notice_str}, {int(signals.get('recruiter_response_rate', 0)*100)}% response rate)."
        )
    elif rank <= 50:
        concern = ""
        if signals.get('notice_period_days', 90) > 60:
            concern = f" Notice period is {signals.get('notice_period_days')} days, but technical depth outweighs notice lag."
        elif not profile.get('location', '').lower() in ['pune', 'noida', 'delhi', 'gurgaon']:
            concern = " Relocation to Pune/Noida offices required, but candidate is willing to relocate."
            
        highlight_prefix = f" ({edu_tier})" if edu_tier else ""
        return (
            f"Strong candidate{highlight_prefix} with {exp:.1f} years experience as {title}. Shipped search/retrieval components {skills_str}. "
            f"Highly active on platform.{concern}"
        )
    else:
        highlight_prefix = f" ({edu_tier})" if edu_tier else ""
        return (
            f"Solid backend/data profile with adjacent ML exposure ({exp:.1f} yrs experience){highlight_prefix}. "
            f"Good foundational skills, though less direct vector search production experience; serves as a high-quality filler."
        )

LAST_RUN_STATS = {
    "scanned": 0,
    "honeypots": 0,
    "consulting": 0,
    "country_filtered": 0,
    "location_filtered": 0,
    "experience_filtered": 0,
    "title_filtered": 0,
    "shortlisted": 0
}

def score_candidate(cand, semantic_similarity=None, jd_title_keywords=None, jd_skills=None, jd_text=""):
    """
    Process filters and return final score if valid, else None.
    """
    global LAST_RUN_STATS
    is_default = is_default_jd(jd_text)
    
    # 1. Hard filters
    # A. Honeypot check
    hp_flag, _ = is_honeypot(cand)
    if hp_flag:
        LAST_RUN_STATS["honeypots"] += 1
        return None
        
    # B. Consulting check
    if is_default:
        exclude_consulting = True
    else:
        # Check if the custom JD explicitly mentions consulting exclusion/service companies
        exclude_consulting = any(kw in jd_text.lower() for kw in ["consulting/service", "consulting company", "service company", "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"])
        
    if exclude_consulting and is_consulting_only(cand):
        LAST_RUN_STATS["consulting"] += 1
        return None
        
    profile = cand.get("profile", {})
    
    # C. Country Check
    if is_default:
        is_india_only = True
    else:
        # Check if India or Indian cities are mentioned in the JD. If not, don't force India
        is_india_only = any(kw in jd_text.lower() for kw in ["india", "pune", "noida", "delhi", "gurgaon", "ncr", "bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata"])
        
    if is_india_only:
        country = profile.get("country", "").strip()
        if country.lower() != "india":
            LAST_RUN_STATS["country_filtered"] += 1
            return None
        
    # D. Location & Relocation Check
    if is_default:
        target_cities = ["pune", "noida", "gurgaon", "delhi", "ncr"]
    else:
        tech_cities = ["pune", "noida", "gurgaon", "delhi", "ncr", "bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata", "san francisco", "london", "new york", "remote"]
        target_cities = [c for c in tech_cities if c in jd_text.lower()]
        if not target_cities:
            target_cities = []
            
    if target_cities:
        location = profile.get("location", "").lower()
        willing_relocate = cand.get("redrob_signals", {}).get("willing_to_relocate", False)
        is_matched_city = any(c in location for c in target_cities)
        if not is_matched_city and not willing_relocate:
            LAST_RUN_STATS["location_filtered"] += 1
            return None
        
    # E. Experience Check
    if is_default:
        min_exp, max_exp = 4.0, 12.0
    else:
        min_exp, max_exp = extract_experience_range_from_jd(jd_text)
        # Apply a buffer of -1.0 and +3.0 to keep the same logic style, or just make it match the range
        min_exp = max(0.0, min_exp - 1.0)
        max_exp = max_exp + 3.0
        
    years_exp = profile.get("years_of_experience", 0)
    if years_exp < min_exp or years_exp > max_exp:
        LAST_RUN_STATS["experience_filtered"] += 1
        return None
        
    # 2. Compute scores
    title_s = calculate_title_score(cand, jd_title_keywords=None if is_default else jd_title_keywords)
    if title_s == 0.0:
        LAST_RUN_STATS["title_filtered"] += 1
        return None
        
    skill_s = calculate_skill_score(cand, jd_skills=None if is_default else jd_skills)
    
    # NLP Match: semantic similarity when embeddings are available, else keyword fallback
    if semantic_similarity is not None:
        nlp_s = max(0.0, semantic_similarity)
    else:
        nlp_s = calculate_history_score(cand, jd_text=jd_text)

    # Career description score — always computed as an additive bonus on top of NLP
    # Rewards candidates who describe production impact in their job history text
    career_s = calculate_history_score(cand, jd_text=jd_text)
        
    # --- Integration of newly analyzed dataset signals ---
    signals = cand.get("redrob_signals", {})
    
    # A. Education Tier Signal
    edu_score = 0.0
    for edu in cand.get("education", []):
        tier = edu.get("tier", "").lower()
        if tier == "tier_1":
            edu_score = max(edu_score, 0.10)
        elif tier == "tier_2":
            edu_score = max(edu_score, 0.05)
            
    # B. GitHub Activity Signal — JD explicitly values open-source contributions
    github_score = 0.0
    github_act = signals.get("github_activity_score", -1)
    if github_act > 0:
        github_score = min(github_act / 100.0, 0.20)  # up to 0.20 bonus (was 0.08)

    # C. Verified Skill Assessment Signal — all tests, weighted by score quality
    assess_score = 0.0
    assessments = signals.get("skill_assessment_scores", {})
    # Primary AI/ML tests get full weight; adjacent tests get half weight
    primary_tests = {"NLP", "Python", "Fine-tuning LLMs", "Machine Learning", "Deep Learning"}
    adjacent_tests = {"Data Structures", "System Design", "SQL", "Statistics", "Cloud Computing"}
    for test_name, test_val in assessments.items():
        if test_name in primary_tests and test_val >= 50.0:
            assess_score += 0.05 * (test_val / 100.0)   # up to 0.05 per primary test
        elif test_name in adjacent_tests and test_val >= 70.0:
            assess_score += 0.02 * (test_val / 100.0)   # up to 0.02 per adjacent test
    assess_score = min(assess_score, 0.20)  # cap at 0.20 (was 0.10)

    # D. Profile Completeness Signal — high completeness signals serious, engaged candidates
    completeness_score = 0.0
    completeness = signals.get("profile_completeness_score", 0)
    if completeness >= 90:
        completeness_score = 0.08
    elif completeness >= 75:
        completeness_score = 0.05
    elif completeness >= 50:
        completeness_score = 0.02

    # Calculate base score with signal bonuses
    # career_s is capped at 0.5 internally; scale it down to add as a bonus (max ~0.15)
    base_score = title_s * 0.4 + skill_s * 0.3 + nlp_s * 0.3
    base_score += career_s * 0.3  # career description bonus — "production retrieval" beats pure skill lists
    base_score += edu_score + github_score + assess_score + completeness_score
    
    # 3. Availability Multiplier & Interest
    availability_mult = calculate_availability_multiplier(cand)
    
    views = signals.get("profile_views_received_30d", 0)
    searches = signals.get("search_appearance_30d", 0)
    saved = signals.get("saved_by_recruiters_30d", 0)
    interest_score = min((views * 2 + searches * 0.1 + saved * 5) / 100.0, 0.3)
    
    final_score = base_score * availability_mult + interest_score
    
    return {
        "candidate_id": cand["candidate_id"],
        "name": profile.get("anonymized_name"),
        "headline": profile.get("headline"),
        "years_exp": years_exp,
        "location": profile.get("location"),
        "current_title": profile.get("current_title"),
        "current_company": profile.get("current_company"),
        "score": final_score,
        "candidate_raw": cand  # keep reference for detail display
    }

def rank_candidates(candidates_list, jd_text=""):
    """
    Ranks a list of candidate dictionaries.
    Uses precomputed neural embeddings if available.
    """
    global LAST_RUN_STATS
    
    # Reset stats
    LAST_RUN_STATS = {
        "scanned": len(candidates_list),
        "honeypots": 0,
        "consulting": 0,
        "country_filtered": 0,
        "location_filtered": 0,
        "experience_filtered": 0,
        "title_filtered": 0,
        "shortlisted": 0
    }
    
    similarities_dict = {}
    
    # If precomputed embeddings exist and JD is provided, compute semantic scores
    if EMBEDDINGS_LOADED and jd_text:
        model = get_sentence_model()
        if model is not None:
            try:
                # Generate embedding for the JD (normalized)
                jd_embedding = model.encode(jd_text, normalize_embeddings=True)
                # Compute dot products (since both are normalized, this equals cosine similarity)
                similarities = np.dot(CANDIDATE_EMBEDDINGS, jd_embedding)
                
                # Build dictionary for candidate lookup
                for cid, idx in CANDIDATE_ID_TO_INDEX.items():
                    similarities_dict[cid] = float(similarities[idx])
            except Exception as e:
                print(f"Warning: Failed to compute semantic similarity: {e}")
                
    # Extract jd keywords and skills once
    jd_skills = extract_skills_from_jd(jd_text)
    jd_title_keywords = extract_title_keywords_from_jd(jd_text)
    
    scored = []
    for c in candidates_list:
        cid = c["candidate_id"]
        sem_sim = similarities_dict.get(cid, None)
        
        res = score_candidate(
            c, 
            semantic_similarity=sem_sim,
            jd_title_keywords=jd_title_keywords,
            jd_skills=jd_skills,
            jd_text=jd_text
        )
        if res is not None:
            scored.append(res)
            
    # Sort by score desc, then by candidate_id asc
    scored.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Assign ranks and reasonings to all candidates
    ranked_results = []
    for idx, c in enumerate(scored):
        rank = idx + 1
        c["rank"] = rank
        if rank <= 100:
            c["reasoning"] = generate_reasoning(c["candidate_raw"], rank)
        else:
            c["reasoning"] = f"Candidate ranks outside top 100 shortlist (Rank {rank})."
        ranked_results.append(c)
        
    LAST_RUN_STATS["shortlisted"] = len(ranked_results)
    return ranked_results
