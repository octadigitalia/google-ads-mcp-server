import os
import sys
import subprocess
import json
import zipfile
from pathlib import Path

def print_banner():
    print("\n" + "="*60)
    print("👑 Google Ads Expert AI Skill - Automated Installer")
    print("="*60 + "\n")

def run_command(cmd):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except Exception as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def create_claude_zip():
    zip_name = "google-ads-expert-skill.zip"
    files_to_include = [
        "skills/google-ads-expert.md",
        "skills/google-ads-expert.json",
        "README.md"
    ]
    try:
        with zipfile.ZipFile(zip_name, 'w') as zipf:
            for file in files_to_include:
                if os.path.exists(file):
                    zipf.write(file)
        return zip_name
    except Exception as e:
        print(f"❌ Erro ao criar ZIP: {e}")
        return None

def main():
    print_banner()
    
    # 1. Instalação
    print("📦 Passo 1: Instalando dependências técnicas...")
    if run_command(["pip", "install", "-r", "requirements.txt"]):
        print("✅ Dependências instaladas com sucesso!")
    
    # 2. Caminho Absoluto
    project_path = str(Path(__file__).parent.absolute()).replace("\\", "/")
    worker_path = f"{project_path}/src/mcp_server/worker.py"
    
    # 3. Configuração Claude Desktop
    mcp_config = {
        "mcpServers": {
            "google-ads-expert": {
                "command": "python",
                "args": [worker_path],
                "env": { "PYTHONPATH": project_path }
            }
        }
    }
    
    # 4. Preparação Claude Web
    print("\n📦 Passo 2: Preparando pacote para Claude Web (Skills)...")
    zip_file = create_claude_zip()
    
    print("\n" + "="*60)
    print("🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*60)
    
    print(f"\n💻 PARA CLAUDE DESKTOP:")
    print("Copie e cole este JSON no seu 'claude_desktop_config.json':")
    print(json.dumps(mcp_config, indent=2))
    
    print(f"\n🌐 PARA CLAUDE WEB / SKILLS:")
    print(f"1. Localize o arquivo criado: {zip_file}")
    print("2. Vá na seção de 'Skills' ou 'Projects' do Claude e faça o UPLOAD deste ZIP.")
    print("3. O Claude lerá as instruções e ativará suas Super-Habilidades automaticamente.")
    
    print("\n🚀 PRÓXIMO PASSO:")
    print("No chat do Claude, diga: 'Inicie a Skill Google Ads e rode o run_setup'")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
