const fs = require('fs');
const content = fs.readFileSync('painel/js/app.js', 'utf8');
const fIdx = content.indexOf('function renderDesigualdades() {');
const htmlStrStart = content.indexOf('main.innerHTML = `', fIdx);
const htmlStrEnd = content.indexOf('`;', htmlStrStart);
const h = content.substring(htmlStrStart, htmlStrEnd);
const matches = h.match(/id="([^"]+)"/g);
console.log(matches ? matches.join('\n') : 'No IDs found');
