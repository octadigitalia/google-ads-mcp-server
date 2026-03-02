import json
from src.mcp_server.config import get_settings
from src.mcp_server.server import create_search_campaign
from google.ads.googleads.errors import GoogleAdsException

# ID da TecPlaner identificado
customer_id = "3400173105"

print(f"Executando CRIAÇÃO REAL de campanha para a conta TecPlaner: {customer_id}")

try:
    resultado = create_search_campaign(
        customer_id=customer_id,
        campaign_name="[MCP TEST] Campanha TecPlaner - Orion",
        daily_budget_amount=1.0 # Valor mínimo para teste
    )
    print("\n✅ SUCESSO!")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
except GoogleAdsException as ex:
    print("\n❌ GoogleAdsException Capturada!")
    for error in ex.failure.errors:
        print(f"\nMensagem: {error.message}")
        print("Caminho do Campo:")
        for path in error.location.field_path_elements:
            print(f"  -> {path.field_name}")
except Exception as e:
    print(f"\n❌ Erro Inesperado: {e}")
