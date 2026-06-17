# -*- coding: utf-8 -*-
"""Extrai medias SAEB da rede MUNICIPAL para Santa Catarina e Brasil
(referencias para o painel de Joinville). Anos: 2017, 2019, 2021 (TS_UF/TS_BRASIL.xlsx)
e 2023 (Resultados_Saeb .xlsb)."""
import pandas as pd, glob, json, os

BASE = r'00. Bases de Dados/03. Desempenho IDEB.SAEB/01. SAEB'
ANOS_XLSX = ['2017', '2019', '2021']

def num(v):
    x = pd.to_numeric(v, errors='coerce')
    return round(float(x), 1) if pd.notna(x) else None

def row_medias(row):
    return {
        '5EF': {'media_lp': num(row.get('MEDIA_5_LP')), 'media_mt': num(row.get('MEDIA_5_MT'))},
        '9EF': {'media_lp': num(row.get('MEDIA_9_LP')), 'media_mt': num(row.get('MEDIA_9_MT'))},
    }

def pick(df):
    """Filtra Municipal / Total / Total."""
    d = df.copy()
    if 'DEPENDENCIA_ADM' in d.columns:
        d = d[d['DEPENDENCIA_ADM'].astype(str).str.strip() == 'Municipal']
    if 'LOCALIZACAO' in d.columns:
        d = d[d['LOCALIZACAO'].astype(str).str.strip() == 'Total']
    if 'CAPITAL' in d.columns:
        d = d[d['CAPITAL'].astype(str).str.strip() == 'Total']
    return d

refs = {}  # ano -> {sc_municipal:{...}, brasil_municipal:{...}}

for ano in ANOS_XLSX:
    refs[ano] = {}
    # Brasil
    fb = glob.glob(f'{BASE}/microdados_saeb_{ano}/PLANILHAS DE RESULTADOS/TS_BRASIL.xlsx')
    if fb:
        db = pick(pd.read_excel(fb[0]))
        if len(db):
            refs[ano]['brasil_municipal'] = row_medias(db.iloc[0])
    # SC (UF)
    fu = glob.glob(f'{BASE}/microdados_saeb_{ano}/PLANILHAS DE RESULTADOS/TS_UF.xlsx')
    if fu:
        du = pd.read_excel(fu[0])
        # normaliza nome UF (encoding)
        du = du[du['NO_UF'].astype(str).str.contains('Catarina', case=False, na=False)]
        du = pick(du)
        if len(du):
            refs[ano]['sc_municipal'] = row_medias(du.iloc[0])
    print(ano, refs[ano])

# 2023 via xlsb
fx = glob.glob(f'{BASE}/microdados_saeb_2023/DADOS/Resultados_Saeb_2023*.xlsb')
if fx:
    xl = pd.ExcelFile(fx[0], engine='pyxlsb')
    print('SHEETS 2023:', xl.sheet_names)
    refs['2023'] = {}
    for sh in xl.sheet_names:
        low = sh.lower()
        df = pd.read_excel(fx[0], sheet_name=sh, engine='pyxlsb')
        cols = set(df.columns)
        # Brasil: sheet com agregado nacional, sem CO_MUNICIPIO/NO_UF especifico
        if 'brasil' in low and {'MEDIA_5_LP'}.issubset(cols):
            d = pick(df)
            if len(d):
                refs['2023']['brasil_municipal'] = row_medias(d.iloc[0])
        if ('estado' in low or 'uf' in low) and 'NO_UF' in cols:
            d = df[df['NO_UF'].astype(str).str.contains('Catarina', case=False, na=False)]
            d = pick(d)
            if len(d):
                refs['2023']['sc_municipal'] = row_medias(d.iloc[0])
    print('2023', refs['2023'])

print('\n=== JSON REFS ===')
print(json.dumps(refs, ensure_ascii=False, indent=2))

# Reestrutura scope -> ano -> etapa e injeta nos JSONs do painel
ref_out = {'sc_municipal': {}, 'brasil_municipal': {}}
for ano, d in refs.items():
    for scope in ('sc_municipal', 'brasil_municipal'):
        if scope in d:
            ref_out[scope][ano] = d[scope]
for fname in ('painel/dados/4_6_saeb.json', 'painel/dados/4_6_saeb_municipal.json'):
    if not os.path.exists(fname):
        continue
    with open(fname, encoding='utf-8') as f:
        j = json.load(f)
    j['referencias'] = ref_out
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    print('OK ->', fname)
