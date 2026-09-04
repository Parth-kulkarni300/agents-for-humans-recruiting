import re

KNOWN_CITIES_MAP = {
    "bangalore": "Bangalore",
    "bengaluru": "Bangalore",
    "banglore": "Bangalore",
    "blr": "Bangalore",
    "pune": "Pune",
    "pnq": "Pune",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",
    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "ncr": "Delhi NCR",
    "gurgaon": "Gurgaon",
    "gurugram": "Gurgaon",
    "noida": "Noida",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "chandigarh": "Chandigarh",
    "indore": "Indore",
    "surat": "Surat",
    "coimbatore": "Coimbatore",
    "visakhapatnam": "Visakhapatnam",
    "lucknow": "Lucknow",
    "bhubaneswar": "Bhubaneswar",
    "san francisco": "San Francisco",
    "new york": "New York",
    "london": "London",
    "singapore": "Singapore",
    "dubai": "Dubai",
    "toronto": "Toronto",
    "sydney": "Sydney"
}

SKILLS_MAP = {
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "python": "Python",
    "py": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "angular": "Angular",
    "html": "HTML",
    "css": "CSS",
    "tailwind": "Tailwind",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "rails": "Ruby on Rails",
    "php": "PHP",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "sql": "SQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "redis": "Redis",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "git": "Git",
    "linux": "Linux",
    "api": "REST API",
    "rest api": "REST API",
    "graphql": "GraphQL",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "keras": "Keras",
    "nlp": "NLP",
    "llm": "LLM",
    "pandas": "Pandas",
    "numpy": "NumPy"
}

def test_extraction(jd_text):
    text = jd_text.lower()
    
    # Extract locations
    found_locs = set()
    for kw, canonical in KNOWN_CITIES_MAP.items():
        pattern = r"(?:\b|\s|^)" + re.escape(kw) + r"(?:\b|\s|[.,;:!?/\-]|$)"
        if re.search(pattern, text):
            found_locs.add(canonical)
            
    # Extract skills
    found_skills = set()
    for kw, canonical in SKILLS_MAP.items():
        # If kw contains non-alphanumeric char (e.g. c++, c#, node.js) or is short, use custom punctuation boundary
        if not kw.isalnum() or len(kw) <= 2:
            pattern = r"(?:\b|\s|^)" + re.escape(kw) + r"(?:\b|\s|[.,;:!?/\-]|$)"
        else:
            pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text):
            found_skills.add(canonical)
            
    return sorted(list(found_locs)), sorted(list(found_skills))

sample_jd = "We are hiring C++ and Python engineers in Banglore and Pune. Must know Java and SQL."
locs, skills = test_extraction(sample_jd)
print("Extracted Locations:", locs)
print("Extracted Skills:", skills)
