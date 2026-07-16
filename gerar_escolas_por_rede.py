# -*- coding: utf-8 -*-
"""Gera escolas_{rede}.json para o mapa territorial reagir ao seletor de dependencia."""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import pandas as pd

from etl_utils_rede import COLS_PARCERIA, mask_conveniada_municipal, mask_municipal_direta

BASE = os.path.dirname(os.path.abspath(__file__))
MICRO = os.path.join(
    BASE,
    "00. Bases de Dados",
    "01. Acesso e Matrículas (Censo Escolar_2010_2025)",
    "01. extrações_2010_2025",
)
PAINEL = os.path.join(BASE, "painel", "dados")
COORDS = os.path.join(BASE, "..", "..", "0000. Bases", "02. Coordenadas", "Escolas_INEP_Coordenadas.xlsx")
CO_MUN = 4209102
LOC = {1: "Urbana", 2: "Rural", "1": "Urbana", "2": "Rural"}


def si(v):
    return 0 if pd.isna(v) else int(v)


def load_coords():
    coords = {}
    if not os.path.exists(COORDS):
        print("AVISO: sem arquivo de coordenadas SED")
        return coords
    cdf = pd.read_excel(COORDS)
    for _, row in cdf.iterrows():
        try:
            inep = str(int(row["INEP"]))
        except Exception:
            continue
        s = row.get("Coordenada")
        if pd.isna(s):
            continue
        parts = [p.strip() for p in str(s).split(",")]
        if len(parts) != 2:
            continue
        try:
            lng, lat = float(parts[0]), float(parts[1])
            if abs(lat) <= 90 and abs(lng) <= 180:
                coords[inep] = (round(lat, 6), round(lng, 6), "SED_Joinville")
        except Exception:
            pass
    print(f"coords SED: {len(coords)}")
    return coords


def _valid_coord(lat, lng):
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lng)):
        return None
    if lat == 0 and lng == 0:
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return round(lat, 6), round(lng, 6)


def attach_coords(e, row, coords):
    inep = e["inep"]
    if inep in coords:
        lat, lng, fonte = coords[inep]
        pair = _valid_coord(lat, lng)
        if pair:
            e["lat"], e["lng"] = pair
            e["coord_fonte"] = fonte
            return
    pair = _valid_coord(row.get("LATITUDE"), row.get("LONGITUDE"))
    if pair:
        e["lat"], e["lng"] = pair
        e["coord_fonte"] = "Censo"


def load_matriculas():
    f_mat = os.path.join(MICRO, "Tabela_Matricula_2025.csv")
    if not os.path.exists(f_mat):
        print("AVISO: sem Tabela_Matricula_2025.csv")
        return {}
    cols = [
        "CO_ENTIDADE", "QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_FUND", "QT_MAT_FUND_AI",
        "QT_MAT_FUND_AF", "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_ESP", "QT_MAT_BAS_N",
    ]
    h = pd.read_csv(f_mat, sep=";", encoding="latin-1", nrows=0)
    use = [c for c in cols if c in h.columns]
    df = pd.read_csv(f_mat, sep=";", encoding="latin-1", usecols=use)
    out = {}
    for _, row in df.iterrows():
        eid = str(int(row["CO_ENTIDADE"]))
        out[eid] = {
            "mat_total": si(row.get("QT_MAT_BAS", 0)),
            "mat_infantil": si(row.get("QT_MAT_INF", 0)),
            "mat_fund": si(row.get("QT_MAT_FUND", 0)),
            "mat_fund_ai": si(row.get("QT_MAT_FUND_AI", 0)),
            "mat_fund_af": si(row.get("QT_MAT_FUND_AF", 0)),
            "mat_medio": si(row.get("QT_MAT_MED", 0)),
            "mat_eja": si(row.get("QT_MAT_EJA", 0)),
            "mat_especial": si(row.get("QT_MAT_ESP", 0)),
            "mat_noturno": si(row.get("QT_MAT_BAS_N", 0)),
        }
    print(f"matriculas: {len(out)} escolas")
    return out


def row_to_escola(row, tipo_rede, coords, mats):
    inep = str(int(row["CO_ENTIDADE"]))
    e = {
        "inep": inep,
        "nome": str(row["NO_ENTIDADE"]),
        "municipio": "Joinville",
        "cod_mun": str(CO_MUN),
        "cre": "",
        "loc": LOC.get(row.get("TP_LOCALIZACAO"), str(row.get("TP_LOCALIZACAO"))),
        "tipo_rede": tipo_rede,
        "mat_total": 0,
        "mat_infantil": 0,
        "mat_fund": 0,
        "mat_fund_ai": 0,
        "mat_fund_af": 0,
        "mat_medio": 0,
        "mat_eja": 0,
        "mat_especial": 0,
        "mat_noturno": 0,
    }
    if inep in mats:
        e.update(mats[inep])
    attach_coords(e, row, coords)
    return e


