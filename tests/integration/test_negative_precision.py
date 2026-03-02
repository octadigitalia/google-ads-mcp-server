from src.mcp_server.server import add_negative_keywords
import json

def test_negative_precision():
    customer_id = "3400173105" # TecPlaner
    campaign_id = "6522329996" # [ONGOING] [RedePesquisa] - LEADS
    
    print("🎯 TESTE DE PRECISÃO: Adicionando negativas específicas...")
    
    # 1. Testar Correspondência EXATA
    print("\n➡️ Passo 1: Negativa EXATA [gratis]...")
    res_exact = add_negative_keywords(customer_id, campaign_id, ["gratis"], match_type="EXACT")
    print(json.dumps(res_exact, indent=2))
    
    # 2. Testar Correspondência de FRASE
    print("\n➡️ Passo 2: Negativa de FRASE \"como fazer\"...")
    res_phrase = add_negative_keywords(customer_id, campaign_id, ["como fazer"], match_type="PHRASE")
    print(json.dumps(res_phrase, indent=2))

if __name__ == "__main__":
    test_negative_precision()
