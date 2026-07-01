from typing import List, Dict, Any
from models.schemas import ChatResponse, Recommendation
from retrieval.hybrid_search import perform_hybrid_search
from retrieval.reranker import rerank_results
from agents.llm_client import get_llm_client

class RecommenderAgent:
    def __init__(self):
        self.llm_client = get_llm_client()

    def handle(self, query_context: Dict[str, Any], messages: List[Dict[str, str]]) -> ChatResponse:
        role = query_context.get("role")
        seniority = query_context.get("seniority")
        skills = query_context.get("skills", [])
        
        # 1. Expand search query based on context details
        search_terms = [role, seniority]
        search_terms.extend(skills)
        
        if query_context.get("personality_testing"):
            search_terms.append("personality OPQ")
        if query_context.get("cognitive_testing"):
            search_terms.append("cognitive reasoning verify")
        if query_context.get("behavioral_testing"):
            search_terms.append("behavioral SJT GSA")
            
        search_query = " ".join(search_terms)
        
        # 2. Retrieve candidates via hybrid search
        # Fetch up to 10 candidates to re-rank
        candidates = perform_hybrid_search(search_query, top_k=8)
        
        # 3. Re-rank retrieved items using LLM reasoning
        latest_user_query = messages[-1]["content"]
        reranked_candidates = rerank_results(query_context, candidates, latest_user_query)
        
        # 4. Limit to top 1-10 assessments
        final_candidates = reranked_candidates[:5]  # Top 5 is a sweet spot for quality
        if not final_candidates:
             # Fallback if somehow empty
             final_candidates = candidates[:3]
             
        # 5. Generate conversational explanation via LLM
        # We pass the catalog info of the chosen final assessments to the LLM
        # to ensure it explains them accurately and conversationally.
        assessment_details = ""
        for idx, item in enumerate(final_candidates):
            assessment_details += (
                f"{idx+1}. {item['name']} (Type: {item['test_type']}, Duration: {item['duration']})\n"
                f"   Description: {item['description']}\n"
                f"   Skills measured: {', '.join(item['skills'])}\n\n"
            )
            
        system_instruction = (
            "You are an expert SHL Assessment consultant. "
            "You are helping a hiring manager select the best assessments for their role. "
            "Explain the recommended assessments clearly and conversationally. "
            "You MUST base your explanations strictly on the provided assessment details. "
            "Do not hallucinate facts, durations, or names. Mention how the recommended assessments "
            "align with the role's skills and seniority."
        )
        
        prompt = (
            f"Hiring Context:\n"
            f"Role: {role}\n"
            f"Seniority: {seniority}\n"
            f"Skills: {', '.join(skills)}\n\n"
            f"Selected Recommended Assessments:\n"
            f"{assessment_details}\n"
            f"Write a conversational response explaining why these specific assessments are recommended for this role."
        )
        
        try:
            reply_text = self.llm_client.generate(prompt, system_instruction=system_instruction)
        except Exception as e:
            print(f"Error generating recommendation explanation: {e}")
            reply_text = (
                f"Based on your requirements for a {seniority} {role}, I recommend the following SHL assessments:\n\n"
                + "\n".join([f"- **{c['name']}** ({c['test_type']}): {c['description']}" for c in final_candidates])
            )

        # Map to Recommendation Pydantic schemas
        recommendations_out = []
        for c in final_candidates:
             recommendations_out.append(
                 Recommendation(
                     name=c["name"],
                     url=c["url"],
                     test_type=c["test_type"]
                 )
             )
             
        # Conversation is considered completed once we deliver structured recommendations,
        # but the user can still ask follow-ups. We set end_of_conversation to True.
        # Wait, does the prompt require end_of_conversation to be true here? Yes, "recommendations provided: end_of_conversation=True".
        return ChatResponse(
            reply=reply_text,
            recommendations=recommendations_out,
            end_of_conversation=True
        )
