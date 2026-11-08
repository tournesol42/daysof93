#!/usr/bin/env python3
"""
Build script: extracts Collider's <script> block from collider-src/collider.html,
applies targeted patches, wraps in ColliderEmbed IIFE, writes collider-embed.js.

Re-run this whenever collider.html changes.
"""

import re, sys, os

SRC  = os.path.join(os.path.dirname(__file__), 'collider.html')
DEST = os.path.join(os.path.dirname(__file__), '..', 'collider-embed.js')

# ── extract <script> block ────────────────────────────────────────────────────
html = open(SRC, encoding='utf-8').read()
m = re.search(r'<script>([\s\S]*?)</script>', html)
if not m:
    sys.exit('ERROR: could not find <script>...</script> in collider.html')
script = m.group(1)
print(f'Extracted {len(script):,} chars from collider.html')

# ── patch helper ─────────────────────────────────────────────────────────────
patches = []
def patch(label, old, new):
    patches.append((label, old, new))

# ── patches ──────────────────────────────────────────────────────────────────

# P1 – use embed canvas instead of #c
patch('P1 canvas element',
    "const canvas = document.getElementById('c');",
    "const canvas = _embedCanvas;")

# P2 – fixed 1600×1000 virtual size
patch('P2 resize() fixed size',
    "function resize() {\n"
    "  DPR = window.devicePixelRatio || 1;\n"
    "  W = window.innerWidth; H = window.innerHeight;\n"
    "  canvas.width  = qCanvas.width  = W * DPR;\n"
    "  canvas.height = qCanvas.height = H * DPR;\n"
    "  mainCtx.setTransform(DPR, 0, 0, DPR, 0, 0);\n"
    "  qctx.setTransform(DPR, 0, 0, DPR, 0, 0);\n"
    "}\n"
    "resize();\n"
    "window.addEventListener('resize', resize);",

    "function resize() {\n"
    "  DPR = 1; W = 1600; H = 1000;\n"
    "  canvas.width  = qCanvas.width  = W;\n"
    "  canvas.height = qCanvas.height = H;\n"
    "  mainCtx.setTransform(1, 0, 0, 1, 0, 0);\n"
    "  qctx.setTransform(1, 0, 0, 1, 0, 0);\n"
    "  _embedScaleCanvas();\n"
    "}\n"
    "resize();\n"
    "window.addEventListener('resize', _embedScaleCanvas);")

# P3 – transparent canvas (remove BG fill)
patch('P3 transparent canvas',
    "  ctx.fillStyle = BG;\n"
    "  ctx.fillRect(0, 0, W, H);",
    "  ctx.clearRect(0, 0, W, H);")

# P4 – gate cadCircles drawing (keep spring physics + live.push)
patch('P4 cadCircles drawing gate',
    "    if (c.alpha < 0.005) return;\n"
    "    const x = bx + c.ox, y = by + c.oy;\n"
    "    const r = (rMin + c.t * (rMax - rMin)) * 0.5;   // half size\n"
    "    ctx.beginPath();\n"
    "    ctx.arc(x, y, r, 0, Math.PI * 2);\n"
    "    const dr = dropA(c, tNow), fa = c.alpha * dr.a;\n"
    "    const col = a => c.white ? `rgba(255,255,255,${a})` : `rgba(${c.g},${c.g},${c.g},${a})`;\n"
    "    ctx.strokeStyle = col(fa);\n"
    "    ctx.lineWidth = c.white ? 2.6 : 0.8;\n"
    "    ctx.stroke();\n"
    "    live.push({ x: bx + c.tx, y: by + c.ty, r, a: c.alpha, i });   // lines: new position, no jelly",

    "    if (c.alpha < 0.005) return;\n"
    "    const x = bx + c.ox, y = by + c.oy;\n"
    "    const r = (rMin + c.t * (rMax - rMin)) * 0.5;   // half size\n"
    "    if (_L.cadCircles) {\n"
    "      ctx.beginPath();\n"
    "      ctx.arc(x, y, r, 0, Math.PI * 2);\n"
    "      const dr = dropA(c, tNow), fa = c.alpha * dr.a;\n"
    "      const col = a => c.white ? `rgba(255,255,255,${a})` : `rgba(${c.g},${c.g},${c.g},${a})`;\n"
    "      ctx.strokeStyle = col(fa);\n"
    "      ctx.lineWidth = c.white ? 2.6 : 0.8;\n"
    "      ctx.stroke();\n"
    "    }\n"
    "    live.push({ x: bx + c.tx, y: by + c.ty, r, a: c.alpha, i });   // lines: new position, no jelly")

