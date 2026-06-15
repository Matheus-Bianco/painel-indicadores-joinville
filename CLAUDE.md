# Painel de Indicadores Abertos — Educação Joinville/SC

> **Refatoração em andamento** a partir do painel original da UNESCO/SEDUC-RS (projeto-base estadual).
> Repositório-base ORIGINAL (zona proibida): `06. UNESCO\04. Produto 4_Indicadores Educacionais` (repo `piloto_unesco`). Nunca operar lá.

## Visão geral
Painel de Indicadores Abertos da Educação para a **Secretaria de Educação de Joinville/SC**.
Adaptado do painel estadual (RS) para o recorte **municipal de Joinville** (IBGE 4209102).
Arquitetura: GitHub Pages + JSON (Python ETL) + HTML/JS/CSS + Chart.js 4 + Leaflet 1.9.

## Decisões de arquitetura (refatoração Joinville)
- **Unidade geográfica:** por **ESCOLA** (mapa de pontos via `NU_LATITUDE`/`NU_LONGITUDE` do Censo + tabela por escola). Substitui os mapas coropléticos por município/CRE do projeto RS.
- **Rede:** apenas **MUNICIPAL** de Joinville (`TP_DEPENDENCIA=3`).
- **Contorno do mapa:** `painel/dados/joinville_municipio.geojson` (IBGE 4209102, prop `codarea`).
- **Avaliação local (aba SAERS):** OCULTA por enquanto (decidir depois — candidata: Diagnóstica Bússola).
- **Branding:** título "Painel de Indicadores Abertos" / sub "Educação — Joinville/SC". Logo: `painel/img/logo_joinville.png`.

## Estrutura do projeto
```
painel/           → Frontend (index.html, js/app.js, css/styles.css, dados/*.json)
etl_*.py          → Scripts ETL que geram os JSONs
00. Bases de Dados/ → Fontes INEP (Censo Escolar, Rendimento, TDI, SAEB)
```

## Seções do painel (5)
1. **Acesso e Matrículas** — V1 ✅
2. **Infraestrutura** — V1 ✅
3. **Docência** — V1 ✅
4. **Fluxo e Rendimento** — V1 ✅
5. **IDEB / SAEB** — V1 ✅

## Arquitetura JS
- Estado central: objeto `S` (S.data, S.geo, S.fluxo, S.saeb, S.infra, S.doc)
- Filtros globais: `S.anoSel`, `S.creSel`, `S.munSel`
- Render loop: `refreshActiveTab()` → clica tab ativa → `renderX()`
- Cada seção: `destroyCharts()` + `destroyMap()` + `innerHTML` + bindings
- Sticky headers: `<div class="section-sticky">` com `sectionBanner()` + KPI strip

## Convenções de código
- Datalabels: presets `DL_BAR`, `DL_BAR_PCT`, `DL_LINE`, `DL_LINE_BOLD`, `DL_BAR_BOLD`
- Font size: 11px bold para todos os datalabels
- Mapas: Leaflet com `buildXxxMap()`, choropleth com escala semafórica 4 níveis
- Tabelas: `xxxBuildMunTable()` com sort, search, click-to-filter
- CSS Grid > Flexbox para cards simétricos
- Nunca misturar classes CSS globais com grids JS inline

## ETL Scripts
| Script | JSON gerado | Fonte |
|--------|-------------|-------|
| `etl_censo_escolar.py` | `4_1_acesso_matriculas.json` | Microdados Censo |
| `etl_infra_docentes.py` | `4_5_infraestrutura.json` + `4_5_docentes.json` | Censo |
| `etl_fluxo_rendimento.py` | `4_3_fluxo_rendimento.json` | INEP Rendimento + TDI |
| `etl_saeb.py` | `4_6_saeb.json` | SAEB |
| `etl_funil_turma_locdif.py` | `4_1_funil_turma_locdif.json` | Censo |

## Dados-chave
- **Joinville Rede Municipal:** `TP_DEPENDENCIA=3`, `CO_MUNICIPIO=4209102` (`SG_UF='SC'`)
- Unidade de análise: **escola** (não há mais município/CRE como dimensão)
- Anos disponíveis (a confirmar pós-extração): 2019-2025 (Censo), Rendimento/TDI, SAEB/IDEB
- GeoJSON: `joinville_municipio.geojson` (contorno). Pontos de escola gerados pelo ETL via lat/long do Censo.
- ⚠️ Bases em `00. Bases de Dados/` ainda são as do RS — substituir por extrações de Joinville na Fase 2.

---

## Regras Universais do Matheus

### Idioma e comunicação
- Falar sempre em **português BR**
- Quando Matheus escrever em inglês: ativar modo prática, responder em inglês, corrigir erros com seção "✏️ Grammar Note"
- Se escrever em português: voltar ao português imediatamente

### Workflow
- **NÃO** abrir browser para verificar deploys, testar resultados visuais ou pesquisar
- Matheus testa manualmente no browser dele e dá retorno no chat
- Usar `search_web` para pesquisas quando necessário

### Visualização de dados
- Nunca pizza/donut com mais de 3 variáveis
- Sempre colocar datalabels em todos os gráficos
- Sempre aumentar eixo Y para que labels não fiquem ocultos
- Fontes de dados sempre no rodapé (nunca no topo)
- Layout compacto estilo Power BI: visualizações cabem em uma viewport

### CSS/Layout
- CSS Grid > Flexbox para altura igual automática
- Nunca misturar classes CSS globais com grids JS inline
- Containers separados para componentes atualizados independentemente
- Não usar float, position:absolute ou display:inline-block para grids de cards

### Design System — Tema Claro
- Paleta: `--pri:#0D47A1`, `--gold:#D4A84B`, `--bg:#f4f6f9`
- Fonte: Inter (Google Fonts), 300-800
- KPI cards: borda lateral 4px, gradiente sutil, sparkline SVG, count-up animation
- Hover: translateY(-3px) + box-shadow expandida
- Separadores de seção: badge 28x28px + ícone + texto uppercase + linha gradiente
