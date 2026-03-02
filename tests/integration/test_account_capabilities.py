import json
from src.mcp_server.server import get_account_capabilities

customer_id = "3400173105"

print(f"Diagnosing Account Capabilities: {customer_id}")

try:
    res = get_account_capabilities(customer_id)
    print("\nAccount Info:")
    print(f"Name: {res['account']['descriptive_name']}")
    print(f"Currency: {res['account']['currency_code']}")
    print(f"Timezone: {res['account']['time_zone']}")

    print("\nActive Conversion Goals:")
    for goal in res['conversion_goals']:
        print(f"  -> Category: {goal['category']} | Origin: {goal['origin']}")

except Exception as e:
    print(f"\nError: {str(e)}")
