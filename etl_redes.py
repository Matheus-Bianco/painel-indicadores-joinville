# -*- coding: utf-8 -*-
"""ETL Redes Joinville - consolida visao cross-dependencia a partir dos JSONs do painel.

Gera painel/dados/4_1_redes.json (sem reler microdados).
Fonte: 4_1_acesso_*.json + 4_5_docentes_*.json
Recorte: municipio de Joinville (4209102) - 5 dependencias.
"""
from __future__ import annotations

import datetime
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "painel", "dados")

REDE_FILES = {
    "Municipal": "municipal",
    "Estadual": "estadual",
    "Federal": "federal",
    "Filantropica": "filantropica",
    "Particular": "particular",
}
REDE_COLORS = {
    "Municipal": "#00897B",
    "Estadual": "#0D47A1",
    "Federal": "#7B1FA2",
    "Filantropica": "#6D4C41",
    "Particular": "#F57C00",
}


def load_json(name):
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        print("  [AVISO] ausente:", name)
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def safe_int(v):
    if v is None:
        return None
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def oferta_from_acesso(acesso, ano):
    empty = {"mat_diurno": None, "mat_noturno": None, "mat_integral": None}
    if not acesso:
        return empty
    st = (acesso.get("serie_temporal") or {}).get(ano) or {}
    turno = st.get("por_turno") or {}

    noturno = safe_int(turno.get("QT_MAT_BAS_N"))
    if noturno is None:
        noturno = safe_int(st.get("mat_noturno"))
    diurno = safe_int(turno.get("QT_MAT_BAS_D"))
    if diurno is None and st.get("mat_total") is not None and noturno is not None:
        diurno = max(0, safe_int(st["mat_total"]) - noturno)

    integ = (acesso.get("integral") or {}).get(ano) or {}
    if isinstance(integ, list):
        integ = {}
    parts = [integ.get(k) for k in ("fund_total", "medio", "infantil") if integ.get(k) is not None]
    mat_integral = safe_int(sum(parts)) if parts else None
    if mat_integral is None:
        parts2 = [integ.get(k) for k in ("fund_ai", "fund_af", "medio", "infantil") if integ.get(k) is not None]
        mat_integral = safe_int(sum(parts2)) if parts2 else None

    fund_n = safe_int(turno.get("QT_MAT_FUND_N"))
    if fund_n is None:
        fund_n = safe_int(st.get("mat_noturno_fund"))
    fund_d = safe_int(turno.get("QT_MAT_FUND_D"))
    if fund_d is None and st.get("mat_fundamental") is not None and fund_n is not None:
        fund_d = max(0, safe_int(st["mat_fundamental"]) - fund_n)

    med_n = safe_int(turno.get("QT_MAT_MED_N"))
    if med_n is None:
        med_n = safe_int(st.get("mat_noturno_medio") or st.get("mat_noturno_med"))
    med_d = safe_int(turno.get("QT_MAT_MED_D"))
    if med_d is None and st.get("mat_medio") is not None and med_n is not None:
        med_d = max(0, safe_int(st["mat_medio"]) - med_n)

    eja_n = safe_int(turno.get("QT_MAT_EJA_N"))
    if eja_n is None:
        eja_n = safe_int(st.get("mat_noturno_eja"))
    eja_d = safe_int(turno.get("QT_MAT_EJA_D"))
    if eja_d is None and st.get("mat_eja") is not None and eja_n is not None:
        eja_d = max(0, safe_int(st["mat_eja"]) - eja_n)

    inf_d = safe_int(turno.get("QT_MAT_INF_D"))
    inf_n = safe_int(turno.get("QT_MAT_INF_N")) or 0
    if inf_d is None and st.get("mat_infantil") is not None:
        inf_d = max(0, safe_int(st["mat_infantil"]) - (inf_n or 0))

    return {
        "mat_diurno": diurno,
        "mat_noturno": noturno,
        "mat_integral": mat_integral,
        "int_fund": safe_int(integ.get("fund_total")),
        "int_fund_ai": safe_int(integ.get("fund_ai")),
        "int_fund_af": safe_int(integ.get("fund_af")),
        "int_medio": safe_int(integ.get("medio")),
        "int_infantil": safe_int(integ.get("infantil")),
        "mat_diurno_fund": fund_d,
        "mat_noturno_fund": fund_n,
        "mat_diurno_medio": med_d,
        "mat_noturno_medio": med_n,
        "mat_diurno_eja": eja_d,
        "mat_noturno_eja": eja_n,
        "mat_diurno_infantil": inf_d,
        "mat_noturno_infantil": inf_n,
    }


