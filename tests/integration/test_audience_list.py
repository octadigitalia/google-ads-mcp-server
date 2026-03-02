import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp_server.server import list_user_lists

customer_id = "3400173105"

print(f"Testing User Lists for: {customer_id}")

try:
    resultado = list_user_lists(customer_id)
    print("
✅ User Lists Found:")
    for ul in resultado['user_lists']:
        print(f"  -> {ul.get('name')} (ID: {ul.get('id')})")

except Exception as e:
    print(f"
❌ Error: {str(e)}")
