import json
from src.mcp_server.server import create_search_campaign

customer_id = "3400173105"

print(f"Creating SMART Search Campaign (Target CPA): {customer_id}")

try:
    resultado = create_search_campaign(
        customer_id=customer_id,
        campaign_name="[MCP SMART] Target CPA - Orion",
        daily_budget_amount=50.0,
        target_cpa=15.0 # R$ 15,00 de CPA
    )
    print("\nSUCCESS: Smart Campaign Created!")
    print(json.dumps(resultado, indent=2))

except Exception as e:
    print(f"\nERROR: {str(e)}")
