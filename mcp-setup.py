import os
import sys
import yaml
import socket
import hashlib
import webbrowser
import urllib.parse
from typing import Dict, Optional

# Garante que as importações do Google Ads e OAuth funcionem
try:
    from google_auth_oauthlib.flow import Flow
    from google.ads.googleads.client import GoogleAdsClient
except ImportError:
    print("
[!] Erro: Dependências não encontradas.")
    print("Execute 'pip install -r requirements.txt' antes de rodar o setup.")
    sys.exit(1)

# Configurações do Servidor Local para OAuth
_PORT = 8080
_SERVER = "127.0.0.1"
_REDIRECT_URI = f"http://{_SERVER}:{_PORT}"
_SCOPE = "https://www.googleapis.com/auth/adwords"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    clear_screen()
    print("=" * 60)
    print(f"🌟 Google Ads MCP Server - {title}")
    print("=" * 60 + "
")

def get_input(prompt: str, required: bool = True) -> str:
    while True:
        value = input(f"{prompt} ").strip()
        if value:
            return value
        if not required:
            return ""
        print("  [!] Este campo é obrigatório.
")

def setup_oauth_flow(client_id: str, client_secret: str) -> Optional[str]:
    """Inicia o fluxo OAuth e captura o token localmente."""
    print("
[Iniciando Servidor Local de Autenticação...]")
    
    # Criamos a configuração do cliente dinamicamente (em memória)
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [_REDIRECT_URI]
        }
    }

    try:
        flow = Flow.from_client_config(client_config, scopes=[_SCOPE])
        flow.redirect_uri = _REDIRECT_URI

        # Token anti-CSRF
        state_token = hashlib.sha256(os.urandom(1024)).hexdigest()

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            state=state_token,
            prompt="consent",
            include_granted_scopes="true",
        )

        print("
🌐 Abrindo o navegador para autorização...")
        print("Se não abrir automaticamente, clique no link abaixo:")
        print(f"👉 {auth_url}
")
        
        webbrowser.open(auth_url)

        # Inicia o servidor de socket
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((_SERVER, _PORT))
        sock.listen(1)
        
        print(f"⏳ Aguardando autorização (Escutando na porta {_PORT})...")
        connection, _ = sock.accept()
        data = connection.recv(2048)
        decoded = data.decode("utf-8")
        
        # Extrai os parâmetros
        import re
        match = re.search(r"GET\s\/\?(.*) ", decoded)
        if not match:
            raise ValueError("Resposta inválida do Google.")
            
        params = dict(urllib.parse.parse_qsl(match.group(1)))
        
        # Resposta HTTP para o navegador
        html_response = (
            "HTTP/1.1 200 OK
"
            "Content-Type: text/html

"
            "<html><body style='font-family: Arial; text-align: center; margin-top: 50px;'>"
            "<h2>✅ Autenticacao Concluida!</h2>"
            "<p>Voce ja pode fechar esta aba e voltar para o terminal.</p>"
            "</body></html>"
        )
        connection.sendall(html_response.encode())
        connection.close()

        if "error" in params:
            raise ValueError(f"Google retornou erro: {params['error']}")
            
        code = params.get("code")
        if not code:
            raise ValueError("Código de autorização ausente.")

        print("
🔐 Trocando código pelo Refresh Token...")
        flow.fetch_token(code=code)
        
        refresh_token = flow.credentials.refresh_token
        if not refresh_token:
            raise ValueError("Refresh Token não recebido. Certifique-se de usar uma conta diferente ou forçar o re-consentimento.")
            
        print("✅ Refresh Token obtido com sucesso!")
        return refresh_token

    except Exception as e:
        print(f"
[!] Falha no fluxo OAuth: {str(e)}")
        return None

def validate_credentials(config: Dict[str, str]) -> bool:
    """Tenta criar um cliente e listar contas acessíveis para validar as credenciais."""
    print("
🧪 Validando credenciais (conectando à API)...")
    try:
        # Configuração mínima necessária
        client_config = {
            "developer_token": config["developer_token"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": config["refresh_token"],
            "use_proto_plus": True
        }
        
        client = GoogleAdsClient.load_from_dict(client_config)
        customer_service = client.get_service("CustomerService")
        
        # Chamada leve
        accessible_customers = customer_service.list_accessible_customers()
        accounts = len(accessible_customers.resource_names)
        
        print(f"✅ Conexão bem-sucedida! Sua credencial tem acesso a {accounts} conta(s).")
        return True
    except Exception as e:
        print(f"❌ Falha na validação das credenciais.")
        print(f"Detalhes do erro: {e}")
        return False

def main():
    print_header("Setup Wizard")
    print("Bem-vindo! Este assistente vai configurar suas credenciais do Google Ads.")
    print("Nós vamos configurar automaticamente o `.env` e o `google-ads.yaml`.")
    input("
[Pressione ENTER para começar]")

    # Passo 1: Developer Token
    print_header("Passo 1: Developer Token")
    print("O Developer Token é obtido no Google Ads (Ferramentas > Centro de API).")
    print("Pode estar no status 'Acesso de teste' para este uso.")
    developer_token = get_input("
Insira seu Developer Token:")

    # Passo 2: Credenciais do GCP
    print_header("Passo 2: Google Cloud Platform (GCP)")
    print("Precisamos de um Client ID e Client Secret (Tipo: Aplicativo Web).")
    print("IMPORTANTE: Adicione 'http://127.0.0.1:8080' em 'URIs de redirecionamento autorizados'.")
    print("Link: https://console.cloud.google.com/apis/credentials")
    
    client_id = get_input("
Insira o Client ID:")
    client_secret = get_input("Insira o Client Secret:")

    # Passo 3: OAuth Flow
    print_header("Passo 3: Autenticação OAuth2")
    print("Vamos abrir o navegador para você aprovar o acesso à sua conta.")
    print("Certifique-se de fazer login com o e-mail que tem acesso ao Google Ads.")
    input("
[Pressione ENTER para abrir o navegador]")
    
    refresh_token = setup_oauth_flow(client_id, client_secret)
    if not refresh_token:
        print("
Setup abortado devido a erro de autenticação.")
        sys.exit(1)

    # Coleta Opcionais
    print_header("Passo 4: Configurações Opcionais")
    login_customer_id = get_input("
Insira o Login Customer ID (ID da MCC, se usar uma. Opcional - deixe em branco para pular):", required=False)

    # Validando
    config = {
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id.replace("-", "")

    if not validate_credentials(config):
        print("
Dica: Verifique se o Developer Token é válido e se a conta do GCP tem a 'Google Ads API' ativada.")
        retry = input("Deseja salvar as credenciais mesmo assim? (s/N): ").lower()
        if retry != 's':
            print("Setup abortado.")
            sys.exit(1)

    # Passo 5: Salvar Arquivos
    print_header("Finalizando...")
    
    # Salvar .env
    with open(".env", "w") as f:
        f.write(f"GOOGLE_ADS_DEVELOPER_TOKEN={developer_token}
")
        f.write(f"GOOGLE_ADS_CLIENT_ID={client_id}
")
        f.write(f"GOOGLE_ADS_CLIENT_SECRET={client_secret}
")
        f.write(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}
")
        if login_customer_id:
            f.write(f"GOOGLE_ADS_LOGIN_CUSTOMER_ID={login_customer_id.replace('-', '')}
")
    print("📄 Arquivo '.env' criado com sucesso.")

    # Salvar google-ads.yaml
    yaml_config = {
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "use_proto_plus": True
    }
    if login_customer_id:
        yaml_config["login_customer_id"] = login_customer_id.replace("-", "")

    with open("google-ads.yaml", "w") as f:
        yaml.dump(yaml_config, f, default_flow_style=False)
    print("📄 Arquivo 'google-ads.yaml' criado com sucesso.")

    print("
🎉 SETUP COMPLETO! O MCP Server está pronto para uso.")
    print("Para iniciar o servidor, execute: mcp run src/mcp_server/server.py")

if __name__ == "__main__":
    main()
