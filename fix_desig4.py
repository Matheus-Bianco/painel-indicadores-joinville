import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace getPct definition
old_getpct = "const getPct = (dim, group, k) => dims[dim]?.[group]?.[k || key]?.pct_adeq_av;"
new_getpct = "const getPct = (dim, group, prop, k) => dims[dim]?.[group]?.[k || key]?.[prop || 'pct_adeq_av'];"
if old_getpct in content:
    content = content.replace(old_getpct, new_getpct)

# Helper function to generate standard stacked bar code
def stacked_bar_code(id_str, groups_var, dim_str):
    return f"""      S.charts.push(new Chart(document.getElementById('{id_str}'), {{
        type: 'bar',
        data: {{ labels: {groups_var}, datasets: [
          {{ label: 'Abaixo do Básico', data: {groups_var}.map(g => getPct('{dim_str}', g, 'pct_abaixo')), backgroundColor: '#E53935', borderRadius: 4 }},
          {{ label: 'Básico', data: {groups_var}.map(g => getPct('{dim_str}', g, 'pct_basico')), backgroundColor: '#F57C00', borderRadius: 4 }},
          {{ label: 'Adequado', data: {groups_var}.map(g => getPct('{dim_str}', g, 'pct_adequado')), backgroundColor: '#43A047', borderRadius: 4 }},
          {{ label: 'Avançado', data: {groups_var}.map(g => getPct('{dim_str}', g, 'pct_avancado')), backgroundColor: '#1d71b9', borderRadius: 4 }}
        ] }},
        options: {{ ...CHART_DEFAULTS, plugins: {{ ...CHART_DEFAULTS.plugins, legend: {{ display: true, position: 'bottom', labels: {{ boxWidth: 10, font: {{ size: 10, family: 'Inter' }} }} }}, datalabels: DL_PCT }},
          scales: {{ ...CHART_DEFAULTS.scales, x: {{ stacked: true }}, y: {{ stacked: true, max: 100, beginAtZero: true, ticks: {{ ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' }} }} }} }}
      }}));"""

# 1. Raca Bar
old_raca_bar = """        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
    }"""
new_raca_bar = old_raca_bar + "\n" + stacked_bar_code('chart-desig-raca-padrao', 'racaGroups', 'raca')
if "chart-desig-raca-padrao" not in content and old_raca_bar in content:
    content = content.replace(old_raca_bar, new_raca_bar, 1)

# 2. Sexo Bar
old_sexo_bar = """        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
    }"""
new_sexo_bar = old_sexo_bar + "\n" + stacked_bar_code('chart-desig-sexo-padrao', 'sexoGroups', 'sexo')
if "chart-desig-sexo-padrao" not in content:
    # Need to target the second occurrence (Sexo)
    parts = content.split(old_sexo_bar)
    if len(parts) >= 3:
        content = parts[0] + old_sexo_bar + parts[1] + new_sexo_bar + parts[2]

# 3. Loc Bar
old_loc_bar = """        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
    }"""
new_loc_bar = old_loc_bar + "\n" + stacked_bar_code('chart-desig-loc-padrao', 'locGroups', 'localizacao')
if "chart-desig-loc-padrao" not in content:
    parts = content.split(old_loc_bar)
    if len(parts) >= 4:
        content = parts[0] + old_loc_bar + parts[1] + old_loc_bar + parts[2] + new_loc_bar + "".join(parts[3:])

# 4. Deficiencia Bar
# Remove the old pct chart and add stacked bar
old_def = """      S.charts.push(new Chart(document.getElementById('chart-desig-def-pct'), {
        type: 'bar',
        data: { labels: defGroups, datasets: [{ label: '% Adequado+Avan\u00e7ado', data: defGroups.map(g => getPct('deficiencia', g)),
          backgroundColor: defGroups.map(g => DEF_COLORS[g]), borderRadius: 4, barPercentage: 0.5 }] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_PCT },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: true, max: 100, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } } } },
      }));"""
if old_def in content:
    content = content.replace(old_def, stacked_bar_code('chart-desig-def-padrao', 'defGroups', 'deficiencia'))

