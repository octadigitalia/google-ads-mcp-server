import pytest
from unittest.mock import MagicMock
from src.mcp_server.utils import translate_google_ads_error

def test_translate_generic_exception():
    e = Exception("Erro generico")
    result = translate_google_ads_error(e)
    assert result["status"] == "ERROR"
    assert result["error_type"] == "Exception"
    assert "Erro generico" in result["message"]

def test_translate_google_ads_exception():
    # Simula uma GoogleAdsException com falhas estruturadas
    mock_error = MagicMock()
    mock_error.message = "Campo invalido na query"
    mock_error.error_code.query_error.name = "UNRECOGNIZED_FIELD"
    
    mock_failure = MagicMock()
    mock_failure.errors = [mock_error]
    
    mock_exception = MagicMock()
    mock_exception.failure = mock_failure
    mock_exception.__str__.return_value = "Erro da API"
    
    result = translate_google_ads_error(mock_exception)
    
    assert result["status"] == "ERROR"
    assert result["error_code"] == "UNRECOGNIZED_FIELD"
    assert "Campo invalido" in result["message"]
    assert len(result["suggestions"]) > 0
    assert result["suggestions"][0] == "Verifique se o campo no SELECT/WHERE existe para este recurso."

def test_translate_permission_denied():
    mock_error = MagicMock()
    mock_error.message = "User doesn't have permission"
    
    # Criamos um objeto de erro que só tenha o authorization_error
    class MockErrorCode:
        def __init__(self):
            self.authorization_error = MagicMock()
            self.authorization_error.name = "USER_PERMISSION_DENIED"
    
    mock_error.error_code = MockErrorCode()
    
    mock_failure = MagicMock()
    mock_failure.errors = [mock_error]
    
    mock_exception = MagicMock()
    mock_exception.failure = mock_failure
    mock_exception.__str__.return_value = "API Error"
    
    result = translate_google_ads_error(mock_exception)
    
    assert "ACESSO NEGADO" in result["message"]
    assert result["error_code"] == "USER_PERMISSION_DENIED"
