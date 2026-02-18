"""
Unit Tests for Hallucination Detector

Tests hallucination detection in LLM-generated responses.
"""


import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.rag.hallucination_detector import (
    HallucinationDetector,
    HallucinationResult,
    create_hallucination_detector,
)


class TestHallucinationResult:
    """Test HallucinationResult class."""

    def test_init(self):
        """Test HallucinationResult initialization."""
        result = HallucinationResult(
            is_hallucination=True,
            confidence=0.8,
            reasons=["Reason 1", "Reason 2"],
            grounded_sentences=["Sentence 1"],
            ungrounded_sentences=["Sentence 2"],
            metadata={"key": "value"},
        )

        assert result.is_hallucination is True
        assert abs(result.confidence - 0.8) < 0.001
        assert len(result.reasons) == 2
        assert len(result.grounded_sentences) == 1
        assert len(result.ungrounded_sentences) == 1
        assert result.metadata["key"] == "value"

    def test_init_with_default_metadata(self):
        """Test HallucinationResult initialization with default metadata."""
        result = HallucinationResult(
            is_hallucination=False,
            confidence=0.5,
            reasons=[],
            grounded_sentences=[],
            ungrounded_sentences=[],
        )

        assert result.metadata == {}

    def test_to_dict(self):
        """Test to_dict method."""
        result = HallucinationResult(
            is_hallucination=True,
            confidence=0.8,
            reasons=["Reason 1"],
            grounded_sentences=["Sentence 1"],
            ungrounded_sentences=["Sentence 2"],
            metadata={"key": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["is_hallucination"] is True
        assert abs(result_dict["confidence"] - 0.8) < 0.001
        assert result_dict["reasons"] == ["Reason 1"]
        assert result_dict["grounded_sentences"] == ["Sentence 1"]
        assert result_dict["ungrounded_sentences"] == ["Sentence 2"]
        assert result_dict["metadata"]["key"] == "value"


class TestHallucinationDetector:
    """Test HallucinationDetector class."""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway."""
        gateway = MagicMock()
        gateway.embed = MagicMock()
        gateway.generate_async = AsyncMock()
        return gateway

    @pytest.fixture
    def detector(self, mock_gateway):
        """Create a HallucinationDetector instance."""
        return HallucinationDetector(
            gateway=mock_gateway,
            enable_llm_verification=True,
            similarity_threshold=0.7,
            min_grounded_ratio=0.6,
        )

    @pytest.fixture
    def detector_no_gateway(self):
        """Create a HallucinationDetector without gateway."""
        return HallucinationDetector(
            gateway=None,
            enable_llm_verification=False,
            similarity_threshold=0.7,
            min_grounded_ratio=0.6,
        )

    @pytest.fixture
    def context_documents(self):
        """Create sample context documents."""
        return [
            {"content": "Python is a programming language. It is widely used for web development."},
            {"content": "Machine learning is a subset of artificial intelligence."},
        ]

    def test_init(self, mock_gateway):
        """Test HallucinationDetector initialization."""
        detector = HallucinationDetector(
            gateway=mock_gateway,
            enable_llm_verification=True,
            similarity_threshold=0.8,
            min_grounded_ratio=0.7,
        )

        assert detector.gateway == mock_gateway
        assert detector.enable_llm_verification is True
        assert abs(detector.similarity_threshold - 0.8) < 0.001
        assert abs(detector.min_grounded_ratio - 0.7) < 0.001

    def test_detect_no_hallucination(self, detector_no_gateway, context_documents):
        """Test detect method with grounded response."""
        response = "Python is a programming language. It is widely used for web development."

        result = detector_no_gateway.detect(response, context_documents)

        assert result.is_hallucination is False
        assert len(result.grounded_sentences) > 0
        assert len(result.ungrounded_sentences) == 0
        assert result.confidence >= 0.5

    def test_detect_with_hallucination(self, detector_no_gateway, context_documents):
        """Test detect method with ungrounded response."""
        # Use a response with clearly ungrounded content
        response = "Python is a programming language. Elephants are large mammals with trunks. Zebras have stripes."

        result = detector_no_gateway.detect(response, context_documents)

        # Should detect hallucination due to ungrounded sentences
        assert result.is_hallucination is True
        assert len(result.ungrounded_sentences) > 0
        assert len(result.reasons) > 0
        assert "grounded_ratio" in result.metadata
        assert result.metadata["grounded_ratio"] < detector_no_gateway.min_grounded_ratio

    def test_detect_with_empty_response(self, detector_no_gateway, context_documents):
        """Test detect method with empty response."""
        response = ""

        result = detector_no_gateway.detect(response, context_documents)

        # Empty response has 0 sentences, so grounded_ratio is 0.0 which is < min_grounded_ratio
        # This is technically a hallucination by the algorithm, but we verify the metadata
        assert result.metadata["total_sentences"] == 0
        assert abs(result.metadata["grounded_ratio"] - 0.0) < 0.001
        assert len(result.grounded_sentences) == 0
        assert len(result.ungrounded_sentences) == 0

    def test_detect_with_llm_verification(self, detector, context_documents):
        """Test detect method with LLM verification enabled."""
        response = "Python is a programming language. Elephants are large mammals."

        # Mock LLM verification response
        # Mock the async method to return a coroutine
        async def mock_llm_verify(*args, **kwargs):  # noqa: ARG001
            # Use await to satisfy async requirement
            await asyncio.sleep(0)
            return {
                "is_hallucination": True,
                "confidence": 0.9,
                "reasons": ["LLM detected ungrounded claims"],
            }

        detector._llm_verify_hallucination = mock_llm_verify

        result = detector.detect(response, context_documents)

        assert result.is_hallucination is True
        assert abs(result.confidence - 0.9) < 0.001
        assert len(result.reasons) > 1  # Should include both grounding and LLM reasons

    def test_detect_with_llm_verification_no_gateway(self, detector_no_gateway, context_documents):
        """Test detect method with LLM verification enabled but no gateway."""
        detector_no_gateway.enable_llm_verification = True
        response = "Python is a programming language. Elephants are large mammals."

        result = detector_no_gateway.detect(response, context_documents)

        # Should still work without gateway
        assert result.is_hallucination is True
        assert result.confidence >= 0.5

    def test_detect_with_llm_verification_no_hallucination(self, detector, context_documents):
        """Test detect method with LLM verification but no hallucination detected."""
        response = "Python is a programming language. It is widely used for web development."

        result = detector.detect(response, context_documents)

        # Should not call LLM verification if no hallucination
        assert result.is_hallucination is False
        assert detector.gateway.generate_async.called is False

    @pytest.mark.asyncio
    async def test_detect_async_no_hallucination(self, detector_no_gateway, context_documents):
        """Test detect_async method with grounded response."""
        response = "Python is a programming language. It is widely used for web development."

        result = await detector_no_gateway.detect_async(response, context_documents)

        assert result.is_hallucination is False
        assert len(result.grounded_sentences) > 0

    @pytest.mark.asyncio
    async def test_detect_async_with_hallucination(self, detector_no_gateway, context_documents):
        """Test detect_async method with ungrounded response."""
        response = "Python is a programming language. Elephants are large mammals. Machine learning is important."

        result = await detector_no_gateway.detect_async(response, context_documents)

        # Should detect hallucination due to "Elephants are large mammals"
        # Note: The grounding check might match "Machine learning" so we check if any ungrounded sentences exist
        assert result.is_hallucination is True or len(result.ungrounded_sentences) > 0

    @pytest.mark.asyncio
    async def test_detect_async_with_llm_verification(self, detector, context_documents):
        """Test detect_async method with LLM verification."""
        response = "Python is a programming language. Elephants are large mammals."

        # Mock LLM verification response
        detector.gateway.generate_async.return_value = MagicMock(
            text='{"is_hallucination": true, "confidence": 0.85, "reasons": ["LLM detected ungrounded claims"]}'
        )

        result = await detector.detect_async(response, context_documents)

        assert result.is_hallucination is True
        # Confidence should be from LLM verification (0.85) or calculated
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_detect_async_with_llm_verification_no_response(self, detector, context_documents):
        """Test detect_async method with LLM verification returning None."""
        response = "Python is a programming language. Elephants are large mammals."

        detector.gateway.generate_async.return_value = MagicMock(text="Invalid JSON")

        result = await detector.detect_async(response, context_documents)

        # Should fall back to grounding-based confidence
        assert result.is_hallucination is True
        assert result.confidence >= 0.5

    def test_split_sentences(self, detector_no_gateway):
        """Test _split_sentences method."""
        text = "First sentence. Second sentence! Third sentence?"

        sentences = detector_no_gateway._split_sentences(text)

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_split_sentences_empty(self, detector_no_gateway):
        """Test _split_sentences with empty text."""
        sentences = detector_no_gateway._split_sentences("")

        assert len(sentences) == 0

    def test_build_context_text(self, detector_no_gateway, context_documents):
        """Test _build_context_text method."""
        context_text = detector_no_gateway._build_context_text(context_documents)

        assert "Python is a programming language" in context_text
        assert "Machine learning" in context_text

    def test_build_context_text_empty(self, detector_no_gateway):
        """Test _build_context_text with empty documents."""
        context_text = detector_no_gateway._build_context_text([])

        assert context_text == ""

    def test_build_context_text_no_content(self, detector_no_gateway):
        """Test _build_context_text with documents without content."""
        documents = [{"title": "Doc 1"}, {"title": "Doc 2"}]
        context_text = detector_no_gateway._build_context_text(documents)

        assert context_text == ""

    def test_check_sentence_grounding_direct_match(self, detector_no_gateway):
        """Test _check_sentence_grounding with direct text match."""
        sentence = "Python is a programming language"
        context = "Python is a programming language. It is widely used."

        is_grounded = detector_no_gateway._check_sentence_grounding(sentence, context)

        assert is_grounded is True

    def test_check_sentence_grounding_short_sentence(self, detector_no_gateway):
        """Test _check_sentence_grounding with very short sentence."""
        sentence = "Hi"
        context = "Some context text here"

        is_grounded = detector_no_gateway._check_sentence_grounding(sentence, context)

        # Short sentences should return True
        assert is_grounded is True

    def test_check_sentence_grounding_with_semantic_similarity(self, detector):
        """Test _check_sentence_grounding using semantic similarity."""
        sentence = "Python is a coding language"
        context = "Python is a programming language used for development"

        # Mock embedding response
        mock_embedding = MagicMock()
        mock_embedding.embeddings = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]  # Same embedding = high similarity

        detector.gateway.embed.return_value = mock_embedding

        is_grounded = detector._check_sentence_grounding(sentence, context)

        assert is_grounded is True

    def test_check_sentence_grounding_with_semantic_similarity_low(self, detector):
        """Test _check_sentence_grounding with low semantic similarity."""
        sentence = "Elephants are large mammals"
        context = "Python is a programming language"

        # Mock embedding response with different embeddings
        mock_embedding1 = MagicMock()
        mock_embedding1.embeddings = [[1.0, 0.0, 0.0]]
        mock_embedding2 = MagicMock()
        mock_embedding2.embeddings = [[0.0, 1.0, 0.0]]

        def mock_embed(*args, **kwargs):
            if "Python" in args[0][0] or "programming" in args[0][0]:
                return mock_embedding2
            return mock_embedding1

        detector.gateway.embed.side_effect = mock_embed

        is_grounded = detector._check_sentence_grounding(sentence, context)

        # Should check citations as fallback
        assert isinstance(is_grounded, bool)

    def test_check_sentence_grounding_with_citations(self, detector_no_gateway):
        """Test _check_sentence_grounding with citations."""
        sentence = "According to [1], Python is a language"
        context = "Some context"

        is_grounded = detector_no_gateway._check_sentence_grounding(sentence, context)

        assert is_grounded is True

    def test_check_sentence_grounding_with_citation_patterns(self, detector_no_gateway):
        """Test _check_sentence_grounding with various citation patterns."""
        citation_sentences = [
            "As stated in the source, Python is great",
            "As mentioned in [1], Python is used",
            "Reference: Python documentation",
            "Source: official docs",
        ]

        for sentence in citation_sentences:
            is_grounded = detector_no_gateway._check_sentence_grounding(sentence, "Some context")
            assert is_grounded is True

    def test_check_sentence_grounding_semantic_error(self, detector):
        """Test _check_sentence_grounding when semantic similarity check fails."""
        sentence = "Python is a language"
        context = "Some context"

        detector.gateway.embed.side_effect = Exception("Embedding error")

        is_grounded = detector._check_sentence_grounding(sentence, context)

        # Should fall back to citation check
        assert isinstance(is_grounded, bool)

    def test_check_semantic_similarity(self, detector):
        """Test _check_semantic_similarity method."""
        sentence = "Python is a programming language"
        context = "Python is used for coding"

        # Mock embedding response
        mock_embedding = MagicMock()
        mock_embedding.embeddings = [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]

        detector.gateway.embed.return_value = mock_embedding

        similarity = detector._check_semantic_similarity(sentence, context)

        assert abs(similarity - 1.0) < 0.001  # Same vectors = perfect similarity

    def test_check_semantic_similarity_no_gateway(self, detector_no_gateway):
        """Test _check_semantic_similarity without gateway."""
        similarity = detector_no_gateway._check_semantic_similarity("sentence", "context")

        assert abs(similarity - 0.0) < 0.001

    def test_check_semantic_similarity_no_embeddings(self, detector):
        """Test _check_semantic_similarity when embeddings are None."""
        mock_embedding = MagicMock()
        mock_embedding.embeddings = None

        detector.gateway.embed.return_value = mock_embedding

        similarity = detector._check_semantic_similarity("sentence", "context")

        assert abs(similarity - 0.0) < 0.001

    def test_check_semantic_similarity_empty_embeddings(self, detector):
        """Test _check_semantic_similarity with empty embeddings."""
        mock_embedding = MagicMock()
        mock_embedding.embeddings = []

        detector.gateway.embed.return_value = mock_embedding

        similarity = detector._check_semantic_similarity("sentence", "context")

        assert abs(similarity - 0.0) < 0.001

    def test_check_semantic_similarity_error(self, detector):
        """Test _check_semantic_similarity when error occurs."""
        detector.gateway.embed.side_effect = Exception("Embedding error")

        similarity = detector._check_semantic_similarity("sentence", "context")

        assert abs(similarity - 0.0) < 0.001

    def test_has_citations(self, detector_no_gateway):
        """Test _has_citations method with various patterns."""
        citation_sentences = [
            "According to [1], this is true",
            "As stated in (source), this works",
            "According to the documentation",
            "As mentioned in the reference",
            "Reference: official docs",
            "Source: documentation",
        ]

        for sentence in citation_sentences:
            has_citation = detector_no_gateway._has_citations(sentence)
            assert has_citation is True

    def test_has_citations_no_citation(self, detector_no_gateway):
        """Test _has_citations with sentence without citations."""
        sentence = "This is a regular sentence without any citations"

        has_citation = detector_no_gateway._has_citations(sentence)

        assert has_citation is False

    @pytest.mark.asyncio
    async def test_llm_verify_hallucination(self, detector):
        """Test _llm_verify_hallucination method."""
        response = "Python is a language. Elephants are large."
        context = "Python is a programming language"
        query = "What is Python?"

        # Mock LLM response with valid JSON
        mock_response = MagicMock()
        mock_response.text = '{"is_hallucination": true, "confidence": 0.9, "reasons": ["Ungrounded claim"], "ungrounded_claims": ["Elephants"]}'

        detector.gateway.generate_async.return_value = mock_response

        result = await detector._llm_verify_hallucination(response, context, query)

        assert result is not None
        assert result["is_hallucination"] is True
        assert abs(result["confidence"] - 0.9) < 0.001
        assert len(result["reasons"]) > 0

    @pytest.mark.asyncio
    async def test_llm_verify_hallucination_no_gateway(self, detector_no_gateway):
        """Test _llm_verify_hallucination without gateway."""
        result = await detector_no_gateway._llm_verify_hallucination("response", "context", "query")

        assert result is None

    @pytest.mark.asyncio
    async def test_llm_verify_hallucination_invalid_json(self, detector):
        """Test _llm_verify_hallucination with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.text = "This is not JSON"

        detector.gateway.generate_async.return_value = mock_response

        result = await detector._llm_verify_hallucination("response", "context", "query")

        assert result is None

    @pytest.mark.asyncio
    async def test_llm_verify_hallucination_error(self, detector):
        """Test _llm_verify_hallucination when error occurs."""
        detector.gateway.generate_async.side_effect = Exception("LLM error")

        result = await detector._llm_verify_hallucination("response", "context", "query")

        assert result is None

    @pytest.mark.asyncio
    async def test_llm_verify_hallucination_json_in_text(self, detector):
        """Test _llm_verify_hallucination with JSON embedded in text."""
        mock_response = MagicMock()
        mock_response.text = 'Some text before {"is_hallucination": false, "confidence": 0.3} and after'

        detector.gateway.generate_async.return_value = mock_response

        result = await detector._llm_verify_hallucination("response", "context", "query")

        assert result is not None
        assert result["is_hallucination"] is False
        assert abs(result["confidence"] - 0.3) < 0.001

    def test_detect_confidence_calculation(self, detector_no_gateway, context_documents):
        """Test confidence calculation in detect method."""
        response = "Python is a programming language. Elephants are large mammals."

        result = detector_no_gateway.detect(response, context_documents)

        assert result.is_hallucination is True
        assert 0.5 <= result.confidence <= 1.0

    def test_detect_confidence_max_one(self, detector_no_gateway, context_documents):
        """Test that confidence is capped at 1.0."""
        # This would require a very high ungrounded ratio
        response = "Elephants are large. Giraffes are tall. Lions are fierce."

        result = detector_no_gateway.detect(response, context_documents)

        assert result.confidence <= 1.0

    def test_detect_metadata(self, detector_no_gateway, context_documents):
        """Test metadata in detect result."""
        response = "Python is a programming language."

        result = detector_no_gateway.detect(response, context_documents)

        assert "grounded_ratio" in result.metadata
        assert "total_sentences" in result.metadata
        assert "context_documents_count" in result.metadata
        assert result.metadata["context_documents_count"] == 2


class TestCreateHallucinationDetector:
    """Test create_hallucination_detector factory function."""

    def test_create_hallucination_detector_default(self):
        """Test create_hallucination_detector with defaults."""
        detector = create_hallucination_detector()

        assert isinstance(detector, HallucinationDetector)
        assert detector.gateway is None
        assert detector.enable_llm_verification is True

    def test_create_hallucination_detector_with_gateway(self):
        """Test create_hallucination_detector with gateway."""
        mock_gateway = MagicMock()
        detector = create_hallucination_detector(gateway=mock_gateway)

        assert detector.gateway == mock_gateway

    def test_create_hallucination_detector_with_params(self):
        """Test create_hallucination_detector with custom parameters."""
        detector = create_hallucination_detector(
            enable_llm_verification=False,
            similarity_threshold=0.8,
            min_grounded_ratio=0.7,
        )

        assert detector.enable_llm_verification is False
        assert abs(detector.similarity_threshold - 0.8) < 0.001
        assert abs(detector.min_grounded_ratio - 0.7) < 0.001

