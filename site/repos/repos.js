/* 14-Repository Interactive Story Cards Controller (/repos/) */
(() => {
  'use strict';

  const { esc, initThemeToggle, loadData } = window.AutoLabShared;
  const { iconMarkup, neighborsOf } = window.AutoLabIcons;
  const { STORIES } = window.AutoLabStories;
  const LAYER_ORDER = ['L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'L0'];

  let DATA = null;
  let activeRepo = 'labbench-posttrain';
  let activeDemoIdx = 0;
  let activeDepthTab = 'how';
  let viewMode = 'detail';

  function fmtInline(text) {
    return esc(text || '').replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  function orderedRepos() {
    if (!DATA) return [];
    return [...(DATA.repos || [])].sort(
      (a, b) => LAYER_ORDER.indexOf(a.layer) - LAYER_ORDER.indexOf(b.layer)
    );
  }

  function selectRepo(repoName, updateHash = true) {
    const exists = (DATA?.repos || []).some(r => r.repo === repoName);
    if (!exists) return;
    if (activeRepo !== repoName) {
      activeRepo = repoName;
      activeDemoIdx = 0;
    }
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
        const story = STORIES[r.repo] || {};
        return (
          r.repo.toLowerCase().includes(q) ||
          JSON.stringify(story).toLowerCase().includes(q) ||
          (r.tagline || '').toLowerCase().includes(q)
        );
      });
      if (!items.length) return '';
      return `
        <div class="sidebar-group">
          <div class="sidebar-group-label">${esc(code)} · ${esc(layer ? layer.name.split(',')[0] : '')}</div>
          ${items.map(r => `
            <button type="button" class="sidebar-item ${activeRepo === r.repo ? 'active' : ''}" data-repo="${esc(r.repo)}" style="justify-content:flex-start;gap:8px;">
              ${iconMarkup(r.repo, 16)}
              <span>${esc(r.repo)}</span>
            </button>`).join('')}
        </div>`;
    }).join('');

    host.innerHTML = groupsHtml || '<p style="padding:8px;font-size:12.5px;color:var(--muted);">No matching repository.</p>';
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
    const fl = c.flow || ['Inputs', r.repo, 'Outputs'];
    const story = STORIES[r.repo] || {
      headline: c.hook || r.tagline,
      why: r.object,
      metrics: c.kpis || [],
      playgroundPrompt: 'Inspect example:',
      demos: [],
      tabs: { how: r.model, guarantee: (r.unique_properties || [])[0] || '', status: r.history },
    };

    const demos = story.demos || [];
    const safeDemoIdx = Math.min(activeDemoIdx, Math.max(0, demos.length - 1));
    const demo = demos[safeDemoIdx] || null;

    const metricsHtml = (story.metrics || []).length
      ? `<div class="story-metrics">
          ${story.metrics.map(([val, lbl]) => `
            <div class="story-metric-cell">
              <strong>${esc(val)}</strong>
              <span>${esc(lbl)}</span>
            </div>`).join('')}
        </div>`
      : '';

    const playgroundHtml = demo
      ? `<section class="story-playground" aria-label="Interactive example">
          <div class="playground-head">
            <div class="playground-kicker">
              <span><strong style="color:var(--accent);">Try an Example</strong> · ${esc(story.playgroundPrompt)}</span>
              <span class="pill ${esc(demo.verdictTone || 'pass')}">${esc(demo.verdict)}</span>
            </div>
            <div class="demo-tabs" role="tablist">
              ${demos.map((d, i) => `
                <button type="button" role="tab" aria-selected="${i === safeDemoIdx}"
                        class="demo-tab-btn ${i === safeDemoIdx ? 'active' : ''}" data-demo-idx="${i}">
                  ${esc(d.tab)}
                </button>`).join('')}
            </div>
          </div>
          <div class="playground-body">
            <div class="io-block">
              <div class="io-bar">
                <span>Input · ${esc(demo.inputLabel)}</span>
              </div>
              <pre class="io-pre">${esc(demo.input)}</pre>
            </div>
            <div class="io-block">
              <div class="io-bar">
                <span>Output · ${esc(demo.outputLabel)}</span>
              </div>
              <pre class="io-pre">${esc(demo.output)}</pre>
            </div>
          </div>
        </section>`
      : '';

    let depthBodyHtml = '';
    if (activeDepthTab === 'how') {
      depthBodyHtml = `
        <div class="flow-strip">
          <div class="flow-node"><small>Takes In</small>${esc(fl[0])}</div>
          <span class="flow-arrow">→</span>
          <div class="flow-node"><small>Core Mechanism</small>${esc(fl[1])}</div>
          <span class="flow-arrow">→</span>
          <div class="flow-node"><small>Produces</small>${esc(fl[2])}</div>
        </div>
        <p>${fmtInline(story.tabs.how)}</p>`;
    } else if (activeDepthTab === 'guarantee') {
      depthBodyHtml = `<p>${fmtInline(story.tabs.guarantee)}</p>`;
    } else {
      depthBodyHtml = `
        <p>${fmtInline(story.tabs.status)}</p>
        <div>
          <a class="table-link" href="${esc(r.url)}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md" target="_blank" rel="noopener">
            Read full ARCHITECTURE_AND_HISTORY.md on GitHub ↗
          </a>
        </div>`;
    }

    const { upstream, downstream } = neighborsOf(r.repo);
    const coreSet = new Set((DATA.repos || []).map(x => x.repo));
    const renderConnPill = item => coreSet.has(item.repo)
      ? `<button type="button" class="conn-chip" data-nav-repo="${esc(item.repo)}">${iconMarkup(item.repo, 14)} <span>${esc(item.repo)}</span> <small>(${esc(item.label)})</small></button>`
      : `<a class="conn-chip" href="https://github.com/yaniguan/${encodeURIComponent(item.repo)}" target="_blank" rel="noopener">${iconMarkup(item.repo, 14)} <span>${esc(item.repo)} ★</span> <small>(${esc(item.label)})</small></a>`;

    const connHtml = `
      <div class="conn-bar" style="margin:18px 0 6px;padding:12px 14px;background:var(--surface2);border:1px solid var(--line);border-radius:10px;">
        <strong style="font-size:10.5px;text-transform:uppercase;letter-spacing:0.8px;color:var(--muted);">Where It Connects:</strong>
        ${upstream.length ? upstream.map(renderConnPill).join('') : '<span style="color:var(--muted);">Raw input</span>'}
        <span class="step-sep">→</span>
        <span class="conn-chip current">${iconMarkup(r.repo, 14)} ${esc(r.repo)}</span>
        <span class="step-sep">→</span>
        ${downstream.length ? downstream.map(renderConnPill).join('') : '<span style="color:var(--muted);">Bench / output</span>'}
      </div>`;

    host.innerHTML = `
      <div class="dossier-header" style="margin-bottom:14px;padding-bottom:16px;">
        <div style="min-width:0;flex:1;">
          <span class="small-label ${colClass}">${esc(r.layer)} · ${esc(r.layer_name)}</span>
          <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
            <span style="color:var(--accent);display:inline-flex;">${iconMarkup(r.repo, 28)}</span>
            <h2 style="margin:0;">${esc(r.repo)}</h2>
          </div>
          <p class="story-headline">${fmtInline(story.headline)}</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="${esc(r.url)}" target="_blank" rel="noopener">GitHub ↗</a>
          <a class="button secondary" href="${esc(r.url)}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md" target="_blank" rel="noopener">Architecture Doc ↗</a>
        </div>
      </div>

      <div class="story-why-callout">
        <span class="story-why-label">Why a wet lab needs this</span>
        <p>${fmtInline(story.why)}</p>
      </div>

      ${metricsHtml}

      ${playgroundHtml}

      <section class="depth-card" aria-label="Engineering details">
        <div class="depth-tabs" role="tablist">
          <button type="button" role="tab" aria-selected="${activeDepthTab === 'how'}"
                  class="depth-tab-btn ${activeDepthTab === 'how' ? 'active' : ''}" data-depth="how">
            How It Works &amp; Data
          </button>
          <button type="button" role="tab" aria-selected="${activeDepthTab === 'guarantee'}"
                  class="depth-tab-btn ${activeDepthTab === 'guarantee' ? 'active' : ''}" data-depth="guarantee">
            Guarantee &amp; Scope
          </button>
          <button type="button" role="tab" aria-selected="${activeDepthTab === 'status'}"
                  class="depth-tab-btn ${activeDepthTab === 'status' ? 'active' : ''}" data-depth="status">
            Status &amp; Next Steps
          </button>
        </div>
        <div class="depth-panel">
          ${depthBodyHtml}
        </div>
      </section>

      ${connHtml}

      <div style="display:flex;justify-content:space-between;align-items:center;margin-top:22px;padding-top:16px;border-top:1px solid var(--line);gap:12px;flex-wrap:wrap;">
        ${prev ? `<button type="button" class="button secondary" data-nav-repo="${esc(prev.repo)}">← ${esc(prev.repo)}</button>` : '<span></span>'}
        ${next ? `<button type="button" class="button secondary" data-nav-repo="${esc(next.repo)}">${esc(next.repo)} →</button>` : '<span></span>'}
      </div>`;

    host.querySelectorAll('[data-demo-idx]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeDemoIdx = Number(btn.dataset.demoIdx) || 0;
        renderCard();
      });
    });

    host.querySelectorAll('[data-depth]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeDepthTab = btn.dataset.depth || 'how';
        renderCard();
      });
    });

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
      const colClass = r.layer === 'L6' || r.layer === 'L0' ? 'purple' : r.layer === 'L5' || r.layer === 'L2' ? 'blue' : r.layer === 'L3' ? 'amber' : 'teal';
      const story = STORIES[r.repo] || {};
      const fl = (r.concise && r.concise.flow) || ['Inputs', r.repo, 'Outputs'];
      const m0 = (story.metrics && story.metrics[0]) ? `${story.metrics[0][0]} ${story.metrics[0][1]}` : '-';
      return `
        <tr>
          <td><span class="layer-code-pill ${colClass}">${esc(r.layer)}</span></td>
          <td style="white-space:nowrap;">
            <button type="button" class="table-link" style="background:none;border:0;padding:0;display:inline-flex;align-items:center;gap:6px;" data-jump-detail="${esc(r.repo)}">
              ${iconMarkup(r.repo, 16)} <strong>${esc(r.repo)}</strong>
            </button>
          </td>
          <td>${fmtInline(story.headline || r.tagline)}</td>
          <td style="color:var(--muted);font-size:12.4px;">${esc(fl[0])} → ${esc(fl[1])} → ${esc(fl[2])}</td>
          <td style="white-space:nowrap;"><code>${esc(m0)}</code></td>
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
