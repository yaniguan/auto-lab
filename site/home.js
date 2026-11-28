/* Overview Homepage Controller
 * Part I: Monoline Two-Armed Lab Robot Sketch mapped to Auto-Lab organs & repos
 * Part II: Synchronized 18-Repo Scheme-Icon Relationship & Dataflow Map
 */
(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const { esc, initThemeToggle, loadData } = window.AutoLabShared;
  const { ICONS, REPO_EDGES, ORGAN_GROUP, iconMarkup, neighborsOf } = window.AutoLabIcons;
  const { STORIES } = window.AutoLabStories;

  let DATA = null;
  let selectedOrgan = 'lab-rehearsal';
  let inspDemoIdx = 0;

  const COMPANION_STORIES = {
    YLM: {
      headline: 'Read English questions and 3D atomic coordinates together—and return vectors that rotate cleanly with the molecule.',
      why: 'Text-only LLMs lose 3D geometry when molecules rotate; YLM fuses frozen language embeddings with SE(3)-equivariant e3nn layers and Lean 4 protocol verification (`LabLean`).',
      metrics: [
        ['0.960', 'force cosine (32 rotations)'],
        ['~2e-6', 'equivariance error'],
        ['84,757', 'TensorQA-v0 3D queries'],
      ],
      demos: [
        {
          tab: 'Rotated Force Query',
          verdict: 'EQUIVARIANT · ~2e-6 err',
          verdictTone: 'pass',
          output: 'Rotate molecule by R in SO(3) -> predicted dipole & force vectors rotate by exact R (vs -0.011 collapsed non-equivariant baseline).',
        },
        {
          tab: 'LabLean Protocol Gate',
          verdict: 'FORMAL LEAN 4 CHECK',
          verdictTone: 'pass',
          output: 'Verifies wet-lab protocol invariants formally in Lean 4 downstream of fast batched pre-filters.',
        },
      ],
    },
    WignerFlow: {
      headline: 'Jump molecular dynamics forward 50 fs per step without a numerical step-by-step integrator.',
      why: 'Classical 2 fs MD steps bottleneck electrolyte screening; EquiTraj flow matching leaps 25x further while refusing out-of-registry chemistry.',
      metrics: [
        ['50 fs', 'single-jump MD horizon'],
        ['4 / 5', 'seeds stable to 10k steps'],
        ['Strict', 'out-of-registry refusal'],
      ],
      demos: [
        {
          tab: '256-Atom Argon Jump',
          verdict: 'STABLE · 10,000 Steps',
          verdictTone: 'pass',
          output: 'EquiTraj residual conditional flow matching advances 50 fs per call while conserving NVE structure across 4/5 seeds.',
        },
        {
          tab: 'Untrained Molecule Check',
          verdict: 'REFUSED · Out of Registry',
          verdictTone: 'hold',
          output: 'FrameSplit `[physics]` API refuses untrained chemical compositions instead of hallucinating trajectories.',
        },
      ],
    },
    'ouroboros-ocsr': {
      headline: 'Read 2D chemical structure drawings from papers at any angle—and verify stereochemistry in 3D.',
      why: 'Standard optical chemical structure recognizers break when figures are rotated or skewed on journal pages.',
      metrics: [
        ['65.8%', 'accuracy across 24 angles'],
        ['0', 'rotated training images'],
        ['229 ms', 'int8 CPU inference'],
      ],
      demos: [
        {
          tab: 'Rotated Journal Figure',
          verdict: '65.8% · 24-Angle Mean',
          verdictTone: 'pass',
          output: 'C8 steerable encoder + CNN ensemble recovers canonical SMILES and 3D conformers on untouched frozen-test-v2.',
        },
      ],
    },
    assayfold: {
      headline: 'Unify scattered open chemistry, reaction, and wet-lab datasets under one SHA-256-sealed, license-gated schema.',
      why: 'Mixing incompatible units (`uM` vs `mol/L`) or non-commercial benchmarks into training pipelines causes silent errors and license breaches.',
      metrics: [
        ['27', 'open lab sources unified'],
        ['UCUM', 'strict unit normalizer'],
        ['SHA-256', 'license & split seal'],
      ],
      demos: [
        {
          tab: 'Commercial Export Gate',
          verdict: 'BLOCKED · Non-Commercial',
          verdictTone: 'fail',
          output: 'Pydantic extra=forbid schema blocks eval_only and non-commercial records before export to downstream post-training.',
        },
      ],
    },
  };

  // 8 Callout Cards framing the central Two-Armed Robot Sketch (4 left, 4 right)
  const ROBOT_CALLOUTS = [
    // Left column (x = 16, width = 258)
    {
      side: 'L', y: 20, h: 104, groups: ['brain'], iconRepo: 'lab-decide',
      tag: 'L6 · BRAIN', title: 'Ask Why & Calibrate',
      repos: ['lab-ask-why', 'lab-decide', 'YLM'],
      leader: 'M 274 72 H 320 A 8 8 0 0 1 328 80 V 88 A 8 8 0 0 0 336 96 H 516',
      anchor: [516, 96],
    },
    {
      side: 'L', y: 138, h: 104, groups: ['eyes', 'ears'], iconRepo: 'lab-ears',
      tag: 'L2 · EARS & EYES', title: 'Protocols, Sound & Figures',
      repos: ['lab-ears', 'ouroboros-ocsr'],
      leader: 'M 274 190 H 312 A 8 8 0 0 0 320 182 V 134 A 8 8 0 0 1 328 126 H 466',
      anchor: [466, 126],
    },
    {
      side: 'L', y: 256, h: 104, groups: ['pipette', 'arms'], iconRepo: 'lab-hands',
      tag: 'L1 · HANDS & COMPILER', title: 'Pipette, RRT & Touch',
      repos: ['stepbot', 'lab-hands'],
      leader: 'M 274 308 H 356',
      anchor: [356, 308],
    },
    {
      side: 'L', y: 374, h: 104, groups: ['edge'], iconRepo: 'lab-feet',
      tag: 'L0 · EDGE FEET', title: 'Distill & Quantize',
      repos: ['lab-feet'],
      leader: 'M 274 426 H 442',
      anchor: [442, 426],
    },
    // Right column (x = 806, width = 258)
    {
      side: 'R', y: 20, h: 104, groups: ['crown', 'chest'], iconRepo: 'buy-or-make',
      tag: 'L5 / L2 · DATA & STOCK', title: 'Ledger, Atlas & Make/Buy',
      repos: ['buy-or-make', 'lab-automation-atlas', 'assayfold'],
      leader: 'M 806 72 H 750 A 8 8 0 0 0 742 80 V 186 A 8 8 0 0 1 734 194 H 558',
      anchor: [558, 194],
    },
    {
      side: 'R', y: 138, h: 104, groups: ['schedule'], iconRepo: 'labshift',
      tag: 'L5 · SCHEDULE', title: 'Multi-Instrument Windows',
      repos: ['labshift'],
      leader: 'M 806 190 H 726 A 8 8 0 0 0 718 198 V 288 A 8 8 0 0 1 710 296 H 700',
      anchor: [700, 296],
    },
    {
      side: 'R', y: 256, h: 104, groups: ['gate', 'attrib'], iconRepo: 'lab-attrib',
      tag: 'L4 · TWIN, GATE & ATTRIB', title: 'Rehearse, Gate & Blame',
      repos: ['lab-rehearsal', 'lab-verify', 'lab-attrib', 'WignerFlow'],
      leader: 'M 806 308 H 764 A 8 8 0 0 1 756 300 V 248 A 8 8 0 0 0 748 240 H 552',
      anchor: [552, 240],
    },
    {
      side: 'R', y: 374, h: 104, groups: ['posttrain'], iconRepo: 'labbench-posttrain',
      tag: 'L3 · POST-TRAINING ↺', title: 'Twins, Packing & RLVR',
      repos: ['twinstep', 'labfill', 'labbench-posttrain'],
      leader: 'M 806 426 H 644',
      anchor: [644, 426],
    },
  ];

  // Coordinates for Part II: 18-Repo Scheme-Icon Relationship Map (viewBox 1080 x 476)
  // 4 clean horizontal rows with generous vertical routing alleys between them!
  const NET_NODES = [
    // Row 0 (y = 26): Sensory & Data Ingestion
    { repo: 'ouroboros-ocsr', sub: '2D -> SMILES', x: 64, y: 26, w: 196, comp: true },
    { repo: 'lab-ears', sub: 'WLP + machine audio', x: 318, y: 26, w: 204 },
    { repo: 'assayfold', sub: 'open data schema', x: 580, y: 26, w: 196, comp: true },
    { repo: 'lab-automation-atlas', sub: 'platforms & DSLs', x: 834, y: 26, w: 206 },

    // Row 1 (y = 142): Brain & Procurement
    { repo: 'YLM', sub: '3D + text brain', x: 40, y: 142, w: 184, comp: true },
    { repo: 'lab-ask-why', sub: 'opposing reasons', x: 256, y: 142, w: 192 },
    { repo: 'lab-decide', sub: 'conformal trust', x: 480, y: 142, w: 192 },
    { repo: 'buy-or-make', sub: 'stock vs N-step', x: 704, y: 142, w: 192 },
    { repo: 'WignerFlow', sub: '50-fs MD gate', x: 916, y: 142, w: 140, comp: true },

    // Row 2 (y = 262): Schedule, Twin Gate & Bench Execution
    { repo: 'labshift', sub: 'CP-SAT schedule', x: 36, y: 262, w: 180 },
    { repo: 'lab-rehearsal', sub: 'recall + 96w twin', x: 244, y: 262, w: 192 },
    { repo: 'lab-verify', sub: 'default-deny gate', x: 464, y: 262, w: 192 },
    { repo: 'stepbot', sub: 'Opentrons v2', x: 684, y: 262, w: 176 },
    { repo: 'lab-hands', sub: 'RRT + touch', x: 886, y: 262, w: 164 },

    // Row 3 (y = 386): Post-Run Attribution, Edge Runtime & Post-Training Flywheel
    { repo: 'lab-feet', sub: 'int8 / 4-bit edge', x: 36, y: 386, w: 180 },
    { repo: 'lab-attrib', sub: 'post-run blame', x: 238, y: 386, w: 182 },
    { repo: 'twinstep', sub: 'seeded error twins', x: 442, y: 386, w: 192 },
    { repo: 'labfill', sub: '5.42x BF16 + check', x: 656, y: 386, w: 192 },
    { repo: 'labbench-posttrain', sub: 'labrl SFT -> GDPO ↺', x: 870, y: 386, w: 190 },
  ];

  const DISPLAY_LAYER_ORDER = ['L6', 'L5', 'L4', 'L2', 'L1', 'L0', 'L3'];

  function el(tag, attrs = {}, text) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v !== undefined && v !== null) n.setAttribute(k, String(v));
    }
    if (text !== undefined) n.textContent = text;
    return n;
  }

  function appendSchemeIcon(parent, repo, x, y, size, strokeColor) {
    const g = el('g', {
      transform: `translate(${x}, ${y}) scale(${size / 24})`,
      fill: 'none',
      stroke: strokeColor,
      'stroke-width': 1.75,
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
    });
    g.innerHTML = ICONS[repo] || ICONS['lab-verify'];
    parent.append(g);
  }

  function selectRepo(repo) {
    if (selectedOrgan !== repo) {
      selectedOrgan = repo;
      inspDemoIdx = 0;
    }
    renderRobotSketch();
    renderRepoNetwork();
    renderInspector();
  }

  /* ---- PART I: Monoline Two-Armed Lab Robot Sketch ---- */
  function renderRobotSketch() {
    const host = document.getElementById('robot-sketch-host');
    if (!host) return;
    const dark = document.documentElement.dataset.theme === 'dark';
    const ink = dark ? '#e2e8f0' : '#1e293b';
    const muted = dark ? '#94a3b8' : '#64748b';
    const accent = dark ? '#2dd4bf' : '#0d9488';

    const activeGroup = ORGAN_GROUP[selectedOrgan] || 'brain';
    const svg = el('svg', { viewBox: '0 0 1080 498', role: 'img' });

    const organCls = grp => (grp === activeGroup ? 'sk-line sk-active-stroke' : 'sk-line');
    const organBox = grp => (grp === activeGroup ? 'sk-box sk-active-fill' : 'sk-box');

    // --- Central Robot & Lab Bench Drawing (centered at cx = 540) ---
    // 1. Crown Orbital (assayfold / atlas)
    const gCrown = el('g', { style: 'cursor:pointer' });
    gCrown.append(el('ellipse', { cx: 540, cy: 40, rx: 16, ry: 5.5, class: organCls('crown') }));
    gCrown.append(el('ellipse', { cx: 540, cy: 40, rx: 16, ry: 5.5, transform: 'rotate(60 540 40)', class: organCls('crown') }));
    gCrown.append(el('ellipse', { cx: 540, cy: 40, rx: 16, ry: 5.5, transform: 'rotate(-60 540 40)', class: organCls('crown') }));
    gCrown.append(el('line', { x1: 540, y1: 52, x2: 540, y2: 68, class: 'sk-line' }));
    gCrown.addEventListener('click', () => selectRepo('assayfold'));
    svg.append(gCrown);

    // 2. Side Ears (lab-ears)
    const gEars = el('g', { style: 'cursor:pointer' });
    gEars.append(el('circle', { cx: 472, cy: 126, r: 9, class: organBox('ears') }));
    gEars.append(el('circle', { cx: 608, cy: 126, r: 9, class: organBox('ears') }));
    gEars.addEventListener('click', () => selectRepo('lab-ears'));
    svg.append(gEars);

    // 3. Neck, Spine & Torso Shell
    svg.append(el('rect', { x: 525, y: 150, width: 30, height: 18, rx: 5, class: 'sk-box' }));
    svg.append(el('path', {
      d: 'M 500 256 L 484 190 A 22 22 0 0 1 505 164 H 575 A 22 22 0 0 1 596 190 L 580 256 A 10 10 0 0 1 570 264 H 510 A 10 10 0 0 1 500 256 Z',
      class: 'sk-box',
    }));
    svg.append(el('rect', { x: 528, y: 264, width: 24, height: 38, rx: 3, class: 'sk-box' }));
    svg.append(el('path', {
      d: 'M 472 354 V 334 A 10 10 0 0 1 482 324 H 598 A 10 10 0 0 1 608 334 V 354 Z',
      class: 'sk-box',
    }));

    // 4. Head Shell + Brain (YLM / ask-why / decide) + Visor Eyes (ouroboros)
    svg.append(el('rect', { x: 480, y: 68, width: 120, height: 86, rx: 24, class: 'sk-box' }));
    const gBrain = el('g', { style: 'cursor:pointer' });
    gBrain.append(el('path', {
      d: 'M 540 86 L 531 81 L 522 86 V 96 L 531 101 L 540 96 L 549 101 L 558 96 V 86 L 549 81 Z M 540 86 V 96',
      class: organCls('brain'),
    }));
    gBrain.addEventListener('click', () => selectRepo('lab-decide'));
    svg.append(gBrain);

    const gEyes = el('g', { style: 'cursor:pointer' });
    gEyes.append(el('rect', { x: 495, y: 106, width: 90, height: 24, rx: 12, class: organCls('eyes') }));
    gEyes.append(el('circle', { cx: 519, cy: 118, r: 6, class: organCls('eyes') }));
    gEyes.append(el('circle', { cx: 561, cy: 118, r: 6, class: organCls('eyes') }));
    gEyes.append(el('circle', { cx: 519, cy: 118, r: 2.2, fill: activeGroup === 'eyes' ? accent : ink }));
    gEyes.append(el('circle', { cx: 561, cy: 118, r: 2.2, fill: activeGroup === 'eyes' ? accent : ink }));
    gEyes.addEventListener('click', () => selectRepo('ouroboros-ocsr'));
    svg.append(gEyes);

    // 5. Chest Trajectory Core (WignerFlow / buy-or-make) & Default-Deny Shield Gate (rehearsal / verify)
    const gChest = el('g', { style: 'cursor:pointer' });
    gChest.append(el('circle', { cx: 540, cy: 194, r: 16, class: organBox('chest') }));
    gChest.append(el('path', { d: 'M 530 200 Q 538 182 547 191', class: organCls('chest'), 'stroke-dasharray': '2.5 2.5' }));
    gChest.append(el('circle', { cx: 547, cy: 191, r: 2.6, fill: activeGroup === 'chest' ? accent : ink }));
    gChest.addEventListener('click', () => selectRepo('buy-or-make'));
    svg.append(gChest);

    const gGate = el('g', { style: 'cursor:pointer' });
    gGate.append(el('path', {
      d: 'M 540 224 L 551 228.5 V 239 C 551 245.5 546 250 540 252 C 534 250 529 245.5 529 239 V 228.5 Z',
      class: organBox('gate'),
    }));
    gGate.append(el('polyline', { points: '536,238 539,241 545,235', class: organCls('gate') }));
    gGate.addEventListener('click', () => selectRepo('lab-verify'));
    svg.append(gGate);

    // 6. Left Articulated Arm + Tactile Gripper (lab-hands) + Pipette & 96-Well Plate (stepbot)
    const gArms = el('g', { style: 'cursor:pointer' });
    gArms.append(el('path', { d: 'M 486 320 L 444 252 L 372 282', class: organCls('arms'), 'stroke-width': 8 }));
    gArms.append(el('circle', { cx: 486, cy: 320, r: 9.5, class: organBox('arms') }));
    gArms.append(el('circle', { cx: 444, cy: 252, r: 8.5, class: organBox('arms') }));
    gArms.append(el('circle', { cx: 372, cy: 282, r: 6.5, class: organBox('arms') }));
    // Tactile gripper pads
    gArms.append(el('rect', { x: 358, y: 294, width: 28, height: 7, rx: 3.5, class: organBox('arms') }));
    gArms.append(el('rect', { x: 362, y: 301, width: 5, height: 18, rx: 2, class: organBox('arms') }));
    gArms.append(el('rect', { x: 377, y: 301, width: 5, height: 18, rx: 2, class: organBox('arms') }));
    gArms.addEventListener('click', () => selectRepo('lab-hands'));
    svg.append(gArms);

    const gPip = el('g', { style: 'cursor:pointer' });
    gPip.append(el('rect', { x: 369, y: 292, width: 6, height: 28, rx: 1.2, class: organBox('pipette') }));
    gPip.append(el('path', { d: 'M 369.5 320 L 371.2 338 H 372.8 L 374.5 320 Z', class: organBox('pipette') }));
    // 96-well plate side profile on bench
    gPip.append(el('rect', { x: 354, y: 342, width: 72, height: 12, rx: 2.5, class: organBox('pipette') }));
    for (let wx = 362; wx <= 418; wx += 9.3) {
      gPip.append(el('circle', { cx: wx, cy: 348, r: 2, class: organCls('pipette') }));
    }
    gPip.addEventListener('click', () => selectRepo('stepbot'));
    svg.append(gPip);

    // 7. Right Articulated Arm + Sample Tube & Shared Instrument Rack (labshift)
    const gSched = el('g', { style: 'cursor:pointer' });
    gSched.append(el('path', { d: 'M 594 320 L 636 252 L 700 282', class: organCls('schedule'), 'stroke-width': 8 }));
    gSched.append(el('circle', { cx: 594, cy: 320, r: 9.5, class: organBox('schedule') }));
    gSched.append(el('circle', { cx: 636, cy: 252, r: 8.5, class: organBox('schedule') }));
    gSched.append(el('circle', { cx: 700, cy: 282, r: 6.5, class: organBox('schedule') }));
    // Held vial + 2-slot instrument/tube rack on bench
    gSched.append(el('rect', { x: 686, y: 294, width: 28, height: 7, rx: 3.5, class: organBox('schedule') }));
    gSched.append(el('path', { d: 'M 695 301 V 330 A 5 5 0 0 0 705 330 V 301 Z', class: organBox('schedule') }));
    gSched.append(el('rect', { x: 656, y: 324, width: 11, height: 24, rx: 2.2, class: organBox('schedule') }));
    gSched.append(el('rect', { x: 672, y: 324, width: 11, height: 24, rx: 2.2, class: organBox('schedule') }));
    gSched.append(el('rect', { x: 650, y: 342, width: 58, height: 12, rx: 2.5, class: organBox('schedule') }));
    gSched.addEventListener('click', () => selectRepo('labshift'));
    svg.append(gSched);

    // 7b. Benchtop Diffraction Spectrometer & Post-Run Blame Organ (lab-attrib)
    const gAttrib = el('g', { style: 'cursor:pointer' });
    gAttrib.append(el('rect', { x: 436, y: 332, width: 28, height: 22, rx: 3, class: organBox('attrib') }));
    gAttrib.append(el('polyline', { points: '440,349 445,342 449,347 453,337 459,349', class: organCls('attrib') }));
    gAttrib.addEventListener('click', () => selectRepo('lab-attrib'));
    svg.append(gAttrib);

    // 8. Benchtop Slab
    svg.append(el('rect', { x: 338, y: 354, width: 404, height: 10, rx: 3, class: 'sk-box' }));

    // 9. Under-Bench Edge Board (lab-feet) & Post-Training GPU Cluster (L3)
    svg.append(el('line', { x1: 466, y1: 364, x2: 466, y2: 402, class: 'sk-line', 'stroke-dasharray': '3 3' }));
    svg.append(el('line', { x1: 618, y1: 364, x2: 618, y2: 402, class: 'sk-line', 'stroke-dasharray': '3 3' }));
    svg.append(el('path', {
      d: 'M 490 426 H 592',
      class: (activeGroup === 'edge' || activeGroup === 'posttrain') ? 'sk-edge-flywheel' : 'sk-line',
      'stroke-dasharray': '4 3',
    }));

    const gEdge = el('g', { style: 'cursor:pointer' });
    gEdge.append(el('rect', { x: 442, y: 402, width: 48, height: 48, rx: 7, class: organBox('edge') }));
    for (const d of [414, 426, 438]) {
      gEdge.append(el('line', { x1: 436, y1: d, x2: 442, y2: d, class: organCls('edge') }));
      gEdge.append(el('line', { x1: 490, y1: d, x2: 496, y2: d, class: organCls('edge') }));
    }
    gEdge.append(el('text', {
      x: 466, y: 430, fill: ink, 'font-size': 9.8, 'font-weight': '750', 'text-anchor': 'middle',
      'font-family': '"SFMono-Regular", Consolas, monospace',
    }, 'INT4'));
    gEdge.addEventListener('click', () => selectRepo('lab-feet'));
    svg.append(gEdge);

    const gPT = el('g', { style: 'cursor:pointer' });
    gPT.append(el('rect', { x: 592, y: 402, width: 52, height: 48, rx: 7, class: organBox('posttrain') }));
    for (const d of [414, 426, 438]) {
      gPT.append(el('line', { x1: 586, y1: d, x2: 592, y2: d, class: organCls('posttrain') }));
      gPT.append(el('line', { x1: 644, y1: d, x2: 650, y2: d, class: organCls('posttrain') }));
    }
    gPT.append(el('text', {
      x: 618, y: 425, fill: ink, 'font-size': 9.8, 'font-weight': '750', 'text-anchor': 'middle',
      'font-family': '"SFMono-Regular", Consolas, monospace',
    }, 'GPU'));
    gPT.append(el('text', {
      x: 618, y: 439, fill: muted, 'font-size': 8.5, 'font-weight': '650', 'text-anchor': 'middle',
    }, 'RLVR ↺'));
    gPT.addEventListener('click', () => selectRepo('labbench-posttrain'));
    svg.append(gPT);

    // --- 8 Surrounding Monoline Callout Cards & Rounded Leader Lines ---
    ROBOT_CALLOUTS.forEach(c => {
      const cx = c.side === 'L' ? 16 : 806;
      const cw = 258;
      const isCardHi = c.repos.includes(selectedOrgan) || c.groups.includes(activeGroup);

      // Leader path + anchor dot on robot
      svg.append(el('path', {
        d: c.leader,
        class: isCardHi ? 'sk-leader sk-active-stroke' : 'sk-leader',
      }));
      svg.append(el('circle', {
        cx: c.anchor[0], cy: c.anchor[1], r: 3,
        fill: isCardHi ? accent : muted,
      }));

      // Callout outer card
      const gCard = el('g', { style: 'cursor:pointer' });
      gCard.append(el('rect', {
        x: cx, y: c.y, width: cw, height: c.h, rx: 10,
        class: isCardHi ? 'sk-box sk-active-fill' : 'sk-box',
      }));

      appendSchemeIcon(gCard, c.iconRepo, cx + 14, c.y + 13, 20, isCardHi ? accent : ink);

      gCard.append(el('text', {
        x: cx + 41, y: c.y + 22,
        fill: isCardHi ? accent : muted,
        'font-size': 9.8, 'font-weight': '750', 'letter-spacing': '0.09em',
      }, c.tag));
      gCard.append(el('text', {
        x: cx + 41, y: c.y + 38,
        fill: ink, 'font-size': 12.6, 'font-weight': '700',
      }, c.title));

      // Clickable repo chips inside the callout card
      let rxCursor = cx + 14;
      let ryCursor = c.y + 54;
      c.repos.forEach(rName => {
        const shortName = rName === 'lab-automation-atlas' ? 'atlas' : rName === 'ouroboros-ocsr' ? 'ouroboros ★' : (COMPANION_STORIES[rName] ? `${rName} ★` : rName);
        const pillW = Math.max(58, shortName.length * 6.7 + 16);
        if (rxCursor + pillW > cx + cw - 10) {
          rxCursor = cx + 14;
          ryCursor += 25;
        }
        const isRepoSel = selectedOrgan === rName;
        const gChip = el('g', { style: 'cursor:pointer' });
        gChip.append(el('rect', {
          x: rxCursor, y: ryCursor, width: pillW, height: 21, rx: 5.5,
          fill: isRepoSel ? accent : (dark ? '#162231' : '#f1f5f9'),
          stroke: isRepoSel ? accent : (dark ? '#33475e' : '#cbd5e1'),
          'stroke-width': 1.1,
        }));
        gChip.append(el('text', {
          x: rxCursor + pillW / 2, y: ryCursor + 14,
          fill: isRepoSel ? (dark ? '#05201c' : '#ffffff') : ink,
          'font-size': 10.6, 'font-weight': '650', 'text-anchor': 'middle',
          'font-family': '"SFMono-Regular", Consolas, monospace',
        }, shortName));
        gChip.addEventListener('click', ev => {
          ev.stopPropagation();
          selectRepo(rName);
        });
        gCard.append(gChip);
        rxCursor += pillW + 6;
      });

      gCard.addEventListener('click', () => selectRepo(c.repos[0]));
      svg.append(gCard);
    });

    host.replaceChildren(svg);
  }

  /* ---- PART II: 18-Repo Scheme-Icon Relationship & Connection Map ---- */
  function renderRepoNetwork() {
    const host = document.getElementById('repo-network-host');
    if (!host) return;
    const dark = document.documentElement.dataset.theme === 'dark';
    const ink = dark ? '#e2e8f0' : '#1e293b';
    const muted = dark ? '#94a3b8' : '#64748b';
    const accent = dark ? '#2dd4bf' : '#0d9488';
    const amber = dark ? '#fbbf24' : '#d97706';

    const svg = el('svg', { viewBox: '0 0 1080 462', role: 'img' });
    const nodeH = 54;
    const byRepo = {};
    NET_NODES.forEach(n => { byRepo[n.repo] = n; });

    const { upstream, downstream } = neighborsOf(selectedOrgan);
    const neighborSet = new Set([
      ...upstream.map(x => x.repo),
      ...downstream.map(x => x.repo),
    ]);

    // Subtle row guides
    const rowLabels = [
      [14, 'SENSES & DATA'],
      [130, 'BRAIN & PROCUREMENT'],
      [250, 'SCHEDULE, GATE & HANDS'],
      [374, 'EDGE, ATTRIBUTION & POST-TRAINING ↺'],
    ];
    rowLabels.forEach(([ry, txt]) => {
      svg.append(el('text', {
        x: 38, y: ry, fill: muted, 'font-size': 9.5, 'font-weight': '750',
        'letter-spacing': '0.12em', opacity: 0.75,
      }, txt));
    });

    // Rounded orthogonal path builder (strictly follows empty alleys & outer margins -> ZERO box crossings!)
    function roundedOrtho(pts, radius = 7) {
      if (pts.length < 2) return '';
      let d = `M ${pts[0][0]} ${pts[0][1]}`;
      for (let i = 1; i < pts.length - 1; i++) {
        const [px, py] = pts[i - 1];
        const [cx, cy] = pts[i];
        const [nx, ny] = pts[i + 1];
        const dx1 = cx - px, dy1 = cy - py;
        const dx2 = nx - cx, dy2 = ny - cy;
        const len1 = Math.hypot(dx1, dy1), len2 = Math.hypot(dx2, dy2);
        const r = Math.min(radius, len1 / 2, len2 / 2);
        if (r < 1) {
          d += ` L ${cx} ${cy}`;
        } else {
          const sx = cx - (dx1 / len1) * r, sy = cy - (dy1 / len1) * r;
          const ex = cx + (dx2 / len2) * r, ey = cy + (dy2 / len2) * r;
          d += ` L ${sx.toFixed(1)} ${sy.toFixed(1)} Q ${cx} ${cy} ${ex.toFixed(1)} ${ey.toFixed(1)}`;
        }
      }
      const [lx, ly] = pts[pts.length - 1];
      return d + ` L ${lx} ${ly}`;
    }

    function buildCurve(u, v, edgeIdx) {
      const ux = Math.round(u.x + u.w / 2);
      const vx = Math.round(v.x + v.w / 2);
      const laneShift = ((edgeIdx % 3) - 1) * 5; // subtle separation in shared alleys

      // 1. Same row
      if (Math.abs(u.y - v.y) < 10) {
        const ym = u.y + nodeH / 2;
        if (v.x > u.x && v.x - (u.x + u.w) < 70) {
          // Adjacent neighbor in same row -> direct horizontal link
          return {
            d: `M ${u.x + u.w} ${ym} L ${v.x} ${ym}`,
            endX: v.x, endY: ym, dir: 'R',
          };
        }
        // Non-adjacent in bottom row (e.g. labbench-posttrain -> lab-feet) -> clean under-row rail
        const underY = 453;
        return {
          d: roundedOrtho([[ux, u.y + nodeH], [ux, underY], [vx, underY], [vx, v.y + nodeH]]),
          endX: vx, endY: v.y + nodeH, dir: 'U',
        };
      }

      // 2. Adjacent row downward (Row k -> Row k+1): route cleanly through empty inter-row alley!
      if (v.y > u.y && v.y - u.y < 140) {
        const y1 = u.y + nodeH, y2 = v.y;
        const alleyY = Math.round((y1 + y2) / 2) + laneShift;
        return {
          d: roundedOrtho([[ux, y1], [ux, alleyY], [vx, alleyY], [vx, y2]]),
          endX: vx, endY: y2, dir: 'D',
        };
      }

      // 3. Multi-row skip (e.g. Row 0 -> Row 2/3, or Row 3 -> Row 1): route via empty alley -> outer margin -> target alley!
      const useRight = (ux + vx) / 2 >= 520;
      const gutterX = useRight ? 1068 : 16;
      const exitY = v.y > u.y ? (u.y + nodeH + 16 + laneShift) : (u.y - 16 + laneShift);
      const enterY = v.y - 18 + laneShift;
      const startY = v.y > u.y ? (u.y + nodeH) : u.y;
      return {
        d: roundedOrtho([
          [ux, startY],
          [ux, exitY],
          [gutterX, exitY],
          [gutterX, enterY],
          [vx, enterY],
          [vx, v.y],
        ]),
        endX: vx, endY: v.y, dir: 'D',
      };
    }

    // 1. Draw quiet background edges first, then active edges on top
    const activeEdges = [];
    REPO_EDGES.forEach(([uName, vName, label, kind], idx) => {
      const u = byRepo[uName], v = byRepo[vName];
      if (!u || !v) return;
      const isAct = uName === selectedOrgan || vName === selectedOrgan;
      const geom = buildCurve(u, v, idx);
      if (isAct) {
        activeEdges.push({ uName, vName, label, kind, geom });
      } else {
        svg.append(el('path', { d: geom.d, class: 'sk-edge-quiet' }));
      }
    });

    // 2. Draw nodes (with monoline scheme icon + name + 2-word sub)
    NET_NODES.forEach(n => {
      const isSel = n.repo === selectedOrgan;
      const isNbr = neighborSet.has(n.repo);
      const g = el('g', { style: 'cursor:pointer' });

      let boxClass = 'sk-box';
      if (isSel) boxClass = 'sk-box sk-active-fill';
      else if (isNbr) boxClass = 'sk-box sk-neighbor-fill';

      g.append(el('rect', {
        x: n.x, y: n.y, width: n.w, height: nodeH, rx: 10,
        class: boxClass,
        'stroke-dasharray': (!isSel && n.comp) ? '4 3' : undefined,
        opacity: (isSel || isNbr) ? 1 : 0.74,
      }));

      const iconCol = isSel ? accent : (isNbr ? ink : muted);
      appendSchemeIcon(g, n.repo, n.x + 11, n.y + 15, 23, iconCol);

      const disp = n.repo === 'lab-automation-atlas' ? 'automation-atlas' : n.repo === 'ouroboros-ocsr' ? 'ouroboros ★' : (n.comp ? `${n.repo} ★` : n.repo);
      g.append(el('text', {
        x: n.x + 41, y: n.y + 24,
        fill: ink, 'font-size': 12, 'font-weight': isSel ? '760' : '680',
      }, disp));
      g.append(el('text', {
        x: n.x + 41, y: n.y + 40,
        fill: muted, 'font-size': 10.4,
      }, n.sub));

      g.addEventListener('click', () => selectRepo(n.repo));
      svg.append(g);
    });

    // 3. Draw active edges & crisp arrowheads (labels live cleanly in the Connections bar below)
    activeEdges.forEach(({ kind, geom }) => {
      const isFly = kind === 'flywheel';
      const col = isFly ? amber : accent;
      svg.append(el('path', {
        d: geom.d,
        class: isFly ? 'sk-edge-flywheel' : 'sk-edge-active',
      }));

      const { endX, endY, dir } = geom;
      const pts = dir === 'R'
        ? `${endX},${endY} ${endX - 7},${endY - 4} ${endX - 7},${endY + 4}`
        : dir === 'L'
        ? `${endX},${endY} ${endX + 7},${endY - 4} ${endX + 7},${endY + 4}`
        : dir === 'U'
        ? `${endX},${endY} ${endX - 4},${endY + 7} ${endX + 4},${endY + 7}`
        : `${endX},${endY} ${endX - 4},${endY - 7} ${endX + 4},${endY - 7}`;
      svg.append(el('polygon', { points: pts, fill: col }));
    });

    host.replaceChildren(svg);

    // 4. Render clickable Upstream -> Selected -> Downstream bar below Part II
    const bar = document.getElementById('conn-trace-bar');
    if (bar) {
      const upHtml = upstream.length
        ? upstream.map(u => `<button type="button" class="conn-chip" data-jump-repo="${esc(u.repo)}">${iconMarkup(u.repo, 14)} <span>${esc(u.repo)}</span> <small>(${esc(u.label)})</small></button>`).join('')
        : '<span style="color:var(--muted);">External / raw input</span>';
      const downHtml = downstream.length
        ? downstream.map(d => `<button type="button" class="conn-chip" data-jump-repo="${esc(d.repo)}">${iconMarkup(d.repo, 14)} <span>${esc(d.repo)}</span> <small>(${esc(d.label)})</small></button>`).join('')
        : '<span style="color:var(--muted);">Terminal output</span>';

      bar.innerHTML = `
        <strong style="font-size:11px;text-transform:uppercase;letter-spacing:0.7px;color:var(--muted);">Connections:</strong>
        ${upHtml}
        <span class="step-sep">→</span>
        <span class="conn-chip current">${iconMarkup(selectedOrgan, 15)} ${esc(selectedOrgan)}</span>
        <span class="step-sep">→</span>
        ${downHtml}`;

      bar.querySelectorAll('[data-jump-repo]').forEach(btn => {
        btn.addEventListener('click', () => selectRepo(btn.dataset.jumpRepo));
      });
    }
  }

  function fmtInline(text) {
    return esc(text || '').replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  function renderStoryMid(story) {
    const demos = story.demos || [];
    const safeIdx = Math.min(inspDemoIdx, Math.max(0, demos.length - 1));
    const d = demos[safeIdx];
    const firstTwoLines = d ? d.output.split('\n').filter(Boolean).slice(0, 2).join('\n') : '';

    return `
      <div class="insp-story-mid">
        ${d ? `
          <div class="insp-demo-row">
            <div class="insp-demo-pills">
              ${demos.map((item, i) => `
                <button type="button" class="insp-demo-btn ${i === safeIdx ? 'active' : ''}" data-insp-demo="${i}">
                  ${esc(item.tab.replace(/^\d+\s*·\s*/, ''))}
                </button>`).join('')}
            </div>
            <span class="pill ${esc(d.verdictTone || 'pass')}">${esc(d.verdict)}</span>
          </div>
          <pre class="insp-snippet">${esc(firstTwoLines)}</pre>
        ` : ''}
        <div class="insp-kpi-row">
          ${(story.metrics || []).map(([v, l]) => `<span class="insp-kpi-chip"><strong>${esc(v)}</strong>${esc(l)}</span>`).join('')}
        </div>
      </div>`;
  }

  function renderInspector() {
    if (!DATA) return;
    const core = (DATA.repos || []).find(r => r.repo === selectedOrgan);
    const comp = (DATA.companions || []).find(c => c.repo === selectedOrgan);

    const badge = document.getElementById('insp-badge');
    const iconEl = document.getElementById('insp-icon');
    const name = document.getElementById('insp-name');
    const hook = document.getElementById('insp-hook');
    const whyEl = document.getElementById('insp-why');
    const previewHost = document.getElementById('insp-story-preview');
    const dosLink = document.getElementById('insp-dossier-link');
    const ghLink = document.getElementById('insp-github-link');

    if (iconEl) iconEl.innerHTML = iconMarkup(selectedOrgan, 24);

    if (core) {
      const story = STORIES[core.repo] || { headline: core.tagline, why: core.object, metrics: [], demos: [] };
      badge.textContent = `${core.layer} · ${core.layer_name.toUpperCase()}`;
      name.textContent = core.repo;
      hook.innerHTML = fmtInline(story.headline);
      if (whyEl) whyEl.innerHTML = `<strong style="color:var(--accent);">Why:</strong> ${fmtInline(story.why)}`;
      if (previewHost) previewHost.innerHTML = renderStoryMid(story);
      dosLink.style.display = '';
      dosLink.href = `repos/#${encodeURIComponent(core.repo)}`;
      ghLink.href = core.url;
    } else if (comp) {
      const story = COMPANION_STORIES[comp.repo] || { headline: comp.summary, why: '', metrics: [], demos: [] };
      badge.textContent = `COMPANION · ${comp.layer}`;
      name.textContent = `${comp.repo} ★`;
      hook.innerHTML = fmtInline(story.headline);
      if (whyEl) whyEl.innerHTML = story.why ? `<strong style="color:var(--accent);">Why:</strong> ${fmtInline(story.why)}` : '';
      if (previewHost) previewHost.innerHTML = renderStoryMid(story);
      dosLink.style.display = 'none';
      ghLink.href = comp.page || comp.url;
    }

    previewHost?.querySelectorAll('[data-insp-demo]').forEach(btn => {
      btn.addEventListener('click', () => {
        inspDemoIdx = Number(btn.dataset.inspDemo) || 0;
        renderInspector();
      });
    });
  }

  function renderDirectoryTable() {
    const tbody = document.getElementById('home-directory-tbody');
    if (!tbody || !DATA) return;

    const ordered = [...(DATA.repos || [])].sort(
      (a, b) => DISPLAY_LAYER_ORDER.indexOf(a.layer) - DISPLAY_LAYER_ORDER.indexOf(b.layer)
    );

    tbody.innerHTML = ordered.map(r => {
      const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';
      const story = STORIES[r.repo] || {};
      const m0 = (story.metrics && story.metrics[0]) ? `${story.metrics[0][0]} ${story.metrics[0][1]}` : '-';
      return `
        <tr>
          <td><span class="layer-code-pill ${colClass}">${esc(r.layer)}</span></td>
          <td>
            <a class="table-link" href="repos/#${encodeURIComponent(r.repo)}" style="display:inline-flex;align-items:center;gap:7px;">
              ${iconMarkup(r.repo, 17)} <strong>${esc(r.repo)}</strong>
            </a>
          </td>
          <td style="color:var(--muted);">${fmtInline(story.headline || r.tagline)}</td>
          <td style="white-space:nowrap;"><code>${esc(m0)}</code></td>
          <td style="white-space:nowrap;">
            <a class="table-link" href="repos/#${encodeURIComponent(r.repo)}">Story</a>
            <span style="color:var(--subtle);margin:0 6px;">·</span>
            <a class="table-link" href="${esc(r.url)}" target="_blank" rel="noopener">GitHub ↗</a>
            ${r.repo === 'lab-attrib' ? '<span style="color:var(--subtle);margin:0 6px;">·</span><a class="table-link" href="assets/lab_attrib_preprint.pdf" target="_blank" rel="noopener">Paper ↗</a>' : ''}
          </td>
        </tr>`;
    }).join('');
  }

  async function init() {
    initThemeToggle(() => {
      renderRobotSketch();
      renderRepoNetwork();
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
    renderRobotSketch();
    renderRepoNetwork();
    renderInspector();
    renderDirectoryTable();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
