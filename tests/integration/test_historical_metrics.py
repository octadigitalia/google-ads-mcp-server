from src.mcp_server.server import get_keyword_historical_metrics
import json

def test_historical_validation():
    customer_id = "3400173105" # TecPlaner
    keywords = ["gerenciamento de obras", "reforma de apartamento"]
    
    print("TESTE DE METRICAS: Validando volume historico para as palavras fornecidas...")
    
    result = get_keyword_historical_metrics(customer_id=customer_id, keywords=keywords)
    
    if "error" in result:
        print("ERRO: " + str(result['error']))
    else:
        print("SUCESSO! Termos validados: " + str(result['metadata']['row_count']))
        
        for item in result['results']:
            text = item.get('text', 'N/A')
            avg = item.get('avg_monthly_searches', 0)
            low = item.get('low_bid_formatted', 0)
            high = item.get('high_bid_formatted', 0)
            
            print("\n- Termo: " + text)
            print("  Media Mensal: " + str(avg))
            print("  CPC Min: R$ " + f"{low:.2f}" + " | CPC Max: R$ " + f"{high:.2f}")
            
            if item.get('monthly_trend'):
                last = item['monthly_trend'][0]
                trend_str = "  Tendencia (" + str(last['month']) + "/" + str(last['year']) + "): " + str(last['volume'])
                print(trend_str)

if __name__ == "__main__":
    test_historical_validation()