def save(rede, escolas, fname):
    n_coord = sum(1 for e in escolas if e.get("lat"))
    mat = sum(e.get("mat_total") or 0 for e in escolas)
    payload = {
        "metadata": {
            "fonte": "Censo Escolar 2025 (Tabela_Escola)",
            "municipio": "Joinville",
            "uf": "SC",
            "rede": rede,
            "gerado_em": pd.Timestamp.now().isoformat(),
            "total_escolas": len(escolas),
            "com_coordenadas": n_coord,
        },
        "escolas": escolas,
    }
    out = os.path.join(PAINEL, fname)
    with open(out, "w", encoding="utf-8") as f:
        # allow_nan=False evita NaN invalido que quebra JSON.parse no browser
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    print(f"  {fname}: {len(escolas)} escolas | {n_coord} coords | mat={mat}")


def main():
    fpath = os.path.join(MICRO, "Tabela_Escola_2025.csv")
    if not os.path.exists(fpath):
        print("ERRO: nao encontrei", fpath)
        sys.exit(1)

    use = [
        "CO_ENTIDADE", "NO_ENTIDADE", "CO_MUNICIPIO", "NO_MUNICIPIO", "TP_DEPENDENCIA",
        "TP_SITUACAO_FUNCIONAMENTO", "TP_LOCALIZACAO", "LATITUDE", "LONGITUDE",
        "TP_CATEGORIA_ESCOLA_PRIVADA", "QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_FUND",
        "QT_MAT_FUND_AI", "QT_MAT_FUND_AF", "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_ESP",
        "QT_MAT_BAS_N",
    ] + COLS_PARCERIA
    h = pd.read_csv(fpath, sep=";", encoding="latin-1", nrows=0)
    cols = [c for c in use if c in h.columns]
    df = pd.read_csv(fpath, sep=";", encoding="latin-1", usecols=cols)
    df = df[(df["CO_MUNICIPIO"] == CO_MUN) & (df["TP_SITUACAO_FUNCIONAMENTO"] == 1)].copy()
    if "TP_CATEGORIA_ESCOLA_PRIVADA" in df.columns:
        df["TP_CATEGORIA_ESCOLA_PRIVADA"] = df["TP_CATEGORIA_ESCOLA_PRIVADA"].fillna(0)

    coords = load_coords()
    mats = load_matriculas()
    dep = pd.to_numeric(df["TP_DEPENDENCIA"], errors="coerce")
    cat = pd.to_numeric(df.get("TP_CATEGORIA_ESCOLA_PRIVADA"), errors="coerce")

    # municipal: manter arquivo rico existente; so gera se ausente
    mun_path = os.path.join(PAINEL, "escolas_municipais.json")
    if not os.path.exists(mun_path):
        mask = mask_municipal_direta(df) | mask_conveniada_municipal(df)
        mdir = mask_municipal_direta(df)
        escolas = []
        for idx, row in df[mask].iterrows():
            tipo = "direta" if bool(mdir.loc[idx]) else "conveniada"
            escolas.append(row_to_escola(row, tipo, coords, mats))
        save("municipal", escolas, "escolas_municipais.json")
    else:
        print("  escolas_municipais.json: mantido (arquivo rico existente)")

    packs = [
        ("estadual", dep == 2, "escolas_estadual.json"),
        ("federal", dep == 1, "escolas_federal.json"),
        ("filantropica", (dep == 4) & (cat == 4), "escolas_filantropica.json"),
        ("particular", (dep == 4) & (cat == 1), "escolas_particular.json"),
    ]
    for rede, mask, fname in packs:
        escolas = [row_to_escola(row, "direta", coords, mats) for _, row in df[mask].iterrows()]
        save(rede, escolas, fname)

    # compat antigo
    src = os.path.join(PAINEL, "escolas_municipais.json")
    dst = os.path.join(PAINEL, "escolas_estaduais.json")
    if os.path.exists(src):
        import shutil
        shutil.copy2(src, dst)
        print("  escolas_estaduais.json: copia de compat de municipal")


if __name__ == "__main__":
    main()
