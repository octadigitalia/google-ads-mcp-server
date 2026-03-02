from src.mcp_server.server import get_search_terms
import json

def test_search_terms():
    customer_id = "3400173105" # TecPlaner
    print(f"🔍 AUDITORIA: Analisando termos de pesquisa reais da conta {customer_id}...")
    
    # Vamos buscar os termos que tiveram pelo menos 1 clique nos últimos 30 dias
    result = get_search_terms(customer_id=customer_id, date_range="LAST_30_DAYS", min_clicks=1)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        count = result['metadata']['row_count']
        print(f"✅ Sucesso! Termos encontrados: {count}")
        
        for row in result['results']:
            term = row.get('search_term_view', {}).get('search_term', 'N/A')
            clicks = row.get('metrics', {}).get('clicks', 0)
            cost = row.get('metrics', {}).get('cost_formatted', 0)
            campaign = row.get('campaign', {}).get('name', 'N/A')
            
            print(f"🔹 Termo: '{term}'")
            print(f"   Clicks: {clicks} | Custo: R$ {cost:.2f} | Campanha: {campaign}")

if __name__ == "__main__":
    test_search_terms()
