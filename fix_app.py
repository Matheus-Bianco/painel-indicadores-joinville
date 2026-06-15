import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix header filters
old_header = r"""  // Populate global topbar sel-ano with desig years
  const anoSel0 = S.anoSel ? parseInt(S.anoSel) : anos[anos.length - 1];
  const selAnoGlobal = document.getElementById('sel-ano');
  if (selAnoGlobal) {
    selAnoGlobal.innerHTML = anos.map(a => '<option value="' + a + '"' + (a === anoSel0 ? ' selected' : '') + '>' + a + '</option>').join('');
    S.anoSel = String(anoSel0);
  }"""

new_header = r"""  const anoSel0 = S.anoSel ? parseInt(S.anoSel) : anos[anos.length - 1];
  S.anoSel = String(anoSel0);"""

content = content.replace(old_header, new_header)

old_build_charts = r"""  function buildCharts() {"""

new_build_charts = r"""  // Re-populate topbar filters
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

  function buildCharts() {"""

content = content.replace(old_build_charts, new_build_charts)

# 2. Fix Etapa and Disciplina style (remove class="filter-select")
old_etapa = r"""<select id="desig-sel-etapa" class="filter-select" style="font-size:10px;padding:2px 6px">"""
new_etapa = r"""<select id="desig-sel-etapa" style="font-size:11px;padding:3px 6px;border:1px solid #ccc;border-radius:4px;background:#fff;color:#333;cursor:pointer">"""
content = content.replace(old_etapa, new_etapa)

old_disc = r"""<select id="desig-sel-disc" class="filter-select" style="font-size:10px;padding:2px 6px">"""
new_disc = r"""<select id="desig-sel-disc" style="font-size:11px;padding:3px 6px;border:1px solid #ccc;border-radius:4px;background:#fff;color:#333;cursor:pointer">"""
content = content.replace(old_disc, new_disc)

# 3. Add TURNO_COLORS if missing (wait, it's NOT missing, but maybe we can make sure it works)
# Wait, TURNO_COLORS is already there. No crash.

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Applied fixes.")
