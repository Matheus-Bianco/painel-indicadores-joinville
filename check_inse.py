# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import pandas as pd, os

BASE = r"c:\Users\mathe\OneDrive\Desktop\Trabalhos\02. Joinville\25. Painel de Indicadores Abertos Joinville\04. Produto 4_Indicadores Educacionais"
INSE = os.path.join(BASE, "00. Bases de Dados", "04. Desigualdades Educacionais (INSE)")

df = pd.read_excel(os.path.join(INSE, "INSE_2023_escolas.xlsx"), sheet_name="INSE_ESC_2023")
print(f"INSE 2023 Brasil: {len(df)} escolas")

rs = df[df["CO_UF"] == 43]
print(f"INSE 2023 RS: {len(rs)} escolas")

col_rede = "TP_TIPO_REDE"
for rede, nome in [(1, "Federal"), (2, "Estadual"), (3, "Municipal"), (4, "Privada")]:
    n = len(rs[rs[col_rede] == rede])
    print(f"  {nome} ({rede}): {n}")

est = rs[rs[col_rede] == 2]
print(f"\nEstaduais — Alunos respondentes:")
print(f"  Total: {int(est['QTD_ALUNOS_INSE'].sum())}")
print(f"  Media/escola: {est['QTD_ALUNOS_INSE'].mean():.0f}")
print(f"  Min: {est['QTD_ALUNOS_INSE'].min()}, Max: {est['QTD_ALUNOS_INSE'].max()}")

# Censo comparison
censo_dir = os.path.join(BASE, "00. Bases de Dados",
    "01. Acesso e Matrículas (Fonte Censo Escolar_Inep_2019_2025)",
    "01. extrações_2019_2025")
for f in os.listdir(censo_dir):
    if "Escola_2025" in f and f.endswith(".csv"):
        dc = pd.read_csv(os.path.join(censo_dir, f), sep=";", encoding="latin-1",
            usecols=["SG_UF", "TP_DEPENDENCIA", "TP_SITUACAO_FUNCIONAMENTO"])
        n_censo = len(dc[(dc["SG_UF"] == "RS") & (dc["TP_DEPENDENCIA"] == 2) & (dc["TP_SITUACAO_FUNCIONAMENTO"] == 1)])
        print(f"\nCenso 2025 RS Estaduais ativas: {n_censo}")
        print(f"Cobertura INSE 2023 / Censo: {len(est)}/{n_censo} = {len(est)/n_censo*100:.1f}%")
        print(f"Diferenca: {n_censo - len(est)} escolas sem INSE")

print("\n=== CONCLUSAO ===")
print("O INSE so cobre escolas cujos alunos fizeram o SAEB e responderam")
print("o questionario socioeconomico (minimo ~15 respondentes).")
print("Escolas sem turmas avaliadas pelo SAEB (ex: somente EI/EJA) nao tem INSE.")
