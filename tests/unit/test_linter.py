import pytest
import os
import json
from src.mcp_server.utils import GaqlLinter

@pytest.fixture
def linter():
    # Garante que os arquivos de metadados existam para o teste
    # (Eles foram gerados durante a auditoria)
    return GaqlLinter()

def test_linter_valid_query(linter):
    query = "SELECT campaign.id, campaign.name FROM campaign"
    result = linter.validate_query(query)
    assert result["valid"] is True

def test_linter_invalid_field_suggestion(linter):
    # Campo com erro de digitação
    query = "SELECT campaign.idd, campaign.namme FROM campaign"
    result = linter.validate_query(query)
    
    assert result["valid"] is False
    assert result["error_code"] == "INVALID_GAQL_FIELD"
    
    invalid_fields = result["invalid_fields"]
    assert any(f["field"] == "campaign.idd" and f["suggestion"] == "campaign.id" for f in invalid_fields)
    assert any(f["field"] == "campaign.namme" and f["suggestion"] == "campaign.name" for f in invalid_fields)

def test_linter_unsupported_resource(linter):
    # Recurso que não auditamos (ex: bidding_strategy)
    query = "SELECT bidding_strategy.id FROM bidding_strategy"
    result = linter.validate_query(query)
    
    assert result["valid"] is False
    # Como bidding_strategy não está no cache, qualquer campo dela será inválido
    assert len(result["invalid_fields"]) > 0

def test_linter_with_alias(linter):
    query = "SELECT campaign.id AS my_id FROM campaign"
    result = linter.validate_query(query)
    assert result["valid"] is True
