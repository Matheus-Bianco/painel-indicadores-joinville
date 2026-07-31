# -*- coding: utf-8 -*-
# ETL Censo Demografico IBGE 2022 - Joinville/SC
# Inclui faixas PME a partir da Tabela SIDRA 9514 (idade simples).
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


def load_idade_simples_9514(path):
    """Le SIDRA 9514 (export xlsx) e retorna dict idade_int -> populacao para Joinville."""
    raw = pd.read_excel(path, sheet_name="Tabela", header=None)
    headers = raw.iloc[5].tolist()
    row = raw[raw[0].astype(str) == CO_MUN]
    if len(row) == 0:
        raise SystemExit("Joinville nao encontrado na tabela 9514")
    r = row.iloc[0]
    by_label = {}
    for i, h in enumerate(headers):
        if h is None or (isinstance(h, float) and pd.isna(h)):
            continue
        by_label[str(h).strip()] = si(r[i])

    ages = {}
    if "Menos de 1 ano" in by_label:
        ages[0] = by_label["Menos de 1 ano"]
    for n in range(1, 100):
        key = "1 ano" if n == 1 else f"{n} anos"
        if key in by_label:
            ages[n] = by_label[key]
    total = by_label.get("Total", sum(ages.values()))
    return ages, total


def build_faixas_pme(ages, total_9514):
    def soma(a, b):
        return sum(ages.get(i, 0) for i in range(a, b + 1))

    f03 = soma(0, 3)
    f614 = soma(6, 14)
    f1517 = soma(15, 17)
    f1824 = soma(18, 24)
    f0_24 = soma(0, 24)
    f25 = total_9514 - f0_24
    pct = lambda v: round(100.0 * v / total_9514, 1) if total_9514 else None
    return {
        "fonte": "IBGE SIDRA Tabela 9514 — Censo Demografico 2022 (idade simples, Universo)",
        "total_referencia": total_9514,
        "nota": (
            "Faixas montadas por soma de idades simples (SIDRA 9514). "
            "O total da 9514 pode diferir ligeiramente dos Agregados por Municipios "
            "(revisoes do Universo). Percentuais usam o total da 9514."
        ),
        "faixas": [
            {"key": "0_3", "label": "0 a 3 anos", "valor": f03, "pct": pct(f03)},
            {"key": "6_14", "label": "6 a 14 anos", "valor": f614, "pct": pct(f614)},
            {"key": "15_17", "label": "15 a 17 anos", "valor": f1517, "pct": pct(f1517)},
            {"key": "18_24", "label": "18 a 24 anos", "valor": f1824, "pct": pct(f1824)},
            {"key": "25_mais", "label": "25 anos ou mais", "valor": f25, "pct": pct(f25)},
        ],
    }


def main():
    f_demo = os.path.join(CENSO_DIR, "Agregados_por_municipios_demografia_BR.xlsx")
    f_alf = os.path.join(CENSO_DIR, "Agregados_por_municipios_alfabetizacao_BR.xlsx")
    f_9514 = os.path.join(CENSO_DIR, "tabela9514.xlsx")

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

    ages_9514, total_9514 = load_idade_simples_9514(f_9514)
    faixas_pme = build_faixas_pme(ages_9514, total_9514)

    # Aproximacoes legadas (grupos quinquenais) — mantidas so para referencia
    approx = {
        "5_14": {
            "label": "5 a 14 anos (aprox. PME 6-14)",
            "valor": si(r["V01032"]) + si(r["V01033"]),
            "nota": "Aproximacao por grupos quinquenais. Preferir faixa 6-14 da SIDRA 9514.",
        },
        "15_24": {
            "label": "15 a 24 anos (aprox.)",
            "valor": si(r["V01034"]) + si(r["V01035"]),
            "nota": "Aproximacao. Preferir 15-17 e 18-24 da SIDRA 9514.",
        },
        "0_14": {
            "label": "0 a 14 anos",
            "valor": si(r["V01031"]) + si(r["V01032"]) + si(r["V01033"]),
            "nota": "Soma 0-4 + 5-9 + 10-14 (agregados).",
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
            "fonte": "IBGE - Censo Demografico 2022",
            "arquivos": [
                "Agregados_por_municipios_demografia_BR.xlsx",
                "Agregados_por_municipios_alfabetizacao_BR.xlsx",
                "tabela9514.xlsx",
            ],
            "municipio": "Joinville",
            "uf": "SC",
            "co_municipio": CO_MUN,
            "ano_referencia": 2022,
            "nota_faixas": (
                "Faixas educacionais (0-3, 6-14, 15-17, 18-24, 25+) vêm da SIDRA 9514 "
                "(idade simples, Resultados do Universo). "
                "Grupos quinquenais vêm dos Agregados por Municipios. "
                "Totais podem diferir ligeiramente entre as duas fontes."
            ),
            "gerado_em": pd.Timestamp.now().isoformat(),
        },
        "populacao": {
            "total": pop_total,
            "masculino": masc,
            "feminino": fem,
            "faixas": faixas,
            "faixas_pme": faixas_pme,
            "aproximacoes_pme": approx,
        },
        "alfabetizacao": alfabetizacao,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("Salvo:", OUT)
    print("  Pop total (agregados):", pop_total)
    print("  Pop total (9514):", total_9514)
    for f in faixas_pme["faixas"]:
        print(f"  {f['label']}: {f['valor']:,} ({f['pct']}%)")
    print("  Alfabetizacao 15+:", alfabetizacao["taxa_alfabetizacao_15_mais"], "%")


if __name__ == "__main__":
    main()
