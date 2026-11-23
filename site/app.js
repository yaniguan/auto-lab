/* Main Interactive Controller for Auto-Lab Studio
 * Powers: EN/中文 bilingual switch, Light/Dark theme, 7-Layer Organ Inspector,
 * 3 Interactive Co-Scientist Sandboxes, 14-Repo Dossier Matrix, and 300+ Issues Explorer.
 */
(() => {
  'use strict';

  let DATA = null;
  let activeOrgan = 'labbench-posttrain';
  let activeCapTab = 'loop';
  let activeScenario = 'serial_dilution';
  let activePtDomain = 'calisol';
  let activePtPack = 'packed_bf16';
  let activeDecideRound = 0;
  let activeLayerFilter = 'ALL';

  const PT_RECIPES = {
    calisol: {
      corpus: 'calisol23 (13,825 rows · electrolyte conductivity)',
      split: 'SplitGuard: 0 cross-formulation leak',
      stages: 'SFT -> MPO (DPO+BCO+SFT) -> GDPO + DAPO',
      cli: 'labrl recipe --algo gdpo_multireward --domain calisol_conductivity --model qwen3_8b --hardware node_8xa100_colocated',
      yaml: `recipe:
  algo: gdpo_multireward
  domain: calisol_conductivity
  model: qwen3_8b
  hardware: node_8xa100_colocated
rewards:
  primary: calisol_log_sigma_mae_gate
  anti_hack:
    think_token_cap: 512
    format_bonus_gated_on_correctness: true
status: CPU smoke verified; 8xA100 run PENDING`,
    },
    bioprobench: {
      corpus: 'BioProBench (PQA / ORD / ERR / GEN · CC BY-NC 4.0)',
      split: 'LAB-Bench canary blocked from training',
      stages: 'SFT Anchor -> DPO / TROPD -> GRPO (KL on)',
      cli: 'labrl recipe --algo tropd_distill --domain bioenvs_pqa_ord_err --model qwen25_7b --hardware local_1gpu_colocated',
      yaml: `recipe:
  algo: tropd_distill
  domain: bioenvs_pqa_ord_err
  model: qwen25_7b
  kl_anchor: sft_checkpoint
verifiers:
  - bioenvs.pqa (exact choice + anti-exploit audit)
  - bioenvs.ordering (step DAG Kendall/exact)
  - bioenvs.err (corrupted step localization)
status: Code-checked verifiers audited; GPU run PENDING`,
    },
    operator: {
      corpus: '49,139 multi-origin records + 20,517 robot frames',
      split: '40,790 train / 4,189 val / 4,160 test (0 group overlap)',
      stages: 'Action Schema SFT -> Constraint RM -> World Model + GRPO',
      cli: 'python operator/check_constraints.py --plan PLAN.json --constraints CONSTRAINTS.json',
      yaml: `operator_track:
  action_schema: src/labpt/actions.py (strict Data/Error)
  spatial_gate: swept-point AABB + joint & workspace bounds
  log_format: Unix-ns topic/timestamp/message JSONL
  evidence_origins:
    measurement: 29399
    compute: 13990
    ml_prediction: 5667
    human_annotation: 83`,
    },
  };

  const DECIDE_ROUNDS = [
    { r: 0, train: 676, test: 226, ans: '79.6%', covIn: '92.2%', maeIn: '0.656', width: '3.044' },
    { r: 1, train: 696, test: 206, ans: '85.4%', covIn: '93.2%', maeIn: '0.656', width: '3.134' },
    { r: 2, train: 716, test: 186, ans: '94.6%', covIn: '93.8%', maeIn: '0.640', width: '3.102' },
    { r: 3, train: 726, test: 176, ans: '100.0%', covIn: '94.9%', maeIn: '0.642', width: '3.210' },
  ];

  function lang() {
    return document.documentElement.dataset.lang === 'zh' ? 'zh' : 'en';
  }

  function esc(s) {
    return String(s ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function applyI18n() {
    const l = lang();
    document.querySelectorAll('[data-i18n-en]').forEach(node => {
      const txt = l === 'zh' ? node.getAttribute('data-i18n-zh') : node.getAttribute('data-i18n-en');
      if (txt) node.textContent = txt;
    });
    renderLayerStack();
    renderOrganInspector();
    renderLoopSandbox();
    if (window.AutoLabCinema) window.AutoLabCinema.redraw();
  }

  /* ---- 1. 7-Layer Brain & Organ Stack ---- */
  function renderLayerStack() {
    const host = document.getElementById('layer-stack-host');
    if (!host || !DATA) return;
    const l = lang();
    const repos = DATA.repos || [];
    const companions = DATA.companions || [];

    const html = (DATA.layers || []).map(layer => {
      const coreInLayer = repos.filter(r => r.layer === layer.code);
      const compInLayer = companions.filter(c => c.layer === layer.code);
      const chips = [
        ...coreInLayer.map(r => `
          <button type="button" class="organ-chip ${activeOrgan === r.repo ? 'active' : ''}" data-organ="${esc(r.repo)}">
            <span>${esc(r.repo)}</span>
            <small>${esc(r.issue_count || 22)} issues</small>
          </button>`),
        ...compInLayer.map(c => `
          <button type="button" class="organ-chip companion ${activeOrgan === c.repo ? 'active' : ''}" data-organ="${esc(c.repo)}">
            <span>${esc(c.repo)} ★</span>
            <small>${l === 'zh' ? '关联器官' : 'companion'}</small>
          </button>`),
      ].join('');

      const colClass = layer.color === 'purple' ? 'purple' : layer.color === 'blue' ? 'blue' : layer.color === 'amber' ? 'amber' : 'teal';
      return `
        <div class="layer-band">
          <div class="layer-meta">
            <span class="layer-badge ${colClass}">${esc(layer.code)} · ${esc(l === 'zh' ? layer.name_zh : layer.name_en)}</span>
            <span class="layer-analogy">${esc(l === 'zh' ? layer.brain_analogy_zh : layer.brain_analogy_en)}</span>
          </div>
          <div class="organ-chips">${chips}</div>
        </div>`;
    }).join('');

    host.innerHTML = html;
    host.querySelectorAll('[data-organ]').forEach(btn => {
      btn.addEventListener('click', () => selectOrgan(btn.dataset.organ, false));
    });
  }

  function selectOrgan(repoName, scrollToInspector) {
    activeOrgan = repoName;
    renderLayerStack();
    renderOrganInspector();
    if (scrollToInspector) {
      document.getElementById('organ-inspector')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function renderOrganInspector() {
    if (!DATA) return;
    const l = lang();
    const core = (DATA.repos || []).find(r => r.repo === activeOrgan);
    const comp = (DATA.companions || []).find(c => c.repo === activeOrgan);

    const tagEl = document.getElementById('insp-layer-tag');
    const titleEl = document.getElementById('insp-title');
    const descEl = document.getElementById('insp-desc');
    const ioEl = document.getElementById('insp-io');
    const ghBtn = document.getElementById('insp-github-btn');
    const dosBtn = document.getElementById('insp-dossier-btn');

    if (core) {
      tagEl.textContent = `LAYER ${core.layer} · ${core.layer_name.toUpperCase()} · HEAD ${core.commit_head || 'main'}`;
      titleEl.textContent = core.repo;
      descEl.textContent = core.object || core.tagline;
      const io = core.io_contract || {};
      ioEl.innerHTML = `
        <div><strong>Input:</strong> ${esc(io.inputs || 'Structured lab records / protocol specs')}</div>
        <div><strong>Output:</strong> ${esc(io.outputs || 'Verified predictions / compiled commands')}</div>
        <div><strong>Tracked Issues:</strong> <code>${esc(core.issue_count || 22)} open issues</code></div>`;
      ghBtn.href = core.url;
      dosBtn.style.display = '';
      dosBtn.onclick = () => {
        const card = document.getElementById(`card-${core.repo}`);
        if (card) {
          activeLayerFilter = 'ALL';
          document.querySelectorAll('[data-layer-filter]').forEach(b => b.classList.toggle('active', b.dataset.layerFilter === 'ALL'));
          renderRepoMatrix();
          document.getElementById(`card-${core.repo}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      };
    } else if (comp) {
      tagEl.textContent = `COMPANION ORGAN · LAYER ${comp.layer}`;
      titleEl.textContent = `${comp.repo} — ${l === 'zh' ? comp.organ_zh : comp.organ_en}`;
      descEl.textContent = l === 'zh' ? comp.summary_zh : comp.summary_en;
      ioEl.innerHTML = `
        <div><strong>Role:</strong> ${esc(l === 'zh' ? comp.organ_zh : comp.organ_en)}</div>
        <div><strong>Repository:</strong> <code>${esc(comp.url)}</code></div>
        ${comp.page ? `<div><strong>Studio Page:</strong> <a href="${esc(comp.page)}" target="_blank" rel="noopener" style="color:var(--blue);text-decoration:underline;">${esc(comp.page)}</a></div>` : ''}`;
      ghBtn.href = comp.page || comp.url;
      dosBtn.style.display = 'none';
    }
  }

  /* ---- 2. Sandboxes ---- */
  function renderLoopSandbox() {
    if (!DATA || !DATA.scenarios) return;
    const strict = document.getElementById('chk-strict-gate')?.checked ?? true;
    const recall = document.getElementById('chk-episodic-recall')?.checked ?? true;
    const key = `${activeScenario}__${strict ? 1 : 0}__${recall ? 1 : 0}`;
    const trace = DATA.scenarios[key] || DATA.scenarios[`${activeScenario}__1__1`];
    if (!trace) return;

    const pill = document.getElementById('loop-status-pill');
    pill.textContent = trace.final_status;
    pill.className = `pill ${trace.final_status}`;

    const list = document.getElementById('loop-trace-list');
    list.innerHTML = trace.steps.map(s => `
      <li class="trace-step">
        <span class="trace-layer">${esc(s.layer)}</span>
        <div class="trace-body">
          <strong>${esc(s.repo)} · ${esc(s.stage)}</strong>
          <span>${esc(s.summary)}</span>
        </div>
        <span class="pill ${esc(s.verdict)}">${esc(s.verdict)}</span>
      </li>`).join('');

    const kpis = document.getElementById('loop-kpis');
    kpis.innerHTML = `
      <div class="kpi-cell"><small>Protocol Hash</small><strong><code>${esc(trace.protocol_hash.slice(0, 8))}</code></strong></div>
      <div class="kpi-cell"><small>Layers Traversed</small><strong>${trace.steps.length}</strong></div>
      <div class="kpi-cell"><small>Sim Latency</small><strong>${trace.total_simulated_ms} ms</strong></div>
      <div class="kpi-cell"><small>Gate Mode</small><strong>${strict ? 'Default-Deny' : 'Advisory'}</strong></div>`;

    document.getElementById('loop-json-pre').textContent = JSON.stringify(trace, null, 2);
  }

  function renderPostTrainSandbox() {
    window.AutoLabCharts.renderPackingChart(document.getElementById('packing-chart-host'), activePtPack);
    const info = PT_RECIPES[activePtDomain] || PT_RECIPES.calisol;
    const packSpeed = { padded: '1.00× (30.6%)', bucketed: '2.09× (58.9%)', packed: '2.60× (92.1%)', packed_bf16: '5.42× (92.1%)' }[activePtPack];
    document.getElementById('pt-kpis').innerHTML = `
      <div class="kpi-cell"><small>Records</small><strong>49,139</strong></div>
      <div class="kpi-cell"><small>Packing Gain</small><strong>${esc(packSpeed)}</strong></div>
      <div class="kpi-cell"><small>SplitGuard</small><strong>0 leak</strong></div>
      <div class="kpi-cell"><small>Reward Templates</small><strong>8 verified</strong></div>`;
    document.getElementById('pt-recipe-pre').textContent = `# CLI\n$ ${info.cli}\n\n${info.yaml}`;
  }

  function renderDecideSandbox() {
    window.AutoLabCharts.renderTrustAndShiftChart(document.getElementById('trust-chart-host'), activeDecideRound);
    window.AutoLabCharts.renderGanttSVG(document.getElementById('gantt-chart-host'));
    const d = DECIDE_ROUNDS[activeDecideRound] || DECIDE_ROUNDS[0];
    document.getElementById('decide-kpis').innerHTML = `
      <div class="kpi-cell"><small>Train / Test</small><strong>${d.train} / ${d.test}</strong></div>
      <div class="kpi-cell"><small>Answered</small><strong>${d.ans}</strong></div>
      <div class="kpi-cell"><small>In-Trust Cov</small><strong>${d.covIn}</strong></div>
      <div class="kpi-cell"><small>In-Trust MAE</small><strong>${d.maeIn}</strong></div>`;
  }

  /* ---- 3. 14-Repo Full Dossier Matrix ---- */
  function renderRepoMatrix() {
    const host = document.getElementById('repo-cards-host');
    if (!host || !DATA) return;
    const q = (document.getElementById('repo-search-input')?.value || '').trim().toLowerCase();
    const list = (DATA.repos || []).filter(r => {
      if (activeLayerFilter !== 'ALL' && r.layer !== activeLayerFilter) return false;
      if (!q) return true;
      const blob = JSON.stringify(r).toLowerCase();
      return blob.includes(q);
    });

    host.innerHTML = list.map(r => {
      const props = (r.unique_properties || []).slice(0, 4).map(p => `<span class="prop-tag">${esc(p)}</span>`).join('');
      const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';
      return `
        <article class="repo-card" id="card-${esc(r.repo)}">
          <div class="repo-card-head">
            <div>
              <span class="small-label ${colClass}">${esc(r.layer)} · ${esc(r.layer_name)}</span>
              <h3><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.repo)} ↗</a></h3>
            </div>
            <span class="pill pass">${esc(r.issue_count || 22)} Issues</span>
          </div>
          <p class="repo-tagline">${esc(r.tagline)}</p>
          <dl class="dossier-dl">
            <div class="dossier-row"><dt>Object</dt><dd>${esc(r.object)}</dd></div>
            <div class="dossier-row"><dt>Data</dt><dd>${esc(r.data)}</dd></div>
            <div class="dossier-row"><dt>Model</dt><dd>${esc(r.model)}</dd></div>
            <div class="dossier-row"><dt>Training</dt><dd>${esc(r.training)}</dd></div>
            <div class="dossier-row"><dt>History</dt><dd>${esc(r.history)}</dd></div>
            <div class="dossier-row"><dt>Properties</dt><dd><div class="prop-tags">${props}</div></dd></div>
          </dl>
          <div class="repo-links">
            <a href="${esc(r.url)}" target="_blank" rel="noopener">Repository ↗</a>
            <span>·</span>
            <a href="${esc(r.url)}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md" target="_blank" rel="noopener">ARCHITECTURE_AND_HISTORY.md ↗</a>
            <span>·</span>
            <a href="${esc(r.url)}/issues" target="_blank" rel="noopener">GitHub Issues (${esc(r.issue_count || 22)}) ↗</a>
          </div>
        </article>`;
    }).join('');
  }

  /* ---- 4. 300+ Issues Deep Audit Explorer ---- */
  function renderAuditExplorer() {
    if (!DATA || !DATA.issues) return;
    const strip = document.getElementById('audit-repo-strip');
    const repoSel = document.getElementById('audit-repo-select');
    const curRepo = repoSel.value || 'ALL';
    const curCat = document.getElementById('audit-cat-select').value || 'ALL';
    const curSev = document.getElementById('audit-sev-select').value || 'ALL';
    const q = (document.getElementById('audit-search-input')?.value || '').trim().toLowerCase();

    const byRepo = DATA.issues.repos || {};
    const total = DATA.issues.total_issues || 0;
    const statEl = document.getElementById('stat-total-issues');
    if (statEl && total > 0) statEl.textContent = String(total);
    const heroLink = document.getElementById('hero-issues-link');
    if (heroLink && total > 0) {
      heroLink.setAttribute('data-i18n-en', `${total} Deep Audit Issues ↗`);
      heroLink.setAttribute('data-i18n-zh', `${total} 条深度检查 Issues ↗`);
      heroLink.textContent = lang() === 'zh' ? `${total} 条深度检查 Issues ↗` : `${total} Deep Audit Issues ↗`;
    }

    if (repoSel.options.length <= 1) {
      Object.keys(byRepo).forEach(rName => {
        const opt = document.createElement('option');
        opt.value = rName;
        opt.textContent = `${rName} (${byRepo[rName].count})`;
        repoSel.appendChild(opt);
      });
    }

    strip.innerHTML = Object.entries(byRepo).map(([rName, info]) => `
      <button type="button" class="audit-repo-pill ${curRepo === rName ? 'active' : ''}" data-audit-repo="${esc(rName)}">
        <strong>${esc(rName)}</strong>
        <span>${esc(info.count)} issues</span>
      </button>`).join('');

    strip.querySelectorAll('[data-audit-repo]').forEach(btn => {
      btn.addEventListener('click', () => {
        const r = btn.dataset.auditRepo;
        repoSel.value = repoSel.value === r ? 'ALL' : r;
        renderAuditExplorer();
      });
    });

    const flat = [];
    for (const [rName, info] of Object.entries(byRepo)) {
      if (curRepo !== 'ALL' && rName !== curRepo) continue;
      for (const it of info.items || []) {
        if (curCat !== 'ALL' && it.category !== curCat) continue;
        if (curSev !== 'ALL' && it.severity !== curSev) continue;
        if (q) {
          const hay = `${rName} ${it.title} ${(it.files || []).join(' ')} ${it.category}`.toLowerCase();
          if (!hay.includes(q)) continue;
        }
        flat.push({ repo: rName, ...it });
      }
    }

    const shown = flat.slice(0, 120);
    const tbody = document.getElementById('audit-issues-tbody');
    tbody.innerHTML = shown.map(it => {
      const issueUrl = it.url || `https://github.com/yaniguan/${it.repo}/issues`;
      const numLabel = it.number ? `#${it.number}` : 'View ↗';
      const filesHtml = (it.files || []).map(f => `<code>${esc(f)}</code>`).join(' ');
      return `
        <tr>
          <td><strong>${esc(it.repo)}</strong></td>
          <td><a href="${esc(issueUrl)}" target="_blank" rel="noopener" style="color:var(--blue);font-weight:700;">${esc(numLabel)}</a></td>
          <td><code>${esc(it.category)}</code></td>
          <td><span class="pill ${esc(it.severity)}">${esc(it.severity)}</span></td>
          <td>
            <div style="font-weight:630;color:var(--text);margin-bottom:3px;">
              <a href="${esc(issueUrl)}" target="_blank" rel="noopener">${esc(it.title)}</a>
            </div>
            <div style="font-size:11.5px;color:var(--muted);">${filesHtml}</div>
          </td>
        </tr>`;
    }).join('');

    document.getElementById('audit-showing-note').textContent =
      `Showing ${shown.length} of ${flat.length} matching issues (Total across all 14 repositories: ${total}).`;
  }

  /* ---- Initialization & Event Wiring ---- */
  async function init() {
    // Theme toggle
    const themeBtn = document.getElementById('theme-toggle');
    themeBtn?.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      themeBtn.textContent = next === 'dark' ? '☀ Light' : '☾ Dark';
      renderPostTrainSandbox();
      renderDecideSandbox();
      if (window.AutoLabCinema) window.AutoLabCinema.redraw();
    });

    // Language toggle
    const langBtn = document.getElementById('lang-toggle');
    langBtn?.addEventListener('click', () => {
      const next = document.documentElement.dataset.lang === 'zh' ? 'en' : 'zh';
      document.documentElement.dataset.lang = next;
      applyI18n();
    });

    // Sandbox tabs
    document.querySelectorAll('[data-cap-tab]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeCapTab = btn.dataset.capTab;
        document.querySelectorAll('[data-cap-tab]').forEach(b => b.classList.toggle('active', b.dataset.capTab === activeCapTab));
        document.querySelectorAll('.cap-pane').forEach(p => p.classList.toggle('active', p.id === `pane-cap-${activeCapTab}`));
        if (activeCapTab === 'posttrain') renderPostTrainSandbox();
        if (activeCapTab === 'decide') renderDecideSandbox();
      });
    });

    // Loop scenario controls
    document.querySelectorAll('[data-scenario]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeScenario = btn.dataset.scenario;
        document.querySelectorAll('[data-scenario]').forEach(b => b.classList.toggle('active', b.dataset.scenario === activeScenario));
        renderLoopSandbox();
      });
    });
    document.getElementById('chk-strict-gate')?.addEventListener('change', renderLoopSandbox);
    document.getElementById('chk-episodic-recall')?.addEventListener('change', renderLoopSandbox);

    // Post-train controls
    document.querySelectorAll('[data-pt-domain]').forEach(btn => {
      btn.addEventListener('click', () => {
        activePtDomain = btn.dataset.ptDomain;
        document.querySelectorAll('[data-pt-domain]').forEach(b => b.classList.toggle('active', b.dataset.ptDomain === activePtDomain));
        renderPostTrainSandbox();
      });
    });
    document.querySelectorAll('[data-pt-pack]').forEach(btn => {
      btn.addEventListener('click', () => {
        activePtPack = btn.dataset.ptPack;
        document.querySelectorAll('[data-pt-pack]').forEach(b => b.classList.toggle('active', b.dataset.ptPack === activePtPack));
        renderPostTrainSandbox();
      });
    });

    // Decide round controls
    document.querySelectorAll('[data-round]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeDecideRound = Number(btn.dataset.round);
        document.querySelectorAll('[data-round]').forEach(b => b.classList.toggle('active', Number(b.dataset.round) === activeDecideRound));
        renderDecideSandbox();
      });
    });

    // Repo filters
    document.querySelectorAll('[data-layer-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeLayerFilter = btn.dataset.layerFilter;
        document.querySelectorAll('[data-layer-filter]').forEach(b => b.classList.toggle('active', b.dataset.layerFilter === activeLayerFilter));
        renderRepoMatrix();
      });
    });
    document.getElementById('repo-search-input')?.addEventListener('input', renderRepoMatrix);

    // Audit filters
    ['audit-repo-select', 'audit-cat-select', 'audit-sev-select'].forEach(id => {
      document.getElementById(id)?.addEventListener('change', renderAuditExplorer);
    });
    document.getElementById('audit-search-input')?.addEventListener('input', renderAuditExplorer);

    // Copy citation
    document.getElementById('copy-citation')?.addEventListener('click', async () => {
      const text = document.getElementById('bibtex')?.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        document.getElementById('copy-status').textContent = 'Copied!';
      } catch {
        document.getElementById('copy-status').textContent = 'Select text manually';
      }
    });

    // Load autolab-data.json
    try {
      const res = await fetch('assets/autolab-data.json');
      DATA = await res.json();
    } catch (err) {
      console.error('Failed to load autolab-data.json:', err);
      DATA = { layers: [], repos: [], companions: [], scenarios: {}, issues: { total_issues: 0, repos: {} } };
    }

    renderLayerStack();
    renderOrganInspector();
    renderLoopSandbox();
    renderPostTrainSandbox();
    renderDecideSandbox();
    renderRepoMatrix();
    renderAuditExplorer();
    if (window.AutoLabCinema) window.AutoLabCinema.init();
  }

  window.AutoLabApp = { selectOrgan };
  document.addEventListener('DOMContentLoaded', init);
})();
