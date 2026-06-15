"""
Gera planilha Excel com todos os dados por município do painel UNESCO RS.
Abas: Matrículas, Infraestrutura, SAEB
"""
import json
import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DADOS = os.path.join(BASE, 'painel', 'dados')
OUT = os.path.join(BASE, 'Dados_Municipios_RS_Painel.xlsx')

# ── 1. Matrículas ──
with open(os.path.join(DADOS, '4_1_acesso_estadual.json'), 'r', encoding='utf-8') as f:
    acesso = json.load(f)

lookup = acesso.get('lookup_municipios', {})
anos = sorted(acesso['serie_temporal'].keys())

rows = []
for ano in anos:
    mun_data = acesso.get('por_municipio', {}).get(ano, {})
    for cod, v in mun_data.items():
        mat_total = v.get('mat_total', 0)
        masc = v.get('masc', 0)
        fem = v.get('fem', 0)
        branca = v.get('branca', 0)
        preta = v.get('preta', 0)
        parda = v.get('parda', 0)
        amarela = v.get('amarela', 0)
        indigena = v.get('indigena', 0)
        nao_decl = v.get('nao_declarada', 0)
        noturno = v.get('mat_noturno', 0)
        esp_total = v.get('esp_total', 0)
        int_fund = v.get('int_fund_total', 0)
        rows.append({
            'Ano': int(ano),
            'Código IBGE': cod,
            'Município': lookup.get(cod, f'Cód. {cod}'),
            'Escolas': v.get('escolas', 0),
            'Matrículas Total': mat_total,
            'Ed. Infantil': v.get('mat_infantil', 0),
            'Fundamental': v.get('mat_fundamental', 0),
            'Fund. Anos Iniciais': v.get('mat_fund_ai', 0),
            'Fund. Anos Finais': v.get('mat_fund_af', 0),
            'Ens. Médio': v.get('mat_medio', 0),
            'EJA': v.get('mat_eja', 0),
            # ── Faixa Etária ──
            'Fx 0-3 anos': v.get('fx_0_3', 0),
            'Fx 4-5 anos': v.get('fx_4_5', 0),
            'Fx 6-10 anos': v.get('fx_6_10', 0),
            'Fx 11-14 anos': v.get('fx_11_14', 0),
            'Fx 15-17 anos': v.get('fx_15_17', 0),
            'Fx 18+ anos': v.get('fx_18_mais', 0),
            # ── Noturno ──
            'Mat. Noturno': noturno,
            '% Noturno': round(noturno / mat_total * 100, 1) if mat_total else 0,
            'Noturno Fund.': v.get('mat_noturno_fund', 0),
            'Noturno Médio': v.get('mat_noturno_med', 0),
            'Noturno EJA': v.get('mat_noturno_eja', 0),
            # ── Educação Especial ──
            'Ed. Especial Total': esp_total,
            'Ed. Esp. Classes Comuns': v.get('esp_cc', 0),
            'Ed. Esp. Classes Exclusivas': v.get('esp_ce', 0),
            '% Ed. Especial': round(esp_total / mat_total * 100, 1) if mat_total else 0,
            # ── Ed. Especial por Etapa (Classes Comuns) ──
            'Esp. CC Infantil': v.get('esp_cc_inf', 0),
            'Esp. CC Fundamental': v.get('esp_cc_fund', 0),
            'Esp. CC Médio': v.get('esp_cc_med', 0),
            'Esp. CC EJA': v.get('esp_cc_eja', 0),
            # ── Ed. Especial por Etapa (Classes Exclusivas) ──
            'Esp. CE Infantil': v.get('esp_ce_inf', 0),
            'Esp. CE Fundamental': v.get('esp_ce_fund', 0),
            'Esp. CE Médio': v.get('esp_ce_med', 0),
            'Esp. CE EJA': v.get('esp_ce_eja', 0),
            # ── Tipo de Deficiência ──
            'Def. Sensorial': v.get('esp_def', 0),
            'Def. Múltipla': v.get('esp_def_mult', 0),
            'Def. Visual': v.get('esp_def_visual', 0),
            # ── Educação Integral ──
            'Integral Fund. Total': int_fund,
            'Integral Fund. AI': v.get('int_fund_ai', 0),
            'Integral Fund. AF': v.get('int_fund_af', 0),
            'Integral Médio': v.get('int_medio', 0),
            'Integral Infantil': v.get('int_infantil', 0),
            '% Integral Fund.': round(int_fund / v.get('mat_fundamental', 1) * 100, 1) if v.get('mat_fundamental', 0) else 0,
            # ── Recorte por Sexo ──
            'Masculino': masc,
            'Feminino': fem,
            '% Masculino': round(masc / mat_total * 100, 1) if mat_total else 0,
            '% Feminino': round(fem / mat_total * 100, 1) if mat_total else 0,
            # ── Recorte por Raça/Cor ──
            'Branca': branca,
            'Preta': preta,
            'Parda': parda,
            'Amarela': amarela,
            'Indígena': indigena,
            'Não Declarada': nao_decl,
            '% Branca': round(branca / mat_total * 100, 1) if mat_total else 0,
            '% Preta': round(preta / mat_total * 100, 1) if mat_total else 0,
            '% Parda': round(parda / mat_total * 100, 1) if mat_total else 0,
            '% Amarela': round(amarela / mat_total * 100, 1) if mat_total else 0,
            '% Indígena': round(indigena / mat_total * 100, 1) if mat_total else 0,
            '% Não Declarada': round(nao_decl / mat_total * 100, 1) if mat_total else 0,
            # ── Zona de Residência ──
            'ZR Urbana': v.get('zr_urbana', 0),
            'ZR Rural': v.get('zr_rural', 0),
            # ── Localização Diferenciada ──
            'Esc. Terra Indígena': v.get('locdif_terra_indigena_esc', 0),
            'Mat. Terra Indígena': v.get('locdif_terra_indigena_mat', 0),
            'Esc. Quilombola': v.get('locdif_quilombola_esc', 0),
            'Mat. Quilombola': v.get('locdif_quilombola_mat', 0),
            'Esc. Assentamento': v.get('locdif_assentamento_esc', 0),
            'Mat. Assentamento': v.get('locdif_assentamento_mat', 0),
        })

