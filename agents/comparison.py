import os
import json
from typing import List, Dict, Any
from models.schemas import ChatResponse
from agents.llm_client import get_llm_client

class ComparisonAgent:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.catalog_path = os.path.join(base_dir, "catalog", "catalog.json")
        with open(self.catalog_path, "r", encoding="utf-8") as f:
            self.catalog = json.load(f)
        self.llm_client = get_llm_client()

    def _find_matching_assessments(self, text: str) -> List[Dict[str, Any]]:
        text_lower = text.lower()
        matches = []
        
        # Match keywords for different tests in catalog
        for item in self.catalog:
            name = item["name"]
            # Extract main identifier (e.g. OPQ32r, GSA, MQ, SJT, Verify, Excel, etc.)
            identifiers = []
            if "opq" in name.lower() or "personality" in name.lower():
                identifiers.extend(["opq", "opq32r", "personality questionnaire"])
            if "gsa" in name.lower() or "global skills" in name.lower():
                identifiers.extend(["gsa", "global skills"])
            if "mq" in name.lower() or "motivation" in name.lower():
                identifiers.extend(["mq", "motivation questionnaire"])
            if "sjt" in name.lower() or "situational judgment" in name.lower():
                identifiers.extend(["sjt", "situational judgment"])
            if "verify" in name.lower():
                identifiers.append("verify")
                if "numerical" in name.lower():
                    identifiers.append("numerical")
                if "verbal" in name.lower():
                    identifiers.append("verbal")
                if "inductive" in name.lower():
                    identifiers.append("inductive")
                if "deductive" in name.lower():
                    identifiers.append("deductive")
            if "coding" in name.lower():
                identifiers.append("coding")
                if "java" in name.lower():
                    identifiers.append("java")
                if "python" in name.lower():
                    identifiers.append("python")
                if "react" in name.lower() or "frontend" in name.lower():
                    identifiers.append("react")
                if "sql" in name.lower():
                    identifiers.append("sql")
            if "excel" in name.lower():
                identifiers.append("excel")
            if "language" in name.lower() or "english" in name.lower():
                identifiers.extend(["language", "english"])
            if "call center" in name.lower():
                identifiers.append("call center")
                
            for identifier in identifiers:
                if identifier in text_lower:
                    matches.append(item)
                    break
                    
        # Deduplicate matches
        unique_matches = []
        seen_names = set()
        for m in matches:
            if m["name"] not in seen_names:
                unique_matches.append(m)
                seen_names.add(m["name"])
                
        return unique_matches

    def handle(self, messages: List[Dict[str, str]]) -> ChatResponse:
        latest_message = messages[-1]["content"]
        
        # Try to find assessments mentioned in query
        matched_assessments = self._find_matching_assessments(latest_message)
        
        # If we didn't find specific ones, let's look at the history
        if len(matched_assessments) < 2 and len(messages) > 1:
            for msg in reversed(messages[:-1]):
                history_matches = self._find_matching_assessments(msg["content"])
                for hm in history_matches:
                    if hm["name"] not in [m["name"] for m in matched_assessments]:
                        matched_assessments.append(hm)
                if len(matched_assessments) >= 2:
                    break
                    
        # If we found at least one, we can build a comparison table based strictly on catalog content
        if matched_assessments:
            # Build markdown table comparison
            reply = "### SHL Assessment Comparison\n\n"
            reply += "Here is a comparison of the requested assessments based strictly on the SHL Catalog:\n\n"
            
            # Table Header
            reply += "| Feature | " + " | ".join([f"**{item['name']}**" for item in matched_assessments]) + " |\n"
            reply += "| --- | " + " | ".join(["---" for _ in matched_assessments]) + " |\n"
            
            # Type
            reply += "| **Test Type** | " + " | ".join([item['test_type'] for item in matched_assessments]) + " |\n"
            
            # Duration
            reply += "| **Duration** | " + " | ".join([item['duration'] for item in matched_assessments]) + " |\n"
            
            # Skills Covered
            reply += "| **Skills Covered** | " + " | ".join([", ".join(item['skills']) for item in matched_assessments]) + " |\n"
            
            # Description
            reply += "| **Description** | " + " | ".join([item['description'] for item in matched_assessments]) + " |\n"
            
            # Catalog URL
            reply += "| **Product URL** | " + " | ".join([f"[Product Link]({item['url']})" for item in matched_assessments]) + " |\n"
            
            return ChatResponse(
                reply=reply,
                recommendations=[],
                end_of_conversation=False
            )
            
        # If no specific matches found, use the LLM but pass the entire catalog as context to ensure no hallucination
        catalog_summary = ""
        for idx, item in enumerate(self.catalog):
            catalog_summary += f"{idx+1}. Name: {item['name']}\nType: {item['test_type']}\nDuration: {item['duration']}\nDescription: {item['description']}\nSkills: {', '.join(item['skills'])}\n\n"
            
        system_instruction = (
            "You are an SHL product consultant. A user has asked to compare assessments. "
            "You must compare them using ONLY the provided catalog data below. "
            "If the user asks to compare assessments that are not in the catalog, politely state that you can only compare products in the catalog. "
            "Never fabricate any information, durations, or URLs. "
            "Format your reply as a clear Markdown comparison table."
        )
        
        prompt = (
            f"SHL Catalog Data:\n{catalog_summary}\n\n"
            f"User Question: {latest_message}\n\n"
            f"Provide a comparative answer using ONLY the catalog data. Output a markdown table."
        )
        
        reply_text = self.llm_client.generate(prompt, system_instruction=system_instruction)
        return ChatResponse(
            reply=reply_text,
            recommendations=[],
            end_of_conversation=False
        )
