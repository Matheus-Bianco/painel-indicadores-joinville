const fs = require('fs');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;

const dom = new JSDOM(`<!DOCTYPE html><html><body><div id="main-wrapper"></div></body></html>`);
global.document = dom.window.document;
global.window = dom.window;

// Mock Leaflet
global.L = {
  map: () => ({
    setView: () => ({
      remove: () => {}
    })
  }),
  tileLayer: () => ({ addTo: () => {} }),
  geoJSON: () => ({ addTo: () => {} }),
  control: () => ({ onAdd: null }),
  DomUtil: { create: () => ({}) }
};

// Mock Chart
global.Chart = class {
  constructor(el, config) {}
};

// Mock S object and data
global.destroyCharts = () => {};
global.destroyMap = () => {};
global.S = {
  anoSel: null,
  munSel: null,
  creSel: null,
  _desigMapMode: 'mun',
  geo: { features: [] },
  desig: JSON.parse(fs.readFileSync('painel/dados/4_11_desigualdades.json', 'utf8'))
};
global.ETAPA_LABELS = { '5_EF': '5º ano EF' };
global.ETAPAS = ['5_EF'];
global.CHART_DEFAULTS = { plugins: { datalabels: {} }, scales: { y: { ticks: {} } } };
global.DL_VAL = {}; global.DL_PCT = {}; global.geoSuffix = () => ''; global.sectionBanner = () => '<div id="sel-ano"></div><div id="sel-cre"></div><div id="sel-mun"></div>';
global.RACA_COLORS = {}; global.SEXO_COLORS = {}; global.LOC_COLORS = {}; global.DEF_COLORS = {}; global.TURNO_COLORS = {};

const appCode = fs.readFileSync('painel/js/app.js', 'utf8');

// Extract renderDesigualdades
const funcMatch = appCode.match(/function renderDesigualdades\(\) \{([\s\S]*?)\n\}/);
if (funcMatch) {
  const body = funcMatch[1];
  try {
    const f = new Function(body);
    f();
    console.log("renderDesigualdades completed successfully!");
  } catch(e) {
    console.error("ERROR in renderDesigualdades:", e);
  }
} else {
  console.log("Function not found");
}