df_mat = pd.DataFrame(rows)
if len(df_mat) > 0:
    df_mat = df_mat.sort_values(['Ano', 'Matrículas Total'], ascending=[True, False])

# ── 2. Série Temporal Estadual ──
rows_st = []
for ano in anos:
    st = acesso['serie_temporal'].get(ano, {})
    rows_st.append({
        'Ano': int(ano),
        'Total Escolas': st.get('total_escolas', st.get('escolas', 0)),
        'Matrículas Total': st.get('mat_total', 0),
        'Ed. Infantil': st.get('mat_infantil', 0),
        'Fundamental': st.get('mat_fundamental', 0),
        'Fund. Anos Iniciais': st.get('mat_fund_ai', 0),
        'Fund. Anos Finais': st.get('mat_fund_af', 0),
        'Ens. Médio': st.get('mat_medio', 0),
        'EJA': st.get('mat_eja', 0),
    })
df_st = pd.DataFrame(rows_st)

# ── 2b. Variação Anual ──
rows_var = []
for periodo, v in sorted(acesso.get('variacao_anual', {}).items()):
    rows_var.append({
        'Período': periodo,
        'Δ Escolas': v.get('total_escolas', 0),
        'Δ Matrículas Total': v.get('mat_total', 0),
        'Δ Ed. Infantil': v.get('mat_infantil', 0),
        'Δ Fundamental': v.get('mat_fundamental', 0),
        'Δ Fund. AI': v.get('mat_fund_ai', 0),
        'Δ Fund. AF': v.get('mat_fund_af', 0),
        'Δ Ens. Médio': v.get('mat_medio', 0),
        'Δ EJA': v.get('mat_eja', 0),
    })
df_var = pd.DataFrame(rows_var)

# ── 3. Infraestrutura ──
with open(os.path.join(DADOS, '4_5_infra_estadual.json'), 'r', encoding='utf-8') as f:
    infra = json.load(f)

