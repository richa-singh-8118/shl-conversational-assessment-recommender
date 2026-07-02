from fastapi import APIRouter, HTTPException
from models.schemas import ChatRequest, ChatResponse
from agents.classifier import ClassifierAgent
from agents.refusal import RefusalAgent
from agents.comparison import ComparisonAgent
from agents.clarifier import ClarifierAgent
from agents.recommender import RecommenderAgent

router = APIRouter()

# Initialize agents
classifier_agent = ClassifierAgent()
refusal_agent = RefusalAgent()
comparison_agent = ComparisonAgent()
clarifier_agent = ClarifierAgent()
recommender_agent = RecommenderAgent()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        # Convert Pydantic request messages to list of dicts
        messages_dict = [m.model_dump() for m in request.messages]
        
        if not messages_dict:
             raise HTTPException(status_code=400, detail="Messages list cannot be empty.")
             
        # 1. Classification Step
        category = classifier_agent.classify(messages_dict)
        print(f"User query classified as: {category}")
        
        # 2. Routing based on Classification
        if category == "REFUSAL":
             return refusal_agent.handle(messages_dict)
             
        elif category == "COMPARISON":
             return comparison_agent.handle(messages_dict)
             
        else: # RECOMMENDATION flow
             # Extract structured context from conversation history
             context = clarifier_agent.extract_context(messages_dict)
             print(f"Extracted context: {context}")
             
             # Format context for UI
             focus_areas = []
             if context.get("cognitive_testing"): focus_areas.append("cognitive")
             if context.get("personality_testing"): focus_areas.append("personality")
             if context.get("behavioral_testing"): focus_areas.append("behavioral")
             context["focus_areas"] = focus_areas
             
             # Check if we need clarification (missing role or seniority)
             clarification_response = clarifier_agent.check_and_clarify(context)
             if clarification_response is not None:
                  print("Context incomplete. Returning clarification prompt.")
                  clarification_response.context = context
                  return clarification_response
                  
             # If context is complete, proceed to retrieval and recommendation
             print("Context complete. Fetching recommendations...")
             response = recommender_agent.handle(context, messages_dict)
             response.context = context
             return response
             
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
