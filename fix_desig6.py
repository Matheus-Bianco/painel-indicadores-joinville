import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the old selects from the HTML
old_html = """      <div class="kpi-strip" style="position:relative" id="desig-kpis">
        <div style="display:none">
          <select id="desig-sel-ano">${anos.map(a => '<option value="' + a + '"' + (a===anos[anos.length-1]?' selected':'') + '>' + a + '</option>').join('')}</select>
        </div>
      </div>
      <div style="display:flex;gap:12px;margin:12px 12px 0">
        <label style="font-size:10px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:4px">
          Etapa:
          <select id="desig-sel-etapa" style="font-size:11px;padding:3px 6px;border:1px solid #ccc;border-radius:4px;background:#fff;color:#333;cursor:pointer">${ETAPAS.map(e => '<option value="' + e + '"' + (e===defaultEtapa?' selected':'') + '>' + ETAPA_LABELS[e] + '</option>').join('')}</select>
        </label>
        <label style="font-size:10px;font-weight:600;color:var(--pri);display:flex;align-items:center;gap:4px">
          Disciplina:
          <select id="desig-sel-disc" style="font-size:11px;padding:3px 6px;border:1px solid #ccc;border-radius:4px;background:#fff;color:#333;cursor:pointer">
            <option value="LP">L\\u00edngua Portuguesa</option>
            <option value="MT">Matem\\u00e1tica</option>
          </select>
        </label>
      </div>"""

new_html = """      <div class="kpi-strip" style="position:relative" id="desig-kpis">
      </div>"""

if old_html in content:
    content = content.replace(old_html, new_html)
else:
    print("Warning: old_html not found")

# 2. Add the injection logic right after bindTopbarFilters();
old_bind = """  // Re-populate topbar filters
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => `<option value="${a}" ${a === anoSel0 ? 'selected' : ''}>${a}</option>`).join('');
  }
  populateCreDropdown();
  populateMunDropdown(S.creSel || null);
  const selCre = document.getElementById('sel-cre');
  if (selCre) selCre.value = S.creSel || '';
  const selMun = document.getElementById('sel-mun');
  if (selMun) selMun.value = S.munSel || '';

  bindTopbarFilters();
  bindRedeToggle();
  updateActiveFilters();"""

new_bind = """  // Re-populate topbar filters
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => `<option value="${a}" ${a === anoSel0 ? 'selected' : ''}>${a}</option>`).join('');
  }
  populateCreDropdown();
  populateMunDropdown(S.creSel || null);
  const selCre = document.getElementById('sel-cre');
  if (selCre) selCre.value = S.creSel || '';
  const selMun = document.getElementById('sel-mun');
  if (selMun) selMun.value = S.munSel || '';

  // Inject Custom Filters into Banner
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
  }

  bindTopbarFilters();
  bindRedeToggle();
  updateActiveFilters();"""

if old_bind in content:
    content = content.replace(old_bind, new_bind)
else:
    print("Warning: old_bind not found")

# 3. Fix the "desig-sel-ano" bindings inside app.js (change to S.anoSel since it's global)
# Line 11002: const anoSel = parseInt(document.getElementById('desig-sel-ano')?.value || S.anoSel);
# Replace with parseInt(S.anoSel)
content = content.replace("const anoSel = parseInt(document.getElementById('desig-sel-ano')?.value || S.anoSel);", "const anoSel = parseInt(S.anoSel);")

# 4. Remove desig-sel-ano event listener
content = re.sub(r"// Sync hidden desig-sel-ano.*?\n.*?document\.getElementById\('desig-sel-ano'\).*?\n", "", content)

# 5. Fix the map layer toggle buttons CSS class to match standard!
# <button id="desig-btn-layer-esc">Escolas</button> -> <button id="desig-btn-layer-esc" class="map-layer-btn">Escolas</button>
old_buttons = """      <div class="map-layer-toggle">
        <button id="desig-btn-layer-esc">Escolas</button>
        <button id="desig-btn-layer-mun" class="active">Municípios</button>
        <button id="desig-btn-layer-cre">CREs</button>
      </div>"""
new_buttons = """      <div class="map-layer-toggle">
        <button id="desig-btn-layer-mun" class="map-layer-btn active">Municípios</button>
        <button id="desig-btn-layer-cre" class="map-layer-btn">CREs</button>
        <button id="desig-btn-layer-esc" class="map-layer-btn">Escolas</button>
      </div>"""

if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)
else:
    print("Warning: old_buttons not found")

# 6. Make sure axes are adaptive for stacked bars (they already are, since Math.max)
# Wait, user said: "mudei aqui a etapa para 3 serie EM, e os valores ultrapassaram os valores do eixo Y"
# In my stacked_bar_code:
# max_val = Math.max(0, ...), but the max for a stacked bar is the SUM of the values!
# Ah! A stacked bar Y-axis goes up to the SUM of all datasets! So we must use sum!
# Wait, let's fix stacked_bar_code max calculation.
old_max = """    const max_val = Math.max(0, ...labels.map((_, i) => {
      let m = 0;
      dsets.forEach(ds => {
        const v = ds.data[i];
        if (v !== null) m = Math.max(m, v);
      });
      return m;
    }));"""
new_max = """    const max_val = Math.max(0, ...labels.map((_, i) => {
      let sum = 0;
      dsets.forEach(ds => {
        const v = ds.data[i];
        if (v !== null) sum += v;
      });
      return sum;
    }));"""
if old_max in content:
    content = content.replace(old_max, new_max)
else:
    print("Warning: old_max not found")

with open(path, 'w', encoding='utf-8', newline='\\n') as f:
    f.write(content)
print("Fixes applied successfully!")