labels = infra.get('labels', {})
infra_anos = sorted(infra.get('serie_temporal', {}).keys())
rows_infra = []
for ano in infra_anos:
    su = infra['serie_temporal'][ano]
    row = {'Ano': int(ano), 'Total Escolas': su.get('total_escolas', 0)}
    for ind_key, ind_data in su.get('indicadores', {}).items():
        label = labels.get(ind_key, ind_key)
        row[f'{label} (%)'] = round(ind_data.get('pct', 0), 1)
        row[f'{label} (n)'] = ind_data.get('n', 0)
    rows_infra.append(row)
df_infra = pd.DataFrame(rows_infra)

# ── 3b. Infraestrutura por Município (2024) ──
lookup_mun = acesso.get('lookup_municipios', {})
infra_mun = infra.get('por_municipio', {})
rows_infra_mun = []
for ano_infra, mun_data in sorted(infra_mun.items()):
    for cod, v in mun_data.items():
        row = {
            'Ano': int(ano_infra),
            'Codigo IBGE': cod,
            'Municipio': lookup_mun.get(cod, f'Cod. {cod}'),
            'Escolas': v.get('escolas', 0),
        }
        for ind_key, ind_data in v.get('indicadores', {}).items():
            label = labels.get(ind_key, ind_key)
            row[f'{label} (n)'] = ind_data.get('count', 0)
            row[f'{label} (%)'] = round(ind_data.get('pct', 0), 1)
        rows_infra_mun.append(row)
df_infra_mun = pd.DataFrame(rows_infra_mun)
if len(df_infra_mun) > 0:
    df_infra_mun = df_infra_mun.sort_values(['Ano', 'Municipio'])

# ── 4. Docentes ──
with open(os.path.join(DADOS, '4_5_docentes.json'), 'r', encoding='utf-8') as f:
    doc = json.load(f)

rows_doc = []
perfil = doc.get('perfil_2025', {})
if perfil:
    rows_doc.append({
        'Ano': 2025,
        'Total Docentes': perfil.get('total', 0),
        **{f'Sexo: {k}': v for k, v in perfil.get('por_sexo', {}).items()},
        **{f'Escolaridade: {k}': v for k, v in perfil.get('por_escolaridade', {}).items()},
        **{f'Faixa Etaria: {k}': v for k, v in perfil.get('por_faixa_etaria', {}).items()},
        **{f'Vinculo: {k}': v for k, v in perfil.get('por_vinculo', {}).items()},
    })
# Razão aluno/professor
razao = doc.get('razao_aluno_professor', {})
rows_razao = []
for ano, v in sorted(razao.items()):
    rows_razao.append({'Ano': int(ano), 'Razao Aluno-Professor': v.get('geral', 0)})
df_razao = pd.DataFrame(rows_razao)

# ── 4b. Docentes por Município (2025) ──
lookup_doc = doc.get('lookup_municipios', {})
rows_doc_mun = []
for cod, v in doc.get('por_municipio_2025', {}).items():
    rows_doc_mun.append({
        'Ano': 2025,
        'Codigo IBGE': cod,
        'Municipio': lookup_doc.get(cod, lookup_mun.get(cod, f'Cod. {cod}')),
        'Escolas': v.get('escolas', 0),
        'Docentes': v.get('docentes', 0),
    })
df_doc_mun = pd.DataFrame(rows_doc_mun)
if len(df_doc_mun) > 0:
    df_doc_mun = df_doc_mun.sort_values('Municipio')

# ── 5. SAEB ──
with open(os.path.join(DADOS, '4_6_saeb.json'), 'r', encoding='utf-8') as f:
    saeb = json.load(f)

rows_saeb = []
for ano, data in sorted(saeb.get('serie_temporal', {}).items()):
    row = {'Ano': int(ano), 'Escolas Total': data.get('n_escolas_total', 0)}
    for etapa in ['5EF', '9EF', 'EM']:
        e = data.get(etapa, {})
        if e:
            row[f'{etapa} - LP'] = e.get('media_lp')
            row[f'{etapa} - MT'] = e.get('media_mt')
            row[f'{etapa} - Escolas'] = e.get('n_escolas')
    rows_saeb.append(row)
