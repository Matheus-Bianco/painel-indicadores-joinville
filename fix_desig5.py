import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace map toggles
old_toggles = """  // Map layer toggle
  const desigBtnMun = document.getElementById('desig-btn-layer-mun');
  const desigBtnCre = document.getElementById('desig-btn-layer-cre');
  if (desigBtnMun) desigBtnMun.addEventListener('click', () => {
    S._desigMapMode = 'mun';
    desigBtnMun.classList.add('active'); desigBtnCre?.classList.remove('active');
    buildDesigMap();
  });
  if (desigBtnCre) desigBtnCre.addEventListener('click', () => {
    S._desigMapMode = 'cre';
    desigBtnCre.classList.add('active'); desigBtnMun?.classList.remove('active');
    buildDesigMap();
  });"""

new_toggles = """  // Map layer toggle
  const desigBtnEsc = document.getElementById('desig-btn-layer-esc');
  const desigBtnMun = document.getElementById('desig-btn-layer-mun');
  const desigBtnCre = document.getElementById('desig-btn-layer-cre');
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

if old_toggles in content:
    content = content.replace(old_toggles, new_toggles)

# Replace buildDesigMap
# I'll just use regex to match from function buildDesigMap() { to the end of the function.
start_str = "  function buildDesigMap() {"
end_str = "    };\n  }"

new_build_desig_map = """  function buildDesigMap() {
    if (S.map) { S.map.remove(); S.map = null; S.mapLayer = null; }
    if (S.mapLegend) { S.mapLegend.remove(); S.mapLegend = null; }
    const mapEl = document.getElementById('desig-map-leaflet');
    const tableBody = document.querySelector('#desig-table tbody');
    if (!mapEl || !tableBody) return;

    const anoSel = parseInt(S.anoSel);
    const etapa = document.getElementById('desig-sel-etapa').value;
    const disc = document.getElementById('desig-sel-disc').value;
    const key = etapa + '_' + disc;
    const yearData = dd.anos.find(a => a.ano === anoSel);
    if (!yearData) return;

    if (!S._desigMapMode) S._desigMapMode = 'mun';
    const mode = S._desigMapMode;
    const isCre = mode === 'cre';
    const isEsc = mode === 'esc';
    
    const dataMap = {};
    const vals = [];
    let tableData = [];

    const formatPct = (val) => val != null ? val.toFixed(1) + '%' : '-';
    const formatMed = (val) => val != null ? val.toFixed(1) : '-';

    if (isEsc && yearData.por_escola) {
      const escolasLookup = yearData.escolas_lookup || S._universalEscolaLookup || {};
      for (const [codEsc, escData] of Object.entries(yearData.por_escola)) {
        const kData = escData?.geral?.[key];
        const geralVal = kData?.media;
        if (geralVal != null) { 
          dataMap[codEsc] = geralVal; 
          vals.push(geralVal);
          tableData.push({
            nome: escolasLookup[codEsc]?.nome || codEsc,
            cod: codEsc,
            media: kData.media,
            avancado: kData.pct_avancado,
            adequado: kData.pct_adequado,
            basico: kData.pct_basico,
            abaixo: kData.pct_abaixo
          });
        }
      }
    } else if (isCre && yearData.dimensoes?.cre) {
      const creLookup = yearData.cre_lookup || {};
      for (const [codCre, creData] of Object.entries(yearData.dimensoes.cre)) {
        const kData = creData[key];
        const val = kData?.media;
        const paddedCode = codCre.padStart(2, '0');
        if (val != null) { 
          dataMap[paddedCode] = val; 
          vals.push(val); 
          tableData.push({
            nome: creLookup[codCre] || codCre + 'ª CRE',
            cod: paddedCode,
            media: kData.media,
            avancado: kData.pct_avancado,
            adequado: kData.pct_adequado,
            basico: kData.pct_basico,
            abaixo: kData.pct_abaixo
          });
        }
      }
    } else if (!isEsc && !isCre && yearData.por_municipio) {
      const nameToCod = {};
      const lookup = S._universalMunLookup || {};
      for (const [cod, nome] of Object.entries(lookup)) nameToCod[nome] = cod;
      if (S.geo) S.geo.features.forEach(f => { if (f.properties.nome) nameToCod[f.properties.nome] = String(f.properties.cod_mun); });
      
      for (const [munName, munData] of Object.entries(yearData.por_municipio)) {
        const kData = munData?.geral?.[key];
        const geralVal = kData?.media;
        const cod = nameToCod[munName];
        if (geralVal != null && cod) { 
          dataMap[cod] = geralVal; 
          vals.push(geralVal); 
          tableData.push({
            nome: munName,
            cod: cod,
            media: kData.media,
            avancado: kData.pct_avancado,
            adequado: kData.pct_adequado,
            basico: kData.pct_basico,
            abaixo: kData.pct_abaixo
          });
        }
      }
    }

    // Populate Table
    tableData.sort((a, b) => b.media - a.media);
    S._desigTableData = tableData;
    
    function renderTable(filterTxt = '') {
      const tbody = document.querySelector('#desig-table tbody');
      if (!tbody) return;
      const lowerF = filterTxt.toLowerCase();
      const filtered = tableData.filter(t => t.nome.toLowerCase().includes(lowerF) || t.cod.includes(lowerF));
      
      tbody.innerHTML = filtered.map(t => `
        <tr>
          <td style="text-align:left;font-weight:600">${t.nome} <span style="color:#999;font-size:9px">(${t.cod})</span></td>
          <td style="font-weight:700">${formatMed(t.media)}</td>
          <td style="color:#1d71b9">${formatPct(t.avancado)}</td>
          <td style="color:#43A047">${formatPct(t.adequado)}</td>
          <td style="color:#F57C00">${formatPct(t.basico)}</td>
          <td style="color:#E53935">${formatPct(t.abaixo)}</td>
        </tr>
      `).join('');
    }
    renderTable('');
    document.getElementById('desig-table-search')?.addEventListener('input', (e) => renderTable(e.target.value));

    if (vals.length === 0) { mapEl.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999">Sem dados georreferenciados</div>'; return; }

    vals.sort((a, b) => a - b);
    const breaks = [];
    for (let i = 0; i < MAP_SCALE.length; i++) {
      const idx = Math.min(Math.floor((i / MAP_SCALE.length) * vals.length), vals.length - 1);
      breaks.push(vals[idx]);
    }
    function getClr(v) {
      if (v == null) return '#f0f0f0';
      for (let i = breaks.length - 1; i >= 0; i--) { if (v >= breaks[i]) return MAP_SCALE[i]; }
      return MAP_SCALE[0];
    }

    S.map = L.map(mapEl).setView([-29.8, -53.5], 6);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', {
      attribution: '© CartoDB © OSM', maxZoom: 18,
    }).addTo(S.map);

    const discLabel = disc === 'LP' ? 'Língua Portuguesa' : 'Matemática';
    const etapaLabel = ETAPA_LABELS[etapa] || etapa;

    if (isEsc && S.escolasGeo) {
      S.mapLayer = L.geoJSON(S.escolasGeo, {
        pointToLayer: (f, latlng) => {
          const cod = String(f.properties.cod);
          const val = dataMap[cod];
          if (val == null) return null; // Only show schools with data
          return L.circleMarker(latlng, {
            radius: 5, fillColor: getClr(val), color: '#fff', weight: 1, opacity: 1, fillOpacity: 0.9
          });
        },
        onEachFeature: (f, layer) => {
          if (!layer) return;
          const cod = String(f.properties.cod);
          const nome = f.properties.nome;
          const val = dataMap[cod];
          layer.bindTooltip(`<strong>${nome}</strong> (${cod})<br>Proficiência ${discLabel} (${etapaLabel}): ${val != null ? val.toFixed(1) : 'Sem dados'}`, { sticky: true, className: 'map-tooltip' });
        }
      }).addTo(S.map);
    } else if (isCre && S.creGeo) {
      const creLookup = {};
      const creLookupRaw = yearData.cre_lookup || {};
      for (const [k, v] of Object.entries(creLookupRaw)) creLookup[k.padStart(2, '0')] = v;
      S.mapLayer = L.geoJSON(S.creGeo, {
        style: f => {
          const cod = String(f.properties.cod_cre || f.properties.CD_GEOCODR || '');
          return { fillColor: getClr(dataMap[cod]), weight: 1.5, color: '#fff', fillOpacity: 0.8 };
        },
        onEachFeature: (f, layer) => {
          const cod = String(f.properties.cod_cre || f.properties.CD_GEOCODR || '');
          const nome = creLookup[cod] || f.properties.nome || cod;
          const val = dataMap[cod];
          layer.bindTooltip(`<strong>${nome}</strong><br>Proficiência ${discLabel} (${etapaLabel}): ${val != null ? val.toFixed(1) : 'Sem dados'}`, { sticky: true, className: 'map-tooltip' });
        }
      }).addTo(S.map);
    } else if (S.geo && !isEsc) {
      const munLookup = yearData.mun_lookup || S._universalMunLookup || {};
      S.mapLayer = L.geoJSON(S.geo, {
        style: f => {
          const cod = String(f.properties.cod_mun);
          return { fillColor: getClr(dataMap[cod]), weight: 0.8, color: '#fff', fillOpacity: 0.85 };
        },
        onEachFeature: (f, layer) => {
          const cod = String(f.properties.cod_mun);
          const nome = munLookup[cod] || f.properties.nome || cod;
          const val = dataMap[cod];
          layer.bindTooltip(`<strong>${nome}</strong><br>Proficiência ${discLabel} (${etapaLabel}): ${val != null ? val.toFixed(1) : 'Sem dados'}`, { sticky: true, className: 'map-tooltip' });
        }
      }).addTo(S.map);
    }

    // Legend
    S.mapLegend = L.control({ position: 'bottomright' });
    S.mapLegend.onAdd = () => {
      const div = L.DomUtil.create('div', 'map-legend');
      div.innerHTML = '<strong>Proficiência ' + discLabel + '</strong><br>' +
        MAP_SCALE.map((c, i) => {
          const from = i === 0 ? 'Menor' : breaks[i]?.toFixed(0);
          const to = i === MAP_SCALE.length - 1 ? 'Maior' : breaks[i + 1]?.toFixed(0);
          return `<div style="display:flex;align-items:center;gap:6px"><span style="display:inline-block;width:12px;height:12px;background:${c};border:1px solid rgba(0,0,0,.1)"></span><span style="font-size:10px">${from} a ${to}</span></div>`;
        }).join('');
      return div;
    };
    S.mapLegend.addTo(S.map);
  }"""

match = re.search(r'  function buildDesigMap\(\) \{.*?\n    \};\n    S\.mapLegend\.addTo\(S\.map\);\n  \}', content, flags=re.DOTALL)
if match:
    content = content.replace(match.group(0), new_build_desig_map)
else:
    print("Could not find buildDesigMap")

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated Map logic!")
