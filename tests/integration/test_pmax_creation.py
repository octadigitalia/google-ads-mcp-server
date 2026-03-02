import json
from src.mcp_server.server import create_pmax_campaign

customer_id = "3400173105"

print(f"Creating PMax Structure: {customer_id}")

try:
    resultado = create_pmax_campaign(
        customer_id=customer_id,
        campaign_name="[MCP PMAX] Automated Pilot - Orion",
        daily_budget_amount=100.0,
        headlines=[
            "Alta Performance IA",
            "Gestao Inteligente",
            "TecPlaner Cloud"
        ],
        descriptions=[
            "Alcance todos os canais do Google com orquestracao via agente.",
            "Maximize seu ROI usando a estrutura automatizada do servidor MCP."
        ],
        final_urls=["https://tecplaner.com.br"]
    )
    print("\nSUCCESS: PMax Created!")
    print(json.dumps(resultado, indent=2))

except Exception as e:
    print(f"\nERROR: {str(e)}")
