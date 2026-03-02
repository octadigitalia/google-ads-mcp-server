from src.mcp_server.server import add_negative_keywords
import json

def test_add_negatives():
    customer_id = "3400173105" # TecPlaner
    campaign_id = "6522329996" # [ONGOING] [RedePesquisa] - LEADS
    negatives = ["consultoria de obra gratuita", "gerenciamento de obra pdf"]
    
    print(f"🛡️ TESTE DE BLINDAGEM: Adicionando {len(negatives)} negativas à campanha {campaign_id}...")
    
    result = add_negative_keywords(customer_id, campaign_id, negatives)
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ SUCESSO! {result['added_count']} palavras adicionadas.")
        print(json.dumps(result, indent=2))
        print(f"\n👉 Verifique na aba 'Palavras-chave Negativas' da campanha {campaign_id} no Google Ads.")

if __name__ == "__main__":
    test_add_negatives()
