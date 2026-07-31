# -*- coding: utf-8 -*-
"""ETL Censo da Educacao Superior - oferta em Joinville/SC (2017-2024).

Recorte: CO_MUNICIPIO == 4209102 nos arquivos CURSOS (oferta local).
Modalidade: Presencial / EAD / Total sempre separados.
"""
import sys
import io
import os
import json
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville"
SRC = os.path.join(BASE, "05. Ensino Superior", "03. Censo da Educação Superior")
OUT = os.path.join(
    BASE,
    "04. Produto 4_Indicadores Educacionais",
    "painel",
    "dados",
    "4_12_ensino_superior.json",
)
CO_MUN = 4209102
ANOS = list(range(2017, 2025))
CHUNK = 200_000

ORG_MAP = {
    1: "Universidade",
    2: "Centro Universitario",
    3: "Faculdade",
    4: "Instituto Federal",
    5: "Centro Federal (CEFET)",
}
CAT_MAP = {
    1: "Publica Federal",
    2: "Publica Estadual",
    3: "Publica Municipal",
    4: "Privada com fins lucrativos",
    5: "Privada sem fins lucrativos",
    6: "Privada - confessional",
    7: "Especial",
    8: "Privada comunitaria",
    9: "Privada confessional",
}

USECOLS_CURSOS = [
    "CO_MUNICIPIO", "CO_IES", "TP_MODALIDADE_ENSINO", "TP_REDE",
    "TP_ORGANIZACAO_ACADEMICA", "TP_CATEGORIA_ADMINISTRATIVA",
    "QT_MAT", "QT_ING", "QT_CONC",
    "QT_MAT_FEM", "QT_MAT_MASC",
    "QT_MAT_BRANCA", "QT_MAT_PRETA", "QT_MAT_PARDA",
    "QT_MAT_AMARELA", "QT_MAT_INDIGENA", "QT_MAT_CORND",
]