df_saeb = pd.DataFrame(rows_saeb)

# ── 6. Perfil Alunos (Raça/Sexo) ──
perfil_alunos = acesso.get('perfil_alunos', {})
rows_perfil = []
for ano in sorted(perfil_alunos.keys()):
    p = perfil_alunos[ano]
    row = {'Ano': int(ano)}
    if 'raca' in p:
        for k, v in p['raca'].items():
            row[f'Raça: {k.replace("_"," ").title()}'] = v
    if 'sexo' in p:
        for k, v in p['sexo'].items():
            row[f'Sexo: {k.title()}'] = v
    rows_perfil.append(row)
df_perfil = pd.DataFrame(rows_perfil)

# ── WRITE EXCEL ──
# Novas redes (alem de Estadual)
REDES_EXTRA = {
    'municipal': 'Mun.',
    'federal': 'Fed.',
    'privada': 'Priv.',
    'filantropica': 'Fil.',
    'todas': 'Todas',
}


def gerar_df_matriculas_rede(rede_key, lookup):
    """Gera DataFrame de matriculas por municipio para uma rede."""
    fpath = os.path.join(DADOS, f'4_1_acesso_{rede_key}.json')
    if not os.path.exists(fpath):
        return pd.DataFrame(), pd.DataFrame()
    with open(fpath, 'r', encoding='utf-8') as f:
        d = json.load(f)
    lk = d.get('lookup_municipios', lookup)
    anos_r = sorted(d['serie_temporal'].keys())

    # Matriculas por municipio
    rows = []
    for ano in anos_r:
        mun_data = d.get('por_municipio', {}).get(ano, {})
        for cod, v in mun_data.items():
            mat_total = v.get('mat_total', 0)
            rows.append({
                'Ano': int(ano),
                'Código IBGE': cod,
                'Município': lk.get(cod, f'Cód. {cod}'),
                'Escolas': v.get('escolas', 0),
                'Matrículas Total': mat_total,
                'Ed. Infantil': v.get('mat_infantil', 0),
                'Fundamental': v.get('mat_fundamental', 0),
                'Fund. Anos Iniciais': v.get('mat_fund_ai', 0),
                'Fund. Anos Finais': v.get('mat_fund_af', 0),
                'Ens. Médio': v.get('mat_medio', 0),
                'EJA': v.get('mat_eja', 0),
            })
    df_m = pd.DataFrame(rows)
    if len(df_m) > 0:
        df_m = df_m.sort_values(['Ano', 'Matrículas Total'], ascending=[True, False])

    # Serie temporal
    rows_s = []
    for ano in anos_r:
        st = d['serie_temporal'].get(ano, {})
        rows_s.append({
            'Ano': int(ano),
            'Total Escolas': st.get('total_escolas', st.get('escolas', 0)),
            'Matrículas Total': st.get('mat_total', 0),
            'Ed. Infantil': st.get('mat_infantil', 0),
            'Fundamental': st.get('mat_fundamental', 0),
            'Fund. Anos Iniciais': st.get('mat_fund_ai', 0),
            'Fund. Anos Finais': st.get('mat_fund_af', 0),
            'Ens. Médio': st.get('mat_medio', 0),
            'EJA': st.get('mat_eja', 0),
        })
    df_s = pd.DataFrame(rows_s)
    return df_m, df_s


