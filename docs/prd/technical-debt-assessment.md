# Technical Debt Assessment - FINAL

## Executive Summary
- **Total de débitos**: 6
- **Críticos**: 1 | **Altos**: 2 | **Médios**: 3
- **Esforço total estimado**: ~8-12 horas
- **Foco Principal**: Implementar o Native Field Linter para a Epic 9 e reduzir fricção no Setup Inicial.

## Inventário Completo de Débitos

### Sistema (Validado por @architect)
| ID | Débito | Severidade | Horas | Prioridade |
|----|--------|------------|-------|------------|
| DT-1 | **Falta de Linter GAQL** - Erros brutos da API quebram o contexto da IA. | Crítico | 4h | P0 |
| DT-2 | **Setup Manual (Wizard)** - Necessidade de editar YAML manual bloqueia adoção. | Alto | 3h | P1 |
| DT-3 | **Hardcoding Geo/Lang** - Ferramentas (ex: métricas) fixas em PT-BR. | Médio | 1h | P2 |
| DT-6 | **Tratamento de Erros Genérico** - Exceções não formatadas para LLM. | Médio | 1h | P2 |

### Database & API (Consolidado por @data-engineer)
| ID | Débito | Severidade | Horas | Prioridade |
|----|--------|------------|-------|------------|
| DT-4 | **Cache de Metadados** - Risco de Rate Limit ao bater no `GoogleAdsFieldService` para o Linter. Necessidade de caching local (`.json`). | Alto | 2h | P1 |

### Frontend & UX (Consolidado por @ux-design-expert)
| ID | Débito | Severidade | Horas | Prioridade |
|----|--------|------------|-------|------------|
| DT-5 | **Controle de Output (Contexto)** - Consultas GAQL não paginadas podem estourar o limite de tokens da LLM. Limite sugerido: máximo de 50 linhas por tool call (com paginação implícita). | Médio | 1h | P2 |

## Respostas Consolidadas aos Especialistas
- **@data-engineer sobre Quotas da API**: Sim, consultar o `GoogleAdsFieldService` dinamicamente para cada `search_ads` é ineficiente e consome quota. A solução é serializar os arquivos JSON de metadados já gerados na auditoria e embarcá-los no servidor como fonte da verdade estática, atualizada apenas via script de build.
- **@ux-design-expert sobre Limites de Linha**: Para manter a janela de contexto limpa e rápida, o servidor deve limitar os resultados GAQL a **no máximo 50 registros por default**, com avisos na metadata se houverem mais resultados disponíveis (paginação).

## Plano de Resolução (Ordem Recomendada)

1. **Sprint Atual (Epic 9 - Data Mastery)**:
   - **(P0) DT-1 & (P1) DT-4**: Implementar Linter (Story 9.4) utilizando os JSONs de metadados cacheados da auditoria. Implementar sugestões inteligentes (Closest Match).
   - **(P2) DT-5**: Adicionar limites de `row_count` nas respostas padronizadas da API.

2. **Próxima Sprint (Epic 8 - Production Ready)**:
   - **(P1) DT-2**: Concluir o `mcp-setup` CLI tool (Story 8.3) com onboarding guiado para credenciais.
   - **(P2) DT-3 & DT-6**: Parametrizar constantes Geo/Idioma e aprimorar tratativas de exceção.

## Riscos e Mitigações
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Linter rejeitar query válida | Alto (IA não consegue agir) | Usar o Linter como Warning (aviso + fallback) no início, não como blocker (erro duro), ou garantir que o cache do FieldService esteja 100% atualizado. |

## Critérios de Sucesso
- `search_ads` não retorna mais Erro 400 por erro de campo, mas sim uma sugestão do Linter.
- Tempo de resposta do `search_ads` não aumenta mais de 50ms com a adição do Linter.
- Servidor inicia com credenciais válidas obtidas via fluxo de CLI.

---
*Assessment consolidado gerado por @architect via Brownfield Discovery Workflow.*
