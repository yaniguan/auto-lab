/* Overview Homepage Controller (Visual, Concise, Zero Wall-of-Text) */
(() => {
  'use strict';

  const { esc, initThemeToggle, loadData, renderClosedLoopSVG } = window.AutoLabShared;

  let DATA = null;
  let selectedOrgan = 'lab-decide';
  let activeStageIdx = 3;

  const STAGE_NOTES = [
    '1. Sense (L2): lab-ears pulls Amount / Temp / Time / Speed from text and flags strange machine audio; ouroboros-ocsr reads 2D structures.',
    '2. Deliberate (L6): lab-ask-why finds reasons on both sides; lab-decide answers only inside its calibrated kNN zone (92.2% coverage).',
    '3. Plan & Shift (L5): buy-or-make checks stock vs 2-step routes; labshift schedules shared instruments via CP-SAT (30/30 feasible).',
    '4. Twin & Gate (L4): lab-rehearsal dry-runs 96-well volumes and tips; lab-verify runs a 4-layer default-deny SQL / protocol check.',
    '5. Act on Edge (L1–L0): stepbot compiles Opentrons v2 code; lab-hands plans obstacle-free RRT paths; lab-feet runs int8 / 4-bit models.',
    '6. Post-Train (L3): twinstep injects 6 error types; labfill packs BF16 batches (5.42x tok/s); labbench-posttrain runs SFT -> MPO -> GDPO.',
  ];

  const COMPANION_CARDS = {
    YLM: {
      hook: 'Reads English questions and 3D atoms together—outputs vectors that rotate with the molecule.',
      flow: ['Question + 3D xyz', 'SE(3) irreps attention', 'Force / dipole + LabLean'],
      short: {
        object: 'Answer 3D force & dipole queries with exact rotation equivariance.',
        data: 'TensorQA-v0 (84,757 questions on 20k QM9 molecules).',
        model: 'Frozen MiniLM / MatSciBERT + e3nn (l <= 2) cross-attention.',
        property: '0.960 force cosine across 32 rotations (~2e-6 equivariance error).',
      },
    },
    WignerFlow: {
      hook: 'Jumps molecular dynamics 50 fs per step without a numerical integrator.',
      flow: ['Last 3 MD frames', 'SO(2) Wigner-D + flow', 't + 50 fs + [physics] gate'],
      short: {
        object: 'Replace stiff 2 fs MD steps and gate untrained molecules for YLM.',
        data: '256-atom liquid argon NVE trajectories + CALiSol-23 alignment.',
        model: 'EquiTraj residual conditional flow matching + FrameSplit CPU API.',
        property: '4/5 seeds stable for 10,000 steps; strict refusal outside registry.',
      },
    },
    'ouroboros-ocsr': {
      hook: 'Reads molecule drawings from papers at any angle and checks stereochemistry in 3D.',
      flow: ['2D paper figure', 'C8 steerable CNN + beam', 'Stereo SMILES + 3D check'],
      short: {
        object: 'Turn 2D chemical figures into confidence-gated SMILES and 3D conformers.',
        data: 'Synthetic 24-angle drawings + untouched 300-image frozen-test-v2.',
        model: 'C8 steerable encoder + plain CNN ensemble + 229 ms int8 CPU API.',
        property: '65.8% across 24 angles with zero rotated training images.',
      },
    },
    assayfold: {
      hook: 'Collects scattered open lab datasets into one SHA-256-sealed, license-gated schema.',
      flow: ['12 open lab sources', 'UCUM units + SPDX gate', 'Parquet / RAG JSONL'],
      short: {
        object: 'Unify protocols, reactions, QM9, and LabPics under one strict record format.',
        data: 'AqSolDB, FreeSolv, ORD, QM9, RGD1, Transition1x, WLP, LabPics.',
        model: 'Pydantic extra=forbid schema + UCUM normalizer + license gate.',
        property: 'Blocks non-commercial & eval_only items from commercial exports.',
      },
    },
  };

  const DISPLAY_LAYER_ORDER = ['L6', 'L5', 'L4', 'L2', 'L1', 'L0', 'L3'];

  function renderStack() {
    const host = document.getElementById('stack-panel-host');
    if (!host || !DATA) return;

    const layersByCode = {};
    (DATA.layers || []).forEach(l => { layersByCode[l.code] = l; });
    const activeLayer = findLayerOfOrgan(selectedOrgan);

    host.innerHTML = DISPLAY_LAYER_ORDER.map(code => {
      const layer = layersByCode[code];
      if (!layer) return '';
      const coreRepos = (DATA.repos || []).filter(r => r.layer === code);
      const compRepos = (DATA.companions || []).filter(c => c.layer === code);
      const colClass = layer.color === 'purple' ? 'purple' : layer.color === 'blue' ? 'blue' : layer.color === 'amber' ? 'amber' : 'teal';

      const pills = [
        ...coreRepos.map(r => `
          <button type="button" class="repo-pill ${selectedOrgan === r.repo ? 'selected' : ''}" data-organ="${esc(r.repo)}">
            ${esc(r.repo)}
          </button>`),
        ...compRepos.map(c => `
          <button type="button" class="repo-pill companion ${selectedOrgan === c.repo ? 'selected' : ''}" data-organ="${esc(c.repo)}">
            ${esc(c.repo)} ★
          </button>`),
      ].join('');

      return `
        <div class="layer-row ${code === 'L3' ? 'flywheel-row' : ''} ${activeLayer === code ? 'active' : ''}" data-layer-row="${esc(code)}">
          <div class="layer-row-top">
            <div style="display:flex;align-items:center;gap:9px;flex-wrap:wrap;">
              <span class="layer-code-pill ${colClass}">${esc(code)}${code === 'L3' ? ' ↺' : ''}</span>
              <span class="layer-title">${esc(layer.name)}</span>
            </div>
            <span class="layer-brain-note">${esc(layer.brain_analogy)}</span>
          </div>
          <div class="chip-row">${pills}</div>
        </div>`;
    }).join('');

    host.querySelectorAll('[data-organ]').forEach(btn => {
      btn.addEventListener('click', ev => {
        ev.stopPropagation();
        selectedOrgan = btn.dataset.organ;
        renderStack();
        renderInspector();
      });
    });

    host.querySelectorAll('[data-layer-row]').forEach(row => {
      row.addEventListener('click', () => {
        const first = (DATA.repos || []).find(r => r.layer === row.dataset.layerRow);
        if (first) {
          selectedOrgan = first.repo;
          renderStack();
          renderInspector();
        }
      });
    });
  }

  function findLayerOfOrgan(name) {
    const core = (DATA.repos || []).find(r => r.repo === name);
    if (core) return core.layer;
    const comp = (DATA.companions || []).find(c => c.repo === name);
    return comp ? comp.layer : 'L6';
  }

  function renderInspector() {
    if (!DATA) return;
    const core = (DATA.repos || []).find(r => r.repo === selectedOrgan);
    const comp = (DATA.companions || []).find(c => c.repo === selectedOrgan);

    const badge = document.getElementById('insp-badge');
    const name = document.getElementById('insp-name');
    const hook = document.getElementById('insp-hook');
    const flow = document.getElementById('insp-flow');
    const specs = document.getElementById('insp-mini-specs');
    const dosLink = document.getElementById('insp-dossier-link');
    const ghLink = document.getElementById('insp-github-link');

    if (core) {
      const c = core.concise || {};
      const sh = c.short || {};
      const fl = c.flow || ['Inputs', core.repo, 'Outputs'];
      badge.textContent = `${core.layer} · ${core.layer_name.toUpperCase()}`;
      name.textContent = core.repo;
      hook.textContent = c.hook || core.tagline;
      flow.innerHTML = `
        <div class="flow-node"><small>In</small>${esc(fl[0])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Core</small>${esc(fl[1])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Out</small>${esc(fl[2])}</div>`;
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
      const fl = cc.flow || ['Input', comp.repo, 'Output'];
      const sh = cc.short || {};
      badge.textContent = `COMPANION · ${comp.layer}`;
      name.textContent = `${comp.repo} ★`;
      hook.textContent = cc.hook || comp.summary;
      flow.innerHTML = `
        <div class="flow-node"><small>In</small>${esc(fl[0])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Core</small>${esc(fl[1])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Out</small>${esc(fl[2])}</div>`;
      specs.innerHTML = `
        <div class="mini-spec"><strong>Object</strong><span>${esc(sh.object || '')}</span></div>
        <div class="mini-spec"><strong>Data</strong><span>${esc(sh.data || '')}</span></div>
        <div class="mini-spec"><strong>Model</strong><span>${esc(sh.model || '')}</span></div>
        <div class="mini-spec"><strong>Key Result</strong><span>${esc(sh.property || '')}</span></div>`;
      dosLink.style.display = 'none';
      ghLink.href = comp.page || comp.url;
    }
  }

  function renderPipeline() {
    renderClosedLoopSVG(document.getElementById('closed-loop-svg-host'), activeStageIdx, idx => {
      activeStageIdx = idx;
      renderPipeline();
    });
    const note = document.getElementById('closed-loop-stage-note');
    if (note) note.textContent = STAGE_NOTES[activeStageIdx] || STAGE_NOTES[0];
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
      const kpi0 = (c.kpis && c.kpis[0]) ? `${c.kpis[0][0]} ${c.kpis[0][1]}` : `${r.issue_count} issues`;
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

  async function init() {
    initThemeToggle(() => renderPipeline());

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
    const total = DATA?.issues?.total_issues;
    if (total) {
      const el = document.getElementById('home-issue-total');
      if (el) el.textContent = String(total);
    }
    renderStack();
    renderInspector();
    renderPipeline();
    renderDirectoryTable();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
