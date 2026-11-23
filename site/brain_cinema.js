/* Interactive 60-Second 7-Layer Brain & Embodied Nervous System Canvas Cinema
 * Renders the multi-layer Auto-Lab cognitive & motor hierarchy (L6 -> L0 + L3 Flywheel)
 * with animated axonal signal pulses, chapter focus highlights, and click-to-inspect.
 */
(() => {
  'use strict';

  const DURATION = 60; // seconds loop
  let playing = true;
  let simTime = 0;
  let lastTs = 0;
  let hoveredRepo = null;

  // Normalized coordinates (0..1) on a 1280 x 664 canvas
  // Left/Center column (x: 0.08 .. 0.67): Cortical-to-Spinal Hierarchy L6 -> L0
  // Right column (x: 0.71 .. 0.96): Lateral Cerebellar/Hippocampal L3 Post-Train Flywheel + Live HUD
  const NODES = [
    // L6 Metacognitive & Epistemic Brain
    { repo: 'lab-ask-why', label: 'lab-ask-why', subEn: 'Socratic Why', subZh: '苏格拉底追问', layer: 'L6', x: 0.21, y: 0.14, col: 'purple' },
    { repo: 'lab-decide', label: 'lab-decide', subEn: 'Conformal Trust', subZh: '共形可信域', layer: 'L6', x: 0.41, y: 0.14, col: 'purple' },
    { repo: 'YLM', label: 'YLM ★', subEn: '3D + Language Brain', subZh: '三维分子语言脑', layer: 'L6', x: 0.59, y: 0.14, col: 'purple', companion: true },

    // L5 Executive Planning, Procurement & Scheduling
    { repo: 'buy-or-make', label: 'buy-or-make', subEn: 'Stock vs N-Step', subZh: '采购/合成权衡', layer: 'L5', x: 0.20, y: 0.29, col: 'blue' },
    { repo: 'labshift', label: 'labshift', subEn: 'CP-SAT Fleet', subZh: '多仪器排程', layer: 'L5', x: 0.40, y: 0.29, col: 'blue' },
    { repo: 'lab-automation-atlas', label: 'automation-atlas', subEn: 'Platform Map', subZh: '自动化生态图谱', layer: 'L5', x: 0.59, y: 0.29, col: 'blue' },

    // L4 Digital-Twin Rehearsal & Default-Deny Gate
    { repo: 'lab-rehearsal', label: 'lab-rehearsal', subEn: 'Recall & Twin', subZh: '记忆与数字孪生', layer: 'L4', x: 0.21, y: 0.45, col: 'teal' },
    { repo: 'lab-verify', label: 'lab-verify', subEn: 'Default-Deny Gate', subZh: '默认拒绝校验门', layer: 'L4', x: 0.41, y: 0.45, col: 'teal' },
    { repo: 'WignerFlow', label: 'WignerFlow ★', subEn: '50-fs [physics] Gate', subZh: '50fs 等变物理门', layer: 'L4', x: 0.59, y: 0.45, col: 'teal', companion: true },

    // L2 Sensory & Protocol Cortex
    { repo: 'lab-ears', label: 'lab-ears', subEn: 'WLP + Acoustic', subZh: '协议与声学听觉', layer: 'L2', x: 0.22, y: 0.61, col: 'blue' },
    { repo: 'ouroboros-ocsr', label: 'ouroboros ★', subEn: 'SE(2) Chem Eyes', subZh: '等变化学视觉', layer: 'L2', x: 0.41, y: 0.61, col: 'blue', companion: true },
    { repo: 'assayfold', label: 'assayfold ★', subEn: 'Unified Ledger', subZh: '开放数据账本', layer: 'L2', x: 0.59, y: 0.61, col: 'blue', companion: true },

    // L1 Motor Compiler & Tactile Hands
    { repo: 'stepbot', label: 'stepbot', subEn: 'Opentrons v2', subZh: '移液协议编译器', layer: 'L1', x: 0.27, y: 0.76, col: 'teal' },
    { repo: 'lab-hands', label: 'lab-hands', subEn: 'RRT + Last-cm Touch', subZh: '避障机械臂与触觉', layer: 'L1', x: 0.50, y: 0.76, col: 'teal' },

    // L0 Edge Body Runtime
    { repo: 'lab-feet', label: 'lab-feet', subEn: 'Distill + INT8 / 4-bit Edge', subZh: '知识蒸馏与 INT8/4-bit 边缘推理', layer: 'L0', x: 0.385, y: 0.90, col: 'purple' },

    // L3 Lateral Post-Training RLVR Flywheel
    { repo: 'twinstep', label: 'twinstep', subEn: 'Seeded Error Twins', subZh: '确定性错误孪生', layer: 'L3', x: 0.82, y: 0.73, col: 'amber' },
    { repo: 'labfill', label: 'labfill', subEn: '5.42× Packed BF16', subZh: '张量化校验与打包', layer: 'L3', x: 0.82, y: 0.53, col: 'amber' },
    { repo: 'labbench-posttrain', label: 'labbench-posttrain', subEn: 'labrl SFT→MPO→GDPO', subZh: '可验证强化学习底座', layer: 'L3', x: 0.82, y: 0.31, col: 'amber' },
  ];

  // Directed axonal & flywheel pathways [fromRepo, toRepo, group]
  const EDGES = [
    ['lab-ears', 'lab-ask-why', 'sensory'],
    ['ouroboros-ocsr', 'YLM', 'sensory'],
    ['assayfold', 'labbench-posttrain', 'flywheel'],
    ['YLM', 'lab-ask-why', 'brain'],
    ['lab-ask-why', 'lab-decide', 'brain'],
    ['lab-decide', 'buy-or-make', 'exec'],
    ['buy-or-make', 'labshift', 'exec'],
    ['lab-automation-atlas', 'labshift', 'exec'],
    ['labshift', 'lab-rehearsal', 'gate'],
    ['WignerFlow', 'lab-rehearsal', 'gate'],
    ['lab-rehearsal', 'lab-verify', 'gate'],
    ['lab-verify', 'stepbot', 'motor'],
    ['lab-verify', 'lab-hands', 'motor'],
    ['stepbot', 'lab-feet', 'motor'],
    ['lab-hands', 'lab-feet', 'motor'],
    ['lab-rehearsal', 'twinstep', 'flywheel'],
    ['lab-feet', 'twinstep', 'flywheel'],
    ['twinstep', 'labfill', 'flywheel'],
    ['labfill', 'labbench-posttrain', 'flywheel'],
    ['labbench-posttrain', 'lab-decide', 'flywheel'],
    ['labbench-posttrain', 'lab-feet', 'flywheel'],
  ];

  const CHAPTERS = [
    {
      t0: 0, t1: 10, layers: ['L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'L0'],
      titleEn: 'Full 7-Layer Brain, Safety Gate & Post-Training Organism',
      titleZh: '全栈七层具身科研大脑、默认拒绝安全门与后训练闭环',
      noteEn: 'Sensory inputs ascend to the calibrated Brain (L6), descend through Executive & Twin Gates (L5–L4) to Motor/Edge (L1–L0), and replay via L3.',
      noteZh: '多模态感知上行至元认知与共形决策脑 (L6)，经采购排程与数字孪生安全门 (L5–L4) 驱动移液/机械臂与边缘板 (L1–L0)，再经 L3 强化学习回写进化。',
    },
    {
      t0: 10, t1: 20, layers: ['L6'],
      titleEn: 'L6 Brain · Socratic Rationale & Conformal Abstention',
      titleZh: 'L6 大脑层 · 苏格拉底证据追问与共形预测可信域弃权',
      noteEn: 'lab-ask-why retrieves SUPPORT/CONTRADICT evidence (0.79 recall@3); lab-decide answers only inside its calibrated kNN trust region (92.2% cov).',
      noteZh: 'lab-ask-why 检索正反文献证据并提出鉴别实验；lab-decide 仅在 kNN 校准可信域内输出 90% 置信区间，域外诚实拒答。',
    },
    {
      t0: 20, t1: 30, layers: ['L5'],
      titleEn: 'L5 Executive · Make-vs-Buy Triage & CP-SAT Fleet Scheduling',
      titleZh: 'L5 执行规划层 · 实价采购/逆合成评估与 CP-SAT 多仪器排程',
      noteEn: 'buy-or-make enforces listed-catalog lower bounds (null if unlisted); labshift eliminates all 13 greedy max_wait violations across 30 benchmarks.',
      noteZh: 'buy-or-make 基于真实目录价计算成本下界（缺失严格记 null）；labshift 用 CP-SAT 在 30 个基准上实现 100% 时间窗可行调度。',
    },
    {
      t0: 30, t1: 40, layers: ['L4'],
      titleEn: 'L4 Inhibitory Gate · Episodic Recall, Twin Dry-Run & Default-Deny',
      titleZh: 'L4 安全抑制门 · 历史事故召回、数字孪生预演与四层默认拒绝校验',
      noteEn: 'lab-rehearsal blocks overfill/empty-aspirate/tip-reuse in a 96-well twin; lab-verify stops 7/14 semantic SQL errors that syntax/schema checks miss.',
      noteZh: 'lab-rehearsal 在虚拟 96 孔板拦截空吸/溢出/枪头交叉污染；lab-verify 用执行级比对拦截仅靠语法检查漏掉的 50% 语义错误。',
    },
    {
      t0: 40, t1: 50, layers: ['L2', 'L1', 'L0'],
      titleEn: 'L2–L0 Embodied Stack · Protocol Ears, Opentrons Compiler, Hands & Feet',
      titleZh: 'L2–L0 具身躯干 · 协议/异响听觉、Opentrons 编译、触觉机械臂与量化推理',
      noteEn: 'lab-ears parses WLP & machine log-mel (speech dropped); stepbot emits apiLevel 2.16 code; lab-hands shortcuts RRT paths; lab-feet quantizes to 4-bit.',
      noteZh: 'lab-ears 提取实验参数并脱敏监测异响；stepbot 编译确定性协议；lab-hands 规划 100% 避障轨迹；lab-feet 实现 35× 参数压缩边缘运行。',
    },
    {
      t0: 50, t1: 60, layers: ['L3'],
      titleEn: 'L3 Plasticity Flywheel · Error Twins, 5.42× Packed BF16 & labrl RLVR',
      titleZh: 'L3 突触可塑性飞轮 · 错误孪生课程、5.42× 序列打包与 labrl 可验证后训练',
      noteEn: 'twinstep injects 6 failure types -> labfill packs to 92.1% useful tokens -> labbench-posttrain runs SFT/MPO/TROPD/GDPO+DAPO with SplitGuard.',
      noteZh: 'twinstep 生成 6 类受控错误孪生对 → labfill 将有效 token 率提至 92.1% → labbench-posttrain 执行防作弊 SFT→MPO→GDPO 全链路后训练。',
    },
  ];

  const LAYER_BANDS = [
    { code: 'L6', y: 0.14, labelEn: 'L6 · BRAIN', labelZh: 'L6 · 元认知大脑' },
    { code: 'L5', y: 0.29, labelEn: 'L5 · EXECUTIVE', labelZh: 'L5 · 规划与排程' },
    { code: 'L4', y: 0.45, labelEn: 'L4 · TWIN & GATE', labelZh: 'L4 · 预演与安全门' },
    { code: 'L2', y: 0.61, labelEn: 'L2 · SENSORY', labelZh: 'L2 · 多模态感知' },
    { code: 'L1', y: 0.76, labelEn: 'L1 · MOTOR & TOUCH', labelZh: 'L1 · 编译与灵巧手' },
    { code: 'L0', y: 0.90, labelEn: 'L0 · EDGE FEET', labelZh: 'L0 · 边缘算力脚' },
  ];

  function nodeMap() {
    const m = {};
    NODES.forEach(n => { m[n.repo] = n; });
    return m;
  }
  const BY_REPO = nodeMap();

  function getLang() {
    return document.documentElement.dataset.lang === 'zh' ? 'zh' : 'en';
  }

  function currentChapter() {
    const t = simTime % DURATION;
    return CHAPTERS.find(c => t >= c.t0 && t < c.t1) || CHAPTERS[0];
  }

  function colorFor(P, key) {
    if (key === 'purple') return P.purple;
    if (key === 'blue') return P.blue;
    if (key === 'amber') return P.amber;
    return P.accent;
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function draw() {
    const canvas = document.getElementById('brain-cinema-canvas');
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const rect = canvas.getBoundingClientRect();
    const W = Math.max(640, Math.round(rect.width));
    const H = Math.max(330, Math.round(rect.height));
    if (canvas.width !== W * dpr || canvas.height !== H * dpr) {
      canvas.width = W * dpr;
      canvas.height = H * dpr;
    }
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.scale(dpr, dpr);

    const dark = document.documentElement.dataset.theme === 'dark';
    const lang = getLang();
    const P = window.AutoLabCharts.getPalette();
    const chap = currentChapter();
    const activeSet = new Set(chap.layers);

    ctx.fillStyle = dark ? '#090f16' : '#f1f5fb';
    ctx.fillRect(0, 0, W, H);

    // Subtle background dot grid
    ctx.fillStyle = dark ? 'rgba(148,163,184,0.09)' : 'rgba(15,23,42,0.06)';
    for (let gx = 24; gx < W; gx += 28) {
      for (let gy = 20; gy < H; gy += 28) {
        ctx.fillRect(gx, gy, 1.5, 1.5);
      }
    }

    // Draw horizontal cortical-to-spinal layer bands on left (x: 0.02..0.685)
    const leftX = W * 0.022;
    const leftW = W * 0.665;
    const bandH = H * 0.118;
    LAYER_BANDS.forEach(b => {
      const by = b.y * H - bandH / 2;
      const isHi = activeSet.has(b.code);
      roundRect(ctx, leftX, by, leftW, bandH, 10);
      ctx.fillStyle = isHi
        ? (dark ? 'rgba(30, 46, 66, 0.72)' : 'rgba(255, 255, 255, 0.88)')
        : (dark ? 'rgba(17, 27, 39, 0.45)' : 'rgba(255, 255, 255, 0.48)');
      ctx.fill();
      ctx.strokeStyle = isHi ? P.accent : P.grid;
      ctx.lineWidth = isHi ? 1.5 : 1;
      ctx.stroke();

      ctx.fillStyle = isHi ? P.accent : P.muted;
      ctx.font = '700 10.5px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(lang === 'zh' ? b.labelZh : b.labelEn, leftX + 10, by + 16);
    });

    // Draw Right Lateral L3 Post-Training Flywheel Enclosure
    const fwX = W * 0.705;
    const fwY = H * 0.19;
    const fwW = W * 0.27;
    const fwH = H * 0.65;
    const l3Hi = activeSet.has('L3');
    roundRect(ctx, fwX, fwY, fwW, fwH, 13);
    ctx.fillStyle = l3Hi
      ? (dark ? 'rgba(251, 191, 36, 0.09)' : 'rgba(255, 251, 235, 0.92)')
      : (dark ? 'rgba(17, 27, 39, 0.55)' : 'rgba(255, 255, 255, 0.66)');
    ctx.fill();
    ctx.strokeStyle = l3Hi ? P.amber : P.grid;
    ctx.setLineDash([5, 4]);
    ctx.lineWidth = l3Hi ? 1.8 : 1.1;
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = P.amber;
    ctx.font = '700 11px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      lang === 'zh' ? 'L3 · 后训练与错误孪生飞轮' : 'L3 · RLVR POST-TRAIN FLYWHEEL',
      fwX + fwW / 2,
      fwY + 20
    );

    // Draw edges + animated synaptic pulses
    EDGES.forEach(([uName, vName, grp], idx) => {
      const u = BY_REPO[uName];
      const v = BY_REPO[vName];
      if (!u || !v) return;
      const x1 = u.x * W, y1 = u.y * H;
      const x2 = v.x * W, y2 = v.y * H;
      const cx = (x1 + x2) / 2 + (grp === 'flywheel' ? 18 : 0);
      const cy = (y1 + y2) / 2;

      const edgeActive = activeSet.has(u.layer) || activeSet.has(v.layer);
      const col = grp === 'flywheel' ? P.amber : grp === 'brain' ? P.purple : P.accent;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.quadraticCurveTo(cx, cy, x2, y2);
      ctx.strokeStyle = edgeActive ? col : P.grid;
      ctx.globalAlpha = edgeActive ? 0.52 : 0.22;
      ctx.lineWidth = edgeActive ? 1.7 : 1.1;
      ctx.stroke();
      ctx.globalAlpha = 1;

      if (edgeActive) {
        const phase = ((simTime * 0.52 + idx * 0.19) % 1 + 1) % 1;
        const mt = 1 - phase;
        const px = mt * mt * x1 + 2 * mt * phase * cx + phase * phase * x2;
        const py = mt * mt * y1 + 2 * mt * phase * cy + phase * phase * y2;
        ctx.beginPath();
        ctx.arc(px, py, 3.3, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
      }
    });

    // Draw nodes
    const nodeW = Math.min(142, W * 0.132);
    const nodeH = Math.min(44, H * 0.076);
    NODES.forEach(n => {
      const nx = n.x * W - nodeW / 2;
      const ny = n.y * H - nodeH / 2;
      const isHi = activeSet.has(n.layer) || hoveredRepo === n.repo;
      const col = colorFor(P, n.col);

      roundRect(ctx, nx, ny, nodeW, nodeH, 8);
      ctx.fillStyle = dark ? '#132030' : '#ffffff';
      ctx.globalAlpha = isHi ? 1 : 0.52;
      ctx.fill();
      ctx.lineWidth = hoveredRepo === n.repo ? 2.4 : isHi ? 1.7 : 1;
      ctx.strokeStyle = isHi ? col : P.grid;
      if (n.companion) ctx.setLineDash([4, 3]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Layer pill dot
      ctx.beginPath();
      ctx.arc(nx + 10, ny + 14, 3.4, 0, Math.PI * 2);
      ctx.fillStyle = col;
      ctx.fill();

      ctx.fillStyle = P.text;
      ctx.font = '700 11.2px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(n.label, nx + 18, ny + 17.5);

      ctx.fillStyle = P.muted;
      ctx.font = '500 10px Inter, sans-serif';
      ctx.fillText(lang === 'zh' ? n.subZh : n.subEn, nx + 10, ny + 33);
      ctx.globalAlpha = 1;
    });

    // Top-right HUD Caption Banner inside Flywheel column top & bottom
    const hudX = W * 0.705;
    const hudW = W * 0.27;
    roundRect(ctx, hudX, H * 0.035, hudW, H * 0.13, 10);
    ctx.fillStyle = dark ? 'rgba(17, 27, 39, 0.92)' : 'rgba(255, 255, 255, 0.94)';
    ctx.fill();
    ctx.strokeStyle = P.accent;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    ctx.fillStyle = P.accent;
    ctx.font = '700 10.5px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(lang === 'zh' ? chap.titleZh.slice(0, 22) : chap.titleEn.slice(0, 38), hudX + 12, H * 0.072);

    ctx.fillStyle = P.muted;
    ctx.font = '500 10.2px Inter, sans-serif';
    const desc = lang === 'zh' ? chap.noteZh : chap.noteEn;
    wrapCanvasText(ctx, desc, hudX + 12, H * 0.102, hudW - 22, 13.5, 3);

    // Bottom-right Legend note
    ctx.fillStyle = P.muted;
    ctx.font = '600 10.5px Inter, sans-serif';
    ctx.fillText(
      lang === 'zh' ? '★ 关联核心器官 · 点击任意节点查看详情' : '★ Companion organ · Click any node to inspect',
      hudX + 6,
      H * 0.915
    );

    ctx.restore();
    syncChapterUI();
  }

  function wrapCanvasText(ctx, text, x, y, maxWidth, lineH, maxLines) {
    const isZh = /[\u4e00-\u9fa5]/.test(text);
    const tokens = isZh ? Array.from(text) : text.split(' ');
    let line = '';
    let row = 0;
    for (let i = 0; i < tokens.length; i++) {
      const sep = isZh ? '' : (line ? ' ' : '');
      const test = line + sep + tokens[i];
      if (ctx.measureText(test).width > maxWidth && line) {
        ctx.fillText(line, x, y + row * lineH);
        line = tokens[i];
        row++;
        if (row >= maxLines - 1) break;
      } else {
        line = test;
      }
    }
    if (line && row < maxLines) ctx.fillText(line, x, y + row * lineH);
  }

  function syncChapterUI() {
    const t = Math.floor(simTime % DURATION);
    const lbl = document.getElementById('cinema-time');
    if (lbl) lbl.textContent = `00:${String(t).padStart(2, '0')} / 01:00`;
    const chap = currentChapter();
    document.querySelectorAll('[data-cinema-seek]').forEach(btn => {
      const s = Number(btn.dataset.cinemaSeek);
      btn.classList.toggle('active', s === chap.t0);
    });
  }

  function hitTest(ev) {
    const canvas = document.getElementById('brain-cinema-canvas');
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const mx = (ev.clientX - rect.left) / rect.width;
    const my = (ev.clientY - rect.top) / rect.height;
    for (const n of NODES) {
      if (Math.abs(mx - n.x) < 0.072 && Math.abs(my - n.y) < 0.042) {
        return n;
      }
    }
    return null;
  }

  function tick(ts) {
    if (!lastTs) lastTs = ts;
    const dt = Math.min(0.1, (ts - lastTs) / 1000);
    lastTs = ts;
    if (playing) simTime = (simTime + dt) % DURATION;
    draw();
    requestAnimationFrame(tick);
  }

  function init() {
    const canvas = document.getElementById('brain-cinema-canvas');
    if (!canvas) return;

    canvas.addEventListener('mousemove', ev => {
      const hit = hitTest(ev);
      hoveredRepo = hit ? hit.repo : null;
    });
    canvas.addEventListener('mouseleave', () => { hoveredRepo = null; });
    canvas.addEventListener('click', ev => {
      const hit = hitTest(ev);
      if (hit && window.AutoLabApp && window.AutoLabApp.selectOrgan) {
        window.AutoLabApp.selectOrgan(hit.repo, true);
      }
    });

    const playBtn = document.getElementById('cinema-play-toggle');
    if (playBtn) {
      playBtn.addEventListener('click', () => {
        playing = !playing;
        playBtn.textContent = playing ? '❚❚ Pause' : '▶ Play';
      });
    }

    document.querySelectorAll('[data-cinema-seek]').forEach(btn => {
      btn.addEventListener('click', () => {
        simTime = Number(btn.dataset.cinemaSeek) + 0.05;
        draw();
      });
    });

    requestAnimationFrame(tick);
  }

  window.AutoLabCinema = { init, redraw: draw };
})();
