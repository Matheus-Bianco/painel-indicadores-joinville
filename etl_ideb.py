# -*- coding: utf-8 -*-
"""
ETL IDEB — Painel Joinville (Produto 4)
Usa planilhas OFICIAIS de municípios do INEP (não média de escolas).
Gera série Joinville + ranking SC + ranking 10 maiores cidades.
"""
import sys, io, os, time, json, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
BASES_DIR = os.path.join(BASE, "00. Bases de Dados")
_fr = next((d for d in os.listdir(BASES_DIR) if d.startswith("02.") and "Fluxo" in d), None)
if _fr is None:
    raise FileNotFoundError("Pasta '02. Fluxo e Rendimento' nao encontrada")
_ideb_sub = next((d for d in os.listdir(os.path.join(BASES_DIR, _fr)) if "IDEB" in d.upper()), "02. IDEB")
IDEB_DIR = os.path.join(BASES_DIR, _fr, _ideb_sub)

CO_MUN_JOINVILLE = "4209102"
UF_SC = "SC"
PAINEL_DIR = os.path.join(BASE, "painel", "dados")
os.makedirs(PAINEL_DIR, exist_ok=True)

POP_PATH = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\01. Indicadores do Censo\POP2025_20260113.xls"

ETAPAS = {
    "AI": {
        "file_mun": "divulgacao_anos_iniciais_municipios_2023.xlsx",
        "file_esc": "divulgacao_anos_iniciais_escolas_2023.xlsx",
        "uf_sheet": "UF e Regiões (AI)",
        "anos_ideb": [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023],
        "anos_proj": [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021],
    },
    "AF": {
        "file_mun": "divulgacao_anos_finais_municipios_2023.xlsx",
        "file_esc": "divulgacao_anos_finais_escolas_2023.xlsx",
        "uf_sheet": "UF e Regiões (AF)",
        "anos_ideb": [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023],
        "anos_proj": [2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021],
    },
}


def safe_numeric(val):
    if val is None or val == "" or val == "-" or val == "ND" or val == "nd":
        return None
    try:
        v = float(val)
        return None if np.isnan(v) else v
    except (ValueError, TypeError):
        return None


def find_file(name):
    """Busca arquivo por nome (inclui subpastas do zip)."""
    for root, _dirs, files in os.walk(IDEB_DIR):
        if name in files:
            return os.path.join(root, name)
    raise FileNotFoundError(f"{name} nao encontrado em {IDEB_DIR}")


def load_mun_file(etapa_key):
    cfg = ETAPAS[etapa_key]
    fpath = find_file(cfg["file_mun"])
    print(f"  Lendo municipios {cfg['file_mun']}...", end=" ", flush=True)
    df = pd.read_excel(fpath, header=9)
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].apply(
        lambda x: str(int(float(x)))[:7] if pd.notna(x) and str(x) not in ("", "nan") else None
    )
    df["REDE"] = df["REDE"].astype(str).str.strip()
    print(f"{len(df)} linhas")
    return df


def load_n_escolas_joinville(etapa_key, rede="Municipal"):
    """Conta escolas com IDEB válido em Joinville (arquivo escolas)."""
    cfg = ETAPAS[etapa_key]
    try:
        fpath = find_file(cfg["file_esc"])
    except FileNotFoundError:
        return {}
    print(f"  Contando escolas Joinville ({etapa_key})...", end=" ", flush=True)
    df = pd.read_excel(fpath, header=9)
    df = df[df["CO_MUNICIPIO"].astype(str).str[:7] == CO_MUN_JOINVILLE]
    df = df[df["REDE"].astype(str).str.strip() == rede]
    out = {}
    for ano in cfg["anos_ideb"]:
        col = f"VL_OBSERVADO_{ano}"
        if col not in df.columns:
            continue
        n = df[col].apply(safe_numeric).notna().sum()
        if n:
            out[str(ano)] = int(n)
    print(out.get("2023", 0), "escolas em 2023")
    return out


