"""
FastAPI Backend for Autonomous Tutor
=====================================

This module provides REST API endpoints for the Autonomous Tutor system,
enabling frontend applications to interact with the various AI agents.

Endpoints:
- POST /api/chat - Main orchestrator endpoint for all interactions
- POST /api/ingest - Direct ingestion of content (PDFs, images, text)
- POST /api/tutor/ask - Direct tutor interaction
- POST /api/game/generate - Generate practice games
- GET /api/session/{session_id} - Get session state
- DELETE /api/session/{session_id} - Clear session
"""

import sys
from pathlib import Path

# Add backend directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime

from agents.orchestrator_agent import OrchestratorAgent
from agents.ingestion_agent import IngestionAgent
from agents.tutor_agent import TutorAgent
from agents.game_master_agent import GameMasterAgent
from core.session_state import SessionState
from services.file_loader import load_pdf_bytes, load_image_bytes, load_text_input

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title="Autonomous Tutor API",
    description="AI-powered adaptive learning system with multimodal content ingestion",
    version="1.0.0"
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

# In-memory session store (replace with Redis/DB in production)
sessions: Dict[str, SessionState] = {}

def get_or_create_session(session_id: Optional[str] = None) -> tuple[str, SessionState]:
    """Get existing session or create new one."""
    if session_id and session_id in sessions:
        return session_id, sessions[session_id]
    
    new_session_id = str(uuid.uuid4())
    sessions[new_session_id] = SessionState()
    return new_session_id, sessions[new_session_id]

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Main orchestrator request - handles all types of interactions."""
    session_id: Optional[str] = None
    type: str  # "text", "image", "pdf", "question", "practice"
    content: Optional[str] = None  # For text content or base64 encoded data
    question: Optional[str] = None  # For tutor questions
    game_type: Optional[str] = None  # "swipe_sort", "impostor", "match_pairs"
    nuances: Optional[List[str]] = []

class IngestRequest(BaseModel):
    """Direct ingestion request."""
    session_id: Optional[str] = None
    type: str  # "text", "image", "pdf"
    content: str  # Raw text or base64 encoded

class TutorRequest(BaseModel):
    """Direct tutor interaction request."""
    session_id: str
    question: str

class GameRequest(BaseModel):
    """Direct game generation request."""
    session_id: str
    game_type: str  # "swipe_sort", "impostor", "match_pairs"
    concept: Optional[str] = None  # Override current concept
    nuances: Optional[List[str]] = []

class ChatResponse(BaseModel):
    """Standard response for all interactions."""
    session_id: str
    response: Dict[str, Any]
    timestamp: str

# ============================================================================
# AGENT INITIALIZATION
# ============================================================================

orchestrator = OrchestratorAgent()
ingestion_agent = IngestionAgent()
tutor_agent = TutorAgent()
game_master_agent = GameMasterAgent()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Autonomous Tutor API",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "active_sessions": len(sessions),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main orchestrator endpoint - handles all user interactions.
    
    The orchestrator automatically routes to the appropriate agent based on:
    - type="text"|"image"|"pdf" -> Ingestion Agent
    - type="question" -> Tutor Agent
    - type="practice" -> Game Master Agent
    """
    try:
        session_id, session = get_or_create_session(request.session_id)
        
        # Prepare input data for orchestrator
        input_data = {
            "type": request.type,
        }
        
        if request.content:
            input_data["content"] = request.content
        if request.question:
            input_data["question"] = request.question
        if request.game_type:
            input_data["game_type"] = request.game_type
        if request.nuances:
            input_data["nuances"] = request.nuances
        
        # Process through orchestrator
        result = await orchestrator.handle(input_data, session)
        
        return ChatResponse(
            session_id=session_id,
            response=result,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest", response_model=ChatResponse)
async def ingest_content(request: IngestRequest):
    """
    Direct ingestion endpoint - process PDFs, images, or text.
    
    Returns structured knowledge artifact with:
    - core_concepts: List of main concepts
    - definitions: Term definitions and formulas
    - examples: Worked examples
    - diagram_descriptions: Visual elements
    - clean_markdown: Structured document
    """
    try:
        session_id, session = get_or_create_session(request.session_id)
        
        input_data = {
            "type": request.type,
            "content": request.content
        }
        
        result = await ingestion_agent.run(input_data)
        
        # Update session
        session.ingested_content = result
        session.last_agent = "ingestion"
        
        if result.get("core_concepts") and len(result["core_concepts"]) > 0:
            session.current_concept = result["core_concepts"][0]
        
        return ChatResponse(
            session_id=session_id,
            response={
                "status": "ingested",
                "message": "Content processed successfully",
                "data": result
            },
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tutor/ask", response_model=ChatResponse)
async def ask_tutor(request: TutorRequest):
    """
    Direct tutor interaction - ask questions about ingested content.
    
    The tutor adapts its explanation style based on:
    - Confusion level detection
    - Previous clarification requests
    - Understanding verification
    
    Note: Content must be ingested first via /api/ingest or /api/chat
    """
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        
        if not session.ingested_content:
            raise HTTPException(
                status_code=400,
                detail="No content ingested. Please ingest content first."
            )
        
        tutor_input = {
            "question": request.question,
            "notes": session.ingested_content["clean_markdown"]
        }
        
        tutor_state = {
            "confusion_level": session.confusion_level,
            "clarification_requests": session.clarification_requests,
            "understood": session.understood,
            "last_explanation_style": session.last_explanation_style
        }
        
        result = await tutor_agent.run(tutor_input, tutor_state)
        
        # Update session
        session.confusion_level = tutor_state["confusion_level"]
        session.clarification_requests = tutor_state["clarification_requests"]
        session.understood = tutor_state["understood"]
        session.last_explanation_style = tutor_state["last_explanation_style"]
        session.concept_understood = result.get("understood", False)
        session.last_agent = "tutor"
        
        return ChatResponse(
            session_id=request.session_id,
            response=result,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/game/generate", response_model=ChatResponse)
async def generate_game(request: GameRequest):
    """
    Generate practice game - creates active recall exercises.
    
    Game types:
    - swipe_sort: Binary classification (8-12 cards)
    - impostor: Find the subtle outlier (4 options)
    - match_pairs: Relational associations (5-8 pairs)
    
    Note: Concept must be understood first (via tutor interaction)
    """
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        
        if not session.concept_understood:
            raise HTTPException(
                status_code=400,
                detail="Concept not understood yet. Complete tutor interaction first."
            )
        
        # Determine concept
        concept = request.concept or session.current_concept
        if not concept and session.ingested_content:
            concepts = session.ingested_content.get("core_concepts", [])
            concept = concepts[0] if concepts else "general knowledge"
        
        if not concept:
            raise HTTPException(
                status_code=400,
                detail="No concept available. Ingest content first."
            )
        
        game_input = {
            "concept": concept,
            "nuances": request.nuances or [],
            "game_type": request.game_type
        }
        
        result = await game_master_agent.run(game_input)
        session.last_agent = "game_master"
        
        return ChatResponse(
            session_id=request.session_id,
            response=result,
            timestamp=datetime.utcnow().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get current session state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "state": {
            "has_content": session.ingested_content is not None,
            "current_concept": session.current_concept,
            "concept_understood": session.concept_understood,
            "confusion_level": session.confusion_level,
            "last_agent": session.last_agent,
            "history_count": len(session.history)
        }
    }

@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    """Clear/delete a session."""
    if session_id in sessions:
        del sessions[session_id]
        return {"message": "Session cleared successfully"}
    
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/session/new")
async def create_session():
    """Create a new session explicitly."""
    session_id, _ = get_or_create_session()
    return {
        "session_id": session_id,
        "message": "New session created"
    }

# ============================================================================
# FILE UPLOAD ENDPOINT (for direct file uploads from frontend)
# ============================================================================

@app.post("/api/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload a file (PDF, image, or text) directly.
    
    Handles multipart/form-data uploads from frontend.
    Supports: .pdf, .txt, .png, .jpg, .jpeg, .gif, .bmp, .webp
    """
    try:
        # Read file content
        content = await file.read()
        
        # Determine type from filename and process accordingly
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith('.txt'):
            # Text files - decode directly to UTF-8
            text_content = content.decode('utf-8')
            input_data = load_text_input(text_content)
            
        elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            # Image files - use file_loader for base64 encoding
            input_data = load_image_bytes(content)
            
        elif filename_lower.endswith('.pdf'):
            # PDF files - extract text using PyPDF2
            input_data = load_pdf_bytes(content)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Supported: .pdf, .txt, .png, .jpg, .jpeg, .gif, .bmp, .webp"
            )
        
        # Process through ingestion
        session_id, session = get_or_create_session(session_id)
        
        result = await ingestion_agent.run(input_data)
        
        # Update session
        session.ingested_content = result
        session.last_agent = "ingestion"
        
        if result.get("core_concepts") and len(result["core_concepts"]) > 0:
            session.current_concept = result["core_concepts"][0]
        
        return {
            "session_id": session_id,
            "response": {
                "status": "ingested",
                "message": f"File '{file.filename}' processed successfully",
                "data": result
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