def gerar_df_infra_rede(rede_key, lookup):
    """Gera DataFrame de infra serie temporal para uma rede."""
    fpath = os.path.join(DADOS, f'4_5_infra_{rede_key}.json')
    if not os.path.exists(fpath):
        return pd.DataFrame(), pd.DataFrame()
    with open(fpath, 'r', encoding='utf-8') as f:
        d = json.load(f)
    lbs = d.get('labels', {})
    anos_i = sorted(d.get('serie_temporal', {}).keys())

    # Serie temporal
    rows = []
    for ano in anos_i:
        su = d['serie_temporal'][ano]
        row = {'Ano': int(ano), 'Total Escolas': su.get('total_escolas', 0)}
        for ind_key, ind_data in su.get('indicadores', {}).items():
            label = lbs.get(ind_key, ind_key)
            row[f'{label} (%)'] = round(ind_data.get('pct', 0), 1)
        rows.append(row)
    df_i = pd.DataFrame(rows)

    # Por municipio (ultimo ano)
    infra_mun = d.get('por_municipio', {})
    rows_im = []
    for ano_infra, mun_data in sorted(infra_mun.items()):
        for cod, v in mun_data.items():
            row = {
                'Ano': int(ano_infra),
                'Codigo IBGE': cod,
                'Municipio': lookup.get(cod, f'Cod. {cod}'),
                'Escolas': v.get('escolas', 0),
            }
            for ind_key, ind_data in v.get('indicadores', {}).items():
                label = lbs.get(ind_key, ind_key)
                row[f'{label} (%)'] = round(ind_data.get('pct', 0), 1)
            rows_im.append(row)
    df_im = pd.DataFrame(rows_im)
    if len(df_im) > 0:
        df_im = df_im.sort_values(['Ano', 'Municipio'])

    return df_i, df_im


OUT_V2 = os.path.join(BASE, 'Dados_Municipios_RS_Painel_v2.xlsx')