# P5 – gate drawConstruction call
patch('P5 drawConstruction gate',
    "  drawConstruction(live);",
    "  if (_L.cadCircles) drawConstruction(live);")

# P6 – gate analyzer visual (keep raUpdate() state running)
patch('P6 drawRadial analyzer gate',
    "function drawRadial() {\n"
    "  raUpdate();\n"
    "  const g = raGeo(), { x, y, R, r0 } = g;",

    "function drawRadial() {\n"
    "  raUpdate();\n"
    "  if (!_L.analyzer) return;\n"
    "  const g = raGeo(), { x, y, R, r0 } = g;")

# P7 – gate presetNumber + valueDisplay
patch('P7 presetNumber + valueDisplay gate',
    "  drawPresetNum();\n"
    "  drawValueDisplay();",
    "  if (_L.presetNumber) drawPresetNum();\n"
    "  if (_L.valueDisplay) drawValueDisplay();")

# P8a – open chart gate (keep updateQuad() running)
patch('P8a chart gate open',
    "  updateQuad(cx, cy, mode === 'moveQuad');\n"
    "  qctx.clearRect(0, 0, W, H);",
    "  updateQuad(cx, cy, mode === 'moveQuad');\n"
    "  if (_L.chart) {\n"
    "  qctx.clearRect(0, 0, W, H);")

# P8b – close chart gate
patch('P8b chart gate close',
    "  ctx.save(); ctx.globalAlpha = chartA; drawArm(); ctx.restore();\n"
    "\n"
    "  const edgeDist",
    "  ctx.save(); ctx.globalAlpha = chartA; drawArm(); ctx.restore();\n"
    "  } // end _L.chart\n"
    "\n"
    "  const edgeDist")

# P9 – gate grooves (rings layer)
patch('P9 grooves gate',
    "  if (s > 0.01) {\n"
    "    grooves.forEach(g => {",
    "  if (_L.rings && s > 0.01) {\n"
    "    grooves.forEach(g => {")

# P10 – gate drawRingLine in extras loop
patch('P10 drawRingLine extras gate',
    "    drawRingLine(cx, cy, R, ex.alpha, ex.solid, s);\n"
    "    const br = base.baseBlobR",
    "    if (_L.rings) drawRingLine(cx, cy, R, ex.alpha, ex.solid, s);\n"
    "    const br = base.baseBlobR")

# P11 – gate drawRingLine in rings loop
patch('P11 drawRingLine rings gate',
    "    drawRingLine(cx, cy, R, 1, ring.solid, s);\n"
    "    dotJobs.push([R, br, ring.main.ang, 1]);",
    "    if (_L.rings) drawRingLine(cx, cy, R, 1, ring.solid, s);\n"
    "    dotJobs.push([R, br, ring.main.ang, 1]);")

# P12 – gate seqDots, pistonDots, ring blobs drawing
patch('P12 dots drawing gate',
    "  seqJobs.forEach(j => drawSeqDot(cx, cy, j[0], j[1], j[2], j[3], aura));\n"
    "  pstDrawDots(cx, cy, pos, laneR);\n"
    "  dotJobs.forEach(j => drawDot(cx, cy, j[0], j[1], j[2], j[3], aura));",
    "  if (_L.seqDots) seqJobs.forEach(j => drawSeqDot(cx, cy, j[0], j[1], j[2], j[3], aura));\n"
    "  if (_L.pistonDots) pstDrawDots(cx, cy, pos, laneR);\n"
    "  if (_L.rings) dotJobs.forEach(j => drawDot(cx, cy, j[0], j[1], j[2], j[3], aura));")

