import os
import sys
import yaml
import socket
import hashlib
import webbrowser
import urllib.parse
from typing import Dict, Optional

# Garante que as importacoes do Google Ads e OAuth funcionem
try:
    from google_auth_oauthlib.flow import Flow
    from google.ads.googleads.client import GoogleAdsClient
except ImportError:
    print("\n[!] Erro: Dependencias nao encontradas.")
    print("Execute 'pip install -r requirements.txt' antes de rodar o setup.")
    sys.exit(1)

# Configuracoes do Servidor Local para OAuth
_PORT = 8080
_SERVER = "127.0.0.1"
_REDIRECT_URI = f"http://{_SERVER}:{_PORT}"
_SCOPE = "https://www.googleapis.com/auth/adwords"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    clear_screen()
    print("=" * 60)
    print(f"Google Ads MCP Server - {title}")
    print("=" * 60 + "\n")

def get_input(prompt: str, required: bool = True) -> str:
    while True:
        value = input(f"{prompt} ").strip()
        if value:
            return value
        if not required:
            return ""
        print("  [!] Este campo e obrigatorio.\n")

def setup_oauth_flow(client_id: str, client_secret: str) -> Optional[str]:
    """Inicia o fluxo OAuth e captura o token localmente."""
    print("\n[Iniciando Servidor Local de Autenticacao...]")
    
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

        state_token = hashlib.sha256(os.urandom(1024)).hexdigest()

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            state=state_token,
            prompt="consent",
            include_granted_scopes="true",
        )

        print("\nAbriando o navegador para autorizacao...")
        print("Se nao abrir automaticamente, clique no link abaixo:")
        print(f"URL: {auth_url}\n")
        
        webbrowser.open(auth_url)

        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((_SERVER, _PORT))
        sock.listen(1)
        
        print(f"Aguardando autorizacao (Escutando na porta {_PORT})...")
        connection, _ = sock.accept()
        data = connection.recv(2048)
        decoded = data.decode("utf-8")
        
        import re
        match = re.search(r"GET\s\/\?(.*) ", decoded)
        if not match:
            raise ValueError("Resposta invalida do Google.")
            
        params = dict(urllib.parse.parse_qsl(match.group(1)))
        
        html_response = (
            "HTTP/1.1 200 OK\n"
            "Content-Type: text/html\n\n"
            "<html><body style='font-family: Arial; text-align: center; margin-top: 50px;'>"
            "<h2>Autenticacao Concluida!</h2>"
            "<p>Voce ja pode fechar esta aba e voltar para o terminal.</p>"
            "</body></html>"
        )
        connection.sendall(html_response.encode("utf-8"))
        connection.close()

        if "error" in params:
            raise ValueError(f"Google retornou erro: {params['error']}")
            
        code = params.get("code")
        if not code:
            raise ValueError("Codigo de autorizacao ausente.")

        print("\nTrocando codigo pelo Refresh Token...")
        flow.fetch_token(code=code)
        
        refresh_token = flow.credentials.refresh_token
        if not refresh_token:
            raise ValueError("Refresh Token nao recebido.")
            
        print("Refresh Token obtido com sucesso!")
        return refresh_token

    except Exception as e:
        print(f"\n[!] Falha no fluxo OAuth: {str(e)}")
        return None

def validate_credentials(config: Dict[str, str]) -> bool:
    """Valida as credenciais conectando a API."""
    print("\nValidando credenciais (conectando a API)...")
    try:
        client_config = {
            "developer_token": config["developer_token"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "refresh_token": config["refresh_token"],
            "use_proto_plus": True
        }
        
        client = GoogleAdsClient.load_from_dict(client_config)
        customer_service = client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()
        accounts = len(accessible_customers.resource_names)
        
        print(f"Conexao bem-sucedida! Acesso a {accounts} conta(s).")
        return True
    except Exception as e:
        print(f"Falha na validacao das credenciais.")
        print(f"Detalhes do erro: {e}")
        return False

def main():
    print_header("Setup Wizard")
    print("Bem-vindo! Este assistente vai configurar suas credenciais do Google Ads.")
    input("\n[Pressione ENTER para comecar]")

    print_header("Passo 1: Developer Token")
    developer_token = get_input("\nInsira seu Developer Token:")

    print_header("Passo 2: Google Cloud Platform (GCP)")
    print("IMPORTANTE: Adicione 'http://127.0.0.1:8080' em 'URIs de redirecionamento autorizados'.")
    
    client_id = get_input("\nInsira o Client ID:")
    client_secret = get_input("Insira o Client Secret:")

    print_header("Passo 3: Autenticacao OAuth2")
    input("\n[Pressione ENTER para abrir o navegador]")
    
    refresh_token = setup_oauth_flow(client_id, client_secret)
    if not refresh_token:
        print("\nSetup abortado devido a erro de autenticacao.")
        sys.exit(1)

    print_header("Passo 4: Configuracoes Opcionais")
    login_customer_id = get_input("\nInsira o Login Customer ID (MCC) ou deixe em branco:", required=False)

    config = {
        "developer_token": developer_token,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }
    if login_customer_id:
        config["login_customer_id"] = login_customer_id.replace("-", "")

    if not validate_credentials(config):
        retry = input("Deseja salvar as credenciais mesmo assim? (s/N): ").lower()
        if retry != 's':
            sys.exit(1)

    print_header("Finalizando...")
    
    with open(".env", "w") as f:
        f.write(f"GOOGLE_ADS_DEVELOPER_TOKEN={developer_token}\n")
        f.write(f"GOOGLE_ADS_CLIENT_ID={client_id}\n")
        f.write(f"GOOGLE_ADS_CLIENT_SECRET={client_secret}\n")
        f.write(f"GOOGLE_ADS_REFRESH_TOKEN={refresh_token}\n")
        if login_customer_id:
            f.write(f"GOOGLE_ADS_LOGIN_CUSTOMER_ID={login_customer_id.replace('-', '')}\n")

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

    print("\nSETUP COMPLETO! O MCP Server esta pronto para uso.")
    print("Execute: mcp run src/mcp_server/server.py")

if __name__ == "__main__":
    main()
