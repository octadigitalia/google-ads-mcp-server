import pytest
from unittest.mock import MagicMock
from src.mcp_server.utils import ResourceResolver

@pytest.fixture
def mock_client():
    client = MagicMock()
    mock_service = MagicMock()
    client.get_service.return_value = mock_service
    return client

def test_resolver_numeric_id(mock_client):
    resolver = ResourceResolver(mock_client)
    result = resolver.resolve("123", "CAMPAIGN", "987654321")
    assert result["id"] == "987654321"
    assert result["resolved"] is False

def test_resolver_resource_name(mock_client):
    resolver = ResourceResolver(mock_client)
    res_name = "customers/123/campaigns/456"
    result = resolver.resolve("123", "CAMPAIGN", res_name)
    assert result["id"] == res_name
    assert result["resolved"] is False

def test_resolver_name_resolution_success(mock_client):
    resolver = ResourceResolver(mock_client)
    
    # Mock da resposta da API
    mock_row = MagicMock()
    mock_row.campaign.id = 12345
    mock_row.campaign.name = "Campanha Teste"
    mock_client.get_service().search.return_value = [mock_row]
    
    result = resolver.resolve("123", "CAMPAIGN", "Campanha Teste")
    assert result["id"] == "12345"
    assert result["resolved"] is True

def test_resolver_ambiguity(mock_client):
    resolver = ResourceResolver(mock_client)
    
    # Mock de dois resultados
    row1 = MagicMock()
    row1.campaign.id = 1
    row1.campaign.name = "Teste"
    row2 = MagicMock()
    row2.campaign.id = 2
    row2.campaign.name = "Teste"
    
    mock_client.get_service().search.return_value = [row1, row2]
    
    result = resolver.resolve("123", "CAMPAIGN", "Teste")
    assert result["error"] == "AMBIGUITY_DETECTED"
    assert result["ambiguous"] is True
    assert len(result["matches"]) == 2
