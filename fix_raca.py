import re

path = 'etl_desigualdades.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_code = "if s in ['Branca', 'Parda', 'Preta', 'Amarela']: return s"
new_code = """if s in ['Branca', 'Parda', 'Preta', 'Amarela']: return s
    if 'Branco' in s: return 'Branca'
    if 'Pardo' in s: return 'Parda'
    if 'Preto' in s: return 'Preta'
    if 'Amarelo' in s: return 'Amarela'"""

content = content.replace(old_code, new_code)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated etl_desigualdades.py")