with pd.ExcelWriter(OUT_V2, engine='openpyxl') as writer:
    # ── Abas existentes (Rede Estadual) ──
    df_mat.to_excel(writer, sheet_name='Matriculas por Municipio', index=False)
    df_st.to_excel(writer, sheet_name='Serie Temporal Estadual', index=False)
    df_var.to_excel(writer, sheet_name='Variacao Anual', index=False)
    df_perfil.to_excel(writer, sheet_name='Perfil Alunos (Estadual)', index=False)
    df_infra.to_excel(writer, sheet_name='Infra (Serie Temporal)', index=False)
    df_infra_mun.to_excel(writer, sheet_name='Infra por Municipio', index=False)
    if rows_doc:
        pd.DataFrame(rows_doc).to_excel(writer, sheet_name='Perfil Docente (Estadual)', index=False)
    df_razao.to_excel(writer, sheet_name='Razao Aluno-Professor', index=False)
    df_doc_mun.to_excel(writer, sheet_name='Docentes por Municipio', index=False)
    df_saeb.to_excel(writer, sheet_name='SAEB', index=False)

    # ── Novas abas por rede ──
    for rede_key, rede_suffix in REDES_EXTRA.items():
        print(f'  Gerando abas para {rede_key}...')
        df_rm, df_rs = gerar_df_matriculas_rede(rede_key, lookup)
        df_ri, df_rim = gerar_df_infra_rede(rede_key, lookup)

        if len(df_rm) > 0:
            df_rm.to_excel(writer, sheet_name=f'Mat. {rede_suffix}', index=False)
        if len(df_rs) > 0:
            df_rs.to_excel(writer, sheet_name=f'Serie Temp. {rede_suffix}', index=False)
        if len(df_ri) > 0:
            df_ri.to_excel(writer, sheet_name=f'Infra {rede_suffix}', index=False)
        if len(df_rim) > 0:
            df_rim.to_excel(writer, sheet_name=f'Infra {rede_suffix} x Mun', index=False)

    # ── 7. Complexidade de Gestão (ICG) ──
    print('  Gerando abas ICG...')
    icg_path = os.path.join(DADOS, '4_8_icg.json')
    if os.path.exists(icg_path):
        with open(icg_path, 'r', encoding='utf-8') as f:
            icg = json.load(f)

        # 7a. ICG Série Temporal (nível estado)
        icg_anos = sorted(icg.get('serie_temporal', {}).keys())
        rows_icg_st = []
        for ano in icg_anos:
            s = icg['serie_temporal'][ano]
            row = {
                'Ano': int(ano),
                'Total Escolas': s.get('total_escolas', 0),
                'Nível Médio': s.get('nivel_medio', 0),
            }
            for n in range(1, 7):
                nk = f'nivel_{n}'
                row[f'Nível {n} (n)'] = s.get(nk, {}).get('count', 0)
                row[f'Nível {n} (%)'] = s.get(nk, {}).get('pct', 0)
            # Urbana / Rural
            urb = s.get('urbana', {})
            rur = s.get('rural', {})
            row['Urbana - Escolas'] = urb.get('total_escolas', 0)
            row['Urbana - Nível Médio'] = urb.get('nivel_medio', 0)
            row['Rural - Escolas'] = rur.get('total_escolas', 0)
            row['Rural - Nível Médio'] = rur.get('nivel_medio', 0)
            rows_icg_st.append(row)
        df_icg_st = pd.DataFrame(rows_icg_st)
        df_icg_st.to_excel(writer, sheet_name='ICG (Serie Temporal)', index=False)

        # 7b. ICG por Município
        icg_lookup = icg.get('lookup_municipios', {})
        rows_icg_mun = []
        for ano in icg_anos:
            mun_data = icg.get('por_municipio', {}).get(ano, {})
            for cod, v in mun_data.items():
                row = {
                    'Ano': int(ano),
                    'Código IBGE': cod,
                    'Município': icg_lookup.get(cod, lookup.get(cod, f'Cód. {cod}')),
                    'Total Escolas': v.get('total_escolas', 0),
                    'Nível Médio': v.get('nivel_medio', 0),
                }
                for n in range(1, 7):
                    nk = f'nivel_{n}'
                    row[f'Nível {n} (n)'] = v.get(nk, {}).get('count', 0)
                    row[f'Nível {n} (%)'] = v.get(nk, {}).get('pct', 0)
                rows_icg_mun.append(row)
        df_icg_mun = pd.DataFrame(rows_icg_mun)
        if len(df_icg_mun) > 0:
            df_icg_mun = df_icg_mun.sort_values(['Ano', 'Município'])
        df_icg_mun.to_excel(writer, sheet_name='ICG por Municipio', index=False)

        # 7c. ICG por rede (serie temporal)
        for rede_key, rede_suffix in REDES_EXTRA.items():
            icg_rede_path = os.path.join(DADOS, f'4_8_icg_{rede_key}.json')
            if not os.path.exists(icg_rede_path):
                continue
            with open(icg_rede_path, 'r', encoding='utf-8') as f:
                icg_r = json.load(f)
            icg_r_anos = sorted(icg_r.get('serie_temporal', {}).keys())
            rows_ir = []
            for ano in icg_r_anos:
                s = icg_r['serie_temporal'][ano]
                row = {
                    'Ano': int(ano),
                    'Total Escolas': s.get('total_escolas', 0),
                    'Nível Médio': s.get('nivel_medio', 0),
                }
                for n in range(1, 7):
                    nk = f'nivel_{n}'
                    row[f'Nível {n} (n)'] = s.get(nk, {}).get('count', 0)
                    row[f'Nível {n} (%)'] = s.get(nk, {}).get('pct', 0)
                rows_ir.append(row)
            df_ir = pd.DataFrame(rows_ir)
            if len(df_ir) > 0:
                df_ir.to_excel(writer, sheet_name=f'ICG {rede_suffix}', index=False)
    # ── 8. TDI (Distorção Idade-Série) ──
    print('  Gerando abas TDI...')
    tdi_path = os.path.join(DADOS, '4_10_tdi_estadual.json')
    if os.path.exists(tdi_path):
        with open(tdi_path, 'r', encoding='utf-8') as f:
            tdi = json.load(f)

        # 8a. TDI Série Temporal (nível estado)
        tdi_anos = sorted(tdi.get('serie_temporal', {}).keys())
        rows_tdi_st = []
        for ano in tdi_anos:
            s = tdi['serie_temporal'][ano]
            rows_tdi_st.append({
                'Ano': int(ano),
                'TDI Fundamental (%)': s.get('tdi_fund'),
                'TDI Anos Iniciais (%)': s.get('tdi_ai'),
                'TDI Anos Finais (%)': s.get('tdi_af'),
                'TDI Ensino Médio (%)': s.get('tdi_med'),
                'Escolas com Dados': s.get('n_escolas', 0),
            })
        df_tdi_st = pd.DataFrame(rows_tdi_st)
        df_tdi_st.to_excel(writer, sheet_name='TDI (Serie Temporal)', index=False)

        # 8b. TDI por Município
        tdi_lookup = tdi.get('lookup_municipios', {})
        rows_tdi_mun = []
        for ano in tdi_anos:
            mun_data = tdi.get('por_municipio', {}).get(ano, {})
            for cod, v in mun_data.items():
                rows_tdi_mun.append({
                    'Ano': int(ano),
                    'Código IBGE': cod,
                    'Município': tdi_lookup.get(cod, lookup.get(cod, f'Cód. {cod}')),
                    'TDI Fundamental (%)': v.get('tdi_fund'),
                    'TDI Anos Iniciais (%)': v.get('tdi_ai'),
                    'TDI Anos Finais (%)': v.get('tdi_af'),
                    'TDI Ensino Médio (%)': v.get('tdi_med'),
                    'Escolas': v.get('n_escolas', 0),
                })
        df_tdi_mun = pd.DataFrame(rows_tdi_mun)
        if len(df_tdi_mun) > 0:
            df_tdi_mun = df_tdi_mun.sort_values(['Ano', 'Município'])
        df_tdi_mun.to_excel(writer, sheet_name='TDI por Municipio', index=False)

        # 8c. TDI por rede (serie temporal)
        for rede_key, rede_suffix in REDES_EXTRA.items():
            tdi_rede_path = os.path.join(DADOS, f'4_10_tdi_{rede_key}.json')
            if not os.path.exists(tdi_rede_path):
                continue
            with open(tdi_rede_path, 'r', encoding='utf-8') as f:
                tdi_r = json.load(f)
            tdi_r_anos = sorted(tdi_r.get('serie_temporal', {}).keys())
            rows_tr = []
            for ano in tdi_r_anos:
                s = tdi_r['serie_temporal'][ano]
                rows_tr.append({
                    'Ano': int(ano),
                    'TDI Fundamental (%)': s.get('tdi_fund'),
                    'TDI Anos Iniciais (%)': s.get('tdi_ai'),
                    'TDI Anos Finais (%)': s.get('tdi_af'),
                    'TDI Ensino Médio (%)': s.get('tdi_med'),
                    'Escolas': s.get('n_escolas', 0),
                })
            df_tr = pd.DataFrame(rows_tr)
            if len(df_tr) > 0:
                df_tr.to_excel(writer, sheet_name=f'TDI {rede_suffix}', index=False)

