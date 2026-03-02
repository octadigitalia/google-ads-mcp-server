from src.mcp_server.server import list_accessible_customers
import json

def test_discovery():
    print("🔍 Iniciando descoberta de contas acessíveis...")
    result = list_accessible_customers()
    
    if "error" in result:
        print(f"❌ Erro: {result['error']}")
    else:
        print(f"✅ Sucesso! Contas encontradas: {result['metadata']['row_count']}")
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_discovery()
