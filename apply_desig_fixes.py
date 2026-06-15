import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove Etapa/Disciplina inner filters and hide desig-sel-ano block
old_filters_block = re.search(r'      <div style="display:flex;gap:12px;align-items:center;padding:4px 20px 2px;flex-wrap:wrap;background:rgba\(255,255,255,\.92\)">(.*?)</div>\n    </div>\n\n    <!-- ═══ BLOCO INFORMATIVO ═══ -->', content, flags=re.DOTALL)
if old_filters_block:
    content = content.replace(old_filters_block.group(0), '    </div>\n\n    <!-- ═══ BLOCO INFORMATIVO ═══ -->')
else:
    print("Warning: old_filters_block not found")

old_sel_ano_hidden = """      <div class="kpi-strip" style="position:relative" id="desig-kpis">
        <div style="display:none">
          <select id="desig-sel-ano">${anos.map(a => '<option value="' + a + '"' + (a===anos[anos.length-1]?' selected':'') + '>' + a + '</option>').join('')}</select>
        </div>
      </div>"""
new_sel_ano_hidden = """      <div class="kpi-strip" style="position:relative" id="desig-kpis"></div>"""
if old_sel_ano_hidden in content:
    content = content.replace(old_sel_ano_hidden, new_sel_ano_hidden)
else:
    print("Warning: old_sel_ano_hidden not found")

# 2. Add Etapa/Disc to banner filters
injection_point = """  // Re-populate topbar filters
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => `<option value="${a}" ${a === anoSel0 ? 'selected' : ''}>${a}</option>`).join('');
  }"""
new_injection = """  // Re-populate topbar filters
  const selAnoGlobal = document.getElementById('sel-ano');
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
if injection_point in content:
    content = content.replace(injection_point, new_injection)
else:
    print("Warning: injection_point not found")


# 3. Add Warning 2022 inside desig-kpis
warning_code = """    // Warning for 2_EF
    const avisoEl = document.getElementById('desig-aviso');
    if (avisoEl) {
      if (etapa === '2_EF') {
        avisoEl.style.display = 'inline';
        avisoEl.textContent = '⚠ O 2º ano EF não possui dados de raça e sexo (questionário não aplicado).';
      } else { avisoEl.style.display = 'none'; }
    }"""
new_warning_code = """    const kpiDiv = document.getElementById('desig-kpis');
    if (anoSel === 2022) {
      kpiDiv.innerHTML = `<div style="padding:16px 20px;background:#FFF3E0;border-left:4px solid #FF9800;border-radius:6px;color:#E65100;font-size:13px;width:100%;margin-bottom:12px;"><strong>Atenção:</strong> O ano de 2022 não possui dados de Raça e Sexo disponíveis no momento. Por favor, selecione outro ano para visualizar estes recortes.</div>`;
    }"""
if warning_code in content:
    content = content.replace(warning_code, new_warning_code)
else:
    print("Warning: warning_code not found")


# 4. Fix HTML structure for Padrões de Desempenho & Interseccionalidade
old_raca_html = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Raça/Cor</div><div style="height:280px"><canvas id="chart-desig-raca-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
new_raca_html = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
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
if old_raca_html in content:
    content = content.replace(old_raca_html, new_raca_html)
else:
    print("Warning: old_raca_html not found")

old_sexo_html = """    <div class="charts-grid">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
new_sexo_html = """    <div class="charts-grid" style="grid-template-columns:1fr 1fr 1fr">
      <div class="chart-card"><div class="chart-title">Proficiência Média por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-bar"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Padrões de Desempenho (Defasagem)</div><div style="height:280px"><canvas id="chart-desig-sexo-padrao"></canvas></div><div class="chart-source">${FONTE}</div></div>
      <div class="chart-card"><div class="chart-title">Evolução Temporal por Sexo</div><div style="height:280px"><canvas id="chart-desig-sexo-line"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>"""
if old_sexo_html in content:
    content = content.replace(old_sexo_html, new_sexo_html)
else:
    print("Warning: old_sexo_html not found")


# 5. Fix JS Charts (add new ones)
old_getpct = "const getPct = (dim, group, k) => dims[dim]?.[group]?.[k || key]?.pct_adeq_av;"
new_getpct = "const getPct = (dim, group, prop, k) => dims[dim]?.[group]?.[k || key]?.[prop || 'pct_adeq_av'];"
if old_getpct in content:
    content = content.replace(old_getpct, new_getpct)

# Fix map toggles HTML
old_map_toggles = """      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="active">Municípios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>"""
new_map_toggles = """      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="map-layer-btn active">Municípios</button>
        <button id="desig-btn-layer-cre" class="map-layer-btn">CREs</button>
        <button id="desig-btn-layer-esc" class="map-layer-btn">Escolas</button>
      </div>"""
if old_map_toggles in content:
    content = content.replace(old_map_toggles, new_map_toggles)
else:
    print("Warning: old_map_toggles not found")

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated successfully!")
