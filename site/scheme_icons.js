/* Monoline Scientific Scheme Icons (24x24) & Inter-Repo Relationship Graph
 * Style: Crisp 1.5px round-cap line-art ("scheme icon / sketch" style)
 */
(() => {
  'use strict';

  // Inner SVG markup for viewBox="0 0 24 24" (fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round")
  const ICONS = {
    'lab-ask-why': `
      <path d="M12 4v15M7 20h10M5 8h14"/>
      <path d="M5 8l-2.5 5h5L5 8zM19 8l-2.5 5h5L19 8z"/>
      <circle cx="12" cy="4" r="1.4"/>`,
    'lab-decide': `
      <circle cx="12" cy="12" r="8.5" stroke-dasharray="3 2.5"/>
      <circle cx="12" cy="12" r="4.8"/>
      <circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/>`,
    'buy-or-make': `
      <path d="M8 3h4M10 3v4.5L5.5 16a2 2 0 0 0 1.8 3h5.4"/>
      <path d="M14.5 11.5l4.5 0 2 2v4.5l-4.5 4.5-4-4 2-7z"/>
      <circle cx="18" cy="14" r="1" fill="currentColor" stroke="none"/>`,
    'labshift': `
      <rect x="3" y="5" width="8" height="3.2" rx="1"/>
      <rect x="8" y="10.4" width="9" height="3.2" rx="1"/>
      <rect x="13" y="15.8" width="8" height="3.2" rx="1"/>
      <path d="M4 3v18" stroke-dasharray="2 2.5"/>`,
    'lab-automation-atlas': `
      <circle cx="12" cy="12" r="8.5"/>
      <polygon points="15.5,8.5 13.3,13.3 8.5,15.5 10.7,10.7"/>
      <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>`,
    'lab-rehearsal': `
      <rect x="3" y="6" width="8" height="12" rx="1.8"/>
      <rect x="13" y="6" width="8" height="12" rx="1.8" stroke-dasharray="2.5 2"/>
      <path d="M8.5 3.8c2.2-1.5 4.8-1.5 7 0"/>
      <polyline points="14,2.5 15.8,3.9 14.2,5.2"/>`,
    'lab-verify': `
      <path d="M12 3l7 3v5.5c0 4.6-3 7.9-7 9.5-4-1.6-7-4.9-7-9.5V6l7-3z"/>
      <polyline points="8.8,12.2 11.1,14.5 15.5,9.8"/>`,
    'lab-attrib': `
      <path d="M3 18h18M6 18v-5l2.5-6 2.5 8 2.5-4 2.5 7"/>
      <circle cx="18.2" cy="7.2" r="2.8"/>
      <polyline points="17.1,7.2 18.0,8.1 19.6,6.3"/>`,
    'labbench-posttrain': `
      <path d="M19.5 10A8 8 0 0 0 6.2 6.5"/>
      <polyline points="6,3.8 6,6.8 9,6.8"/>
      <path d="M4.5 14a8 8 0 0 0 13.3 3.5"/>
      <polyline points="18,20.2 18,17.2 15,17.2"/>
      <circle cx="12" cy="12" r="2.3"/>`,
    'twinstep': `
      <path d="M4 12h5l3-5h8"/>
      <path d="M9 12l3 5h8" stroke-dasharray="2.5 2"/>
      <polyline points="18,5 20.2,7 18,9"/>
      <path d="M17.5 15.2l3 3.6M20.5 15.2l-3 3.6"/>`,
    'labfill': `
      <rect x="3.5" y="4" width="17" height="16" rx="2"/>
      <rect x="6.5" y="7" width="4.8" height="4.2" rx="0.7"/>
      <rect x="12.7" y="7" width="4.8" height="4.2" rx="0.7"/>
      <rect x="6.5" y="12.8" width="11" height="4.2" rx="0.7"/>`,
    'lab-ears': `
      <path d="M3.5 12h2l2-5 3 10 2.8-7 2.2 4h5"/>
      <circle cx="19.5" cy="7" r="1.4"/>`,
    'stepbot': `
      <path d="M10.5 3.5h3v4l1.5 2v6.5l-3 4.5-3-4.5V9.5l1.5-2v-4z"/>
      <path d="M6 8.5L3.8 12 6 15.5M18 8.5l2.2 3.5-2.2 3.5"/>`,
    'lab-hands': `
      <circle cx="6" cy="18" r="2.2"/>
      <path d="M7.5 16.3L12 9.5l5.5 2.5"/>
      <circle cx="12" cy="9.5" r="1.8"/>
      <path d="M17.5 10v5.5M15.5 15.5h4M15.8 19.5h3.4"/>`,
    'lab-feet': `
      <rect x="6.5" y="6.5" width="11" height="11" rx="2"/>
      <rect x="9.5" y="9.5" width="5" height="5" rx="0.8"/>
      <path d="M9 3.5v3M15 3.5v3M9 17.5v3M15 17.5v3M3.5 9h3M3.5 15h3M17.5 9h3M17.5 15h3"/>`,
    'YLM': `
      <polygon points="12,4 18,7.5 18,14.5 12,18 6,14.5 6,7.5"/>
      <path d="M12 11l6.5-5.5"/>
      <polyline points="15.5,5.2 18.7,5.3 18.5,8.5"/>`,
    'WignerFlow': `
      <circle cx="5.5" cy="15.5" r="2"/>
      <circle cx="11.5" cy="10.5" r="2" stroke-dasharray="2 1.8"/>
      <circle cx="18.5" cy="8.5" r="2.3"/>
      <path d="M7.3 14.2c2.5-2.5 5.5-4.5 8.8-5.2"/>`,
    'ouroboros-ocsr': `
      <path d="M2.5 12c2.3-4.2 5.7-6.3 9.5-6.3s7.2 2.1 9.5 6.3c-2.3 4.2-5.7 6.3-9.5 6.3S4.8 16.2 2.5 12z"/>
      <polygon points="12,8.5 15,10.2 15,13.8 12,15.5 9,13.8 9,10.2"/>`,
    'assayfold': `
      <ellipse cx="12" cy="6.5" rx="7" ry="2.8"/>
      <path d="M5 6.5v5.5c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8V6.5"/>
      <path d="M5 12v5.5c0 1.5 3.1 2.8 7 2.8s7-1.3 7-2.8V12"/>`,
  };

  // Explicit directed relationships between Auto-Lab & companion repositories
  // [sourceRepo, targetRepo, shortEdgeRole, kind ('forward' | 'flywheel' | 'ground')]
  const REPO_EDGES = [
    ['ouroboros-ocsr', 'YLM', '2D -> 3D SMILES', 'forward'],
    ['ouroboros-ocsr', 'WignerFlow', 'reagent SMILES', 'forward'],
    ['assayfold', 'labbench-posttrain', 'licensed records', 'flywheel'],
    ['assayfold', 'buy-or-make', 'shared schema', 'ground'],
    ['lab-ears', 'lab-ask-why', 'protocol claims', 'forward'],
    ['lab-ears', 'stepbot', 'slot parameters', 'forward'],
    ['YLM', 'lab-ask-why', '3D + text recall', 'forward'],
    ['YLM', 'lab-verify', 'LabLean rules', 'ground'],
    ['lab-ask-why', 'lab-decide', 'discriminating test', 'forward'],
    ['lab-decide', 'buy-or-make', 'trusted candidate', 'forward'],
    ['lab-automation-atlas', 'labshift', 'platform specs', 'ground'],
    ['lab-automation-atlas', 'stepbot', 'DSL standards', 'ground'],
    ['buy-or-make', 'labshift', 'sourced jobs', 'forward'],
    ['WignerFlow', 'lab-rehearsal', '[physics] gate', 'ground'],
    ['labshift', 'lab-rehearsal', 'scheduled run', 'forward'],
    ['lab-rehearsal', 'lab-verify', 'twin state', 'forward'],
    ['lab-verify', 'stepbot', 'Lean-MCP token', 'forward'],
    ['lab-verify', 'lab-hands', 'safe bounds', 'forward'],
    ['stepbot', 'lab-attrib', 'run telemetry', 'flywheel'],
    ['lab-attrib', 'assayfold', 'certified +/-', 'flywheel'],
    ['lab-attrib', 'lab-decide', 'recalibrate tau', 'flywheel'],
    ['stepbot', 'lab-feet', 'edge execution', 'forward'],
    ['lab-hands', 'lab-feet', 'quantized policy', 'forward'],
    ['lab-rehearsal', 'twinstep', 'failed runs.jsonl', 'flywheel'],
    ['stepbot', 'twinstep', 'clean protocols', 'flywheel'],
    ['twinstep', 'labfill', 'error + DAG pairs', 'flywheel'],
    ['labfill', 'labbench-posttrain', '5.42x packed BF16', 'flywheel'],
    ['labbench-posttrain', 'lab-decide', 'aligned brain', 'flywheel'],
    ['labbench-posttrain', 'lab-feet', 'distilled student', 'flywheel'],
  ];

  // Maps each repo to an anatomical group on the Robot Line-Art Sketch
  const ORGAN_GROUP = {
    'YLM': 'brain',
    'lab-ask-why': 'brain',
    'lab-decide': 'brain',
    'ouroboros-ocsr': 'eyes',
    'lab-ears': 'ears',
    'assayfold': 'crown',
    'lab-automation-atlas': 'crown',
    'WignerFlow': 'chest',
    'buy-or-make': 'chest',
    'lab-rehearsal': 'gate',
    'lab-verify': 'gate',
    'lab-attrib': 'gate',
    'labshift': 'schedule',
    'stepbot': 'pipette',
    'lab-hands': 'arms',
    'lab-feet': 'edge',
    'twinstep': 'posttrain',
    'labfill': 'posttrain',
    'labbench-posttrain': 'posttrain',
  };

  function iconMarkup(repo, size = 22) {
    const inner = ICONS[repo] || ICONS['lab-verify'];
    return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;
  }

  function neighborsOf(repo) {
    const upstream = [];
    const downstream = [];
    for (const [u, v, label, kind] of REPO_EDGES) {
      if (v === repo) upstream.push({ repo: u, label, kind });
      if (u === repo) downstream.push({ repo: v, label, kind });
    }
    return { upstream, downstream };
  }

  window.AutoLabIcons = {
    ICONS,
    REPO_EDGES,
    ORGAN_GROUP,
    iconMarkup,
    neighborsOf,
  };
})();
