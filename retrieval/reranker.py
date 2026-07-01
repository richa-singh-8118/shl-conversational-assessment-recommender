import json
from typing import List, Dict, Any
from agents.llm_client import get_llm_client

def rerank_results(
    query_context: Dict[str, Any], 
    candidates: List[Dict[str, Any]], 
    user_query: str
) -> List[Dict[str, Any]]:
    if not candidates:
        return []
        
    # If there is only one candidate, no need to rerank
    if len(candidates) == 1:
        return candidates
        
    client = get_llm_client()
    
    # Format candidates list for LLM context
    candidates_list_str = ""
    for idx, c in enumerate(candidates):
        candidates_list_str += (
            f"Candidate {idx+1}:\n"
            f"Name: {c['name']}\n"
            f"URL: {c['url']}\n"
            f"Type: {c['test_type']}\n"
            f"Duration: {c['duration']}\n"
            f"Description: {c['description']}\n"
            f"Skills: {', '.join(c['skills'])}\n"
            f"---------------------------------\n"
        )
        
    system_instruction = (
        "You are an expert Talent Acquisition Agent and SHL Product specialist. "
        "Your task is to re-rank the retrieved SHL assessments based on how well they fit the recruiter's hiring context. "
        "Evaluate the candidate assessments strictly on their relevance to the target role, seniority, skills, and testing type (personality, cognitive, behavioral). "
        "You must return a JSON array of objects representing the re-ranked candidates. "
        "Each object must contain exactly: 'name', 'fit_score' (between 0.0 and 1.0), and 'explanation'. "
        "Do not include any text outside the JSON array. Output valid JSON only."
    )
    
    prompt = (
        f"Hiring Context:\n"
        f"Target Role: {query_context.get('role')}\n"
        f"Seniority: {query_context.get('seniority')}\n"
        f"Skills/Preferences: {', '.join(query_context.get('skills', []))}\n"
        f"User Query: {user_query}\n\n"
        f"Candidate SHL Assessments:\n"
        f"{candidates_list_str}\n"
        f"Re-rank the candidates and output the final array in JSON format."
    )
    
    try:
        response_text = client.generate(prompt, system_instruction=system_instruction, json_mode=True)
        
        # Clean response if markdown blocks are present
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        scores_list = json.loads(response_text)
        
        # Map score results by name
        scores_map = {}
        for item in scores_list:
            name = item.get("name")
            fit_score = item.get("fit_score", 0.0)
            explanation = item.get("explanation", "")
            if name:
                scores_map[name.lower()] = (fit_score, explanation)
                
        # Re-sort candidates based on LLM fit_score
        reranked_candidates = []
        for c in candidates:
            c_copy = c.copy()
            # Look up score (case-insensitive)
            lookup_key = c["name"].lower()
            if lookup_key in scores_map:
                c_copy["rerank_score"] = scores_map[lookup_key][0]
                c_copy["explanation"] = scores_map[lookup_key][1]
            else:
                # Try partial match
                matched = False
                for k, v in scores_map.items():
                    if k in lookup_key or lookup_key in k:
                        c_copy["rerank_score"] = v[0]
                        c_copy["explanation"] = v[1]
                        matched = True
                        break
                if not matched:
                    # Fallback to hybrid score
                    c_copy["rerank_score"] = c_copy.get("hybrid_score", 0.0)
                    c_copy["explanation"] = "Matches criteria."
                    
            reranked_candidates.append(c_copy)
            
        # Sort by rerank score
        reranked_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked_candidates
        
    except Exception as e:
        print(f"Reranker failed ({e}). Falling back to hybrid score ordering.")
        # Fallback to sorting by hybrid score
        for c in candidates:
            if "explanation" not in c:
                c["explanation"] = "Recommended based on skills match."
        return candidates
