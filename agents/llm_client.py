import os
import json
import re
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Use the new google-genai SDK (v2+)
from google import genai
from google.genai import types as genai_types

load_dotenv()

# Set env overrides
os.environ["USE_TF"] = "NO"
os.environ["USE_TORCH"] = "YES"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.use_api = self.api_key is not None
        
        if self.use_api:
            try:
                self._client = genai.Client(api_key=self.api_key)
                # gemini-2.0-flash is the recommended efficient model
                self.model_name = "gemini-2.0-flash"
                print(f"Gemini API configured successfully with model {self.model_name}.")
            except Exception as e:
                print(f"Error configuring Gemini API: {e}. Falling back to simulated mode.")
                self.use_api = False
        else:
            print("No GEMINI_API_KEY environment variable found. Running in simulated fallback mode.")

    def generate(self, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> str:
        if self.use_api:
            try:
                config_kwargs = {}
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction
                if json_mode:
                    config_kwargs["response_mime_type"] = "application/json"
                config = genai_types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                print(f"Gemini API call failed ({e}). Falling back to simulated heuristics.")
        
        return self._simulate_response(prompt, system_instruction)

    def _simulate_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        prompt_lower = prompt.lower()
        sys_lower = (system_instruction or "").lower()
        
        # 1. Classifier Agent Simulation
        if "classify" in sys_lower or "classification" in sys_lower:
            # Check for refusal triggers in prompt
            refusal_keywords = [
                "salary", "pay scale", "how much", "legal advice", "hr consulting", "contract law",
                "ignore previous", "system prompt", "aws certification", "non-shl", "microsoft cert",
                "hiring strategy", "interview advice"
            ]
            if any(kw in prompt_lower for kw in refusal_keywords):
                return "REFUSAL"
            if "compare" in prompt_lower or "difference between" in prompt_lower or "versus" in prompt_lower or " vs " in prompt_lower:
                return "COMPARISON"
            return "RECOMMENDATION"
            
        # 2. Refusal Agent Simulation
        if "refusal" in sys_lower:
            return "I can only help with SHL assessments from the SHL catalog."
            
        # 3. Context Extraction Agent Simulation
        if "extract" in sys_lower or "context object" in sys_lower:
            role = None
            seniority = None
            skills = []
            personality = False
            cognitive = False
            behavioral = False
            
            # Simple keyword extraction rules
            if "java" in prompt_lower:
                role = "Java Developer"
                skills.append("Java")
            elif "excel" in prompt_lower:
                role = "Office Assistant"
                skills.append("Microsoft Excel")
            elif "developer" in prompt_lower or "engineer" in prompt_lower:
                role = "Software Developer"
            elif "support" in prompt_lower or "customer" in prompt_lower or "call center" in prompt_lower:
                role = "Customer Service Representative"
                skills.append("Customer Service")
                
            if "senior" in prompt_lower:
                seniority = "Senior"
            elif "junior" in prompt_lower:
                seniority = "Junior"
            elif "mid" in prompt_lower or "middle" in prompt_lower:
                seniority = "Mid"
                
            if "personality" in prompt_lower or "opq" in prompt_lower:
                personality = True
            if "cognitive" in prompt_lower or "verify" in prompt_lower or "logic" in prompt_lower or "reasoning" in prompt_lower:
                cognitive = True
            if "behavioral" in prompt_lower or "sjt" in prompt_lower or "gsa" in prompt_lower:
                behavioral = True
                
            result = {
                "role": role,
                "seniority": seniority,
                "skills": skills,
                "personality_testing": personality,
                "cognitive_testing": cognitive,
                "behavioral_testing": behavioral
            }
            return json.dumps(result)
            
        # 4. Reranker Agent Simulation
        if "rerank" in sys_lower or "re-rank" in sys_lower:
            # Parse names and build simple match scores
            try:
                # Find JSON lists or extract candidate names
                lines = prompt.split("\n")
                candidates = []
                for line in lines:
                    if "name" in line.lower() or "SHL" in line:
                        match = re.search(r'["\']?name["\']?\s*:\s*["\']([^"\']+)["\']', line)
                        if match:
                            candidates.append(match.group(1))
                        else:
                            # Extract any SHL test name
                            name_match = re.search(r'(SHL\s+[A-Za-z0-9\s()+-]+)', line)
                            if name_match:
                                candidates.append(name_match.group(1).strip())
                
                # Deduplicate candidates list
                seen = set()
                candidates = [x for x in candidates if not (x in seen or seen.add(x))]
                
                reranked = []
                for idx, c in enumerate(candidates):
                    # Give higher scores to items matching query keywords
                    fit_score = 0.8 - (idx * 0.05)
                    if "java" in prompt_lower and "Java" in c:
                        fit_score = 0.95
                    elif "excel" in prompt_lower and "Excel" in c:
                        fit_score = 0.95
                    elif "personality" in prompt_lower and "OPQ" in c:
                        fit_score = 0.95
                        
                    reranked.append({
                        "name": c,
                        "fit_score": fit_score,
                        "explanation": f"Assessment matches the role requirements and skills."
                    })
                return json.dumps(reranked)
            except Exception as e:
                print(f"Error in reranking simulation: {e}")
                return "[]"
                
        # 5. General response fallback
        return "I can assist you in identifying SHL assessments from the product catalog."

# Singleton getter
_llm_client = None
def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