# P13 – gate lane fire flashes
patch('P13 lane fire gate',
    "  laneR.forEach((lr, li) => {\n"
    "    if (!lr) return;\n"
    "    const age = now - laneHit[li];\n"
    "    if (laneHit[li] < 0 || age < 0 || age > 0.35) return;\n"
    "    const k = 1 - age / 0.35;\n"
    "    ctx.beginPath(); ctx.arc(cx, cy - lr[0], 3 + (1 - k) * 9, 0, Math.PI * 2);\n"
    "    ctx.strokeStyle = `rgba(255,85,0,${k * lr[1]})`; ctx.lineWidth = 1.4; ctx.stroke();\n"
    "  });\n"
    "  meets.forEach(m => {",
    "  if (_L.seqDots) laneR.forEach((lr, li) => {\n"
    "    if (!lr) return;\n"
    "    const age = now - laneHit[li];\n"
    "    if (laneHit[li] < 0 || age < 0 || age > 0.35) return;\n"
    "    const k = 1 - age / 0.35;\n"
    "    ctx.beginPath(); ctx.arc(cx, cy - lr[0], 3 + (1 - k) * 9, 0, Math.PI * 2);\n"
    "    ctx.strokeStyle = `rgba(255,85,0,${k * lr[1]})`; ctx.lineWidth = 1.4; ctx.stroke();\n"
    "  });\n"
    "  meets.forEach(m => {")

# P14 – gate meets (ring collision rings)
patch('P14 meets gate',
    "  meets.forEach(m => {\n"
    "    const lr = laneR[m.li]; if (!lr) return;\n"
    "    const age = now - m.t; if (age < 0 || age > 0.6) return;\n"
    "    const k = 1 - age / 0.6;\n"
    "    ctx.beginPath(); ctx.arc(cx + Math.cos(m.ang) * lr[0], cy + Math.sin(m.ang) * lr[0], 2 + (1 - k) * 7, 0, Math.PI * 2);\n"
    "    ctx.strokeStyle = `rgba(17,17,17,${k * 0.7 * lr[1]})`; ctx.lineWidth = 0.9; ctx.stroke();\n"
    "  });\n"
    "  // 0 point marker (12 o'clock)",
    "  if (_L.rings) meets.forEach(m => {\n"
    "    const lr = laneR[m.li]; if (!lr) return;\n"
    "    const age = now - m.t; if (age < 0 || age > 0.6) return;\n"
    "    const k = 1 - age / 0.6;\n"
    "    ctx.beginPath(); ctx.arc(cx + Math.cos(m.ang) * lr[0], cy + Math.sin(m.ang) * lr[0], 2 + (1 - k) * 7, 0, Math.PI * 2);\n"
    "    ctx.strokeStyle = `rgba(17,17,17,${k * 0.7 * lr[1]})`; ctx.lineWidth = 0.9; ctx.stroke();\n"
    "  });\n"
    "  // 0 point marker (12 o'clock)")

# P15a – gate 0-point marker
patch('P15a 0-point marker gate',
    "  if (outerR > 0) {",
    "  if (_L.rings && outerR > 0) {")

# P15b – gate center dot
patch('P15b center dot gate',
    "  ctx.beginPath();\n"
    "  ctx.arc(cx, cy, 5, 0, Math.PI * 2);\n"
    "  ctx.fillStyle = '#111111';\n"
    "  ctx.fill();\n"
    "\n"
    "  drawFaders();",
    "  if (_L.rings) {\n"
    "    ctx.beginPath();\n"
    "    ctx.arc(cx, cy, 5, 0, Math.PI * 2);\n"
    "    ctx.fillStyle = '#111111';\n"
    "    ctx.fill();\n"
    "  }\n"
    "\n"
    "  drawFaders();")

