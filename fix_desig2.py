"""
Fix Desigualdades section:
1. Remove duplicate filter strip (Ano/Etapa/Disciplina below header) - use only topbar Ano
   Move Etapa+Disciplina as compact selectors inside KPI strip area
2. Fix all hardcoded Y-axis min/max to be adaptive
3. Move Distribuição Territorial to be the last section (after Panorama)
"""

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════
# 1. Remove the filter strip and move Etapa+Disciplina into KPIs
# ═══════════════════════════════════════════════════════════════

old_filter_strip = """      <!-- Filtros no header -->
      <div class="rede-toggle-strip" style="display:flex;gap:16px;align-items:center;flex-wrap:wrap;padding:6px 20px">
        <label style="font-size:11px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:5px">
          <img src="img/icons/sec_evolucao.png" alt="" style="width:14px;height:14px"> Ano:
          <select id="desig-sel-ano" class="filter-select">${anos.map(a => '<option value="' + a + '"' + (a===anos[anos.length-1]?' selected':'') + '>' + a + '</option>').join('')}</select>
        </label>
        <label style="font-size:11px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:5px">
          <img src="img/icons/sec_saeb.png" alt="" style="width:14px;height:14px"> Etapa:
          <select id="desig-sel-etapa" class="filter-select">${ETAPAS.map(e => '<option value="' + e + '"' + (e===defaultEtapa?' selected':'') + '>' + ETAPA_LABELS[e] + '</option>').join('')}</select>
        </label>
        <label style="font-size:11px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:5px">
          <img src="img/icons/panorama.png" alt="" style="width:14px;height:14px"> Disciplina:
          <select id="desig-sel-disc" class="filter-select">
            <option value="LP">L\\u00edngua Portuguesa</option>
            <option value="MT">Matem\\u00e1tica</option>
          </select>
        </label>
        <span id="desig-aviso" style="font-size:10px;color:#E65100;font-style:italic;display:none;margin-left:auto"></span>
      </div>

      <div class="kpi-strip" id="desig-kpis"></div>"""

new_filter_area = """      <div class="kpi-strip" style="position:relative" id="desig-kpis">
        <div style="display:none">
          <select id="desig-sel-ano">${anos.map(a => '<option value="' + a + '"' + (a===anos[anos.length-1]?' selected':'') + '>' + a + '</option>').join('')}</select>
        </div>
      </div>
      <div style="display:flex;gap:12px;align-items:center;padding:4px 20px 2px;flex-wrap:wrap;background:rgba(255,255,255,.92)">
        <label style="font-size:10px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:4px">
          Etapa:
          <select id="desig-sel-etapa" class="filter-select" style="font-size:10px;padding:2px 6px">${ETAPAS.map(e => '<option value="' + e + '"' + (e===defaultEtapa?' selected':'') + '>' + ETAPA_LABELS[e] + '</option>').join('')}</select>
        </label>
        <label style="font-size:10px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:4px">
          Disciplina:
          <select id="desig-sel-disc" class="filter-select" style="font-size:10px;padding:2px 6px">
            <option value="LP">L\\u00edngua Portuguesa</option>
            <option value="MT">Matem\\u00e1tica</option>
          </select>
        </label>
        <span id="desig-aviso" style="font-size:10px;color:#E65100;font-style:italic;display:none;margin-left:auto"></span>
      </div>"""

content = content.replace(old_filter_strip, new_filter_area)

# Now update buildCharts to read anoSel from sel-ano (topbar) with fallback to desig-sel-ano
old_ano_read = "    const anoSel = parseInt(document.getElementById('desig-sel-ano').value);"
new_ano_read = "    const anoSel = parseInt(document.getElementById('desig-sel-ano')?.value || S.anoSel);"
content = content.replace(old_ano_read, new_ano_read)

# Sync desig-sel-ano with sel-ano changes
old_change_bindings = """  ['desig-sel-ano', 'desig-sel-etapa', 'desig-sel-disc'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', () => { buildCharts(); buildDesigMap(); });
  });"""
new_change_bindings = """  ['desig-sel-etapa', 'desig-sel-disc'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', () => { buildCharts(); buildDesigMap(); });
  });
  // Sync hidden desig-sel-ano with topbar sel-ano
  document.getElementById('desig-sel-ano')?.addEventListener('change', () => { buildCharts(); buildDesigMap(); });"""
content = content.replace(old_change_bindings, new_change_bindings)

# Also update the sel-ano population to sync desig-sel-ano when topbar changes
# The bindTopbarFilters already calls refreshActiveTab which calls renderDesigualdades
# But we need desig-sel-ano to exist and stay in sync. Let's make the topbar sel-ano also update desig-sel-ano
old_selano_global = """  // Populate global topbar sel-ano with desig years
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    const anoSel = S.anoSel ? parseInt(S.anoSel) : anos[anos.length - 1];
    selAnoGlobal.innerHTML = anos.map(a => '<option value="' + a + '"' + (a === anoSel ? ' selected' : '') + '>' + a + '</option>').join('');
    S.anoSel = String(anoSel);
  }"""
