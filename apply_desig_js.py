import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update getPct
old_getpct = "const getPct = (dim, group, k) => dims[dim]?.[group]?.[k || key]?.pct_adeq_av;"
new_getpct = "const getPct = (dim, group, prop, k) => dims[dim]?.[group]?.[k || key]?.[prop || 'pct_adeq_av'];"
content = content.replace(old_getpct, new_getpct)

# 2. Add Padrões de Desempenho for Raça
old_raca_bar = r'        options: \{ \.\.\.CHART_DEFAULTS, plugins: \{ \.\.\.CHART_DEFAULTS\.plugins, legend: \{ display: false \}, datalabels: DL_VAL \},\n          scales: \{ \.\.\.CHART_DEFAULTS\.scales, y: \{ \.\.\.CHART_DEFAULTS\.scales\.y, beginAtZero: false \} \} \},\n      \}\)\);\n    \}'
new_raca_padrao = """        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));

      S.charts.push(new Chart(document.getElementById('chart-desig-raca-padrao'), {
        type: 'bar',
        data: { labels: racaGroups, datasets: [
          { label: 'Abaixo do Básico', data: racaGroups.map(g => getPct('raca', g, 'pct_abaixo')), backgroundColor: '#E53935', borderRadius: 4 },
          { label: 'Básico', data: racaGroups.map(g => getPct('raca', g, 'pct_basico')), backgroundColor: '#F57C00', borderRadius: 4 },
          { label: 'Adequado', data: racaGroups.map(g => getPct('raca', g, 'pct_adequado')), backgroundColor: '#43A047', borderRadius: 4 },
          { label: 'Avançado', data: racaGroups.map(g => getPct('raca', g, 'pct_avancado')), backgroundColor: '#1d71b9', borderRadius: 4 }
        ] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } }, datalabels: DL_PCT },
          scales: { ...CHART_DEFAULTS.scales, x: { stacked: true }, y: { stacked: true, max: 100, beginAtZero: true, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } } } }
      }));
    }"""
content = re.sub(old_raca_bar, new_raca_padrao, content, count=1)

# 3. Add Padrões de Desempenho for Sexo
old_sexo_bar = r'      S\.charts\.push\(new Chart\(document\.getElementById\(\'chart-desig-sexo-bar\'\), \{\n        type: \'bar\',\n        data: \{ labels: sexoGroups, datasets: \[\{ label: \'Proficiência\', data: sexoGroups\.map\(g => getVal\(\'sexo\', g\)\), backgroundColor: \[\'#1d71b9\', \'#FFCB04\'\], borderRadius: 6 \}\] \},\n        options: \{ \.\.\.CHART_DEFAULTS, plugins: \{ \.\.\.CHART_DEFAULTS\.plugins, legend: \{ display: false \}, datalabels: DL_VAL \},\n          scales: \{ \.\.\.CHART_DEFAULTS\.scales, y: \{ \.\.\.CHART_DEFAULTS\.scales\.y, beginAtZero: false \} \} \},\n      \}\)\);\n    \}'
new_sexo_padrao = """      S.charts.push(new Chart(document.getElementById('chart-desig-sexo-bar'), {
        type: 'bar',
        data: { labels: sexoGroups, datasets: [{ label: 'Proficiência', data: sexoGroups.map(g => getVal('sexo', g)), backgroundColor: ['#1d71b9', '#FFCB04'], borderRadius: 6 }] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));

      S.charts.push(new Chart(document.getElementById('chart-desig-sexo-padrao'), {
        type: 'bar',
        data: { labels: sexoGroups, datasets: [
          { label: 'Abaixo do Básico', data: sexoGroups.map(g => getPct('sexo', g, 'pct_abaixo')), backgroundColor: '#E53935', borderRadius: 4 },
          { label: 'Básico', data: sexoGroups.map(g => getPct('sexo', g, 'pct_basico')), backgroundColor: '#F57C00', borderRadius: 4 },
          { label: 'Adequado', data: sexoGroups.map(g => getPct('sexo', g, 'pct_adequado')), backgroundColor: '#43A047', borderRadius: 4 },
          { label: 'Avançado', data: sexoGroups.map(g => getPct('sexo', g, 'pct_avancado')), backgroundColor: '#1d71b9', borderRadius: 4 }
        ] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } }, datalabels: DL_PCT },
          scales: { ...CHART_DEFAULTS.scales, x: { stacked: true }, y: { stacked: true, max: 100, beginAtZero: true, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } } } }
      }));
    }"""
content = re.sub(old_sexo_bar, new_sexo_padrao, content, count=1)