# 5. Intersecao Raca Loc Padrao
old_inter = """    if (interGrupos.length > 0) {
      const interColors = interGrupos.map(g => RACA_COLORS[g.split(' - ')[0]] || '#999');
      S.charts.push(new Chart(document.getElementById('chart-desig-inter'), {
        type: 'bar',
        data: { labels: interGrupos.map(g => g.replace(' - ', '\\n')),
          datasets: [{ label: 'Profici\\u00eancia', data: interGrupos.map(g => getVal('raca_loc', g)),
            backgroundColor: interGrupos.map((g,i) => g.includes('Rural') ? interColors[i] + '77' : interColors[i] + 'CC'),
            borderColor: interColors, borderWidth: 1, borderRadius: 4, barPercentage: 0.7 }] },
        options: { ...CHART_DEFAULTS, indexAxis: 'y',
          plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: { ...DL_VAL, anchor: 'end', align: 'right' } },
          scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false }, y: { ticks: { font: { size: 9, family: 'Inter' } } } } },
      }));
    }"""
new_inter = old_inter + """
      S.charts.push(new Chart(document.getElementById('chart-desig-raca-loc-padrao'), {
        type: 'bar',
        data: { labels: interGrupos.map(g => g.replace(' - ', '\\n')), datasets: [
          { label: 'Abaixo do Básico', data: interGrupos.map(g => getPct('raca_loc', g, 'pct_abaixo')), backgroundColor: '#E53935' },
          { label: 'Básico', data: interGrupos.map(g => getPct('raca_loc', g, 'pct_basico')), backgroundColor: '#F57C00' },
          { label: 'Adequado', data: interGrupos.map(g => getPct('raca_loc', g, 'pct_adequado')), backgroundColor: '#43A047' },
          { label: 'Avançado', data: interGrupos.map(g => getPct('raca_loc', g, 'pct_avancado')), backgroundColor: '#1d71b9' }
        ] },
        options: { ...CHART_DEFAULTS, indexAxis: 'y', plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } }, datalabels: DL_PCT },
          scales: { x: { stacked: true, max: 100, beginAtZero: true, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } }, y: { stacked: true, ticks: { font: { size: 9, family: 'Inter' } } } } }
      }));
"""
if "chart-desig-raca-loc-padrao" not in content and old_inter in content:
    content = content.replace(old_inter, new_inter)

# 6. Turno Bar
old_turno_pct = """      S.charts.push(new Chart(document.getElementById('chart-desig-turno-pct'), {
        type: 'bar',
        data: { labels: turnoGrupos, datasets: [{ label: '% Adequado+Avan\\u00e7ado', data: turnoGrupos.map(g => getPct('turno', g)),
          backgroundColor: turnoGrupos.map(g => TURNO_COLORS[g]), borderRadius: 4, barPercentage: 0.6 }] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_PCT },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: true, max: 100, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } } } },
      }));"""
if old_turno_pct in content:
    content = content.replace(old_turno_pct, stacked_bar_code('chart-desig-turno-padrao', 'turnoGrupos', 'turno'))

# 7. Interseccionalidade Raça x Sexo
# Add before ── 6. TURNO ──
inter_raca_sexo = """
    // ── 5B. INTERSECÇÃO RAÇA x SEXO ──
    const rsOrder = ['Branca - Feminino', 'Branca - Masculino', 'Parda - Feminino', 'Parda - Masculino', 'Preta - Feminino', 'Preta - Masculino', 'Indígena - Feminino', 'Indígena - Masculino', 'Amarela - Feminino', 'Amarela - Masculino'];
    const rsGrupos = rsOrder.filter(g => dims.raca_sexo?.[g]?.[key]);
    if (rsGrupos.length > 0) {
      const rsColors = rsGrupos.map(g => RACA_COLORS[g.split(' - ')[0]] || '#999');
      S.charts.push(new Chart(document.getElementById('chart-desig-raca-sexo-bar'), {
        type: 'bar',
        data: { labels: rsGrupos.map(g => g.replace(' - ', '\\n')),
          datasets: [{ label: 'Proficiência', data: rsGrupos.map(g => getVal('raca_sexo', g)),
            backgroundColor: rsGrupos.map((g,i) => g.includes('Feminino') ? rsColors[i] + 'CC' : rsColors[i] + '77'),
            borderColor: rsColors, borderWidth: 1, borderRadius: 4, barPercentage: 0.7 }] },
        options: { ...CHART_DEFAULTS, indexAxis: 'y',
          plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: { ...DL_VAL, anchor: 'end', align: 'right' } },
          scales: { x: { ...CHART_DEFAULTS.scales.y, beginAtZero: false }, y: { ticks: { font: { size: 9, family: 'Inter' } } } } },
      }));
      S.charts.push(new Chart(document.getElementById('chart-desig-raca-sexo-padrao'), {
        type: 'bar',
        data: { labels: rsGrupos.map(g => g.replace(' - ', '\\n')), datasets: [
          { label: 'Abaixo do Básico', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_abaixo')), backgroundColor: '#E53935' },
          { label: 'Básico', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_basico')), backgroundColor: '#F57C00' },
          { label: 'Adequado', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_adequado')), backgroundColor: '#43A047' },
          { label: 'Avançado', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_avancado')), backgroundColor: '#1d71b9' }
        ] },
        options: { ...CHART_DEFAULTS, indexAxis: 'y', plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } }, datalabels: DL_PCT },
          scales: { x: { stacked: true, max: 100, beginAtZero: true, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } }, y: { stacked: true, ticks: { font: { size: 9, family: 'Inter' } } } } }
      }));
    }
"""
if "chart-desig-raca-sexo-bar" not in content and "// ── 6. TURNO ──" in content:
    content = content.replace("// ── 6. TURNO ──", inter_raca_sexo + "\n    // ── 6. TURNO ──")

