"""
Basic API Backend Example

Demonstrates how to use the API Backend component
for exposing SDK functionality via REST API.

Dependencies: Agent Framework, LiteLLM Gateway, RAG
"""

# Standard library imports
import sys
from pathlib import Path
from typing import Dict, Any, List

# Third-party imports
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if load_dotenv:
    load_dotenv(project_root / ".env")

# Local application/library specific imports
from src.core.api_backend_services import create_api_app, add_health_check


# Request/Response Models
class GenerateRequest(BaseModel):
    """Request model for text generation."""

    prompt: str
    model: str = "gpt-4"
    max_tokens: int = 1000


class GenerateResponse(BaseModel):
    """Response model for text generation."""

    text: str
    model: str
    tokens_used: int


class RAGQueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str
    top_k: int = 5
    threshold: float = 0.7


class RAGQueryResponse(BaseModel):
    """Response model for RAG queries."""

    answer: str
    retrieved_documents: list
    num_documents: int


def _handle_generation_endpoint(app: FastAPI) -> None:
    """Add text generation endpoint to app."""

    @app.post("/generate", response_model=GenerateResponse)
    async def generate_text(request: GenerateRequest):
        """Generate text using LLM."""
        try:
            # Note: In production, initialize LiteLLMGateway and use it here
            # For this example, we demonstrate the endpoint structure
            result = {
                "text": f"Generated response for: {request.prompt}",
                "model": request.model,
                "tokens_used": len(request.prompt.split()) + request.max_tokens,
            }
            return GenerateResponse(
                text=result["text"],
                model=result["model"],
                tokens_used=result.get("tokens_used", 0),
            )
        except (ConnectionError, TimeoutError, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"Error generating text: {str(e)}")


def _handle_rag_endpoint(app: FastAPI) -> None:
    """Add RAG query endpoint to app."""

    @app.post("/rag/query", response_model=RAGQueryResponse)
    async def rag_query(request: RAGQueryRequest):
        """Query RAG system."""
        try:
            # Note: In production, initialize RAGSystem and use it here
            result = {
                "answer": f"Answer for: {request.query}",
                "retrieved_documents": [],
                "num_documents": 0,
            }
            return RAGQueryResponse(
                answer=result["answer"],
                retrieved_documents=result["retrieved_documents"],
                num_documents=result["num_documents"],
            )
        except (ConnectionError, TimeoutError, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"Error querying RAG: {str(e)}")


def _handle_agent_endpoint(app: FastAPI) -> None:
    """Add agent task endpoint to app."""

    @app.post("/agent/task")
    async def agent_task(task_type: str, parameters: Dict[str, Any]):
        """Execute agent task."""
        try:
            # Note: In production, initialize Agent and use it here
            result = {"task_type": task_type, "status": "completed", "result": parameters}
            return result
        except (ConnectionError, TimeoutError, ValueError) as e:
            raise HTTPException(
                status_code=500, detail=f"Error executing agent task: {str(e)}"
            )


def _handle_embeddings_endpoint(app: FastAPI) -> None:
    """Add embeddings endpoint to app."""

    @app.post("/embeddings")
    async def create_embeddings_endpoint(texts: List[str], model: str = "text-embedding-3-small"):
        """Create embeddings for texts."""
        try:
            # Note: In production, use LiteLLMGateway to generate actual embeddings
            result = {"embeddings": [[0.0] * 1536 for _ in texts], "model": model}
            return result
        except (ConnectionError, TimeoutError, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    # Use SDK's factory function to create app with CORS
    app = create_api_app(
        title="Motadata AI SDK API",
        description="REST API for AI SDK functionality",
        version="1.0.0",
        enable_cors=True,
        cors_origins=["*"],
    )

    # Add health check using SDK function
    add_health_check(app)

    # Register endpoints
    _handle_generation_endpoint(app)
    _handle_rag_endpoint(app)
    _handle_agent_endpoint(app)
    _handle_embeddings_endpoint(app)

    return app


def main():
    """Run the API server."""
    app = create_app()

    print("🚀 Starting API server...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
