# -*- coding: utf-8 -*-
"""
ETL IDEB — Produto 4 UNESCO RS
Extrai IDEB observado, metas, notas SAEB e indicador de rendimento
das planilhas oficiais INEP (divulgação 2023) por escola.
Gera JSONs multi-rede para o painel.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import json, os, time

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
BASES_DIR = os.path.join(BASE, "00. Bases de Dados")
# Resolve a pasta de IDEB de forma robusta (nome do diretorio varia entre versoes)
_fr = next((d for d in os.listdir(BASES_DIR) if d.startswith("02.") and "Fluxo" in d), None)
if _fr is None:
    raise FileNotFoundError("Pasta '02. Fluxo e Rendimento' nao encontrada")
_ideb_sub = next((d for d in os.listdir(os.path.join(BASES_DIR, _fr)) if "IDEB" in d.upper()), "02. IDEB")
IDEB_DIR = os.path.join(BASES_DIR, _fr, _ideb_sub)
CO_MUN_JOINVILLE = "4209102"  # codigo IBGE de Joinville/SC
PAINEL_DIR = os.path.join(BASE, "painel", "dados")
os.makedirs(PAINEL_DIR, exist_ok=True)

# Files and etapa config
ETAPAS = {
    "AI": {
        "file": "divulgacao_anos_iniciais_escolas_2023.xlsx",
        "label": "Anos Iniciais (5º ano)",
        "anos_ideb": [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023],
        "anos_proj": [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021],
    },
    "AF": {
        "file": "divulgacao_anos_finais_escolas_2023.xlsx",
        "label": "Anos Finais (9º ano)",
        "anos_ideb": [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023],
        "anos_proj": [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021],
    },
    "EM": {
        "file": "divulgacao_ensino_medio_escolas_2023.xlsx",
        "label": "Ensino Médio",
        "anos_ideb": [2017, 2019, 2021, 2023],
        "anos_proj": [2019, 2021],
    },
}

REDES = {
    'municipal': ['Municipal'],
}


def safe_numeric(val):
    """Convert to float, handling '-', 'ND', 'nan', etc."""
    if val is None or val == '' or val == '-' or val == 'ND' or val == 'nd':
        return None
    try:
        v = float(val)
        return v if not np.isnan(v) else None
    except (ValueError, TypeError):
        return None


def load_ideb_file(etapa_key):
    """Load IDEB Excel file with header at row 9."""
    cfg = ETAPAS[etapa_key]
    fpath = os.path.join(IDEB_DIR, cfg["file"])
    print(f"  Lendo {cfg['file']}...", end=" ", flush=True)
    df = pd.read_excel(fpath, header=9)
    # Filtra Joinville/SC (codigo IBGE 4209102)
    df = df[df['CO_MUNICIPIO'].astype(str).str[:7] == CO_MUN_JOINVILLE].copy()
    print(f"{len(df)} escolas Joinville")
    return df


def extract_etapa_data(df, etapa_key, rede_filter=None):
    """Extract IDEB data for one etapa, optionally filtered by rede."""
    cfg = ETAPAS[etapa_key]
    
    if rede_filter:
        df = df[df['REDE'].isin(rede_filter)].copy()
    
    serie = {}
    for ano in cfg["anos_ideb"]:
        obs_col = f"VL_OBSERVADO_{ano}"
        nota_col = f"VL_NOTA_MEDIA_{ano}"
        rend_col = f"VL_INDICADOR_REND_{ano}"
        proj_col = f"VL_PROJECAO_{ano}" if ano in cfg["anos_proj"] else None
        
        if obs_col not in df.columns:
            continue
        
        # Convert to numeric — use df index for alignment
        vals_obs = df[obs_col].apply(safe_numeric)
        vals_nota = df[nota_col].apply(safe_numeric) if nota_col in df.columns else pd.Series(dtype=float, index=df.index)
        vals_rend = df[rend_col].apply(safe_numeric) if rend_col in df.columns else pd.Series(dtype=float, index=df.index)
        vals_proj = df[proj_col].apply(safe_numeric) if proj_col and proj_col in df.columns else pd.Series(dtype=float, index=df.index)
        
        # Only schools with valid IDEB
        valid_idx = vals_obs.dropna().index
        n_escolas = len(valid_idx)
        
        if n_escolas == 0:
            continue
        
        entry = {
            "ideb": round(float(vals_obs.loc[valid_idx].mean()), 2),
            "nota_saeb": round(float(vals_nota.loc[valid_idx].mean()), 2) if vals_nota.loc[valid_idx].notna().sum() > 0 else None,
            "rendimento": round(float(vals_rend.loc[valid_idx].mean()), 4) if vals_rend.loc[valid_idx].notna().sum() > 0 else None,
            "n_escolas": int(n_escolas),
        }
        
        # Projection (meta)
        proj_valid = vals_proj.loc[valid_idx].dropna()
        if len(proj_valid) > 0:
            entry["meta"] = round(float(proj_valid.mean()), 2)
        
        serie[str(ano)] = entry
    
    return serie


def extract_municipio_data(df, etapa_key, rede_filter=None):
    """Extract per-municipality IDEB data."""
    cfg = ETAPAS[etapa_key]
    
    if rede_filter:
        df = df[df['REDE'].isin(rede_filter)].copy()
    
    # Use latest year with data
    for ano in reversed(cfg["anos_ideb"]):
        obs_col = f"VL_OBSERVADO_{ano}"
        if obs_col in df.columns:
            df['_ideb'] = df[obs_col].apply(safe_numeric)
            df_valid = df[df['_ideb'].notna()].copy()
            if len(df_valid) > 0:
                break
    else:
        return {}, {}
    
    lookup = {}
    mun_data = {}
    
    for cod, grp in df_valid.groupby('CO_MUNICIPIO'):
        cod_str = str(int(cod))[:7]
        nome = grp['NO_MUNICIPIO'].iloc[0]
        lookup[cod_str] = nome
        
        mun_data[cod_str] = {
            "ideb": round(float(grp['_ideb'].mean()), 2),
            "n_escolas": len(grp),
        }
    
    return mun_data, lookup


def extract_mun_all_years(df, etapa_key, rede_filter=None):
    """Extract per-municipality IDEB for ALL years."""
    cfg = ETAPAS[etapa_key]
    
    if rede_filter:
        df = df[df['REDE'].isin(rede_filter)].copy()
    
    por_ano = {}
    lookup = {}
    
    for ano in cfg["anos_ideb"]:
        obs_col = f"VL_OBSERVADO_{ano}"
        if obs_col not in df.columns:
            continue
        
        df['_ideb'] = df[obs_col].apply(safe_numeric)
        df_valid = df[df['_ideb'].notna()].copy()
        
        if len(df_valid) == 0:
            continue
        
        mun_data = {}
        for cod, grp in df_valid.groupby('CO_MUNICIPIO'):
            cod_str = str(int(cod))[:7]
            nome = grp['NO_MUNICIPIO'].iloc[0]
            lookup[cod_str] = nome
            mun_data[cod_str] = {
                "ideb": round(float(grp['_ideb'].mean()), 2),
                "n_escolas": len(grp),
            }
        
        if mun_data:
            por_ano[str(ano)] = mun_data
    
    return por_ano, lookup


def main():
    t0 = time.time()
    print("=" * 60)
    print("ETL IDEB — MULTI-REDE RS")
    print("=" * 60)
    
    # Load all files once
    raw_dfs = {}
    for etapa_key in ETAPAS:
        raw_dfs[etapa_key] = load_ideb_file(etapa_key)
    
    # Generate per-rede JSONs
    for rede_key, rede_filter in REDES.items():
        print(f"\n{'='*60}")
        print(f"  REDE: {rede_key.upper()}")
        print(f"{'='*60}")
        
        resultado = {
            "metadata": {
                "fonte": "IDEB/INEP — Divulgação 2023",
                "recorte": f"Rede {rede_key.title()} RS",
                "gerado_em": pd.Timestamp.now().isoformat(),
                "formula": "IDEB = N (Nota SAEB padronizada) × P (Indicador de Rendimento)",
            },
            "serie_temporal": {},
            "por_municipio": {},
            "lookup_municipios": {},
        }
        
        all_lookup = {}
        
        for etapa_key in ETAPAS:
            df = raw_dfs[etapa_key]
            serie = extract_etapa_data(df, etapa_key, rede_filter)
            
            for ano, data in serie.items():
                if ano not in resultado["serie_temporal"]:
                    resultado["serie_temporal"][ano] = {}
                resultado["serie_temporal"][ano][etapa_key] = data
            
            # Per-municipality (all years)
            por_ano, lookup = extract_mun_all_years(df, etapa_key, rede_filter)
            all_lookup.update(lookup)
            
            for ano, mun_data in por_ano.items():
                if ano not in resultado["por_municipio"]:
                    resultado["por_municipio"][ano] = {}
                for cod, md in mun_data.items():
                    if cod not in resultado["por_municipio"][ano]:
                        resultado["por_municipio"][ano][cod] = {}
                    resultado["por_municipio"][ano][cod][etapa_key] = md
            
            # Summary
            anos_disp = sorted(serie.keys())
            if anos_disp:
                ultimo = anos_disp[-1]
                d = serie[ultimo]
                print(f"  {etapa_key}: IDEB {ultimo} = {d['ideb']} ({d['n_escolas']} escolas)")
        
        resultado["lookup_municipios"] = all_lookup
        
        # Save JSON
        out_json = os.path.join(PAINEL_DIR, f"4_7_ideb_{rede_key}.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        size_kb = os.path.getsize(out_json) / 1024
        print(f"  JSON: {os.path.basename(out_json)} ({size_kb:.0f} KB)")
    
    # Backward compat
    import shutil
    src = os.path.join(PAINEL_DIR, "4_7_ideb_municipal.json")
    dst = os.path.join(PAINEL_DIR, "4_7_ideb.json")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"\n[COMPAT] Copiado -> 4_7_ideb.json")
    
    print(f"\nTempo total: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
