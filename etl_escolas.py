# -*- coding: utf-8 -*-
"""
ETL Escolas — Visão por Escola (Rede Municipal Joinville/SC)

Reescrita enxuta: base Censo 2025 + coordenadas INEP + indicadores disponíveis por escola.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import json, os, re, glob, time, shutil

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
BASES_DADOS = os.path.join(BASE, "00. Bases de Dados")
PAINEL_DIR = os.path.join(BASE, "painel", "dados")
MICRO_DIR = os.path.join(BASES_DADOS, "01. Acesso e Matrículas (Censo Escolar_2010_2025)", "01. extrações_2010_2025")
COORDS_FILE = os.path.join(BASE, "..", "..", "0000. Bases", "02. Coordenadas", "Escolas_INEP_Coordenadas.xlsx")

CO_MUN_JOINVILLE = 4209102
CO_UF_SC = 42

LOC_MAP = {1: "Urbana", 2: "Rural", "1": "Urbana", "2": "Rural"}


def safe_float(val):
    if val is None or val == '' or val == '-' or val == 'ND':
        return None
    try:
        v = float(val)
        return None if np.isnan(v) else round(v, 2)
    except (ValueError, TypeError):
        return None


def si(v):
    return 0 if pd.isna(v) else int(v)


def parse_coord(s):
    """Parse 'lng, lat' string -> (lat, lng) floats."""
    if pd.isna(s) or not str(s).strip():
        return None, None
    parts = [p.strip() for p in str(s).split(',')]
    if len(parts) != 2:
        return None, None
    try:
        lng, lat = float(parts[0]), float(parts[1])
        if abs(lat) > 90 or abs(lng) > 180:
            return None, None
        return round(lat, 6), round(lng, 6)
    except ValueError:
        return None, None


def load_coords():
    """Carrega coordenadas por codigo INEP."""
    if not os.path.exists(COORDS_FILE):
        print(f"  [AVISO] Coordenadas nao encontradas: {COORDS_FILE}")
        return {}
    df = pd.read_excel(COORDS_FILE)
    result = {}
    for _, row in df.iterrows():
        inep = str(int(row['INEP']))
        lat, lng = parse_coord(row.get('Coordenada'))
        if lat is not None:
            result[inep] = {'lat': lat, 'lng': lng, 'fonte': 'SED_Joinville'}
    print(f"  Coordenadas SED: {len(result)} escolas")
    return result


def load_base_schools():
    """Escolas da rede MUNICIPAL de Joinville (Censo Tabela_Escola 2025)."""
    fpath = os.path.join(MICRO_DIR, "Tabela_Escola_2025.csv")
    print(f"  Censo: lendo {os.path.basename(fpath)}...")
    use = [
        "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO",
        "TP_DEPENDENCIA", "TP_SITUACAO_FUNCIONAMENTO", "TP_LOCALIZACAO",
        "LATITUDE", "LONGITUDE", "QT_SALAS_UTILIZADAS",
    ]
    h = pd.read_csv(fpath, sep=";", encoding="latin-1", nrows=0)
    cols = [c for c in use if c in h.columns]
    df = pd.read_csv(fpath, sep=";", encoding="latin-1", usecols=cols)
    df = df[
        (df["CO_MUNICIPIO"] == CO_MUN_JOINVILLE)
        & (df["TP_DEPENDENCIA"] == 3)
        & (df["TP_SITUACAO_FUNCIONAMENTO"] == 1)
    ].copy()
    df["INEP"] = df["CO_ENTIDADE"].astype(int).astype(str)
    print(f"  Censo: {len(df)} escolas municipais Joinville")
    return df


def _muni_inep_set(df_base):
    return set(df_base["INEP"].tolist())


def load_ideb(muni_inep):
    ideb_dir = os.path.join(BASES_DADOS, "02. Fluxo e Rendimento (Inep_2010_2024_Rendimento_TDI)", "02. IDEB")
    etapas = {
        'AI': 'divulgacao_anos_iniciais_escolas_2023.xlsx',
        'AF': 'divulgacao_anos_finais_escolas_2023.xlsx',
        'EM': 'divulgacao_ensino_medio_escolas_2023.xlsx',
    }
    result = {}
    for etapa, fname in etapas.items():
        fpath = os.path.join(ideb_dir, fname)
        if not os.path.exists(fpath):
            continue
        print(f"  IDEB {etapa}: {fname}...")
        df = pd.read_excel(fpath, header=9)
        df = df[
            (df['CO_MUNICIPIO'].astype(str).str[:7] == str(CO_MUN_JOINVILLE))
            & (df['REDE'] == 'Municipal')
        ]
        for _, row in df.iterrows():
            eid = str(int(row['ID_ESCOLA']))
            if eid not in muni_inep:
                continue
            obs = {y: safe_float(row.get(f'VL_OBSERVADO_{y}')) for y in [2017, 2019, 2021, 2023]}
            if obs[2023] is None:
                continue
            if eid not in result:
                result[eid] = {'ideb_hist': {}}
            result[eid][f'ideb_{etapa.lower()}'] = obs[2023]
            hist_key = f'ideb_{etapa.lower()}'
            result[eid]['ideb_hist'][hist_key] = {str(y): v for y, v in obs.items() if v is not None}
    print(f"    -> {len(result)} escolas com IDEB")
    return result


def load_inse(muni_inep):
    inse_dir = os.path.join(BASES_DADOS, "04. Desigualdades Educacionais (INSE)")
    fpath = os.path.join(inse_dir, "INSE_2023_escolas.xlsx")
    if not os.path.exists(fpath):
        return {}
    print(f"  INSE: {os.path.basename(fpath)}...")
    df = pd.read_excel(fpath)
    df = df[df['CO_MUNICIPIO'].astype(str).str[:7] == str(CO_MUN_JOINVILLE)]
    if 'TP_TIPO_REDE' in df.columns:
        df = df[df['TP_TIPO_REDE'] == 3]
    result = {}
    for _, row in df.iterrows():
        eid = str(int(row['ID_ESCOLA']))
        if eid not in muni_inep:
            continue
        media = safe_float(row.get('MEDIA_INSE'))
        if media is not None:
            result[eid] = {
                'inse_media': media,
                'inse_nivel': str(row.get('INSE_CLASSIFICACAO', '')),
            }
    print(f"    -> {len(result)} escolas com INSE")
    return result


def load_icg(muni_inep):
    icg_dir = next((os.path.join(BASES_DADOS, d) for d in os.listdir(BASES_DADOS) if 'Complex' in d), None)
    if not icg_dir:
        return {}
    files = sorted(glob.glob(os.path.join(icg_dir, 'ICG_ESCOLAS_*.xlsx')), reverse=True)
    if not files:
        return {}
    fpath = files[0]
    print(f"  ICG: {os.path.basename(fpath)}...")
    df = pd.read_excel(fpath, header=6)
    df.columns = ['Ano', 'Regiao', 'UF', 'Cod_Mun', 'Nome_Mun',
                  'Cod_Escola', 'Nome_Escola', 'Loc', 'Dep', 'Nivel']
    df['Cod_Mun'] = df['Cod_Mun'].astype(str).str[:7]
    df = df[(df['Cod_Mun'] == str(CO_MUN_JOINVILLE)) & (df['Dep'] == 'Municipal')]
    result = {}
    for _, row in df.iterrows():
        try:
            eid = str(int(row['Cod_Escola']))
        except (ValueError, TypeError):
            continue
        if eid not in muni_inep:
            continue
        m = re.search(r'(\d)', str(row['Nivel']))
        if m:
            result[eid] = {'icg_nivel': int(m.group(1))}
    print(f"    -> {len(result)} escolas com ICG")
    return result


def load_tdi(muni_inep):
    tdi_dir = os.path.join(BASES_DADOS, "02. Fluxo e Rendimento (Inep_2010_2024_Rendimento_TDI)", "01. Rendimento e TDI")
    files = sorted(glob.glob(os.path.join(tdi_dir, 'TDI_ESCOLAS_*.xlsx')), reverse=True)
    files = [f for f in files if any(str(y) in os.path.basename(f) for y in range(2021, 2027))]
    result = {}
    for fpath in files[:3]:
        year = re.search(r'(\d{4})', os.path.basename(fpath)).group(1)
        print(f"  TDI: {os.path.basename(fpath)}...")
        df = pd.read_excel(fpath, header=8)
        if 'SG_UF' not in df.columns:
            continue
        df = df[
            (df['SG_UF'].astype(str).str.strip() == 'SC')
            & (df['NO_DEPENDENCIA'].astype(str).str.strip() == 'Municipal')
        ]
        df['cod_mun'] = df['CO_MUNICIPIO'].apply(lambda x: str(int(x))[:7] if pd.notna(x) else None)
        df = df[df['cod_mun'] == str(CO_MUN_JOINVILLE)]
        for _, row in df.iterrows():
            try:
                eid = str(int(row['CO_ENTIDADE']))
            except (ValueError, TypeError):
                continue
            if eid not in muni_inep:
                continue
            if eid not in result:
                result[eid] = {'tdi_hist': {}}
            entry = {}
            for col, key in [('FUN_CAT_0', 'tdi_fund'), ('FUN_AI_CAT_0', 'tdi_ai'),
                             ('FUN_AF_CAT_0', 'tdi_af'), ('MED_CAT_0', 'tdi_med')]:
                if col in df.columns:
                    v = safe_float(row[col])
                    if v is not None:
                        entry[key] = v
            if entry:
                if 'tdi_fund' not in result[eid]:
                    result[eid].update(entry)
                result[eid]['tdi_hist'][year] = entry
    print(f"    -> {len(result)} escolas com TDI")
    return result


def load_infra(muni_inep):
    fpath = os.path.join(MICRO_DIR, "Tabela_Escola_2025.csv")
    KEY_INFRA = [
        "IN_INTERNET", "IN_BANDA_LARGA", "IN_COMPUTADOR",
        "IN_LABORATORIO_INFORMATICA", "IN_BIBLIOTECA", "IN_BIBLIOTECA_SALA_LEITURA",
        "IN_LABORATORIO_CIENCIAS", "IN_QUADRA_ESPORTES", "IN_QUADRA_ESPORTES_COBERTA",
        "IN_SALA_ATENDIMENTO_ESPECIAL", "IN_REFEITORIO",
        "IN_ACESSIBILIDADE_RAMPAS", "IN_BANHEIRO_PNE",
        "IN_AGUA_POTAVEL", "IN_ALIMENTACAO",
        "IN_SALA_DIRETORIA", "IN_SALA_PROFESSOR",
    ]
    LABEL_MAP = {
        "IN_INTERNET": "internet", "IN_BANDA_LARGA": "banda_larga", "IN_COMPUTADOR": "computador",
        "IN_LABORATORIO_INFORMATICA": "lab_info", "IN_BIBLIOTECA": "biblioteca",
        "IN_BIBLIOTECA_SALA_LEITURA": "bib_sala_leit", "IN_LABORATORIO_CIENCIAS": "lab_ciencias",
        "IN_QUADRA_ESPORTES": "quadra", "IN_QUADRA_ESPORTES_COBERTA": "quadra_coberta",
        "IN_SALA_ATENDIMENTO_ESPECIAL": "sala_aee", "IN_REFEITORIO": "refeitorio",
        "IN_ACESSIBILIDADE_RAMPAS": "rampas", "IN_BANHEIRO_PNE": "banheiro_pne",
        "IN_AGUA_POTAVEL": "agua_potavel", "IN_ALIMENTACAO": "alimentacao",
        "IN_SALA_DIRETORIA": "sala_diretoria", "IN_SALA_PROFESSOR": "sala_professor",
    }
    print(f"  Infra: Tabela_Escola_2025...")
    h = pd.read_csv(fpath, sep=";", encoding="latin-1", nrows=0)
    avail = [c for c in KEY_INFRA if c in h.columns]
    cols = ["CO_ENTIDADE"] + avail
    if "QT_SALAS_UTILIZA_CLIMATIZADAS" in h.columns:
        cols.append("QT_SALAS_UTILIZA_CLIMATIZADAS")
    df = pd.read_csv(fpath, sep=";", encoding="latin-1", usecols=cols)
    result = {}
    for _, row in df.iterrows():
        eid = str(int(row["CO_ENTIDADE"]))
        if eid not in muni_inep:
            continue
        entry = {}
        has_items = total_items = 0
        for col in avail:
            key = LABEL_MAP.get(col, col.lower())
            val = si(row.get(col, 0))
            entry[key] = val
            total_items += 1
            has_items += val
        entry['infra_score'] = round(has_items / total_items * 100, 0) if total_items else 0
        if "QT_SALAS_UTILIZA_CLIMATIZADAS" in cols:
            entry['salas_clim'] = si(row.get("QT_SALAS_UTILIZA_CLIMATIZADAS", 0))
        result[eid] = entry
    print(f"    -> {len(result)} escolas com infra")
    return result


def load_matriculas(muni_inep):
    f_mat = os.path.join(MICRO_DIR, "Tabela_Matricula_2025.csv")
    if not os.path.exists(f_mat):
        return {}
    print(f"  Matriculas: Tabela_Matricula_2025...")
    cols = ["CO_ENTIDADE", "QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_FUND", "QT_MAT_FUND_AI",
            "QT_MAT_FUND_AF", "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_ESP", "QT_MAT_BAS_N"]
    h = pd.read_csv(f_mat, sep=";", encoding="latin-1", nrows=0)
    use = [c for c in cols if c in h.columns]
    df = pd.read_csv(f_mat, sep=";", encoding="latin-1", usecols=use)
    result = {}
    for _, row in df.iterrows():
        eid = str(int(row["CO_ENTIDADE"]))
        if eid not in muni_inep:
            continue
        result[eid] = {
            'mat_total': si(row.get("QT_MAT_BAS", 0)),
            'mat_infantil': si(row.get("QT_MAT_INF", 0)),
            'mat_fund': si(row.get("QT_MAT_FUND", 0)),
            'mat_fund_ai': si(row.get("QT_MAT_FUND_AI", 0)),
            'mat_fund_af': si(row.get("QT_MAT_FUND_AF", 0)),
            'mat_medio': si(row.get("QT_MAT_MED", 0)),
            'mat_eja': si(row.get("QT_MAT_EJA", 0)),
            'mat_especial': si(row.get("QT_MAT_ESP", 0)),
            'mat_noturno': si(row.get("QT_MAT_BAS_N", 0)),
        }
    print(f"    -> {len(result)} escolas com matriculas")
    return result


def load_docentes(muni_inep):
    f_doc = os.path.join(MICRO_DIR, "Tabela_Docente_2025.csv")
    if not os.path.exists(f_doc):
        return {}
    print(f"  Docentes: Tabela_Docente_2025...")
    cols = ["CO_ENTIDADE", "QT_DOC_BAS", "QT_DOC_FUND_AI", "QT_DOC_FUND_AF",
            "QT_DOC_MED", "QT_DOC_EJA", "QT_DOC_BAS_FEM",
            "QT_DOC_BAS_ESCO_SUP_GRAD", "QT_DOC_BAS_ESCO_SUP_GRAD_LICEN",
            "QT_DOC_BAS_VINCULO_CONCUR", "QT_DOC_BAS_VINCULO_CONTRA"]
    h = pd.read_csv(f_doc, sep=";", encoding="latin-1", nrows=0)
    use = [c for c in cols if c in h.columns]
    df = pd.read_csv(f_doc, sep=";", encoding="latin-1", usecols=use)
    result = {}
    for _, row in df.iterrows():
        eid = str(int(row["CO_ENTIDADE"]))
        if eid not in muni_inep:
            continue
        result[eid] = {
            'doc_total': si(row.get("QT_DOC_BAS", 0)),
            'doc_fund_ai': si(row.get("QT_DOC_FUND_AI", 0)),
            'doc_fund_af': si(row.get("QT_DOC_FUND_AF", 0)),
            'doc_medio': si(row.get("QT_DOC_MED", 0)),
            'doc_eja': si(row.get("QT_DOC_EJA", 0)),
            'doc_fem': si(row.get("QT_DOC_BAS_FEM", 0)),
            'doc_sup': si(row.get("QT_DOC_BAS_ESCO_SUP_GRAD", 0)),
            'doc_licen': si(row.get("QT_DOC_BAS_ESCO_SUP_GRAD_LICEN", 0)),
            'doc_concur': si(row.get("QT_DOC_BAS_VINCULO_CONCUR", 0)),
            'doc_contrat': si(row.get("QT_DOC_BAS_VINCULO_CONTRA", 0)),
        }
    print(f"    -> {len(result)} escolas com docentes")
    return result


def load_censo_hist(muni_inep):
    result = {}
    for year in range(2021, 2025):
        matches = glob.glob(os.path.join(MICRO_DIR, f"microdados_ed_basica_{year}.*"))
        if not matches:
            continue
        fpath = matches[0]
        h = pd.read_csv(fpath, sep=";", encoding="latin-1", nrows=0)
        use = [c for c in ["CO_MUNICIPIO", "CO_ENTIDADE", "TP_DEPENDENCIA",
                           "TP_SITUACAO_FUNCIONAMENTO", "QT_MAT_BAS", "QT_DOC_BAS"] if c in h.columns]
        df = pd.read_csv(fpath, sep=";", encoding="latin-1", usecols=use)
        df = df[
            (df["CO_MUNICIPIO"] == CO_MUN_JOINVILLE)
            & (df["TP_DEPENDENCIA"] == 3)
            & (df["TP_SITUACAO_FUNCIONAMENTO"] == 1)
        ]
        for _, row in df.iterrows():
            eid = str(int(row["CO_ENTIDADE"]))
            if eid not in muni_inep:
                continue
            if eid not in result:
                result[eid] = {'mat_hist': {}, 'doc_hist': {}}
            if "QT_MAT_BAS" in row and pd.notna(row["QT_MAT_BAS"]):
                result[eid]['mat_hist'][str(year)] = si(row["QT_MAT_BAS"])
            if "QT_DOC_BAS" in row and pd.notna(row["QT_DOC_BAS"]):
                result[eid]['doc_hist'][str(year)] = si(row["QT_DOC_BAS"])
    print(f"  Historico Censo: {len(result)} escolas (2021-2024)")
    return result


def load_fluxo_json(muni_inep):
    fpath = os.path.join(PAINEL_DIR, "4_3_fluxo_municipal.json")
    if not os.path.exists(fpath):
        return {}
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for rec in data.get("por_escola_2024", []):
        eid = str(rec.get("cod_escola", "")).split(".")[0]
        if not eid or eid not in muni_inep:
            continue
        result[eid] = {k: rec[k] for k in [
            'aprov_fund', 'aprov_fund_ai', 'aprov_fund_af', 'aprov_med',
            'reprov_fund', 'reprov_fund_ai', 'reprov_fund_af', 'reprov_med',
            'aband_fund', 'aband_fund_ai', 'aband_fund_af', 'aband_med',
        ] if k in rec}
    print(f"  Fluxo 2024: {len(result)} escolas")
    return result


def load_afd_json(muni_inep):
    fpath = os.path.join(PAINEL_DIR, "4_9_afd_municipal.json")
    if not os.path.exists(fpath):
        return {}
    with open(fpath, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for rec in data.get("por_escola_2025", []):
        eid = str(rec.get("cod_escola", ""))
        if not eid or eid not in muni_inep:
            continue
        entry = {}
        for etapa in ['ed_inf', 'fund_total', 'fund_ai', 'fund_af', 'medio', 'eja_fund', 'eja_medio']:
            if etapa in rec:
                entry[f'afd_{etapa}'] = rec[etapa]
        if entry:
            result[eid] = entry
    print(f"  AFD 2025: {len(result)} escolas")
    return result


def main():
    t0 = time.time()
    print("=" * 60)
    print("ETL ESCOLAS — Rede Municipal Joinville/SC")
    print("=" * 60)

    df = load_base_schools()
    muni_inep = _muni_inep_set(df)
    coords = load_coords()

    print("\n-- Indicadores por escola --")
    ideb = load_ideb(muni_inep)
    inse = load_inse(muni_inep)
    icg = load_icg(muni_inep)
    tdi = load_tdi(muni_inep)
    infra = load_infra(muni_inep)
    matriculas = load_matriculas(muni_inep)
    docentes = load_docentes(muni_inep)
    censo_hist = load_censo_hist(muni_inep)
    fluxo = load_fluxo_json(muni_inep)
    afd = load_afd_json(muni_inep)

    for eid in censo_hist:
        if eid in matriculas:
            censo_hist[eid]['mat_hist']['2025'] = matriculas[eid]['mat_total']
        if eid in docentes:
            censo_hist[eid]['doc_hist']['2025'] = docentes[eid]['doc_total']

    print("\n-- Montando JSON --")
    escolas = []
    stats = {'coords_sed': 0, 'coords_censo': 0, 'sem_coords': 0}

    for _, row in df.iterrows():
        inep = row['INEP']
        loc_raw = row.get('TP_LOCALIZACAO')
        escola = {
            'inep': inep,
            'nome': str(row['NO_ENTIDADE']),
            'municipio': str(row.get('NO_MUNICIPIO', 'Joinville')),
            'cod_mun': str(CO_MUN_JOINVILLE),
            'cre': '',
            'loc': LOC_MAP.get(loc_raw, str(loc_raw)),
            'salas': si(row['QT_SALAS_UTILIZADAS']) if 'QT_SALAS_UTILIZADAS' in row and pd.notna(row.get('QT_SALAS_UTILIZADAS')) else None,
        }

        if inep in coords:
            escola['lat'] = coords[inep]['lat']
            escola['lng'] = coords[inep]['lng']
            escola['coord_fonte'] = coords[inep]['fonte']
            stats['coords_sed'] += 1
        else:
            lat = safe_float(row.get('LATITUDE'))
            lng = safe_float(row.get('LONGITUDE'))
            if lat and lng and lat != 0 and lng != 0:
                escola['lat'] = lat
                escola['lng'] = lng
                escola['coord_fonte'] = 'Censo'
                stats['coords_censo'] += 1
            else:
                stats['sem_coords'] += 1

        for src in (ideb, inse, icg, tdi, infra, matriculas, docentes, censo_hist, fluxo, afd):
            if inep in src:
                escola.update(src[inep])

        escolas.append(escola)

    total = len(escolas)
    with_coords = sum(1 for e in escolas if e.get('lat'))
    output = {
        'metadata': {
            'fonte': 'Censo Escolar 2025 + Escolas_INEP_Coordenadas + Microdados INEP',
            'municipio': 'Joinville',
            'uf': 'SC',
            'rede': 'Municipal',
            'gerado_em': pd.Timestamp.now().isoformat(),
            'total_escolas': total,
            'com_coordenadas': with_coords,
        },
        'escolas': escolas,
    }

    out_main = os.path.join(PAINEL_DIR, 'escolas_municipais.json')
    with open(out_main, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))
    size_kb = os.path.getsize(out_main) / 1024

    # Compat: nome antigo usado pelo app.js (sera atualizado na Fase 3)
    out_compat = os.path.join(PAINEL_DIR, 'escolas_estaduais.json')
    shutil.copy2(out_main, out_compat)

    print(f"\n  JSON: escolas_municipais.json ({size_kb:.0f} KB)")
    print(f"  Total: {total} | Com coords: {with_coords} ({100*with_coords/total:.1f}%)")
    print(f"    SED Joinville: {stats['coords_sed']} | Censo fallback: {stats['coords_censo']} | Sem: {stats['sem_coords']}")
    print(f"  IDEB: {sum(1 for e in escolas if 'ideb_ai' in e or 'ideb_af' in e)}")
    print(f"  INSE: {sum(1 for e in escolas if 'inse_media' in e)}")
    print(f"  ICG:  {sum(1 for e in escolas if 'icg_nivel' in e)}")
    print(f"  TDI:  {sum(1 for e in escolas if 'tdi_fund' in e)}")
    print(f"  Infra: {sum(1 for e in escolas if 'infra_score' in e)}")
    print(f"  Fluxo 2024: {sum(1 for e in escolas if 'aprov_fund' in e)}")
    print(f"\nTempo total: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
