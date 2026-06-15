import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# For Raça
old_raca_part = '<div class="chart-card"><div class="chart-title">Profici\\u00eancia M\\u00e9dia por Ra\\u00e7a/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>'
new_raca_padrao = '<div class="chart-card"><div class="chart-title">Profici\\u00eancia M\\u00e9dia por Ra\\u00e7a/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>\n      <div class="chart-card"><div class="chart-title">Padr\\u00f5es de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-raca-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>'
content = content.replace(old_raca_part, new_raca_padrao)

# For Sexo
old_sexo_part = '<div class="chart-card"><div class="chart-title">Profici\\u00eancia M\\u00e9dia por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>'
new_sexo_padrao = '<div class="chart-card"><div class="chart-title">Profici\\u00eancia M\\u00e9dia por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>\n      <div class="chart-card"><div class="chart-title">Padr\\u00f5es de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>'
content = content.replace(old_sexo_part, new_sexo_padrao)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Added HTML canvases successfully")
