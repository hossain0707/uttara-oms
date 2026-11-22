// Offline control regression; run after npm ci in apps/web.
const fs = require('node:fs');
const path = require('node:path');
const {JSDOM} = require('../../apps/web/node_modules/jsdom');
const html = fs.readFileSync(path.join(__dirname, 'architecture-explorer.html'), 'utf8');
for (const reduced of [false, true]) {
  const dom = new JSDOM(html, {runScripts:'dangerously', beforeParse(window) {
    window.matchMedia = () => ({matches:reduced});
  }});
  const document = dom.window.document;
  const get = id => document.getElementById(id);
  if (get('play').textContent !== (reduced ? 'Play tour' : 'Pause tour')) throw Error('Motion preference ignored');
  for (const tab of document.querySelectorAll('[data-tour]')) {
    tab.click();
    if (tab.getAttribute('aria-pressed') !== 'true') throw Error('Tour selection failed');
    for (let i=0;i<4;i++) get('next').click();
    if (get('stepCount').textContent !== 'Step 1 / 4') throw Error('Step cycle failed');
  }
  for (const node of document.querySelectorAll('[data-node]')) {
    node.click();
    if (!get('serviceText').textContent) throw Error('Service details missing');
  }
  get('play').click();
  if (get('play').textContent !== (reduced ? 'Pause tour' : 'Play tour')) throw Error('Pause toggle failed');
  get('view').click();
  if (!document.body.classList.contains('flat')) throw Error('Flat view failed');
  dom.window.close();
}
console.log('Explorer controls passed: five tours, step cycle, pause, flat view, seven service details and reduced motion.');
