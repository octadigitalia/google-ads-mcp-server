# 👑 Google Ads Expert AI Skill (Unified Product)

Este repositório fornece uma **AI Skill de Elite** para gestão de Google Ads, compatível com o ecossistema do Claude e outros agentes baseados em MCP.

---

## 📂 O que você está baixando?
- **`/skills`**: O "Cérebro" (Manifesto da Skill em JSON e Markdown).
- **`/src`**: O "Corpo" (Worker Engine em Python que executa as ações).

---

## 🚀 Instalação Rápida

### 1. Requisitos
- Python 3.10+
- `pip install -r requirements.txt`

### 2. No Claude Desktop (Recomendado para usar no Web)
O **Claude Web** sincroniza as ferramentas configuradas no seu **Claude Desktop**. Para usar na Web:
1. Abra o arquivo `claude_desktop_config.json`:
   - No Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - No Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. Adicione a Skill:
```json
{
  "mcpServers": {
    "google-ads-skill": {
      "command": "python",
      "args": ["C:/CAMINHO_DO_PROJETO/src/mcp_server/worker.py"],
      "env": {
        "PYTHONPATH": "C:/CAMINHO_DO_PROJETO"
      }
    }
  }
}
```
3. Reinicie o Claude Desktop.
4. **Para usar no Claude.ai (Web)**: Certifique-se de que o Claude Desktop esteja rodando. Usuários Pro/Team verão o ícone de martelo (Tools) habilitado na Web, permitindo usar a Skill de qualquer lugar!

---

## 🧠 Como usar a Skill (Primeiros Passos)
Após configurar, inicie um chat e diga:
> "Ative a Skill Google Ads Expert e rode o `run_setup`."

O sistema abrirá o seu navegador para você autorizar o acesso à sua conta. Depois disso, você pode dar comandos como:
- *"Faça uma auditoria completa na minha conta 123-456-7890"*
- *"Quais termos de pesquisa estão desperdiçando dinheiro?"*
- *"Aumente o orçamento da campanha X em 20%"*

---

## 🧠 Super-Skills Disponíveis

1. **`run_unified_audit`**: Auditoria completa de performance, desperdício e estrutura.
2. **`run_optimization_action`**: Aplica negativas, ajusta orçamentos e altera status.
3. **`run_setup`**: Configura suas credenciais via fluxo seguro de OAuth2.

---
*Created by Octa Digitalia. Elevate your Google Ads game with AI.*
