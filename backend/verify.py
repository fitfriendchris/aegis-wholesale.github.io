import json, urllib.request

url = "http://localhost:5001/api/pipeline/filter?arv_min=350000&arv_max=450000"
with urllib.request.urlopen(url) as r:
    d = json.load(r)

print(f"Found {len(d)} deals ~$400K ARV")
print("Top 5 by ARV:")
sorted_deals = sorted(d, key=lambda x: x["arv"], reverse=True)
for i, x in enumerate(sorted_deals[:5]):
    print(f"  {i+1}. {x['address'][:45]} - ARV: ${x['arv']:,} | Fee: ${x['assignment_fee']:,} | {x['status']}")

print()
print("Status breakdown:")
from collections import Counter
c = Counter(x["status"] for x in d)
for k, v in c.items():
    print(f"  {k}: {v}")
print(f"Total assignment fees: ${sum(x['assignment_fee'] for x in d):,}")