new_selano_global = """  // Populate global topbar sel-ano with desig years
  const anoSel0 = S.anoSel ? parseInt(S.anoSel) : anos[anos.length - 1];
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => '<option value="' + a + '"' + (a === anoSel0 ? ' selected' : '') + '>' + a + '</option>').join('');
    S.anoSel = String(anoSel0);
  }"""
content = content.replace(old_selano_global, new_selano_global)

# ═══════════════════════════════════════════════════════════════
# 2. Fix all hardcoded Y-axis min/max in Desigualdades charts
# ═══════════════════════════════════════════════════════════════

# Replace all hardcoded min:190, max:230 in the desigualdades section
# These appear in chart options. We need to remove them so Chart.js auto-scales.
# The pattern appears multiple times in the desigualdades buildCharts function

# For bar charts: remove beginAtZero: false, min: 190, max: 230
content = content.replace(
    "scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false, min: 190, max: 230 } }",
    "scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } }"
)

# For line charts (same pattern in y-axis)
content = content.replace(
    "scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, min: 150, max: 250 } }",
    "scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } }"
)

# For horizontal bar charts (x-axis min/max)
content = content.replace(
    "scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false, min: 190, max: 230 }, y: { ticks: { font: { size: 9, family: 'Inter' } } } }",
    "scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false }, y: { ticks: { font: { size: 9, family: 'Inter' } } } }"
)
content = content.replace(
    "scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false, min: 190, max: 230 }, y: { ticks: { font: { size: 8, family: 'Inter' } } } }",
    "scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false }, y: { ticks: { font: { size: 8, family: 'Inter' } } } }"
)

# ═══════════════════════════════════════════════════════════════
# 3. Move Distribuição Territorial to be the LAST section
# ═══════════════════════════════════════════════════════════════

# Cut section 7 (Distribuição Territorial) and paste after section 8 (Panorama)
old_section_7 = """    <!-- ═══ 7. Distribuição Territorial ═══ -->
    <div class="section-divider">
      <span class="section-divider-icon"><img src="img/icons/escola.png" alt=""></span>
      <span class="section-divider-text">Distribui\\u00e7\\u00e3o Territorial</span>
      <span class="section-divider-line"></span>
    </div>
    <div style="display:flex;gap:10px;align-items:center;padding:0 0 8px;flex-wrap:wrap">
      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="active">Munic\\u00edpios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card" style="min-height:460px"><div id="desig-map-leaflet" style="height:440px;border-radius:8px"></div></div>
      <div class="chart-card"><div class="chart-title">Profici\\u00eancia por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>

    <!-- ═══ 8. Panorama ═══ -->"""

new_sections_order = """    <!-- ═══ 7. Panorama ═══ -->"""

# First remove section 7 and the separator to section 8
content = content.replace(old_section_7, new_sections_order)

# Now add section 7 (Territorial) AFTER the Panorama section
old_panorama_end = """    <div class="charts-grid">
      <div class="chart-card full-width"><div class="chart-title">Desigualdade Racial (Branca vs Preta) \\u2014 Todas as Etapas e Disciplinas</div><div style="height:300px"><canvas id="chart-desig-panorama"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>
  \`;"""

new_panorama_plus_territorial = """    <div class="charts-grid">
      <div class="chart-card full-width"><div class="chart-title">Desigualdade Racial (Branca vs Preta) \\u2014 Todas as Etapas e Disciplinas</div><div style="height:300px"><canvas id="chart-desig-panorama"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>

    <!-- ═══ 8. Distribuição Territorial ═══ -->
    <div class="section-divider">
      <span class="section-divider-icon"><img src="img/icons/escola.png" alt=""></span>
      <span class="section-divider-text">Distribui\\u00e7\\u00e3o Territorial</span>
      <span class="section-divider-line"></span>
    </div>
    <div style="display:flex;gap:10px;align-items:center;padding:0 0 8px;flex-wrap:wrap">
      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="active">Munic\\u00edpios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>
    </div>
    <div class="charts-grid" style="grid-template-columns:1fr 1fr">
      <div class="chart-card" style="min-height:460px"><div id="desig-map-leaflet" style="height:440px;border-radius:8px"></div></div>
      <div class="chart-card"><div class="chart-title">Profici\\u00eancia por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>
  \`;"""

content = content.replace(old_panorama_end, new_panorama_plus_territorial)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f'Done. Total lines: {len(content.split(chr(10)))}')

# Verify changes
checks = [
    ('rede-toggle-strip removed', 'rede-toggle-strip' not in content or content.count('rede-toggle-strip') == 0),
    ('Adaptive Y-axis', 'min: 190, max: 230' not in content),
    ('desig-map-leaflet present', 'desig-map-leaflet' in content),
    ('Panorama before Territorial', content.index('chart-desig-panorama') < content.index('desig-map-leaflet')),
]
for label, ok in checks:
    print(f'  {"✓" if ok else "✗"} {label}')
