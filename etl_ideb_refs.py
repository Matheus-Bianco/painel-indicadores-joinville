# -*- coding: utf-8 -*-
"""Calcula IDEB de referencia (rede MUNICIPAL de SC e do Brasil) como media
dos IDEBs das escolas (VL_OBSERVADO), mesma metodologia usada no painel para
o valor de rede. Anos: todas as edicoes; etapas AI e AF."""
import sys, io, os, glob, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd, numpy as np

BASE = r"00. Bases de Dados"
fr = next(d for d in os.listdir(BASE) if d.startswith("02.") and "Fluxo" in d)
ideb_sub = next(d for d in os.listdir(os.path.join(BASE, fr)) if "IDEB" in d.upper())
IDEB_DIR = os.path.join(BASE, fr, ideb_sub)

FILES = {
    'AI': 'divulgacao_anos_iniciais_escolas_2023.xlsx',
    'AF': 'divulgacao_anos_finais_escolas_2023.xlsx',
}
ANOS = [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023]

def safe_num(v):
    if v is None or v == '' or v == '-' or str(v).strip() in ('ND', 'nd', 'nan'):
        return np.nan
    try:
        return float(v)
    except (ValueError, TypeError):
        return np.nan

ref = {'sc_municipal': {}, 'brasil_municipal': {}}

for etapa, fname in FILES.items():
    fp = os.path.join(IDEB_DIR, fname)
    print(f"Lendo {fname} ...", flush=True)
    df = pd.read_excel(fp, header=9)
    df = df[df['REDE'].astype(str).str.strip() == 'Municipal'].copy()
    df['_co'] = df['CO_MUNICIPIO'].astype(str).str.replace(r'\.0$', '', regex=True)
    df_sc = df[df['_co'].str[:2] == '42']
    print(f"  Municipal Brasil: {len(df)} | SC: {len(df_sc)}")
    for ano in ANOS:
        col = f"VL_OBSERVADO_{ano}"
        if col not in df.columns:
            continue
        vb = df[col].apply(safe_num).dropna()
        vs = df_sc[col].apply(safe_num).dropna()
        if len(vb):
            ref['brasil_municipal'].setdefault(str(ano), {})[etapa] = round(float(vb.mean()), 2)
        if len(vs):
            ref['sc_municipal'].setdefault(str(ano), {})[etapa] = round(float(vs.mean()), 2)

print(json.dumps(ref, ensure_ascii=False, indent=2))

# Injeta nos JSONs do painel
for fname in ('painel/dados/4_7_ideb.json', 'painel/dados/4_7_ideb_municipal.json'):
    if not os.path.exists(fname):
        continue
    with open(fname, encoding='utf-8') as f:
        j = json.load(f)
    j['referencias'] = ref
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    print('OK ->', fname)
