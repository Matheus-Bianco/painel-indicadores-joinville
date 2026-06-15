import re

path = 'etl_desigualdades.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update COLS
old_cols = """COLS = [
    'CD_ESCOLA', 'NM_ESCOLA', 'CD_MUNICIPIO', 'NM_MUNICIPIO',
    'CD_REGIONAL', 'NM_REGIONAL', 'CD_REDE', 'DC_REDE',
    'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA',
    'NM_DISCIPLINA', 'VL_PROFICIENCIA', 'DC_PADRAO_DESEMPENHO',
    'FL_AVALIADO', 'FL_PREVISTO',
    'DC_COR_RACA', 'DC_SEXO', 'DC_ALUNO_NEC_ESPECIAL', 'DC_LOCALIZACAO', 'DC_TURNO'
]"""

new_cols = """COLS = [
    'CD_ESCOLA', 'NM_ESCOLA', 'CD_MUNICIPIO', 'NM_MUNICIPIO',
    'CD_REGIONAL', 'NM_REGIONAL', 'CD_REDE', 'DC_REDE',
    'CD_ETAPA_AVALIADA', 'DC_ETAPA_AVALIADA',
    'NM_DISCIPLINA', 'VL_PROFICIENCIA', 'DC_PADRAO_DESEMPENHO',
    'FL_AVALIADO', 'FL_PREVISTO',
    'DC_COR_RACA', 'DC_RACA', 'DC_SEXO', 'DC_ALUNO_NEC_ESPECIAL', 'TIPO_DEFICIENCIA', 'DC_LOCALIZACAO', 'DC_TURNO'
]"""
content = content.replace(old_cols, new_cols)

# 2. Update process_year
old_process = """    if 'DC_SEXO' in df.columns: df['sexo'] = df['DC_SEXO'].apply(norm_sexo)
    if 'DC_COR_RACA' in df.columns: df['raca'] = df['DC_COR_RACA'].apply(norm_raca)
    if 'DC_ALUNO_NEC_ESPECIAL' in df.columns: df['deficiencia'] = df['DC_ALUNO_NEC_ESPECIAL'].apply(norm_deficiencia)
    if 'DC_LOCALIZACAO' in df.columns: df['loc'] = df['DC_LOCALIZACAO'].apply(norm_loc)
    if 'DC_TURNO' in df.columns: df['turno'] = df['DC_TURNO'].apply(norm_turno)"""

new_process = """    if 'DC_SEXO' in df.columns: df['sexo'] = df['DC_SEXO'].apply(norm_sexo)
    if 'DC_COR_RACA' in df.columns: df['raca'] = df['DC_COR_RACA'].apply(norm_raca)
    elif 'DC_RACA' in df.columns: df['raca'] = df['DC_RACA'].apply(norm_raca)
    
    if 'DC_ALUNO_NEC_ESPECIAL' in df.columns: df['deficiencia'] = df['DC_ALUNO_NEC_ESPECIAL'].apply(norm_deficiencia)
    elif 'TIPO_DEFICIENCIA' in df.columns: df['deficiencia'] = df['TIPO_DEFICIENCIA'].apply(norm_deficiencia)
    
    if 'DC_LOCALIZACAO' in df.columns: df['loc'] = df['DC_LOCALIZACAO'].apply(norm_loc)
    if 'DC_TURNO' in df.columns: df['turno'] = df['DC_TURNO'].apply(norm_turno)"""
content = content.replace(old_process, new_process)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated etl_desigualdades.py columns!")
