"""
Generator

Handles LLM generation with retrieved context.
"""


from typing import Any, Dict, List, Optional

from ..litellm_gateway import LiteLLMGateway
from .hallucination_detector import (
    HallucinationDetector,
    create_hallucination_detector,
)


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
        enable_hallucination_detection: bool = True,
    ):
        """
        Initialize RAG generator.
        
        Args:
            gateway (LiteLLMGateway): Gateway client used for LLM calls.
            model (str): Model name or identifier to use.
            system_prompt (Optional[str]): System prompt used to guide behaviour.
            enable_hallucination_detection (bool): Flag to enable or disable hallucination detection.
        """
        self.gateway = gateway
        self.model = model
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.enable_hallucination_detection = enable_hallucination_detection

        # Initialize hallucination detector
        self.hallucination_detector: Optional[HallucinationDetector] = None
        if self.enable_hallucination_detection:
            self.hallucination_detector = create_hallucination_detector(
                gateway=gateway, enable_llm_verification=True
            )

    def generate(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        check_hallucination: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Generate response using retrieved context.
        
        Args:
            query (str): Input parameter for this operation.
            context_documents (List[Dict[str, Any]]): Input parameter for this operation.
            max_tokens (int): Input parameter for this operation.
            temperature (float): Input parameter for this operation.
            check_hallucination (Optional[bool]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        import asyncio

        # Call async method from sync context
        return asyncio.run(
            self.generate_async(
                query=query,
                context_documents=context_documents,
                max_tokens=max_tokens,
                temperature=temperature,
                check_hallucination=check_hallucination,
            )
        )

    async def generate_async(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        check_hallucination: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Generate response asynchronously.
        
        Args:
            query (str): Input parameter for this operation.
            context_documents (List[Dict[str, Any]]): Input parameter for this operation.
            max_tokens (int): Input parameter for this operation.
            temperature (float): Input parameter for this operation.
            check_hallucination (Optional[bool]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        context = self._build_context(context_documents)
        prompt = self._build_prompt(query, context)

        response = await self.gateway.generate_async(
            prompt=prompt, model=self.model, max_tokens=max_tokens, temperature=temperature
        )

        result = {"response": response.text, "model": response.model, "usage": response.usage}

        # Check for hallucinations if enabled
        should_check = (
            check_hallucination
            if check_hallucination is not None
            else self.enable_hallucination_detection
        )
        if should_check and self.hallucination_detector:
            hallucination_result = await self.hallucination_detector.detect_async(
                response=response.text, context_documents=context_documents, query=query
            )
            result["hallucination_result"] = hallucination_result.to_dict()
            result["is_hallucination"] = hallucination_result.is_hallucination

        return result

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from documents.
        
        Args:
            documents (List[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            title = doc.get("title", f"Document {i}")
            content = doc.get("content", "")
            similarity = doc.get("similarity", 0.0)

            context_parts.append(
                f"[Document {i}: {title} (Similarity: {similarity:.3f})]\n{content}\n"
            )

        return "\n---\n".join(context_parts)

    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build prompt with query and context.
        
        Args:
            query (str): Input parameter for this operation.
            context (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        return f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""

    def _default_system_prompt(self) -> str:
        """
        Get default system prompt.
        
        Returns:
            str: Returned text value.
        """
        return """You are a helpful assistant that answers questions based on the provided context.
Use only the information from the context to answer questions. If the context doesn't contain
enough information to answer the question, say so. Be accurate and cite specific parts of
the context when possible."""
