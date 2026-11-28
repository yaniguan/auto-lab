/* Unlisted Maintainer Issue Backlog Controller (/audit/) */
(() => {
  'use strict';

  const { esc, fmtMd, initThemeToggle } = window.AutoLabShared;
  const PAGE_SIZE = 20;

  let BY_REPO = {};
  let ALL_ISSUES = [];
  let page = 1;

  async function fetchFreshSiteData() {
    const res = await fetch('../assets/autolab-data.json?v=15');
    if (!res.ok) throw new Error(`Failed loading autolab-data.json (${res.status})`);
    return res.json();
  }

  function filteredIssues() {
    const round = document.getElementById('filter-round')?.value || 'ALL';
    const state = document.getElementById('filter-state')?.value || 'ALL';
    const repo = document.getElementById('filter-repo')?.value || 'ALL';
    const cat = document.getElementById('filter-cat')?.value || 'ALL';
    const sev = document.getElementById('filter-sev')?.value || 'ALL';
    const q = (document.getElementById('filter-search')?.value || '').trim().toLowerCase();

    return ALL_ISSUES.filter(it => {
      if (round !== 'ALL' && String(it.round) !== round) return false;
      if (state !== 'ALL' && String(it.state || 'closed') !== state) return false;
      if (repo !== 'ALL' && it.repo !== repo) return false;
      if (cat !== 'ALL' && it.category !== cat) return false;
      if (sev !== 'ALL') {
        if (sev === 'high') {
          if (it.severity !== 'high' && it.severity !== 'critical') return false;
        } else if (it.severity !== sev) {
          return false;
        }
      }
      if (q) {
        const gpuTag = it.pending_gpu ? 'pending_gpu' : '';
        const hay = `${it.repo} #${it.number || ''} r${it.round} ${it.state || ''} ${gpuTag} ${it.title} ${(it.files || []).join(' ')} ${it.category}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function updateKpis(list) {
    let high = 0, medium = 0, low = 0, closedCnt = 0, openCnt = 0;
    for (const it of list) {
      if (it.severity === 'high' || it.severity === 'critical') high++;
      else if (it.severity === 'low') low++;
      else medium++;
      if (it.state === 'open') openCnt++;
      else closedCnt++;
    }
    document.getElementById('kpi-total').textContent = String(list.length);
    document.getElementById('kpi-high').textContent = String(high);
    document.getElementById('kpi-medium').textContent = String(medium);
    document.getElementById('kpi-low').textContent = String(low);
    const closedEl = document.getElementById('kpi-closed');
    const openEl = document.getElementById('kpi-open');
    if (closedEl) closedEl.textContent = String(closedCnt);
    if (openEl) openEl.textContent = String(openCnt);
  }

  function renderRepoPills() {
    const host = document.getElementById('repo-pill-grid');
    const curRepo = document.getElementById('filter-repo')?.value || 'ALL';
    const curRound = document.getElementById('filter-round')?.value || 'ALL';
    if (!host) return;

    host.innerHTML = Object.entries(BY_REPO).map(([name, info]) => {
      const isSel = curRepo === name;
      const r1 = info.round1_count ?? (info.items || []).filter(x => (x.round || 1) === 1).length;
      const r2 = info.round2_count ?? (info.items || []).filter(x => x.round === 2).length;
      const r3 = info.round3_count ?? (info.items || []).filter(x => x.round === 3).length;
      const openCnt = info.open_count ?? (info.items || []).filter(x => x.state === 'open').length;
      const openTag = openCnt > 0 ? ` · ${openCnt} GPU` : ' · 0 open';
      let countLabel = `${info.count} issues${openTag}`;
      if (curRound === '3') countLabel = `${r3} R3 issues`;
      else if (curRound === '2') countLabel = `${r2} R2 issues`;
      else if (curRound === '1') countLabel = `${r1} R1 issues`;

      return `
        <button type="button" data-pill-repo="${esc(name)}"
          style="text-align:left;padding:9px 12px;border-radius:9px;background:${isSel ? 'var(--accent-soft)' : 'var(--surface)'};border:1px solid ${isSel ? 'var(--accent)' : 'var(--line)'};">
          <strong style="display:block;font-size:12.6px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(name)}</strong>
          <span style="font-size:11.2px;font-weight:700;color:var(--accent);">${esc(countLabel)}</span>
        </button>`;
    }).join('');

    host.querySelectorAll('[data-pill-repo]').forEach(btn => {
      btn.addEventListener('click', () => {
        const sel = document.getElementById('filter-repo');
        const target = btn.dataset.pillRepo;
        sel.value = sel.value === target ? 'ALL' : target;
        page = 1;
        render();
      });
    });
  }

  function populateDynamicCategoryFilter() {
    const catSelect = document.getElementById('filter-cat');
    if (!catSelect) return;
    const prev = catSelect.value || 'ALL';

    const counts = new Map();
    for (const it of ALL_ISSUES) {
      const c = (it.category || 'bug').toLowerCase();
      counts.set(c, (counts.get(c) || 0) + 1);
    }

    const sortedCats = Array.from(counts.entries()).sort((a, b) => {
      if (b[1] !== a[1]) return b[1] - a[1];
      return a[0].localeCompare(b[0]);
    });

    catSelect.innerHTML = '<option value="ALL">All Categories</option>';
    for (const [catName, cnt] of sortedCats) {
      const opt = document.createElement('option');
      opt.value = catName;
      opt.textContent = `${catName} (${cnt})`;
      catSelect.appendChild(opt);
    }
    if (prev !== 'ALL' && counts.has(prev)) {
      catSelect.value = prev;
    }
  }

  function render() {
    renderRepoPills();
    const list = filteredIssues();
    updateKpis(list);

    const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (page > totalPages) page = totalPages;
    if (page < 1) page = 1;

    const start = (page - 1) * PAGE_SIZE;
    const slice = list.slice(start, start + PAGE_SIZE);

    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = slice.map(it => {
      const url = it.url || `https://github.com/yaniguan/${it.repo}/issues`;
      const num = it.number ? `#${it.number}` : 'Open ↗';
      const files = (it.files || []).slice(0, 4).map(f => `<code>${esc(f)}</code>`).join(' ');
      const sevClass = it.severity === 'critical' ? 'high' : it.severity;
      const rnd = Number(it.round || 1);
      const roundBadge = rnd === 3
        ? `<span class="pill pass" title="Round 3 · Wave 1–3 Frontier, Audit Closure & Wire Hardening (${esc(it.state || 'closed')})">R3</span>`
        : rnd === 2
        ? `<span class="pill pass" title="Round 2 · Lean 4, Wire & Attribution (${esc(it.state || 'closed')})">R2</span>`
        : `<span class="pill" style="background:var(--surface2);color:var(--muted);border:1px solid var(--line);" title="Round 1 · Initial Audit (${esc(it.state || 'closed')})">R1</span>`;
      const stateBadge = it.state === 'open'
        ? `<span class="pill hold" title="Awaiting physical multi-GPU / A100 hardware execution">OPEN · GPU</span>`
        : `<span class="pill" style="background:var(--surface2);color:var(--muted);border:1px solid var(--line);">closed</span>`;

      return `
        <tr>
          <td><strong><a class="table-link" href="https://github.com/yaniguan/${encodeURIComponent(it.repo)}/issues" target="_blank" rel="noopener">${esc(it.repo)}</a></strong></td>
          <td><a class="table-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(num)}</a></td>
          <td>${roundBadge}</td>
          <td>${stateBadge}</td>
          <td><span class="pill ${esc(sevClass)}">${esc(it.severity)}</span></td>
          <td><code>${esc(it.category)}</code></td>
          <td>
            <div style="font-weight:620;margin-bottom:3px;">
              <a href="${esc(url)}" target="_blank" rel="noopener">${fmtMd(it.title)}</a>
            </div>
            <div style="font-size:11.8px;color:var(--muted);">${files}</div>
          </td>
        </tr>`;
    }).join('');

    document.getElementById('page-summary').textContent = list.length
      ? `Showing ${start + 1}–${Math.min(start + PAGE_SIZE, list.length)} of ${list.length} issues`
      : 'No matching issues';
    document.getElementById('page-indicator').textContent = `Page ${page} / ${totalPages}`;
    document.getElementById('btn-prev').disabled = page <= 1;
    document.getElementById('btn-next').disabled = page >= totalPages;
  }

  async function init() {
    initThemeToggle();

    const data = await fetchFreshSiteData();
    const issuesMeta = data?.issues || {};
    BY_REPO = issuesMeta.repos || {};

    const repoSelect = document.getElementById('filter-repo');
    const roundSelect = document.getElementById('filter-round');
    const stateSelect = document.getElementById('filter-state');
    let r1Total = 0;
    let r2Total = 0;
    let r3Total = 0;
    let openTotal = 0;
    let closedTotal = 0;

    for (const [repoName, info] of Object.entries(BY_REPO)) {
      const opt = document.createElement('option');
      opt.value = repoName;
      opt.textContent = `${repoName} (${info.count})`;
      repoSelect.appendChild(opt);

      for (const it of info.items || []) {
        const sev = (it.severity || 'medium').toLowerCase();
        const cat = (it.category || 'bug').toLowerCase();
        const rnd = Number(it.round || 1);
        const st = (it.state || 'closed').toLowerCase();
        if (rnd === 3) r3Total++;
        else if (rnd === 2) r2Total++;
        else r1Total++;
        if (st === 'open') openTotal++;
        else closedTotal++;
        ALL_ISSUES.push({ repo: repoName, ...it, round: rnd, state: st, category: cat, severity: sev });
      }
    }

    if (roundSelect) {
      roundSelect.innerHTML = `
        <option value="ALL">All Rounds (${ALL_ISSUES.length})</option>
        <option value="3">Round 3 · Wave 1–3 Frontier &amp; Wire (${r3Total})</option>
        <option value="2">Round 2 · Lean, Wire &amp; Attribution (${r2Total})</option>
        <option value="1">Round 1 · Initial Audit (${r1Total})</option>
      `;
    }
    if (stateSelect) {
      stateSelect.innerHTML = `
        <option value="ALL">All States (${ALL_ISSUES.length})</option>
        <option value="open">Open · PENDING_GPU (${openTotal})</option>
        <option value="closed">Closed (${closedTotal})</option>
      `;
    }

    populateDynamicCategoryFilter();

    const params = new URLSearchParams(location.search);
    const qRepo = params.get('repo');
    if (qRepo && BY_REPO[qRepo]) {
      repoSelect.value = qRepo;
    }
    const qRound = params.get('round');
    if (qRound === '1' || qRound === '2' || qRound === '3') {
      roundSelect.value = qRound;
    }
    const qState = params.get('state');
    if (stateSelect && (qState === 'open' || qState === 'closed')) {
      stateSelect.value = qState;
    }
    const qCat = params.get('cat');
    if (qCat) {
      const catSelect = document.getElementById('filter-cat');
      if (Array.from(catSelect.options).some(o => o.value === qCat.toLowerCase())) {
        catSelect.value = qCat.toLowerCase();
      }
    }

    const onFilter = () => { page = 1; render(); };
    roundSelect.addEventListener('change', onFilter);
    stateSelect?.addEventListener('change', onFilter);
    repoSelect.addEventListener('change', onFilter);
    document.getElementById('filter-cat').addEventListener('change', onFilter);
    document.getElementById('filter-sev').addEventListener('change', onFilter);
    document.getElementById('filter-search').addEventListener('input', onFilter);

    document.getElementById('btn-reset-filters').addEventListener('click', () => {
      roundSelect.value = 'ALL';
      if (stateSelect) stateSelect.value = 'ALL';
      repoSelect.value = 'ALL';
      document.getElementById('filter-cat').value = 'ALL';
      document.getElementById('filter-sev').value = 'ALL';
      document.getElementById('filter-search').value = '';
      history.replaceState(null, '', './');
      onFilter();
    });

    document.getElementById('btn-prev').addEventListener('click', () => { page--; render(); });
    document.getElementById('btn-next').addEventListener('click', () => { page++; render(); });

    render();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
