# 👑 Google Ads Expert AI Skill (Unified Product)

Este repositório fornece uma **AI Skill de Elite** para gestão de Google Ads, compatível com o ecossistema do Claude e outros agentes baseados em MCP.

---

## 📂 O que você está baixando?
- **`/skills`**: O "Cérebro" (Manifesto da Skill em JSON e Markdown).
- **`/src`**: O "Corpo" (Worker Engine em Python que executa as ações).

---

## 🚀 Instalação Rápida (Claude Desktop / Cowork)

### 1. Requisitos
- Python 3.10+
- `pip install -r requirements.txt`

### 2. Configuração (Claude Desktop)
Adicione o seguinte ao seu `claude_desktop_config.json`:

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

### 3. Primeira Execução e Autenticação
Ao iniciar um chat no Claude, peça para a Skill rodar o setup:
> "Rode a Skill Google Ads Expert e inicie o `run_setup`."

O Worker abrirá o seu navegador automaticamente para autorização do Google Ads.

---

## 🧠 Super-Skills Disponíveis

1. **`run_unified_audit`**: Auditoria completa de performance, desperdício e estrutura.
2. **`run_optimization_action`**: Aplica negativas, ajusta orçamentos e altera status.
3. **`run_setup`**: Configura suas credenciais via fluxo seguro de OAuth2.

---
*Created by Octa Digitalia. Elevate your Google Ads game with AI.*