# 4. Add Interseccionalidade Raça x Gênero before Localização
loc_marker = r'    // ── 4\. Localização ──'
inter_raca_sexo = """    // ── 3B. Interseccionalidade Raça x Gênero ──
    const rsGrupos = [];
    ['Branca', 'Preta', 'Parda'].forEach(r => {
      ['Feminino', 'Masculino'].forEach(s => {
        const k2 = r + ' - ' + s;
        if (dims.raca_sexo && dims.raca_sexo[k2] && dims.raca_sexo[k2][key]) rsGrupos.push(k2);
      });
    });
    if (rsGrupos.length > 0 && document.getElementById('chart-desig-raca-sexo-bar')) {
      const rsColors = rsGrupos.map(g => g.includes('Feminino') ? '#1d71b9' : '#FFCB04');
      S.charts.push(new Chart(document.getElementById('chart-desig-raca-sexo-bar'), {
        type: 'bar',
        data: { labels: rsGrupos.map(g => g.replace(' - ', '\\n')), datasets: [{ label: 'Proficiência', data: rsGrupos.map(g => getVal('raca_sexo', g)), backgroundColor: rsColors, borderRadius: 6 }] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: false }, datalabels: DL_VAL },
          scales: { ...CHART_DEFAULTS.scales, y: { ...CHART_DEFAULTS.scales.y, beginAtZero: false } } },
      }));
      S.charts.push(new Chart(document.getElementById('chart-desig-raca-sexo-padrao'), {
        type: 'bar',
        data: { labels: rsGrupos.map(g => g.replace(' - ', '\\n')), datasets: [
          { label: 'Abaixo do Básico', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_abaixo')), backgroundColor: '#E53935', borderRadius: 4 },
          { label: 'Básico', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_basico')), backgroundColor: '#F57C00', borderRadius: 4 },
          { label: 'Adequado', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_adequado')), backgroundColor: '#43A047', borderRadius: 4 },
          { label: 'Avançado', data: rsGrupos.map(g => getPct('raca_sexo', g, 'pct_avancado')), backgroundColor: '#1d71b9', borderRadius: 4 }
        ] },
        options: { ...CHART_DEFAULTS, plugins: { ...CHART_DEFAULTS.plugins, legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } }, datalabels: DL_PCT },
          scales: { ...CHART_DEFAULTS.scales, x: { stacked: true }, y: { stacked: true, max: 100, beginAtZero: true, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => v + '%' } } } }
      }));
    }

"""
content = re.sub(loc_marker, inter_raca_sexo + loc_marker, content)

