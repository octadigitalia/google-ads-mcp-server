import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp_server.server import get_demographic_insights

customer_id = "3400173105"

print(f"Analyzing Demographics: {customer_id}")

try:
    resultado = get_demographic_insights(customer_id, "LAST_30_DAYS")
    
    print("\nAge Groups Ranking:")
    for item in resultado['age_distribution']:
        age = item['ad_group_criterion']['age_range']['type_']
        clicks = int(item['metrics']['clicks'])
        print(f"  -> Range: {age:18} | Clicks: {clicks}")

except Exception as e:
    print(f"\nError: {str(e)}")
