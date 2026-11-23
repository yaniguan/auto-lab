/* 14-Repository Concise Visual Cards Controller (/repos/) */
(() => {
  'use strict';

  const { esc, fmtMd, initThemeToggle, loadData } = window.AutoLabShared;
  const LAYER_ORDER = ['L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'L0'];

  let DATA = null;
  let activeRepo = 'labbench-posttrain';
  let viewMode = 'detail';

  function orderedRepos() {
    if (!DATA) return [];
    return [...(DATA.repos || [])].sort(
      (a, b) => LAYER_ORDER.indexOf(a.layer) - LAYER_ORDER.indexOf(b.layer)
    );
  }

  function selectRepo(repoName, updateHash = true) {
    const exists = (DATA?.repos || []).some(r => r.repo === repoName);
    if (!exists) return;
    activeRepo = repoName;
    if (updateHash) history.replaceState(null, '', `#${encodeURIComponent(repoName)}`);
    if (viewMode !== 'detail') setViewMode('detail');
    renderSidebar();
    renderCard();
  }

  function setViewMode(mode) {
    viewMode = mode;
    document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('active', b.dataset.view === mode));
    document.getElementById('reader-view').style.display = mode === 'detail' ? '' : 'none';
    document.getElementById('matrix-view').style.display = mode === 'matrix' ? '' : 'none';
  }

  function renderSidebar() {
    const host = document.getElementById('sidebar-groups');
    if (!host || !DATA) return;
    const q = (document.getElementById('sidebar-search')?.value || '').trim().toLowerCase();

    const groupsHtml = LAYER_ORDER.map(code => {
      const layer = (DATA.layers || []).find(l => l.code === code);
      const items = (DATA.repos || []).filter(r => {
        if (r.layer !== code) return false;
        if (!q) return true;
        return JSON.stringify(r.concise || r).toLowerCase().includes(q) || r.repo.toLowerCase().includes(q);
      });
      if (!items.length) return '';
      return `
        <div class="sidebar-group">
          <div class="sidebar-group-label">${esc(code)} · ${esc(layer ? layer.name.split(',')[0] : '')}</div>
          ${items.map(r => `
            <button type="button" class="sidebar-item ${activeRepo === r.repo ? 'active' : ''}" data-repo="${esc(r.repo)}">
              <span>${esc(r.repo)}</span>
              <small style="font-size:11px;opacity:0.75;">${esc(r.issue_count)}</small>
            </button>`).join('')}
        </div>`;
    }).join('');

    host.innerHTML = groupsHtml || '<p style="padding:8px;font-size:12.5px;color:var(--muted);">No match.</p>';
    host.querySelectorAll('[data-repo]').forEach(btn => {
      btn.addEventListener('click', () => selectRepo(btn.dataset.repo));
    });
  }

  function renderCard() {
    const host = document.getElementById('dossier-host');
    if (!host || !DATA) return;
    const list = orderedRepos();
    const idx = list.findIndex(r => r.repo === activeRepo);
    const r = list[idx >= 0 ? idx : 0];
    if (!r) return;

    const prev = idx > 0 ? list[idx - 1] : null;
    const next = idx < list.length - 1 ? list[idx + 1] : null;
    const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';

    const c = r.concise || {};
    const sh = c.short || {};
    const fl = c.flow || ['Inputs', r.repo, 'Outputs'];
    const kpis = c.kpis || [];

    const kpiHtml = kpis.length
      ? `<div class="kpi-strip" style="margin:16px 0;grid-template-columns:repeat(${kpis.length}, 1fr);">
          ${kpis.map(([val, lbl]) => `
            <div class="kpi-cell">
              <small>${esc(lbl)}</small>
              <strong>${esc(val)}</strong>
            </div>`).join('')}
        </div>`
      : '';

    host.innerHTML = `
      <div class="dossier-header" style="margin-bottom:16px;padding-bottom:16px;">
        <div>
          <span class="small-label ${colClass}">${esc(r.layer)} · ${esc(r.layer_name)} · <code>${esc(r.commit_head)}</code></span>
          <h2>${esc(r.repo)}</h2>
          <p style="color:var(--muted);font-size:15.5px;margin-top:4px;">${esc(c.hook || r.tagline)}</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="${esc(r.url)}" target="_blank" rel="noopener">GitHub ↗</a>
          <a class="button secondary" href="../audit/?repo=${encodeURIComponent(r.repo)}">${esc(r.issue_count)} Issues →</a>
        </div>
      </div>

      <div class="flow-strip">
        <div class="flow-node"><small>Input</small>${esc(fl[0])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Method</small>${esc(fl[1])}</div>
        <span class="flow-arrow">→</span>
        <div class="flow-node"><small>Output</small>${esc(fl[2])}</div>
      </div>

      ${kpiHtml}

      <div class="bento-6">
        <div class="bento-tile">
          <span class="bento-label">1 · Object</span>
          <p>${esc(sh.object || r.object)}</p>
        </div>
        <div class="bento-tile">
          <span class="bento-label">2 · Data</span>
          <p>${esc(sh.data || r.data)}</p>
        </div>
        <div class="bento-tile">
          <span class="bento-label">3 · Model</span>
          <p>${esc(sh.model || r.model)}</p>
        </div>
        <div class="bento-tile">
          <span class="bento-label">4 · Training</span>
          <p>${esc(sh.training || r.training)}</p>
        </div>
        <div class="bento-tile">
          <span class="bento-label">5 · History</span>
          <p>${esc(sh.history || r.history)}</p>
        </div>
        <div class="bento-tile highlight">
          <span class="bento-label">6 · Unique Property</span>
          <p>${esc(sh.property || (r.unique_properties || [])[0] || '')}</p>
        </div>
      </div>

      <details class="deep-drawer">
        <summary>Expand detailed technical notes &amp; ARCHITECTURE_AND_HISTORY.md</summary>
        <div class="deep-drawer-body">
          <div><strong>Object</strong>${fmtMd(r.object)}</div>
          <div><strong>Data</strong>${fmtMd(r.data)}</div>
          <div><strong>Model</strong>${fmtMd(r.model)}</div>
          <div><strong>Training</strong>${fmtMd(r.training)}</div>
          <div><strong>History</strong>${fmtMd(r.history)}</div>
          <div>
            <a class="table-link" href="${esc(r.url)}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md" target="_blank" rel="noopener">
              Read full ARCHITECTURE_AND_HISTORY.md on GitHub ↗
            </a>
          </div>
        </div>
      </details>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:22px;padding-top:16px;border-top:1px solid var(--line);gap:12px;flex-wrap:wrap;">
        ${prev ? `<button type="button" class="button secondary" data-nav-repo="${esc(prev.repo)}">← ${esc(prev.repo)}</button>` : '<span></span>'}
        ${next ? `<button type="button" class="button secondary" data-nav-repo="${esc(next.repo)}">${esc(next.repo)} →</button>` : '<span></span>'}
      </div>`;

    host.querySelectorAll('[data-nav-repo]').forEach(btn => {
      btn.addEventListener('click', () => {
        selectRepo(btn.dataset.navRepo);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  function renderMatrix() {
    const tbody = document.getElementById('matrix-tbody');
    if (!tbody || !DATA) return;
    tbody.innerHTML = orderedRepos().map(r => {
      const sh = (r.concise && r.concise.short) || {};
      return `
        <tr>
          <td><span class="layer-code-pill">${esc(r.layer)}</span></td>
          <td><button type="button" class="table-link" style="background:none;border:0;padding:0;" data-jump-detail="${esc(r.repo)}">${esc(r.repo)}</button></td>
          <td>${esc(sh.object || '')}</td>
          <td>${esc(sh.data || '')}</td>
          <td>${esc(sh.model || '')}</td>
          <td>${esc(sh.training || '')}</td>
          <td>${esc(sh.property || '')}</td>
        </tr>`;
    }).join('');

    tbody.querySelectorAll('[data-jump-detail]').forEach(btn => {
      btn.addEventListener('click', () => selectRepo(btn.dataset.jumpDetail));
    });
  }

  async function init() {
    initThemeToggle();

    document.querySelectorAll('[data-view]').forEach(btn => {
      btn.addEventListener('click', () => setViewMode(btn.dataset.view));
    });
    document.getElementById('sidebar-search')?.addEventListener('input', renderSidebar);

    DATA = await loadData('../');
    const hashRepo = decodeURIComponent(location.hash.replace(/^#/, '').trim());
    if (hashRepo && (DATA.repos || []).some(r => r.repo === hashRepo)) {
      activeRepo = hashRepo;
    }

    window.addEventListener('hashchange', () => {
      const hr = decodeURIComponent(location.hash.replace(/^#/, '').trim());
      if (hr) selectRepo(hr, false);
    });

    renderSidebar();
    renderCard();
    renderMatrix();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
