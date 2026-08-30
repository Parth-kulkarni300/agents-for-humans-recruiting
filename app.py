import streamlit as st
import json
import os
import re
import hashlib
import pandas as pd
import numpy as np
import ranker
import importlib
importlib.reload(ranker)
from pathlib import Path
import plotly.express as px


# Configure page layout and style
st.set_page_config(
    page_title="Redrob AI Ranker | Talent Acquisition Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS injection
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        /* Sidebar styling overrides */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #07090E 0%, #0F1420 100%) !important;
            border-right: 1px solid rgba(56, 189, 248, 0.12) !important;
            box-shadow: 5px 0 25px rgba(0, 0, 0, 0.6) !important;
        }
        
        /* Customize sidebar scrollbar */
        [data-testid="stSidebar"]::-webkit-scrollbar {
            width: 4px;
        }
        [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
            background: rgba(56, 189, 248, 0.2);
            border-radius: 2px;
        }
        [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
            background: #00E5FF;
        }
        
        /* Sidebar Labels Styling */
        [data-testid="stSidebar"] label[data-testid="stWidgetLabel"] p {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            color: #E5E7EB !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            font-size: 0.8rem !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stTextInput"] input,
        [data-testid="stSidebar"] [data-testid="stTextarea"] textarea {
            background-color: rgba(15, 23, 42, 0.5) !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            color: #F3F4F6 !important;
            border-radius: 8px !important;
            transition: all 0.3s ease !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stTextInput"] input:focus,
        [data-testid="stSidebar"] [data-testid="stTextarea"] textarea:focus {
            border-color: #00E5FF !important;
            box-shadow: 0 0 12px rgba(0, 229, 255, 0.3) !important;
            background-color: rgba(15, 23, 42, 0.7) !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background-color: rgba(15, 23, 42, 0.3) !important;
            border: 1px dashed rgba(56, 189, 248, 0.25) !important;
            border-radius: 8px !important;
            padding: 12px !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
            background-color: rgba(56, 189, 248, 0.1) !important;
            color: #38BDF8 !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 6px !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
            background-color: rgba(0, 229, 255, 0.15) !important;
            color: #00E5FF !important;
            border-color: #00E5FF !important;
            box-shadow: 0 0 12px rgba(0, 229, 255, 0.25) !important;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: #0B0E14;
        }
        ::-webkit-scrollbar-thumb {
            background: #1E293B;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #38BDF8;
        }
        
        /* Global Streamlit elements overrides */
        .stApp {
            background-color: #0B0E14;
        }
        
        /* Streamlit Tab Styling Override */
        button[data-baseweb="tab"] {
            font-family: 'Outfit', sans-serif !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
            color: #9CA3AF !important;
            background-color: transparent !important;
            border: none !important;
            padding: 10px 20px !important;
            transition: all 0.2s ease-in-out !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #38BDF8 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #00E5FF !important;
            border-bottom: 2px solid #00E5FF !important;
            text-shadow: 0 0 10px rgba(0, 229, 255, 0.2);
        }
        
        /* Custom Neon Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            margin: 2px;
        }
        .badge-green {
            background: rgba(16, 185, 129, 0.1);
            color: #34D399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-yellow {
            background: rgba(245, 158, 11, 0.1);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .badge-red {
            background: rgba(239, 68, 68, 0.1);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .badge-blue {
            background: rgba(56, 189, 248, 0.1);
            color: #38BDF8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        
        /* Pulsate Animation */
        @keyframes pulse-glow {
            0% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0.4); }
            70% { box-shadow: 0 0 0 8px rgba(56, 189, 248, 0); }
            100% { box-shadow: 0 0 0 0 rgba(56, 189, 248, 0); }
        }
        .pulse-active {
            width: 8px;
            height: 8px;
            background-color: currentColor;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 8px currentColor;
            animation: pulse-glow 2s infinite;
        }
        
        .main-title {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            background: linear-gradient(90deg, #38BDF8, #00E5FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 3rem;
            margin-bottom: 0.2rem;
            letter-spacing: -0.02em;
        }
        
        .sub-title {
            font-size: 1.05rem;
            color: #9CA3AF;
            margin-bottom: 2rem;
            font-weight: 400;
        }
        
        /* Glassmorphism Metric Cards */
        .metric-card {
            background: linear-gradient(135deg, rgba(21, 30, 46, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
            border-radius: 16px;
            border: 1px solid rgba(56, 189, 248, 0.15);
            padding: 1.5rem;
            text-align: center;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 229, 255, 0.5);
            box-shadow: 0 0 25px rgba(0, 229, 255, 0.25);
        }
        
        .metric-num {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 2.5rem;
            color: #00E5FF;
            margin: 0.1rem 0;
            text-shadow: 0 0 20px rgba(0, 229, 255, 0.3);
        }
        
        .metric-label {
            font-size: 0.8rem;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 600;
        }
        
        /* Timeline style with neon blue glows */
        .timeline-card {
            border-left: 2px solid #38BDF8;
            padding-left: 1.5rem;
            margin-left: 0.5rem;
            margin-bottom: 1.5rem;
            position: relative;
        }
        
        .timeline-dot {
            height: 12px;
            width: 12px;
            background-color: #00E5FF;
            border-radius: 50%;
            position: absolute;
            left: -7px;
            top: 6px;
            box-shadow: 0 0 10px #00E5FF, 0 0 20px #00E5FF;
        }
        
        .timeline-company {
            font-weight: 700;
            font-size: 1.05rem;
            color: #F9FAFB;
        }
        
        .timeline-title {
            font-weight: 500;
            color: #38BDF8;
            font-size: 0.95rem;
        }
        
        .timeline-dates {
            font-size: 0.8rem;
            color: #9CA3AF;
        }
        
        .reasoning-box {
            background-color: rgba(56, 189, 248, 0.06);
            border-left: 4px solid #38BDF8;
            padding: 1.25rem;
            border-radius: 0 12px 12px 0;
            margin-bottom: 1.5rem;
            box-shadow: inset 0 0 15px rgba(56, 189, 248, 0.02);
        }
    </style>
""", unsafe_allow_html=True)

# Preloaded Job Description
DEFAULT_JD = """Job Description: Senior AI Engineer — Founding Team
Company: Redrob AI (Series A AI-native talent intelligence platform)
Location: Pune/Noida, India (Hybrid) | Open to relocation candidates from Tier-1 Indian cities
Employment Type: Full-time
Experience Required: 5–9 years

We need a Senior AI Engineer to own the intelligence layer of Redrob's product.
Required:
- Production experience with embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5)
- Vector databases or hybrid search infrastructure (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS)
- Strong Python code quality
- Design offline/online evaluation frameworks for ranking systems (NDCG, MRR, MAP)
Nice to have:
- LLM fine-tuning experience (LoRA, QLoRA, PEFT)
- Learning-to-rank models (XGBoost-based or neural)

Disqualifiers:
- Pure academic/research environment (no production deployment)
- AI experience consisting primarily of recent (<12 months) LangChain tutorials
- Consulting/service-company background (TCS, Infosys, Wipro, Accenture, Capgemini, Cognizant, etc.) in entire career
- CV/speech/robotics specialists without NLP/IR exposure"""

# Load and cache candidate dataset
@st.cache_data
def load_candidates(file_path, limit=None):
    cands = []
    honeypots_caught = 0
    consulting_filtered = 0
    total_raw = 0
    
    if not os.path.exists(file_path):
        return [], 0, 0, 0
        
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_raw += 1
            cand = json.loads(line)
            
            # Pre-filter checks to count statistics
            hp, _ = ranker.is_honeypot(cand)
            if hp:
                honeypots_caught += 1
            elif ranker.is_consulting_only(cand):
                consulting_filtered += 1
                
            cands.append(cand)
            if limit and len(cands) >= limit:
                break
                
    return cands, total_raw, honeypots_caught, consulting_filtered

def parse_custom_resume_pdf(uploaded_file):
    """
    Parse a custom candidate resume PDF into a candidates.jsonl style dictionary.
    Uses realistic heuristics to extract name, skills, experience, and title.
    Does NOT fabricate IIT education, python test scores, or AI titles.
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        text_parts = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
        text = "\n".join(text_parts)
    except Exception as e:
        st.error(f"Error parsing uploaded candidate PDF: {e}")
        return None
        
    if not text.strip():
        return None
        
    text_lower = text.lower()
    lines = [l.strip() for l in text.split("\n") if l.strip()]
        
    # Heuristic 1: Extract Name from text stream or filename fallback
    name = ""
    job_titles_blacklist = ["engineer", "developer", "designer", "consultant", "manager", "advisor", "analyst", "intern", "architect", "scientist", "lead", "senior", "junior"]
    if lines:
        for line in lines:
            clean_line = line.strip()
            # Must be Title Case, 3-30 chars, only letters and spaces, not a header/job title
            if (clean_line 
                and len(clean_line) >= 3 
                and len(clean_line) < 30 
                and re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$", clean_line)
                and not any(c in clean_line.lower() for c in ["@", "street", "road", "+", "phone", "email", "www", "resume", "curriculum", "page", "summary", "experience", "education", "skills", "projects", "contact", "profile", "objective", "work", "history", "languages", "interests", "present", "university", "college", "school"])
                and not any(title_word in clean_line.lower() for title_word in job_titles_blacklist)):
                name = clean_line
                break
                
    if not name:
        filename = uploaded_file.name
        base_name = os.path.splitext(filename)[0]
        name = base_name.replace("_", " ").replace("-", " ").title()
        name = re.sub(r"\b(Resume|Cv|Bio|Vitae|Final|Update|Updated|Doc|Pdf)\b", "", name, flags=re.I).strip()
        
    if not name:
        name = "Custom Candidate (PDF)"
        
    # Heuristic 2: Extract Years of Experience
    years_exp = 5.0 # default baseline
    exp_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?)\b", text, re.I)
    if exp_matches:
        try:
            valid_exps = [float(e) for e in exp_matches if 1.0 <= float(e) <= 25.0]
            if valid_exps:
                years_exp = max(valid_exps)
        except:
            pass
            
    # Heuristic 3: Extract Current Title
    title = "Candidate" # neutral default
    titles_pool = [
        "Senior AI Engineer", "AI Engineer", "Machine Learning Engineer", "ML Engineer",
        "Data Scientist", "Lead Data Scientist", "Senior ML Engineer", "NLP Engineer",
        "Applied Scientist", "Backend Engineer", "Software Engineer", "Frontend Engineer",
        "Full Stack Engineer", "Systems Engineer", "Project Manager", "Financial Advisor",
        "Senior Financial Advisor", "Consultant", "Director", "Manager"
    ]
    found_title = False
    for t in titles_pool:
        if re.search(r"\b" + re.escape(t) + r"\b", text, re.I):
            title = t
            found_title = True
            break
            
    if not found_title and len(lines) > 1:
        # Check first 5 lines for a title string
        for line in lines[1:5]:
            if len(line) > 5 and len(line) < 40 and not any(c in line for c in ["@", "street", "road", "+", "phone", "email", "www"]):
                title = line.strip()
                break
            
    # Heuristic 4: Extract Education Tier
    edu_tier = "unknown"
    edu_institution = "Other Institution"
    if any(k in text_lower for k in ["iit", "bits pilani", "indian institute of technology", "iisc"]):
        edu_tier = "tier_1"
        edu_institution = "IIT / BITS (Tier-1)"
    elif any(k in text_lower for k in ["nit", "iiit", "dtu", "vit"]):
        edu_tier = "tier_2"
        edu_institution = "NIT / IIIT (Tier-2)"
    else:
        # Look for university keywords in text
        uni_match = re.search(r"([A-Za-z\s]+(?:University|College|Institute))", text)
        if uni_match:
            edu_institution = uni_match.group(1).strip()
            
    # Heuristic 5: Extract Skills (Only if present)
    skills_catalog = {
        "Python": "expert",
        "Pinecone": "expert",
        "Weaviate": "expert",
        "Qdrant": "expert",
        "Milvus": "expert",
        "Elasticsearch": "advanced",
        "Faiss": "advanced",
        "Sentence-Transformers": "expert",
        "Embeddings": "expert",
        "NLP": "expert",
        "NDCG": "advanced",
        "MRR": "advanced",
        "MAP": "advanced",
        "LoRA": "advanced",
        "QLoRA": "advanced",
        "PEFT": "advanced",
        "LLM": "expert",
        "XGBoost": "advanced"
    }
    detected_skills = []
    for sname, prof in skills_catalog.items():
        if re.search(r"\b" + re.escape(sname) + r"\b", text, re.I):
            detected_skills.append({
                "name": sname,
                "proficiency": prof,
                "duration_months": int(years_exp * 6)
            })
            
    # Heuristic 6: GitHub Presence
    github_score = 0.0
    if "github.com" in text_lower:
        github_score = 60.0
        
    # Construct candidate dictionary
    cand_id = "CUSTOM_" + hashlib.md5(uploaded_file.name.encode('utf-8')).hexdigest()[:8].upper()
    
    cand_dict = {
        "candidate_id": cand_id,
        "profile": {
            "anonymized_name": name,
            "current_title": title,
            "headline": f"{title} (Custom Upload)",
            "summary": text[:500].replace("\n", " ") + "...",
            "years_of_experience": years_exp,
            "location": "Noida, India" if "india" in text_lower or "noida" in text_lower or "pune" in text_lower or "delhi" in text_lower else "Remote, India",
            "country": "India",
            "current_company": lines[2][:30] if len(lines) > 2 else "Independent Consultant"
        },
        "skills": detected_skills,
        "education": [
            {
                "institution": edu_institution,
                "degree": "Degree",
                "field_of_study": "Engineering" if "engineering" in text_lower or "science" in text_lower else "Business / General",
                "start_year": 2018,
                "end_year": 2022,
                "grade": "N/A",
                "tier": edu_tier
            }
        ],
        "career_history": [
            {
                "company": "Previous Company",
                "title": title,
                "start_date": "2022-06-01",
                "end_date": None,
                "duration_months": int(years_exp * 12),
                "industry": "Software / AI" if "software" in text_lower or "artificial" in text_lower else "Other Industry",
                "company_size": "51-200",
                "description": text
            }
        ],
        "redrob_signals": {
            "signup_date": "2026-04-01",
            "last_active_date": "2026-04-20", # ~52d inactive relative to CURRENT_REF_DATE (neutral: 1.0)
            "open_to_work_flag": False, # neutral: 1.0
            "recruiter_response_rate": 0.4, # neutral: 1.0
            "notice_period_days": 90, # standard: 0.8
            "willing_to_relocate": True,
            "github_activity_score": github_score,
            "skill_assessment_scores": {}, # No fake tests
            "profile_views_received_30d": 5,
            "search_appearance_30d": 15,
            "saved_by_recruiters_30d": 0
        }
    }
    
    return cand_dict

