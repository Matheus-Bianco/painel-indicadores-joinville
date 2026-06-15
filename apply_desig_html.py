import re
import codecs

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Etapa/Disciplina inner filters and hide desig-sel-ano block
old_filters_block = r'      <div style="display:flex;gap:12px;align-items:center;padding:4px 20px 2px;flex-wrap:wrap;background:rgba\(255,255,255,\.92\)">(.*?)</div>\n    </div>\n\n    <!-- ═══ BLOCO INFORMATIVO ═══ -->'
content = re.sub(old_filters_block, '    </div>\n\n    <!-- ═══ BLOCO INFORMATIVO ═══ -->', content, flags=re.DOTALL)

old_sel_ano_hidden = r'      <div class="kpi-strip" style="position:relative" id="desig-kpis">\s*<div style="display:none">\s*<select id="desig-sel-ano">.*?</select>\s*</div>\s*</div>'
new_sel_ano_hidden = r'      <div class="kpi-strip" style="position:relative" id="desig-kpis"></div>'
content = re.sub(old_sel_ano_hidden, new_sel_ano_hidden, content, flags=re.DOTALL)

# 2. Add Etapa/Disc to banner filters
injection_point = r'  const selAnoGlobal = document\.getElementById\(\'sel-ano\'\);\n  if \(selAnoGlobal\) \{\n    selAnoGlobal\.innerHTML = anos\.map\(a => `<option value="\$\{a\}" \$\{a === anoSel0 \? \'selected\' : \'\'\}>\$\{a\}</option>`\)\.join\(\'\'\);\n  \}'
new_injection = """  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => `<option value="${a}" ${a === anoSel0 ? 'selected' : ''}>${a}</option>`).join('');
  }
  
  const bannerFilters = main.querySelector('.banner-filters');
  if (bannerFilters) {
    bannerFilters.insertAdjacentHTML('beforeend', `
      <div class="banner-filter-group">
        <label class="banner-filter-label">Etapa de Ensino</label>
        <select id="desig-sel-etapa" class="banner-filter-select">
          ${ETAPAS.map(e => '<option value="' + e + '"' + (e===defaultEtapa?' selected':'') + '>' + ETAPA_LABELS[e] + '</option>').join('')}
        </select>
      </div>
      <div class="banner-filter-group">
        <label class="banner-filter-label">Componente Curricular</label>
        <select id="desig-sel-disc" class="banner-filter-select">
          <option value="LP">Língua Portuguesa</option>
          <option value="MT">Matemática</option>
        </select>
      </div>
    `);
  }"""
content = re.sub(injection_point, new_injection, content, flags=re.DOTALL)

# 3. Add Warning 2022 inside desig-kpis
warning_code = r'    const avisoEl = document\.getElementById\(\'desig-aviso\'\);\n    if \(avisoEl\) \{\n      if \(etapa === \'2_EF\'\) \{\n        avisoEl\.style\.display = \'inline\';\n        avisoEl\.textContent = \'⚠ O 2º ano EF não possui dados de raça e sexo \(questionário não aplicado\)\.\';\n      \} else \{ avisoEl\.style\.display = \'none\'; \}\n    \}'
new_warning_code = """    const kpiDiv = document.getElementById('desig-kpis');
    if (anoSel === 2022) {
      kpiDiv.innerHTML = `<div style="padding:16px 20px;background:#FFF3E0;border-left:4px solid #FF9800;border-radius:6px;color:#E65100;font-size:13px;width:100%;margin-bottom:12px;"><strong>Atenção:</strong> O ano de 2022 não possui dados de Raça e Sexo disponíveis no momento. Por favor, selecione outro ano para visualizar estes recortes.</div>`;
    }"""
content = re.sub(warning_code, new_warning_code, content, flags=re.DOTALL)

# 4. Fix HTML structure for Padrões de Desempenho & Interseccionalidade
old_raca_html = r'      <div class="chart-card"><div class="chart-title">Proficiência Média por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">\$\{FONTE\}</div></div>\n      <div class="chart-card"><div class="chart-title">Evolução Temporal por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-line"></canvas></div><div class="chart-source">\$\{FONTE\}</div></div>'
new_raca_html = r"""      <div class="chart-card"><div class="chart-title">Proficiência Média por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-raca-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-line"></canvas></div><div class="chart-source">${FONTE}</div></div>"""
content = re.sub(old_raca_html, new_raca_html, content, flags=re.DOTALL)
# Fix grid-template-columns for raca
content = re.sub(r'(<!-- ═══ 2. Raça/Cor ═══ -->\s*<div class="section-divider">.*?</div>\s*)<div class="charts-grid">', r'\1<div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">', content, flags=re.DOTALL)

# Add Interseccionalidade
intersec_html = r"""    <!-- ═══ 3B. Interseccionalidade Raça x Gênero ═══ -->
    <div class="section-divider">
      <span class="section-divider-icon"><img src="img/icons/icon_interseccionalidade.png" alt="" onerror="this.src='img/icons/nav_desigualdades.png'"></span>
      <span class="section-divider-text">Interseccionalidade: Raça x Gênero</span>
      <span class="section-divider-line"></span>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card full-width"><div class="chart-title">Proficiência Média: Raça x Gênero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card full-width"><div class="chart-title">Padrões de Desempenho: Raça x Gênero</div><div style="height:320px"><canvas id="chart-desig-raca-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
content = re.sub(r'(<!-- ═══ 3. Sexo ═══ -->)', intersec_html + r'\n\n    \1', content, flags=re.DOTALL)

old_sexo_html = r'      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">\$\{FONTE\}</div></div>\n      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">\$\{FONTE\}</div></div>'
new_sexo_html = r"""      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>"""
content = re.sub(old_sexo_html, new_sexo_html, content, flags=re.DOTALL)
# Fix grid-template-columns for sexo
content = re.sub(r'(<!-- ═══ 3. Sexo ═══ -->\s*<div class="section-divider">.*?</div>\s*)<div class="charts-grid">', r'\1<div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">', content, flags=re.DOTALL)


# 5. Fix map toggles HTML
old_map_toggles = r'<button id="desig-btn-layer-mun" class="active">Munic\\u00edpios</button>\s*<button id="desig-btn-layer-cre">CREs</button>'
new_map_toggles = r'<button id="desig-btn-layer-mun" class="map-layer-btn active">Municípios</button>\n        <button id="desig-btn-layer-cre" class="map-layer-btn">CREs</button>\n        <button id="desig-btn-layer-esc" class="map-layer-btn">Escolas</button>'
content = re.sub(old_map_toggles, new_map_toggles, content, flags=re.DOTALL)
if 'class="map-layer-btn"' not in content:
    # try without double slash
    old_map_toggles2 = r'<button id="desig-btn-layer-mun" class="active">Munic\\?u00edpios</button>\s*<button id="desig-btn-layer-cre">CREs</button>'
    content = re.sub(old_map_toggles2, new_map_toggles, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated HTML logic successfully!")
