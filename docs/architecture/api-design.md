# API Design & Serialization Standards

**Version:** 1.0.0
**Status:** Approved
**Author:** Aria (@architect)

## Overview
Este documento define os padrões de comunicação entre o servidor MCP e o Google Ads SDK, focando na transformação de objetos Protobuf em JSON compatível com LLMs.

## GAQL Serialization Pattern

### 1. Protobuf to JSON Mapping
O servidor deve converter os objetos de resposta do `GoogleAdsService` seguindo estas regras:
- **Keys:** Manter a nomenclatura oficial do GAQL (ex: `campaign.id`).
- **Enums:** Converter obrigatoriamente para strings legíveis (ex: `ENABLED` em vez de `2`).
- **Numbers:** IDs devem ser tratados como strings para evitar perda de precisão em grandes números.
- **Nulls:** Campos não preenchidos devem ser omitidos ou retornados como `null`.

### 2. Standard Response Structure
Todas as ferramentas de consulta devem retornar o seguinte envelope:

```json
{
  "metadata": {
    "customer_id": "string",
    "row_count": "number",
    "query": "string (optional)",
    "execution_time_ms": "number"
  },
  "results": [
    {
      "resource_name": {
        "field": "value"
      },
      "metrics": {
        "field": "value"
      }
    }
  ]
}
```

## MCC & Multi-Account Support

### 1. Account Context Logic
O servidor deve suportar a distinção entre a conta de autenticação (Manager) e a conta de operação (Client):
- **Header `login-customer-id`:** Sempre preenchido com o ID da MCC (se aplicável) definido no config.
- **Param `customer_id` (Tools):** Define em qual conta a operação será executada. Se omitido, o servidor tentará usar o `login-customer-id` como conta operacional.

### 2. Hierarchy Discovery
Para suportar MCCs, o servidor deve fornecer uma ferramenta de descoberta de contas.

## Mutation & Write Standards

### 1. Surgical Update Pattern
Para garantir a integridade dos dados, todas as operações de mutação devem:
- **Field Masks:** Usar máscaras de campo explícitas para atualizar apenas os campos solicitados.
- **Resource Name Construction:** Construir o `resource_name` programaticamente usando os helpers do SDK (ex: `campaign_path`).
- **Validation Before Mutate:** Validar IDs e valores de Enum localmente antes de enviar a requisição à API.

### 2. Standard Mutation Response
Todas as ferramentas de escrita devem retornar um objeto de confirmação:

```json
{
  "status": "SUCCESS | FAILURE",
  "operation": "string (ex: UPDATE_STATUS)",
  "affected_resource": "string (resource_name)",
  "changes": {
    "field": "new_value"
  },
  "request_id": "string"
}
```

## MCP Tool Definitions

### Tool: `list_accessible_customers`
- **Purpose:** Listar todas as contas de clientes acessíveis através das credenciais atuais.
- **Output:** Lista de IDs de contas, nomes descritivos e status.

### Tool: `search_ads`
- **Purpose:** Execução de qualquer query GAQL válida.
- **Input Syntax:**
  - `query` (Required): String GAQL.
  - `customer_id` (Optional): ID da conta alvo.

### Tool: `set_campaign_status`
- **Purpose:** Alterar o status de veiculação de uma campanha.
- **Parameters:**
  - `customer_id` (Required): ID da conta cliente.
  - `campaign_id` (Required): ID da campanha alvo.
  - `status` (Required): 'ENABLED' ou 'PAUSED'.

## Error Handling Standards
Erros da API devem ser capturados e traduzidos:
- **ERRO 400 (Invalid Query):** Retornar a mensagem de erro específica do campo que falhou no GAQL.
- **ERRO 403 (Permission Denied):** Informar que o Customer ID ou Developer Token não tem acesso ao recurso.
