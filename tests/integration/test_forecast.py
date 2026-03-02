import json
import sys
import os

# Adiciona a raiz do projeto ao path para encontrar o modulo 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp_server.server import get_keyword_forecast

customer_id = "3400173105"

print(f"Running Forecast for TecPlaner: {customer_id}")

try:
    keywords = ["gestao google ads", "agencia trafego pago", "consultoria marketing"]
    resultado = get_keyword_forecast(customer_id, keywords)
    print("\nForecast Results:")
    print(json.dumps(resultado, indent=2))
except Exception as e:
    print(f"\nError: {str(e)}")
