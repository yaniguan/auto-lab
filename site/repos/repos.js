/* 14-Repository Technical Dossiers Controller (/repos/) */
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
    renderDossier();
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
        return JSON.stringify(r).toLowerCase().includes(q);
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

    host.innerHTML = groupsHtml || '<p style="padding:8px;font-size:12.5px;color:var(--muted);">No matching repositories.</p>';
    host.querySelectorAll('[data-repo]').forEach(btn => {
      btn.addEventListener('click', () => selectRepo(btn.dataset.repo));
    });
  }

  function renderDossier() {
    const host = document.getElementById('dossier-host');
    if (!host || !DATA) return;
    const list = orderedRepos();
    const idx = list.findIndex(r => r.repo === activeRepo);
    const r = list[idx >= 0 ? idx : 0];
    if (!r) return;

    const prev = idx > 0 ? list[idx - 1] : null;
    const next = idx < list.length - 1 ? list[idx + 1] : null;
    const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';

    const metrics = (r.key_metrics || []).slice(0, 4);
    const kpiHtml = metrics.length
      ? `<div class="kpi-strip" style="margin-bottom:24px;grid-template-columns:repeat(${metrics.length}, 1fr);">
          ${metrics.map(m => `
            <div class="kpi-cell">
              <small>${esc(m.label)}</small>
              <strong>${esc(m.value)}</strong>
            </div>`).join('')}
        </div>`
      : '';

    const io = r.io_contract || {};
    host.innerHTML = `
      <div class="dossier-header">
        <div>
          <span class="small-label ${colClass}">${esc(r.layer)} · ${esc(r.layer_name)} · HEAD ${esc(r.commit_head)}</span>
          <h2>${esc(r.repo)}</h2>
          <p style="color:var(--muted);font-size:15px;max-width:640px;">${esc(r.tagline)}</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="${esc(r.url)}" target="_blank" rel="noopener">GitHub Repo ↗</a>
          <a class="button secondary" href="${esc(r.url)}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md" target="_blank" rel="noopener">ARCHITECTURE_AND_HISTORY.md ↗</a>
          <a class="button secondary" href="../audit/?repo=${encodeURIComponent(r.repo)}">${esc(r.issue_count)} Audit Issues →</a>
        </div>
      </div>

      ${kpiHtml}

      <div class="dossier-sections">
        <section class="dossier-block">
          <h3>1. Object</h3>
          <p>${fmtMd(r.object)}</p>
        </section>

        <section class="dossier-block">
          <h3>2. Data</h3>
          <p>${fmtMd(r.data)}</p>
        </section>

        <section class="dossier-block">
          <h3>3. Model</h3>
          <p>${fmtMd(r.model)}</p>
        </section>

        <section class="dossier-block">
          <h3>4. Training</h3>
          <p>${fmtMd(r.training)}</p>
        </section>

        <section class="dossier-block">
          <h3>5. History</h3>
          <p>${fmtMd(r.history)}</p>
        </section>

        <section class="dossier-block">
          <h3>6. Unique Properties</h3>
          <ul>
            ${(r.unique_properties || []).map(p => `<li>${fmtMd(p)}</li>`).join('')}
          </ul>
        </section>

        <section class="dossier-block">
          <h3>Input &amp; Output Contract</h3>
          <div class="inspector-box">
            <div><strong>Inputs:</strong> <span>${fmtMd(io.inputs || '-')}</span></div>
            <div><strong>Outputs:</strong> <span>${fmtMd(io.outputs || '-')}</span></div>
          </div>
        </section>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:28px;padding-top:18px;border-top:1px solid var(--line);gap:12px;flex-wrap:wrap;">
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
    const clip = (s, n = 135) => {
      const str = String(s || '').replace(/`/g, '');
      return str.length <= n ? str : str.slice(0, n - 1) + '…';
    };
    tbody.innerHTML = orderedRepos().map(r => `
      <tr>
        <td><span class="layer-code-pill">${esc(r.layer)}</span></td>
        <td><button type="button" class="table-link" style="background:none;border:0;padding:0;" data-jump-detail="${esc(r.repo)}">${esc(r.repo)}</button></td>
        <td>${esc(clip(r.object))}</td>
        <td>${esc(clip(r.data))}</td>
        <td>${esc(clip(r.model))}</td>
        <td>${esc(clip(r.training))}</td>
        <td>${esc(clip((r.unique_properties || [])[0] || ''))}</td>
      </tr>`).join('');

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
    renderDossier();
    renderMatrix();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
