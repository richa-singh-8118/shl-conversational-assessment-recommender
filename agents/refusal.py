from typing import Dict, Any, List
from models.schemas import ChatResponse

class RefusalAgent:
    def handle(self, messages: List[Dict[str, str]]) -> ChatResponse:
        # A standard, friendly, compliance-ready refusal response
        return ChatResponse(
            reply="I can only help with SHL assessments from the SHL catalog.",
            recommendations=[],
            end_of_conversation=False
        )
