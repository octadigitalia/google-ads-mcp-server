from src.mcp_server.server import search_ads
import json

def test_performance_analysis():
    # Query avançada: Performance por campanha com custo e métricas calculadas
    query = """
        SELECT 
            campaign.id, 
            campaign.name, 
            metrics.impressions, 
            metrics.clicks, 
            metrics.ctr, 
            metrics.average_cpc, 
            metrics.cost_micros
        FROM campaign 
        WHERE metrics.impressions > 0
        AND segments.date DURING LAST_30_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    
    customer_id = "3400173105" # TecPlaner
    print(f"📈 Analisando performance da conta {customer_id} (Últimos 30 dias)...")
    
    result = search_ads(query=query, customer_id=customer_id)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Análise concluída!")
        print(f"Campanhas Ativas encontradas: {result['metadata']['row_count']}")
        
        for row in result['results']:
            # Google Ads retorna custo em 'micros' (dividir por 1.000.000)
            cost_micros = row.get('metrics', {}).get('cost_micros', 0)
            cost = float(cost_micros) / 1_000_000
            
            name = row.get('campaign', {}).get('name', 'Desconhecida')
            clicks = row.get('metrics', {}).get('clicks', 0)
            ctr_raw = row.get('metrics', {}).get('ctr', 0)
            ctr = float(ctr_raw) * 100
            
            print(f"\n🔹 Campanha: {name}")
            print(f"   - Cliques: {clicks}")
            print(f"   - CTR: {ctr:.2f}%")
            print(f"   - Investimento: R$ {cost:.2f}")

if __name__ == "__main__":
    test_performance_analysis()
