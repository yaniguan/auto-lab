/* Overview Homepage Controller — Clean Orthogonal SVG Brain & Flywheel Diagram */
(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const { esc, getPalette, initThemeToggle, loadData } = window.AutoLabShared;

  let DATA = null;
  let selectedOrgan = 'lab-decide';
  let activeChapIdx = 0;
  let autoTourTimer = null;

  const CHAPTERS = [
    {
      layers: ['L6', 'L5', 'L4', 'L2', 'L1', 'L0', 'L3'],
      lead: 'Full Organism:',
      text: 'Goals descend through calibrated & default-deny gates (L6 → L0); verified outcomes replay up the L3 post-training rail.',
    },
    {
      layers: ['L6'],
      lead: 'L6 · Brain:',
      text: 'lab-ask-why retrieves opposing evidence (0.79 recall@3); lab-decide answers only inside its calibrated kNN zone (92.2% coverage).',
    },
    {
      layers: ['L5'],
      lead: 'L5 · Executive:',
      text: 'buy-or-make bounds catalog vs 2-step synthesis cost; labshift schedules shared instruments via CP-SAT (30/30 window-feasible).',
    },
    {
      layers: ['L4'],
      lead: 'L4 · Safety Gate:',
      text: 'lab-rehearsal dry-runs 96-well volumes and recalls runs.jsonl; lab-verify blocks wrong SQL and protocols (0 false passes).',
    },
    {
      layers: ['L2', 'L1', 'L0'],
      lead: 'L2–L0 · Body:',
      text: 'lab-ears extracts slots & monitors audio; stepbot compiles Opentrons v2; lab-hands shortcuts RRT paths; lab-feet runs 4-bit models.',
    },
    {
      layers: ['L3'],
      lead: 'L3 · Flywheel:',
      text: 'twinstep seeds 6 error types → labfill packs BF16 sequences (5.42x tok/s) → labbench-posttrain runs SFT · MPO · GDPO.',
    },
  ];

  // Strict aligned grid shelves: ZERO crossing wires!
  const SHELVES = [
    {
      code: 'L6', label: 'L6 · BRAIN', sub: 'Why & Conformal', colKey: 'purple',
      nodes: [
        { repo: 'lab-ask-why', sub: 'Socratic Why' },
        { repo: 'lab-decide', sub: 'Conformal Trust' },
        { repo: 'YLM', sub: '3D + Language ★', companion: true },
      ],
    },
    {
      code: 'L5', label: 'L5 · EXECUTIVE', sub: 'Procure & Schedule', colKey: 'blue',
      nodes: [
        { repo: 'buy-or-make', sub: 'Stock vs N-Step' },
        { repo: 'labshift', sub: 'CP-SAT Fleet' },
        { repo: 'lab-automation-atlas', sub: 'Ecosystem Map' },
      ],
    },
    {
      code: 'L4', label: 'L4 · SAFETY GATE', sub: 'Twin & Default-Deny', colKey: 'accent',
      nodes: [
        { repo: 'lab-rehearsal', sub: 'Recall & 96w Twin' },
        { repo: 'lab-verify', sub: 'Lean · SQL · Rules' },
        { repo: 'WignerFlow', sub: '50-fs [physics] ★', companion: true },
      ],
    },
    {
      code: 'L2', label: 'L2 · SENSORY', sub: 'Ears, Eyes & Data', colKey: 'blue',
      nodes: [
        { repo: 'lab-ears', sub: 'WLP + Machine Audio' },
        { repo: 'ouroboros-ocsr', sub: '2D Chem Eyes ★', companion: true },
        { repo: 'assayfold', sub: 'Unified Schema ★', companion: true },
      ],
    },
    {
      code: 'L1', label: 'L1 · HANDS', sub: 'Compile & Touch', colKey: 'accent',
      nodes: [
        { repo: 'stepbot', sub: 'Opentrons API v2' },
        { repo: 'lab-hands', sub: 'RRT + Last-cm Touch' },
      ],
    },
    {
      code: 'L0', label: 'L0 · FEET', sub: 'Edge Compute', colKey: 'purple',
      nodes: [
        { repo: 'lab-feet', sub: 'Distill + INT8 / 4-bit' },
      ],
    },
  ];

  const FLYWHEEL_NODES = [
    { repo: 'labbench-posttrain', sub: 'labrl: SFT → MPO → GDPO', y: 100 },
    { repo: 'labfill', sub: '5.42x Packed BF16 + Check', y: 236 },
    { repo: 'twinstep', sub: '6 Seeded Error Twins', y: 372 },
  ];

  const COMPANION_CARDS = {
    YLM: {
      hook: 'Reads English questions and 3D atoms together—outputs vectors that rotate with the molecule.',
      short: {
        object: 'Answer 3D force & dipole queries with exact rotation equivariance.',
        data: 'TensorQA-v0 (84,757 questions on 20k QM9 molecules).',
        model: 'Frozen MiniLM / MatSciBERT + e3nn (l <= 2) cross-attention.',
        property: '0.960 force cosine across 32 rotations (~2e-6 equivariance error).',
      },
    },
    WignerFlow: {
      hook: 'Jumps molecular dynamics 50 fs per step without a numerical integrator.',
      short: {
        object: 'Replace stiff 2 fs MD steps and gate untrained molecules for YLM.',
        data: '256-atom liquid argon NVE trajectories + CALiSol-23 alignment.',
        model: 'EquiTraj residual conditional flow matching + FrameSplit CPU API.',
        property: '4/5 seeds stable for 10,000 steps; strict refusal outside registry.',
      },
    },
    'ouroboros-ocsr': {
      hook: 'Reads molecule drawings from papers at any angle and checks stereochemistry in 3D.',
      short: {
        object: 'Turn 2D chemical figures into confidence-gated SMILES and 3D conformers.',
        data: 'Synthetic 24-angle drawings + untouched 300-image frozen-test-v2.',
        model: 'C8 steerable encoder + plain CNN ensemble + 229 ms int8 CPU API.',
        property: '65.8% across 24 angles with zero rotated training images.',
      },
    },
    assayfold: {
      hook: 'Collects scattered open lab datasets into one SHA-256-sealed, license-gated schema.',
      short: {
        object: 'Unify protocols, reactions, QM9, and LabPics under one strict record format.',
        data: 'AqSolDB, FreeSolv, ORD, QM9, RGD1, Transition1x, WLP, LabPics.',
        model: 'Pydantic extra=forbid schema + UCUM normalizer + license gate.',
        property: 'Blocks non-commercial & eval_only items from commercial exports.',
      },
    },
  };

  const DISPLAY_LAYER_ORDER = ['L6', 'L5', 'L4', 'L2', 'L1', 'L0', 'L3'];

  function el(tag, attrs = {}, text) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v !== undefined && v !== null) n.setAttribute(k, String(v));
    }
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function renderBrainSVG() {
    const host = document.getElementById('brain-svg-host');
    if (!host) return;
    const P = getPalette();
    const dark = document.documentElement.dataset.theme === 'dark';
    const chap = CHAPTERS[activeChapIdx] || CHAPTERS[0];
    const hiSet = new Set(chap.layers);

    const W = 1090, H = 524;
    const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img' });

    const shelfX = 18, shelfW = 736, shelfH = 66, stepY = 82, startY = 18;
    const colOf = k => (k === 'purple' ? P.purple : k === 'blue' ? P.blue : k === 'amber' ? P.amber : P.accent);

    // 1. Draw 6 horizontal shelves (L6 -> L0) + clean inter-shelf vertical spine arrows
    SHELVES.forEach((sh, idx) => {
      const y = startY + idx * stepY;
      const isHi = hiSet.has(sh.code);
      const col = colOf(sh.colKey);

      svg.append(el('rect', {
        x: shelfX, y, width: shelfW, height: shelfH, rx: 11,
        fill: isHi ? (dark ? '#132131' : '#ffffff') : (dark ? '#0d1621' : '#f8fafc'),
        stroke: isHi ? col : P.grid,
        'stroke-width': isHi ? 1.8 : 1.1,
        opacity: isHi ? 1 : 0.52,
      }));

      // Shelf label column (x: 32..164) — completely separate from node boxes!
      svg.append(el('text', {
        x: shelfX + 16, y: y + 29,
        fill: isHi ? col : P.muted, 'font-size': 11.5, 'font-weight': '780',
        'font-family': '"SFMono-Regular", Consolas, monospace',
      }, sh.label));
      svg.append(el('text', {
        x: shelfX + 16, y: y + 47,
        fill: P.muted, 'font-size': 10.8, opacity: isHi ? 0.95 : 0.55,
      }, sh.sub));

      // Node cards inside shelf (3 aligned columns: x = 180, 368, 556; width = 176, height = 46)
      sh.nodes.forEach((nd, cIdx) => {
        const nx = 180 + cIdx * 188;
        const ny = y + 10;
        const isSel = selectedOrgan === nd.repo;
        const g = el('g', { style: 'cursor:pointer', opacity: isHi ? 1 : 0.52 });

        g.append(el('rect', {
          x: nx, y: ny, width: 176, height: 46, rx: 8,
          fill: isSel ? (dark ? '#173332' : '#f0fdfa') : (dark ? '#162231' : '#f8fafc'),
          stroke: isSel ? P.accent : (isHi ? col : P.grid),
          'stroke-width': isSel ? 2.3 : 1.2,
          'stroke-dasharray': nd.companion ? '4 3' : undefined,
        }));
        g.append(el('circle', { cx: nx + 12, cy: ny + 17, r: 3.3, fill: col }));
        g.append(el('text', {
          x: nx + 21, y: ny + 21,
          fill: P.text, 'font-size': 12.2, 'font-weight': '720',
        }, nd.repo === 'lab-automation-atlas' ? 'automation-atlas' : nd.repo));
        g.append(el('text', {
          x: nx + 12, y: ny + 37,
          fill: P.muted, 'font-size': 10.5,
        }, nd.sub));

        g.addEventListener('click', () => {
          selectedOrgan = nd.repo;
          renderBrainSVG();
          renderInspector();
        });
        svg.append(g);
      });

      // Short vertical downward connector arrow strictly in the 16px gap between shelves!
      if (idx < SHELVES.length - 1) {
        const ay1 = y + shelfH + 2;
        const ay2 = y + stepY - 3;
        const spineX = 268;
        const activeArrow = hiSet.has(sh.code) && hiSet.has(SHELVES[idx + 1].code);
        svg.append(el('line', {
          x1: spineX, y1: ay1, x2: spineX, y2: ay2 - 3,
          stroke: activeArrow ? P.accent : P.axis,
          'stroke-width': activeArrow ? 2 : 1.3,
          opacity: activeArrow ? 0.9 : 0.4,
        }));
        svg.append(el('polygon', {
          points: `${spineX},${ay2} ${spineX - 4},${ay2 - 6} ${spineX + 4},${ay2 - 6}`,
          fill: activeArrow ? P.accent : P.axis,
          opacity: activeArrow ? 0.9 : 0.4,
        }));
      }
    });

    // 2. Right Column: L3 Post-Training Flywheel Enclosure (x: 806..1072, y: 18..494)
    const fwX = 806, fwW = 266, fwY = 18, fwH = 476;
    const l3Hi = hiSet.has('L3');
    svg.append(el('rect', {
      x: fwX, y: fwY, width: fwW, height: fwH, rx: 13,
      fill: l3Hi ? (dark ? 'rgba(251,191,36,0.08)' : '#fffbeb') : (dark ? '#0d1621' : '#f8fafc'),
      stroke: l3Hi ? P.amber : P.grid,
      'stroke-width': l3Hi ? 1.8 : 1.2,
      'stroke-dasharray': '5 4',
      opacity: l3Hi ? 1 : 0.58,
    }));

    svg.append(el('text', {
      x: fwX + fwW / 2, y: fwY + 30,
      fill: P.amber, 'font-size': 11.5, 'font-weight': '780', 'text-anchor': 'middle',
      'font-family': '"SFMono-Regular", Consolas, monospace',
    }, 'L3 · POST-TRAIN FLYWHEEL ↺'));
    svg.append(el('text', {
      x: fwX + fwW / 2, y: fwY + 48,
      fill: P.muted, 'font-size': 10.8, 'text-anchor': 'middle',
    }, 'Replay, Pack & RLVR Alignment'));

    FLYWHEEL_NODES.forEach((fn, fIdx) => {
      const nx = fwX + 24, ny = fn.y, nw = 218, nh = 62;
      const isSel = selectedOrgan === fn.repo;
      const g = el('g', { style: 'cursor:pointer', opacity: l3Hi ? 1 : 0.58 });

      g.append(el('rect', {
        x: nx, y: ny, width: nw, height: nh, rx: 9,
        fill: isSel ? (dark ? '#2b2312' : '#fef3c7') : (dark ? '#162231' : '#ffffff'),
        stroke: isSel ? P.amber : (l3Hi ? P.amber : P.grid),
        'stroke-width': isSel ? 2.3 : 1.3,
      }));
      g.append(el('circle', { cx: nx + 14, cy: ny + 22, r: 3.5, fill: P.amber }));
      g.append(el('text', {
        x: nx + 24, y: ny + 26,
        fill: P.text, 'font-size': 12.6, 'font-weight': '730',
      }, fn.repo));
      g.append(el('text', {
        x: nx + 14, y: ny + 45,
        fill: P.muted, 'font-size': 11,
      }, fn.sub));

      g.addEventListener('click', () => {
        selectedOrgan = fn.repo;
        renderBrainSVG();
        renderInspector();
      });
      svg.append(g);

      // Upward arrows strictly in the 74px vertical gap between flywheel cards!
      if (fIdx < FLYWHEEL_NODES.length - 1) {
        const nextTop = FLYWHEEL_NODES[fIdx + 1].y;
        const curBot = ny + nh;
        const midX = nx + nw / 2;
        svg.append(el('line', {
          x1: midX, y1: nextTop - 6, x2: midX, y2: curBot + 10,
          stroke: l3Hi ? P.amber : P.axis,
          'stroke-width': l3Hi ? 2 : 1.3,
          class: l3Hi ? 'flow-pulse-line' : undefined,
        }));
        svg.append(el('polygon', {
          points: `${midX},${curBot + 4} ${midX - 4.5},${curBot + 12} ${midX + 4.5},${curBot + 12}`,
          fill: l3Hi ? P.amber : P.axis,
        }));
      }
    });

    // 3. Clean Orthogonal Gutter Rail (x = 780, strictly inside empty channel 754..806!)
    // Bottom feed: L0 (y=461) & L4 (y=215) -> gutter x=780 -> into twinstep (x=830, y=403)
    const railActive = l3Hi || activeChapIdx === 0;
    const railCol = railActive ? P.amber : P.axis;
    const railOp = railActive ? 0.9 : 0.35;

    // L0 / L4 outcome feed into twinstep
    svg.append(el('path', {
      d: 'M 754 461 L 780 461 L 780 403 L 824 403',
      fill: 'none', stroke: railCol, 'stroke-width': 1.8, opacity: railOp,
      class: railActive ? 'flow-pulse-line' : undefined,
    }));
    svg.append(el('line', {
      x1: 754, y1: 215, x2: 780, y2: 215,
      stroke: railCol, 'stroke-width': 1.5, 'stroke-dasharray': '4 3', opacity: railOp,
    }));
    svg.append(el('polygon', {
      points: '828,403 820,398.5 820,407.5',
      fill: railCol, opacity: railOp,
    }));

    // Top return: labbench-posttrain (x=830, y=131) -> gutter x=780 -> up to L6 Brain (x=758, y=51)
    svg.append(el('path', {
      d: 'M 830 131 L 780 131 L 780 51 L 760 51',
      fill: 'none', stroke: railCol, 'stroke-width': 1.8, opacity: railOp,
      class: railActive ? 'flow-pulse-line' : undefined,
    }));
    svg.append(el('polygon', {
      points: '755,51 763,46.5 763,55.5',
      fill: railCol, opacity: railOp,
    }));

    svg.append(el('text', {
      x: fwX + fwW / 2, y: fwY + fwH - 14,
      fill: P.muted, 'font-size': 10.5, 'text-anchor': 'middle',
    }, '★ Companion organ in @yaniguan'));

    host.replaceChildren(svg);

    const cap = document.getElementById('cinema-caption-line');
    if (cap) {
      cap.innerHTML = `<strong>${esc(chap.lead)}</strong> ${esc(chap.text)}`;
    }
  }

  function renderInspector() {
    if (!DATA) return;
    const core = (DATA.repos || []).find(r => r.repo === selectedOrgan);
    const comp = (DATA.companions || []).find(c => c.repo === selectedOrgan);

    const badge = document.getElementById('insp-badge');
    const name = document.getElementById('insp-name');
    const hook = document.getElementById('insp-hook');
    const specs = document.getElementById('insp-mini-specs');
    const dosLink = document.getElementById('insp-dossier-link');
    const ghLink = document.getElementById('insp-github-link');

    if (core) {
      const c = core.concise || {};
      const sh = c.short || {};
      badge.textContent = `${core.layer} · ${core.layer_name.toUpperCase()}`;
      name.textContent = core.repo;
      hook.textContent = c.hook || core.tagline;
      specs.innerHTML = `
        <div class="mini-spec"><strong>Object</strong><span>${esc(sh.object || '')}</span></div>
        <div class="mini-spec"><strong>Data</strong><span>${esc(sh.data || '')}</span></div>
        <div class="mini-spec"><strong>Model</strong><span>${esc(sh.model || '')}</span></div>
        <div class="mini-spec"><strong>Unique Property</strong><span>${esc(sh.property || '')}</span></div>`;
      dosLink.style.display = '';
      dosLink.href = `repos/#${encodeURIComponent(core.repo)}`;
      ghLink.href = core.url;
    } else if (comp) {
      const cc = COMPANION_CARDS[comp.repo] || {};
      const sh = cc.short || {};
      badge.textContent = `COMPANION · ${comp.layer}`;
      name.textContent = `${comp.repo} ★`;
      hook.textContent = cc.hook || comp.summary;
      specs.innerHTML = `
        <div class="mini-spec"><strong>Object</strong><span>${esc(sh.object || '')}</span></div>
        <div class="mini-spec"><strong>Data</strong><span>${esc(sh.data || '')}</span></div>
        <div class="mini-spec"><strong>Model</strong><span>${esc(sh.model || '')}</span></div>
        <div class="mini-spec"><strong>Key Result</strong><span>${esc(sh.property || '')}</span></div>`;
      dosLink.style.display = 'none';
      ghLink.href = comp.page || comp.url;
    }
  }

  function renderDirectoryTable() {
    const tbody = document.getElementById('home-directory-tbody');
    if (!tbody || !DATA) return;

    const ordered = [...(DATA.repos || [])].sort(
      (a, b) => DISPLAY_LAYER_ORDER.indexOf(a.layer) - DISPLAY_LAYER_ORDER.indexOf(b.layer)
    );

    tbody.innerHTML = ordered.map(r => {
      const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';
      const c = r.concise || {};
      const kpi0 = (c.kpis && c.kpis[0]) ? `${c.kpis[0][0]} ${c.kpis[0][1]}` : '-';
      return `
        <tr>
          <td><span class="layer-code-pill ${colClass}">${esc(r.layer)}</span></td>
          <td><strong><a class="table-link" href="repos/#${encodeURIComponent(r.repo)}">${esc(r.repo)}</a></strong></td>
          <td style="color:var(--muted);">${esc(c.hook || r.tagline)}</td>
          <td style="white-space:nowrap;"><code>${esc(kpi0)}</code></td>
          <td style="white-space:nowrap;">
            <a class="table-link" href="repos/#${encodeURIComponent(r.repo)}">Card</a>
            <span style="color:var(--subtle);margin:0 6px;">·</span>
            <a class="table-link" href="${esc(r.url)}" target="_blank" rel="noopener">GitHub ↗</a>
          </td>
        </tr>`;
    }).join('');
  }

  function selectChapter(idx) {
    activeChapIdx = idx;
    document.querySelectorAll('[data-chap]').forEach(b => {
      b.classList.toggle('active', Number(b.dataset.chap) === idx);
    });
    renderBrainSVG();
  }

  async function init() {
    initThemeToggle(() => renderBrainSVG());

    document.querySelectorAll('[data-chap]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (autoTourTimer) {
          clearInterval(autoTourTimer);
          autoTourTimer = null;
          document.getElementById('cinema-cycle-btn').textContent = '▶ Auto-Tour';
        }
        selectChapter(Number(btn.dataset.chap));
      });
    });

    const cycleBtn = document.getElementById('cinema-cycle-btn');
    cycleBtn?.addEventListener('click', () => {
      if (autoTourTimer) {
        clearInterval(autoTourTimer);
        autoTourTimer = null;
        cycleBtn.textContent = '▶ Auto-Tour';
      } else {
        cycleBtn.textContent = '❚❚ Pause';
        autoTourTimer = setInterval(() => {
          selectChapter((activeChapIdx + 1) % CHAPTERS.length);
        }, 3200);
      }
    });

    document.getElementById('copy-citation')?.addEventListener('click', async () => {
      const text = document.getElementById('bibtex')?.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        document.getElementById('copy-status').textContent = 'Copied!';
      } catch {
        document.getElementById('copy-status').textContent = 'Select manually';
      }
    });

    DATA = await loadData('');
    renderBrainSVG();
    renderInspector();
    renderDirectoryTable();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