def si(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def modality_key(v):
    try:
        t = int(v)
    except (TypeError, ValueError):
        return None
    if t == 1:
        return "presencial"
    if t == 2:
        return "ead"
    return None


def empty_mod():
    return {"presencial": 0, "ead": 0, "total": 0}


def add_mod(dst, key, val):
    n = si(val)
    dst[key] = dst.get(key, 0) + n
    dst["total"] = dst.get("total", 0) + n


def ies_path(ano):
    if ano >= 2022:
        name = f"MICRODADOS_ED_SUP_IES_{ano}.CSV"
    else:
        name = f"MICRODADOS_CADASTRO_IES_{ano}.CSV"
    return os.path.join(SRC, name)


def cursos_path(ano):
    return os.path.join(SRC, f"MICRODADOS_CADASTRO_CURSOS_{ano}.CSV")


def load_ies(ano):
    path = ies_path(ano)
    usecols = ["CO_IES", "NO_IES", "SG_IES", "CO_MUNICIPIO_IES",
               "TP_ORGANIZACAO_ACADEMICA", "TP_CATEGORIA_ADMINISTRATIVA"]
    df = pd.read_csv(path, sep=";", encoding="latin-1", usecols=lambda c: c in usecols,
                     dtype=str, low_memory=False)
    df["CO_IES"] = df["CO_IES"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["CO_MUNICIPIO_IES"] = pd.to_numeric(df["CO_MUNICIPIO_IES"], errors="coerce")
    return df


def load_cursos_joinville(ano):
    path = cursos_path(ano)
    # descobrir colunas disponiveis
    header = pd.read_csv(path, sep=";", encoding="latin-1", nrows=0)
    cols = [c for c in USECOLS_CURSOS if c in header.columns]
    frames = []
    for chunk in pd.read_csv(
        path, sep=";", encoding="latin-1", usecols=cols,
        chunksize=CHUNK, low_memory=False,
    ):
        chunk["CO_MUNICIPIO"] = pd.to_numeric(chunk["CO_MUNICIPIO"], errors="coerce")
        sub = chunk[chunk["CO_MUNICIPIO"] == CO_MUN].copy()
        if len(sub):
            frames.append(sub)
    if not frames:
        return pd.DataFrame(columns=cols)
    df = pd.concat(frames, ignore_index=True)
    df["CO_IES"] = df["CO_IES"].astype(str).str.replace(r"\.0$", "", regex=True)
    for c in ["QT_MAT", "QT_ING", "QT_CONC", "QT_MAT_FEM", "QT_MAT_MASC",
              "QT_MAT_BRANCA", "QT_MAT_PRETA", "QT_MAT_PARDA",
              "QT_MAT_AMARELA", "QT_MAT_INDIGENA", "QT_MAT_CORND",
              "TP_MODALIDADE_ENSINO", "TP_REDE", "TP_ORGANIZACAO_ACADEMICA",
              "TP_CATEGORIA_ADMINISTRATIVA"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


def process_ano(ano):
    print(f"  [{ano}] lendo CURSOS...")
    cursos = load_cursos_joinville(ano)
    print(f"  [{ano}] {len(cursos)} linhas oferta Joinville")
    print(f"  [{ano}] lendo IES...")
    ies = load_ies(ano)
    ies_lookup = ies.set_index("CO_IES")

    sedes = ies[ies["CO_MUNICIPIO_IES"] == CO_MUN].copy()
    ies_sede = []
    for _, r in sedes.iterrows():
        ies_sede.append({
            "co_ies": str(r["CO_IES"]),
            "no_ies": str(r.get("NO_IES") or ""),
            "sg_ies": str(r.get("SG_IES") or "") if pd.notna(r.get("SG_IES")) else "",
            "categoria": CAT_MAP.get(si(r.get("TP_CATEGORIA_ADMINISTRATIVA")), "Outra"),
            "org": ORG_MAP.get(si(r.get("TP_ORGANIZACAO_ACADEMICA")), "Outra"),
        })
    ies_sede.sort(key=lambda x: x["no_ies"])

    mat = empty_mod()
    ing = empty_mod()
    conc = empty_mod()
    cursos_n = empty_mod()
    ies_por_mod = {"presencial": set(), "ead": set(), "total": set()}

    sexo = {
        "presencial": {"masculino": 0, "feminino": 0},
        "ead": {"masculino": 0, "feminino": 0},
        "total": {"masculino": 0, "feminino": 0},
    }
    raca = {
        "presencial": {"branca": 0, "preta": 0, "parda": 0, "amarela": 0, "indigena": 0, "nao_declarada": 0},
        "ead": {"branca": 0, "preta": 0, "parda": 0, "amarela": 0, "indigena": 0, "nao_declarada": 0},
        "total": {"branca": 0, "preta": 0, "parda": 0, "amarela": 0, "indigena": 0, "nao_declarada": 0},
    }

    por_rede = {
        "publica": {"mat": empty_mod(), "ing": empty_mod(), "conc": empty_mod(), "cursos": empty_mod()},
        "privada": {"mat": empty_mod(), "ing": empty_mod(), "conc": empty_mod(), "cursos": empty_mod()},
    }
    por_org = {}
    por_ies = {}

    for _, r in cursos.iterrows():
        mod = modality_key(r.get("TP_MODALIDADE_ENSINO"))
        if not mod:
            continue
        co = str(r["CO_IES"])
        m, i, c = si(r.get("QT_MAT")), si(r.get("QT_ING")), si(r.get("QT_CONC"))

        add_mod(mat, mod, m)
        add_mod(ing, mod, i)
        add_mod(conc, mod, c)
        add_mod(cursos_n, mod, 1)
        ies_por_mod[mod].add(co)
        ies_por_mod["total"].add(co)

        # perfil matrículas
        fem, masc = si(r.get("QT_MAT_FEM")), si(r.get("QT_MAT_MASC"))
        for bucket in (mod, "total"):
            sexo[bucket]["feminino"] += fem
            sexo[bucket]["masculino"] += masc
            raca[bucket]["branca"] += si(r.get("QT_MAT_BRANCA"))
            raca[bucket]["preta"] += si(r.get("QT_MAT_PRETA"))
            raca[bucket]["parda"] += si(r.get("QT_MAT_PARDA"))
            raca[bucket]["amarela"] += si(r.get("QT_MAT_AMARELA"))
            raca[bucket]["indigena"] += si(r.get("QT_MAT_INDIGENA"))
            raca[bucket]["nao_declarada"] += si(r.get("QT_MAT_CORND"))

        # rede
        rede_code = si(r.get("TP_REDE"))
        rede_key = "publica" if rede_code == 1 else "privada"
        add_mod(por_rede[rede_key]["mat"], mod, m)
        add_mod(por_rede[rede_key]["ing"], mod, i)
        add_mod(por_rede[rede_key]["conc"], mod, c)
        add_mod(por_rede[rede_key]["cursos"], mod, 1)

        # org academica
        org_code = si(r.get("TP_ORGANIZACAO_ACADEMICA"))
        org_label = ORG_MAP.get(org_code, "Outra")
        if org_label not in por_org:
            por_org[org_label] = {"mat": empty_mod(), "ing": empty_mod(), "conc": empty_mod(), "cursos": empty_mod()}
        add_mod(por_org[org_label]["mat"], mod, m)
        add_mod(por_org[org_label]["ing"], mod, i)
        add_mod(por_org[org_label]["conc"], mod, c)
        add_mod(por_org[org_label]["cursos"], mod, 1)

        # por IES
        if co not in por_ies:
            meta = ies_lookup.loc[co] if co in ies_lookup.index else None
            if meta is not None and isinstance(meta, pd.DataFrame):
                meta = meta.iloc[0]
            no_ies = str(meta["NO_IES"]) if meta is not None else co
            sg = ""
            if meta is not None and pd.notna(meta.get("SG_IES")):
                sg = str(meta["SG_IES"])
            cat = CAT_MAP.get(si(meta.get("TP_CATEGORIA_ADMINISTRATIVA")) if meta is not None else 0, "Outra")
            org = ORG_MAP.get(si(meta.get("TP_ORGANIZACAO_ACADEMICA")) if meta is not None else 0, "Outra")
            sede = bool(meta is not None and si(meta.get("CO_MUNICIPIO_IES")) == CO_MUN)
            por_ies[co] = {
                "co_ies": co,
                "no_ies": no_ies,
                "sg_ies": sg,
                "categoria": cat,
                "org": org,
                "sede_joinville": sede,
                "mat_pres": 0, "mat_ead": 0, "mat_total": 0,
                "ing_pres": 0, "ing_ead": 0, "ing_total": 0,
                "conc_pres": 0, "conc_ead": 0, "conc_total": 0,
                "cursos_pres": 0, "cursos_ead": 0, "cursos_total": 0,
            }
        row = por_ies[co]
        if mod == "presencial":
            row["mat_pres"] += m
            row["ing_pres"] += i
            row["conc_pres"] += c
            row["cursos_pres"] += 1
        else:
            row["mat_ead"] += m
            row["ing_ead"] += i
            row["conc_ead"] += c
            row["cursos_ead"] += 1
        row["mat_total"] += m
        row["ing_total"] += i
        row["conc_total"] += c
        row["cursos_total"] += 1

    por_ies_list = sorted(por_ies.values(), key=lambda x: -x["mat_total"])

    serie = {
        "ies_oferta": len(ies_por_mod["total"]),
        "ies_oferta_presencial": len(ies_por_mod["presencial"]),
        "ies_oferta_ead": len(ies_por_mod["ead"]),
        "ies_sede": len(ies_sede),
        "cursos": cursos_n,
        "mat": mat,
        "ing": ing,
        "conc": conc,
    }

    return {
        "serie": serie,
        "perfil": {"sexo": sexo, "raca": raca},
        "por_rede": por_rede,
        "por_org": por_org,
        "por_ies": por_ies_list,
        "ies_sede": ies_sede,
    }


def main():
    print("ETL Ensino Superior - Joinville (oferta municipal)")
    serie_temporal = {}
    perfil_alunos = {}
    por_rede = {}
    por_org_academica = {}
    por_ies = {}
    ies_sede_latest = []

    for ano in ANOS:
        y = str(ano)
        if not os.path.exists(cursos_path(ano)):
            print(f"  [{ano}] CURSOS ausente - pulando")
            continue
        if not os.path.exists(ies_path(ano)):
            print(f"  [{ano}] IES ausente - pulando")
            continue
        out = process_ano(ano)
        serie_temporal[y] = out["serie"]
        perfil_alunos[y] = out["perfil"]
        por_rede[y] = out["por_rede"]
        por_org_academica[y] = out["por_org"]
        por_ies[y] = out["por_ies"]
        ies_sede_latest = out["ies_sede"]
        s = out["serie"]
        print(
            f"  [{ano}] IES oferta={s['ies_oferta']} sede={s['ies_sede']} "
            f"MAT total={s['mat']['total']:,} pres={s['mat']['presencial']:,} ead={s['mat']['ead']:,}"
        )

    payload = {
        "metadata": {
            "titulo": "Ensino Superior - oferta em Joinville/SC",
            "fonte": "INEP - Censo da Educacao Superior",
            "recorte": "Oferta no municipio de Joinville (CO_MUNICIPIO)",
            "cod_mun": str(CO_MUN),
            "municipio": "Joinville",
            "anos": sorted(serie_temporal.keys()),
            "gerado_em": str(date.today()),
            "nota": (
                "Inclui polos/EAD de IES sediadas fora do municipio. "
                "Presencial e EAD sempre separados. "
                "ies_sede = instituicoes com reitoria/sede em Joinville."
            ),
        },
        "serie_temporal": serie_temporal,
        "perfil_alunos": perfil_alunos,
        "por_rede": por_rede,
        "por_org_academica": por_org_academica,
        "por_ies": por_ies,
        "ies_sede": ies_sede_latest,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
    print(f"OK ? {OUT}")
    print(f"  anos: {payload['metadata']['anos']}")
    if "2024" in serie_temporal:
        print(f"  2024 MAT: {serie_temporal['2024']['mat']}")


if __name__ == "__main__":
    main()
