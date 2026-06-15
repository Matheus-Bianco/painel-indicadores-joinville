import re
import os

path = 'etl_desigualdades.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = "json.dump({'anos': anos_data}, f, ensure_ascii=False, separators=(',', ':'))"
new_code = "meta = json.load(open(r'painel/dados/4_11_desigualdades.json', encoding='utf-8')).get('metadata', {})\n        json.dump({'metadata': meta, 'anos': anos_data}, f, ensure_ascii=False, separators=(',', ':'))"

content = content.replace(old_code, new_code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed ETL script.')
