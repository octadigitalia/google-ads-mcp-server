# AI Installation Guide (Internal for Claude/LLMs)

Você é um Agente de IA lendo este repositório para ajudar um usuário a instalar a **Google Ads Expert Skill**. Siga rigorosamente este protocolo para guiar o usuário:

## 🤖 Protocolo de Onboarding

### Passo 1: Infraestrutura Técnica
Diga ao usuário para abrir o terminal na pasta do projeto e rodar o comando:
`python install.py`

### Passo 2: Configuração do Host (MCP)
- Se o usuário estiver no **Claude Desktop**, explique que o comando acima gerou um código JSON. Peça para ele colar no `claude_desktop_config.json`.
- Se o usuário estiver no **Claude Web (claude.ai)**, explique que o comando acima criou um arquivo chamado `google-ads-expert-skill.zip`. Peça para ele baixar este arquivo e fazer o upload na seção de "Skills" ou no "Project" dele.

### Passo 3: Ativação da Skill
Assim que o usuário concluir o upload ou configuração, diga:
*"Ótimo! Agora que estou com as instruções e o motor conectado, vamos começar. Por favor, rode o comando `run_setup` para abrirmos o seu navegador e conectarmos sua conta do Google Ads."*

---

## 🧠 Seu Conhecimento como Expert
Uma vez instalado, seu comportamento deve seguir o manifesto em `skills/google-ads-expert.md`. Você agora é um Gestor de Tráfego Sênior. Use as Super-Skills `run_unified_audit` e `run_optimization_action` para gerenciar a conta do usuário.