# P16 – gate drawFaders
patch('P16 drawFaders gate',
    "  drawFaders();\n"
    "  drawTransport();",
    "  if (_L.faders) drawFaders();\n"
    "  drawTransport();")

# P17a – gate transport inside drawTransport (keep drawRhythm call unconditional)
patch('P17a drawTransport gate',
    "function drawTransport() {\n"
    "  const { x, y } = tPos();\n"
    "  ctx.save();\n"
    "  ctx.globalAlpha = playing ? 0.3 : 1;\n"
    "  ctx.fillStyle = '#0B0B0B';\n"
    "  ctx.fillRect(x, y, T_SQ, T_SQ);\n"
    "  ctx.strokeStyle = '#6A6A6A'; ctx.lineWidth = 1;\n"
    "  ctx.strokeRect(x + 0.5, y + 0.5, T_SQ - 1, T_SQ - 1);\n"
    "  ctx.globalAlpha = playing ? 1 : 0.3;\n"
    "  const tx = x + T_SQ + T_GAP;\n"
    "  ctx.beginPath();\n"
    "  ctx.moveTo(tx, y); ctx.lineTo(tx + T_TRI_W, y + T_SQ / 2); ctx.lineTo(tx, y + T_SQ); ctx.closePath();\n"
    "  ctx.fillStyle = '#1C1C1C'; ctx.fill();\n"
    "  ctx.restore();\n"
    "  drawKnobAndDot();\n"
    "  drawRhythm();\n"
    "}",
    "function drawTransport() {\n"
    "  if (_L.transport) {\n"
    "    const { x, y } = tPos();\n"
    "    ctx.save();\n"
    "    ctx.globalAlpha = playing ? 0.3 : 1;\n"
    "    ctx.fillStyle = '#0B0B0B';\n"
    "    ctx.fillRect(x, y, T_SQ, T_SQ);\n"
    "    ctx.strokeStyle = '#6A6A6A'; ctx.lineWidth = 1;\n"
    "    ctx.strokeRect(x + 0.5, y + 0.5, T_SQ - 1, T_SQ - 1);\n"
    "    ctx.globalAlpha = playing ? 1 : 0.3;\n"
    "    const tx = x + T_SQ + T_GAP;\n"
    "    ctx.beginPath();\n"
    "    ctx.moveTo(tx, y); ctx.lineTo(tx + T_TRI_W, y + T_SQ / 2); ctx.lineTo(tx, y + T_SQ); ctx.closePath();\n"
    "    ctx.fillStyle = '#1C1C1C'; ctx.fill();\n"
    "    ctx.restore();\n"
    "    drawKnobAndDot();\n"
    "  }\n"
    "  drawRhythm();\n"
    "}")

# P17b – gate drawRhythm
patch('P17b drawRhythm gate',
    "function drawRhythm() {\n"
    "  const g = rhyGeo();",
    "function drawRhythm() {\n"
    "  if (!_L.rhythm) return;\n"
    "  const g = rhyGeo();")

# P18 – coordinate transform for scaled canvas (mousedown)
patch('P18 mousedown coord transform',
    "canvas.addEventListener('mousedown', e => {\n"
    "  const mx = e.clientX, my = e.clientY;",
    "canvas.addEventListener('mousedown', e => {\n"
    "  const _r = canvas.getBoundingClientRect();\n"
    "  const mx = (e.clientX - _r.left) * (W / _r.width);\n"
    "  const my = (e.clientY - _r.top) * (H / _r.height);")

# P19 – coordinate transform for scaled canvas (mousemove)
patch('P19 mousemove coord transform',
    "window.addEventListener('mousemove', e => {\n"
    "  const mx = e.clientX, my = e.clientY;",
    "window.addEventListener('mousemove', e => {\n"
    "  const _r = canvas.getBoundingClientRect();\n"
    "  const mx = (e.clientX - _r.left) * (W / _r.width);\n"
    "  const my = (e.clientY - _r.top) * (H / _r.height);")

