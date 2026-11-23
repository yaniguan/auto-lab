/* Overview Homepage Controller (Pure English, Clean Hierarchy & Pipeline) */
(() => {
  'use strict';

  const { esc, fmtMd, initThemeToggle, loadData, renderClosedLoopSVG } = window.AutoLabShared;

  let DATA = null;
  let selectedOrgan = 'lab-decide';
  let activeStageIdx = 3;

  const STAGE_NOTES = [
    'Stage 1 · Multimodal Sensory Cortex (L2): lab-ears extracts structured Amount, Temperature, Time, and Speed spans from protocol text (F1 0.75–0.91 on WLP) and monitors DCASE machine audio with 300–3400 Hz speech frequencies dropped; ouroboros-ocsr reads rotated 2D chemical figures.',
    'Stage 2 · Metacognitive & Epistemic Brain (L6): lab-ask-why retrieves supporting and contradicting rationales (0.789 recall@3 on SciFact) and poses discriminating tests; lab-decide answers only inside its calibrated kNN conformal trust region (92.2% coverage on ESOL) and abstains outside.',
    'Stage 3 · Executive Procurement & Scheduling (L5): buy-or-make classifies candidates into buyable, makeable in N steps, or unknown using strictly listed catalog prices; labshift schedules shared instrument pools with OR-Tools CP-SAT (30/30 window-feasible vs 24/30 greedy).',
    'Stage 4 · Digital-Twin Rehearsal & Default-Deny Gate (L4): lab-rehearsal recalls historical failures from runs.jsonl and dry-runs 96-well deck volumes and tip state; lab-verify enforces a 4-layer parse -> read-only -> schema -> execution gate before any actuator command passes.',
    'Stage 5 · Motor Compilation, Tactile Hands & Edge Runtime (L1–L0): stepbot compiles YAML/JSON steps to deterministic Opentrons Python API v2 (apiLevel 2.16); lab-hands plans collision-free RRT paths with last-centimeter tactile sensing; lab-feet runs distilled int8/4-bit models locally.',
    'Stage 6 · Post-Training & Error-Twin Flywheel (L3): twinstep injects 6 typed failure modes; labfill batches validation (225.8k proto/s) and packs BF16 sequences to 92.1% useful tokens (5.42x CPU tok/s); labbench-posttrain runs SFT -> MPO/TROPD -> GDPO+DAPO under SplitGuard.',
  ];

  // Order cortical-to-edge top-down, then L3 Flywheel at the bottom as a distinct feedback band
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
      const isRowActive = activeLayer === code;
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
        <div class="layer-row ${code === 'L3' ? 'flywheel-row' : ''} ${isRowActive ? 'active' : ''}" data-layer-row="${esc(code)}">
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
        const code = row.dataset.layerRow;
        const first = (DATA.repos || []).find(r => r.layer === code);
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
    const summary = document.getElementById('insp-summary');
    const contract = document.getElementById('insp-contract');
    const props = document.getElementById('insp-props');
    const dosLink = document.getElementById('insp-dossier-link');
    const ghLink = document.getElementById('insp-github-link');

    if (core) {
      badge.textContent = `LAYER ${core.layer} · ${core.layer_name.toUpperCase()}`;
      name.textContent = core.repo;
      summary.innerHTML = fmtMd(core.tagline);
      const io = core.io_contract || {};
      contract.innerHTML = `
        <div><strong>Inputs:</strong> <span>${fmtMd(io.inputs || '-')}</span></div>
        <div><strong>Outputs:</strong> <span>${fmtMd(io.outputs || '-')}</span></div>
        <div><strong>Audit:</strong> <span>${esc(core.issue_count || 22)} tracked GitHub Issues (HEAD <code>${esc(core.commit_head)}</code>)</span></div>`;
      props.innerHTML = (core.unique_properties || []).slice(0, 3).map(p => `<li>${fmtMd(p)}</li>`).join('');
      dosLink.style.display = '';
      dosLink.href = `repos/#${encodeURIComponent(core.repo)}`;
      ghLink.href = core.url;
    } else if (comp) {
      badge.textContent = `COMPANION ORGAN · LAYER ${comp.layer}`;
      name.textContent = `${comp.repo} ★`;
      summary.textContent = comp.summary;
      contract.innerHTML = `
        <div><strong>Organ:</strong> <span>${esc(comp.organ)}</span></div>
        <div><strong>Repo:</strong> <span>${esc(comp.url)}</span></div>`;
      props.innerHTML = `<li>Connected companion repository in @yaniguan providing domain-specialized equivariant perception, physics, or unified data schemas.</li>`;
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

    const ordered = [...(DATA.repos || [])].sort((a, b) => {
      return DISPLAY_LAYER_ORDER.indexOf(a.layer) - DISPLAY_LAYER_ORDER.indexOf(b.layer);
    });

    tbody.innerHTML = ordered.map(r => {
      const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';
      return `
        <tr>
          <td><span class="layer-code-pill ${colClass}">${esc(r.layer)}</span></td>
          <td><strong><a class="table-link" href="repos/#${encodeURIComponent(r.repo)}">${esc(r.repo)}</a></strong></td>
          <td style="color:var(--muted);">${esc(r.tagline)}</td>
          <td><a class="table-link" href="audit/?repo=${encodeURIComponent(r.repo)}">${esc(r.issue_count)} issues →</a></td>
          <td style="white-space:nowrap;">
            <a class="table-link" href="repos/#${encodeURIComponent(r.repo)}">Dossier</a>
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
