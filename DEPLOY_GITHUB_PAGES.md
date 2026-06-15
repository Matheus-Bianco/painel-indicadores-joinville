# ─────────────────────────────────────────────────────────
# DEPLOY — Painel Indicadores RS → GitHub Pages
# Execute esses comandos na pasta painel/ após criar o repo
# ─────────────────────────────────────────────────────────

# 1. Inicializar git dentro da pasta painel/
cd "c:\Users\mathe\OneDrive\Desktop\Trabalhos\06. UNESCO\04. Produto 4_Indicadores Educacionais\painel"
git init
git branch -M main

# 2. Adicionar remote (substituir SEU_USUARIO e NOME_REPO)
git remote add origin https://github.com/SEU_USUARIO/NOME_REPO.git

# 3. Primeiro commit
git add .
git commit -m "feat: Painel Indicadores Educacionais RS v12 - deploy inicial"

# 4. Push
git push -u origin main

# ─────────────────────────────────────────────────────────
# GitHub Pages: Settings → Pages → Branch: main → / (root)
# URL final: https://SEU_USUARIO.github.io/NOME_REPO/
# ─────────────────────────────────────────────────────────

# Para updates futuros (após regenerar JSONs):
# git add dados/
# git commit -m "data: atualiza JSONs Censo Escolar"
# git push