def extract_serie_municipio(df, etapa_key, co_mun, rede="Municipal"):
    """IDEB oficial do município (1 linha por rede)."""
    cfg = ETAPAS[etapa_key]
    row = df[(df["CO_MUNICIPIO"] == co_mun) & (df["REDE"] == rede)]
    if row.empty:
        return {}
    r = row.iloc[0]
    serie = {}
    for ano in cfg["anos_ideb"]:
        obs = safe_numeric(r.get(f"VL_OBSERVADO_{ano}"))
        if obs is None:
            continue
        entry = {
            "ideb": round(obs, 1),
            "nota_saeb": None,
            "rendimento": None,
            "n_escolas": None,
        }
        nota = safe_numeric(r.get(f"VL_NOTA_MEDIA_{ano}"))
        rend = safe_numeric(r.get(f"VL_INDICADOR_REND_{ano}"))
        if nota is not None:
            entry["nota_saeb"] = round(nota, 2)
        if rend is not None:
            entry["rendimento"] = round(rend, 4)
        if ano in cfg["anos_proj"]:
            meta = safe_numeric(r.get(f"VL_PROJECAO_{ano}"))
            if meta is not None:
                entry["meta"] = round(meta, 1)
        serie[str(ano)] = entry
    return serie


def extract_sc_municipal_all(df, etapa_key, ano=2023, rede="Municipal"):
    """Todos os municípios de SC com IDEB na rede municipal (ano)."""
    cfg = ETAPAS[etapa_key]
    obs_col = f"VL_OBSERVADO_{ano}"
    meta_col = f"VL_PROJECAO_{ano}" if ano in cfg["anos_proj"] else None
    sc = df[(df["SG_UF"] == UF_SC) & (df["REDE"] == rede)].copy()
    sc["_ideb"] = sc[obs_col].apply(safe_numeric)
    sc = sc[sc["_ideb"].notna()]
    rows = []
    for _, r in sc.iterrows():
        item = {
            "cod": r["CO_MUNICIPIO"],
            "nome": str(r["NO_MUNICIPIO"]).strip(),
            "ideb": round(float(r["_ideb"]), 1),
        }
        if meta_col and meta_col in sc.columns:
            m = safe_numeric(r.get(meta_col))
            if m is not None:
                item["meta"] = round(m, 1)
                item["atingiu_meta"] = item["ideb"] >= item["meta"]
        rows.append(item)
    rows.sort(key=lambda x: (-x["ideb"], x["nome"]))
    for i, item in enumerate(rows, 1):
        item["posicao"] = i
    return rows


