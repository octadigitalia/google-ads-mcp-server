import sys
import os
import logging
from typing import Optional

# Adiciona o diretorio raiz ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from mcp.server.fastmcp import FastMCP
from src.mcp_server import logic, auth, config

# Inicializa o Worker Engine
mcp = FastMCP("Google Ads AI Skill Worker")

@mcp.tool()
def run_setup(client_id: str, client_secret: str, developer_token: str, login_customer_id: str = None) -> dict:
    """
    [SETUP] Inicia o fluxo de autenticação e configuração do Worker. 
    Abre o navegador para login e salva as credenciais localmente.
    """
    try:
        refresh_token = auth.run_oauth_flow(client_id, client_secret)
        if not refresh_token:
            return {"status": "ERROR", "message": "Falha na autenticação via navegador."}
        
        # Salva no .env para persistência
        with open(".env", "w") as f:
            f.write(f"GOOGLE_ADS_DEVELOPER_TOKEN={developer_token}\n")
            f.write(f"GOOGLE_ADS_CLIENT_ID={client_id}\n")
            f.write(f"GOOGLE_ADS_CLIENT_SECRET={client_secret}\n")
            f.write(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}\n")
            if login_customer_id:
                f.write(f"GOOGLE_ADS_LOGIN_CUSTOMER_ID={login_customer_id.replace('-', '')}\n")
        
        return {
            "status": "SUCCESS", 
            "message": "Autenticação concluída e configurada!",
            "refresh_token": "SALVO_LOCALMENTE"
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
def run_unified_audit(customer_id: str, date_range: str = "LAST_30_DAYS") -> dict:
    """
    [SUPER-SKILL] Executa uma AUDITORIA COMPLETA da conta em um único passo.
    Consolida Saúde da Conta, Desperdício (Waste) e Qualidade da Estrutura.
    """
    try:
        # 1. Pulse (Health Check)
        snapshot = logic.get_account_snapshot(customer_id, date_range)
        
        # 2. Waste (Leak Detection)
        search_terms = logic.get_search_terms(customer_id, date_range, min_clicks=5)
        
        # 3. Structure & Capabilities
        capabilities = logic.get_account_capabilities(customer_id)
        
        return {
            "status": "SUCCESS",
            "audit_report": {
                "snapshot": snapshot,
                "waste_analysis": search_terms,
                "account_capabilities": capabilities
            }
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
def run_optimization_action(customer_id: str, action_type: str, params: dict) -> dict:
    """
    [SUPER-SKILL] Executa AÇÕES DE OTIMIZAÇÃO baseadas em recomendações.
    Suporta: 'add_negatives', 'update_budget', 'change_status'.
    """
    try:
        if action_type == "add_negatives":
            return logic.add_negative_keywords(customer_id, params['campaign_id'], params['keywords'])
        elif action_type == "update_budget":
            return logic.set_campaign_budget(customer_id, params['campaign_id'], params['amount'])
        elif action_type == "change_status":
            return logic.set_campaign_status(customer_id, params['campaign_id'], params['status'])
        else:
            return {"status": "ERROR", "message": f"Ação '{action_type}' desconhecida."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@mcp.tool()
def check_connection() -> dict:
    """
    [UTILITY] Verifica se o Worker está pronto e autenticado.
    """
    status = logic.connection_status()
    return {"status": status}

if __name__ == "__main__":
    mcp.run()
