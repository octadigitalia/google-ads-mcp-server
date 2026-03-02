from src.mcp_server.server import get_campaign_performance
import json

def test_dynamic_reporting():
    customer_id = "3400173105" # TecPlaner
    
    # Lista de períodos para testar a robustez
    periods = ["YESTERDAY", "LAST_7_DAYS"]
    
    for period in periods:
        print(f"\n{'-'*50}")
        print(f"📅 TESTANDO PERÍODO: {period}")
        print(f"{'-'*50}")
        
        result = get_campaign_performance(customer_id=customer_id, date_range=period)
        
        if "error" in result:
            print(f"❌ Falha para {period}: {result['error']}")
        else:
            count = result['metadata']['row_count']
            print(f"✅ Sucesso! Campanhas processadas: {count}")
            
            # Mostra apenas a primeira para validar o formato
            if count > 0:
                item = result['results'][0]
                name = item['campaign']['name']
                cost = item['metrics']['cost_formatted']
                print(f"   Exemplo: {name} | Gasto: R$ {cost:.2f}")
            else:
                print("   ℹ️ Nenhuma campanha com impressões neste período.")

if __name__ == "__main__":
    test_dynamic_reporting()
