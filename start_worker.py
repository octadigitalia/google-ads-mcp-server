"""
Inicia o Google Ads Expert Worker como servidor HTTP/SSE na porta 8765.
Rode este script UMA VEZ antes de usar o Claude Code ou Claude Desktop.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
os.environ["MCP_TRANSPORT"] = "sse"
os.environ["MCP_PORT"] = "8765"

print("=" * 50)
print("Google Ads Expert Worker")
print("Iniciando servidor HTTP/SSE na porta 8765...")
print("Mantenha esta janela aberta enquanto usa o Claude.")
print("Pressione Ctrl+C para parar.")
print("=" * 50)

from src.mcp_server.worker import mcp
mcp.settings.port = 8765
mcp.run(transport="sse")
