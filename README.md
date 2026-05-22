# Google Ads Expert — MCP Server

Servidor MCP (Model Context Protocol) para gestão completa de contas Google Ads via IA. Conecta Claude (Desktop, Web ou Code) à Google Ads API com **77 tools** cobrindo auditoria, criação de campanhas, otimização, pesquisa de keywords, targeting, estratégias de lance e muito mais.

---

## O que é isso?

Um **worker engine em Python** que expõe a Google Ads API como tools MCP. Quando conectado ao Claude, transforma o modelo em um Gestor de Tráfego Sênior capaz de:

- Auditar contas completas com uma instrução
- Criar e estruturar campanhas do zero
- Otimizar keywords, bids e orçamentos com base em dados
- Manter histórico de ações para decisões incrementais
- Aplicar estratégias especializadas (Growth, Lançamento, Low Ticket, VSL)

---

## Arquitetura

```
Claude (Web / Desktop / Code)
        │
        │  MCP Protocol (SSE ou stdio)
        ▼
  Worker Engine (Python)          ← src/mcp_server/worker.py
        │  77 tools expostos
        ▼
  Google Ads API (v23)            ← src/mcp_server/logic.py
        │
        ▼
  Sua conta Google Ads
```

**Skills** (`/skills/*.md`) — instruções de persona e orquestração carregadas pelo Claude. Não executam código; orientam como usar as tools.

**Log de ações** (`campaign-log/{customer_id}.md`) — histórico persistente de mutações para garantir incrementalidade nas otimizações.

---

## Pré-requisitos

