import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.mcp_server.server import link_audience_to_adgroup

customer_id = "3400173105"
ad_group_id = "190668784741"
user_list_id = "6725984187" # All Users of TecPlaner (ID Real)

print(f"Linking Audience {user_list_id} to AdGroup {ad_group_id}")

try:
    resultado = link_audience_to_adgroup(
        customer_id=customer_id,
        ad_group_id=ad_group_id,
        user_list_id=user_list_id,
        bid_modifier=1.1
    )
    
    print("\nSUCCESS: Audience linked!")
    print(json.dumps(resultado, indent=2))

except Exception as e:
    print(f"\nERROR: {str(e)}")
