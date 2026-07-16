# -*- coding: utf-8 -*-
# ETL Censo Demografico IBGE 2022 - Joinville/SC
import sys
import io
import os
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import pandas as pd

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville"
CENSO_DIR = os.path.join(BASE, "01. Indicadores do Censo")
OUT = os.path.join(
    BASE,
    "04. Produto 4_Indicadores Educacionais",
    "painel",
    "dados",
    "4_11_censo_ibge_municipal.json",
)
CO_MUN = "4209102"

FAIXAS_DEMO = [
    ("0_4", "V01031", "0 a 4 anos"),
    ("5_9", "V01032", "5 a 9 anos"),
    ("10_14", "V01033", "10 a 14 anos"),
    ("15_19", "V01034", "15 a 19 anos"),
    ("20_24", "V01035", "20 a 24 anos"),
    ("25_29", "V01036", "25 a 29 anos"),
    ("30_39", "V01037", "30 a 39 anos"),
    ("40_49", "V01038", "40 a 49 anos"),
    ("50_59", "V01039", "50 a 59 anos"),
    ("60_69", "V01040", "60 a 69 anos"),
    ("70_mais", "V01041", "70 anos ou mais"),
]


def si(v):
    if pd.isna(v):
        return 0
    return int(v)


def main():
    f_demo = os.path.join(CENSO_DIR, "Agregados_por_municipios_demografia_BR.xlsx")
    f_alf = os.path.join(CENSO_DIR, "Agregados_por_municipios_alfabetizacao_BR.xlsx")

    demo = pd.read_excel(f_demo)
    demo["CD_MUN"] = demo["CD_MUN"].astype(str)
    row = demo[demo["CD_MUN"] == CO_MUN]
    if len(row) == 0:
        raise SystemExit("Joinville nao encontrado em demografia")
    r = row.iloc[0]

    faixas = []
    for key, col, label in FAIXAS_DEMO:
        faixas.append({"key": key, "label": label, "valor": si(r[col])})

    pop_total = si(r["V01006"])
    masc = si(r["V01007"])
    fem = si(r["V01008"])

    approx = {
        "5_14": {
            "label": "5 a 14 anos (aprox. PME 6-14)",
            "valor": si(r["V01032"]) + si(r["V01033"]),
            "nota": "Soma das faixas 5-9 e 10-14 do Censo 2022. O PME pede 6-14.",
        },
        "15_24": {
            "label": "15 a 24 anos (aprox. PME 15-17 + 18-24)",
            "valor": si(r["V01034"]) + si(r["V01035"]),
            "nota": "Soma das faixas 15-19 e 20-24. O PME pede 15-17 e 18-24 separados.",
        },
        "0_14": {
            "label": "0 a 14 anos",
            "valor": si(r["V01031"]) + si(r["V01032"]) + si(r["V01033"]),
            "nota": "Soma 0-4 + 5-9 + 10-14.",
        },
    }

    alf = pd.read_excel(f_alf)
    alf["CD_MUN"] = alf["CD_MUN"].astype(str)
    ra = alf[alf["CD_MUN"] == CO_MUN].iloc[0]
    alf_sim = si(ra["V00900"])
    alf_nao = si(ra["V00901"])
    alf_tot = alf_sim + alf_nao

    alfabetizacao = {
        "15_mais_alfabetizados": alf_sim,
        "15_mais_nao_alfabetizados": alf_nao,
        "15_mais_total": alf_tot,
        "taxa_alfabetizacao_15_mais": round(100.0 * alf_sim / alf_tot, 1) if alf_tot else None,
        "taxa_analfabetismo_15_mais": round(100.0 * alf_nao / alf_tot, 1) if alf_tot else None,
        "por_faixa": [
            {
                "label": "15 a 19 anos",
                "populacao": si(ra["V00644"]),
                "alfabetizados": si(ra["V00748"]),
            },
            {
                "label": "20 a 24 anos",
                "populacao": si(ra["V00645"]),
                "alfabetizados": si(ra["V00749"]),
            },
            {
                "label": "15 a 29 anos",
                "alfabetizados": si(ra["V00852"]),
                "nao_alfabetizados": si(ra["V00853"]),
            },
            {
                "label": "30 a 59 anos",
                "alfabetizados": si(ra["V00854"]),
                "nao_alfabetizados": si(ra["V00855"]),
            },
            {
                "label": "60 anos ou mais",
                "alfabetizados": si(ra["V00856"]),
                "nao_alfabetizados": si(ra["V00857"]),
            },
        ],
    }

    out = {
        "metadata": {
            "fonte": "IBGE - Censo Demografico 2022 (Agregados por Municipios)",
            "arquivos": [
                "Agregados_por_municipios_demografia_BR.xlsx",
                "Agregados_por_municipios_alfabetizacao_BR.xlsx",
            ],
            "municipio": "Joinville",
            "uf": "SC",
            "co_municipio": CO_MUN,
            "ano_referencia": 2022,
            "nota_faixas": (
                "As faixas etarias do Censo 2022 (0-4, 5-9, 10-14, 15-19, 20-24) "
                "nao coincidem com as faixas tipicas do PME (0-3, 4-5, 6-14, 15-17, 18-24). "
                "Nao ha estimativas anuais 2023/2024 nesta base. "
                "Nivel de escolaridade (instrucao) nao esta disponivel nestes arquivos - "
                "apenas alfabetizacao."
            ),
            "gerado_em": pd.Timestamp.now().isoformat(),
        },
        "populacao": {
            "total": pop_total,
            "masculino": masc,
            "feminino": fem,
            "faixas": faixas,
            "aproximacoes_pme": approx,
        },
        "alfabetizacao": alfabetizacao,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Salvo:", OUT)
    print("  Pop total:", pop_total)
    print("  Alfabetizacao 15+:", alfabetizacao["taxa_alfabetizacao_15_mais"], "%")


if __name__ == "__main__":
    main()
