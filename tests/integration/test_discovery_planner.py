from src.mcp_server.server import generate_keyword_ideas
import json

def test_discovery_planner():
    customer_id = "3400173105" # TecPlaner
    seeds = ["gerenciamento de obras", "software para engenharia"]
    
    print(f"📡 TESTE DO RADAR: Gerando ideias para sementes: {seeds}...")
    
    result = generate_keyword_ideas(customer_id=customer_id, keyword_texts=seeds)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        count = result['metadata']['row_count']
        print(f"✅ SUCESSO! {count} ideias encontradas.")
        
        # Mostra as TOP 5 ideias por volume de busca
        sorted_results = sorted(result['results'], key=lambda x: x.get('avg_monthly_searches', 0), reverse=True)
        
        print("\n🏆 TOP 5 OPORTUNIDADES:")
        for item in sorted_results[:5]:
            text = item.get('text', 'N/A')
            searches = item.get('avg_monthly_searches', 0)
            low_bid = item.get('low_bid_formatted', 0)
            high_bid = item.get('high_bid_formatted', 0)
            print(f"🔹 {text}")
            print(f"   Buscas: {searches} | CPC Min: R$ {low_bid:.2f} | CPC Max: R$ {high_bid:.2f}")

if __name__ == "__main__":
    test_discovery_planner()
