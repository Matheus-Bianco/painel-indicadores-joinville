# -*- coding: utf-8 -*-
"""
ATUALIZAR TABELA MÃE — Adiciona novas abas com dados de Série, Turno e Ed. Profissional
ao arquivo Dados_Municipios_RS_Painel_v2.xlsx
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import json, os, time

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
OUT_DIR = os.path.join(BASE, "painel", "dados")
XLSX_PATH = os.path.join(BASE, "Dados_Municipios_RS_Painel_v2.xlsx")

REDES = {
    'estadual': '4_1_acesso_estadual.json',
    'municipal': '4_1_acesso_municipal.json',
    'federal': '4_1_acesso_federal.json',
    'privada': '4_1_acesso_privada.json',
    'filantropica': '4_1_acesso_filantropica.json',
    'todas': '4_1_acesso_todas.json',
}

def safe_get(d, *keys, default=0):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d


def build_serie_temporal_df(data, rede_label):
    """Constrói DataFrame de série temporal com os novos indicadores."""
    st = data.get('serie_temporal', {})
    anos = sorted(st.keys())
    rows = []
    for ano in anos:
        s = st[ano]
        row = {
            'Ano': int(ano),
            'Rede': rede_label,
            'Mat. Total': s.get('mat_total', 0),
            'Mat. Profissional': s.get('mat_prof', 0),
            'Mat. Técnico': s.get('mat_prof_tec', 0),
            'Médio Integrado': s.get('mat_med_integrado', 0),
            'EJA Técnico': s.get('mat_eja_med_tec', 0),
        }
        # Série (só 2025)
        ps = s.get('por_serie', {})
        for col, label in [
            ('QT_MAT_FUND_AI_1', '1º Ano'), ('QT_MAT_FUND_AI_2', '2º Ano'),
            ('QT_MAT_FUND_AI_3', '3º Ano'), ('QT_MAT_FUND_AI_4', '4º Ano'),
            ('QT_MAT_FUND_AI_5', '5º Ano'),
            ('QT_MAT_FUND_AF_6', '6º Ano'), ('QT_MAT_FUND_AF_7', '7º Ano'),
            ('QT_MAT_FUND_AF_8', '8º Ano'), ('QT_MAT_FUND_AF_9', '9º Ano'),
            ('QT_MAT_MED_PROP_1', '1ª Série EM'), ('QT_MAT_MED_PROP_2', '2ª Série EM'),
            ('QT_MAT_MED_PROP_3', '3ª Série EM'), ('QT_MAT_MED_PROP_4', '4ª Série EM'),
        ]:
            row[label] = ps.get(col, '')
        # Turno (só 2025)
        pt = s.get('por_turno', {})
        for col, label in [
            ('QT_MAT_BAS_D', 'Total Diurno'), ('QT_MAT_BAS_N', 'Total Noturno'),
            ('QT_MAT_FUND_D', 'Fund. Diurno'), ('QT_MAT_FUND_N', 'Fund. Noturno'),
            ('QT_MAT_MED_D', 'Médio Diurno'), ('QT_MAT_MED_N', 'Médio Noturno'),
            ('QT_MAT_PROF_D', 'Prof. Diurno'), ('QT_MAT_PROF_N', 'Prof. Noturno'),
            ('QT_MAT_EJA_D', 'EJA Diurno'), ('QT_MAT_EJA_N', 'EJA Noturno'),
        ]:
            row[label] = pt.get(col, '')
        # Detalhes Prof (só 2025)
        dp = s.get('detalhes_prof', {})
        for col, label in [
            ('QT_MAT_PROF_TEC_CONC', 'Técnico Concomitante'),
            ('QT_MAT_PROF_TEC_SUBS', 'Técnico Subsequente'),
            ('QT_MAT_MED_IFTP_CT', 'Médio Integrado CT'),
        ]:
            row[label] = dp.get(col, '')
        rows.append(row)
    return pd.DataFrame(rows)


def build_municipio_df(data, rede_label, ano='2025'):
    """Constrói DataFrame por município com os novos indicadores."""
    pm = data.get('por_municipio', {}).get(ano, {})
    lookup = data.get('lookup_municipios', {})
    rows = []
    for cod, m in pm.items():
        row = {
            'Código IBGE': int(cod),
            'Município': lookup.get(cod, cod),
            'Rede': rede_label,
            'Mat. Total': m.get('mat_total', 0),
            'Mat. Profissional': m.get('mat_prof', 0),
            'Mat. Técnico': m.get('mat_prof_tec', 0),
        }
        # Série
        ps = m.get('por_serie', {})
        for col, label in [
            ('QT_MAT_FUND_AI_1', '1º Ano'), ('QT_MAT_FUND_AI_2', '2º Ano'),
            ('QT_MAT_FUND_AI_3', '3º Ano'), ('QT_MAT_FUND_AI_4', '4º Ano'),
            ('QT_MAT_FUND_AI_5', '5º Ano'),
            ('QT_MAT_FUND_AF_6', '6º Ano'), ('QT_MAT_FUND_AF_7', '7º Ano'),
            ('QT_MAT_FUND_AF_8', '8º Ano'), ('QT_MAT_FUND_AF_9', '9º Ano'),
            ('QT_MAT_MED_PROP_1', '1ª Série EM'), ('QT_MAT_MED_PROP_2', '2ª Série EM'),
            ('QT_MAT_MED_PROP_3', '3ª Série EM'), ('QT_MAT_MED_PROP_4', '4ª Série EM'),
        ]:
            row[label] = ps.get(col, '')
        # Turno
        pt = m.get('por_turno', {})
        for col, label in [
            ('QT_MAT_BAS_D', 'Total Diurno'), ('QT_MAT_BAS_N', 'Total Noturno'),
            ('QT_MAT_FUND_D', 'Fund. Diurno'), ('QT_MAT_FUND_N', 'Fund. Noturno'),
            ('QT_MAT_MED_D', 'Médio Diurno'), ('QT_MAT_MED_N', 'Médio Noturno'),
            ('QT_MAT_PROF_D', 'Prof. Diurno'), ('QT_MAT_PROF_N', 'Prof. Noturno'),
            ('QT_MAT_EJA_D', 'EJA Diurno'), ('QT_MAT_EJA_N', 'EJA Noturno'),
        ]:
            row[label] = pt.get(col, '')
        rows.append(row)
    return pd.DataFrame(rows).sort_values('Mat. Total', ascending=False)


if __name__ == '__main__':
    print("=" * 70)
    print("ATUALIZAR TABELA MÃE — Novos Indicadores")
    print("=" * 70)
    t0 = time.time()

    # Carregar Excel existente
    print(f"\nCarregando {os.path.basename(XLSX_PATH)}...")
    existing = pd.read_excel(XLSX_PATH, sheet_name=None)
    print(f"  {len(existing)} abas existentes")

    new_sheets = {}

    for rede_key, json_file in REDES.items():
        json_path = os.path.join(OUT_DIR, json_file)
        if not os.path.exists(json_path):
            print(f"  [SKIP] {json_file}")
            continue

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        rede_label = rede_key.capitalize()
        print(f"\n  Rede: {rede_label}")

        # Série Temporal (todos os anos, com novos campos)
        df_st = build_serie_temporal_df(data, rede_label)
        sheet_name = f"Prof+Serie {rede_label[:5]}"
        new_sheets[sheet_name] = df_st
        print(f"    {sheet_name}: {len(df_st)} anos")

        # Por Município (2025)
        df_mun = build_municipio_df(data, rede_label, '2025')
        sheet_name_mun = f"Serie Mun {rede_label[:5]}"
        new_sheets[sheet_name_mun] = df_mun
        print(f"    {sheet_name_mun}: {len(df_mun)} municípios")

    # Gravar: preservar abas existentes + adicionar novas
    print(f"\nGravando {os.path.basename(XLSX_PATH)}...")
    with pd.ExcelWriter(XLSX_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        for sheet_name, df in new_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  Gravado: {sheet_name}")

    print(f"\nTempo total: {time.time()-t0:.1f}s")
    print("Concluído!")
