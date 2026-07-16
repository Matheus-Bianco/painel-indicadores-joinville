// ============================================================
// REDES - Visao por Redes (Joinville / dependencias administrativas)
// Comparativo Municipal | Estadual | Federal | Filantropica | Particular
// ============================================================

async function ensureRedes() {
  if (S.redesData) { await renderRedes(); return; }
  if (S._redesLoading) return;
  S._redesLoading = true;
  const main = document.getElementById('main-content');
  if (main) {
    main.innerHTML = `
      <div class="loading">
        <div class="spinner"></div>
        <span>Carregando Visão por Redes...</span>
      </div>`;
  }
  try {
    const resp = await fetch('dados/4_1_redes.json?_cb=' + Date.now());
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    S.redesData = await resp.json();
    await renderRedes();
  } catch (err) {
    if (main) {
      main.innerHTML = `
        <div class="loading" style="color:#C62828;text-align:center;padding:40px">
          <span>Não foi possível carregar os dados de Redes.<br>${err.message}</span>
          <button onclick="ensureRedes()" style="margin-top:14px;padding:8px 18px;border-radius:6px;border:1px solid #C62828;background:#fff;color:#C62828;cursor:pointer;font-weight:600">Tentar novamente</button>
        </div>`;
    }
  } finally {
    S._redesLoading = false;
  }
}

