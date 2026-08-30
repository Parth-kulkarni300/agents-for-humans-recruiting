import argparse
import json
import os
import sys
import pandas as pd
from pathlib import Path
import ranker

# Standard Job Description used for ranking
JD_TEXT = """Job Description: Senior AI Engineer — Founding Team
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

def main():
    parser = argparse.ArgumentParser(description="Redrob Candidate Ranking CLI Tool")
    parser.add_argument(
        "--candidates",
        type=str,
        required=True,
        help="Path to the candidates.jsonl file."
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Path to save the output submission CSV file."
    )
    
    args = parser.parse_args()
    
    candidates_path = Path(args.candidates)
    output_path = Path(args.out)
    
    if not candidates_path.exists():
        print(f"Error: Candidate database not found at '{candidates_path}'")
        sys.exit(1)
        
    print(f"Reading candidate database from '{candidates_path}'...")
    candidates = []
    
    with open(candidates_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                cand = json.loads(line)
                candidates.append(cand)
            except Exception as e:
                print(f"Warning: Failed to parse candidate line: {e}")
                
    total_candidates = len(candidates)
    print(f"Successfully loaded {total_candidates} candidate records.")
    
    print("Executing candidate discovery and trap-filtering brain...")
    # Rank candidates using our shared module
    ranked = ranker.rank_candidates(candidates, jd_text=JD_TEXT)
    
    # Check if we got the required top 100 shortlist
    if not ranked:
        print("Warning: No candidates matched our criteria!")
        ranked_shortlist = []
    else:
        ranked_shortlist = ranked[:100]

    print(f"Shortlisted top {len(ranked_shortlist)} candidates.")

    # Normalize scores to [0, 1] relative to the top candidate
    max_score = ranked_shortlist[0]["score"] if ranked_shortlist else 1.0
    for c in ranked_shortlist:
        c["score"] = round(c["score"] / max_score, 4)

    # Re-sort after rounding to enforce tie-break by candidate_id ascending (per submission spec)
    ranked_shortlist.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    for idx, c in enumerate(ranked_shortlist):
        c["rank"] = idx + 1

    # Create output dataframe
    output_data = []
    for c in ranked_shortlist:
        output_data.append({
            "candidate_id": c["candidate_id"],
            "rank": c["rank"],
            "score": c["score"],
            "reasoning": c["reasoning"]
        })
        
    # Pad to exactly 100 rows if needed (per format requirements)
    # The submission spec requires exactly 100 rows, so if we have fewer, we warn the user
    # (Though on 100,000 dataset we will have plenty of candidates).
    while len(output_data) < 100:
        fill_rank = len(output_data) + 1
        output_data.append({
            "candidate_id": "CAND_0000000",
            "rank": fill_rank,
            "score": 0.0,
            "reasoning": "Filler candidate added to satisfy the 100-row format requirement."
        })
        
    # Ensure correct column order
    df = pd.DataFrame(output_data)[["candidate_id", "rank", "score", "reasoning"]]
    
    # Save to CSV (UTF-8 encoding)
    print(f"Writing validated shortlist to '{output_path}'...")
    df.to_csv(output_path, index=False, encoding="utf-8")
    print("Successfully completed! Shortlist is ready.")

if __name__ == "__main__":
    main()
