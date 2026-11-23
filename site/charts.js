/* Native SVG Chart Renderers for Auto-Lab Studio (Zero External Dependencies) */
(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';

  function getPalette() {
    const dark = document.documentElement.dataset.theme === 'dark';
    return dark
      ? {
          bg: '#111b27',
          plot: '#0f1722',
          grid: '#223142',
          axis: '#475569',
          text: '#f1f5f9',
          muted: '#94a3b8',
          accent: '#2dd4bf',
          blue: '#60a5fa',
          purple: '#a78bfa',
          amber: '#fbbf24',
          orange: '#fb7185',
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
          orange: '#e11d48',
        };
  }

  function el(tag, attrs = {}, text) {
    const node = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v !== undefined && v !== null) node.setAttribute(k, String(v));
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  /* 1. labfill Recipe 4 GPU/CPU Sequence-Packing Throughput Bar Chart */
  function renderPackingChart(host, activeKey) {
    if (!host) return;
    const P = getPalette();
    const rows = [
      { key: 'padded', label: 'Padded FP32', tokS: 1509.9, useful: 30.6, speedup: '1.00×', col: P.axis },
      { key: 'bucketed', label: 'Length Bucketed', tokS: 3150.4, useful: 58.9, speedup: '2.09×', col: P.blue },
      { key: 'packed', label: 'Sequence Packed', tokS: 3931.5, useful: 92.1, speedup: '2.60×', col: P.purple },
      { key: 'block_sparse', label: 'Block-Sparse BF16', tokS: 7428.2, useful: 92.1, speedup: '4.92×', col: P.amber },
      { key: 'packed_bf16', label: 'Packed + BF16', tokS: 8180.5, useful: 92.1, speedup: '5.42×', col: P.accent },
    ];
    const W = 540, H = 225, padL = 128, padR = 68, topY = 18, rowH = 38;
    const maxV = 9000;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'labfill Recipe 4 real tokens per second' });

    rows.forEach((r, idx) => {
      const y = topY + idx * rowH;
      const bw = Math.max(6, ((W - padL - padR) * r.tokS) / maxV);
      const isSel = r.key === activeKey;
      svg.append(el('text', {
        x: padL - 10, y: y + 17, fill: isSel ? P.text : P.muted,
        'font-size': 11.8, 'font-weight': isSel ? '700' : '560', 'text-anchor': 'end',
      }, r.label));
      svg.append(el('rect', {
        x: padL, y: y + 3, width: W - padL - padR, height: 22, rx: 5, fill: P.plot, stroke: P.grid,
      }));
      svg.append(el('rect', {
        x: padL, y: y + 3, width: bw, height: 22, rx: 5, fill: r.col, 'fill-opacity': isSel ? 1 : 0.78,
      }));
      svg.append(el('text', {
        x: padL + bw + 8, y: y + 18, fill: P.text, 'font-size': 11.5, 'font-weight': '700',
      }, `${r.speedup} (${Math.round(r.tokS)} tok/s)`));
    });
    host.replaceChildren(svg);
  }

  /* 2. lab-decide Conformal Trust Expansion & labshift Solver Comparison */
  function renderTrustAndShiftChart(host, roundIdx) {
    if (!host) return;
    const P = getPalette();
    const rounds = [
      { r: 0, train: 676, test: 226, ans: 0.796, covIn: 0.922, covOut: 0.870, maeIn: 0.656, maeOut: 0.892 },
      { r: 1, train: 696, test: 206, ans: 0.854, covIn: 0.932, covOut: 0.767, maeIn: 0.656, maeOut: 0.942 },
      { r: 2, train: 716, test: 186, ans: 0.946, covIn: 0.938, covOut: 0.800, maeIn: 0.640, maeOut: 0.847 },
      { r: 3, train: 726, test: 176, ans: 1.000, covIn: 0.949, covOut: null, maeIn: 0.642, maeOut: null },
    ];
    const W = 540, H = 220;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Conformal trust coverage across rounds' });

    // Target 90% coverage dashed line
    const plotX = 52, plotW = 460, plotY = 24, plotH = 148;
    const yOf = v => plotY + plotH * (1 - (v - 0.65) / 0.38);

    svg.append(el('rect', { x: plotX, y: plotY, width: plotW, height: plotH, rx: 8, fill: P.plot, stroke: P.grid }));
    const y90 = yOf(0.90);
    svg.append(el('line', {
      x1: plotX, y1: y90, x2: plotX + plotW, y2: y90,
      stroke: P.amber, 'stroke-width': 1.5, 'stroke-dasharray': '5 4',
    }));
    svg.append(el('text', { x: plotX + plotW - 8, y: y90 - 5, fill: P.amber, 'font-size': 10.5, 'text-anchor': 'end', 'font-weight': '650' }, '90% Nominal Target'));

    const ptsIn = rounds.map((d, i) => `${plotX + 46 + i * 122},${yOf(d.covIn)}`).join(' ');
    svg.append(el('polyline', { points: ptsIn, fill: 'none', stroke: P.accent, 'stroke-width': 2.6 }));

    const ptsAns = rounds.map((d, i) => `${plotX + 46 + i * 122},${yOf(d.ans)}`).join(' ');
    svg.append(el('polyline', { points: ptsAns, fill: 'none', stroke: P.purple, 'stroke-width': 2.2, 'stroke-dasharray': '4 3' }));

    rounds.forEach((d, i) => {
      const cx = plotX + 46 + i * 122;
      const isCur = i === roundIdx;
      if (isCur) {
        svg.append(el('line', { x1: cx, y1: plotY, x2: cx, y2: plotY + plotH, stroke: P.accent, 'stroke-width': 1.2, opacity: 0.45 }));
      }
      svg.append(el('circle', { cx, cy: yOf(d.covIn), r: isCur ? 6 : 4.2, fill: P.accent }));
      svg.append(el('circle', { cx, cy: yOf(d.ans), r: isCur ? 5.5 : 3.8, fill: P.purple }));
      svg.append(el('text', {
        x: cx, y: plotY + plotH + 18, fill: isCur ? P.text : P.muted,
        'font-size': 11.5, 'font-weight': isCur ? '700' : '550', 'text-anchor': 'middle',
      }, `Round ${d.r} (n=${d.train})`));
    });

    svg.append(el('text', { x: plotX + 10, y: plotY + 18, fill: P.accent, 'font-size': 11.2, 'font-weight': '700' }, '● Inside-Region Coverage'));
    svg.append(el('text', { x: plotX + 185, y: plotY + 18, fill: P.purple, 'font-size': 11.2, 'font-weight': '700' }, '● Answered Fraction'));
    host.replaceChildren(svg);
  }

  /* 3. labshift Multi-Instrument Gantt SVG (small_00 CP-SAT 105m Optimal) */
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
    const colMap = { L: P.accent, I: P.purple, R: P.blue, C: P.amber, W: P.orange };
    const W = 540, H = 205, padL = 62, padR = 18, topY = 22, rowH = 25, maxT = 105;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'labshift small_00 CP-SAT Gantt schedule' });

    const scale = t => padL + ((W - padL - padR) * t) / maxT;
    [0, 21, 42, 63, 84, 105].forEach(t => {
      const x = scale(t);
      svg.append(el('line', { x1: x, y1: topY - 4, x2: x, y2: topY + jobs.length * rowH, stroke: P.grid, 'stroke-width': 1 }));
      svg.append(el('text', { x, y: H - 10, fill: P.muted, 'font-size': 10.5, 'text-anchor': 'middle' }, `${t}m`));
    });

    jobs.forEach((job, idx) => {
      const y = topY + idx * rowH;
      svg.append(el('text', { x: padL - 8, y: y + 15, fill: P.text, 'font-size': 11.2, 'font-weight': '650', 'text-anchor': 'end' }, job.id));
      job.ops.forEach(([pool, s, e]) => {
        const x1 = scale(s), x2 = scale(e);
        svg.append(el('rect', { x: x1, y: y + 3, width: Math.max(3, x2 - x1), height: 17, rx: 4, fill: colMap[pool] || P.accent }));
        if (x2 - x1 > 16) {
          svg.append(el('text', { x: (x1 + x2) / 2, y: y + 14.5, fill: '#ffffff', 'font-size': 9.8, 'font-weight': '700', 'text-anchor': 'middle' }, pool));
        }
      });
    });
    host.replaceChildren(svg);
  }

  window.AutoLabCharts = {
    getPalette,
    renderPackingChart,
    renderTrustAndShiftChart,
    renderGanttSVG,
  };
})();
