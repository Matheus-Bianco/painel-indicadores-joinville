import os
import json

folder = r'painel\dados'

def fix_text(text):
    if not isinstance(text, str):
        return text
    try:
        # If it was double-encoded, encoding as latin1 and decoding as utf-8 fixes it
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text

def fix_obj(obj):
    if isinstance(obj, dict):
        return {k: fix_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fix_obj(x) for x in obj]
    elif isinstance(obj, str):
        return fix_text(obj)
    return obj

for filename in os.listdir(folder):
    if filename.endswith('.json'):
        filepath = os.path.join(folder, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'Ã' in content or 'Â' in content:
            print(f"Fixing {filename}...")
            data = json.loads(content)
            fixed_data = fix_obj(data)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, separators=(',', ':'))

print("Done.")
