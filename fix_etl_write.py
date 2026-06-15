import re

path = 'etl_desigualdades.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = """    with open(out_path, 'w', encoding='utf-8') as f:
        meta = json.load(open(r'painel/dados/4_11_desigualdades.json', encoding='utf-8')).get('metadata', {})
        json.dump({'metadata': meta, 'anos': anos_data}, f, ensure_ascii=False, separators=(',', ':'))"""

new_code = """    meta = {'fonte': 'SAERS/CAED - Microdados da Avaliação do Estado do Rio Grande do Sul', 'etapa_labels': {'2_EF': '2º ano EF', '5_EF': '5º ano EF', '9_EF': '9º ano EF', '3_EM': '3ª série EM'}}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({'metadata': meta, 'anos': anos_data}, f, ensure_ascii=False, separators=(',', ':'))"""
        
content = content.replace(old_code, new_code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated etl_desigualdades.py writing logic!")
