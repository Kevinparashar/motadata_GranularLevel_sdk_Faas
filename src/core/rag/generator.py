"""
Generator

Handles LLM generation with retrieved context.
"""

from typing import List, Dict, Any, Optional
from ..litellm_gateway import LiteLLMGateway


class RAGGenerator:
    """
    RAG generator that combines retrieval with generation.
    
    Uses retrieved documents as context for LLM generation.
    """
    
    def __init__(
        self,
        gateway: LiteLLMGateway,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize RAG generator.
        
        Args:
            gateway: LiteLLM gateway instance
            model: LLM model to use
            system_prompt: Optional system prompt
        """
        self.gateway = gateway
        self.model = model
        self.system_prompt = system_prompt or self._default_system_prompt()
    
    def generate(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response using retrieved context.
        
        Args:
            query: User query
            context_documents: Retrieved context documents
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        
        Returns:
            Generated response
        """
        # Build context from documents
        context = self._build_context(context_documents)
        
        # Build prompt with context
        prompt = self._build_prompt(query, context)
        
        # Generate response
        response = self.gateway.generate(
            prompt=prompt,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.text
    
    async def generate_async(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response asynchronously.
        
        Args:
            query: User query
            context_documents: Retrieved context documents
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
        
        Returns:
            Generated response
        """
        context = self._build_context(context_documents)
        prompt = self._build_prompt(query, context)
        
        response = await self.gateway.generate_async(
            prompt=prompt,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.text
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from documents.
        
        Args:
            documents: Retrieved documents
        
        Returns:
            Context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            title = doc.get('title', f'Document {i}')
            content = doc.get('content', '')
            similarity = doc.get('similarity', 0.0)
            
            context_parts.append(
                f"[Document {i}: {title} (Similarity: {similarity:.3f})]\n{content}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with query and context.
        
        Args:
            query: User query
            context: Retrieved context
        
        Returns:
            Formatted prompt
        """
        return f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
    
    def _default_system_prompt(self) -> str:
        """Get default system prompt."""
        return """You are a helpful assistant that answers questions based on the provided context.
Use only the information from the context to answer questions. If the context doesn't contain
enough information to answer the question, say so. Be accurate and cite specific parts of
the context when possible."""

