# -*- coding: utf-8 -*-
"""Gera serie historica das conveniadas SED (4_1_conveniadas_serie.json)."""
from __future__ import annotations

import json
import os
import sys

import pandas as pd

# Importa loaders sem reexecutar wrap de stdout conflitante
import etl_censo_escolar as etl

OUT_DIR = etl.OUT_DIR
CO_MUN = etl.CO_MUN_JOINVILLE


def load_ineps():
    path = os.path.join(OUT_DIR, "4_1_conveniadas_sed.json")
    data = json.load(open(path, encoding="utf-8"))
    return sorted({str(e["inep"]) for e in data["conveniadas"]})


def filter_ineps(df, ineps):
    if df is None or len(df) == 0:
        return df
    s = df["CO_ENTIDADE"].map(lambda x: str(int(x)) if pd.notna(x) else "")
    return df[s.isin(ineps)].copy()


def serie_from_df(df_ano):
    si = etl.safe_int
    sc = etl.safe_col_sum
    if df_ano is None or len(df_ano) == 0:
        return {
            "total_escolas": 0, "mat_total": 0, "mat_infantil": 0, "mat_infantil_creche": 0,
            "mat_infantil_pre": 0, "mat_fundamental": 0, "mat_fund_ai": 0, "mat_fund_af": 0,
            "mat_medio": 0, "mat_eja": 0, "mat_especial": 0,
            "fx_0_3": 0, "fx_4_5": 0, "fx_6_10": 0, "fx_11_14": 0, "fx_15_17": 0, "fx_18_mais": 0,
            "mat_noturno": 0, "mat_noturno_fund": 0, "mat_noturno_medio": 0, "mat_noturno_eja": 0,
            "esp_total": 0, "esp_classes_comuns": 0, "esp_classes_exclusivas": 0,
            "esp_cc_inf": 0, "esp_cc_fund": 0, "esp_cc_med": 0, "esp_cc_eja": 0,
            "esp_ce_inf": 0, "esp_ce_fund": 0, "esp_ce_med": 0, "esp_ce_eja": 0,
            "esp_d": 0, "esp_dm": 0, "esp_dv": 0,
        }
    return {
        "total_escolas": int(df_ano["CO_ENTIDADE"].nunique()),
        "mat_total": si(df_ano["QT_MAT_BAS"].sum()) if "QT_MAT_BAS" in df_ano else 0,
        "mat_infantil": si(df_ano["QT_MAT_INF"].sum()) if "QT_MAT_INF" in df_ano else 0,
        "mat_infantil_creche": sc(df_ano, "QT_MAT_INF_CRE"),
        "mat_infantil_pre": sc(df_ano, "QT_MAT_INF_PRE"),
        "mat_fundamental": si(df_ano["QT_MAT_FUND"].sum()) if "QT_MAT_FUND" in df_ano else 0,
        "mat_fund_ai": si(df_ano["QT_MAT_FUND_AI"].sum()) if "QT_MAT_FUND_AI" in df_ano else 0,
        "mat_fund_af": si(df_ano["QT_MAT_FUND_AF"].sum()) if "QT_MAT_FUND_AF" in df_ano else 0,
        "mat_medio": si(df_ano["QT_MAT_MED"].sum()) if "QT_MAT_MED" in df_ano else 0,
        "mat_eja": si(df_ano["QT_MAT_EJA"].sum()) if "QT_MAT_EJA" in df_ano else 0,
        "mat_especial": sc(df_ano, "QT_MAT_ESP"),
        "fx_0_3": sc(df_ano, "QT_MAT_BAS_0_3"),
        "fx_4_5": sc(df_ano, "QT_MAT_BAS_4_5"),
        "fx_6_10": sc(df_ano, "QT_MAT_BAS_6_10"),
        "fx_11_14": sc(df_ano, "QT_MAT_BAS_11_14"),
        "fx_15_17": sc(df_ano, "QT_MAT_BAS_15_17"),
        "fx_18_mais": sc(df_ano, "QT_MAT_BAS_18_MAIS"),
        "mat_noturno": sc(df_ano, "QT_MAT_BAS_N"),
        "mat_noturno_fund": sc(df_ano, "QT_MAT_FUND_N"),
        "mat_noturno_medio": sc(df_ano, "QT_MAT_MED_N"),
        "mat_noturno_eja": sc(df_ano, "QT_MAT_EJA_N"),
        "esp_total": sc(df_ano, "QT_MAT_ESP"),
        "esp_classes_comuns": sc(df_ano, "QT_MAT_ESP_CC"),
        "esp_classes_exclusivas": sc(df_ano, "QT_MAT_ESP_CE"),
        "esp_cc_inf": sc(df_ano, "QT_MAT_ESP_CC_INF"),
        "esp_cc_fund": sc(df_ano, "QT_MAT_ESP_CC_FUND"),
        "esp_cc_med": sc(df_ano, "QT_MAT_ESP_CC_MED"),
        "esp_cc_eja": sc(df_ano, "QT_MAT_ESP_CC_EJA"),
        "esp_ce_inf": sc(df_ano, "QT_MAT_ESP_CE_INF"),
        "esp_ce_fund": sc(df_ano, "QT_MAT_ESP_CE_FUND"),
        "esp_ce_med": sc(df_ano, "QT_MAT_ESP_CE_MED"),
        "esp_ce_eja": sc(df_ano, "QT_MAT_ESP_CE_EJA"),
        "esp_d": sc(df_ano, "QT_MAT_ESP_D"),
        "esp_dm": sc(df_ano, "QT_MAT_ESP_DM"),
        "esp_dv": sc(df_ano, "QT_MAT_ESP_DV"),
    }