# P21 – null guard: setTimeout panel listener fires before create() sets up panel
# (The setTimeout(...,0) runs immediately after IIFE; panel div doesn't exist yet.)
patch('P21 panel setTimeout null guard',
    "  P.addEventListener('input', pick); P.addEventListener('change', pick);\n"
    "}, 0);",
    "  if (P) { P.addEventListener('input', pick); P.addEventListener('change', pick); }\n"
    "}, 0);")

# P20 – replace init code at bottom (create() handles this)
patch('P20 remove init code',
    "(function restore() {\n"
    "  let L = null;\n"
    "  try { L = JSON.parse(localStorage.getItem(LAYOUT_KEY) || 'null'); } catch (e) {}\n"
    "  applyLayout(L || DEFAULT_LAYOUT);\n"
    "  velX = velY = 0;\n"
    "})();\n"
    "buildPanel();\n"
    "document.getElementById('saveBtn').addEventListener('click', saveLayout);\n"
    "document.getElementById('inBtn').addEventListener('click', toggleMic);\n"
    "draw();",
    "// ColliderEmbed: init handled by create()")

# ── apply patches ─────────────────────────────────────────────────────────────
for label, old, new_ in patches:
    count = script.count(old)
    if count != 1:
        sys.exit(f'ERROR: {label}: expected 1 match, found {count}')
    script = script.replace(old, new_, 1)
    print(f'  OK  {label}')

# ── IIFE wrapper ──────────────────────────────────────────────────────────────
PREAMBLE = r"""// collider-embed.js — generated by collider-src/build-embed.py
// DO NOT EDIT BY HAND. Re-run build-embed.py when collider.html changes.
// Changes from standalone collider.html:
//   P1  canvas = _embedCanvas (created by ColliderEmbed, not #c)
//   P2  resize() uses fixed 1600×1000 virtual size; CSS scales canvas to container
//   P3  ctx.clearRect replaces BG fillRect (transparent canvas)
//   P4  cadCircles ctx.beginPath…ctx.stroke gated by _L.cadCircles (live.push always runs)
//   P5  drawConstruction(live) gated by _L.cadCircles
//   P6  drawRadial: raUpdate() always runs; drawing gated by _L.analyzer
//   P7  drawPresetNum/drawValueDisplay gated by _L.presetNumber/_L.valueDisplay
//   P8  chart drawing block gated by _L.chart; updateQuad() always runs
//   P9  grooves gated by _L.rings
//   P10 drawRingLine in extras loop gated by _L.rings
//   P11 drawRingLine in rings loop gated by _L.rings
//   P12 seqJobs/pstDrawDots/dotJobs drawing gated by _L.seqDots/_L.pistonDots/_L.rings
//   P13 lane fire flashes gated by _L.seqDots
//   P14 meets gated by _L.rings
//   P15 0-point marker + center dot gated by _L.rings
//   P16 drawFaders gated by _L.faders
//   P17 drawTransport gated by _L.transport; drawRhythm gated by _L.rhythm
//   P18 mousedown: transform clientX/Y to 1600×1000 canvas coords
//   P19 mousemove: transform clientX/Y to 1600×1000 canvas coords
//   P20 init code removed; ColliderEmbed.create() handles layout + draw start

(function (root) {
  'use strict';

  // ── no-op canvas context proxy for layer gating ───────────────────────────
  const _nullGrad = { addColorStop() {} };
  const _nullCtx = new Proxy({}, {
    get(_, k) {
      if (k === 'measureText') return () => ({ width: 0 });
      if (k === 'createRadialGradient' || k === 'createLinearGradient') return () => _nullGrad;
      if (k === 'canvas') return { width: 1600, height: 1000 };
      return () => {};
    },
    set() { return true; },
  });

  // ── layer visibility state (all hidden by default) ────────────────────────
  const _L = {
    rings: false, seqDots: false, pistonDots: false, cadCircles: false,
    chart: false, analyzer: false, faders: false, rhythm: false,
    transport: false, valueDisplay: false, presetNumber: false,
    header: false, panel: false,
  };

  // ── embed canvas and container ────────────────────────────────────────────
  const _embedCanvas = document.createElement('canvas');
  let _embedContainer = null;

  function _embedScaleCanvas() {
    if (!_embedCanvas || !_embedContainer) return;
    const cw = _embedContainer.clientWidth || 0;
    const ch = _embedContainer.clientHeight || 0;
    if (!cw || !ch) return;
    const scale = Math.min(cw / 1600, ch / 1000);
    const dw = 1600 * scale, dh = 1000 * scale;
    _embedCanvas.style.width  = dw + 'px';
    _embedCanvas.style.height = dh + 'px';
    _embedCanvas.style.left   = ((cw - dw) / 2) + 'px';
    _embedCanvas.style.top    = ((ch - dh) / 2) + 'px';
  }

  // ── Collider engine (patched) ─────────────────────────────────────────────
"""

