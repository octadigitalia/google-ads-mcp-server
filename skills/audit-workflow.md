# Google Ads AI Skill: Robust Audit Workflow

Este workflow orquestra ferramentas MCP para realizar auditorias profundas de performance e estrutura no Google Ads.

## 📋 Pré-requisitos
- **Google Ads MCP Server** conectado e autenticado.
- Acesso à conta de cliente desejada (ex: `TecPlaner`).

---

## 🚀 O Workflow (4 Fases)

Sempre que solicitado a "auditar" ou "analisar performance", siga rigorosamente estas fases:

### Fase 1: Pulse (Health Check)
**Objetivo**: Validar conectividade e extrair o "batimento cardíaco" da conta.
- **Tools**: `get_campaign_performance` (date_range='LAST_30_DAYS').
- **Critério de Sucesso**: Identificar top 3 campanhas por gasto e validar o status da conta.

### Fase 2: Waste (Leak Detection)
**Objetivo**: Localizar desperdício imediato em termos de pesquisa ineficientes.
- **Tools**: `get_search_terms` (min_clicks=5).
- **Critério de Sucesso**: Gerar lista de termos com cliques significativos mas zero conversões para negativação imediata.

### Fase 3: Structure (Optimization)
**Objetivo**: Avaliar a qualidade dos anúncios e palavras-chave.
- **Tools**: `search_ads` (Usar GAQL para Ad Strength e Keyword Status).
- **Critério de Sucesso**: Identificar RSAs com status 'POOR' ou Keywords 'REJECTED'.

### Fase 4: Action (Correction)
**Objetivo**: Aplicar as recomendações geradas.
- **Tools**: `add_negative_keywords`, `set_campaign_budget`.
- **Critério de Sucesso**: Aplicar as negativas da Fase 2 e ajustar orçamentos ineficientes.

---

## 🛡️ Operational Standards
1. **Name-to-ID Resolution**: Prefira sempre usar o `campaign_name`. O servidor resolverá o ID internamente.
2. **Ambiguity Handling**: Se houver múltiplas campanhas com o mesmo nome, pare e peça o ID.
3. **Data Limit**: Respeite o limite de 50 linhas em consultas GAQL para evitar estouro de contexto.

---
*Created by Octa Digitalia (https://github.com/octadigitalia/google-ads-mcp-server)*
