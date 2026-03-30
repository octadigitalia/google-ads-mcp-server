# PRD: Google Ads Unified AI Skill Product

## 1. Context and Goals
- **Mission**: Replace the complex MCP server (50+ tools) with a single, high-level **AI Skill**.
- **User Experience**: The user does not interact with "tools". They interact with the **Google Ads Expert Skill**.
- **Architecture**: The Python server becomes an internal "Worker Engine" that only serves high-level Super-Skill requests. All atomic operations are handled internally by the Engine, not by the LLM.

## 2. The Unified Product (The Skill)
- **Interface**: A single entry point (The Skill) that understands "Audit", "Scale", "Shield", and "Strategy".
- **Internal Engine**: Python backend executing complex multi-step GAQL logic without exposing it to the prompt.

## 3. High-Level Requirements (Super-Skills)

### Super-Skill: Audit Engine
- Executes Pulse, Waste, Structure, and Action phases in a single backend process.
- Returns a comprehensive Intelligence Report in Markdown.

### Super-Skill: Growth Engine (The Scaler/Sniper)
- Handles budget analysis, keyword expansion, and performance validation in one go.

### Super-Skill: Protection Engine (The Shield)
- Real-time spend monitoring and anomaly detection managed by the Skill's background logic.

## 4. Technical Strategy
- **Deprecation**: Disable all atomic tools (`get_campaign`, `list_ads`, etc.) from being visible to the user.
- **Exposure**: Only expose Super-Skill endpoints (`audit`, `optimize`, `shield`).
- **Distribution**: The product is the `google-ads-expert.skill` package.

## 5. Roadmap
- **Phase 1**: Refactor Python `server.py` to aggregate logic into Super-Skill functions.
- **Phase 2**: Create the AI Skill definition file (The Product).
- **Phase 3**: Update documentation to show "Zero MCP Tool" interaction.

---
*Created by Orion (Master Orchestrator) via Morgan (PM).*
