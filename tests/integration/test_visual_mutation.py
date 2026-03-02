from src.mcp_server.server import set_campaign_status
import json
import time

def test_visual_mutation():
    customer_id = "3400173105" # TecPlaner
    campaign_id = "6522329996" # [ONGOING] [RedePesquisa] - LEADS
    WAIT_TIME = 45 # Segundos para você conferir no painel
    
    print("🛠️ [VISUAL TEST] Iniciando troca de status em câmera lenta...")
    
    # 1. ATIVAR
    print("\n🚀 PASSO 1: MUDANDO PARA 'ENABLED'...")
    res1 = set_campaign_status(customer_id, campaign_id, "ENABLED")
    
    if "error" in res1:
        print(f"❌ Erro ao ativar: {res1['error']}")
        return

    print("✅ COMANDO ENVIADO! A campanha deve aparecer como ATIVA no Google Ads agora.")
    print(f"⏳ Aguardando {WAIT_TIME} segundos para você atualizar seu navegador...")
    
    # Contagem regressiva visual
    for i in range(WAIT_TIME, 0, -1):
        print(f"\r⏱️ Revertendo para PAUSED em: {i}s  ", end="", flush=True)
        time.sleep(1)
    
    # 2. PAUSAR (SEGURANÇA)
    print("\n\n🛑 PASSO 2: VOLTANDO PARA 'PAUSED'...")
    res2 = set_campaign_status(customer_id, campaign_id, "PAUSED")
    
    if "error" in res2:
        print(f"❌ Erro ao pausar: {res2['error']}")
    else:
        print("✅ SEGURANÇA: Campanha pausada com sucesso. Teste visual concluído!")

if __name__ == "__main__":
    test_visual_mutation()
