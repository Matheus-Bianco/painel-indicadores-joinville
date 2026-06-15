import etl_desigualdades as etl
import json, os, time

t0 = time.time()
old = json.load(open(os.path.join(etl.OUT_DIR, '4_11_desigualdades.json'), 'r', encoding='utf-8'))
res = etl.process_year(2025)
old_anos = [a for a in old['anos'] if a['ano'] != 2025]
old_anos.append(res)
old_anos.sort(key=lambda x: x['ano'])
old['anos'] = old_anos
json.dump(old, open(os.path.join(etl.OUT_DIR, '4_11_desigualdades.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'Done in {time.time()-t0:.0f}s')
print(f'escola_lookup entries: {len(res.get("escola_lookup", {}))}')
sample = list(res.get('escola_lookup', {}).items())[:2]
for k, v in sample:
    print(f'  {k}: {v}')
