"""
Unit Tests for LiteLLM Gateway Component

Tests LLM operations across multiple providers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.litellm_gateway import LiteLLMGateway


class TestLiteLLMGateway:
    """Test LiteLLMGateway."""
    
    @pytest.fixture
    def gateway_config(self):
        """Gateway configuration fixture."""
        return {
            "api_key": "test-api-key",
            "provider": "openai"
        }
    
    @pytest.fixture
    def mock_gateway(self, gateway_config):
        """Mock gateway with patched litellm."""
        with patch('src.core.litellm_gateway.gateway.litellm') as mock_litellm:
            gateway = LiteLLMGateway(**gateway_config)
            gateway._litellm = mock_litellm
            return gateway, mock_litellm
    
    def test_initialization(self, gateway_config):
        """Test gateway initialization."""
        gateway = LiteLLMGateway(**gateway_config)
        assert gateway.api_key == "test-api-key"
        assert gateway.provider == "openai"
    
    def test_generate(self, mock_gateway):
        """Test text generation."""
        gateway, mock_litellm = mock_gateway
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.model = "gpt-4"
        mock_litellm.completion.return_value = mock_response
        
        response = gateway.generate(
            prompt="Test prompt",
            model="gpt-4"
        )
        
        assert response.text == "Generated text"
        assert response.model == "gpt-4"
        mock_litellm.completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_async(self, mock_gateway):
        """Test async text generation."""
        gateway, mock_litellm = mock_gateway
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async generated text"
        mock_response.model = "gpt-4"
        mock_litellm.acompletion.return_value = mock_response
        
        response = await gateway.generate_async(
            prompt="Test prompt",
            model="gpt-4"
        )
        
        assert response.text == "Async generated text"
        mock_litellm.acompletion.assert_called_once()
    
    def test_stream(self, mock_gateway):
        """Test streaming generation."""
        gateway, mock_litellm = mock_gateway
        
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock()]
        mock_chunk1.choices[0].delta.content = "Hello "
        
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock()]
        mock_chunk2.choices[0].delta.content = "World"
        
        mock_litellm.completion.return_value = [mock_chunk1, mock_chunk2]
        
        chunks = list(gateway.stream(
            prompt="Test prompt",
            model="gpt-4"
        ))
        
        assert len(chunks) == 2
    
    def test_embed(self, mock_gateway):
        """Test embedding generation."""
        gateway, mock_litellm = mock_gateway
        
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 1536)
        ]
        mock_litellm.embedding.return_value = mock_response
        
        response = gateway.embed(
            texts=["Hello", "World"],
            model="text-embedding-3-small"
        )
        
        assert len(response.embeddings) == 1
        assert len(response.embeddings[0]) == 1536
        mock_litellm.embedding.assert_called_once()
    
    def test_error_handling(self, mock_gateway):
        """Test error handling."""
        gateway, mock_litellm = mock_gateway
        
        mock_litellm.completion.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            gateway.generate(prompt="Test", model="gpt-4")
    
    def test_provider_switching(self):
        """Test provider switching."""
        gateway_openai = LiteLLMGateway(
            api_key="test-key",
            provider="openai"
        )
        assert gateway_openai.provider == "openai"
        
        gateway_anthropic = LiteLLMGateway(
            api_key="test-key",
            provider="anthropic"
        )
        assert gateway_anthropic.provider == "anthropic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