def register_custom_candidate_embedding(cand_dict, resume_text):
    """
    Ensure the custom candidate is added to the ranker's global embedding variables.
    """
    if not ranker.EMBEDDINGS_LOADED or ranker.CANDIDATE_EMBEDDINGS is None:
        return
        
    cid = cand_dict["candidate_id"]
    if cid in ranker.CANDIDATE_ID_TO_INDEX:
        return
        
    model = ranker.get_sentence_model()
    if model is not None:
        try:
            profile = cand_dict.get("profile", {})
            title = profile.get("current_title", "")
            headline = profile.get("headline", "")
            summary = profile.get("summary", "")
            combined_text = f"Title: {title}. Headline: {headline}. Summary: {summary}"
            
            # Generate embedding
            emb = model.encode(combined_text, normalize_embeddings=True)
            
            # Append vector
            ranker.CANDIDATE_EMBEDDINGS = np.vstack([ranker.CANDIDATE_EMBEDDINGS, emb])
            # Add to index mapping
            new_idx = len(ranker.CANDIDATE_ID_TO_INDEX)
            ranker.CANDIDATE_ID_TO_INDEX[cid] = new_idx
        except Exception as e:
            st.error(f"Error generating embedding for custom candidate: {e}")

# Main Layout
st.markdown("<div class='main-title'>🧠 Redrob AI Recruiter Brain</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Intelligent Candidate Discovery, Anomaly Filtering, and Predictive Ranking Dashboard</div>", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 1rem; padding-top: 1rem;">
        <img src="https://img.icons8.com/nolan/96/brain.png" style="width: 70px; filter: drop-shadow(0 0 12px rgba(0, 229, 255, 0.45));" />
        <h2 style="font-family: 'Outfit', sans-serif; font-weight: 800; background: linear-gradient(90deg, #38BDF8, #00E5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-top: 0.5rem; margin-bottom: 0.2rem; font-size: 1.35rem; letter-spacing: -0.02em;">RECRUIT COCKPIT</h2>
        <p style="color: #9CA3AF; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; margin-bottom: 1.5rem;">Engine Status Center</p>
    </div>
""", unsafe_allow_html=True)

# Initialize custom candidates list in session state
if "custom_candidates" not in st.session_state:
    st.session_state.custom_candidates = []
if "processed_custom_resumes" not in st.session_state:
    st.session_state.processed_custom_resumes = {}

# Top Config Control Center
with st.expander("⚙️ DISCOVERY ENGINE CONTROL CENTER & FILTERS", expanded=True):
    col_left, col_right = st.columns([1.3, 1.0])
    
    with col_left:
        st.markdown("<div style='font-weight: 600; color: #E5E7EB; margin-bottom: 0.3rem;'>📝 Target Job Description</div>", unsafe_allow_html=True)
        jd_text = st.text_area("Target Job Description", value=DEFAULT_JD, height=220, label_visibility="collapsed")
        
        st.markdown("<div style='font-weight: 600; color: #E5E7EB; margin-top: 0.8rem; margin-bottom: 0.3rem;'>📁 Candidate Database Path (.jsonl)</div>", unsafe_allow_html=True)
        default_dataset_path = "../[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl"
        dataset_path = st.text_input("Candidate Database Path", value=default_dataset_path, label_visibility="collapsed")
        
    with col_right:
        st.markdown("<div style='font-weight: 600; color: #E5E7EB; margin-bottom: 0.3rem;'>🎯 Target Candidate Filters</div>", unsafe_allow_html=True)
        
        experience_range = st.slider("Required Experience (Years)", 0.0, 20.0, (5.0, 9.0), step=0.5)
        max_notice_period = st.slider("Maximum Notice Period (Days)", 0, 180, 90, step=15)
        
        is_default = ranker.is_default_jd(jd_text)
        
        # Checkboxes and File Uploader
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            if is_default:
                reloc_label = "Include Noida/Pune or willing to relocate"
                show_reloc = True
            else:
                tech_cities = ["pune", "noida", "gurgaon", "delhi", "ncr", "bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata", "san francisco", "london", "new york"]
                mentioned_cities = [c.capitalize() for c in tech_cities if c in jd_text.lower()]
                if mentioned_cities:
                    reloc_label = f"Include {', '.join(mentioned_cities)} or willing to relocate"
                    show_reloc = True
                else:
                    reloc_label = "Include target cities or willing to relocate"
                    show_reloc = False
            
            if show_reloc:
                only_relocate = st.checkbox(reloc_label, value=True)
            else:
                only_relocate = False
                st.markdown("<div style='color: #9CA3AF; font-size: 0.85rem; padding-top: 0.5rem;'>📍 No location constraints found in custom JD.</div>", unsafe_allow_html=True)
        with c_col2:
            limit_toggle = st.checkbox("Limit to first 10,000 candidates (faster)", value=True)
            
        load_limit = 10000 if limit_toggle else None
        
        # Sibling File Uploaders
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.markdown("<div style='font-weight: 600; color: #E5E7EB; margin-top: 0.3rem; margin-bottom: 0.2rem;'>Database Sample (.jsonl)</div>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Upload Custom Sample", type=["jsonl"], label_visibility="collapsed")
        with f_col2:
            st.markdown("<div style='font-weight: 600; color: #E5E7EB; margin-top: 0.3rem; margin-bottom: 0.2rem;'>➕ Custom Resume (PDF)</div>", unsafe_allow_html=True)
            uploaded_custom_resume = st.file_uploader("Upload Custom Candidate PDF", type=["pdf"], key="custom_resume_uploader", label_visibility="collapsed")
            
            if uploaded_custom_resume:
                file_key = uploaded_custom_resume.name + str(uploaded_custom_resume.size)
                if file_key not in st.session_state.processed_custom_resumes:
                    with st.spinner(f"Embedding candidate..."):
                        cand_dict = parse_custom_resume_pdf(uploaded_custom_resume)
                        if cand_dict:
                            # Register embedding
                            register_custom_candidate_embedding(cand_dict, cand_dict["career_history"][0]["description"])
                            # Store in session state
                            st.session_state.custom_candidates.append(cand_dict)
                            st.session_state.processed_custom_resumes[file_key] = cand_dict["candidate_id"]
                            st.toast(f"Added custom candidate: {cand_dict['profile']['anonymized_name']}!", icon="🟢")
                            
        if st.session_state.custom_candidates:
            st.write(f"📁 **Custom Resumes Active:** {len(st.session_state.custom_candidates)}")
            if st.button("🗑️ Clear Custom Candidates", key="clear_custom_cands"):
                st.session_state.custom_candidates = []
                st.session_state.processed_custom_resumes = {}
                st.rerun()

# Handle loading data
file_to_load = dataset_path
if uploaded_file:
    # Save uploaded file temporarily
    temp_path = "temp_uploaded_candidates.jsonl"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    file_to_load = temp_path

with st.spinner("Loading candidate database and scanning for anomalies..."):
    candidates_list, total_raw, total_hp, total_consulting = load_candidates(file_to_load, limit=load_limit)

if not candidates_list:
    st.error("""
        ### 📥 Candidate Database Upload Required
        To proceed with candidate discovery and ranking, please upload a candidate database file first.
        
        **Steps to upload:**
        1. Expand the **`DISCOVERY ENGINE CONTROL CENTER & FILTERS`** panel above.
        2. Upload your **`candidates.jsonl`** file into the **`Database Sample (.jsonl)`** box.
        3. Once uploaded, the system will instantly scan, filter anomalies, and display the ranked shortlist.
    """)
    st.stop()

# Inject custom candidates into the active database pool
if st.session_state.custom_candidates:
    for custom_cand in st.session_state.custom_candidates:
        if not any(c["candidate_id"] == custom_cand["candidate_id"] for c in candidates_list):
            candidates_list.append(custom_cand)
            # Ensure embedding remains registered on script reload
            register_custom_candidate_embedding(custom_cand, custom_cand["career_history"][0]["description"])

# System Status sidebar card (appended after data loading succeeds)
st.sidebar.markdown(f"""
    <div style="border-left: 3px solid #00E5FF; padding-left: 10px; margin: 1.2rem 0 0.8rem 0;">
        <h4 style="font-family: 'Outfit', sans-serif; font-weight: 700; color: #F3F4F6; margin: 0; font-size: 1rem; letter-spacing: 0.03em; text-transform: uppercase;">⚡ System Status</h4>
    </div>
    <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;">
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #E5E7EB;"><b>AI Model:</b> <span style="color: #00E5FF; font-weight:600;">BGE-Small-v1.5</span> 🟢</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #E5E7EB;"><b>Database:</b> <span style="color: #38BDF8; font-weight:600;">Connected</span> 🟢</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #E5E7EB;"><b>Embeddings:</b> <span style="color: #34D399; font-weight:600;">{"Loaded" if ranker.EMBEDDINGS_LOADED else "Not Found"}</span> 🟢</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #D1D5DB; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.3rem;"><b>Total Scanned:</b> {total_raw:,}</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #F87171;"><b>Anomalies Blocked:</b> {total_hp:,}</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #FBBF24;"><b>Consulting Filtered:</b> {total_consulting:,}</p>
        <p style="margin: 0.3rem 0; font-size: 0.85rem; color: #38BDF8;"><b>Custom Uploads:</b> {len(st.session_state.custom_candidates)}</p>
    </div>
""", unsafe_allow_html=True)


# Run Ranking Core
with st.spinner("Analyzing profiles and computing scores..."):
    # Rank candidates using our shared library
    ranked_candidates = ranker.rank_candidates(candidates_list, jd_text=jd_text)
    
    # Normalize scores relative to the top candidate in the entire ranked set (matching submission.csv)
    if ranked_candidates:
        max_score = ranked_candidates[0]["score"] if ranked_candidates[0]["score"] > 0 else 1.0
        for c in ranked_candidates:
            c["raw_score"] = c["score"]
            c["score"] = round(c["score"] / max_score, 4)

# Filter ranked results based on slider controls (dynamic UI overrides)
filtered_ranked = []
for c in ranked_candidates:
    # Experience filter
    if not (experience_range[0] <= c["years_exp"] <= experience_range[1]):
        continue
    # Notice period filter
    notice = c["candidate_raw"].get("redrob_signals", {}).get("notice_period_days", 90)
    if notice > max_notice_period:
        continue
    # Relocation filter
    if only_relocate:
        location = c["location"].lower()
        if is_default:
            target_cities = ["pune", "noida", "gurgaon", "delhi", "ncr"]
        else:
            tech_cities = ["pune", "noida", "gurgaon", "delhi", "ncr", "bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata", "san francisco", "london", "new york"]
            target_cities = [ct for ct in tech_cities if ct in jd_text.lower()]
            
        if target_cities:
            willing_relocate = c["candidate_raw"].get("redrob_signals", {}).get("willing_to_relocate", False)
            is_matched_city = any(ct in location for ct in target_cities)
            if not is_matched_city and not willing_relocate:
                continue
            
    filtered_ranked.append(c)

# Layout Metrics Row
run_stats = getattr(ranker, "LAST_RUN_STATS", {})
actual_hp = run_stats.get("honeypots", total_hp)
actual_consulting = run_stats.get("consulting", total_consulting)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Scanned Database</div><div class='metric-num'>{total_raw:,}</div><div class='metric-label'>Total Candidates</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Profile Anomalies</div><div class='metric-num' style='color: #EF4444;'>{actual_hp:,}</div><div class='metric-label'>Anomalous Profiles Blocked</div></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Consulting Filtered</div><div class='metric-num' style='color: #F59E0B;'>{actual_consulting:,}</div><div class='metric-label'>Service Profiles Blocked</div></div>", unsafe_allow_html=True)
with m4:
    st.markdown(f"<div class='metric-card'><div class='metric-label'>Ranked Shortlist</div><div class='metric-num'>{len(filtered_ranked)}</div><div class='metric-label'>Matches After Filters</div></div>", unsafe_allow_html=True)
# Funnel & Filter Audit Log Expander
with st.expander("🔍 Programmatic Funnel & Filter Audit Log", expanded=False):
    run_stats = getattr(ranker, "LAST_RUN_STATS", {})
    if run_stats:
        f_col1, f_col2 = st.columns([1.3, 1.0])
        with f_col1:
            st.markdown("#### 🎯 Candidate Discovery Funnel")
            
            # Prepare data
            stages = [
                "1. Scanned Pool",
                "2. Anomalies Blocked",
                "3. Service Blocked",
                "4. Country Mismatch",
                "5. Relocation Blocked",
                "6. Out-of-Range Exp",
                "7. Non-Tech Title",
                "8. Shortlisted Matches"
            ]
            candidates_count = [
                run_stats.get("scanned", 0),
                run_stats.get("honeypots", 0),
                run_stats.get("consulting", 0),
                run_stats.get("country_filtered", 0),
                run_stats.get("location_filtered", 0),
                run_stats.get("experience_filtered", 0),
                run_stats.get("title_filtered", 0),
                run_stats.get("shortlisted", 0)
            ]
            
            df_funnel = pd.DataFrame({
                "Stage": stages,
                "Candidates": candidates_count
            })
            
            # Generate horizontal bar chart representing funnel stages
            fig_funnel = px.bar(
                df_funnel,
                x="Candidates",
                y="Stage",
                orientation="h",
                color="Candidates",
                color_continuous_scale=["#EF4444", "#F59E0B", "#38BDF8", "#00E5FF"],
                text="Candidates"
            )
            fig_funnel.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
                coloraxis_showscale=False,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Number of Candidates"),
                yaxis=dict(showgrid=False, tickfont=dict(size=11))
            )
            fig_funnel.update_traces(
                textposition="outside",
                marker_line_color="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_funnel, use_container_width=True, config={'displayModeBar': False})
            
        with f_col2:
            st.markdown("#### 🛡️ Backend Audit Report")
            
            # Check custom JD constraints dynamically
            exclude_consulting = is_default or any(kw in jd_text.lower() for kw in ["consulting/service", "consulting company", "service company", "tcs", "infosys", "wipro", "accenture", "cognizant", "capgemini"])
            is_india_only = is_default or any(kw in jd_text.lower() for kw in ["india", "pune", "noida", "delhi", "gurgaon", "ncr", "bangalore", "bengaluru", "hyderabad", "mumbai", "chennai", "kolkata"])
            
            # Dim styles for disabled filters
            consulting_style = "margin: 0.4rem 0; font-size: 0.9rem; color: #FBBF24;" if exclude_consulting else "margin: 0.4rem 0; font-size: 0.9rem; color: #6B7280; opacity: 0.5;"
            country_style = "margin: 0.4rem 0; font-size: 0.9rem; color: #E5E7EB;" if is_india_only else "margin: 0.4rem 0; font-size: 0.9rem; color: #6B7280; opacity: 0.5;"
            reloc_style = "margin: 0.4rem 0; font-size: 0.9rem; color: #E5E7EB;" if (is_default or show_reloc) else "margin: 0.4rem 0; font-size: 0.9rem; color: #6B7280; opacity: 0.5;"
            
            consulting_label = "Service/Consulting Blocked:" if exclude_consulting else "Service Filter (N/A for this JD):"
            country_label = "Country Mismatch:" if is_india_only else "Country Check (N/A for this JD):"
            reloc_label = "Relocation Disqualified:" if (is_default or show_reloc) else "Relocation Check (N/A for this JD):"
            
            st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 12px; padding: 1.25rem; height: 300px; overflow-y: auto;">
                <p style="margin: 0.4rem 0; font-size: 0.9rem; color: #E5E7EB;"><b>1. Total Scanned Pool:</b> <span style="color: #38BDF8; font-weight:700;">{run_stats.get("scanned", 0):,}</span> profiles</p>
                <p style="margin: 0.4rem 0; font-size: 0.9rem; color: #F87171;"><b>2. Profile Anomalies Blocked:</b> <span style="color: #EF4444; font-weight:700;">-{run_stats.get("honeypots", 0):,}</span> accounts (contradictory logs)</p>
                <p style="{consulting_style}"><b>3. {consulting_label}</b> <span style="color: #F59E0B; font-weight:700;">-{run_stats.get("consulting", 0):,}</span> profiles</p>
                <p style="{country_style}"><b>4. {country_label}</b> <span style="color: #9CA3AF; font-weight:700;">-{run_stats.get("country_filtered", 0):,}</span> profiles</p>
                <p style="{reloc_style}"><b>5. {reloc_label}</b> <span style="color: #9CA3AF; font-weight:700;">-{run_stats.get("location_filtered", 0):,}</span> profiles</p>
                <p style="margin: 0.4rem 0; font-size: 0.9rem; color: #E5E7EB;"><b>6. Out-of-Range Experience:</b> <span style="color: #9CA3AF; font-weight:700;">-{run_stats.get("experience_filtered", 0):,}</span> profiles (below/above target years)</p>
                <p style="margin: 0.4rem 0; font-size: 0.9rem; color: #E5E7EB;"><b>7. Non-Technical / Irrelevant Title:</b> <span style="color: #9CA3AF; font-weight:700;">-{run_stats.get("title_filtered", 0):,}</span> profiles (disallowed HR/Sales/Finance roles)</p>
                <div style="border-top: 1px solid rgba(255,255,255,0.08); margin-top: 0.5rem; padding-top: 0.5rem;">
                    <p style="margin: 0; font-size: 0.95rem; color: #00E5FF; font-weight: 700;"><b>Qualified Candidates Shortlisted:</b> {run_stats.get("shortlisted", 0):,}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Create Tabs
tab_list, tab_dive, tab_matcher, tab_traps = st.tabs(["📋 Candidate Shortlist", "🔍 Profile Deep Dive", "📄 Resume Matcher", "🛡️ Anomalies Audit"])

# Tab 1: Shortlist
with tab_list:
    st.markdown("### Top Candidate Matches")
    if not filtered_ranked:
        st.warning("No candidates matched your filters. Try widening your experience or notice period criteria.")
    else:
        # Render custom candidates ranking status if any are uploaded
        if "custom_candidates" in st.session_state and st.session_state.custom_candidates:
            custom_ids = {cc["candidate_id"] for cc in st.session_state.custom_candidates}
            
            # Find their scores and ranks in filtered_ranked
            custom_statuses = []
            for c in filtered_ranked:
                if c["candidate_id"] in custom_ids:
                    in_top_100 = c["rank"] <= 100
                    status_badge = "🟢 In Top 100 Shortlist" if in_top_100 else "⚪ Outside Shortlist"
                    custom_statuses.append({
                        "Name": c["name"],
                        "ID": c["candidate_id"],
                        "Rank": f"Rank {c['rank']}",
                        "Score": f"{c['score']:.4f}",
                        "Status": status_badge,
                        "Title": c["current_title"]
                    })
            
            # Find those that were filtered out by user sliders or hard filters
            matched_ids = {cs["ID"] for cs in custom_statuses}
            for cc in st.session_state.custom_candidates:
                if cc["candidate_id"] not in matched_ids:
                    reason = "🔴 Filtered Out (Check experience/relocation settings)"
                    title_score = ranker.calculate_title_score(cc)
                    if title_score == 0.0:
                        reason = "🔴 Filtered Out (Non-tech / Disallowed Job Title)"
                    elif not cc.get("skills", []):
                        reason = "🔴 Filtered Out (No relevant AI/ML skills found)"
                        
                    custom_statuses.append({
                        "Name": cc["profile"]["anonymized_name"],
                        "ID": cc["candidate_id"],
                        "Rank": "N/A",
                        "Score": "N/A",
                        "Status": reason,
                        "Title": cc["profile"]["current_title"]
                    })
                    
            st.markdown("""
                <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem;">
                    <h4 style="margin-top:0; color:#38BDF8; font-family:'Outfit', sans-serif; font-size:1.1rem; font-weight:700;">📁 Custom Uploaded Resumes Ranking</h4>
                    <p style="font-size:0.85rem; color:#9CA3AF; margin-bottom:1rem;">Your custom PDF uploads are evaluated using the same rules and BGE model as the main database. Here is where they rank:</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.dataframe(
                pd.DataFrame(custom_statuses)[["Name", "Title", "Rank", "Score", "Status"]],
                use_container_width=True,
                column_config={
                    "Rank": st.column_config.TextColumn(width=100),
                    "Score": st.column_config.TextColumn(width=100),
                    "Status": st.column_config.TextColumn(width=300),
                },
                hide_index=True
            )
            st.write("")
        # Build dataframe for nice tabular display
        df_display = []
        for i, c in enumerate(filtered_ranked[:100]):
            signals = c["candidate_raw"].get("redrob_signals", {})
            df_display.append({
                "Rank": c["rank"],
                "ID": c["candidate_id"],
                "Name": c["name"],
                "Current Title": c["current_title"],
                "Current Company": c["current_company"],
                "Experience": f"{c['years_exp']:.1f} Yrs",
                "Location": c["location"],
                "Score": f"{c['score']:.4f}",
                "Notice Period": f"{signals.get('notice_period_days')} days",
                "Reasoning Summary": c["reasoning"]
            })
            
        st.dataframe(
            pd.DataFrame(df_display),
            use_container_width=True,
            column_config={
                "Rank": st.column_config.NumberColumn(width=60),
                "ID": st.column_config.TextColumn(width=100),
                "Score": st.column_config.TextColumn(width=80),
                "Notice Period": st.column_config.TextColumn(width=100),
                "Reasoning Summary": st.column_config.TextColumn(width=450),
            },
            hide_index=True
        )
        
        # Show Shortlist Analytics
        st.write("")
        st.markdown("### 📊 Shortlist Cohort Analytics")
        if filtered_ranked:
            top_100 = filtered_ranked[:100]
            avg_exp = np.mean([c["years_exp"] for c in top_100])
            avg_notice = np.mean([c["candidate_raw"].get("redrob_signals", {}).get("notice_period_days", 90) for c in top_100])
            
            # Count locations
            loc_counts = {}
            for c in top_100:
                loc = c["location"].split(",")[0].strip()
                loc_counts[loc] = loc_counts.get(loc, 0) + 1
                
            # Count top skills
            skill_counts = {}
            for c in top_100:
                for s in c["candidate_raw"].get("skills", []):
                    sname = s.get("name")
                    skill_counts[sname] = skill_counts.get(sname, 0) + 1
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:4]
            
            sa1, sa2, sa3 = st.columns([1, 1.2, 1.2])
            with sa1:
                avg_score = np.mean([c["score"] for c in top_100])
                st.markdown(f"<div style='margin-bottom: 1rem;'>💼 <b>Average Experience</b><br><span style='font-size: 1.5rem; font-weight: 700; color: #38BDF8;'>{avg_exp:.1f} Years</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-bottom: 1rem;'>📅 <b>Average Notice Period</b><br><span style='font-size: 1.5rem; font-weight: 700; color: #38BDF8;'>{avg_notice:.1f} Days</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='margin-bottom: 1rem;'>📈 <b>Average Fit Score</b><br><span style='font-size: 1.5rem; font-weight: 700; color: #00E5FF;'>{avg_score:.4f}</span></div>", unsafe_allow_html=True)
            with sa2:
                st.markdown("**📍 Top Locations**")
                df_loc = pd.DataFrame(list(loc_counts.items()), columns=["Location", "Candidates"]).sort_values(by="Candidates", ascending=True).tail(5)
                fig_loc = px.bar(
                    df_loc, 
                    x="Candidates", 
                    y="Location", 
                    orientation="h",
                    color="Candidates",
                    color_continuous_scale=["#1E3A8A", "#38BDF8", "#00E5FF"],
                    text="Candidates"
                )
                fig_loc.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#F3F4F6",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=200,
                    coloraxis_showscale=False,
                    xaxis=dict(showgrid=False, zeroline=False, visible=False),
                    yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=11))
                )
                fig_loc.update_traces(
                    textposition="inside",
                    marker_line_color="rgba(0,0,0,0)",
                    hovertemplate="<b>%{y}</b><br>Candidates: %{x}<extra></extra>"
                )
                st.plotly_chart(fig_loc, use_container_width=True, config={'displayModeBar': False})
            with sa3:
                st.markdown("**⚡ Core Skill Coverage**")
                df_skills = pd.DataFrame(sorted_skills, columns=["Skill", "Candidates"]).sort_values(by="Candidates", ascending=False)
                fig_skills = px.bar(
                    df_skills,
                    x="Skill",
                    y="Candidates",
                    color="Candidates",
                    color_continuous_scale=["#1E3A8A", "#38BDF8", "#00E5FF"],
                    text="Candidates"
                )
                fig_skills.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#F3F4F6",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=200,
                    coloraxis_showscale=False,
                    yaxis=dict(showgrid=False, zeroline=False, visible=False),
                    xaxis=dict(showgrid=False, zeroline=False, tickangle=-15, tickfont=dict(size=11))
                )
                fig_skills.update_traces(
                    textposition="inside",
                    marker_line_color="rgba(0,0,0,0)",
                    hovertemplate="<b>%{x}</b><br>Candidates: %{y}<extra></extra>"
                )
                st.plotly_chart(fig_skills, use_container_width=True, config={'displayModeBar': False})
        st.write("")
        
        # Download Shortlist CSV Button
        # Create CSV text
        csv_data = "candidate_id,rank,score,reasoning\n"
        for c in ranked_candidates[:100]:
            csv_data += f"{c['candidate_id']},{c['rank']},{c['score']:.4f},\"{c['reasoning']}\"\n"
            
        st.download_button(
            label="💾 Download Validated Shortlist CSV",
            data=csv_data,
            file_name="team_submission.csv",
            mime="text/csv",
            help="Download the verified top-100 shortlist ready for portal submission."
        )

