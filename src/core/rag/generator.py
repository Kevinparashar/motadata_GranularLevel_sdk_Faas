"""
Generator

Handles LLM generation with retrieved context.
"""

from typing import List, Dict, Any, Optional
from ..litellm_gateway import LiteLLMGateway
from .hallucination_detector import HallucinationDetector, create_hallucination_detector, HallucinationResult


class RAGGenerator:
    """
    RAG generator that combines retrieval with generation.
    
    Uses retrieved documents as context for LLM generation.
    """
    
    def __init__(
        self,
        gateway: LiteLLMGateway,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None,
        enable_hallucination_detection: bool = True
    ):
        """
        Initialize RAG generator.
        
        Args:
            gateway: LiteLLM gateway instance
            model: LLM model to use
            system_prompt: Optional system prompt
            enable_hallucination_detection: Whether to enable hallucination detection
        """
        self.gateway = gateway
        self.model = model
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.enable_hallucination_detection = enable_hallucination_detection
        
        # Initialize hallucination detector
        self.hallucination_detector: Optional[HallucinationDetector] = None
        if self.enable_hallucination_detection:
            self.hallucination_detector = create_hallucination_detector(
                gateway=gateway,
                enable_llm_verification=True
            )
    
    def generate(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        check_hallucination: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate response using retrieved context.
        
        Args:
            query: User query
            context_documents: Retrieved context documents
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            check_hallucination: Whether to check for hallucinations (default: uses instance setting)
        
        Returns:
            Dictionary with 'response' and optionally 'hallucination_result'
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
        
        result = {
            "response": response.text,
            "model": response.model,
            "usage": response.usage
        }
        
        # Check for hallucinations if enabled
        should_check = check_hallucination if check_hallucination is not None else self.enable_hallucination_detection
        if should_check and self.hallucination_detector:
            hallucination_result = self.hallucination_detector.detect(
                response=response.text,
                context_documents=context_documents,
                query=query
            )
            result["hallucination_result"] = hallucination_result.to_dict()
            result["is_hallucination"] = hallucination_result.is_hallucination
        
        return result
    
    async def generate_async(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        check_hallucination: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate response asynchronously.
        
        Args:
            query: User query
            context_documents: Retrieved context documents
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            check_hallucination: Whether to check for hallucinations (default: uses instance setting)
        
        Returns:
            Dictionary with 'response' and optionally 'hallucination_result'
        """
        context = self._build_context(context_documents)
        prompt = self._build_prompt(query, context)
        
        response = await self.gateway.generate_async(
            prompt=prompt,
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        result = {
            "response": response.text,
            "model": response.model,
            "usage": response.usage
        }
        
        # Check for hallucinations if enabled
        should_check = check_hallucination if check_hallucination is not None else self.enable_hallucination_detection
        if should_check and self.hallucination_detector:
            hallucination_result = await self.hallucination_detector.detect_async(
                response=response.text,
                context_documents=context_documents,
                query=query
            )
            result["hallucination_result"] = hallucination_result.to_dict()
            result["is_hallucination"] = hallucination_result.is_hallucination
        
        return result
    
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

