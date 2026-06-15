# -*- coding: utf-8 -*-
"""
Exploração rápida dos microdados do Censo Escolar (INEP)
Objetivo: mapear colunas QT_MAT_*, TP_*, CO_* disponíveis em cada ano
para construir o ETL de harmonização.
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import os, glob

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais\00. Bases de Dados"
MICRO_DIR = os.path.join(BASE, "01. Acesso e Matrículas (Fonte Censo Escolar_Inep_2019_2025)", "01. extrações_2019_2025")

CO_UF_RS = 43

# ── 1. Listar arquivos de microdados ──
microdados = sorted(glob.glob(os.path.join(MICRO_DIR, "microdados_ed_basica_*.csv")))
tabelas_2025 = sorted(glob.glob(os.path.join(MICRO_DIR, "Tabela_*.csv")))

print("=" * 80)
print("MICRODADOS ENCONTRADOS:")
for f in microdados:
    size_mb = os.path.getsize(f) / 1024 / 1024
    print(f"  {os.path.basename(f):45s} ({size_mb:.0f} MB)")

print(f"\nTABELAS 2025:")
for f in tabelas_2025:
    size_mb = os.path.getsize(f) / 1024 / 1024
    print(f"  {os.path.basename(f):45s} ({size_mb:.0f} MB)")

# ── 2. Para cada ano, ler SOMENTE o header + primeiras linhas do RS ──
print("\n" + "=" * 80)
print("ANÁLISE DE COLUNAS POR ANO")
print("=" * 80)

for f in microdados:
    ano = os.path.basename(f).replace("microdados_ed_basica_", "").replace(".csv", "").replace(".CSV", "")
    
    # Ler só o header para pegar nomes das colunas
    df_header = pd.read_csv(f, sep=";", encoding="latin-1", nrows=0)
    all_cols = list(df_header.columns)
    
    # Filtrar colunas de interesse
    qt_mat = [c for c in all_cols if c.startswith("QT_MAT_")]
    qt_doc = [c for c in all_cols if c.startswith("QT_DOC_")]
    qt_tur = [c for c in all_cols if c.startswith("QT_TUR_")]
    in_cols = [c for c in all_cols if c.startswith("IN_")]
    tp_cols = [c for c in all_cols if c.startswith("TP_")]
    co_cols = [c for c in all_cols if c.startswith("CO_")]
    
    print(f"\n{'-' * 60}")
    print(f"ANO {ano} — {len(all_cols)} colunas totais")
    print(f"  QT_MAT_*: {len(qt_mat)}")
    print(f"  QT_DOC_*: {len(qt_doc)}")
    print(f"  QT_TUR_*: {len(qt_tur)}")
    print(f"  IN_*:     {len(in_cols)}")
    print(f"  TP_*:     {len(tp_cols)}")
    print(f"  CO_*:     {len(co_cols)}")

# -- 3. Analise detalhada do ANO MAIS RECENTE (2024) --
print("\n" + "=" * 80)
print("DETALHAMENTO 2024 — COLUNAS QT_MAT_*")
print("=" * 80)

f2024 = [f for f in microdados if "2024" in f][0]
df_header = pd.read_csv(f2024, sep=";", encoding="latin-1", nrows=0)
qt_mat = sorted([c for c in df_header.columns if c.startswith("QT_MAT_")])

for i, col in enumerate(qt_mat, 1):
    print(f"  {i:3d}. {col}")

# -- 4. Ler amostra do RS (2024) para verificar dados --
print("\n" + "=" * 80)
print("AMOSTRA RS 2024 — Colunas-chave")
print("=" * 80)

# Colunas essenciais para leitura parcial
use_cols = [
    "CO_UF", "CO_MUNICIPIO", "CO_ENTIDADE", "NO_ENTIDADE",
    "TP_DEPENDENCIA", "TP_LOCALIZACAO", "TP_SITUACAO_FUNCIONAMENTO",
    "QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_INF_CRE", "QT_MAT_INF_PRE",
    "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF",
    "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_ESP",
    "QT_MAT_BAS_MASC", "QT_MAT_BAS_FEM",
    "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_PRETA", "QT_MAT_BAS_PARDA",
    "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_ND",
    "QT_MAT_BAS_INT"
]

# Verificar quais colunas existem
all_cols_2024 = list(pd.read_csv(f2024, sep=";", encoding="latin-1", nrows=0).columns)
cols_presentes = [c for c in use_cols if c in all_cols_2024]
cols_ausentes = [c for c in use_cols if c not in all_cols_2024]

if cols_ausentes:
    print(f"AVISO: Colunas NAO encontradas em 2024: {cols_ausentes}")

# Ler apenas RS
df_rs = pd.read_csv(f2024, sep=";", encoding="latin-1", usecols=cols_presentes)
df_rs = df_rs[df_rs["CO_UF"] == CO_UF_RS]
df_rs = df_rs[df_rs["TP_SITUACAO_FUNCIONAMENTO"] == 1]  # Apenas ativas

print(f"\nEscolas ativas no RS (2024): {len(df_rs)}")
print(f"\nPor dependência administrativa:")
dep_map = {1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"}
for dep, nome in dep_map.items():
    n = len(df_rs[df_rs["TP_DEPENDENCIA"] == dep])
    mat = df_rs[df_rs["TP_DEPENDENCIA"] == dep]["QT_MAT_BAS"].sum()
    print(f"  {nome:12s}: {n:5d} escolas | {mat:>10,.0f} matrículas")

print(f"\nPor localização:")
loc_map = {1: "Urbana", 2: "Rural"}
for loc, nome in loc_map.items():
    n = len(df_rs[df_rs["TP_LOCALIZACAO"] == loc])
    mat = df_rs[df_rs["TP_LOCALIZACAO"] == loc]["QT_MAT_BAS"].sum()
    print(f"  {nome:8s}: {n:5d} escolas | {mat:>10,.0f} matrículas")

total_mat = df_rs["QT_MAT_BAS"].sum()
print(f"\nTOTAL GERAL RS 2024: {len(df_rs)} escolas | {total_mat:,.0f} matriculas")

# -- 5. Colunas presentes por ano para harmonizacao --
print("\n" + "=" * 80)
print("VERIFICAÇÃO DE HARMONIZAÇÃO — Colunas-chave em TODOS os anos")
print("=" * 80)

colunas_chave = [
    "QT_MAT_BAS", "QT_MAT_INF", "QT_MAT_INF_CRE", "QT_MAT_INF_PRE",
    "QT_MAT_FUND", "QT_MAT_FUND_AI", "QT_MAT_FUND_AF",
    "QT_MAT_MED", "QT_MAT_EJA", "QT_MAT_ESP",
    "QT_MAT_BAS_MASC", "QT_MAT_BAS_FEM",
    "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_PRETA", "QT_MAT_BAS_PARDA",
    "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_ND",
    "QT_MAT_BAS_INT",
    "TP_DEPENDENCIA", "TP_LOCALIZACAO", "CO_MUNICIPIO", "CO_ENTIDADE",
]

# Tabela de presença
presenca = {}
for f in microdados:
    ano = os.path.basename(f).split("_")[-1].replace(".csv", "").replace(".CSV", "")
    cols = list(pd.read_csv(f, sep=";", encoding="latin-1", nrows=0).columns)
    presenca[ano] = {c: c in cols for c in colunas_chave}

print(f"\n{'Coluna':35s}", end="")
for ano in sorted(presenca.keys()):
    print(f" {ano}", end="")
print()
print("-" * (35 + 6 * len(presenca)))

for col in colunas_chave:
    print(f"{col:35s}", end="")
    for ano in sorted(presenca.keys()):
        status = "  OK" if presenca[ano][col] else "  --"
        print(f" {status}", end="")
    print()

# -- 6. Verificar estrutura das Tabelas 2025 --
print("\n" + "=" * 80)
print("TABELAS 2025 — Headers")
print("=" * 80)

for f in tabelas_2025:
    nome = os.path.basename(f)
    df_h = pd.read_csv(f, sep=";", encoding="latin-1", nrows=0)
    print(f"\n{nome} — {len(df_h.columns)} colunas")
    # Mostrar colunas QT_MAT se existirem
    qt = [c for c in df_h.columns if c.startswith("QT_MAT")]
    if qt:
        print(f"  QT_MAT_*: {len(qt)} → primeiras 10: {qt[:10]}")
    else:
        print(f"  Primeiras 15 colunas: {list(df_h.columns[:15])}")

print("\nExploracao concluida!")
