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


def load_estimativa_ibge(path):
    """Le arquivo oficial POPYYYY_*.xls e retorna populacao de Joinville."""
    xl = pd.ExcelFile(path)
    sheet = xl.sheet_names[1]
    df = pd.read_excel(path, sheet_name=sheet, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    nome_col = [c for c in df.columns if "NOME" in c.upper()][0]
    pop_col = [c for c in df.columns if "POPULA" in c.upper()][0]
    uf_col = [c for c in df.columns if c.upper() == "UF"][0]
    cod_uf = [c for c in df.columns if "COD. UF" in c.upper()][0]
    cod_mun = [c for c in df.columns if "COD. MUNIC" in c.upper()][0]
    m = df[
        (df[nome_col].astype(str).str.contains("Joinville", case=False, na=False))
        & (df[uf_col].astype(str) == "SC")
    ]
    if m.empty:
        raise SystemExit(f"Joinville nao encontrado em {path}")
    r = m.iloc[0]
    code = f"{int(r[cod_uf]):02d}{int(r[cod_mun]):05d}"
    if code != CO_MUN:
        raise SystemExit(f"Codigo inesperado em {path}: {code}")
    return si(r[pop_col])


def scale_faixas_largest_remainder(base_faixas, total_base, total_target):
    """Escala faixas mantendo soma = total_target (metodo do maior resto)."""
    if not total_base:
        return [0] * len(base_faixas)
    # Mesmo total: preserva valores do Censo (evita drift de ponto flutuante)
    if total_target == total_base:
        return [f["valor"] for f in base_faixas]
    raw = [(f["valor"] / total_base) * total_target for f in base_faixas]
    floors = [int(x) for x in raw]
    rem = total_target - sum(floors)
    order = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]), reverse=True)
    for i in order[: max(rem, 0)]:
        floors[i] += 1
    if rem < 0:
        order_neg = sorted(range(len(raw)), key=lambda i: (raw[i] - floors[i]))
        for i in order_neg[: -rem]:
            if floors[i] > 0:
                floors[i] -= 1
    return floors


def build_projecoes_pme(faixas_pme, pop_2024, pop_2025):
    base = faixas_pme["faixas"]
    total_2022 = faixas_pme["total_referencia"]
    # 2023: IBGE nao publicou estimativa propria; usou populacoes do Censo 2022 no FPM
    totais = {
        "2022": {"valor": total_2022, "tipo": "censo", "fonte": "SIDRA 9514 (Censo 2022)"},
        "2023": {
            "valor": total_2022,
            "tipo": "censo_fpm",
            "fonte": "IBGE — em 2023 publicou no DOU as populacoes do Censo 2022 (sem estimativa intercensitaria propria)",
        },
        "2024": {
            "valor": pop_2024,
            "tipo": "estimativa",
            "fonte": "IBGE Estimativas da populacao residente — 1o jul/2024 (POP2024_20241230.xls)",
        },
        "2025": {
            "valor": pop_2025,
            "tipo": "estimativa",
            "fonte": "IBGE Estimativas da populacao residente — 1o jul/2025 (POP2025_20260113.xls)",
        },
    }

    por_ano = {}
    for ano, info in totais.items():
        vals = scale_faixas_largest_remainder(base, total_2022, info["valor"])
        faixas = []
        for f, v in zip(base, vals):
            faixas.append({
                "key": f["key"],
                "label": f["label"],
                "valor": v,
                "pct": round(100.0 * v / info["valor"], 1) if info["valor"] else None,
            })
        por_ano[ano] = {
            "total": info["valor"],
            "tipo": info["tipo"],
            "fonte_total": info["fonte"],
            "faixas": faixas,
        }

    metodologia = {
        "titulo": "Projecao das faixas educacionais 2022-2025",
        "metodo": (
            "Estrutura etaria constante do Censo 2022 (SIDRA 9514), "
            "escalada pelo total populacional oficial de cada ano."
        ),
        "formula": "faixa_t = (faixa_2022 / pop_2022) x pop_total_t",
        "arredondamento": "Maior resto (largest remainder), para a soma das faixas fechar no total do ano.",
        "limitacao": (
            "O IBGE nao publica projecao por idade no nivel municipal. "
            "Esta serie assume que a composicao etaria de 2022 se mantem; "
            "apenas o total acompanha as Estimativas IBGE (2024 e 2025)."
        ),
        "ancoras": [
            {"ano": "2022", "total": total_2022, "fonte": totais["2022"]["fonte"]},
            {"ano": "2023", "total": total_2022, "fonte": totais["2023"]["fonte"]},
            {"ano": "2024", "total": pop_2024, "fonte": totais["2024"]["fonte"]},
            {"ano": "2025", "total": pop_2025, "fonte": totais["2025"]["fonte"]},
        ],
        "urls": [
            "https://sidra.ibge.gov.br/tabela/9514",
            "https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html",
        ],
    }
    return {"metodologia": metodologia, "por_ano": por_ano}


def main():
    f_demo = os.path.join(CENSO_DIR, "Agregados_por_municipios_demografia_BR.xlsx")
    f_alf = os.path.join(CENSO_DIR, "Agregados_por_municipios_alfabetizacao_BR.xlsx")
    f_9514 = os.path.join(CENSO_DIR, "tabela9514.xlsx")
    f_pop2024 = os.path.join(CENSO_DIR, "POP2024_20241230.xls")
    f_pop2025 = os.path.join(CENSO_DIR, "POP2025_20260113.xls")

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
    pop_2024 = load_estimativa_ibge(f_pop2024)
    pop_2025 = load_estimativa_ibge(f_pop2025)
    projecoes_pme = build_projecoes_pme(faixas_pme, pop_2024, pop_2025)

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
            "fonte": "IBGE - Censo Demografico 2022 + Estimativas da populacao",
            "arquivos": [
                "Agregados_por_municipios_demografia_BR.xlsx",
                "Agregados_por_municipios_alfabetizacao_BR.xlsx",
                "tabela9514.xlsx",
                "POP2024_20241230.xls",
                "POP2025_20260113.xls",
            ],
            "municipio": "Joinville",
            "uf": "SC",
            "co_municipio": CO_MUN,
            "ano_referencia": 2022,
            "nota_faixas": (
                "Faixas educacionais (0-3, 6-14, 15-17, 18-24, 25+) vêm da SIDRA 9514 "
                "(idade simples, Resultados do Universo). "
                "Projecoes 2023-2025: estrutura 2022 x totais oficiais IBGE. "
                "Grupos quinquenais vêm dos Agregados por Municipios."
            ),
            "gerado_em": pd.Timestamp.now().isoformat(),
        },
        "populacao": {
            "total": pop_total,
            "masculino": masc,
            "feminino": fem,
            "faixas": faixas,
            "faixas_pme": faixas_pme,
            "projecoes_pme": projecoes_pme,
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
    print("  Estimativa 2024:", pop_2024)
    print("  Estimativa 2025:", pop_2025)
    for f in faixas_pme["faixas"]:
        print(f"  {f['label']}: {f['valor']:,} ({f['pct']}%)")
    for ano in ["2022", "2023", "2024", "2025"]:
        y = projecoes_pme["por_ano"][ano]
        print(f"  [{ano}] total={y['total']:,} | 6-14={next(x['valor'] for x in y['faixas'] if x['key']=='6_14'):,}")
    print("  Alfabetizacao 15+:", alfabetizacao["taxa_alfabetizacao_15_mais"], "%")


if __name__ == "__main__":
    main()
