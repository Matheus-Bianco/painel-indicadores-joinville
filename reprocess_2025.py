import json
import etl_desigualdades
from etl_desigualdades import process_year

print("Loading existing JSON...")
with open(r'painel/dados/4_11_desigualdades.json', encoding='utf-8') as f:
    data = json.load(f)

meta = data.get('metadata', {})
anos_data = data.get('anos', [])

print("Reprocessing 2025...")
# Keep everything except 2025
new_anos = [y for y in anos_data if y['ano'] != 2025]

# Process 2025
y2025 = process_year(2025)
new_anos.append(y2025)

print("Writing JSON...")
with open(r'painel/dados/4_11_desigualdades.json', 'w', encoding='utf-8') as f:
    json.dump({'metadata': meta, 'anos': new_anos}, f, ensure_ascii=False, separators=(',', ':'))

print("Done reprocessing 2025!")
