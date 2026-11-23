/* Interactive Lab Subpage Controller (/studio/) */
(() => {
  'use strict';

  const { esc, initThemeToggle, loadData, renderPackingChart, renderTrustChart, renderGanttSVG } = window.AutoLabShared;

  let DATA = null;
  let activeTab = 'loop';
  let activeScenario = 'serial_dilution';
  let activeDomain = 'calisol';
  let activePack = 'packed_bf16';
  let activeRound = 0;

  const PT_RECIPES = {
    calisol: {
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
    { r: 0, train: 676, test: 226, ans: '79.6%', covIn: '92.2%', maeIn: '0.656' },
    { r: 1, train: 696, test: 206, ans: '85.4%', covIn: '93.2%', maeIn: '0.656' },
    { r: 2, train: 716, test: 186, ans: '94.6%', covIn: '93.8%', maeIn: '0.640' },
    { r: 3, train: 726, test: 176, ans: '100.0%', covIn: '94.9%', maeIn: '0.642' },
  ];

  function activateTab(tab) {
    activeTab = tab;
    document.querySelectorAll('[data-tab]').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `pane-${tab}`));
    if (tab === 'posttrain') renderPostTrain();
    if (tab === 'decide') renderDecide();
  }

  function renderLoop() {
    if (!DATA || !DATA.scenarios) return;
    const strict = document.getElementById('chk-strict')?.checked ?? true;
    const recall = document.getElementById('chk-recall')?.checked ?? true;
    const key = `${activeScenario}__${strict ? 1 : 0}__${recall ? 1 : 0}`;
    const trace = DATA.scenarios[key] || DATA.scenarios[`${activeScenario}__1__1`];
    if (!trace) return;

    const pill = document.getElementById('loop-status-pill');
    pill.textContent = trace.final_status;
    pill.className = `pill ${trace.final_status}`;

    document.getElementById('loop-trace-list').innerHTML = trace.steps.map(s => `
      <li class="trace-step">
        <span class="trace-layer">${esc(s.layer)}</span>
        <div class="trace-body">
          <strong>${esc(s.repo)} · ${esc(s.stage)}</strong>
          <span>${esc(s.summary)}</span>
        </div>
        <span class="pill ${esc(s.verdict)}">${esc(s.verdict)}</span>
      </li>`).join('');

    document.getElementById('loop-kpis').innerHTML = `
      <div class="kpi-cell"><small>Protocol Hash</small><strong><code>${esc(trace.protocol_hash.slice(0, 8))}</code></strong></div>
      <div class="kpi-cell"><small>Steps</small><strong>${trace.steps.length}</strong></div>
      <div class="kpi-cell"><small>Sim Latency</small><strong>${trace.total_simulated_ms} ms</strong></div>
      <div class="kpi-cell"><small>Gate Policy</small><strong>${strict ? 'Default-Deny' : 'Advisory'}</strong></div>`;

    document.getElementById('loop-json-pre').textContent = JSON.stringify(trace, null, 2);
  }

  function renderPostTrain() {
    renderPackingChart(document.getElementById('packing-chart-host'), activePack);
    const info = PT_RECIPES[activeDomain] || PT_RECIPES.calisol;
    const gain = {
      padded: '1.00x (30.6%)',
      bucketed: '2.09x (58.9%)',
      packed: '2.60x (92.1%)',
      packed_bf16: '5.42x (92.1%)',
    }[activePack];
    document.getElementById('pt-kpis').innerHTML = `
      <div class="kpi-cell"><small>Ledger</small><strong>49,139</strong></div>
      <div class="kpi-cell"><small>Throughput</small><strong>${esc(gain)}</strong></div>
      <div class="kpi-cell"><small>SplitGuard</small><strong>0 leak</strong></div>
      <div class="kpi-cell"><small>Verifiers</small><strong>8 templates</strong></div>`;
    document.getElementById('pt-recipe-pre').textContent = `$ ${info.cli}\n\n${info.yaml}`;
  }

  function renderDecide() {
    renderTrustChart(document.getElementById('trust-chart-host'), activeRound);
    renderGanttSVG(document.getElementById('gantt-chart-host'));
    const d = DECIDE_ROUNDS[activeRound] || DECIDE_ROUNDS[0];
    document.getElementById('decide-kpis').innerHTML = `
      <div class="kpi-cell"><small>Train / Test</small><strong>${d.train} / ${d.test}</strong></div>
      <div class="kpi-cell"><small>Answered</small><strong>${d.ans}</strong></div>
      <div class="kpi-cell"><small>In-Trust Cov</small><strong>${d.covIn}</strong></div>
      <div class="kpi-cell"><small>In-Trust MAE</small><strong>${d.maeIn}</strong></div>`;
  }

  async function init() {
    initThemeToggle(() => {
      if (activeTab === 'posttrain') renderPostTrain();
      if (activeTab === 'decide') renderDecide();
    });

    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.addEventListener('click', () => activateTab(btn.dataset.tab));
    });

    document.querySelectorAll('[data-scenario]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeScenario = btn.dataset.scenario;
        document.querySelectorAll('[data-scenario]').forEach(b => b.classList.toggle('active', b.dataset.scenario === activeScenario));
        renderLoop();
      });
    });
    document.getElementById('chk-strict')?.addEventListener('change', renderLoop);
    document.getElementById('chk-recall')?.addEventListener('change', renderLoop);

    document.querySelectorAll('[data-domain]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeDomain = btn.dataset.domain;
        document.querySelectorAll('[data-domain]').forEach(b => b.classList.toggle('active', b.dataset.domain === activeDomain));
        renderPostTrain();
      });
    });
    document.querySelectorAll('[data-pack]').forEach(btn => {
      btn.addEventListener('click', () => {
        activePack = btn.dataset.pack;
        document.querySelectorAll('[data-pack]').forEach(b => b.classList.toggle('active', b.dataset.pack === activePack));
        renderPostTrain();
      });
    });

    document.querySelectorAll('[data-round]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeRound = Number(btn.dataset.round);
        document.querySelectorAll('[data-round]').forEach(b => b.classList.toggle('active', Number(b.dataset.round) === activeRound));
        renderDecide();
      });
    });

    DATA = await loadData('../');
    if (location.hash === '#posttrain') activateTab('posttrain');
    else if (location.hash === '#decide') activateTab('decide');
    renderLoop();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
