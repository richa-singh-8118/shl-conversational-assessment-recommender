import re
from typing import List, Dict, Any
from retrieval.vectorstore import get_vector_store

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'for', 'with', 'in', 'on', 'at', 'by',
    'about', 'to', 'of', 'i', 'need', 'test', 'assessment', 'assessments', 'solutions', 'solution',
    'hiring', 'recruiting', 'candidate', 'candidates', 'role', 'roles', 'want', 'please', 'include', 'actually'
}

def tokenize(text: str) -> List[str]:
    # Extract alphanumeric tokens and convert to lowercase
    tokens = re.findall(r'\b\w+\b', text.lower())
    return [t for t in tokens if t not in STOPWORDS]

def get_keyword_score(item: Dict[str, Any], query_tokens: List[str]) -> float:
    if not query_tokens:
        return 0.0
        
    score = 0.0
    name_lower = item["name"].lower()
    desc_lower = item["description"].lower()
    type_lower = item["test_type"].lower()
    skills_lower = [s.lower() for s in item["skills"]]
    
    # Exact keyword check for each query token
    for token in query_tokens:
        # Match in Name (Weight: 3.0)
        if token in name_lower:
            score += 3.0
        # Match in Skills list (Weight: 2.5)
        for skill in skills_lower:
            if token in skill:
                score += 2.5
                break
        # Match in Test Type (Weight: 1.5)
        if token in type_lower:
            score += 1.5
        # Match in Description (Weight: 1.0)
        if token in desc_lower:
            score += 1.0
            
    # Normalize score
    return min(score / (len(query_tokens) * 3.0), 1.0)

def perform_hybrid_search(query: str, top_k: int = 10, vector_weight: float = 0.7) -> List[Dict[str, Any]]:
    # Get vector search results (fetch a slightly larger set to merge)
    store = get_vector_store()
    vector_results = store.search(query, top_k=top_k * 2)
    
    # Tokenize the query for keyword search
    query_tokens = tokenize(query)
    
    # We will score ALL metadata items for keyword match
    # and combine with their vector scores
    all_items = store.metadata
    
    merged_results = []
    vector_map = {item["name"]: item["vector_score"] for item in vector_results}
    
    for item in all_items:
        name = item["name"]
        
        # Get vector score if it was in the top vector results, otherwise default to a small number
        v_score = vector_map.get(name, 0.0)
        
        # Get keyword score
        kw_score = get_keyword_score(item, query_tokens)
        
        # Calculate hybrid score
        hybrid_score = (vector_weight * v_score) + ((1.0 - vector_weight) * kw_score)
        
        # Only include if there is some semantic or keyword overlap
        if v_score > 0.1 or kw_score > 0.0:
            result_item = item.copy()
            result_item["vector_score"] = v_score
            result_item["keyword_score"] = kw_score
            result_item["hybrid_score"] = hybrid_score
            merged_results.append(result_item)
            
    # Sort by hybrid score in descending order
    merged_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    
    # Return top K results
    return merged_results[:top_k]