- Python 3.10+
- Conta Google Ads com acesso de desenvolvedor
- [Developer Token](https://developers.google.com/google-ads/api/docs/get-started/dev-token) do Google Ads API
- OAuth2 credentials (Client ID + Secret) do Google Cloud Console

---

## Instalação

```bash
git clone https://github.com/octadigitalia/google-ads-mcp-server
cd google-ads-mcp-server
python install.py
```

O instalador oferece três modos:

### Modo 1: Local (Claude Desktop / Claude Code)

O worker roda na sua máquina. Configure o Claude com:

```json
{
  "mcpServers": {
    "google-ads-expert": {
      "type": "sse",
      "url": "http://127.0.0.1:8765/sse"
    }
  }
}
```

Inicie o worker antes de usar:
```bash
python start_worker.py
```

Ou use o atalho no Windows:
```
start_worker.bat
```

### Modo 2: VPS / Servidor Linux

O `install.py` gera automaticamente:
- `google-ads-mcp.service` — serviço systemd para auto-start
- `google-ads-mcp-nginx.conf` — proxy reverso nginx (opcional)
- URL pública configurável com HTTPS via Let's Encrypt

Configure com:
```bash
python install.py
# escolha opção 2 (VPS)
```

### Modo 3: Claude Web (claude.ai)

O instalador gera um `.zip` com a skill escolhida. Faça upload em **Settings > Skills** ou adicione ao seu **Project**.

---

## Configuração de Credenciais

Após instalar, rode o setup para autenticar com sua conta Google Ads:

No chat com Claude:
```
check_connection
run_setup
```

O `run_setup` abre o navegador para OAuth2 e salva as credenciais em `.env`.

Ou configure manualmente em `.env`:
```env
GOOGLE_ADS_DEVELOPER_TOKEN=seu_token
GOOGLE_ADS_CLIENT_ID=seu_client_id
GOOGLE_ADS_CLIENT_SECRET=seu_client_secret
GOOGLE_ADS_REFRESH_TOKEN=seu_refresh_token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=seu_mcc_id
```

---

## Skills Disponíveis

| Skill | Arquivo | Para quem |
|-------|---------|-----------|
| **Master** | `skills/google-ads-expert.md` | Gestão geral, diagnóstico completo, 77 tools |
| **Growth Marketing** | `skills/growth-marketing.md` | SaaS, e-commerce, negócios com LTV — ICE Score |
| **Fórmula de Lançamento** | `skills/launch-formula.md` | PLF, carrinho aberto/fechado, pré-lançamento |
| **Low Ticket** | `skills/low-ticket.md` | Produtos R$27-197, volume, CPA baixo, PMax |
| **Funil VSL** | `skills/vsl-funnel.md` | VSL, retargeting por profundidade de vídeo |

Para usar uma skill no Claude, adicione o arquivo `.md` ao contexto do seu Project ou peça ao Claude para seguir as instruções do arquivo.

---

## 77 Tools por Categoria

| Categoria | Qtd | Exemplos |
|-----------|-----|---------|
| Setup & Utilidades | 3 | `check_connection`, `run_setup`, `list_accounts` |
| Relatórios & Auditoria | 14 | `get_account_snapshot`, `get_keyword_performance`, `get_auction_insights` |
| Pesquisa de Keywords | 4 | `keyword_ideas`, `keyword_volume`, `keyword_forecast` |
| Criação Atômica | 5 | `create_search_campaign`, `create_ad_group`, `create_responsive_search_ad` |
| Criação por Conveniência | 2 | `create_full_campaign`, `create_campaign_structure` |
| Targeting & Segmentação | 6 | `set_location_targeting`, `set_device_bid_adjustment`, `set_ad_schedule` |
| Estratégias de Lance | 5 | `create_bid_strategy`, `apply_bid_strategy`, `create_shared_budget` |
| Otimização / Mutações | 12 | `bulk_pause_keywords`, `replace_keywords_exact`, `set_keyword_bid` |
| Extensões / Assets | 6 | `add_campaign_sitelinks`, `add_callout_extension`, `add_price_extension` |
| Conversões | 3 | `create_conversion_action`, `upload_offline_conversions`, `upload_customer_match` |
| Organização / Labels | 3 | `create_label`, `apply_label`, `list_labels` |
| Audiências | 3 | `list_user_lists`, `link_audience_to_adgroup`, `create_audience` |
| Features Avançadas | 7 | `apply_recommendation`, `get_billing_info`, `list_invoices` |
| Faturamento | 2 | `get_billing_info`, `list_invoices` |

---

## Primeiros Passos

Após conectar o worker e configurar as credenciais:

```
# 1. Verificar conexão
check_connection

# 2. Listar suas contas
list_accounts

# 3. Auditoria completa
"Faça uma auditoria completa na conta {customer_id}"

# 4. Pesquisa de keywords
"Pesquisa de keywords para 'plano de saúde empresarial'"

# 5. Criar campanha
"Crie uma campanha de pesquisa para minha conta com foco em [produto]"
```

---

## Log de Ações

O sistema mantém um histórico em `campaign-log/{customer_id}.md`. Toda mutação é registrada automaticamente com:
- O que foi alterado (antes → depois)
- Dados que embasaram a decisão
- Data e contexto estratégico
- Próxima data de revisão

Isso garante que otimizações futuras sejam incrementais e baseadas em evidência.

---

## Estrutura do Projeto

```
google-ads-mcp-server/
├── src/mcp_server/
│   ├── worker.py      # 77 tools expostos via MCP
│   ├── logic.py       # Implementação das chamadas Google Ads API
│   ├── auth.py        # Fluxo OAuth2
│   ├── client.py      # Cliente Google Ads
│   ├── config.py      # Configurações
│   └── utils.py       # Helpers (serialização, ResourceResolver, etc.)
├── skills/
│   ├── google-ads-expert.md   # Skill master (77 tools)
│   ├── growth-marketing.md    # Skill Growth Marketing
│   ├── launch-formula.md      # Skill Fórmula de Lançamento
│   ├── low-ticket.md          # Skill Low Ticket
│   ├── vsl-funnel.md          # Skill Funil VSL
│   ├── audit-workflow.md      # Referência rápida de diagnóstico
│   └── google-ads-expert.json # Metadados do pacote
├── campaign-log/      # Histórico de ações por conta (gitignored)
├── install.py         # Instalador (local + VPS)
├── start_worker.py    # Entrypoint do worker (SSE)
├── start_worker.bat   # Atalho Windows
└── requirements.txt
```

---

## Segurança

- Credenciais armazenadas apenas em `.env` e `google-ads.yaml` (gitignored)
- Campanhas criadas sempre **PAUSADAS** — ativação manual obrigatória
- `bulk_pause_keywords` tem `dry_run=True` por padrão
- Toda mutação financeira exige confirmação explícita (via skill)

---

## Licença

MIT — Octa Digitalia
