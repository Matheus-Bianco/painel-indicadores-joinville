# -*- coding: utf-8 -*-
"""
ETL Fluxo e Rendimento — Painel Joinville (rede MUNICIPAL)

Processa taxas de rendimento (aprovação/reprovação/abandono) e TDI dos arquivos
oficiais INEP (por município e escola), filtra Santa Catarina, e gera o JSON do
painel com foco em Joinville/SC.

PRINCÍPIO (descoberta do projeto UNESCO): as taxas de rendimento NÃO devem ser
calculadas como média/mediana das escolas — devem vir das bases JÁ CONSOLIDADAS
do INEP por município. Por isso, para todos os anos com arquivo por município
(2011/2012, 2015-2025), usamos o registro oficial do município de Joinville.
Apenas anos sem arquivo por município (ex.: 2010, 2013-2014) recorrem à agregação
de escolas.

FONTES (procuradas na pasta do Joinville e, como complemento, na pasta UNESCO):
  - tx_rend_municipios_*.xlsx / TX_REND_MUNICIPIOS_*.xlsx / TX_REND_MUN_*.xlsx /
    tx_rendimento_municipios_* / TAXAS RENDIMENTOS MUNICIPIOS *  → por município
  - tx_rendimento_escolas_2010/2011.xls                          → 2010-2011 (fallback)
  - tx_rend_escolas_2025.xlsx                                    → mapa por escola
  - TDI_MUNICIPIOS_*.xlsx / TDI_BRASIL_REGIOES_UFS_*.xlsx        → distorção idade-série

Mantém TODOS os municípios de SC em `por_municipio` (e `lookup_municipios`) para
permitir comparação com outros municípios e com a média municipal de SC
(`serie_municipios_sc`). `serie_temporal` é o dado oficial de Joinville.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import json, os, glob, time, re, shutil

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
UNESCO_BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\06. UNESCO\04. Produto 4_Indicadores Educacionais"
_REND_SUB = os.path.join("00. Bases de Dados", "02. Fluxo e Rendimento (Inep_2010_2024_Rendimento_TDI)", "01. Rendimento e TDI")
REND_DIR = os.path.join(BASE, _REND_SUB)
# Pasta da UNESCO usada apenas como COMPLEMENTO para arquivos que o Joinville não
# possui localmente (ex.: 2025, anos históricos). Os dados são nacionais (filtramos SC).
UNESCO_REND_DIR = os.path.join(UNESCO_BASE, _REND_SUB)
DATA_DIRS = [d for d in [REND_DIR, UNESCO_REND_DIR] if os.path.isdir(d)]
OUT_DIR = os.path.join(BASE, "painel", "dados")
os.makedirs(OUT_DIR, exist_ok=True)

SG_UF = "SC"
CO_MUN_JOINVILLE = 4209102  # codigo IBGE de Joinville/SC

# Joinville: apenas rede MUNICIPAL
REDES = {
    'municipal': {'dep': ['Municipal'], 'label': 'Municipal'},
}

# ══════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════

def safe_float(v):
    """Convert value to float, handling '--', NaN, etc."""
    if pd.isna(v) or v == '--' or v == '' or v is None:
        return None
    try:
        val = float(str(v).replace(',', '.'))
        if np.isnan(val) or np.isinf(val):
            return None
        return round(val, 1)
    except:
        return None

def extract_year_from_filename(fname):
    """Extract year (4 digits) from filename."""
    m = re.search(r'(\d{4})', fname)
    return int(m.group(1)) if m else None

def gfind(pattern):
    """Glob `pattern` em TODAS as DATA_DIRS, deduplicando por (basename, ano).
    Prefere a primeira pasta (Joinville) quando o mesmo arquivo existir nas duas."""
    seen, out = set(), []
    for d in DATA_DIRS:
        for f in glob.glob(os.path.join(d, pattern)):
            key = os.path.basename(f).lower()
            if key not in seen:
                seen.add(key)
                out.append(f)
    return out

# Sufixos de etapa/série -> sufixo da coluna INEP (CAT_*)
# Inclui as séries: Fundamental 1º-9º (FUN_01..09) e Médio 1ª-4ª (MED_01..04) + não-seriado.
REND_SUFIXOS = {
    'fund': '_CAT_FUN', 'fund_ai': '_CAT_FUN_AI', 'fund_af': '_CAT_FUN_AF',
    'fund_01': '_CAT_FUN_01', 'fund_02': '_CAT_FUN_02', 'fund_03': '_CAT_FUN_03',
    'fund_04': '_CAT_FUN_04', 'fund_05': '_CAT_FUN_05', 'fund_06': '_CAT_FUN_06',
    'fund_07': '_CAT_FUN_07', 'fund_08': '_CAT_FUN_08', 'fund_09': '_CAT_FUN_09',
    'med': '_CAT_MED', 'med_01': '_CAT_MED_01', 'med_02': '_CAT_MED_02',
    'med_03': '_CAT_MED_03', 'med_04': '_CAT_MED_04', 'med_ns': '_CAT_MED_NS',
}
# Prefixos de taxa: 1=Aprovação, 2=Reprovação, 3=Abandono
REND_RATES = {'aprov': '1', 'reprov': '2', 'aband': '3'}

# Lista completa de chaves geradas (etapa + série)
REND_KEYS = [f"{rk}_{sk}" for rk in REND_RATES for sk in REND_SUFIXOS]

def build_rend_record(row):
    """Monta um registro de rendimento com etapas E séries a partir de uma linha INEP."""
    rec = {}
    for rate_key, pfx in REND_RATES.items():
        for suf_key, suf_col in REND_SUFIXOS.items():
            rec[f"{rate_key}_{suf_key}"] = safe_float(row.get(f"{pfx}{suf_col}"))
    return rec

# ══════════════════════════════════════════════════════════
# READERS — ESCOLA-LEVEL (2010-2011, fallback)
# ══════════════════════════════════════════════════════════

def ler_escolas_2010_2011(filepath):
    """Lê arquivos .xls por escola de 2010-2011 (RS/SC/PR na aba 'SUL')."""
    fname = os.path.basename(filepath)
    sheet_name = 'SUL'
    for hrow in [6, 7, 5]:
        try:
            df_test = pd.read_excel(filepath, header=hrow, nrows=3, dtype=str, engine='xlrd', sheet_name=sheet_name)
            cols = [str(c) for c in df_test.columns]
            if any('Ano' in c for c in cols) and any('UF' in c for c in cols):
                df = pd.read_excel(filepath, header=hrow, dtype=str, engine='xlrd', sheet_name=sheet_name)
                uf_col = None
                for c in df.columns:
                    if 'UF' in str(c) and 'Unnamed' not in str(c):
                        uf_col = str(c); break
                if not uf_col:
                    continue
                df = df.dropna(subset=[uf_col])
                df = df[df[uf_col] == SG_UF]
                col_map = {}
                for i, c in enumerate(df.columns):
                    cs = str(c).lower()
                    if 'ano' in cs and 'unnamed' not in cs:
                        col_map['ano'] = i
                    elif ('código do mun' in cs or 'codigo do mun' in cs) and 'unnamed' not in cs:
                        col_map['cod_mun'] = i
                    elif ('nome do mun' in cs) and 'unnamed' not in cs:
                        col_map['nome_mun'] = i
                    elif ('rede' == cs or 'dependência' in cs or 'dependencia' in cs) and 'unnamed' not in cs:
                        col_map['dep'] = i
                if 'cod_mun' not in col_map or 'dep' not in col_map:
                    continue
                rate_starts = []
                for i, c in enumerate(df.columns):
                    cs = str(c).lower()
                    if 'taxa de aprov' in cs and 'fundamental' in cs:
                        rate_starts.append(('aprov_fund', i))
                    elif 'taxa de aprov' in cs and ('médio' in cs or 'medio' in cs):
                        rate_starts.append(('aprov_med', i))
                    elif 'taxa de reprov' in cs and 'fundamental' in cs:
                        rate_starts.append(('reprov_fund', i))
                    elif 'taxa de reprov' in cs and ('médio' in cs or 'medio' in cs):
                        rate_starts.append(('reprov_med', i))
                    elif 'taxa de abandon' in cs and 'fundamental' in cs:
                        rate_starts.append(('aband_fund', i))
                    elif 'taxa de abandon' in cs and ('médio' in cs or 'medio' in cs):
                        rate_starts.append(('aband_med', i))
                RATE_KEY_MAP = {
                    'aprov_fund': ('tap_FUN', 'tap_F14', 'tap_F58'),
                    'aprov_med':  ('tap_MED',),
                    'reprov_fund': ('tre_FUN', 'tre_F14', 'tre_F58'),
                    'reprov_med':  ('tre_MED',),
                    'aband_fund': ('tab_FUN', 'tab_F14', 'tab_F58'),
                    'aband_med':  ('tab_MED',),
                }
                cols_orig = list(df.columns)
                records = []
                for _, row in df.iterrows():
                    rec = {
                        'NU_ANO_CENSO': row.iloc[col_map.get('ano', 0)],
                        'CO_MUNICIPIO': row.iloc[col_map['cod_mun']],
                        'NO_MUNICIPIO': row.iloc[col_map.get('nome_mun', col_map['cod_mun'])],
                        'NO_DEPENDENCIA': row.iloc[col_map['dep']],
                    }
                    for label, start_idx in rate_starts:
                        out_keys = RATE_KEY_MAP.get(label, ())
                        for offset, key in enumerate(out_keys):
                            if start_idx + offset < len(cols_orig):
                                rec[key] = safe_float(row.iloc[start_idx + offset])
                    records.append(rec)
                result = pd.DataFrame(records)
                result['SG_UF'] = SG_UF
                print(f"    {fname}: header={hrow}, {len(result)} escolas SC")
                return result
        except Exception as e:
            continue
    print(f"    [ERRO] Não consegui ler: {fname}")
    return pd.DataFrame()

def agregar_escolas_por_municipio(df_escolas, dep_filter):
    """Agrega taxas por escola -> município via mediana (fallback p/ 2010-2011)."""
    if len(df_escolas) == 0:
        return {}, {}
    dep_col = 'NO_DEPENDENCIA' if 'NO_DEPENDENCIA' in df_escolas.columns else 'Dependad'
    if dep_col not in df_escolas.columns:
        return {}, {}
    df = df_escolas[df_escolas[dep_col].isin(dep_filter)].copy()
    if len(df) == 0:
        return {}, {}
    rate_map = {
        'tap_FUN': 'aprov_fund', 'tap_F14': 'aprov_fund_ai', 'tap_F58': 'aprov_fund_af', 'tap_MED': 'aprov_med',
        'tre_FUN': 'reprov_fund', 'tre_F14': 'reprov_fund_ai', 'tre_F58': 'reprov_fund_af', 'tre_MED': 'reprov_med',
        'tab_FUN': 'aband_fund', 'tab_F14': 'aband_fund_ai', 'tab_F58': 'aband_fund_af', 'tab_MED': 'aband_med',
    }
    for col in rate_map:
        if col in df.columns:
            df[col] = df[col].apply(safe_float)
    por_mun, lookup = {}, {}
    for cod_mun, grp in df.groupby('CO_MUNICIPIO'):
        cod = str(cod_mun).split('.')[0]
        entry = {}
        for esc_col, painel_key in rate_map.items():
            if esc_col in grp.columns:
                vals = grp[esc_col].dropna()
                entry[painel_key] = round(float(vals.median()), 1) if len(vals) > 0 else None
            else:
                entry[painel_key] = None
        por_mun[cod] = entry
        nomes = grp['NO_MUNICIPIO'].dropna()
        if len(nomes) > 0:
            lookup[cod] = str(nomes.iloc[0])
    return por_mun, lookup

# ══════════════════════════════════════════════════════════
# READERS — MUNICÍPIO-LEVEL (consolidado oficial)
# ══════════════════════════════════════════════════════════

def ler_excel_inep(filepath, uf_filter=True):
    """Lê Excel INEP com detecção automática do header (formato moderno e legado)."""
    fname = os.path.basename(filepath)
    for hrow in [8, 5, 9, 7, 6]:
        try:
            df = pd.read_excel(filepath, header=hrow, nrows=3, dtype=str)
        except:
            continue
        cols = [str(c) for c in df.columns]
        if any(c in cols for c in ['NU_ANO_CENSO', 'Ano']) and any(c in cols for c in ['SG_UF', 'UF']):
            break
    else:
        print(f"  [ERRO] Não encontrou header em {fname}")
        return pd.DataFrame()

    df = pd.read_excel(filepath, header=hrow, dtype=str)
    rename = {}
    for old, new in [('Ano', 'NU_ANO_CENSO'), ('UF', 'SG_UF'),
                      ('Código do Município', 'CO_MUNICIPIO'), ('Nome do Município', 'NO_MUNICIPIO'),
                      ('Localização', 'NO_CATEGORIA'), ('Dependência Administrativa', 'NO_DEPENDENCIA'),
                      ('Rede', 'NO_DEPENDENCIA'), ('Região', 'NO_REGIAO')]:
        if old in df.columns and new not in df.columns:
            rename[old] = new
    if rename:
        df = df.rename(columns=rename)
    if 'NO_DEPENDENCIA' in df.columns:
        df['NO_DEPENDENCIA'] = df['NO_DEPENDENCIA'].replace({'Particular': 'Privada'})
    if uf_filter and 'SG_UF' in df.columns:
        df = df[(df['SG_UF'] == SG_UF) & (df['NO_CATEGORIA'] == 'Total')]
    if 'NU_ANO_CENSO' in df.columns:
        df = df.dropna(subset=['NU_ANO_CENSO'])

    cols = list(df.columns)
    has_modern = any('1_CAT_FUN' in str(c) for c in cols)
    has_legacy = any('Taxa de Aprov' in str(c) for c in cols)
    if has_legacy and not has_modern and len(cols) >= 50:
        # Formato mesclado (2019): mapeia por posição -> incluindo séries 1º-9º e EM
        POS_MAP = {}
        for taxa_pref, base in (('1', 7), ('2', 25), ('3', 43)):
            POS_MAP[base + 0] = f'{taxa_pref}_CAT_FUN'
            POS_MAP[base + 1] = f'{taxa_pref}_CAT_FUN_AI'
            POS_MAP[base + 2] = f'{taxa_pref}_CAT_FUN_AF'
            for i in range(1, 10):
                POS_MAP[base + 2 + i] = f'{taxa_pref}_CAT_FUN_{i:02d}'
            POS_MAP[base + 12] = f'{taxa_pref}_CAT_MED'
            for i in range(1, 5):
                POS_MAP[base + 12 + i] = f'{taxa_pref}_CAT_MED_{i:02d}'
            POS_MAP[base + 17] = f'{taxa_pref}_CAT_MED_NS'
        new_cols = {}
        for pos, new_name in POS_MAP.items():
            if pos < len(cols):
                new_cols[cols[pos]] = new_name
        df = df.rename(columns=new_cols)
        print(f"[legacy->modern] ", end="")
    return df

def ler_rendimento_municipios():
    """Lê todos os arquivos de rendimento por município (consolidado oficial)."""
    patterns = [
        "tx_rend_municipios_*.xlsx",          # 2019-2025 (Windows: casa também 2016-2018)
        "TX_REND_MUNICIPIOS_*.xlsx",          # 2016-2018
        "TX_REND_MUN_*.xlsx",                 # 2015
        "tx_rendimento_municipios_*.xlsx",    # 2012
        "TAXAS RENDIMENTOS MUNICIPIOS *.xlsx",# 2013-2014
    ]
    seen, files = set(), []
    for pat in patterns:
        for f in gfind(pat):
            key = os.path.basename(f).lower()
            if key not in seen:
                seen.add(key); files.append(f)
    files = sorted(files, key=lambda p: extract_year_from_filename(os.path.basename(p)) or 0)
    print(f"  Encontrados {len(files)} arquivos de rendimento por município")
    frames = []
    for f in files:
        print(f"    Lendo {os.path.basename(f)}...", end=" ", flush=True)
        t0 = time.time()
        df = ler_excel_inep(f)
        print(f"{len(df)} municípios ({time.time()-t0:.1f}s)")
        if len(df) > 0:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def ler_rendimento_escolas_2010_2011():
    """Lê arquivos por escola apenas de 2010-2011 (anos sem arquivo por município)."""
    all_frames = {}
    for f in gfind("tx_rendimento_escolas_201*.xls"):
        if f.lower().endswith('.xlsx'):
            continue
        year = extract_year_from_filename(os.path.basename(f))
        if year and year <= 2011:
            print(f"    Lendo {os.path.basename(f)}...", end=" ", flush=True)
            t0 = time.time()
            df = ler_escolas_2010_2011(f)
            if len(df) > 0:
                all_frames[year] = df
            print(f"({time.time()-t0:.1f}s)")
    return all_frames

def ler_tdi_municipios():
    """Lê TDI por município (todos os SC)."""
    files = sorted(gfind("TDI_MUNICIPIOS_*.xlsx"))
    if not files:
        print("  [AVISO] Nenhum arquivo TDI_MUNICIPIOS_*.xlsx encontrado")
        return pd.DataFrame()
    frames = []
    for f in files:
        print(f"    Lendo {os.path.basename(f)}...", end=" ", flush=True)
        t0 = time.time()
        df = ler_excel_inep(f)
        print(f"{len(df)} municípios ({time.time()-t0:.1f}s)")
        if len(df) > 0:
            frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

def ler_escolas_rend_recente():
    """Lê o arquivo de rendimento por escola mais recente (2025, senão 2024)."""
    for nome, ano in [("tx_rend_escolas_2025.xlsx", 2025), ("tx_rend_escolas_2024.xlsx", 2024)]:
        hits = gfind(nome)
        if hits:
            filepath = hits[0]
            print(f"    Lendo {nome}...", end=" ", flush=True)
            t0 = time.time()
            df = ler_excel_inep(filepath, uf_filter=False)
            if len(df) > 0 and 'SG_UF' in df.columns:
                df = df[df['SG_UF'] == SG_UF]
            print(f"{len(df)} escolas SC — ano {ano} ({time.time()-t0:.1f}s)")
            return df, ano
    print("  [AVISO] Nenhum arquivo tx_rend_escolas_2025/2024.xlsx encontrado!")
    return pd.DataFrame(), None

# ══════════════════════════════════════════════════════════
# PROCESSOR
# ══════════════════════════════════════════════════════════

def _is_jv(cod):
    try:
        return int(float(cod)) == CO_MUN_JOINVILLE
    except (ValueError, TypeError):
        return False

def processar(dep_filter, rede_label, escolas_2010_2011, df_escolas_recente, ano_escola_recente):
    resultado = {
        "metadata": {
            "fonte": "INEP — Indicadores Educacionais (bases consolidadas por município)",
            "indicadores": "Taxas de Rendimento + Distorção Idade-Série",
            "uf": "SC",
            "municipio": "Joinville",
            "cod_municipio": str(CO_MUN_JOINVILLE),
            "rede": rede_label,
            "gerado_em": pd.Timestamp.now().isoformat(),
        },
        "serie_temporal": {},          # Joinville (consolidado oficial)
        "serie_municipios_sc": {},     # média dos municípios de SC (comparação)
        "por_municipio": {},           # TODOS os municípios de SC (comparação)
        "tdi_estadual": {},
        "tdi_por_municipio": {},
        "lookup_municipios": {},
    }

    # ── 1. ESCOLA-LEVEL (2010-2011) → agregação por município (fallback) ──
    print(f"\n  [Fase 1] Agregando escolas 2010-2011 por município (fallback)...")
    for year in sorted(escolas_2010_2011.keys()):
        por_mun, lookup = agregar_escolas_por_municipio(escolas_2010_2011[year], dep_filter)
        if por_mun:
            resultado["por_municipio"][str(year)] = por_mun
            resultado["lookup_municipios"].update(lookup)
            print(f"    {year}: {len(por_mun)} municípios")

    # ── 2. MUNICÍPIO-LEVEL (consolidado oficial) — substitui integralmente ──
    print(f"\n  [Fase 2] Lendo dados por município (consolidado oficial)...")
    df_mun = ler_rendimento_municipios()
    if len(df_mun) > 0:
        df_mun = df_mun[df_mun['NO_DEPENDENCIA'].isin(dep_filter)]
    if len(df_mun) > 0:
        for _, row in df_mun.drop_duplicates('CO_MUNICIPIO').iterrows():
            resultado["lookup_municipios"][str(row['CO_MUNICIPIO'])] = row['NO_MUNICIPIO']
        for ano in sorted(df_mun['NU_ANO_CENSO'].unique()):
            df_ano = df_mun[df_mun['NU_ANO_CENSO'] == ano]
            ano_str = str(ano)
            resultado["por_municipio"][ano_str] = {}   # oficial substitui agregação
            for _, row in df_ano.iterrows():
                cod = str(row['CO_MUNICIPIO'])
                resultado["por_municipio"][ano_str][cod] = build_rend_record(row)
            print(f"    {ano_str}: {len(df_ano)} municípios (arquivo por município)")

    # ── 3. SÉRIE TEMPORAL (Joinville) + MÉDIA MUNICÍPIOS SC ──
    cod_jv = str(CO_MUN_JOINVILLE)
    for ano, muns in sorted(resultado["por_municipio"].items()):
        # Joinville oficial (consolidado)
        resultado["serie_temporal"][ano] = dict(muns.get(cod_jv, {}))
        # Média dos municípios de SC (comparação) — média simples entre municípios com dado
        agg = {}
        for k in REND_KEYS:
            vals = [v.get(k) for v in muns.values() if v.get(k) is not None]
            agg[k] = round(float(np.mean(vals)), 1) if vals else None
        resultado["serie_municipios_sc"][ano] = agg

    # ── 4. TDI POR MUNICÍPIO (todos SC) + Joinville ──
    df_tdi = ler_tdi_municipios()
    if len(df_tdi) > 0:
        df_tdi = df_tdi[df_tdi['NO_DEPENDENCIA'].isin(dep_filter)]
    if len(df_tdi) > 0:
        for ano_tdi_val in sorted(df_tdi['NU_ANO_CENSO'].dropna().unique()):
            try:
                ano_tdi_str = str(int(float(ano_tdi_val)))
            except:
                continue
            df_tdi_ano = df_tdi[df_tdi['NU_ANO_CENSO'] == ano_tdi_val]
            resultado["tdi_ano"] = ano_tdi_str
            for _, row in df_tdi_ano.iterrows():
                cod = str(row['CO_MUNICIPIO'])
                resultado["tdi_por_municipio"][cod] = {
                    "tdi_fund": safe_float(row.get('FUN_CAT_0')),
                    "tdi_fund_ai": safe_float(row.get('FUN_AI_CAT_0')),
                    "tdi_fund_af": safe_float(row.get('FUN_AF_CAT_0')),
                    "tdi_med": safe_float(row.get('MED_CAT_0')),
                }
                if cod not in resultado["lookup_municipios"]:
                    resultado["lookup_municipios"][cod] = row.get('NO_MUNICIPIO', f'Cod.{cod}')
    jv_tdi = resultado["tdi_por_municipio"].get(cod_jv)
    if jv_tdi:
        resultado["tdi_estadual"] = jv_tdi

    # TDI série temporal de Joinville (caso haja múltiplos anos de TDI por município)
    tdi_serie = {}
    if len(df_tdi) > 0:
        df_tdi_jv = df_tdi[df_tdi['CO_MUNICIPIO'].apply(_is_jv)]
        for _, row in df_tdi_jv.iterrows():
            try:
                ano_str = str(int(float(row['NU_ANO_CENSO'])))
            except:
                continue
            tdi_serie[ano_str] = {
                "tdi_fund": safe_float(row.get('FUN_CAT_0')),
                "tdi_fund_ai": safe_float(row.get('FUN_AI_CAT_0')),
                "tdi_fund_af": safe_float(row.get('FUN_AF_CAT_0')),
                "tdi_med": safe_float(row.get('MED_CAT_0')),
            }
    resultado["tdi_serie_temporal"] = tdi_serie

    # ── 5. DADOS ESCOLAS (Mapa) — ano mais recente disponível, filtrado p/ Joinville ──
    por_escola = []
    if len(df_escolas_recente) > 0:
        df_esc = df_escolas_recente[df_escolas_recente['NO_DEPENDENCIA'].isin(dep_filter)]
        if 'CO_MUNICIPIO' in df_esc.columns:
            df_esc = df_esc[df_esc['CO_MUNICIPIO'].apply(_is_jv)]
        for _, row in df_esc.iterrows():
            rec = {
                "cod_escola": str(row.get('CO_ENTIDADE', '')),
                "nome_escola": str(row.get('NO_ENTIDADE', '')),
                "cod_mun": str(row.get('CO_MUNICIPIO', '')),
                "nome_mun": str(row.get('NO_MUNICIPIO', '')),
            }
            rec.update(build_rend_record(row))
            por_escola.append(rec)
    ano_rec = str(ano_escola_recente) if ano_escola_recente else "2025"
    resultado[f"por_escola_{ano_rec}"] = por_escola
    resultado["por_escola_recente"] = por_escola
    resultado["ano_escola_recente"] = ano_rec

    return resultado

# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("ETL FLUXO E RENDIMENTO — Painel Joinville (rede MUNICIPAL)")
    print(f"Pastas de dados: {DATA_DIRS}")
    print("=" * 70)
    t0 = time.time()

    print("\n[PRE-LOAD] Lendo arquivos de escola 2010-2011 (fallback)...")
    escolas_2010_2011 = ler_rendimento_escolas_2010_2011()
    print(f"  Carregados: {sorted(escolas_2010_2011.keys())}")

    print("\n[PRE-LOAD] Lendo arquivo de escola mais recente (2025/2024)...")
    df_escolas_recente, ano_escola_recente = ler_escolas_rend_recente()

    for rede_key, rede_cfg in REDES.items():
        print(f"\n{'='*60}\n  REDE: {rede_key.upper()} ({rede_cfg['label']})\n{'='*60}")
        resultado = processar(rede_cfg['dep'], rede_cfg['label'], escolas_2010_2011,
                              df_escolas_recente, ano_escola_recente or 2025)
        out_json = os.path.join(OUT_DIR, f"4_3_fluxo_{rede_key}.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, separators=(',', ':'))
        size_mb = os.path.getsize(out_json) / 1024 / 1024
        print(f"\n  JSON: {os.path.basename(out_json)} ({size_mb:.1f} MB)")
        print(f"  Anos rendimento: {sorted(resultado['serie_temporal'].keys())}")
        print(f"  Municípios SC: {len(resultado['lookup_municipios'])}")
        jv = resultado['serie_temporal'].get(sorted(resultado['serie_temporal'].keys())[-1], {})
        print(f"  Joinville último ano (aprov_fund_ai/af): {jv.get('aprov_fund_ai')}/{jv.get('aprov_fund_af')}")

    # Backward compatibility
    src = os.path.join(OUT_DIR, "4_3_fluxo_municipal.json")
    dst = os.path.join(OUT_DIR, "4_3_fluxo_rendimento.json")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"\n[COMPAT] Copiado -> {os.path.basename(dst)}")

    print(f"\nTempo total: {time.time()-t0:.1f}s")
    print("=" * 70)