print(f'\nOK - Planilha gerada: {OUT_V2}')
print(f'  [Acesso Est.] Matriculas: {len(df_mat)} linhas ({df_mat["Município"].nunique()} mun x {len(anos)} anos)')
print(f'  [Acesso Est.] Serie Temporal: {len(df_st)} | Variacao Anual: {len(df_var)} | Perfil Alunos: {len(df_perfil)}')
print(f'  [Infra Est.]  Serie Temporal: {len(df_infra)} | Por Municipio: {len(df_infra_mun)}')
print(f'  [Doc]    Perfil: {len(rows_doc)} | Razao: {len(df_razao)} | Por Municipio: {len(df_doc_mun)}')
print(f'  [SAEB]   Serie Temporal: {len(df_saeb)}')
if os.path.exists(icg_path):
    print(f'  [ICG]    Serie Temporal: {len(df_icg_st)} | Por Municipio: {len(df_icg_mun)}')
for rede_key, rede_suffix in REDES_EXTRA.items():
    fpath_r = os.path.join(DADOS, f'4_1_acesso_{rede_key}.json')
    if os.path.exists(fpath_r):
        with open(fpath_r, 'r', encoding='utf-8') as f:
            d = json.load(f)
        ultimo = sorted(d['serie_temporal'].keys())[-1]
        st_r = d['serie_temporal'][ultimo]
        print(f'  [{rede_suffix:6s}] Ultimo ano ({ultimo}): {st_r.get("total_escolas",0)} escolas, {st_r.get("mat_total",0):,} matriculas')