def perfil_from_df(df_ano):
    sc = etl.safe_col_sum
    return {
        "sexo": {"masculino": sc(df_ano, "QT_MAT_BAS_MASC"), "feminino": sc(df_ano, "QT_MAT_BAS_FEM")},
        "raca": {
            "branca": sc(df_ano, "QT_MAT_BAS_BRANCA"),
            "preta": sc(df_ano, "QT_MAT_BAS_PRETA"),
            "parda": sc(df_ano, "QT_MAT_BAS_PARDA"),
            "amarela": sc(df_ano, "QT_MAT_BAS_AMARELA"),
            "indigena": sc(df_ano, "QT_MAT_BAS_INDIGENA"),
            "nao_declarada": sc(df_ano, "QT_MAT_BAS_ND"),
        },
    }


def integral_from_df(df_ano):
    sc = etl.safe_col_sum
    if df_ano is None or len(df_ano) == 0:
        return None
    if "QT_MAT_FUND_INT" not in df_ano.columns or not df_ano["QT_MAT_FUND_INT"].notna().any():
        return None
    return {
        "fund_total": sc(df_ano, "QT_MAT_FUND_INT"),
        "fund_ai": sc(df_ano, "QT_MAT_FUND_AI_INT"),
        "fund_af": sc(df_ano, "QT_MAT_FUND_AF_INT"),
        "medio": sc(df_ano, "QT_MAT_MED_INT"),
        "infantil": sc(df_ano, "QT_MAT_INF_INT"),
    }


def main():
    sys.stdout.write("=== ETL serie conveniadas SED ===\n")
    sys.stdout.flush()
    ineps = load_ineps()
    sys.stdout.write("INEPs: %d\n" % len(ineps))
    sys.stdout.flush()

    serie_temporal = {}
    perfil_alunos = {}
    integral = {}
    escolas_por_ano = {}

    for ano in range(2010, 2025):
        try:
            df = etl.ler_microdados_ano(ano)
        except Exception as e:
            sys.stdout.write("  skip %s %s\n" % (ano, e))
            continue
        if df is None or len(df) == 0:
            continue
        if "CO_MUNICIPIO" in df.columns:
            df = df[df["CO_MUNICIPIO"] == CO_MUN]
        df = filter_ineps(df, ineps)
        key = str(ano)
        serie_temporal[key] = serie_from_df(df)
        perfil_alunos[key] = perfil_from_df(df)
        integ = integral_from_df(df)
        if integ:
            integral[key] = integ
        escolas_por_ano[key] = serie_temporal[key]["total_escolas"]
        sys.stdout.write("  %s: esc=%s mat=%s\n" % (ano, serie_temporal[key]["total_escolas"], serie_temporal[key]["mat_total"]))
        sys.stdout.flush()

    try:
        df25 = etl.ler_tabelas_2025()
        if "CO_MUNICIPIO" in df25.columns:
            df25 = df25[df25["CO_MUNICIPIO"] == CO_MUN]
        df25 = filter_ineps(df25, ineps)
        serie_temporal["2025"] = serie_from_df(df25)
        perfil_alunos["2025"] = perfil_from_df(df25)
        integ = integral_from_df(df25)
        if integ:
            integral["2025"] = integ
        escolas_por_ano["2025"] = serie_temporal["2025"]["total_escolas"]
        sys.stdout.write("  2025: esc=%s mat=%s\n" % (serie_temporal["2025"]["total_escolas"], serie_temporal["2025"]["mat_total"]))
    except Exception as e:
        sys.stdout.write("  2025 FAIL %s\n" % e)

    out = {
        "metadata": {
            "titulo": "Serie das escolas conveniadas SED (privadas no Censo)",
            "fonte": "INEP Censo Escolar + lista SED Unidades escolares",
            "municipio": "Joinville",
            "cod_mun": str(CO_MUN),
            "n_ineps_lista": len(ineps),
            "ineps": ineps,
            "anos": sorted(serie_temporal.keys()),
            "escolas_por_ano": escolas_por_ano,
            "gerado_em": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "nota": "Mesmos INEPs da base SED aplicados retrospectivamente em cada ano do Censo.",
        },
        "serie_temporal": serie_temporal,
        "perfil_alunos": perfil_alunos,
        "integral": integral,
    }
    path = os.path.join(OUT_DIR, "4_1_conveniadas_serie.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("OK %s anos=%d\n" % (path, len(serie_temporal)))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
