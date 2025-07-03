"""
FastAPI application for Mairie Radar backend.

This module provides REST API endpoints for interacting with the
budget anomaly detection system and its agents.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio

from ..core.config import get_settings
from ..core.logging import setup_logging, get_logger
from ..agents.test_agent import create_test_agent


# Setup logging
setup_logging()
logger = get_logger("api.main")

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Mairie Radar API",
    description="AI-powered system for detecting budget anomalies in French city halls",
    version="0.1.0",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global test agent instance
test_agent = None


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    
class ChatResponse(BaseModel):
    response: str
    confidence: float
    agent_id: str

class AnalysisRequest(BaseModel):
    text: str
    analysis_type: str = "general"
    
class AnalysisResponse(BaseModel):
    analysis: str
    insights: list[str]
    agent_id: str

class HealthResponse(BaseModel):
    status: str
    version: str
    agent_status: str


@app.on_event("startup")
async def startup_event():
    """Initialize the application and test agent."""
    global test_agent
    
    logger.info("Starting Mairie Radar API")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # Initialize test agent
        test_agent = create_test_agent()
        if await test_agent.initialize():
            logger.info("Test agent initialized successfully")
        else:
            logger.error("Failed to initialize test agent")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Mairie Radar API")


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint providing API health status."""
    agent_status = "initialized" if test_agent and test_agent.llm else "not_initialized"
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        agent_status=agent_status
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    agent_status = "initialized" if test_agent and test_agent.llm else "not_initialized"
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        agent_status=agent_status
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Chat with the test agent."""
    if not test_agent:
        raise HTTPException(status_code=503, detail="Test agent not available")
    
    if not test_agent.llm:
        raise HTTPException(status_code=503, detail="Test agent not initialized")
    
    try:
        logger.info(f"Chat request: {request.message[:50]}...")
        
        result = await test_agent._handle_chat(request.message)
        
        logger.info(f"Chat response generated with confidence: {result['confidence']}")
        
        return ChatResponse(
            response=result["response"],
            confidence=result["confidence"],
            agent_id=test_agent.agent_id
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """Analyze text using the test agent."""
    if not test_agent:
        raise HTTPException(status_code=503, detail="Test agent not available")
    
    if not test_agent.llm:
        raise HTTPException(status_code=503, detail="Test agent not initialized")
    
    try:
        logger.info(f"Analysis request: {request.analysis_type} for {len(request.text)} characters")
        
        result = await test_agent._handle_text_analysis(request.text, request.analysis_type)
        
        logger.info(f"Analysis completed with {len(result['insights'])} insights")
        
        return AnalysisResponse(
            analysis=result["analysis"],
            insights=result["insights"],
            agent_id=test_agent.agent_id
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/capabilities")
async def get_agent_capabilities():
    """Get the capabilities of the test agent."""
    if not test_agent:
        raise HTTPException(status_code=503, detail="Test agent not available")
    
    try:
        capabilities = test_agent.get_capabilities()
        return {
            "agent_id": test_agent.agent_id,
            "agent_name": test_agent.name,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "input_schema": cap.input_schema,
                    "output_schema": cap.output_schema
                }
                for cap in capabilities
            ]
        }
    except Exception as e:
        logger.error(f"Error getting capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get public configuration information."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "features": {
            "anomaly_detection": settings.enable_anomaly_detection,
            "batch_processing": settings.enable_batch_processing,
            "web_scraping": settings.enable_web_scraping,
            "pdf_processing": settings.enable_pdf_processing,
        }
    }


def main():
    """Entry point for running the API server."""
    import uvicorn
    
    logger.info("Starting Mairie Radar API server")
    
    uvicorn.run(
        "backend.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload and settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main() 