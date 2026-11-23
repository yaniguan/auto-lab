/* Unlisted Maintainer Issue Backlog Controller (/audit/) */
(() => {
  'use strict';

  const { esc, fmtMd, initThemeToggle, loadData } = window.AutoLabShared;
  const PAGE_SIZE = 20;

  let BY_REPO = {};
  let ALL_ISSUES = [];
  let page = 1;

  function filteredIssues() {
    const repo = document.getElementById('filter-repo')?.value || 'ALL';
    const cat = document.getElementById('filter-cat')?.value || 'ALL';
    const sev = document.getElementById('filter-sev')?.value || 'ALL';
    const q = (document.getElementById('filter-search')?.value || '').trim().toLowerCase();

    return ALL_ISSUES.filter(it => {
      if (repo !== 'ALL' && it.repo !== repo) return false;
      if (cat !== 'ALL' && it.category !== cat) return false;
      if (sev !== 'ALL' && it.severity !== sev) return false;
      if (q) {
        const hay = `${it.repo} ${it.title} ${(it.files || []).join(' ')} ${it.category}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }

  function renderRepoPills() {
    const host = document.getElementById('repo-pill-grid');
    const cur = document.getElementById('filter-repo')?.value || 'ALL';
    if (!host) return;

    host.innerHTML = Object.entries(BY_REPO).map(([name, info]) => {
      const isSel = cur === name;
      return `
        <button type="button" data-pill-repo="${esc(name)}"
          style="text-align:left;padding:9px 12px;border-radius:9px;background:${isSel ? 'var(--accent-soft)' : 'var(--surface)'};border:1px solid ${isSel ? 'var(--accent)' : 'var(--line)'};">
          <strong style="display:block;font-size:12.6px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(name)}</strong>
          <span style="font-size:11.2px;font-weight:700;color:var(--accent);">${esc(info.count)} issues</span>
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

  function render() {
    renderRepoPills();
    const list = filteredIssues();
    const totalPages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (page > totalPages) page = totalPages;
    if (page < 1) page = 1;

    const start = (page - 1) * PAGE_SIZE;
    const slice = list.slice(start, start + PAGE_SIZE);

    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = slice.map(it => {
      const url = it.url || `https://github.com/yaniguan/${it.repo}/issues`;
      const num = it.number ? `#${it.number}` : 'Open ↗';
      const files = (it.files || []).slice(0, 3).map(f => `<code>${esc(f)}</code>`).join(' ');
      return `
        <tr>
          <td><strong><a class="table-link" href="https://github.com/yaniguan/${encodeURIComponent(it.repo)}/issues" target="_blank" rel="noopener">${esc(it.repo)}</a></strong></td>
          <td><a class="table-link" href="${esc(url)}" target="_blank" rel="noopener">${esc(num)}</a></td>
          <td><span class="pill ${esc(it.severity)}">${esc(it.severity)}</span></td>
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

    const data = await loadData('../');
    BY_REPO = data?.issues?.repos || {};
    const repoSelect = document.getElementById('filter-repo');

    let high = 0, medium = 0, low = 0;
    for (const [repoName, info] of Object.entries(BY_REPO)) {
      const opt = document.createElement('option');
      opt.value = repoName;
      opt.textContent = `${repoName} (${info.count})`;
      repoSelect.appendChild(opt);

      for (const it of info.items || []) {
        const sev = (it.severity || 'medium').toLowerCase();
        if (sev === 'high') high++;
        else if (sev === 'low') low++;
        else medium++;
        ALL_ISSUES.push({ repo: repoName, ...it, severity: sev });
      }
    }

    document.getElementById('kpi-total').textContent = String(ALL_ISSUES.length);
    document.getElementById('kpi-high').textContent = String(high);
    document.getElementById('kpi-medium').textContent = String(medium);
    document.getElementById('kpi-low').textContent = String(low);

    const params = new URLSearchParams(location.search);
    const qRepo = params.get('repo');
    if (qRepo && BY_REPO[qRepo]) {
      repoSelect.value = qRepo;
    }

    const onFilter = () => { page = 1; render(); };
    repoSelect.addEventListener('change', onFilter);
    document.getElementById('filter-cat').addEventListener('change', onFilter);
    document.getElementById('filter-sev').addEventListener('change', onFilter);
    document.getElementById('filter-search').addEventListener('input', onFilter);

    document.getElementById('btn-reset-filters').addEventListener('click', () => {
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
