# 🚀 Google Ads MCP Server

Este é um servidor **Model Context Protocol (MCP)** robusto para interagir com a API do Google Ads (v23+). Ele foi projetado para permitir que agentes de IA operem contas de Google Ads com autonomia, segurança e economia de tokens.

## ✨ Principais Funcionalidades

- **Onboarding Zero-Friction**: Script interativo (mcp-setup.py) que automatiza o fluxo OAuth2 e valida credenciais.
- **Resolução de Nomes Inteligente**: Todas as ferramentas aceitam **Nomes de Recursos** (ex: 'Campanha de Vendas') em vez de IDs numéricos chatos.
- **Linter GAQL Nativo**: Validação prévia de consultas GAQL com sugestões 'Did you mean?' em caso de erros.
- **Self-Healing AI**: Tradução de erros complexos da API em mensagens semânticas que a IA consegue entender e corrigir.
- **Account Snapshot**: Visão 360º da conta em um único comando para análise rápida de performance.
- **Data Density**: Otimização agressiva de JSON para economizar tokens na janela de contexto da LLM.

## 🛠️ Instalação e Setup

1. **Clone o repositório e instale dependências:**
   \\\ash
   pip install -r requirements.txt
   \\\

2. **Execute o Assistente de Configuração:**
   \\\ash
   python mcp-setup.py
   \\\
   *O assistente irá guiar você na obtenção do Developer Token, Client ID/Secret e fará a autorização no navegador automaticamente.*

## 🚀 Como Executar

Após o setup, você pode iniciar o servidor usando o MCP:

\\\ash
$env:PYTHONPATH="."; python src/mcp_server/server.py
\\\

Ou usando o **MCP Inspector** para testes visuais:

\\\ash
npx @modelcontextprotocol/inspector $env:PYTHONPATH="."; python src/mcp_server/server.py
\\\

## 📂 Estrutura das Ferramentas (Tools)

- **[REPORT]**: \search_ads\, \get_campaign_performance\, \get_account_snapshot\, \get_search_terms\, \list_user_lists\.
- **[MUTATION]**: \create_search_campaign\, \set_campaign_status\, \set_campaign_budget\, \dd_keywords\, \update_rsa_assets\, \create_pmax_campaign\.
- **[MARKET_DATA]**: \generate_keyword_ideas\, \get_keyword_historical_metrics\.

## 🛡️ Segurança

Este servidor utiliza **Field Masks** em todas as operações de mutação para garantir que apenas os campos pretendidos sejam alterados. Nunca suba seus arquivos \.env\ ou \google-ads.yaml\ para repositórios públicos.

---
*Desenvolvido para máxima eficiência com agentes de IA.*
