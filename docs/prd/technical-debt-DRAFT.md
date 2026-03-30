# Technical Debt Assessment - DRAFT
## Para Revisão dos Especialistas

Este documento consolida os débitos técnicos identificados durante a fase de Descoberta Brownfield do Google Ads MCP Server.

### 1. Débitos de Sistema (Validado por @architect)
- [ ] **Validação de GAQL Inexistente**: O servidor executa queries brutas. Erros de sintaxe ou campos inválidos resultam em falhas 400 da API sem contexto para a IA.
- [ ] **Hardcoding de Localização/Idioma**: Ferramentas de ideias de palavras-chave estão fixas em Brasil/Português, limitando o uso global.
- [ ] **Configuração Manual**: A dependência de `google-ads.yaml` manual dificulta o onboarding de novos usuários (Story 8.3 pendente).
- [ ] **Tratamento de Erros Genérico**: Exceções gRPC são repassadas quase sem tratamento, dificultando o "self-healing" da IA.

### 2. Débitos de API e Dados (⚠️ PENDENTE: Revisão do @data-engineer)
- [ ] **Falta de Cache de Metadados**: Cada validação (futura) do Linter pode exigir chamadas extras ao `GoogleAdsFieldService` se não houver cache local.
- [ ] **Serialização de Campos Vazios**: Embora `proto_to_dict` use `always_print_fields_with_no_presence`, o comportamento em mutações (updates) ainda pode omitir campos `False` ou `0` se não for usado FieldMask corretamente em todas as ferramentas.
- [ ] **Mapeamento de Enums Incompleto**: Nem todos os Enums críticos para a Epic 9 (Data Mastery) estão mapeados com sugestões legíveis para a IA.

### 3. Débitos de Interface e UX (⚠️ PENDENTE: Revisão do @ux-design-expert)
- [ ] **Outputs Densos**: Ferramentas de relatório retornam JSONs grandes que podem estourar o contexto da LLM se não houver sumarização ou paginação no servidor.
- [ ] **Feedback do Linter**: A interface de erro atual não fornece "Closest Match" para campos GAQL errados.

### 4. Matriz Preliminar de Priorização
| ID | Débito | Área | Impacto | Esforço | Prioridade |
|----|--------|------|---------|---------|------------|
| DT-1 | Falta de Linter GAQL | Sistema | Crítico | Médio | P0 |
| DT-2 | Hardcoding Geo/Lang | Sistema | Alto | Baixo | P1 |
| DT-3 | Setup Manual (Wizard) | Sistema | Alto | Médio | P1 |
| DT-4 | Cache de Metadados | Dados | Médio | Baixo | P2 |

### 5. Perguntas para Especialistas
- **@data-engineer**: Existe risco de atingir limites de quota da API ao consultar o `GoogleAdsFieldService` frequentemente para o Linter? Devemos persistir o audit.json localmente?
- **@ux-design-expert**: Qual o limite ideal de linhas (`row_count`) que devemos retornar por ferramenta para manter a eficiência do contexto da LLM?

---
*DRAFT gerado por @architect via Brownfield Discovery Workflow.*
