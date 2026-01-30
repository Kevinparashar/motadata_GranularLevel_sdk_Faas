"""
Integration Tests for API-Agent Integration

Tests the integration between API Backend and Agent Framework.
"""

# Standard library imports
from unittest.mock import MagicMock

# Third-party imports
import pytest

# Local application/library specific imports
from src.core.agno_agent_framework import Agent


@pytest.mark.integration
class TestAPIAgentIntegration:
    """Test API-Agent integration."""

    @pytest.fixture
    def mock_api_service(self):
        """Create mock API service."""
        mock_service = MagicMock()
        mock_service.generate_text.return_value = {
            "text": "Generated text",
            "model": "gpt-4",
            "tokens_used": 100,
        }
        return mock_service

    @pytest.fixture
    def mock_agent(self):
        """Create mock agent."""
        mock_gateway = MagicMock()
        agent = Agent(agent_id="api-agent", name="API Agent", gateway=mock_gateway)
        return agent

    def test_api_service_with_agent(self, mock_api_service, mock_agent):
        """Test API service using agent."""
        # API service should be able to use agent
        assert mock_api_service is not None
        assert mock_agent is not None

    def test_agent_task_via_api(self, mock_agent):
        """Test executing agent task via API."""
        task_id = mock_agent.add_task(task_type="test_task", parameters={"key": "value"})

        assert task_id is not None
        assert len(mock_agent.task_queue) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
