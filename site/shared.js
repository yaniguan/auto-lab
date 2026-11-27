/* Shared Utilities, Theme Persistence, Data Loader & SVG Charts for Auto-Lab Pages */
(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const THEME_KEY = 'autolab_theme';

  // Apply persisted theme immediately
  const savedTheme = localStorage.getItem(THEME_KEY);
  if (savedTheme === 'dark' || savedTheme === 'light') {
    document.documentElement.dataset.theme = savedTheme;
  }

  function esc(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function fmtMd(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  }

  function getPalette() {
    const dark = document.documentElement.dataset.theme === 'dark';
    return dark
      ? {
          bg: '#111b27',
          plot: '#0f1722',
          grid: '#223142',
          axis: '#64748b',
          text: '#f1f5f9',
          muted: '#94a3b8',
          accent: '#2dd4bf',
          blue: '#60a5fa',
          purple: '#a78bfa',
          amber: '#fbbf24',
          rose: '#fb7185',
        }
      : {
          bg: '#ffffff',
          plot: '#f8fafc',
          grid: '#e2e8f0',
          axis: '#94a3b8',
          text: '#0f172a',
          muted: '#475569',
          accent: '#0d9488',
          blue: '#2563eb',
          purple: '#7c3aed',
          amber: '#d97706',
          rose: '#e11d48',
        };
  }

  function svgEl(tag, attrs = {}, text) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v !== undefined && v !== null) node.setAttribute(k, String(v));
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function initThemeToggle(onThemeChange) {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    const syncLabel = () => {
      btn.textContent = document.documentElement.dataset.theme === 'dark' ? '☀ Light' : '☾ Dark';
    };
    syncLabel();
    btn.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      localStorage.setItem(THEME_KEY, next);
      syncLabel();
      if (typeof onThemeChange === 'function') onThemeChange(next);
    });
  }

  async function loadData(basePrefix = '') {
    const res = await fetch(`${basePrefix}assets/autolab-data.json?v=5`);
    if (!res.ok) throw new Error(`Failed loading autolab-data.json (${res.status})`);
    return res.json();
  }

  /* Clean 6-Stage Closed-Loop Pipeline Diagram (Overview Page) */
  function renderClosedLoopSVG(host, activeIdx, onSelectStage) {
    if (!host) return;
    const P = getPalette();
    const dark = document.documentElement.dataset.theme === 'dark';
    const stages = [
      { idx: 0, layer: 'L2', title: '1. Sense', sub: 'lab-ears · ouroboros', col: P.blue },
      { idx: 1, layer: 'L6', title: '2. Deliberate', sub: 'ask-why · decide · YLM', col: P.purple },
      { idx: 2, layer: 'L5', title: '3. Plan & Shift', sub: 'buy-or-make · labshift', col: P.blue },
      { idx: 3, layer: 'L4', title: '4. Twin & Gate', sub: 'rehearsal · verify', col: P.accent },
      { idx: 4, layer: 'L1–L0', title: '5. Act on Edge', sub: 'stepbot · hands · feet', col: P.accent },
      { idx: 5, layer: 'L3', title: '6. Post-Train', sub: 'twinstep · labfill · labrl', col: P.amber },
    ];

    const W = 1080, H = 192;
    const boxW = 152, boxH = 98, gap = 24, startX = 24, topY = 26;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Six-stage closed-loop Auto-Lab pipeline' });

    for (let i = 0; i < stages.length - 1; i++) {
      const x1 = startX + i * (boxW + gap) + boxW;
      const x2 = x1 + gap;
      const ym = topY + boxH / 2;
      const hi = activeIdx === i || activeIdx === i + 1;
      svg.append(svgEl('line', {
        x1: x1 + 3, y1: ym, x2: x2 - 6, y2: ym,
        stroke: hi ? P.accent : P.axis, 'stroke-width': hi ? 2.2 : 1.5,
      }));
      svg.append(svgEl('polygon', {
        points: `${x2 - 2},${ym} ${x2 - 9},${ym - 4.5} ${x2 - 9},${ym + 4.5}`,
        fill: hi ? P.accent : P.axis,
      }));
    }

    // Clean Flywheel Return Arc from Stage 6 (L3) back to Stage 2 (L6) and Stage 5 (L0)
    const xEnd = startX + 5 * (boxW + gap) + boxW / 2;
    const xBrain = startX + 1 * (boxW + gap) + boxW / 2;
    svg.append(svgEl('path', {
      d: `M ${xEnd} ${topY + boxH + 2} C ${xEnd} ${H - 12}, ${xBrain} ${H - 12}, ${xBrain} ${topY + boxH + 4}`,
      fill: 'none', stroke: P.amber, 'stroke-width': 1.8, 'stroke-dasharray': '6 4',
    }));
    svg.append(svgEl('text', {
      x: (xEnd + xBrain) / 2, y: H - 8,
      fill: P.muted, 'font-size': 11.5, 'font-weight': '600', 'text-anchor': 'middle',
    }, '↺ Episodic traces, seeded error twins & RLVR checkpoints update Brain (L6) and Edge (L0)'));

    stages.forEach(s => {
      const x = startX + s.idx * (boxW + gap);
      const isSel = s.idx === activeIdx;
      const g = svgEl('g', { style: 'cursor:pointer', tabindex: '0', role: 'button' });
      g.append(svgEl('rect', {
        x, y: topY, width: boxW, height: boxH, rx: 11,
        fill: isSel ? (dark ? '#162636' : '#f0fdfa') : P.plot,
        stroke: isSel ? s.col : P.grid,
        'stroke-width': isSel ? 2.4 : 1.3,
      }));
      g.append(svgEl('text', {
        x: x + 13, y: topY + 26, fill: s.col, 'font-size': 11, 'font-weight': '750',
        'font-family': '"SFMono-Regular", Consolas, monospace',
      }, s.layer));
      g.append(svgEl('text', {
        x: x + 13, y: topY + 52, fill: P.text, 'font-size': 14, 'font-weight': '720',
      }, s.title));
      g.append(svgEl('text', {
        x: x + 13, y: topY + 74, fill: P.muted, 'font-size': 11.2,
      }, s.sub));
      if (onSelectStage) {
        g.addEventListener('click', () => onSelectStage(s.idx));
      }
      svg.append(g);
    });

    host.replaceChildren(svg);
  }

  /* Studio Chart 1: LabFill Recipe 4 Sequence Packing */
  function renderPackingChart(host, activeKey) {
    if (!host) return;
    const P = getPalette();
    const rows = [
      { key: 'padded', label: 'Padded FP32', tokS: 1509.9, speedup: '1.00x', col: P.axis },
      { key: 'bucketed', label: 'Length Bucketed', tokS: 3150.4, speedup: '2.09x', col: P.blue },
      { key: 'packed', label: 'Sequence Packed', tokS: 3931.5, speedup: '2.60x', col: P.purple },
      { key: 'block_sparse', label: 'Block-Sparse BF16', tokS: 7428.2, speedup: '4.92x', col: P.amber },
      { key: 'packed_bf16', label: 'Packed + BF16', tokS: 8180.5, speedup: '5.42x', col: P.accent },
    ];
    const W = 540, H = 222, padL = 132, padR = 96, topY = 16, rowH = 38;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });

    rows.forEach((r, idx) => {
      const y = topY + idx * rowH;
      const bw = Math.max(6, ((W - padL - padR) * r.tokS) / 9000);
      const isSel = r.key === activeKey;
      svg.append(svgEl('text', {
        x: padL - 10, y: y + 17, fill: isSel ? P.text : P.muted,
        'font-size': 12, 'font-weight': isSel ? '700' : '560', 'text-anchor': 'end',
      }, r.label));
      svg.append(svgEl('rect', {
        x: padL, y: y + 3, width: W - padL - padR, height: 22, rx: 5, fill: P.plot, stroke: P.grid,
      }));
      svg.append(svgEl('rect', {
        x: padL, y: y + 3, width: bw, height: 22, rx: 5, fill: r.col, 'fill-opacity': isSel ? 1 : 0.78,
      }));
      svg.append(svgEl('text', {
        x: padL + bw + 8, y: y + 18, fill: P.text, 'font-size': 11.5, 'font-weight': '700',
      }, `${r.speedup} (${Math.round(r.tokS)} tok/s)`));
    });
    host.replaceChildren(svg);
  }

  /* Studio Chart 2: ESOL Conformal Coverage Curve */
  function renderTrustChart(host, roundIdx) {
    if (!host) return;
    const P = getPalette();
    const rounds = [
      { r: 0, train: 676, ans: 0.796, covIn: 0.922 },
      { r: 1, train: 696, ans: 0.854, covIn: 0.932 },
      { r: 2, train: 716, ans: 0.946, covIn: 0.938 },
      { r: 3, train: 726, ans: 1.000, covIn: 0.949 },
    ];
    const W = 540, H = 216, plotX = 48, plotW = 464, plotY = 22, plotH = 148;
    const yOf = v => plotY + plotH * (1 - (v - 0.70) / 0.34);
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });

    svg.append(svgEl('rect', { x: plotX, y: plotY, width: plotW, height: plotH, rx: 8, fill: P.plot, stroke: P.grid }));
    const y90 = yOf(0.90);
    svg.append(svgEl('line', {
      x1: plotX, y1: y90, x2: plotX + plotW, y2: y90,
      stroke: P.amber, 'stroke-width': 1.5, 'stroke-dasharray': '5 4',
    }));
    svg.append(svgEl('text', {
      x: plotX + plotW - 8, y: y90 - 5, fill: P.amber, 'font-size': 10.5, 'text-anchor': 'end', 'font-weight': '650',
    }, '90% Target Coverage'));

    const ptsIn = rounds.map((d, i) => `${plotX + 48 + i * 122},${yOf(d.covIn)}`).join(' ');
    svg.append(svgEl('polyline', { points: ptsIn, fill: 'none', stroke: P.accent, 'stroke-width': 2.5 }));
    const ptsAns = rounds.map((d, i) => `${plotX + 48 + i * 122},${yOf(d.ans)}`).join(' ');
    svg.append(svgEl('polyline', { points: ptsAns, fill: 'none', stroke: P.purple, 'stroke-width': 2.1, 'stroke-dasharray': '4 3' }));

    rounds.forEach((d, i) => {
      const cx = plotX + 48 + i * 122;
      const isCur = i === roundIdx;
      svg.append(svgEl('circle', { cx, cy: yOf(d.covIn), r: isCur ? 6 : 4, fill: P.accent }));
      svg.append(svgEl('circle', { cx, cy: yOf(d.ans), r: isCur ? 5.5 : 3.8, fill: P.purple }));
      svg.append(svgEl('text', {
        x: cx, y: plotY + plotH + 20, fill: isCur ? P.text : P.muted,
        'font-size': 11.5, 'font-weight': isCur ? '700' : '550', 'text-anchor': 'middle',
      }, `Round ${d.r}`));
    });

    svg.append(svgEl('text', { x: plotX + 12, y: plotY + 18, fill: P.accent, 'font-size': 11, 'font-weight': '700' }, '● In-Region Coverage'));
    svg.append(svgEl('text', { x: plotX + 168, y: plotY + 18, fill: P.purple, 'font-size': 11, 'font-weight': '700' }, '● Answered Fraction'));
    host.replaceChildren(svg);
  }

  /* Studio Chart 3: LabShift CP-SAT Gantt */
  function renderGanttSVG(host) {
    if (!host) return;
    const P = getPalette();
    const jobs = [
      { id: 'job_01', ops: [['L', 0, 18], ['L', 18, 28], ['I', 29, 56], ['R', 58, 62]] },
      { id: 'job_02', ops: [['L', 4, 15], ['L', 15, 24], ['I', 26, 52], ['R', 53, 58]] },
      { id: 'job_03', ops: [['L', 36, 44], ['I', 56, 85], ['R', 85, 94]] },
      { id: 'job_04', ops: [['L', 44, 60], ['L', 60, 65], ['I', 76, 99], ['R', 99, 105]] },
      { id: 'job_05', ops: [['L', 28, 36], ['C', 39, 52], ['W', 52, 58], ['R', 62, 69]] },
      { id: 'job_06', ops: [['L', 24, 39], ['L', 39, 49], ['I', 52, 76], ['R', 77, 84]] },
    ];
    const colMap = { L: P.accent, I: P.purple, R: P.blue, C: P.amber, W: P.rose };
    const W = 540, H = 205, padL = 62, padR = 18, topY = 20, rowH = 26, maxT = 105;
    const scale = t => padL + ((W - padL - padR) * t) / maxT;
    const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });

    [0, 21, 42, 63, 84, 105].forEach(t => {
      const x = scale(t);
      svg.append(svgEl('line', { x1: x, y1: topY - 4, x2: x, y2: topY + jobs.length * rowH, stroke: P.grid, 'stroke-width': 1 }));
      svg.append(svgEl('text', { x, y: H - 8, fill: P.muted, 'font-size': 10.5, 'text-anchor': 'middle' }, `${t}m`));
    });

    jobs.forEach((job, idx) => {
      const y = topY + idx * rowH;
      svg.append(svgEl('text', { x: padL - 8, y: y + 15, fill: P.text, 'font-size': 11.2, 'font-weight': '650', 'text-anchor': 'end' }, job.id));
      job.ops.forEach(([pool, s, e]) => {
        const x1 = scale(s), x2 = scale(e);
        svg.append(svgEl('rect', { x: x1, y: y + 3, width: Math.max(3, x2 - x1), height: 17, rx: 4, fill: colMap[pool] || P.accent }));
        if (x2 - x1 > 16) {
          svg.append(svgEl('text', { x: (x1 + x2) / 2, y: y + 14.5, fill: '#ffffff', 'font-size': 9.8, 'font-weight': '700', 'text-anchor': 'middle' }, pool));
        }
      });
    });
    host.replaceChildren(svg);
  }

  window.AutoLabShared = {
    esc,
    fmtMd,
    getPalette,
    initThemeToggle,
    loadData,
    renderClosedLoopSVG,
    renderPackingChart,
    renderTrustChart,
    renderGanttSVG,
  };
})();