# Tab 2: Profile Deep Dive
with tab_dive:
    st.markdown("### Profile Inspection & Signals Audit")
    
    if not filtered_ranked:
        st.info("Please adjust filters to view matching profiles.")
    else:
        # Select box and Compare checkbox side-by-side
        col_select, col_compare = st.columns([2.2, 1.0])
        with col_select:
            c_names = [f"Rank {c['rank']}: {c['name']} ({c['candidate_id']})" for c in filtered_ranked[:100]]
            selected_index = st.selectbox("Select Candidate to Inspect:", range(len(c_names)), format_func=lambda x: c_names[x])
        with col_compare:
            st.write("") # spacing
            st.write("")
            compare_mode = st.checkbox("📊 Compare Candidates", value=False, help="Select and compare up to 3 candidates side-by-side.")
            
        if compare_mode:
            compare_selected = st.multiselect(
                "Select up to 3 candidates to compare:",
                options=range(len(c_names)),
                default=[selected_index],
                format_func=lambda x: c_names[x],
                max_selections=3
            )
            if len(compare_selected) < 2:
                st.info("Please select at least 2 candidates from the list to compare side-by-side.")
            else:
                st.write("---")
                cols = st.columns(len(compare_selected))
                comparison_data = []
                for idx, col_idx in enumerate(compare_selected):
                    comp_cand = filtered_ranked[col_idx]
                    comp_raw = comp_cand["candidate_raw"]
                    comp_profile = comp_raw.get("profile", {})
                    comp_signals = comp_raw.get("redrob_signals", {})
                    
                    t_score = ranker.calculate_title_score(comp_raw)
                    s_score = ranker.calculate_skill_score(comp_raw)
                    availability_mult = ranker.calculate_availability_multiplier(comp_raw)
                    
                    comparison_data.append({
                        "Candidate": comp_cand["name"],
                        "Title Fit (40%)": t_score * 0.4,
                        "Skills Fit (30%)": s_score * 0.3,
                        "Availability Index": availability_mult * 0.5,
                        "Overall Score": comp_cand["score"]
                    })
                    
                    with cols[idx]:
                        st.markdown(f"### Rank {comp_cand['rank']}: {comp_cand['name']}")
                        st.write(f"**ID**: `{comp_cand['candidate_id']}`")
                        st.write(f"**Current Title**: {comp_cand['current_title']}")
                        st.write(f"**Current Company**: {comp_cand['current_company']}")
                        st.write(f"💼 **Experience**: {comp_cand['years_exp']:.1f} Years")
                        st.write(f"📍 **Location**: {comp_cand['location']}")
                        
                        st.markdown(f"""
                            <div style="text-align: center; margin: 1rem 0; padding: 0.75rem; border-radius: 12px; background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.25);">
                                <div style="font-size: 0.75rem; color:#9CA3AF; letter-spacing:0.05em; font-weight:600;">FIT SCORE</div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #00E5FF; text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);">{comp_cand['score']:.4f}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        skills_list = [s.get("name") for s in comp_raw.get("skills", [])][:5]
                        skills_str = ", ".join(skills_list) if skills_list else "None listed"
                        st.write(f"⚡ **Top Skills**: {skills_str}")
                        
                        notice_days = comp_signals.get("notice_period_days", 90)
                        otw_status = "🟢 Available" if comp_signals.get("open_to_work_flag", False) else "⚪ Passive"
                        st.write(f"📅 **Notice**: {notice_days} days ({otw_status})")
                        st.write(f"💬 **Response Rate**: {comp_signals.get('recruiter_response_rate', 0.0)*100:.0f}%")
                        
                        st.write("---")
                        st.markdown("**AI Fit Analysis:**")
                        st.markdown(f"<div class='reasoning-box'>{comp_cand['reasoning']}</div>", unsafe_allow_html=True)
                        
                st.write("")
                st.markdown("### 📊 Fit Component Comparison")
                df_comp = pd.DataFrame(comparison_data)
                fig_comp = px.bar(
                    df_comp,
                    x="Candidate",
                    y=["Title Fit (40%)", "Skills Fit (30%)", "Availability Index", "Overall Score"],
                    barmode="group",
                    color_discrete_sequence=["#1E3A8A", "#38BDF8", "#00E5FF", "#FBBF24"]
                )
                fig_comp.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#F3F4F6",
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=300,
                    xaxis=dict(showgrid=False, title=""),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Component Scores"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})
        else:
            cand_data = filtered_ranked[selected_index]
            cand_raw = cand_data["candidate_raw"]
            profile = cand_raw.get("profile", {})
            signals = cand_raw.get("redrob_signals", {})
            
            st.write("---")
            
            c1, c2 = st.columns([1.8, 1.2])
            
            with c1:
                st.markdown(f"## {profile.get('anonymized_name')}")
                st.markdown(f"**Headline**: {profile.get('headline')}")
                st.write(f"📍 **Location**: {profile.get('location')}, {profile.get('country')} | 💼 **Experience**: {profile.get('years_of_experience')} Years")
                
                # Recruiter reasoning
                st.markdown("#### AI Recruiter Fit Analysis")
                st.markdown(f"<div class='reasoning-box'>{cand_data['reasoning']}</div>", unsafe_allow_html=True)
                
                # Career History Timeline
                st.markdown("#### Professional Timeline")
                for job in cand_raw.get("career_history", []):
                    start = job.get("start_date", "N/A")
                    end = job.get("end_date") or "Present"
                    dur = job.get("duration_months", 0)
                    
                    st.markdown(f"""
                        <div class='timeline-card'>
                            <div class='timeline-dot'></div>
                            <div class='timeline-company'>{job.get('company')} <span style='font-size:0.8rem; color:#9CA3AF;'>({job.get('company_size')} employees)</span></div>
                            <div class='timeline-title'>{job.get('title')}</div>
                            <div class='timeline-dates'>{start} to {end} ({dur} months) | Industry: {job.get('industry')}</div>
                            <p style='margin-top:0.5rem; font-size:0.9rem; color:#D1D5DB;'>{job.get('description')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # Education Timeline
                st.markdown("#### Education")
                for edu in cand_raw.get("education", []):
                    tier_badge = f"<span style='color:#3B82F6;'>[{edu.get('tier', 'unknown').upper()}]</span>"
                    st.markdown(f"""
                        <div class='timeline-card' style='border-left-color: #3B82F6;'>
                            <div class='timeline-dot' style='background-color: #3B82F6;'></div>
                            <div class='timeline-company'>{edu.get('institution')} {tier_badge}</div>
                            <div class='timeline-title'>{edu.get('degree')} in {edu.get('field_of_study')}</div>
                            <div class='timeline-dates'>{edu.get('start_year')} - {edu.get('end_year')} | Grade: {edu.get('grade')}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
            with c2:
                # AI Score Profile showing both Normalized and Raw Scores
                st.markdown(f"""
                    <div style="background: rgba(56, 189, 248, 0.05); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem; text-align: center;">
                        <span style="font-size: 0.75rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">AI Recruiter Score Profile</span>
                        <div style="display: flex; justify-content: space-around; align-items: center; margin-top: 0.5rem;">
                            <div>
                                <div style="font-size: 0.7rem; color: #9CA3AF;">NORMALIZED FIT</div>
                                <div style="font-size: 1.4rem; font-weight: 800; color: #00E5FF;">{cand_data['score']:.4f}</div>
                            </div>
                            <div style="border-left: 1px solid rgba(255,255,255,0.1); height: 30px;"></div>
                            <div>
                                <div style="font-size: 0.7rem; color: #9CA3AF;">RAW SCORE</div>
                                <div style="font-size: 1.4rem; font-weight: 800; color: #FBBF24;">{cand_data.get('raw_score', 0.0):.3f}</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("### Platform Availability Envelope")
                
                # Custom neon styled availability badges
                otw = signals.get("open_to_work_flag", False)
                if otw:
                    otw_badge = '<span class="badge badge-green"><span class="pulse-active"></span>Active Open-To-Work</span>'
                else:
                    otw_badge = '<span class="badge badge-yellow">Passive Searcher</span>'
                    
                rrr = signals.get("recruiter_response_rate", 0.0)
                if rrr >= 0.7:
                    rrr_badge = f'<span class="badge badge-green">{rrr*100:.0f}% Response Rate</span>'
                elif rrr >= 0.4:
                    rrr_badge = f'<span class="badge badge-yellow">{rrr*100:.0f}% Response Rate</span>'
                else:
                    rrr_badge = f'<span class="badge badge-red">{rrr*100:.0f}% Response Rate</span>'
                    
                notice = signals.get("notice_period_days", 90)
                if notice <= 30:
                    notice_badge = f'<span class="badge badge-green">{notice}d Notice Period</span>'
                elif notice <= 60:
                    notice_badge = f'<span class="badge badge-yellow">{notice}d Notice Period</span>'
                else:
                    notice_badge = f'<span class="badge badge-red">{notice}d Notice Period</span>'
                    
                last_active = signals.get("last_active_date", "")
                active_days = 999
                if last_active:
                    active_date = ranker.parse_date(last_active)
                    if active_date:
                        active_days = (ranker.CURRENT_REF_DATE - active_date).days
                
                if active_days <= 30:
                    active_badge = f'<span class="badge badge-green">Active {active_days}d ago</span>'
                elif active_days <= 90:
                    active_badge = f'<span class="badge badge-yellow">Active {active_days}d ago</span>'
                else:
                    active_badge = f'<span class="badge badge-red">Inactive {active_days}d ago</span>'
                    
                email_badge = '<span class="badge badge-blue">📧 Email Verified</span>' if signals.get("verified_email") else '<span class="badge badge-red">📧 Email Unverified</span>'
                phone_badge = '<span class="badge badge-blue">📱 Phone Verified</span>' if signals.get("verified_phone") else '<span class="badge badge-red">📱 Phone Unverified</span>'
                github_badge = f'<span class="badge badge-blue">💻 GitHub Score: {signals.get("github_activity_score", 0)}/100</span>'
                
                st.markdown(f"""
                    <div style="margin-bottom: 1.5rem;">
                        <p style="font-weight: 600; color: #9CA3AF; margin-bottom: 0.5rem;">Candidate Signals:</p>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            {otw_badge}
                            {notice_badge}
                            {rrr_badge}
                            {active_badge}
                            {email_badge}
                            {phone_badge}
                            {github_badge}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.write("---")
                
                st.markdown("### Skill Set & Experience Duration")
                skills_data = []
                for s in cand_raw.get("skills", []):
                    skills_data.append({
                        "Skill": s.get("name"),
                        "Proficiency": s.get("proficiency").capitalize(),
                        "Months": s.get("duration_months", 0),
                        "Endorsements": s.get("endorsements", 0)
                    })
                
                if skills_data:
                    df_skills = pd.DataFrame(skills_data)
                    df_skills = df_skills.sort_values(by="Months", ascending=True)
                    
                    color_map = {
                        "Expert": "#00E5FF",
                        "Advanced": "#38BDF8",
                        "Intermediate": "#1E3A8A",
                        "Beginner": "#1E293B"
                    }
                    
                    fig_skills = px.bar(
                        df_skills,
                        x="Months",
                        y="Skill",
                        orientation="h",
                        color="Proficiency",
                        color_discrete_map=color_map,
                        hover_data=["Proficiency", "Endorsements"],
                        text="Months"
                    )
                    fig_skills.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#F3F4F6",
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=max(200, len(skills_data) * 32),
                        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Experience (Months)"),
                        yaxis=dict(showgrid=False, title="", tickfont=dict(size=11)),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    fig_skills.update_traces(
                        textposition="inside",
                        marker_line_color="rgba(0,0,0,0)",
                        hovertemplate="<b>%{y}</b><br>Experience: %{x} months<br>Proficiency: %{customdata[0]}<br>Endorsements: %{customdata[1]}<extra></extra>"
                    )
                    st.plotly_chart(fig_skills, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.write("No skills listed.")

# Tab 3: Resume Matcher
with tab_matcher:
    st.markdown("### Candidate Resume Matching Sandpit")
    st.write("Upload a PDF/TXT resume to calculate match suitability and identify key skill alignments or gaps against the active Job Description.")
    
    # PDF/TXT Resume uploader
    uploaded_resume = st.file_uploader("Upload Candidate Resume (PDF or TXT):", type=["pdf", "txt"])
    
    # Store resume text in session state to avoid overwriting edits on script reruns
    if "resume_text" not in st.session_state:
        st.session_state.resume_text = ""
        
    if uploaded_resume:
        if "last_uploaded_name" not in st.session_state or st.session_state.last_uploaded_name != uploaded_resume.name:
            st.session_state.last_uploaded_name = uploaded_resume.name
            if uploaded_resume.name.endswith(".pdf"):
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(uploaded_resume)
                    text_parts = []
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_parts.append(extracted)
                    st.session_state.resume_text = "\n".join(text_parts)
                    st.success("Successfully extracted text from uploaded PDF resume!")
                except Exception as e:
                    st.error(f"Error parsing PDF file: {e}. Please try another file or copy-paste the text.")
            else:
                try:
                    st.session_state.resume_text = uploaded_resume.getvalue().decode("utf-8")
                    st.success("Successfully loaded TXT resume!")
                except Exception as e:
                    st.error(f"Error reading TXT file: {e}")
                    
    resume_text_input = st.text_area(
        "Or Paste/Edit Resume Text Here:",
        value=st.session_state.resume_text,
        placeholder="Paste candidate's CV content, skills, and experiences here...",
        height=200
    )
    # Sync edited text back to session state
    st.session_state.resume_text = resume_text_input
    
    if st.session_state.resume_text.strip():
        resume_lower = st.session_state.resume_text.lower()
        
        # Extract skills and check relevance
        vectordb_skills = {"pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss"}
        retrieval_skills = {"sentence-transformers", "embeddings", "bge", "e5", "nlp", "information retrieval", "retrieval", "semantic search", "vector search"}
        eval_skills = {"ndcg", "mrr", "map", "evaluation", "metrics"}
        
        matched_vdb = [s for s in vectordb_skills if s in resume_lower]
        matched_ret = [s for s in retrieval_skills if s in resume_lower]
        matched_eval = [s for s in eval_skills if s in resume_lower]
        
        score = 0.0
        if matched_vdb: score += 0.35
        if matched_ret: score += 0.35
        if matched_eval: score += 0.2
        if "python" in resume_lower: score += 0.1
        
        # Render layout columns
        g1, g2 = st.columns([1.2, 1.8])
        
        with g1:
            # Speedometer Gauge Chart using go.Indicator
            import plotly.graph_objects as go
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=round(score * 100, 1),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Match Suitability %", 'font': {'size': 15, 'color': '#9CA3AF'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#F3F4F6"},
                    'bar': {'color': "#00E5FF"},
                    'bgcolor': "rgba(30, 41, 59, 0.5)",
                    'borderwidth': 1,
                    'bordercolor': "rgba(56, 189, 248, 0.3)",
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.1)'},
                        {'range': [40, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                        {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
                    ],
                    'threshold': {
                        'line': {'color': "#38BDF8", 'width': 3},
                        'thickness': 0.75,
                        'value': 75
                    }
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#F3F4F6",
                height=200,
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
            
        with g2:
            # Skill breakdown
            sc1, sc2 = st.columns(2)
            with sc1:
                st.success("#### Found Skills")
                st.write(f"**Vector DBs**: {', '.join(matched_vdb) if matched_vdb else 'None'}")
                st.write(f"**Retrieval**: {', '.join(matched_ret) if matched_ret else 'None'}")
                st.write(f"**Evaluation**: {', '.join(matched_eval) if matched_eval else 'None'}")
                st.write(f"**Python**: {'Yes' if 'python' in resume_lower else 'No'}")
            with sc2:
                st.error("#### Gaps / Missing Focus")
                missing_vdb = vectordb_skills - set(matched_vdb)
                missing_eval = eval_skills - set(matched_eval)
                
                st.write(f"**Missing Vector DBs**: {', '.join(list(missing_vdb)[:3]) if missing_vdb else 'None'}")
                st.write(f"**Missing Eval Metrics**: {', '.join(list(missing_eval)[:3]) if missing_eval else 'None'}")
        
        st.write("---")
        st.info("Note: This sandpit calculates a zero-shot keyword match similarity score. Real candidate profiles from the pool also incorporate platform activity history (notice periods, response rate, etc.) which optimizes the final ranking.")
    else:
        st.info("💡 Please upload a PDF/TXT resume or paste text into the area above to run the match suitability engine.")

# Tab 4: Defused Traps Audit
with tab_traps:
    st.markdown("### 🛡️ Programmatic Profile Anomaly Audit Log")
    st.write("Our AI Engine runs multiple physical and logical consistency audits to catch anomalous profile accounts and IT services consulting profiles.")
    
    # Check for honeypot count stats
    # Let's count trap types for the 5 anomaly parameters
    anomaly_counts = {
        "1. Date Conflict (Signup > Active)": 0,
        "2. Skill Duration Mismatch (Skill > Exp + 1.5 Yrs)": 0,
        "3. Proficiency Contradiction (Expert with 0 mo)": 0,
        "4. Timeline Contradiction (Job pre-founding)": 0,
        "5. Job Duration Mismatch (Job > Comp age)": 0
    }
    consulting_count = 0
    
    caught_details = []
    
    # Let's scan candidates to classify traps
    for cand in candidates_list:
        # check consulting
        is_c = ranker.is_consulting_only(cand)
        hp, hp_reason = ranker.is_honeypot(cand)
        
        if hp:
            # Identify sub-reason to attribute to exactly one of the 5 anomaly parameters
            signals = cand.get("redrob_signals", {})
            signup = ranker.parse_date(signals.get("signup_date"))
            active = ranker.parse_date(signals.get("last_active_date"))
            profile = cand.get("profile", {})
            years_exp = profile.get("years_of_experience", 0)
            
            # Rule 1: Signup Date after Active Date
            if signup and active and signup > active:
                anomaly_counts["1. Date Conflict (Signup > Active)"] += 1
            else:
                # Rule 2: Skill Duration Exceeds Experience + 1.5 Year Buffer
                skills_mismatch = False
                for s in cand.get("skills", []):
                    dur_years = s.get("duration_months", 0) / 12.0
                    if dur_years > years_exp + 1.5:
                        skills_mismatch = True
                        break
                if skills_mismatch:
                    anomaly_counts["2. Skill Duration Mismatch (Skill > Exp + 1.5 Yrs)"] += 1
                else:
                    # Rule 3: Expert/Advanced with 0 months
                    expert_zero = False
                    for s in cand.get("skills", []):
                        if s.get("proficiency") in ["expert", "advanced"] and s.get("duration_months", 0) == 0:
                            expert_zero = True
                            break
                    if expert_zero:
                        anomaly_counts["3. Proficiency Contradiction (Expert with 0 mo)"] += 1
                    else:
                        # Rule 4 & 5: Job pre-founding or job duration exceeds company age
                        timeline_pre = False
                        timeline_dur = False
                        career = cand.get("career_history", [])
                        for job in career:
                            comp = job.get("company", "")
                            if comp in ranker.FOUNDING_YEARS:
                                f_year = ranker.FOUNDING_YEARS[comp]
                                start_str = job.get("start_date")
                                if start_str:
                                    try:
                                        start_year = int(start_str.split("-")[0])
                                        if start_year < f_year:
                                            timeline_pre = True
                                            break
                                    except:
                                        pass
                                dur_years = job.get("duration_months", 0) / 12.0
                                max_dur = ranker.CURRENT_REF_DATE.year - f_year
                                if dur_years > max_dur:
                                    timeline_dur = True
                                    break
                                    
                        if timeline_pre:
                            anomaly_counts["4. Timeline Contradiction (Job pre-founding)"] += 1
                        elif timeline_dur:
                            anomaly_counts["5. Job Duration Mismatch (Job > Comp age)"] += 1
                        else:
                            # Fallback just in case some other check matched in is_honeypot
                            anomaly_counts["4. Timeline Contradiction (Job pre-founding)"] += 1
                            
            if len(caught_details) < 50:
                caught_details.append({
                    "ID": cand["candidate_id"],
                    "Name": profile.get("anonymized_name", "Anonymous"),
                    "Type": "Anomalous Account",
                    "Reason": hp_reason
                })
        elif is_c:
            consulting_count += 1
            if len(caught_details) < 50:
                caught_details.append({
                    "ID": cand["candidate_id"],
                    "Name": cand.get("profile", {}).get("anonymized_name", "Anonymous"),
                    "Type": "Consulting Filter",
                    "Reason": "Entire career spent at IT consulting/services firms (disallowed by JD)."
                })
                
    # Display breakdown pie chart
    t_cols = st.columns([1.6, 1.4])
    with t_cols[0]:
        st.markdown("#### Anomaly Category Distribution")
        df_traps = pd.DataFrame(list(anomaly_counts.items()), columns=["Category", "Blocked Profiles"])
        fig_traps = px.pie(
            df_traps,
            names="Category",
            values="Blocked Profiles",
            hole=0.4,
            color_discrete_sequence=["#EF4444", "#F59E0B", "#38BDF8", "#00E5FF", "#1E3A8A"]
        )
        fig_traps.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F3F4F6",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05,
                font=dict(size=13)
            )
        )
        fig_traps.update_traces(
            sort=False,
            textinfo='percent',
            textfont_size=14,
            marker=dict(line=dict(color='#0B0E14', width=2))
        )
        st.plotly_chart(fig_traps, use_container_width=True, config={'displayModeBar': False})
            
    with t_cols[1]:
        st.markdown("#### Real-time Anomalies Defused Audit Log")
        st.write("Flagged profiles caught by the Redrob Recruiter system:")
        df_caught = pd.DataFrame(caught_details)
        if not df_caught.empty:
            st.dataframe(
                df_caught,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID": st.column_config.TextColumn(width=100),
                    "Name": st.column_config.TextColumn(width=120),
                    "Type": st.column_config.TextColumn(width=120),
                    "Reason": st.column_config.TextColumn(width=300),
                }
            )
        else:
            st.write("No defused traps in sample.")