def docentes_ano(doc, ano):
    if not doc:
        return None
    st = (doc.get("serie_temporal_total") or {}).get(ano) or {}
    return safe_int(st.get("QT_DOC_BAS"))


def row_from_serie(acesso, doc, ano):
    st = ((acesso or {}).get("serie_temporal") or {}).get(ano) or {}
    esc = st.get("total_escolas")
    if esc is None:
        esc = st.get("escolas")
    row = {
        "escolas": safe_int(esc),
        "mat_total": safe_int(st.get("mat_total")),
        "mat_infantil": safe_int(st.get("mat_infantil")),
        "mat_fundamental": safe_int(st.get("mat_fundamental")),
        "mat_fund_ai": safe_int(st.get("mat_fund_ai")),
        "mat_fund_af": safe_int(st.get("mat_fund_af")),
        "mat_medio": safe_int(st.get("mat_medio")),
        "mat_eja": safe_int(st.get("mat_eja")),
    }
    row["docentes"] = docentes_ano(doc, ano)
    row.update(oferta_from_acesso(acesso, ano))
    if row.get("mat_fund_ai") is not None:
        row["mat_diurno_fund_ai"] = row["mat_fund_ai"]
        row["mat_noturno_fund_ai"] = 0
    if row.get("mat_fund_af") is not None:
        row["mat_diurno_fund_af"] = row["mat_fund_af"]
        row["mat_noturno_fund_af"] = 0
    if row.get("docentes") and row.get("mat_total"):
        row["razao_ap"] = round(row["mat_total"] / row["docentes"], 1)
    else:
        row["razao_ap"] = None
    return row


def main():
    print("=== ETL Redes Joinville (consolidacao) ===")
    acesso_rede = {}
    doc_rede = {}
    anos_set = set()
    for label, key in REDE_FILES.items():
        acesso_rede[label] = load_json("4_1_acesso_%s.json" % key)
        doc_rede[label] = load_json("4_5_docentes_%s.json" % key)
        if acesso_rede[label] and acesso_rede[label].get("serie_temporal"):
            anos_set.update(acesso_rede[label]["serie_temporal"].keys())

    if not anos_set:
        raise SystemExit("Nenhum 4_1_acesso_*.json com serie_temporal encontrado")

    anos = sorted(anos_set)
    por_rede = {}
    for ano in anos:
        por_rede[ano] = {}
        for label in REDE_FILES:
            por_rede[ano][label] = row_from_serie(acesso_rede[label], doc_rede[label], ano)

    out = {
        "metadata": {
            "titulo": "Oferta educacional por dependencia administrativa - Joinville/SC",
            "fonte": "INEP - Censo Escolar da Educacao Basica",
            "abrangencia": "Municipio de Joinville (4209102) - 5 dependencias",
            "municipio": "Joinville",
            "cod_mun": "4209102",
            "uf": "SC",
            "anos": anos,
            "redes": list(REDE_FILES.keys()),
            "cores": REDE_COLORS,
            "nota": (
                "Agregado a partir dos JSONs do painel (serie_temporal por dependencia + docentes). "
                "Filantropica = privada cat_priv=4; Particular = privada cat_priv=1. "
                "Integral disponivel nos anos em que o Censo publica QT_MAT_*_INT."
            ),
            "gerado_em": datetime.datetime.now().strftime("%Y-%m-%d"),
        },
        "por_rede": por_rede,
    }

    out_path = os.path.join(OUT_DIR, "4_1_redes.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    size_kb = os.path.getsize(out_path) / 1024
    print("OK -> %s (%.1f KB)" % (out_path, size_kb))
    y = por_rede.get("2025") or por_rede[anos[-1]]
    for r, v in y.items():
        print(
            "  %s: esc=%s mat=%s doc=%s not=%s int=%s"
            % (r, v.get("escolas"), v.get("mat_total"), v.get("docentes"), v.get("mat_noturno"), v.get("mat_integral"))
        )


if __name__ == "__main__":
    main()
