from src.mcp_server.server import set_campaign_status
import json
import time

def test_mutation():
    customer_id = "3400173105" # TecPlaner
    campaign_id = "6522329996" # [ONGOING] [RedePesquisa] - LEADS
    
    print(f"🛠️ Testando alteração de status para a campanha {campaign_id}...")
    
    # 1. Tentar Ativar
    print("\n➡️ Passo 1: Mudando para ENABLED...")
    res1 = set_campaign_status(customer_id, campaign_id, "ENABLED")
    
    if "error" in res1:
        print(f"❌ Erro no Passo 1: {res1['error']}")
        return

    print(json.dumps(res1, indent=2))
    print("✅ Campanha Ativada com sucesso!")
    
    # Pequena pausa para a API processar
    time.sleep(2)
    
    # 2. Voltar para PAUSED (Segurança)
    print("\n➡️ Passo 2: Voltando para PAUSED...")
    res2 = set_campaign_status(customer_id, campaign_id, "PAUSED")
    
    if "error" in res2:
        print(f"❌ Erro no Passo 2: {res2['error']}")
        return

    print(json.dumps(res2, indent=2))
    print("✅ Campanha Pausada novamente. Teste concluído com segurança.")

if __name__ == "__main__":
    test_mutation()
