import os
import pytest
from src.mcp_server.config import GoogleAdsConfig

def test_load_from_env(monkeypatch):
    """Verifica se carrega corretamente das variáveis de ambiente."""
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "test_token")
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_ID", "test_id")
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_SECRET", "test_secret")
    monkeypatch.setenv("GOOGLE_ADS_REFRESH_TOKEN", "test_refresh")
    monkeypatch.setenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "123456")

    config = GoogleAdsConfig.load(yaml_path="non_existent.yaml")

    assert config.developer_token == "test_token"
    assert config.client_id == "test_id"
    assert config.client_secret.get_secret_value() == "test_secret"
    assert config.refresh_token.get_secret_value() == "test_refresh"
    assert config.login_customer_id == "123456"

def test_pydantic_validation():
    """Verifica se lança erro se faltar campos obrigatórios."""
    with pytest.raises(Exception):
        GoogleAdsConfig(developer_token="only_this")

def test_secret_str_obfuscation(monkeypatch):
    """Verifica se campos sensíveis não aparecem no __str__."""
    monkeypatch.setenv("GOOGLE_ADS_DEVELOPER_TOKEN", "test")
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_ID", "test")
    monkeypatch.setenv("GOOGLE_ADS_CLIENT_SECRET", "secret_pass")
    monkeypatch.setenv("GOOGLE_ADS_REFRESH_TOKEN", "secret_refresh")

    config = GoogleAdsConfig.load(yaml_path="non_existent.yaml")

    config_str = str(config)
    assert "secret_pass" not in config_str
    assert "secret_refresh" not in config_str
    assert "**********" in config_str