# 8. Panorama Multi-Etapa for all races
old_panorama = """    const panLabels = []; const panBranca = []; const panPreta = [];
    ETAPAS.forEach(et => {
      ['LP', 'MT'].forEach(dc => {
        const k = et + '_' + dc;
        const b = dims.raca?.Branca?.[k]?.media;
        const p = dims.raca?.Preta?.[k]?.media;
        if (b != null && p != null) {
          panLabels.push(ETAPA_LABELS[et] + ' ' + dc);
          panBranca.push(b); panPreta.push(p);
        }
      });
    });
    if (panLabels.length > 0) {
      S.charts.push(new Chart(document.getElementById('chart-desig-panorama'), {
        type: 'bar',
        data: { labels: panLabels, datasets: [
          { label: 'Branca', data: panBranca, backgroundColor: '#1d71b9CC', borderRadius: 3, barPercentage: 0.35, categoryPercentage: 0.8 },
          { label: 'Preta', data: panPreta, backgroundColor: '#333333CC', borderRadius: 3, barPercentage: 0.35, categoryPercentage: 0.8 },
        ] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, datalabels: { ...DL_VAL, font: { size: 8, weight: 'bold' } } },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
    }"""
new_panorama = """    const panLabels = [];
    const panRacas = { 'Branca': [], 'Parda': [], 'Preta': [], 'Indígena': [], 'Amarela': [] };
    const racaCoresPan = { 'Branca': '#1d71b9CC', 'Parda': '#FFCB04CC', 'Preta': '#333333CC', 'Indígena': '#E53935CC', 'Amarela': '#43A047CC' };
    
    ETAPAS.forEach(et => {
      ['LP', 'MT'].forEach(dc => {
        const k = et + '_' + dc;
        // Check if at least Branca and Preta exist
        if (dims.raca?.Branca?.[k]?.media != null && dims.raca?.Preta?.[k]?.media != null) {
          panLabels.push(ETAPA_LABELS[et] + ' ' + dc);
          Object.keys(panRacas).forEach(r => {
            panRacas[r].push(dims.raca?.[r]?.[k]?.media || null);
          });
        }
      });
    });
    
    if (panLabels.length > 0) {
      const activeRacas = Object.keys(panRacas).filter(r => panRacas[r].some(v => v != null));
      S.charts.push(new Chart(document.getElementById('chart-desig-panorama'), {
        type: 'bar',
        data: { labels: panLabels, datasets: activeRacas.map(r => ({
          label: r, data: panRacas[r], backgroundColor: racaCoresPan[r], borderRadius: 3, barPercentage: 0.4, categoryPercentage: 0.8
        })) },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom' }, datalabels: { ...DL_VAL, font: { size: 8, weight: 'bold' }, formatter: v => v != null ? Math.round(v) : '' } },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
    }"""
if old_panorama in content:
    content = content.replace(old_panorama, new_panorama)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated Javascript charts!")