def load_top10_sc_pop():
    """Top 10 municípios de SC por população (IBGE estimativa 2025)."""
    df = pd.read_excel(POP_PATH, sheet_name="Municípios", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    nome_col = [c for c in df.columns if "NOME" in c.upper()][0]
    pop_col = [c for c in df.columns if "POPULA" in c.upper()][0]
    uf_col = [c for c in df.columns if c.upper() == "UF"][0]
    cod_uf = [c for c in df.columns if "COD. UF" in c.upper()][0]
    cod_mun = [c for c in df.columns if "COD. MUNIC" in c.upper()][0]
    sc = df[df[uf_col].astype(str) == UF_SC].copy()
    sc["_pop"] = pd.to_numeric(sc[pop_col], errors="coerce")
    sc = sc.dropna(subset=["_pop"])
    sc["_cod"] = sc.apply(
        lambda r: f"{int(r[cod_uf]):02d}{int(r[cod_mun]):05d}", axis=1
    )
    top = sc.nlargest(10, "_pop")
    out = []
    for i, (_, r) in enumerate(top.iterrows(), 1):
        out.append({
            "rank_pop": i,
            "cod": r["_cod"],
            "nome": str(r[nome_col]).strip(),
            "populacao": int(r["_pop"]),
        })
    return out


def load_uf_publica_refs():
    """Referências oficiais rede Pública (UF SC e Brasil) — planilha regiões/UFs."""
    try:
        fpath = find_file("divulgacao_regioes_ufs_ideb_2023.xlsx")
    except FileNotFoundError:
        return {}
    refs = {"sc_publica": {}, "brasil_publica": {}}
    # Mantém chaves antigas do painel apontando para pública oficial
    refs_compat = {"sc_municipal": {}, "brasil_municipal": {}}

    for etapa_key, cfg in ETAPAS.items():
        df = pd.read_excel(fpath, sheet_name=cfg["uf_sheet"], header=9)
        df = df.rename(columns={df.columns[0]: "UF", df.columns[1]: "REDE"})
        for ano in cfg["anos_ideb"]:
            col = f"VL_OBSERVADO_{ano}"
            if col not in df.columns:
                continue
            # Santa Catarina — Pública
            sc = df[
                (df["UF"].astype(str) == "Santa Catarina")
                & (df["REDE"].astype(str).str.contains("Pública", case=False, na=False))
            ]
            if len(sc):
                v = safe_numeric(sc.iloc[0][col])
                if v is not None:
                    refs["sc_publica"].setdefault(str(ano), {})[etapa_key] = round(v, 1)
                    refs_compat["sc_municipal"].setdefault(str(ano), {})[etapa_key] = round(v, 1)
            # Brasil — última ocorrência com Pública no bloco nacional
            br = df[
                (df["UF"].astype(str).str.strip().isin(["Brasil", "BRASIL"]))
                & (df["REDE"].astype(str).str.contains("Pública", case=False, na=False))
            ]
            if br.empty:
                # Em algumas versões Brasil vem sem nome de UF nas primeiras linhas regionais;
                # usa média nacional via linha 'Total' da região inexistente — fallback:
                pass
            else:
                v = safe_numeric(br.iloc[0][col])
                if v is not None:
                    refs["brasil_publica"].setdefault(str(ano), {})[etapa_key] = round(v, 1)
                    refs_compat["brasil_municipal"].setdefault(str(ano), {})[etapa_key] = round(v, 1)

    # Fallback Brasil: se não achar, calcula mediana dos municípios (rede Municipal) no arquivo mun
    return {**refs_compat, **refs}


def build_rankings(dfs_mun, top10_pop):
    """Monta rankings 2023 (AI/AF) para SC geral e 10 maiores."""
    ano = 2023
    rankings = {"ano": ano, "rede": "Municipal", "sc_geral": {}, "top10_cidades": {}}

    for et in ("AI", "AF"):
        rows = extract_sc_municipal_all(dfs_mun[et], et, ano=ano)
        rankings["sc_geral"][et] = rows
        # posição Joinville
        jv = next((r for r in rows if r["cod"] == CO_MUN_JOINVILLE), None)
        rankings["sc_geral"][f"joinville_{et}"] = {
            "posicao": jv["posicao"] if jv else None,
            "ideb": jv["ideb"] if jv else None,
            "n_municipios": len(rows),
        }

    # Top 10 — junta AI + AF + pop
    lookup_ai = {r["cod"]: r for r in rankings["sc_geral"]["AI"]}
    lookup_af = {r["cod"]: r for r in rankings["sc_geral"]["AF"]}
    jv_ai = lookup_ai.get(CO_MUN_JOINVILLE, {}).get("ideb")
    jv_af = lookup_af.get(CO_MUN_JOINVILLE, {}).get("ideb")

    top_rows = []
    for t in top10_pop:
        ai = lookup_ai.get(t["cod"])
        af = lookup_af.get(t["cod"])
        row = {
            **t,
            "ideb_ai": ai["ideb"] if ai else None,
            "ideb_af": af["ideb"] if af else None,
            "posicao_sc_ai": ai["posicao"] if ai else None,
            "posicao_sc_af": af["posicao"] if af else None,
            "delta_ai_vs_joinville": round(ai["ideb"] - jv_ai, 1) if ai and jv_ai is not None else None,
            "delta_af_vs_joinville": round(af["ideb"] - jv_af, 1) if af and jv_af is not None else None,
        }
        top_rows.append(row)

    # ranking interno top10 por AI e AF
    for et_key, field in (("AI", "ideb_ai"), ("AF", "ideb_af")):
        ranked = sorted(
            [r for r in top_rows if r[field] is not None],
            key=lambda x: (-x[field], x["nome"]),
        )
        pos = {r["cod"]: i for i, r in enumerate(ranked, 1)}
        for r in top_rows:
            r[f"posicao_top10_{et_key.lower()}"] = pos.get(r["cod"])

    rankings["top10_cidades"] = {
        "criterio_pop": "IBGE Estimativa população residente 1º jul/2025",
        "linhas": top_rows,
        "joinville": next((r for r in top_rows if r["cod"] == CO_MUN_JOINVILLE), None),
    }

    # Tabela contraste compacta SC (top 15 + Joinville se fora)
    for et in ("AI", "AF"):
        rows = rankings["sc_geral"][et]
        top15 = rows[:15]
        codes = {r["cod"] for r in top15}
        if CO_MUN_JOINVILLE not in codes:
            jv = next((r for r in rows if r["cod"] == CO_MUN_JOINVILLE), None)
            if jv:
                top15 = top15 + [jv]
        rankings["sc_geral"][f"contraste_{et}"] = top15

    return rankings


def main():
    t0 = time.time()
    print("=" * 60)
    print("ETL IDEB — MUNICÍPIOS OFICIAIS INEP (Joinville/SC)")
    print("=" * 60)

    dfs_mun = {}
    for et in ETAPAS:
        dfs_mun[et] = load_mun_file(et)

    n_esc = {et: load_n_escolas_joinville(et) for et in ETAPAS}
    top10 = load_top10_sc_pop()
    print("\nTop 10 SC (pop 2025):")
    for t in top10:
        print(f"  {t['rank_pop']:2d}. {t['nome']:<22} {t['populacao']:>9,}  {t['cod']}")

    # Série Joinville municipal
    serie_temporal = {}
    for et in ETAPAS:
        serie = extract_serie_municipio(dfs_mun[et], et, CO_MUN_JOINVILLE)
        for ano, data in serie.items():
            n = n_esc[et].get(ano)
            if n:
                data["n_escolas"] = n
            serie_temporal.setdefault(ano, {})[et] = data
        print(f"\n  {et} Joinville 2023 = {serie.get('2023', {}).get('ideb')} (oficial INEP)")

    # por_municipio: todos SC (para rankings no front) — só último ano completo + série JV
    por_municipio = {}
    lookup = {CO_MUN_JOINVILLE: "Joinville"}
    for ano in ETAPAS["AI"]["anos_ideb"]:
        por_municipio[str(ano)] = {}
        for et in ETAPAS:
            rows = extract_sc_municipal_all(dfs_mun[et], et, ano=ano)
            for r in rows:
                lookup[r["cod"]] = r["nome"]
                por_municipio[str(ano)].setdefault(r["cod"], {})[et] = {
                    "ideb": r["ideb"],
                    "n_escolas": None,
                }
                if "meta" in r:
                    por_municipio[str(ano)][r["cod"]][et]["meta"] = r["meta"]

    rankings = build_rankings(dfs_mun, top10)
    refs = load_uf_publica_refs()

    # Média simples dos municípios SC (útil como contraste no ranking)
    media_sc = {}
    for et in ("AI", "AF"):
        for ano_s, mun_map in por_municipio.items():
            vals = [m[et]["ideb"] for m in mun_map.values() if et in m and m[et].get("ideb") is not None]
            if vals:
                media_sc.setdefault(ano_s, {})[et] = round(float(np.mean(vals)), 1)

    resultado = {
        "metadata": {
            "fonte": "IDEB/INEP — Divulgação 2023 (planilhas de municípios)",
            "recorte": "Rede Municipal — Joinville/SC",
            "gerado_em": pd.Timestamp.now().isoformat(),
            "formula": "IDEB = N (Nota SAEB padronizada) × P (Indicador de Rendimento)",
            "nota_metodologica": (
                "Valores municipais oficiais do INEP (VL_OBSERVADO). "
                "Não é média dos IDEBs escolares — a média escolar distorce o índice da rede."
            ),
        },
        "serie_temporal": serie_temporal,
        "por_municipio": por_municipio,
        "lookup_municipios": lookup,
        "referencias": refs,
        "media_municipios_sc": media_sc,
        "rankings": rankings,
    }

    for out_name in ("4_7_ideb_municipal.json", "4_7_ideb.json"):
        out_json = os.path.join(PAINEL_DIR, out_name)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        print(f"\nJSON: {out_name} ({os.path.getsize(out_json)/1024:.0f} KB)")

    # Resumo contraste
    jv_ai = rankings["sc_geral"]["joinville_AI"]
    jv_af = rankings["sc_geral"]["joinville_AF"]
    print("\n--- Ranking Joinville em SC (rede Municipal, 2023) ---")
    print(f"  AI: {jv_ai['ideb']} — {jv_ai['posicao']}º de {jv_ai['n_municipios']}")
    print(f"  AF: {jv_af['ideb']} — {jv_af['posicao']}º de {jv_af['n_municipios']}")
    jv_t10 = rankings["top10_cidades"]["joinville"]
    if jv_t10:
        print("--- Entre as 10 maiores cidades ---")
        print(f"  AI: {jv_t10.get('posicao_top10_ai')}º | AF: {jv_t10.get('posicao_top10_af')}º")

    print(f"\nTempo total: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
