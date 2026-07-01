import json
from typing import List, Dict, Any, Optional
from models.schemas import ChatResponse
from agents.llm_client import get_llm_client

class ClarifierAgent:
    def __init__(self):
        self.llm_client = get_llm_client()

    def extract_context(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Formulate history as a single string
        history_str = ""
        for m in messages:
            history_str += f"{m['role'].upper()}: {m['content']}\n"
            
        system_instruction = (
            "You are a talent acquisition data extractor. Your task is to extract the hiring context from the conversation history. "
            "You must return a JSON object with the following fields:\n"
            "- 'role': (string or null) The job title or role being hired for (e.g., 'Java Developer', 'Data Analyst', 'Customer Service').\n"
            "- 'seniority': (string or null) The seniority level (e.g., 'Junior', 'Mid-Level', 'Senior', 'Manager', 'Executive').\n"
            "- 'skills': (array of strings) Key skills or requirements mentioned (e.g., ['Java', 'SQL', 'Excel', 'English proficiency']).\n"
            "- 'personality_testing': (boolean or null) True if the user explicitly requested personality testing or OPQ.\n"
            "- 'cognitive_testing': (boolean or null) True if the user explicitly requested cognitive/aptitude testing or reasoning tests.\n"
            "- 'behavioral_testing': (boolean or null) True if the user requested behavioral assessments, collaboration, or SJTs.\n\n"
            "Analyze the history carefully. If the user corrects or refines an parameter (e.g., 'Actually make it senior'), "
            "the updated value must override the previous value. Output ONLY valid JSON."
        )
        
        prompt = f"Conversation History:\n{history_str}\n\nExtract and return the hiring context JSON."
        
        try:
            response_text = self.llm_client.generate(prompt, system_instruction=system_instruction, json_mode=True)
            
            # Clean markdown formatting if present
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            context = json.loads(response_text)
            
            # Post-process list fields to be lists
            if not isinstance(context.get("skills"), list):
                context["skills"] = []
                
            return context
        except Exception as e:
            print(f"Context extraction error: {e}. Falling back to default empty context.")
            return {
                "role": None,
                "seniority": None,
                "skills": [],
                "personality_testing": None,
                "cognitive_testing": None,
                "behavioral_testing": None
            }

    def check_and_clarify(self, context: Dict[str, Any]) -> Optional[ChatResponse]:
        # Rule 1: If role is missing, ask for role
        role = context.get("role")
        if not role or str(role).strip().lower() in ["null", "none", ""]:
            return ChatResponse(
                reply="To help me recommend the most suitable SHL assessments, could you please tell me what specific role or job title you are hiring for?",
                recommendations=[],
                end_of_conversation=False
            )
            
        # Rule 2: If seniority is missing, ask for seniority
        seniority = context.get("seniority")
        if not seniority or str(seniority).strip().lower() in ["null", "none", ""]:
            return ChatResponse(
                reply=f"Thanks! What is the seniority or experience level for the {role} role? (e.g., Entry-Level/Junior, Mid-Level, Senior, Manager, or Executive)",
                recommendations=[],
                end_of_conversation=False
            )
            
        # Context is complete, signal caller to run recommendations
        return None