# 5. Fix Panorama Multi-Etapa
old_panorama = r'    // ── 8\. PANORAMA MULTI-ETAPA ──\n    const panLabels = \[\]; const panBranca = \[\]; const panPreta = \[\];\n    ETAPAS\.forEach\(et => \{\n      \[\'LP\', \'MT\'\]\.forEach\(dc => \{\n        const k = et \+ \'_\' \+ dc;\n        const b = dims\.raca\?\.Branca\?\.\[k\]\?\.media;\n        const p = dims\.raca\?\.Preta\?\.\[k\]\?\.media;\n        if \(b != null && p != null\) \{\n          panLabels\.push\(ETAPA_LABELS\[et\] \+ \' \' \+ dc\);\n          panBranca\.push\(b\); panPreta\.push\(p\);\n        \}\n      \}\);\n    \}\);\n    if \(panLabels\.length > 0\) \{\n      S\.charts\.push\(new Chart\(document\.getElementById\(\'chart-desig-panorama\'\), \{\n        type: \'bar\',\n        data: \{ labels: panLabels, datasets: \[\n          \{ label: \'Branca\', data: panBranca, backgroundColor: \'#1d71b9CC\', borderRadius: 3, barPercentage: 0\.35, categoryPercentage: 0\.8 \},\n          \{ label: \'Preta\', data: panPreta, backgroundColor: \'#333333CC\', borderRadius: 3, barPercentage: 0\.35, categoryPercentage: 0\.8 \},\n        \] \},\n        options: \{ \.\.\.CHART_DEFAULTS, plugins: \{ \.\.\.CHART_DEFAULTS\.plugins, datalabels: \{ \.\.\.DL_VAL, font: \{ size: 8, weight: \'bold\' \} \} \},\n          scales: \{ \.\.\.CHART_DEFAULTS\.scales, y: \{ \.\.\.CHART_DEFAULTS\.scales\.y, beginAtZero: false \} \} \},\n      \}\)\);\n    \}'
new_panorama = """    // ── 8. PANORAMA MULTI-ETAPA ──
    const panLabels = [];
    const panRacas = { 'Branca': [], 'Parda': [], 'Preta': [], 'Indígena': [], 'Amarela': [] };
    const racaCoresPan = { 'Branca': '#1d71b9CC', 'Parda': '#FFCB04CC', 'Preta': '#333333CC', 'Indígena': '#E53935CC', 'Amarela': '#43A047CC' };
    
    ETAPAS.forEach(et => {
      ['LP', 'MT'].forEach(dc => {
        const k = et + '_' + dc;
        let hasData = false;
        Object.keys(panRacas).forEach(r => {
          if (dims.raca?.[r]?.[k]?.media != null) hasData = true;
        });
        if (hasData) {
          panLabels.push(ETAPA_LABELS[et] + ' ' + dc);
          Object.keys(panRacas).forEach(r => {
            panRacas[r].push(dims.raca?.[r]?.[k]?.media);
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
content = re.sub(old_panorama, new_panorama, content)

# 6. Add "Escolas" to buildDesigMap
# Inside buildDesigMap(): const isCre = S._desigMapMode === 'cre';
old_isCre = r'const isCre = S\._desigMapMode === \'cre\';\n    const dataMap = \{\};\n    const vals = \[\];\n\n    if \(isCre && yearData\.dimensoes\?\.cre\)'
new_isCre = """const isCre = S._desigMapMode === 'cre';
    const isEsc = S._desigMapMode === 'esc';
    const dataMap = {};
    const vals = [];

    if (isEsc && yearData.por_escola) {
      const escolasLookup = yearData.escolas_lookup || S._universalEscolaLookup || {};
      for (const [codEsc, escData] of Object.entries(yearData.por_escola)) {
        const kData = escData?.geral?.[key];
        const geralVal = kData?.media;
        if (geralVal != null) { dataMap[codEsc] = geralVal; vals.push(geralVal); }
      }
    } else if (isCre && yearData.dimensoes?.cre)"""
content = re.sub(old_isCre, new_isCre, content)

old_leaflet_escolas = r'    \} else if \(S\.geo\) \{\n      const munLookup = yearData\.mun_lookup \|\| S\._universalMunLookup \|\| \{\};\n      S\.mapLayer = L\.geoJSON\(S\.geo, \{'
new_leaflet_escolas = """    } else if (isEsc && S.escolasGeo) {
      const escolasLookup = yearData.escolas_lookup || S._universalEscolaLookup || {};
      S.mapLayer = L.geoJSON(S.escolasGeo, {
        pointToLayer: (f, latlng) => L.circleMarker(latlng, { radius: 6, weight: 1, color: '#fff', fillOpacity: 0.9 }),
        style: f => {
          const cod = String(f.properties.cod_escola || f.properties.co_entidade);
          return { fillColor: getClr(dataMap[cod]) };
        },
        onEachFeature: (f, layer) => {
          const cod = String(f.properties.cod_escola || f.properties.co_entidade);
          const nome = escolasLookup[cod] || f.properties.nome || cod;
          const val = dataMap[cod];
          layer.bindTooltip(`<strong>${nome}</strong><br>Proficiência ${discLabel} (${etapaLabel}): ${val != null ? val.toFixed(1) : 'Sem dados'}`, { sticky: true, className: 'map-tooltip' });
        }
      }).addTo(S.map);
    } else if (S.geo) {
      const munLookup = yearData.mun_lookup || S._universalMunLookup || {};
      S.mapLayer = L.geoJSON(S.geo, {"""
content = re.sub(old_leaflet_escolas, new_leaflet_escolas, content)

# 7. Add Escolas map layer toggle logic
old_map_toggle_js = r'  const desigBtnMun = document\.getElementById\(\'desig-btn-layer-mun\'\);\n  const desigBtnCre = document\.getElementById\(\'desig-btn-layer-cre\'\);\n  if \(desigBtnMun\) desigBtnMun\.addEventListener\(\'click\', \(\) => \{\n    S\._desigMapMode = \'mun\';\n    desigBtnMun\.classList\.add\(\'active\'\); desigBtnCre\?\.classList\.remove\(\'active\'\);\n    buildDesigMap\(\);\n  \}\);\n  if \(desigBtnCre\) desigBtnCre\.addEventListener\(\'click\', \(\) => \{\n    S\._desigMapMode = \'cre\';\n    desigBtnCre\.classList\.add\(\'active\'\); desigBtnMun\?\.classList\.remove\(\'active\'\);\n    buildDesigMap\(\);\n  \}\);'
new_map_toggle_js = """  const desigBtnMun = document.getElementById('desig-btn-layer-mun');
  const desigBtnCre = document.getElementById('desig-btn-layer-cre');
  const desigBtnEsc = document.getElementById('desig-btn-layer-esc');
  
  if (desigBtnEsc) desigBtnEsc.addEventListener('click', () => {
    S._desigMapMode = 'esc';
    desigBtnEsc.classList.add('active'); desigBtnMun?.classList.remove('active'); desigBtnCre?.classList.remove('active');
    buildDesigMap();
  });
  if (desigBtnMun) desigBtnMun.addEventListener('click', () => {
    S._desigMapMode = 'mun';
    desigBtnMun.classList.add('active'); desigBtnEsc?.classList.remove('active'); desigBtnCre?.classList.remove('active');
    buildDesigMap();
  });
  if (desigBtnCre) desigBtnCre.addEventListener('click', () => {
    S._desigMapMode = 'cre';
    desigBtnCre.classList.add('active'); desigBtnEsc?.classList.remove('active'); desigBtnMun?.classList.remove('active');
    buildDesigMap();
  });"""
content = re.sub(old_map_toggle_js, new_map_toggle_js, content)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated JS logic successfully!")
