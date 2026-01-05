"""
Basic API Backend Example

Demonstrates how to use the API Backend component
for exposing SDK functionality via REST API.

Dependencies: Agent Framework, LiteLLM Gateway, RAG
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.core.api_backend_services import APIService


# Request/Response Models
class GenerateRequest(BaseModel):
    prompt: str
    model: str = "gpt-4"
    max_tokens: int = 1000


class GenerateResponse(BaseModel):
    text: str
    model: str
    tokens_used: int


class RAGQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    threshold: float = 0.7


class RAGQueryResponse(BaseModel):
    answer: str
    retrieved_documents: list
    num_documents: int


def create_app():
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Motadata AI SDK API",
        description="REST API for AI SDK functionality",
        version="1.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize API service
    api_service = APIService()
    
    # 1. Health Check Endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "motadata-ai-sdk"}
    
    # 2. Text Generation Endpoint
    @app.post("/generate", response_model=GenerateResponse)
    async def generate_text(request: GenerateRequest):
        """Generate text using LLM."""
        try:
            result = await api_service.generate_text(
                prompt=request.prompt,
                model=request.model,
                max_tokens=request.max_tokens
            )
            return GenerateResponse(
                text=result["text"],
                model=result["model"],
                tokens_used=result.get("tokens_used", 0)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 3. RAG Query Endpoint
    @app.post("/rag/query", response_model=RAGQueryResponse)
    async def rag_query(request: RAGQueryRequest):
        """Query RAG system."""
        try:
            result = await api_service.rag_query(
                query=request.query,
                top_k=request.top_k,
                threshold=request.threshold
            )
            return RAGQueryResponse(
                answer=result["answer"],
                retrieved_documents=result["retrieved_documents"],
                num_documents=result["num_documents"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 4. Agent Task Endpoint
    @app.post("/agent/task")
    async def agent_task(task_type: str, parameters: dict):
        """Execute agent task."""
        try:
            result = await api_service.execute_agent_task(
                task_type=task_type,
                parameters=parameters
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    # 5. Embeddings Endpoint
    @app.post("/embeddings")
    async def create_embeddings(texts: list[str], model: str = "text-embedding-3-small"):
        """Create embeddings for texts."""
        try:
            result = await api_service.create_embeddings(
                texts=texts,
                model=model
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


def main():
    """Run the API server."""
    app = create_app()
    
    print("🚀 Starting API server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()

