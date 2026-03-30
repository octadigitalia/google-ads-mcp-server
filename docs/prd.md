# Google Ads MCP Server Product Requirements Document (PRD)

## 1. Goals and Background Context

### Goals
- Implementar um servidor MCP robusto em Python para integração com a Google Ads API.
- **Autonomia de Gestão:** Fornecer ferramentas para diagnóstico independente e execução cirúrgica (Negativas, Criativos, Lances).
- **Blindagem de Conta:** Ferramentas para identificar e estancar "Wasted Spend" sem depender das recomendações automáticas do Google.
- Facilitar a automação de marketing via agentes de IA com foco em ROI real.

### Background Context
Este projeto visa preencher a lacuna entre modelos de linguagem (LLMs) e a complexa API do Google Ads. Ao expor as capacidades da API através do protocolo MCP, permitimos que agentes de IA orquestrem campanhas publicitárias com precisão técnica, analisando dados em tempo real e aplicando otimizações baseadas em lógica de negócio independente.

### Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2026-02-27 | 0.2.0 | Reorientação estratégica: Autonomia > Recomendações | Orion (aios-master) |
| 2026-02-27 | 0.1.0 | Initial draft with core requirements | Orion (aios-master) |

## 2. Requirements

### Functional Requirements
- **FR1: Autenticação e Configuração:** (Concluído)
- **FR2: Ferramentas de Relatórios:** (Concluído - GAQL Dinâmico)
- **FR3: Gestão de Ciclo de Vida:** (Concluído - Status e Orçamentos)
- **FR4: Controle de Negativas (O Escudo):** Tools para analisar Search Terms e adicionar negativas em massa.
- **FR5: Autonomia Criativa (A Mensagem):** Tools para atualizar Headlines e Descriptions de RSAs.
- **FR6: Planejamento Inteligente (O Radar):** Integração com Keyword Planner para novas ideias e tráfego.
- **FR7: Diagnóstico de Saúde (O Auditor):** Auditoria de gastos ineficientes.

### Non-Functional Requirements
- **NFR1: Performance:** Consultas de relatórios devem utilizar `SearchStream` para eficiência em grandes volumes de dados.
- **NFR2: Segurança:** Credenciais sensíveis nunca devem ser logadas ou expostas nas respostas das ferramentas.
- **NFR3: Robustez:** Implementar retry dinâmico para erros de quota da API.
- **NFR4: Documentação:** Cada Tool MCP deve ter descrições claras para que o LLM entenda quando e como usá-la.

## 3. Technical Assumptions

- **Linguagem:** Python 3.10+
- **SDK Principal:** `google-ads-python`
- **Protocolo:** Model Context Protocol (MCP) via `mcp` Python SDK.
- **Arquitetura:** Servidor MCP Stateless.
- **Testes:** Unidade para lógica de tradução e Integração em conta real.

## 4. Epic List

- **Epic 1: Foundation & Auth:** (Concluído)
- **Epic 2: Reporting & Data Collection:** (Concluído)
- **Epic 3: Campaign Lifecycle:** (Concluído - Status/Orçamentos)
- **Epic 4: Advanced Control & Shielding:** Gestão de Negativas e Criativos.
- **Epic 5: Intelligent Discovery:** Planejamento e Descoberta de Palavras-chave.

---
*Documento atualizado por Orion (aios-master). Próximo passo: Epic 4.*
