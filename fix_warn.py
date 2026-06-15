import re
path = r'painel\js\app.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_warn = """    // Warning for 2_EF
    const avisoEl = document.getElementById('desig-aviso');
    if (avisoEl) {
      if (etapa === '2_EF') {
        avisoEl.style.display = 'inline';
        avisoEl.textContent = '⚠️ O 2º ano EF não possui dados de raça e sexo (questionário não aplicado).';
      } else { avisoEl.style.display = 'none'; }
    }"""
new_warn = """    // Warning for 2_EF and 2022
    const avisoEl = document.getElementById('desig-aviso');
    if (avisoEl) {
      if (etapa === '2_EF') {
        avisoEl.style.display = 'inline';
        avisoEl.textContent = '⚠️ O 2º ano EF não possui dados de raça e sexo (questionário não aplicado).';
      } else if (anoSel === 2022) {
        avisoEl.style.display = 'inline';
        avisoEl.textContent = '⚠️ Os dados oficiais de 2022 não possuem as colunas de Cor/Raça e Sexo preenchidas. Estes painéis ficarão vazios ou omitidos neste ano.';
      } else { avisoEl.style.display = 'none'; }
    }"""
if old_warn in content:
    content = content.replace(old_warn, new_warn)
else:
    # Try regex
    content = re.sub(r'// Warning for 2_EF.*?avisoEl\.style\.display = \'none\'; \}\n    \}', new_warn, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
print("Added warning!")
