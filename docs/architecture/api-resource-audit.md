# Google Ads API Resource Audit (Schema Audit)

**Date**: 2026-03-02
**Auditor**: Orion (@aios-master)
**Scope**: Resources used by Google Ads MCP Server (`campaign`, `ad_group`, `ad_group_ad`).

---

## Executive Summary
This audit maps the metadata of core Google Ads resources to support the implementation of the **Native Field Linter (Story 9.4)**. By querying the `GoogleAdsFieldService`, we've identified all selectable, filterable, and sortable fields.

### Resource Statistics
| Resource | Total Fields | Selectable | Filterable | Sortable |
|----------|--------------|------------|------------|----------|
| Campaign | 100+ | Yes | Yes | Yes |
| Ad Group | 50+ | Yes | Yes | Yes |
| Ad Group Ad | 30+ | Yes | Yes | Yes |

---

## Critical Findings for Linter (Story 9.4)

### 1. Attribute Categories
Fields are categorized as `ATTRIBUTE`, `METRIC`, or `SEGMENT`.
- **Constraint**: Metrics and segments often require specific `SELECT` fields or `WHERE` clauses to be valid.
- **Linter Rule**: The linter must verify if the requested field is `selectable: true` for the primary resource in the `FROM` clause.

### 2. Data Type Mapping
The API uses specific data types (ENUM, INT64, STRING, BOOLEAN, DOUBLE, RESOURCE_NAME).
- **Linter Rule**: When generating `WHERE` clauses, the linter must ensure values match the `dataType`.

### 3. Selection Constraints
Some fields are `selectable: true` but not `filterable: true`.
- **Linter Rule**: Validate that fields in the `WHERE` clause are marked as `filterable`.

---

## API Limits & Performance
- **Query Complexity**: Large queries with many segments can increase latency.
- **Reporting Limits**: Up to 10,000 rows per page (default in search). Stream is preferred for large datasets.

---

## Action Items for Story 9.4
1. [ ] Create a local cache or registry of `selectable` fields to avoid redundant `GoogleAdsFieldService` calls.
2. [ ] Implement a validation function that checks `field_name` against the audited metadata.
3. [ ] Map `ENUM` values for common fields (Status, AdvertisingChannelType) to provide better error suggestions.

---
## Audit Artifacts
- `docs/architecture/api-audit-campaign.json`
- `docs/architecture/api-audit-ad-group.json`
- `docs/architecture/api-audit-ad-group-ad.json`

---
*Audit report generated as part of Brownfield Discovery workflow.*
