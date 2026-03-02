from src.mcp_server.server import search_ads
import json

def test_reporting():
    # Query básica para listar campanhas
    query = """
        SELECT 
            campaign.id, 
            campaign.name, 
            campaign.status,
            metrics.impressions,
            metrics.clicks
        FROM campaign 
        WHERE segments.date DURING LAST_7_DAYS
        LIMIT 5
    """
    
    print(f"📊 Executando consulta GAQL na conta TecPlaner (3400173105)...")
    result = search_ads(query=query, customer_id="3400173105")
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Relatório extraído com sucesso!")
        print(f"Linhas retornadas: {result['metadata']['row_count']}")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_reporting()
