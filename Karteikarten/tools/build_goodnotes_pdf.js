const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [,, bodyPath, outPath] = process.argv;
  const body = fs.readFileSync(bodyPath, 'utf8');
  const css = `
  @page { size: A5 landscape; margin: 12mm; }
  body { font-family: 'DejaVu Sans', Arial, sans-serif; font-size: 10.5pt; color:#1a1a1a; }
  h1 { font-size: 18pt; color:#0b4f8a; } h2 { font-size: 13pt; color:#0b4f8a; }
  table { border-collapse: collapse; font-size: 9pt; } td, th { border:1px solid #999; padding:2px 5px; vertical-align:top; }
  hr { display:none; }
  .q, .a { page-break-before: always; min-height: 100mm; }
  .q { display:flex; flex-direction:column; justify-content:center; }
  .q .num, .a .num { font-size: 9pt; color:#777; }
  .q .txt { font-size: 15pt; font-weight:600; margin-top:8mm; }
  .a .lab { color:#0a7a3e; font-weight:700; }
  .chap { font-size:9pt; color:#0b4f8a; }
  .intro { page-break-after: always; }
  `;
  const page = await (await chromium.launch()).newPage();
  await page.setContent(`<html><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`);
  await page.evaluate(() => {
    let chap = '';
    const out = document.createElement('div');
    const intro = document.createElement('div'); intro.className = 'intro';
    const all = [...document.body.querySelectorAll('section.level3')];
    // Intro: everything before first level1 TEIL section
    const first = document.body.querySelector('section.level1');
    first.querySelectorAll(':scope > *').forEach(n => { if (!n.matches('section')) intro.appendChild(n.cloneNode(true)); });
    out.appendChild(intro);
    for (const s of all) {
      const l1 = s.closest('section.level1'); const h1 = l1 && l1.querySelector('h1');
      chap = h1 ? h1.textContent : chap;
      const title = s.querySelector('h3').textContent;
      const kids = [...s.children].filter(n => n.tagName !== 'H3');
      const qi = kids.findIndex(n => /^Frage:/.test(n.textContent.trim()));
      const ai = kids.findIndex(n => /^Antwort/.test(n.textContent.trim()));
      const q = document.createElement('div'); q.className = 'q';
      q.innerHTML = `<div class="chap">${chap}</div><div class="num">${title}</div>`;
      const qt = document.createElement('div'); qt.className = 'txt';
      kids.slice(qi, ai).forEach(n => qt.appendChild(n.cloneNode(true)));
      qt.innerHTML = qt.innerHTML.replace(/<strong>Frage:<\/strong>\s*/, '');
      q.appendChild(qt);
      const a = document.createElement('div'); a.className = 'a';
      a.innerHTML = `<div class="num">${title} – Antwort</div>`;
      kids.slice(ai).forEach(n => a.appendChild(n.cloneNode(true)));
      out.appendChild(q); out.appendChild(a);
    }
    document.body.innerHTML = ''; document.body.appendChild(out);
  });
  await page.pdf({ path: outPath, preferCSSPageSize: true, printBackground: true });
  process.exit(0);
})();
