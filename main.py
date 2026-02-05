from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import uuid
from dotenv import load_dotenv
from core.manager import HoneyPotManager

# Load environment variables
load_dotenv(override=True)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agentic Honey-Pot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory
app.mount("/demo", StaticFiles(directory="static", html=True), name="static")

# Security: API Key for accessing this service
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    # In a real app, this might validate against a DB or env var
    # For this hackathon/demo, we'll accept any non-empty key or a specific one if set
    required_key = os.getenv("SERVICE_API_KEY") 
    if required_key and api_key_header != required_key:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )
    if not api_key_header:
         raise HTTPException(
            status_code=403, detail="Missing API Key"
        )
    return api_key_header

# Initialize Manager
manager = HoneyPotManager()

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class EngagementMetrics(BaseModel):
    start_time: float
    duration_seconds: float
    turn_count: int

class ChatResponse(BaseModel):
    scam_detected: bool
    response: str
    metadata: Optional[Dict[str, Any]] = None
    engagement_metrics: Optional[EngagementMetrics] = None

@app.get("/")
async def root():
    return {"status": "active", "system": "Agentic Honey-Pot"}

@app.post("/chat")
async def chat_endpoint(request: dict, api_key: str = Depends(get_api_key)):
    """
    Main endpoint for receiving scam messages.
    Requires X-API-Key header.
    Accepts: {"message": "..."} or {"conversation_id": "...", "message": "..."}
    """
    try:
        # Extract message from request (flexible format)
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=422, detail="Missing 'message' field")
        
        # Auto-generate conversation_id if not provided
        conversation_id = request.get("conversation_id") or str(uuid.uuid4())
        
        result = await manager.process_message(conversation_id, message)
        # Extract metrics from metadata if available (it was put there by manager)
        metrics_data = result["metadata"].get("engagement_metrics")
        
        return {
            "scam_detected": result["scam_detected"],
            "response": result["response"],
            "metadata": result["metadata"],
            "engagement_metrics": metrics_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
