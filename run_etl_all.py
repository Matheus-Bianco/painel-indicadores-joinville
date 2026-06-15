import etl_desigualdades as etl
import json, os, time

t0 = time.time()
old = json.load(open(os.path.join(etl.OUT_DIR, '4_11_desigualdades.json'), 'r', encoding='utf-8'))

for year in [2022, 2023, 2024]:
    res = etl.process_year(year)
    if res:
        old_anos = [a for a in old['anos'] if a['ano'] != year]
        old_anos.append(res)
        old_anos.sort(key=lambda x: x['ano'])
        old['anos'] = old_anos
        print(f'{year}: escola_lookup entries: {len(res.get("escola_lookup", {}))}')

json.dump(old, open(os.path.join(etl.OUT_DIR, '4_11_desigualdades.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'Done in {time.time()-t0:.0f}s')
