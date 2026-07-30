# -*- coding: utf-8 -*-
"""Gera lista SED + conveniadas e atualiza metadata do acesso municipal."""
from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

import pandas as pd

BASE = Path(r"C:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville")
XLSX = BASE / "03. Escolas de Joinville + Conveniadas" / "Unidades escolares-2026-07-30-08-54-12-1785412452259.xlsx"
OUT_DIR = BASE / "03. Escolas de Joinville + Conveniadas"
PAINEL = BASE / "04. Produto 4_Indicadores Educacionais" / "painel" / "dados"
MICRO = BASE / "04. Produto 4_Indicadores Educacionais" / "00. Bases de Dados" / "01. Acesso e Matrículas (Censo Escolar_2010_2025)" / "01. extrações_2010_2025"

DEP = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
CAT = {1: "Particular", 2: "Comunitaria", 3: "Confessionaria", 4: "Filantropica"}


def norm_inep(v):
    if pd.isna(v):
        return None
    try:
        return str(int(float(v)))
    except Exception:
        s = str(v).strip()
        return s if s and s.lower() != "nan" else None


def main():
    df = pd.read_excel(XLSX)
    rename = {}
    for c in df.columns:
        cl = str(c).lower()
        if "inep" in cl:
            rename[c] = "inep"
        elif "nome completo" in cl:
            rename[c] = "nome_completo"
        elif cl.strip() == "nome":
            rename[c] = "nome"
        elif "prefixo" in cl:
            rename[c] = "prefixo"
        elif "classe" in cl:
            rename[c] = "classe"
        elif "bairro" in cl:
            rename[c] = "bairro"
    df = df.rename(columns=rename)
    df["inep"] = df["inep"].map(norm_inep)
    df = df[df["inep"].notna()].copy()

    # dedupe por INEP (mantem primeira ocorrencia)
    df_u = df.drop_duplicates(subset=["inep"], keep="first").copy()

    f_esc = MICRO / "Tabela_Escola_2025.csv"
    cols = [
        "CO_ENTIDADE", "NO_ENTIDADE", "TP_DEPENDENCIA", "CO_MUNICIPIO",
        "TP_CATEGORIA_ESCOLA_PRIVADA", "IN_PODER_PUBLICO_PARCERIA", "TP_PODER_PUBLICO_PARCERIA",
    ]
    dfc = pd.read_csv(f_esc, sep=";", encoding="latin-1", usecols=cols)
    dfc = dfc[dfc["CO_MUNICIPIO"] == 4209102].copy()
    dfc["inep"] = dfc["CO_ENTIDADE"].map(norm_inep)
    dfc["dep"] = dfc["TP_DEPENDENCIA"].map(DEP)

    # matriculas 2025
    f_mat = MICRO / "Tabela_Matricula_2025.csv"
    dm = pd.read_csv(f_mat, sep=";", encoding="latin-1", usecols=["CO_ENTIDADE", "QT_MAT_BAS", "QT_MAT_INF"])
    dm["inep"] = dm["CO_ENTIDADE"].map(norm_inep)
    mat_map = dm.groupby("inep").agg(mat_total=("QT_MAT_BAS", "sum"), mat_infantil=("QT_MAT_INF", "sum")).to_dict("index")

    censo = dfc.set_index("inep", drop=False)

    escolas = []
    for _, r in df_u.iterrows():
        inep = r["inep"]
        if inep in censo.index:
            cen = censo.loc[inep]
            if isinstance(cen, pd.DataFrame):
                cen = cen.iloc[0]
            dep = cen["dep"]
            nome_censo = str(cen["NO_ENTIDADE"])
            cat = cen.get("TP_CATEGORIA_ESCOLA_PRIVADA")
            parc = cen.get("IN_PODER_PUBLICO_PARCERIA")
            tp_parc = cen.get("TP_PODER_PUBLICO_PARCERIA")
        else:
            dep, nome_censo, cat, parc, tp_parc = "NAO_NO_CENSO", None, None, None, None
        mats = mat_map.get(inep) or {}
        tipo = "conveniada" if dep == "Privada" else ("municipal_direta" if dep == "Municipal" else "outra")
        escolas.append({
            "inep": inep,
            "nome_sed": str(r.get("nome_completo") or r.get("nome") or ""),
            "nome_censo": nome_censo,
            "prefixo": None if pd.isna(r.get("prefixo")) else str(r.get("prefixo")),
            "classe": None if pd.isna(r.get("classe")) else str(r.get("classe")),
            "bairro": None if pd.isna(r.get("bairro")) else str(r.get("bairro")),
            "dep_censo": dep,
            "cat_priv": None if pd.isna(cat) else int(cat),
            "cat_priv_label": CAT.get(int(cat)) if pd.notna(cat) else None,
            "parceria_poder_publico": None if pd.isna(parc) else int(parc),
            "tp_parceria": None if pd.isna(tp_parc) else int(tp_parc),
            "tipo_rede_jv": tipo,
            "mat_total_censo_2025": int(mats.get("mat_total") or 0),
            "mat_infantil_censo_2025": int(mats.get("mat_infantil") or 0),
        })

    conv = [e for e in escolas if e["tipo_rede_jv"] == "conveniada"]
    diretas = [e for e in escolas if e["tipo_rede_jv"] == "municipal_direta"]
    outras = [e for e in escolas if e["tipo_rede_jv"] == "outra"]

    payload = {
        "metadata": {
            "titulo": "Rede municipal Joinville — unidades do sistema de matriculas (SED) x Censo Escolar",
            "fonte_sed": "Unidades escolares (sistema de matriculas) — export 2026-07-30",
            "fonte_censo": "INEP Censo Escolar 2025 (Tabela_Escola + Tabela_Matricula)",
            "municipio": "Joinville",
            "cod_mun": "4209102",
            "criterio_conveniada": (
                "INEP presente na base SED de unidades validas da rede municipal "
                "e com TP_DEPENDENCIA=Privada no Censo Escolar 2025."
            ),
            "criterio_rede_municipal_painel": (
                "Dependencia Municipal no Censo + escolas privadas com convenio "
                "identificadas na base SED (em geral CEIs)."
            ),
            "gerado_em": datetime.datetime.now().strftime("%Y-%m-%d"),
            "total_unidades_sed": len(escolas),
            "municipais_diretas": len(diretas),
            "conveniadas": len(conv),
            "outras_ou_sem_censo": len(outras),
            "mat_conveniadas_censo_2025": int(sum(e["mat_total_censo_2025"] for e in conv)),
            "mat_infantil_conveniadas_censo_2025": int(sum(e["mat_infantil_censo_2025"] for e in conv)),
        },
        "escolas": sorted(escolas, key=lambda e: (e["tipo_rede_jv"], e["nome_sed"] or "")),
        "conveniadas": sorted(conv, key=lambda e: e["nome_sed"] or ""),
    }

    # JSON painel
    out_json = PAINEL / "4_1_conveniadas_sed.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print("OK", out_json, "conv=", len(conv), "mat=", payload["metadata"]["mat_conveniadas_censo_2025"])

    # CSVs legiveis
    pd.DataFrame(escolas).to_csv(OUT_DIR / "lista_ineps_rede_municipal_sed.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(conv).to_csv(OUT_DIR / "lista_ineps_conveniadas_provaveis.csv", index=False, encoding="utf-8-sig")

    # Atualiza metadata do acesso municipal
    for fname in ("4_1_acesso_municipal.json", "4_1_acesso_matriculas.json"):
        path = PAINEL / fname
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        meta = data.setdefault("metadata", {})
        meta["escolas_conveniadas"] = len(conv)
        meta["mat_conveniadas"] = payload["metadata"]["mat_conveniadas_censo_2025"]
        meta["nota_conveniadas"] = (
            "Conveniadas = INEPs da base SED (sistema de matriculas) com dependencia Privada no Censo. "
            "Em 2025: %d escolas (quase todas CEIs), %d matriculas no Censo. "
            "KPIs principais desta secao = dependencia Municipal (rede direta)."
            % (len(conv), payload["metadata"]["mat_conveniadas_censo_2025"])
        )
        meta["fonte_conveniadas"] = "SED Unidades escolares 2026-07-30 x Censo Escolar 2025"
        # tambem no ano corrente da serie
        st = data.get("serie_temporal", {}).get("2025")
        if st is not None:
            st["escolas_conveniadas"] = len(conv)
            st["mat_conveniadas"] = payload["metadata"]["mat_conveniadas_censo_2025"]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        print("updated", fname)

    print("Prefixos conv:", pd.Series([e["prefixo"] for e in conv]).value_counts().to_dict())
    print("Classes conv:", pd.Series([e["classe"] for e in conv]).value_counts().to_dict())


if __name__ == "__main__":
    main()
