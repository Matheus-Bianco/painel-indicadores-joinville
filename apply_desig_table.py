import re

path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject HTML for table
old_map_html = r'      <div class="chart-card"><div class="chart-title">Proficiência por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">\$\{FONTE\}</div></div>\n    </div>'
new_map_html = """      <div class="chart-card"><div class="chart-title">Proficiência por CRE</div><div style="height:440px"><canvas id="chart-desig-cre"></canvas></div><div class="chart-source">${FONTE}</div></div>
    </div>
    
    <div class="chart-card" id="desig-table-container" style="display:none;margin-top:16px;overflow-x:auto">
      <div class="chart-title" style="margin-bottom:12px">Proficiência por Escolas</div>
      <table id="desig-table" class="data-table">
        <thead>
          <tr>
            <th style="text-align:left">Escola</th>
            <th style="text-align:right">Média</th>
            <th style="text-align:right">% Avançado</th>
            <th style="text-align:right">% Adequado</th>
            <th style="text-align:right">% Básico</th>
            <th style="text-align:right">% Abaixo</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>"""
content = re.sub(old_map_html, new_map_html, content)

# 2. Add table logic to buildDesigMap
# First, update variables at the start of buildDesigMap
old_vars = r'    const dataMap = \{\};\n    const vals = \[\];'
new_vars = """    const dataMap = {};
    const vals = [];
    const tableData = [];"""
content = re.sub(old_vars, new_vars, content)

# Inside the `if (isEsc && yearData.por_escola) {` block
old_isEsc = r'        if \(geralVal != null\) \{ dataMap\[codEsc\] = geralVal; vals\.push\(geralVal\); \}'
new_isEsc = """        if (geralVal != null) { 
          dataMap[codEsc] = geralVal; vals.push(geralVal); 
          tableData.push({
            nome: escolasLookup[codEsc]?.nome || codEsc,
            cod: codEsc,
            media: kData.media,
            avancado: kData.pct_avancado,
            adequado: kData.pct_adequado,
            basico: kData.pct_basico,
            abaixo: kData.pct_abaixo
          });
        }"""
content = re.sub(old_isEsc, new_isEsc, content)

# At the end of buildDesigMap
old_legend = r'      return div;\n    \};\n    S\.mapLegend\.addTo\(S\.map\);\n  \}'
new_legend = """      return div;
    };
    S.mapLegend.addTo(S.map);

    // Update table
    const tableCont = document.getElementById('desig-table-container');
    const tableBody = document.querySelector('#desig-table tbody');
    if (isEsc && tableCont && tableBody) {
      tableCont.style.display = 'block';
      tableData.sort((a, b) => (b.media || 0) - (a.media || 0));
      tableBody.innerHTML = tableData.map(d => `
        <tr>
          <td style="text-align:left;font-weight:500">${d.nome}</td>
          <td style="text-align:right;font-weight:600;color:var(--pri)">${d.media != null ? d.media.toFixed(1) : '-'}</td>
          <td style="text-align:right">${d.avancado != null ? d.avancado.toFixed(1) + '%' : '-'}</td>
          <td style="text-align:right">${d.adequado != null ? d.adequado.toFixed(1) + '%' : '-'}</td>
          <td style="text-align:right">${d.basico != null ? d.basico.toFixed(1) + '%' : '-'}</td>
          <td style="text-align:right;color:#C62828">${d.abaixo != null ? d.abaixo.toFixed(1) + '%' : '-'}</td>
        </tr>
      `).join('');
    } else if (tableCont) {
      tableCont.style.display = 'none';
    }
  }"""
content = re.sub(old_legend, new_legend, content)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Updated table logic successfully!")
