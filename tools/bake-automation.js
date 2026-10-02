// Thin a MIDI console export and bake it into explore4.html as BAKED_P1 (v133)
const fs = require('fs');
const [,, jsonPath, htmlPath] = process.argv;
const snap = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
const p = (snap.presets || []).find(x => x && x.rec && x.rec.evts && x.rec.evts.length);
if (!p) { console.error('No recording found in JSON'); process.exit(1); }
const evts = p.rec.evts.slice().sort((a, b) => a.t - b.t);
// Thinning per controller: keep the first event, any change of >=3 steps, the extremes (0/127),
// and the last event before a pause of >150 ms (so every gesture ends on its exact final value)
const STEP = 3, GAP = 150, byCc = {};
evts.forEach((e, i) => { (byCc[e.cc] = byCc[e.cc] || []).push(i); });
const keep = new Set();
Object.values(byCc).forEach(idx => {
  let last = null;
  idx.forEach((i, k) => {
    const e = evts[i], next = idx[k + 1] !== undefined ? evts[idx[k + 1]] : null;
    const endOfGesture = !next || next.t - e.t > GAP;
    if (last === null || Math.abs(e.v - last) >= STEP || e.v === 0 || e.v === 127 || endOfGesture) { keep.add(i); last = e.v; }
  });
});
const flat = [];
evts.forEach((e, i) => { if (keep.has(i)) flat.push(e.t, e.cc, e.v); });
const baked = 'const BAKED_P1=' + JSON.stringify({ dur: p.rec.dur, e: flat }) + ';';
let html = fs.readFileSync(htmlPath, 'utf8');
const m = html.match(/const BAKED_P1=[^\n]*;/);
if (!m) { console.error('BAKED_P1 line not found'); process.exit(1); }
html = html.replace(m[0], baked);
fs.writeFileSync(htmlPath, html);
console.log('events: ' + evts.length + ' -> ' + flat.length / 3 + ', duration ' + (p.rec.dur / 1000).toFixed(1) + ' s, from preset ' + p.name);