async function renderRedes() {
  const main = document.getElementById('main-content');
  destroyCharts();
  destroyMap();
  document.body.classList.remove('sidebar-hidden');

  const rd = S.redesData;
  if (!rd?.por_rede) {
    main.innerHTML = `<div class="placeholder-view"><div style="font-size:15px;font-weight:600">Visão por Redes</div><div style="font-size:11px;opacity:.7">Dados não disponíveis</div></div>`;
    return;
  }

  const meta = rd.metadata || {};
  const redes = meta.redes || ['Municipal', 'Estadual', 'Federal', 'Filantropica', 'Particular'];
  const cores = meta.cores || { Municipal: '#00897B', Estadual: '#0D47A1', Federal: '#7B1FA2', Filantropica: '#6D4C41', Particular: '#F57C00' };
  const anos = (meta.anos || Object.keys(rd.por_rede)).slice().sort();
  const anoSel = (S.anoSel && (rd.por_rede[S.anoSel] || anos.includes(S.anoSel))) ? S.anoSel : anos[anos.length - 1];
  S.anoSel = anoSel;

  const geoLabel = (typeof JV_MODE !== 'undefined' && JV_MODE)
    ? (JV.munNome + '/' + JV.uf)
    : 'Joinville/SC';

  // Joinville: dados ja no recorte municipal - sem filtro geo sob demanda
  const porRedeAll = rd.por_rede;

  const anoData = porRedeAll[anoSel] || {};
  const anoPrev = anos[anos.indexOf(anoSel) - 1];
  const prevData = anoPrev ? (porRedeAll[anoPrev] || {}) : {};

  const totEsc = redes.reduce((s, r) => s + (anoData[r]?.escolas || 0), 0);
  const totMat = redes.reduce((s, r) => s + (anoData[r]?.mat_total || 0), 0);
  const totDoc = redes.reduce((s, r) => s + (anoData[r]?.docentes || 0), 0);
  const prevEsc = redes.reduce((s, r) => s + (prevData[r]?.escolas || 0), 0);
  const prevMat = redes.reduce((s, r) => s + (prevData[r]?.mat_total || 0), 0);
  const prevDoc = redes.reduce((s, r) => s + (prevData[r]?.docentes || 0), 0);
  const majRede = [...redes].sort((a, b) => (anoData[b]?.mat_total || 0) - (anoData[a]?.mat_total || 0))[0];
  const majPct = totMat ? ((anoData[majRede]?.mat_total || 0) / totMat * 100) : 0;
  const prevMajPct = (() => {
    const prevTot = redes.reduce((s, r) => s + (prevData[r]?.mat_total || 0), 0);
    if (!prevTot) return null;
    const prevMaj = [...redes].sort((a, b) => (prevData[b]?.mat_total || 0) - (prevData[a]?.mat_total || 0))[0];
    return 100 * (prevData[prevMaj]?.mat_total || 0) / prevTot;
  })();

  const pctFn = (cur, old) => (cur != null && old != null && old !== 0) ? ((cur - old) / old * 100) : null;
  const absFn = (cur, old) => (cur != null && old != null) ? (cur - old) : null;
  const refLabel = anoPrev ? `vs ${anoPrev}` : '';

  function sparkline(vals, color) {
    if (!vals.length || vals.every(v => !v)) return '';
    const max = Math.max(...vals, 1);
    const min = Math.min(...vals);
    const w = 64, h = 22, pad = 2;
    const pts = vals.map((v, i) => {
      const x = pad + (i / Math.max(vals.length - 1, 1)) * (w - pad * 2);
      const y = h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
      return `${x},${y}`;
    }).join(' ');
    const last = pts.split(' ').pop().split(',');
    return `<svg class="kpi-sparkline" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round"/>
      <circle cx="${last[0]}" cy="${last[1]}" r="2.5" fill="${color}"/>
    </svg>`;
  }

  const histEsc = anos.map(a => redes.reduce((s, r) => s + (porRedeAll[a]?.[r]?.escolas || 0), 0));
  const histMat = anos.map(a => redes.reduce((s, r) => s + (porRedeAll[a]?.[r]?.mat_total || 0), 0));
  const histDoc = anos.map(a => redes.reduce((s, r) => s + (porRedeAll[a]?.[r]?.docentes || 0), 0));

  const kpis = [
    { label: 'Escolas', val: totEsc, prev: prevEsc, icon: 'img/icons/escola.png', accent: 'green', spark: histEsc, color: '#1d71b9' },
    { label: 'Matrículas', val: totMat, prev: prevMat, icon: 'img/icons/matriculas.png', accent: 'green', spark: histMat, color: '#00AB4E' },
    { label: 'Docentes', val: totDoc, prev: prevDoc, icon: 'img/icons/sec_docentes.png', accent: 'blue', spark: histDoc, color: '#1565C0' },
    { label: `Maior rede (${majRede})`, val: majPct, prev: prevMajPct, icon: 'img/icons/panorama.png', accent: 'yellow', spark: null, color: '#FFCB04', isPct: true },
  ];

  main.innerHTML = `
    <div class="section-sticky">
      ${sectionBanner('img/icons/panorama.png', 'Visão por Redes', `Comparativo por Dependência — ${geoLabel}`, { redeToggle: false })}
      <div class="kpi-strip" id="redes-kpis"></div>
    </div>

    <div class="section-content" style="padding:10px 16px 50px">
      <div class="section-divider">
        <span class="section-divider-icon"><img src="img/icons/sec_evolucao.png" alt=""></span>
        <span class="section-divider-text">Histórico por Mantenedora${geoSuffix()}</span>
        <span class="section-divider-line"></span>
      </div>

      <div class="charts-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="chart-card">
          <div class="chart-title" id="redes-mat-hist-title">Matrículas por Rede (${anos[0]}–${anos[anos.length - 1]})${geoSuffix()}</div>
          <div class="flx-toggle-pills" id="redes-hist-etapa-pills" style="position:relative;z-index:6;margin:4px 0 8px">
            ${[
              { key: 'mat_total', label: 'Total' },
              { key: 'mat_infantil', label: 'Infantil' },
              { key: 'mat_fund_ai', label: 'Anos Iniciais' },
              { key: 'mat_fund_af', label: 'Anos Finais' },
              { key: 'mat_medio', label: 'Médio' },
              { key: 'mat_eja', label: 'EJA' },
            ].map(e => `
              <button type="button" class="flx-pill redes-hist-etapa-pill${(S.redesHistEtapaSel || 'mat_total') === e.key ? ' active' : ''}"
                data-etapa="${e.key}" style="--pill-color:#0D47A1">${e.label}</button>
            `).join('')}
          </div>
          <div style="height:230px"><canvas id="chart-redes-mat-hist"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
        <div class="chart-card">
          <div class="chart-title">Escolas por Rede (${anos[0]}–${anos[anos.length - 1]})${geoSuffix()}</div>
          <div style="height:230px"><canvas id="chart-redes-esc-hist"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
      </div>

      <div class="section-divider">
        <span class="section-divider-icon"><img src="img/icons/matriculas.png" alt=""></span>
        <span class="section-divider-text">Perfil da Oferta — ${anoSel}${geoSuffix()}</span>
        <span class="section-divider-line"></span>
      </div>

      <div id="redes-etapa-filters" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 10px;padding:0 2px">
        <span style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.4px;margin-right:4px">Etapa</span>
        ${[
          { key: '', label: 'Todas' },
          { key: 'mat_infantil', label: 'Infantil' },
          { key: 'mat_fund_ai', label: 'Anos Iniciais' },
          { key: 'mat_fund_af', label: 'Anos Finais' },
          { key: 'mat_medio', label: 'Médio' },
          { key: 'mat_eja', label: 'EJA' },
        ].map(e => `
          <button type="button" class="flx-pill redes-etapa-pill${(S.redesEtapaSel || '') === e.key ? ' active' : ''}"
            data-etapa="${e.key}" style="--pill-color:#0D47A1">${e.label}</button>
        `).join('')}
      </div>

      <div class="charts-grid" style="display:grid;grid-template-columns:1.2fr 1fr;gap:10px">
        <div class="chart-card">
          <div class="chart-title" id="redes-etapas-title">Matrículas por Etapa e Rede — ${anoSel}${geoSuffix()}</div>
          <div style="height:250px"><canvas id="chart-redes-etapas"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
        <div class="chart-card">
          <div class="chart-title" id="redes-share-title">Participação nas Matrículas — ${anoSel}${geoSuffix()}</div>
          <div style="height:250px"><canvas id="chart-redes-share"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
      </div>

      <div class="charts-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="chart-card">
          <div class="chart-title" id="redes-turno-title">Forma de Oferta — Diurno × Noturno — ${anoSel}${geoSuffix()}</div>
          <div style="height:230px"><canvas id="chart-redes-turno"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
        <div class="chart-card">
          <div class="chart-title" id="redes-integral-title">Educação Integral por Rede — ${anoSel}${geoSuffix()}</div>
          <div style="height:230px"><canvas id="chart-redes-integral"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
      </div>

      <div class="section-divider">
        <span class="section-divider-icon"><img src="img/icons/sec_docentes.png" alt=""></span>
        <span class="section-divider-text">Docentes e Razão Aluno/Professor${geoSuffix()}</span>
        <span class="section-divider-line"></span>
      </div>

      <div class="charts-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
        <div class="chart-card">
          <div class="chart-title">Docentes por Rede (histórico)${geoSuffix()}</div>
          <div style="height:230px"><canvas id="chart-redes-doc-hist"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
        <div class="chart-card">
          <div class="chart-title">Razão Aluno / Professor — ${anoSel}${geoSuffix()}</div>
          <div style="height:230px"><canvas id="chart-redes-razao"></canvas></div>
          <div class="chart-source">${FONTE_CENSO}</div>
        </div>
      </div>

      <div class="section-divider">
        <span class="section-divider-icon"><img src="img/icons/territorial.png" alt=""></span>
        <span class="section-divider-text">Tabela Comparativa — ${anoSel}${geoSuffix()}</span>
        <span class="section-divider-line"></span>
      </div>

      <div class="chart-card" style="overflow-x:auto">
        <table class="data-table" id="redes-table">
          <thead><tr>
            <th>Rede</th><th>Escolas</th><th>Matrículas</th><th>% Mat.</th>
            <th>Infantil</th><th>Anos Iniciais</th><th>Anos Finais</th><th>Médio</th><th>EJA</th>
            <th>Docentes</th><th>A/P</th><th>Noturno</th><th>Integral</th>
          </tr></thead>
          <tbody>
            ${redes.map(r => {
              const v = anoData[r] || {};
              const pct = totMat ? (100 * (v.mat_total || 0) / totMat) : 0;
              return `<tr>
                <td style="font-weight:700;color:${cores[r] || '#333'}"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${cores[r]};margin-right:6px"></span>${r}</td>
                <td>${formatNum(v.escolas || 0)}</td>
                <td>${formatNum(v.mat_total || 0)}</td>
                <td>${pct.toFixed(1)}%</td>
                <td>${formatNum(v.mat_infantil || 0)}</td>
                <td>${formatNum(v.mat_fund_ai || 0)}</td>
                <td>${formatNum(v.mat_fund_af || 0)}</td>
                <td>${formatNum(v.mat_medio || 0)}</td>
                <td>${formatNum(v.mat_eja || 0)}</td>
                <td>${v.docentes != null ? formatNum(v.docentes) : '—'}</td>
                <td>${v.razao_ap != null ? Number(v.razao_ap).toFixed(1) : '—'}</td>
                <td>${v.mat_noturno != null ? formatNum(v.mat_noturno) : '—'}</td>
                <td>${v.mat_integral != null ? formatNum(v.mat_integral) : '—'}</td>
              </tr>`;
            }).join('')}
            <tr style="font-weight:800;background:#f8fafc">
              <td>Total</td>
              <td>${formatNum(totEsc)}</td>
              <td>${formatNum(totMat)}</td>
              <td>100%</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_infantil || 0), 0))}</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_fund_ai || 0), 0))}</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_fund_af || 0), 0))}</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_medio || 0), 0))}</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_eja || 0), 0))}</td>
              <td>${totDoc ? formatNum(totDoc) : '—'}</td>
              <td>${totDoc ? (totMat / totDoc).toFixed(1) : '—'}</td>
              <td>${formatNum(redes.reduce((s, r) => s + (anoData[r]?.mat_noturno || 0), 0))}</td>
              <td>${(() => { const n = redes.reduce((s, r) => s + (anoData[r]?.mat_integral || 0), 0); return n ? formatNum(n) : '—'; })()}</td>
            </tr>
          </tbody>
        </table>
        <div class="chart-source" style="margin-top:8px">${FONTE_CENSO} · Filantropica = privada sem fins lucrativos (cat_priv=4); Particular = privada com fins lucrativos (cat_priv=1).</div>
      </div>
    </div>
  `;

  // KPIs no formato premium das demais secoes
  const strip = document.getElementById('redes-kpis');
  if (strip) {
    strip.innerHTML = kpis.map((k, i) => {
      const delta = k.isPct
        ? (k.prev != null ? (k.val - k.prev) : null)
        : pctFn(k.val, k.prev);
      const abs = k.isPct ? null : absFn(k.val, k.prev);
      const sign = abs != null && abs > 0 ? '+' : '';
      const displayVal = k.isPct ? k.val.toFixed(1) + '%' : formatNum(k.val);
      return `
      <div class="kpi-card accent-${k.accent}" style="animation-delay:${i * 80}ms">
        <div class="kpi-top">
          <span class="kpi-label">${k.label}</span>
          <img class="kpi-icon" src="${k.icon}" alt="">
        </div>
        <div class="kpi-body">
          <span class="kpi-value">${displayVal}</span>
          ${k.spark ? sparkline(k.spark, k.color) : ''}
        </div>
        <div class="kpi-footer">
          ${delta != null ? `
            <span class="kpi-delta ${deltaClass(delta)}">${deltaArrow(delta)} ${k.isPct ? (delta >= 0 ? '+' : '') + delta.toFixed(1) + ' pp' : formatPct(delta)}</span>
            ${abs != null ? `<span class="kpi-abs">${sign}${formatNum(abs)} ${refLabel}</span>` : `<span class="kpi-abs">${refLabel}</span>`}
          ` : '<span class="kpi-abs">—</span>'}
        </div>
      </div>`;
    }).join('');
  }

  // Banner filters
  const selAno = document.getElementById('sel-ano');
  if (selAno) {
    selAno.innerHTML = anos.map(a => `<option value="${a}" ${a === anoSel ? 'selected' : ''}>${a}</option>`).join('');
  }
  populateCreDropdown();
  populateMunDropdown(S.creSel || null);
  bindTopbarFilters();
  updateActiveFilters();

  const seriesFor = (field) => redes.map(r => ({
    label: r,
    data: anos.map(a => porRedeAll[a]?.[r]?.[field] ?? null),
    borderColor: cores[r],
    backgroundColor: cores[r],
    tension: 0.25,
    pointRadius: 2.5,
    pointHoverRadius: 4,
    borderWidth: 2,
    spanGaps: true,
  }));

  const yMax = (arr) => {
    const vals = arr.filter(v => v != null && !isNaN(v));
    return vals.length ? Math.max(...vals) * 1.15 : undefined;
  };

  // Tooltip: valor + % da fatia entre séries no mesmo ponto (ex.: redes no mesmo ano/etapa)
  const tipPctEntreSeries = {
    ...CHART_DEFAULTS.plugins.tooltip,
    callbacks: {
      label: (ctx) => {
        const raw = ctx.parsed.y ?? ctx.parsed;
        if (raw == null || Number.isNaN(Number(raw))) return ` ${ctx.dataset.label || ''}: —`;
        const v = Number(raw);
        const idx = ctx.dataIndex;
        const tot = ctx.chart.data.datasets.reduce((s, ds) => {
          const x = ds.data[idx];
          return s + (x != null && !Number.isNaN(Number(x)) ? Number(x) : 0);
        }, 0);
        const pct = tot ? (100 * v / tot) : 0;
        return ` ${ctx.dataset.label || ''}: ${formatNum(v)} (${pct.toFixed(1)}%)`;
      },
    },
  };

  // Tooltip: valor + % do total da própria série (ex.: barras de uma etapa filtrada)
  const tipPctDaSerie = {
    ...CHART_DEFAULTS.plugins.tooltip,
    callbacks: {
      label: (ctx) => {
        const raw = ctx.parsed.y ?? ctx.parsed;
        if (raw == null || Number.isNaN(Number(raw))) return ` ${ctx.dataset.label || ''}: —`;
        const v = Number(raw);
        const tot = (ctx.dataset.data || []).reduce((s, x) => s + (x != null && !Number.isNaN(Number(x)) ? Number(x) : 0), 0);
        const pct = tot ? (100 * v / tot) : 0;
        return ` ${ctx.dataset.label || ''}: ${formatNum(v)} (${pct.toFixed(1)}%)`;
      },
    },
  };

  const matHistLabels = {
    mat_total: 'Total',
    mat_infantil: 'Infantil',
    mat_fund_ai: 'Anos Iniciais',
    mat_fund_af: 'Anos Finais',
    mat_fundamental: 'Fundamental',
    mat_medio: 'Médio',
    mat_eja: 'EJA',
  };

  let matHistChart = null;

  const buildRedesMatHist = (field) => {
    const el = document.getElementById('chart-redes-mat-hist');
    if (!el) return;
    const f = field || 'mat_total';
    const titleEl = document.getElementById('redes-mat-hist-title');
    const etapaTxt = f === 'mat_total' ? '' : ` — ${matHistLabels[f] || f}`;
    if (titleEl) titleEl.textContent = `Matrículas por Rede${etapaTxt} (${anos[0]}–${anos[anos.length - 1]})${geoSuffix()}`;

    const datasets = seriesFor(f);
    const matHistMax = yMax(datasets.flatMap(d => d.data));

    // Reusa o chart se já existir (update in-place — mais confiável que destroy/recreate)
    const existing = matHistChart || Chart.getChart(el);
    if (existing) {
      existing.data.labels = anos;
      existing.data.datasets = datasets;
      if (existing.options?.scales?.y) existing.options.scales.y.suggestedMax = matHistMax;
      existing.update('active');
      matHistChart = existing;
      if (!S.charts.includes(existing)) S.charts.push(existing);
      return;
    }

    matHistChart = new Chart(el, {
      type: 'line',
      data: { labels: anos, datasets },
      options: {
        ...CHART_DEFAULTS,
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } },
          datalabels: { ...DL_LINE, display: ctx => ctx.dataIndex === anos.length - 1 || ctx.dataIndex === 0 },
          tooltip: tipPctEntreSeries,
        },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, suggestedMax: matHistMax, ticks: { ...CHART_DEFAULTS.scales.y.ticks, callback: v => formatNumChart(v) } },
        },
      },
    });
    S.charts.push(matHistChart);
  };

  buildRedesMatHist(S.redesHistEtapaSel || 'mat_total');

  const histPillsWrap = document.getElementById('redes-hist-etapa-pills');
  if (histPillsWrap) {
    histPillsWrap.style.position = 'relative';
    histPillsWrap.style.zIndex = '6';
    histPillsWrap.addEventListener('click', (ev) => {
      const btn = ev.target.closest('.redes-hist-etapa-pill');
      if (!btn) return;
      ev.preventDefault();
      ev.stopPropagation();
      const etapa = btn.getAttribute('data-etapa') || 'mat_total';
      S.redesHistEtapaSel = etapa;
      histPillsWrap.querySelectorAll('.redes-hist-etapa-pill').forEach(b => {
        b.classList.toggle('active', b === btn);
      });
      buildRedesMatHist(etapa);
    });
  }

  const escHistMax = yMax(seriesFor('escolas').flatMap(d => d.data));
  S.charts.push(new Chart(document.getElementById('chart-redes-esc-hist'), {
    type: 'line',
    data: { labels: anos, datasets: seriesFor('escolas') },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } },
        datalabels: { ...DL_LINE, display: ctx => ctx.dataIndex === anos.length - 1 || ctx.dataIndex === 0 },
        tooltip: tipPctEntreSeries,
      },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, suggestedMax: escHistMax },
      },
    },
  }));

  const etapas = [
    { key: 'mat_infantil', label: 'Infantil' },
    { key: 'mat_fund_ai', label: 'Anos Iniciais' },
    { key: 'mat_fund_af', label: 'Anos Finais' },
    { key: 'mat_medio', label: 'Médio' },
    { key: 'mat_eja', label: 'EJA' },
  ];

  const destroyRedesPerfilCharts = () => {
    ['chart-redes-etapas', 'chart-redes-share', 'chart-redes-turno', 'chart-redes-integral'].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const existing = Chart.getChart(el);
      if (existing) {
        S.charts = S.charts.filter(c => c !== existing);
        existing.destroy();
      }
    });
  };

  const buildRedesPerfilCharts = (etapaKey) => {
    destroyRedesPerfilCharts();
    const etSel = etapas.find(e => e.key === etapaKey) || null;
    const etLabel = etSel ? etSel.label : 'Todas as etapas';
    const matField = etSel ? etSel.key : 'mat_total';

    const tEl = document.getElementById('redes-etapas-title');
    const sEl = document.getElementById('redes-share-title');
    const uEl = document.getElementById('redes-turno-title');
    const iEl = document.getElementById('redes-integral-title');
    if (tEl) tEl.textContent = etSel
      ? `Matrículas — ${etSel.label} por Rede — ${anoSel}${geoSuffix()}`
      : `Matrículas por Etapa e Rede — ${anoSel}${geoSuffix()}`;
    if (sEl) sEl.textContent = `Participação nas Matrículas${etSel ? ` (${etSel.label})` : ''} — ${anoSel}${geoSuffix()}`;
    if (uEl) uEl.textContent = `Forma de Oferta — Diurno × Noturno${etSel ? ` (${etSel.label})` : ''} — ${anoSel}${geoSuffix()}`;
    if (iEl) iEl.textContent = `Educação Integral${etSel ? ` (${etSel.label})` : ''} por Rede — ${anoSel}${geoSuffix()}`;

    // 1) Etapas × rede (ou só a etapa filtrada)
    if (etSel) {
      const vals = redes.map(r => anoData[r]?.[etSel.key] || 0);
      S.charts.push(new Chart(document.getElementById('chart-redes-etapas'), {
        type: 'bar',
        data: {
          labels: redes,
          datasets: [{
            label: etSel.label,
            data: vals,
            backgroundColor: redes.map(r => cores[r]),
            borderRadius: 4,
          }],
        },
        options: {
          ...CHART_DEFAULTS,
          plugins: {
            ...CHART_DEFAULTS.plugins,
            legend: { display: false },
            datalabels: { ...DL_BAR, formatter: v => v ? formatNumChart(v) : '' },
            tooltip: tipPctDaSerie,
          },
          scales: {
            ...CHART_DEFAULTS.scales,
            y: { ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max(...vals, 1) * 1.18, ticks: { callback: v => formatNumChart(v) } },
          },
        },
      }));
    } else {
      const etapaVals = etapas.flatMap(et => redes.map(r => anoData[r]?.[et.key] || 0));
      S.charts.push(new Chart(document.getElementById('chart-redes-etapas'), {
        type: 'bar',
        data: {
          labels: etapas.map(e => e.label),
          datasets: redes.map(r => ({
            label: r,
            data: etapas.map(et => anoData[r]?.[et.key] || 0),
            backgroundColor: cores[r],
            borderRadius: 3,
          })),
        },
        options: {
          ...CHART_DEFAULTS,
          plugins: {
            ...CHART_DEFAULTS.plugins,
            legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } },
            datalabels: { ...DL_BAR, font: { family: 'Inter', size: 8, weight: '600' }, formatter: v => v >= 1000 ? formatNumChart(v) : (v || '') },
            tooltip: tipPctEntreSeries,
          },
          scales: {
            ...CHART_DEFAULTS.scales,
            y: { ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max(...etapaVals, 1) * 1.18, ticks: { callback: v => formatNumChart(v) } },
          },
        },
      }));
    }

    // 2) Participação % — eixo Y com nomes das redes
    const shareData = redes.map(r => anoData[r]?.[matField] || 0);
    const shareTot = shareData.reduce((a, b) => a + b, 0);
    const sharePct = shareData.map(v => shareTot ? +(100 * v / shareTot).toFixed(1) : 0);
    S.charts.push(new Chart(document.getElementById('chart-redes-share'), {
      type: 'bar',
      data: {
        labels: redes,
        datasets: [{
          label: 'Participação',
          data: sharePct,
          backgroundColor: redes.map(r => cores[r]),
          borderRadius: 4,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        indexAxis: 'y',
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { display: false },
          datalabels: {
            display: true,
            anchor: 'end',
            align: 'end',
            font: { family: 'Inter', size: 11, weight: '700' },
            color: '#333',
            formatter: v => (v == null ? '' : Number(v).toFixed(1) + '%'),
          },
          tooltip: {
            callbacks: {
              label: ctx => ` ${formatNum(shareData[ctx.dataIndex])} matrículas (${Number(ctx.parsed.x).toFixed(1)}%)`,
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            suggestedMax: Math.max(...sharePct, 1) * 1.2,
            grid: { color: COLORS.gridLine },
            ticks: { font: { family: 'Inter', size: 9 }, callback: v => v + '%' },
          },
          y: {
            grid: { display: false },
            ticks: { font: { family: 'Inter', size: 11, weight: '600' }, color: '#334155' },
          },
        },
      },
    }));

    // 3) Turno diurno × noturno (com % no rótulo = % do total da rede na etapa)
    const turnoMap = {
      '': { d: 'mat_diurno', n: 'mat_noturno' },
      mat_infantil: { d: 'mat_diurno_infantil', n: 'mat_noturno_infantil' },
      mat_fund_ai: { d: 'mat_diurno_fund_ai', n: 'mat_noturno_fund_ai' },
      mat_fund_af: { d: 'mat_diurno_fund_af', n: 'mat_noturno_fund_af' },
      mat_fundamental: { d: 'mat_diurno_fund', n: 'mat_noturno_fund' },
      mat_medio: { d: 'mat_diurno_medio', n: 'mat_noturno_medio' },
      mat_eja: { d: 'mat_diurno_eja', n: 'mat_noturno_eja' },
    };
    const tm = turnoMap[etapaKey || ''] || turnoMap[''];
    const diurno = redes.map(r => anoData[r]?.[tm.d] || 0);
    const noturno = redes.map(r => anoData[r]?.[tm.n] || 0);
    S.charts.push(new Chart(document.getElementById('chart-redes-turno'), {
      type: 'bar',
      data: {
        labels: redes,
        datasets: [
          { label: 'Diurno', data: diurno, backgroundColor: '#1565C0', borderRadius: 3 },
          { label: 'Noturno', data: noturno, backgroundColor: '#FF8F00', borderRadius: 3 },
        ],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } },
          datalabels: {
            ...DL_BAR,
            font: { family: 'Inter', size: 8, weight: '600' },
            formatter: (v, ctx) => {
              if (!v) return '';
              const rowTot = (diurno[ctx.dataIndex] || 0) + (noturno[ctx.dataIndex] || 0);
              const pct = rowTot ? (100 * v / rowTot) : 0;
              return formatNumChart(v) + ' (' + pct.toFixed(0) + '%)';
            },
          },
          tooltip: {
            ...CHART_DEFAULTS.plugins.tooltip,
            callbacks: {
              label: (ctx) => {
                const v = ctx.parsed.y ?? 0;
                const rowTot = (diurno[ctx.dataIndex] || 0) + (noturno[ctx.dataIndex] || 0);
                const pct = rowTot ? (100 * v / rowTot) : 0;
                return ` ${ctx.dataset.label}: ${formatNum(v)} (${pct.toFixed(1)}%)`;
              },
            },
          },
        },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max(...diurno, ...noturno, 1) * 1.22, ticks: { callback: v => formatNumChart(v) } },
        },
      },
    }));

    // 4) Integral
    const integMap = {
      '': 'mat_integral',
      mat_infantil: 'int_infantil',
      mat_fund_ai: 'int_fund_ai',
      mat_fund_af: 'int_fund_af',
      mat_fundamental: 'int_fund',
      mat_medio: 'int_medio',
      mat_eja: null, // sem integral EJA tipico
    };
    const integKey = integMap[etapaKey || ''];
    const integ = redes.map(r => (integKey ? (anoData[r]?.[integKey] || 0) : 0));
    const matBase = redes.map(r => anoData[r]?.[matField] || 0);
    S.charts.push(new Chart(document.getElementById('chart-redes-integral'), {
      type: 'bar',
      data: {
        labels: redes,
        datasets: [{
          label: 'Integral',
          data: integ,
          backgroundColor: redes.map(r => cores[r]),
          borderRadius: 4,
        }],
      },
      options: {
        ...CHART_DEFAULTS,
        plugins: {
          ...CHART_DEFAULTS.plugins,
          legend: { display: false },
          datalabels: {
            ...DL_BAR,
            formatter: (v, ctx) => {
              if (!v) return etapaKey === 'mat_eja' ? '—' : '';
              const base = matBase[ctx.dataIndex] || 0;
              const pct = base ? (100 * v / base) : 0;
              return formatNumChart(v) + ' (' + pct.toFixed(0) + '%)';
            },
          },
          tooltip: {
            ...CHART_DEFAULTS.plugins.tooltip,
            callbacks: {
              label: (ctx) => {
                const v = ctx.parsed.y ?? 0;
                if (!v && etapaKey === 'mat_eja') return ' Integral: —';
                const base = matBase[ctx.dataIndex] || 0;
                const pct = base ? (100 * v / base) : 0;
                return ` Integral: ${formatNum(v)} (${pct.toFixed(1)}% das matrículas)`;
              },
            },
          },
        },
        scales: {
          ...CHART_DEFAULTS.scales,
          y: { ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max(...integ, 1) * 1.22, ticks: { callback: v => formatNumChart(v) } },
        },
      },
    }));
  };

  buildRedesPerfilCharts(S.redesEtapaSel || '');

  document.querySelectorAll('.redes-etapa-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      S.redesEtapaSel = btn.dataset.etapa || '';
      document.querySelectorAll('.redes-etapa-pill').forEach(b => b.classList.toggle('active', b === btn));
      buildRedesPerfilCharts(S.redesEtapaSel);
      setTimeout(() => injectExportButtons(), 40);
    });
  });

  const docHistMax = yMax(seriesFor('docentes').flatMap(d => d.data));
  S.charts.push(new Chart(document.getElementById('chart-redes-doc-hist'), {
    type: 'line',
    data: { labels: anos, datasets: seriesFor('docentes') },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10, family: 'Inter' } } },
        datalabels: { ...DL_LINE, display: ctx => ctx.dataIndex === anos.length - 1 || ctx.dataIndex === 0 },
        tooltip: tipPctEntreSeries,
      },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, suggestedMax: docHistMax, ticks: { callback: v => formatNumChart(v) } },
      },
    },
  }));

  const razao = redes.map(r => anoData[r]?.razao_ap ?? null);
  S.charts.push(new Chart(document.getElementById('chart-redes-razao'), {
    type: 'bar',
    data: {
      labels: redes,
      datasets: [{
        label: 'Alunos por professor',
        data: razao,
        backgroundColor: redes.map(r => cores[r]),
        borderRadius: 4,
      }],
    },
    options: {
      ...CHART_DEFAULTS,
      plugins: {
        ...CHART_DEFAULTS.plugins,
        legend: { display: false },
        datalabels: { ...DL_BAR, formatter: v => v != null ? Number(v).toFixed(1) : '' },
      },
      scales: {
        ...CHART_DEFAULTS.scales,
        y: { ...CHART_DEFAULTS.scales.y, suggestedMax: Math.max(...razao.filter(v => v != null), 1) * 1.2 },
      },
    },
  }));

  setTimeout(() => injectExportButtons(), 50);
}
