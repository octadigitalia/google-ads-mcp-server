from src.mcp_server.server import set_campaign_budget
import json

def test_budget_update():
    customer_id = "3400173105" # TecPlaner
    campaign_id = "6522329996" # [ONGOING] [RedePesquisa] - LEADS
    NEW_AMOUNT = 1.00 # Vamos testar com 1 real
    
    print(f"💰 TESTE DE ORCAMENTO: Alterando campanha {campaign_id} para R$ {NEW_AMOUNT:.2f}...")
    
    result = set_campaign_budget(customer_id, campaign_id, NEW_AMOUNT)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print("✅ SUCESSO! Orcamento atualizado.")
        print(json.dumps(result, indent=2))
        print(f"\n👉 Confira no Google Ads se o orcamento da campanha mudou para R$ {NEW_AMOUNT:.2f}.")

if __name__ == "__main__":
    test_budget_update()
