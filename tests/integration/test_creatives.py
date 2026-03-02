from src.mcp_server.server import search_ads, update_rsa_assets
import json

def test_creative_update():
    customer_id = "3400173105" # TecPlaner
    
    print("SEARCH: Buscando anuncio RSA ativo...")
    # Query melhorada para incluir nomes de Campanha e Grupo
    query = """
        SELECT 
            ad_group_ad.ad.id, 
            campaign.name,
            ad_group.name,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions
        FROM ad_group_ad 
        WHERE ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
        AND ad_group_ad.status = 'ENABLED'
        LIMIT 1
    """
    
    search_result = search_ads(query=query, customer_id=customer_id)
    
    if "error" in search_result or search_result["metadata"]["row_count"] == 0:
        print("ERROR: Nao foi possivel encontrar um anuncio RSA ativo.")
        return

    res = search_result["results"][0]
    ad_data = res["ad_group_ad"]["ad"]
    camp_name = res["campaign"]["name"]
    group_name = res["ad_group"]["name"]
    ad_id = ad_data["id"]
    
    current_headlines = [h["text"] for h in ad_data["responsive_search_ad"]["headlines"]]
    current_descriptions = [d["text"] for d in ad_data["responsive_search_ad"]["descriptions"]]
    
    print(f"\n📍 LOCALIZAÇÃO DO ANÚNCIO:")
    print(f"   Campanha: {camp_name}")
    print(f"   Grupo:    {group_name}")
    print(f"   ID do Ad: {ad_id}")

    # 🚀 O TESTE
    print("\nTOOL: Enviando comando de atualizacao (Replace)...")
    result = update_rsa_assets(
        customer_id=customer_id,
        ad_id=ad_id,
        headlines=current_headlines,
        descriptions=current_descriptions
    )
    
    if "error" in result:
        print(f"❌ Erro na Tool: {result['error']}")
    else:
        print("✅ SUCCESS: O MCP atualizou os assets do RSA com sucesso.")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_creative_update()
