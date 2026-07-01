import os
# Configure environment overrides before other imports
os.environ["USE_TF"] = "NO"
os.environ["USE_TORCH"] = "YES"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="Conversational SHL Assessment Recommender",
    description="A stateless conversational AI agent to discover SHL assessments.",
    version="1.0.0"
)

# Configure CORS - open for automated test runners
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes at the root level
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Cloud platforms (Render, Railway, HuggingFace Spaces) inject PORT at runtime
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
