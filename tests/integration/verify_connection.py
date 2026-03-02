import sys
from src.mcp_server.client import create_google_ads_client
from src.mcp_server.config import get_settings

def verify():
    """Realiza uma chamada simples para validar as credenciais."""
    print("🚀 Iniciando verificação de conexão com Google Ads API...")
    
    try:
        settings = get_settings()
        client = create_google_ads_client()
        googleads_service = client.get_service("GoogleAdsService")

        # Se tivermos um customer_id, tentamos listar algo básico dele
        if settings.login_customer_id:
            customer_id = settings.login_customer_id
            print(f"📡 Testando acesso à conta: {customer_id}")
            
            query = "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"
            response = googleads_service.search(customer_id=customer_id, query=query)
            
            for row in response:
                print(f"✅ Conexão estabelecida! Conta: {row.customer.descriptive_name} ({row.customer.id})")
                return True
        else:
            print("⚠️ login_customer_id não fornecido. Apenas o cliente foi inicializado.")
            return True

    except Exception as e:
        print(f"❌ Erro na conexão: {str(e)}")
        return False

if __name__ == "__main__":
    if verify():
        sys.exit(0)
    else:
        sys.exit(1)
