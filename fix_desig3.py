import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════
# 1. Update HTML structure in renderDesigualdades
# ═══════════════════════════════════════════════════════════════

def replace_section(old_html_str, new_html_str):
    global content
    if old_html_str in content:
        content = content.replace(old_html_str, new_html_str)
    else:
        print(f"Failed to find: {old_html_str[:50]}...")

# SEXO
old_sexo = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_sexo = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_sexo, new_sexo)

# RACA
old_raca = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_raca = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-raca-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>

    <!-- ═══ 3B. Interseccionalidade Raça x Gênero ═══ -->
    <div class="section-divider">
      <span class="section-divider-icon"><img src="img/icons/icon_interseccionalidade.png" alt="" onerror="this.src='img/icons/nav_desigualdades.png'"></span>
      <span class="section-divider-text">Interseccionalidade: Raça x Gênero</span>
      <span class="section-divider-line"></span>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card full-width"><div class="chart-title">Proficiência Média: Raça x Gênero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card full-width"><div class="chart-title">Padrões de Desempenho: Raça x Gênero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_raca, new_raca)

# RACA X LOCALIZACAO
old_racaloc = """    <div class="charts-grid">
      <div class="chart-card full-width"><div class="chart-title">Proficiência Média (Raça/Cor x Localização)</div><div style="height:350px"><canvas id="chart-desig-raca-loc-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_racaloc = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média (Raça/Cor x Localização)</div><div style="height:350px"><canvas id="chart-desig-raca-loc-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Raça x Localização)</div><div style="height:350px"><canvas id="chart-desig-raca-loc-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_racaloc, new_racaloc)

# LOCALIZACAO
old_loc = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Localização</div><div style="height:280px"><canvas id="chart-desig-loc-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Localização</div><div style="height:280px"><canvas id="chart-desig-loc-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_loc = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Localização</div><div style="height:280px"><canvas id="chart-desig-loc-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-loc-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Localização</div><div style="height:280px"><canvas id="chart-desig-loc-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_loc, new_loc)

# TURNO
old_turno = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Turno</div><div style="height:280px"><canvas id="chart-desig-turno-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Turno</div><div style="height:280px"><canvas id="chart-desig-turno-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_turno = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Turno</div><div style="height:280px"><canvas id="chart-desig-turno-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-turno-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Turno</div><div style="height:280px"><canvas id="chart-desig-turno-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_turno, new_turno)

# DEFICIENCIA
old_def = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Deficiência</div><div style="height:280px"><canvas id="chart-desig-def-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Deficiência</div><div style="height:280px"><canvas id="chart-desig-def-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_def = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Deficiência</div><div style="height:280px"><canvas id="chart-desig-def-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-def-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Deficiência</div><div style="height:280px"><canvas id="chart-desig-def-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
replace_section(old_def, new_def)

# MAP LAYER ESC e TABELA
old_map = """    <div style="display:flex;gap:10px;align-items:center;padding:0 0 8px;flex-wrap:wrap">
      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="active">Municípios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card" style="min-height:460px"><div id="desig-map-leaflet" style="height:440px;border-radius:8px"></div></div>
      <div class="chart-card"><div class="chart-title">Proficiência por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

new_map = """    <div style="display:flex;gap:10px;align-items:center;padding:0 0 8px;flex-wrap:wrap">
      <div class="map-layer-toggle">
        <button id="desig-btn-layer-esc">Escolas</button>
        <button id="desig-btn-layer-mun" class="active">Municípios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card" style="min-height:460px"><div id="desig-map-leaflet" style="height:440px;border-radius:8px"></div></div>
      <div class="chart-card"><div class="chart-title">Proficiência por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>
    <div class="chart-card full-width mt-4">
      <div class="chart-title" style="display:flex;align-items:center;justify-content:space-between">
        Tabela Analítica - Desigualdades
        <div style="display:flex;gap:10px">
          <input type="text" id="desig-table-search" placeholder="Pesquisar..." style="font-size:12px;padding:4px 8px;border:1px solid #ddd;border-radius:4px;width:200px">
        </div>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table" id="desig-table" style="font-size:11px;min-width:1000px">
          <thead>
            <tr>
              <th style="text-align:left">Localidade</th>
              <th>Média</th>
              <th>% Avançado</th>
              <th>% Adequado</th>
              <th>% Básico</th>
              <th>% Abaixo</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
      <div class="chart-source">${FONTE}</div>
    </div>"""
replace_section(old_map, new_map)

# ═══════════════════════════════════════════════════════════════
# 2. Add build charts logic
# ═══════════════════════════════════════════════════════════════
# I will output the final content so I can verify
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("Updated HTML structure.")
