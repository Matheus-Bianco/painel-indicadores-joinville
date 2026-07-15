# -*- coding: utf-8 -*-
"""Classificacao de rede municipal Joinville -- direta vs conveniada.

Conveniada municipal (Censo / Fundeb):
  TP_DEPENDENCIA = 4 (privada)
  parceria/convenio com poder publico municipal (TP in {2, 3})
  exclui categoria particular (1) -- SENAI e similares ficam de fora

Campos 2022+: IN_PODER_PUBLICO_PARCERIA, TP_PODER_PUBLICO_PARCERIA
Legado (~2020): IN_CONVENIADA_PP, TP_CONVENIO_PODER_PUBLICO
  TP: 1=estadual, 2=municipal, 3=estadual e municipal
"""
from __future__ import annotations

import pandas as pd

COLS_PARCERIA = [
    "IN_PODER_PUBLICO_PARCERIA",
    "TP_PODER_PUBLICO_PARCERIA",
    "IN_CONVENIADA_PP",
    "TP_CONVENIO_PODER_PUBLICO",
    "TP_CATEGORIA_ESCOLA_PRIVADA",
]

CAT_PARTICULAR = 1


def _series_or_nan(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce")
    return pd.Series([pd.NA] * len(df), index=df.index)


def mask_parceria_municipal(df):
    tp_novo = _series_or_nan(df, "TP_PODER_PUBLICO_PARCERIA")
    tp_legado = _series_or_nan(df, "TP_CONVENIO_PODER_PUBLICO")
    tp = tp_novo.where(tp_novo.notna(), tp_legado)
    return tp.isin([2, 3])


def mask_conveniada_municipal(df):
    dep = _series_or_nan(df, "TP_DEPENDENCIA")
    cat = _series_or_nan(df, "TP_CATEGORIA_ESCOLA_PRIVADA")
    if "TP_CATEGORIA_ESCOLA_PRIVADA" not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    nao_particular = cat.notna() & (cat != CAT_PARTICULAR) & (cat != 0)
    return (dep == 4) & mask_parceria_municipal(df) & nao_particular


def mask_municipal_direta(df):
    dep = _series_or_nan(df, "TP_DEPENDENCIA")
    return dep == 3


def filtrar_conveniadas(df):
    return df[mask_conveniada_municipal(df)].copy()


def resumo_conveniadas(df, mat_col="QT_MAT_BAS"):
    conv = filtrar_conveniadas(df)
    mats = 0
    if mat_col in conv.columns and len(conv):
        mats = int(pd.to_numeric(conv[mat_col], errors="coerce").fillna(0).sum())
    ineps = []
    if "CO_ENTIDADE" in conv.columns:
        ineps = [str(int(x)) for x in conv["CO_ENTIDADE"].tolist()]
    return {
        "escolas_conveniadas": int(len(conv)),
        "mat_conveniadas": mats,
        "inep_conveniadas": ineps,
    }
