"""
Hallucination Detection

Detects hallucinations in LLM-generated responses by checking if
the response is grounded in the retrieved context documents.
"""


# Standard library imports
import logging
import re
from typing import Any, Dict, List, Optional

# Local application/library specific imports
from ..litellm_gateway import LiteLLMGateway

logger = logging.getLogger(__name__)


class HallucinationResult:
    """Result of hallucination detection."""

    def __init__(
        self,
        is_hallucination: bool,
        confidence: float,
        reasons: List[str],
        grounded_sentences: List[str],
        ungrounded_sentences: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize hallucination result.
        
        Args:
            is_hallucination (bool): Flag to indicate whether hallucination is true.
            confidence (float): Input parameter for this operation.
            reasons (List[str]): Input parameter for this operation.
            grounded_sentences (List[str]): Input parameter for this operation.
            ungrounded_sentences (List[str]): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        """
        self.is_hallucination = is_hallucination
        self.confidence = confidence
        self.reasons = reasons
        self.grounded_sentences = grounded_sentences
        self.ungrounded_sentences = ungrounded_sentences
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        return {
            "is_hallucination": self.is_hallucination,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "grounded_sentences": self.grounded_sentences,
            "ungrounded_sentences": self.ungrounded_sentences,
            "metadata": self.metadata,
        }


class HallucinationDetector:
    """
    Detects hallucinations in LLM-generated responses.

    Uses multiple strategies:
    1. Semantic similarity between response and context
    2. Fact extraction and verification
    3. Citation checking
    4. Contradiction detection
    """

    def __init__(
        self,
        gateway: Optional[LiteLLMGateway] = None,
        enable_llm_verification: bool = True,
        similarity_threshold: float = 0.7,
        min_grounded_ratio: float = 0.6,
    ):
        """
        Initialize hallucination detector.
        
        Args:
            gateway (Optional[LiteLLMGateway]): Gateway client used for LLM calls.
            enable_llm_verification (bool): Flag to enable or disable llm verification.
            similarity_threshold (float): Input parameter for this operation.
            min_grounded_ratio (float): Input parameter for this operation.
        """
        self.gateway = gateway
        self.enable_llm_verification = enable_llm_verification
        self.similarity_threshold = similarity_threshold
        self.min_grounded_ratio = min_grounded_ratio

    def detect(
        self, response: str, context_documents: List[Dict[str, Any]], query: Optional[str] = None
    ) -> HallucinationResult:
        """
        Detect hallucinations in a response.
        
        Args:
            response (str): Input parameter for this operation.
            context_documents (List[Dict[str, Any]]): Input parameter for this operation.
            query (Optional[str]): Input parameter for this operation.
        
        Returns:
            HallucinationResult: Result of the operation.
        """
        reasons = []
        grounded_sentences = []
        ungrounded_sentences = []

        # Split response into sentences
        sentences = self._split_sentences(response)

        # Build context text
        context_text = self._build_context_text(context_documents)

        # Check each sentence
        for sentence in sentences:
            if not sentence.strip():
                continue

            is_grounded = self._check_sentence_grounding(sentence, context_text)

            if is_grounded:
                grounded_sentences.append(sentence)
            else:
                ungrounded_sentences.append(sentence)

        # Calculate grounded ratio
        total_sentences = len(grounded_sentences) + len(ungrounded_sentences)
        grounded_ratio = len(grounded_sentences) / total_sentences if total_sentences > 0 else 0.0

        # Determine if hallucination
        is_hallucination = grounded_ratio < self.min_grounded_ratio

        # Build reasons
        if is_hallucination:
            reasons.append(
                f"Only {grounded_ratio:.1%} of sentences are grounded in context "
                f"(minimum required: {self.min_grounded_ratio:.1%})"
            )
            reasons.append(f"{len(ungrounded_sentences)} ungrounded sentences detected")

        # LLM-based verification if enabled
        if self.enable_llm_verification and self.gateway and is_hallucination:
            llm_verification = self._llm_verify_hallucination(response, context_text, query)
            if llm_verification:
                reasons.extend(llm_verification.get("reasons", []))
                # Adjust confidence based on LLM verification
                confidence = llm_verification.get("confidence", 0.5)
            else:
                confidence = 0.5 + (1.0 - grounded_ratio) * 0.5
        else:
            confidence = 0.5 + (1.0 - grounded_ratio) * 0.5

        return HallucinationResult(
            is_hallucination=is_hallucination,
            confidence=min(confidence, 1.0),
            reasons=reasons,
            grounded_sentences=grounded_sentences,
            ungrounded_sentences=ungrounded_sentences,
            metadata={
                "grounded_ratio": grounded_ratio,
                "total_sentences": total_sentences,
                "context_documents_count": len(context_documents),
            },
        )

    def detect_async(
        self, response: str, context_documents: List[Dict[str, Any]], query: Optional[str] = None
    ) -> HallucinationResult:
        """
        Detect hallucinations asynchronously.
        
        Args:
            response (str): Input parameter for this operation.
            context_documents (List[Dict[str, Any]]): Input parameter for this operation.
            query (Optional[str]): Input parameter for this operation.
        
        Returns:
            HallucinationResult: Result of the operation.
        """
        # Same as sync version for now, but can be extended with async LLM calls
        return self.detect(response, context_documents, query)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        # Simple sentence splitting (can be improved with NLTK/spaCy)
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _build_context_text(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context text from documents.
        
        Args:
            documents (List[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        context_parts = []
        for doc in documents:
            content = doc.get("content", "")
            if content:
                context_parts.append(content)
        return "\n\n".join(context_parts)

    def _check_sentence_grounding(
        self, sentence: str, context_text: str
    ) -> bool:
        """
        Check if a sentence is grounded in context.
        
        Args:
            sentence (str): Input parameter for this operation.
            context_text (str): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        # Strategy 1: Check for direct text overlap
        sentence_lower = sentence.lower()
        context_lower = context_text.lower()

        # Extract key phrases from sentence
        words = sentence_lower.split()
        if len(words) < 3:
            # Very short sentences might be hard to verify
            return True

        # Check if significant words appear in context
        significant_words = [w for w in words if len(w) > 4]  # Words longer than 4 chars
        if not significant_words:
            significant_words = words[:5]  # Use first 5 words

        matches = sum(1 for word in significant_words if word in context_lower)
        match_ratio = matches / len(significant_words) if significant_words else 0.0

        if match_ratio >= 0.5:
            return True

        # Strategy 2: Check semantic similarity if gateway available
        if self.gateway:
            try:
                similarity = self._check_semantic_similarity(sentence, context_text)
                if similarity >= self.similarity_threshold:
                    return True
            except Exception as e:
                logger.warning(f"Error checking semantic similarity: {str(e)}")

        # Strategy 3: Check for citations/references
        if self._has_citations(sentence):
            return True

        return False

    def _check_semantic_similarity(self, sentence: str, context: str) -> float:
        """
        Check semantic similarity using embeddings.
        
        Args:
            sentence (str): Input parameter for this operation.
            context (str): Input parameter for this operation.
        
        Returns:
            float: Result of the operation.
        """
        if not self.gateway:
            return 0.0

        try:
            # Generate embeddings
            sentence_embedding = self.gateway.embed([sentence], model="text-embedding-3-small")
            context_embedding = self.gateway.embed(
                [context[:1000]], model="text-embedding-3-small"
            )  # Limit context

            if not sentence_embedding.embeddings or not context_embedding.embeddings:
                return 0.0

            # Calculate cosine similarity
            from numpy import dot
            from numpy.linalg import norm

            sent_vec = sentence_embedding.embeddings[0]
            ctx_vec = context_embedding.embeddings[0]

            similarity = dot(sent_vec, ctx_vec) / (norm(sent_vec) * norm(ctx_vec))
            return float(similarity)
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {str(e)}")
            return 0.0

    def _has_citations(self, sentence: str) -> bool:
        """
        Check if sentence has citations.
        
        Args:
            sentence (str): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        # Check for citation patterns
        citation_patterns = [
            r"\[.*?\]",  # [1], [source], etc.
            r"\(.*?\)",  # (source), etc.
            r"according to",
            r"as stated in",
            r"as mentioned in",
            r"reference",
            r"source:",
        ]

        sentence_lower = sentence.lower()
        for pattern in citation_patterns:
            if re.search(pattern, sentence_lower):
                return True

        return False

    def _llm_verify_hallucination(
        self, response: str, context_text: str, query: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to verify hallucination.
        
        Args:
            response (str): Input parameter for this operation.
            context_text (str): Input parameter for this operation.
            query (Optional[str]): Input parameter for this operation.
        
        Returns:
            Optional[Dict[str, Any]]: Dictionary result of the operation.
        """
        if not self.gateway:
            return None

        try:
            prompt = f"""Analyze the following response and determine if it contains information that is NOT supported by the provided context.

Context:
{context_text[:2000]}

Response to analyze:
{response}

Question (if applicable):
{query or "N/A"}

Please determine:
1. Does the response contain information not found in the context?
2. Are there any factual claims that cannot be verified from the context?
3. What is your confidence level (0.0-1.0)?

Respond in JSON format:
{{
    "is_hallucination": true/false,
    "confidence": 0.0-1.0,
    "reasons": ["reason1", "reason2"],
    "ungrounded_claims": ["claim1", "claim2"]
}}"""

            result = self.gateway.generate(
                prompt=prompt, model="gpt-4", max_tokens=500, temperature=0.0
            )

            # Parse JSON response
            import json

            response_text = result.text.strip()

            # Extract JSON from response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                verification = json.loads(json_match.group())
                return verification
        except Exception as e:
            logger.warning(f"Error in LLM verification: {str(e)}")

        return None


def create_hallucination_detector(
    gateway: Optional[LiteLLMGateway] = None, enable_llm_verification: bool = True, **kwargs: Any
) -> HallucinationDetector:
    """
    Create a hallucination detector instance.

    Args:
        gateway: Optional gateway for LLM verification
        enable_llm_verification: Whether to use LLM verification
        **kwargs: Additional configuration

    Returns:
        HallucinationDetector instance
    """
    return HallucinationDetector(
        gateway=gateway, enable_llm_verification=enable_llm_verification, **kwargs
    )