SUFFIX = r"""
  // ── ColliderEmbed public API ──────────────────────────────────────────────
  let _drawStarted = false;

  function _updatePointerEvents() {
    const interactive = _L.faders || _L.rhythm || _L.transport ||
                        _L.chart || _L.analyzer || _L.panel;
    _embedCanvas.style.pointerEvents = interactive ? 'auto' : 'none';
  }

  function _injectStyles(container) {
    if (document.getElementById('_collider_embed_styles')) return;
    const link = document.createElement('link');
    link.id = '_collider_embed_styles';
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;700&display=swap';
    document.head.appendChild(link);
    const style = document.createElement('style');
    style.id = '_collider_embed_panel_styles';
    style.textContent = [
      '._ce_panel{position:absolute;top:0;left:0;width:350px;max-height:calc(100% - 24px);overflow-y:auto;',
      'background:rgba(237,232,223,0.92);backdrop-filter:blur(2px);',
      'border-right:1px solid #FF6B00;border-bottom:1px solid #FF6B00;',
      'padding:14px 16px 16px;z-index:90;',
      'font-family:"Space Mono","Courier New",monospace;',
      'font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#2B2B2B;',
      'user-select:none;}',
      '._ce_panel h3{font-size:9px;font-weight:700;letter-spacing:.2em;color:#FF5500;margin:12px 0 6px;}',
      '._ce_panel h3:first-child{margin-top:0;}',
      '._ce_panel .prow{display:grid;grid-template-columns:70px 1fr 90px;align-items:center;gap:8px;height:20px;}',
      '._ce_panel .prow input[type=range]{width:100%;accent-color:#FF5500;height:12px;}',
      '._ce_panel .prow .pv{text-align:right;color:#555;}',
      '._ce_panel select{font-family:"Space Mono",monospace;font-size:9px;background:transparent;border:1px solid #999;color:#2B2B2B;padding:1px 2px;}',
      '._ce_panel .lrow{display:grid;grid-template-columns:22px 64px 84px 1fr;gap:6px;align-items:center;height:16px;color:#444;}',
      '._ce_panel .lrow input{accent-color:#FF5500;margin:0;}',
      '._ce_panel .lmod{color:#FF5500;font-weight:400;}',
    ].join('');
    document.head.appendChild(style);
  }

  async function create({ container, layout, layers, audioContext: extAC } = {}) {
    _embedContainer = container || document.body;

    // inject fonts + panel CSS
    _injectStyles(_embedContainer);

    // create panel div (Collider's buildPanel() needs id="panel")
    const _panelEl = document.getElementById('panel') || document.createElement('div');
    _panelEl.id = 'panel';
    _panelEl.className = '_ce_panel';
    _panelEl.style.display = 'none';
    if (!_panelEl.parentElement) _embedContainer.appendChild(_panelEl);

    // position canvas inside container
    if (getComputedStyle(_embedContainer).position === 'static')
      _embedContainer.style.position = 'relative';
    _embedCanvas.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none;';
    _embedContainer.appendChild(_embedCanvas);

    // observe container resize
    if (typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(_embedScaleCanvas).observe(_embedContainer);
    }
    _embedScaleCanvas();

    // override AudioContext if provided
    if (extAC) {
      AC = extAC;
    }

    // apply initial layer visibility
    if (layers) {
      Object.keys(layers).forEach(k => { if (k in _L) _L[k] = !!layers[k]; });
      _updatePointerEvents();
    }

    // load layout
    let layoutObj = layout;
    if (typeof layout === 'string') {
      const r = await fetch(layout);
      layoutObj = await r.json();
    }
    applyLayout(layoutObj || DEFAULT_LAYOUT);
    velX = velY = 0;

    // build synth panel (needs panel div in DOM)
    buildPanel();
    if (!_L.panel) _panelEl.style.display = 'none';

    // start draw loop
    if (!_drawStarted) { _drawStarted = true; draw(); }

    return collider;
  }

  const collider = {
    /** Resume AudioContext and start audio (call from a click handler). */
    start() {
      audioInit();
      if (AC && AC.state !== 'running') AC.resume();
      playing = true;
      syncAudio();
    },
    /** Suspend audio. */
    stop() {
      playing = false;
      syncAudio();
    },
    /** Show a named layer. */
    show(name) {
      if (!(name in _L)) return;
      _L[name] = true;
      if (name === 'panel') {
        const p = document.getElementById('panel');
        if (p) p.style.display = 'block';
      }
      _updatePointerEvents();
    },
    /** Hide a named layer. */
    hide(name) {
      if (!(name in _L)) return;
      _L[name] = false;
      if (name === 'panel') {
        const p = document.getElementById('panel');
        if (p) p.style.display = 'none';
      }
      _updatePointerEvents();
    },
    /** Current layer visibility snapshot. */
    get layers() { return Object.assign({}, _L); },
    /**
     * Set a parameter.
     * set('fader', label, 0–1)   – orange fader bank by label
     * set('wedge', name, 0–1)    – analyzer wedge by WEDGE_NAMES entry
     * set('bpm', value)           – tempo (30–300 BPM)
     */
    set(type, nameOrVal, val) {
      if (type === 'bpm') {
        bpm = Math.max(30, Math.min(300, Math.round(nameOrVal)));
        return;
      }
      if (type === 'fader') {
        const f = faders.find(x => x.label === nameOrVal);
        if (f) f.val = Math.max(0, Math.min(1, val));
        return;
      }
      if (type === 'wedge') {
        const i = WEDGE_NAMES.indexOf(nameOrVal);
        if (i >= 0) wedges[i] = Math.max(0, Math.min(1, val));
        return;
      }
    },
    /** Recall a preset by index (0–19). */
    preset(n) { recallPreset(n); },
    /**
     * Toggle a RHYTHM button.
     * rhythm('UNEVEN' | 'STRAIGHT' | 'BREAKS' | 'BOUNCE', true|false)
     */
    rhythm(name, val) {
      const key = name.toLowerCase();
      if (key in RHY) RHY[key] = val ? 1 : 0;
    },
    /** Current bar position, phase-locked to seq-2 grid. 1 bar = 4 beats = 240/bpm s. */
    barPos() { if (!q2R) return null; const barDur = 240 / bpm; const gridT0 = q2T - q2P / q2R; return (AC.currentTime - gridT0) / barDur; },
    /** AudioContext time of bar line n, phase-locked to seq-2 grid. Null if stopped. */
    timeOfBar(n) { if (!q2R) return null; const barDur = 240 / bpm; const gridT0 = q2T - q2P / q2R; return gridT0 + n * barDur; },
    /** The final AudioNode (limiter) — connect to your own graph or meter. */
    get output() { return typeof OUT_NODE === 'function' ? OUT_NODE() : null; },
    create,
  };

  root.ColliderEmbed = { create };

}(typeof globalThis !== 'undefined' ? globalThis : window));
"""

output = PREAMBLE + script + SUFFIX

out_path = os.path.abspath(DEST)
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(output)

print(f'\nWrote {len(output):,} chars → {out_path}')
