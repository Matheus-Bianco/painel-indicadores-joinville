import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add Interseccionalidade Raça x Gênero right after Sexo line chart
marker = '<div class="chart-card"><div class="chart-title">Evolu\\u00e7\\u00e3o Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>\n    </div>'
inter_html = """<div class="chart-card"><div class="chart-title">Evolu\\u00e7\\u00e3o Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>

    <!-- ═══ 3B. Interseccionalidade Raça x Gênero ═══ -->
    <div class="section-divider">
      <span class="section-divider-icon"><img src="img/icons/icon_interseccionalidade.png" alt="" onerror="this.src='img/icons/nav_desigualdades.png'"></span>
      <span class="section-divider-text">Interseccionalidade: Ra\\u00e7a x G\\u00eanero</span>
      <span class="section-divider-line"></span>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card full-width"><div class="chart-title">Profici\\u00eancia M\\u00e9dia: Ra\\u00e7a x G\\u00eanero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card full-width"><div class="chart-title">Padr\\u00f5es de Desempenho: Ra\\u00e7a x G\\u00eanero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""

if 'chart-desig-raca-sexo-bar' not in content:
    content = content.replace(marker, inter_html)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Added Intersec HTML correctly")
