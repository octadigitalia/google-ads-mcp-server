import json
import sys
from src.mcp_server.server import create_ad_group, create_responsive_search_ad, add_keywords

customer_id = "3400173105"
campaign_id = "23608928120"

print(f"Starting Upgrade for Campaign: {campaign_id}")

try:
    # 1. Ad Group
    print("\n1. Creating Ad Group...")
    res_group = create_ad_group(
        customer_id=customer_id,
        campaign_id=campaign_id,
        ad_group_name="[MCP] Test Group - Orion"
    )
    group_id = res_group["ad_group_id"]
    print(f"OK: {group_id}")

    # 2. RSA Ad
    print("\n2. Creating RSA Ad...")
    res_ad = create_responsive_search_ad(
        customer_id=customer_id,
        ad_group_id=group_id,
        headlines=[
            "Automacao Inteligente",
            "Gestao via Agente IA",
            "Resultados Reais Hoje"
        ],
        descriptions=[
            "Sua conta Google Ads orquestrada por agentes de inteligencia artificial de elite.",
            "Escalabilidade e precisao tecnica sem precedentes para seu marketing digital."
        ],
        final_url="https://tecplaner.com.br"
    )
    print(f"OK: {res_ad['ad_id']}")

    # 3. Keywords
    print("\n3. Adding Keywords...")
    res_kw = add_keywords(
        customer_id=customer_id,
        ad_group_id=group_id,
        keywords=["gestao google ads", "automacao marketing", "agente ia"],
        match_type="PHRASE"
    )
    print(f"OK: Added {res_kw['added_count']} keywords")

    print("\nSUCCESS: FULL STRUCTURE CREATED!")

except Exception as e:
    print(f"\nERROR: {str(e)}")
