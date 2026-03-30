# AIOS Project Memory - Google Ads MCP

## Account Hierarchy
- **MCC (Manager):** 9440421594
- **Operational Account (Client):** 3400173105 (TecPlaner)
- **Rule:** Never create campaigns directly in the MCC; always target TecPlaner.

## Technical Environment
- **SDK Version:** google-ads v23 (Python)
- **Bidding Strategy:** Preference for `MaximizeConversions` in new smart campaigns to avoid history-based rejection.
- **Compliance:** EU Political Advertising field must be set via Enum in every new campaign.

## Production Roadmap & Architecture
### 1. Token Efficiency Directive
- **Goal:** Minimize LLM context usage by delegating technical lookups (ID hunting) to the Python server.
- **Mechanism:** Tools should accept "Name or ID". If a Name is provided, the tool resolves it internally via GAQL.

### 2. Robust Resolution Strategy (Anti-Frustration)
- **Constraint:** Internal resolution must be deterministic.
- **Policy:** 
    - Exact Match: If one match found, proceed.
    - Ambiguity: If multiple matches found (e.g., "Campaign Leads" matches 3 items), the tool must NOT pick one. It must return a "CLARIFICATION_REQUIRED" error with the list of options for the user/AI to choose.
    - Failure: If no match found, return a clear "RESOURCE_NOT_FOUND" with suggestions.

### 3. Setup Optimization (Zero-Friction Onboarding)
- **Problem:** Developer Token and OAuth secrets are barriers for end-users.
- **Vision:** Implement a `mcp-setup` CLI tool. Favor "Guided Onboarding" with local callback servers for OAuth2 and proactive error repair.

### 4. AI Skills Layer (The Mental Model)
- **Concept:** Companion "Skill Package" (.agent/workflows) teaching the AI orchestrated workflows (Audit, Scale, Shield).
- **Optimization:** Skills emphasize tool combinations and semantic precision.

### 5. Data & Context Mastery (Epic 9)
- **Goal:** Enable full data extraction equivalent to Google Ads UI, optimized for AI.
- **Approach:** Hybrid reporting: Robust GAQL (Linter/Suggestions) + Aggregated Snapshots + Strategy Skills.

## Project Workspace Architecture
- **Lab (Source):** `C:\Users\notebook acer\google-ads-mcp-server` - Full development environment with AIOS metadata and Epics.
- **Dist (Release):** `C:\Users\notebook acer\google-ads-mcp-dist` - Clean distribution, mirrored to GitHub.
- **GitHub Repo:** `https://github.com/octadigitalia/google-ads-mcp-server`

## Deployment Workflow
1. Develop and test in the **Lab**.
2. Run unit tests (`pytest tests/unit/`).
3. Sync essential files to **Dist** (excluding AIOS/temp files).
4. Push to GitHub from the **Dist** folder.

## Current Status
- **Epic 8 (Production Readiness)**: 100% COMPLETED.
- **Epic 9 (Data Mastery)**: 100% COMPLETED.
- **Epic 10 (Skill Transformation)**: 100% COMPLETED. The project has evolved from an MCP Toolset to a **Unified AI Skill Product**.

## The Unified Skill Architecture
- **The Product**: `skills/google-ads-expert.md`. This is the brain that any LLM can use to manage Google Ads.
- **The Engine**: `src/mcp_server/worker.py`. An invisible backend that executes high-level "Super-Skills".
- **Super-Skills**:
    - `run_unified_audit`: Consolidates Health, Waste, and Structure analysis.
    - `run_optimization_action`: Executes complex mutations (budget, negatives, status).
    - `run_setup`: Handles OAuth2 flow and configuration via browser.
- **Deprecation**: All 50+ atomic tools are now private functions in `logic.py`, ensuring a clean and intelligent interface for the user.

## Deployment & Distribution
- **GitHub Ready**: All AIOS internal metadata is ignored via `.gitignore`.
- **Packaging**: The user installs the Skill and runs the Worker as a local background process.

## Verified Test Resources
- **Campaign ID**: customers/3400173105/campaigns/23608928120 (Standard Search)
- **Campaign ID**: customers/3400173105/campaigns/23613592981 (Smart Search)
- **Ad Group ID**: customers/3400173105/adGroups/190668784741
- **User List ID**: customers/3400173105/userLists/6725984187 (GA4 All Users)
