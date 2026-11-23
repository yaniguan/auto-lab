/* Interactive Lean 4 Trust Regime & Empirical Lift Explorer (/trust/) */
(() => {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const { esc, initThemeToggle } = window.AutoLabShared;
  const { iconMarkup } = window.AutoLabIcons;

  const LEAN_SPECS = [
    {
      layer: 'L6', repo: 'lab-ask-why', file: 'AutoLabLean/L6_Epistemic.lean',
      theorem: 'contested_claim_requires_experiment',
      boundary: 'Never crown one hypothesis when opposing papers disagree without naming a falsifiable discriminating experiment; abstain (`NOINFO`) when retrieval support falls below threshold.',
      allowCase: ['askWhy { score=789 >= 350, support=2, contradict=1, hasDiscriminatingExperiment=true }', 'ALLOW · Symmetric evidence paired with falsifiable check'],
      denyCase: ['askWhy { score=789, support=2, contradict=1, hasDiscriminatingExperiment=false }', 'DENY  [lab-ask-why :: contested_requires_experiment]'],
      code: `structure EpistemicProbeOK (p : EpistemicProbe) : Prop where
  enoughEvidence    : p.noinfoThreshPermille ≤ p.topScorePermille
  nonEmptyRationale : 0 < p.supportHits + p.contradictHits
  contestedResolved : (0 < p.supportHits ∧ 0 < p.contradictHits) →
                        p.hasDiscriminatingExperiment = true

theorem contested_claim_requires_experiment (p : EpistemicProbe)
    (hok : checkAskWhy p = none)
    (hsup : 0 < p.supportHits) (hcon : 0 < p.contradictHits) :
    p.hasDiscriminatingExperiment = true`,
    },
    {
      layer: 'L6', repo: 'lab-decide', file: 'AutoLabLean/L6_Epistemic.lean',
      theorem: 'out_of_domain_always_abstains & undersized_calib_always_abstains',
      boundary: 'Never extrapolate outside the calibrated 5-NN distance threshold (`knnDist <= tauDist`), and never clamp finite-sample conformal rank `ceil((n+1)*(1-alpha))` when `k > n`.',
      allowCase: ['decide { nCalib=180, alpha=100, knnDist=410 <= 758, interval=[-2.41, +0.63] }', 'ALLOW · Certified 90% conformal interval inside trust support'],
      denyCase: ['decide { nCalib=180, alpha=100, knnDist=1380 > 758 (out-of-domain macrocycle) }', 'DENY  [lab-decide :: knn_trust_boundary] -> ABSTAIN'],
      code: `def conformalRank (n alphaPermille : Nat) : Nat :=
  ((n + 1) * (1000 - alphaPermille) + 999) / 1000

theorem out_of_domain_always_abstains (q : ConformalQuery)
    (hood : q.tauDistPermille < q.knnDistPermille) :
    checkDecide q ≠ none

theorem undersized_calib_always_abstains (q : ConformalQuery)
    (hsmall : q.nCalib < conformalRank q.nCalib q.alphaPermille) :
    checkDecide q ≠ none`,
    },
    {
      layer: 'L5', repo: 'buy-or-make', file: 'AutoLabLean/L5_Executive.lean',
      theorem: 'ring_cleavage_rejected & unpriced_never_passes_budget',
      boundary: 'Retrosynthetic disconnections must cleave acyclic bonds (`!@`) and conserve exact heavy-atom counts; unpriced (`null`), partial-leaf, or non-`USD/g` quotes never pass a numeric budget gate.',
      allowCase: ['procurement { steps=1, bondIsAcyclic=true, target=(12,3,1)+delta(0,0,0,1) == reactants, price=$14.50/g <= $25/g }', 'ALLOW · Atom-balanced acyclic route with complete USD/g leaf pricing'],
      denyCase: ['procurement { Analog-6 lactam cleavage: bondIsAcyclic=false, C12 -> C3 + C10 (13 carbons!) }', 'DENY  [buy-or-make :: acyclic_atom_balanced_route]'],
      code: `def routeStoichiometryOK (p : MakeOrBuyProposal) : Bool :=
  if p.isDirectBuy then p.steps == 0
  else decide (1 ≤ p.steps ∧ p.steps ≤ p.maxSteps) &&
       p.bondIsAcyclic && p.allLeavesInStock &&
       decide (sumAtoms p.reactantAtoms = AtomVec.add p.targetAtoms p.leavingDelta)

theorem ring_cleavage_rejected (p : MakeOrBuyProposal)
    (hmake : p.isDirectBuy = false) (hring : p.bondIsAcyclic = false) :
    checkBuyOrMake p ≠ none`,
    },
    {
      layer: 'L5', repo: 'labshift', file: 'AutoLabLean/L5_Executive.lean',
      theorem: 'checkSchedule_ok_iff & missed_incubation_window_rejected',
      boundary: 'Every scheduled operation must respect pool capacity, pairwise machine mutual exclusion, release/deadline bounds, and `[min_wait, max_wait]` post-incubation handoff windows.',
      allowCase: ['CP-SAT schedule: L[0..18] -> I[20..50] -> R[52..57] (wait 2 min <= max_wait 15 min)', 'ALLOW · 0 machine overlaps, 0 incubation window violations'],
      denyCase: ['Greedy schedule: incubate ends @ 50m, plate reader starts @ 90m (wait 40m > max_wait 15m)', 'DENY  [labshift :: inter_step_wait_window]'],
      code: `def waitLinkOK (w : WaitLink) : Bool :=
  decide (w.predEndMin + w.minWaitMin ≤ w.succStartMin ∧
          w.succStartMin ≤ w.predEndMin + w.maxWaitMin)

theorem missed_incubation_window_rejected (ops : List ScheduledOp) (links : List WaitLink)
    (w : WaitLink) (hw : w ∈ links) (hover : w.predEndMin + w.maxWaitMin < w.succStartMin) :
    checkSchedule ops links ≠ none`,
    },
    {
      layer: 'L5', repo: 'lab-automation-atlas', file: 'AutoLabLean/L5_Executive.lean',
      theorem: 'eval_only_blocked_from_training',
      boundary: 'External resources must use HTTPS (no private/loopback SSRF), carry explicit SPDX licenses, and block `evalOnly` benchmarks (`LAB-Bench`) or non-commercial corpora from training.',
      allowCase: ['AtlasResource { httpsOnly=true, spdxKnown=true, license=.permissive, forTraining=true }', 'ALLOW · Permissive MIT/CC-BY corpus safe for training'],
      denyCase: ['AtlasResource { license=.evalOnly (LAB-Bench), forTraining=true }', 'DENY  [lab-automation-atlas :: eval_only_contamination_guard]'],
      code: `theorem eval_only_blocked_from_training (r : AtlasResource)
    (htr : r.forTraining = true) (hev : r.licenseClass = .evalOnly) :
    checkAtlasResource r ≠ none`,
    },
    {
      layer: 'L4', repo: 'lab-rehearsal', file: 'AutoLabLean/L4_TwinAndGate.lean',
      theorem: 'checkRehearsal_preserves_capacity & runRehearsalSteps_conserves',
      boundary: 'Multi-step 96-well twin enforces dead-volume reserve, well capacity, solute concentration monotonicity (`A1 -> H1`, blocking `B1 -> A1` back-entry), `>= 80 C` seal, and episodic recall fast-deny.',
      allowCase: ['2-well serial dilution + sealWell(3) + incubate(95 C) + dropTip (initVol = endVol = 400.0 uL)', 'ALLOW · Total liquid conserved (4000 == 4000) & all wells <= capacity'],
      denyCase: ['Tip mixes dilute well B1 (25%) then re-enters concentrated well A1 (50%)', 'DENY  [lab-rehearsal :: no_tip_cross_contamination]'],
      code: `theorem checkRehearsal_preserves_capacity (s sEnd : DeckState) (protoHash : Nat)
    (steps : List RehearsalStep)
    (hok : checkRehearsal s protoHash steps = .ok sEnd) :
    AllWellsFit sEnd.wells ∧
    totalWellsVol sEnd.wells = totalWellsVol s.wells ∧
    sEnd.tip = .noTip`,
    },
    {
      layer: 'L4', repo: 'lab-verify', file: 'AutoLabLean/L4_TwinAndGate.lean',
      theorem: 'mutating_or_stacked_sql_denied & sorry_proof_always_denied',
      boundary: 'Default-deny 4-layer SQL gate blocks stacked statements, mutations/PRAGMAs, system tables, unknown schema columns, Cartesian joins, and semantic mismatches on counterexample DBs; Lean gate blocks `sorry`/`axiom`.',
      allowCase: ['SELECT COUNT(DISTINCT experiment_id) FROM samples  (passes L1-L4 + 2 perturbation DBs)', 'ALLOW · Certified read-only & behaviorally verified'],
      denyCase: ['SELECT COUNT(experiment_id) FROM samples  (passes L1-L3, fails L4 result (14,) != (5,))', 'DENY  [lab-verify :: layer4_behavioral_verification]'],
      code: `theorem mutating_or_stacked_sql_denied (q : SqlCandidateCheck)
    (hbad : q.statementCount ≠ 1 ∨ q.astReadOnly = false ∨ q.matchesGoldResult = false) :
    checkSqlGate q ≠ none

theorem sorry_proof_always_denied (p : LeanProofCheck) (hs : p.hasSorryOrAdmit = true) :
    checkLeanProofGate p ≠ none`,
    },
    {
      layer: 'L3', repo: 'labbench-posttrain', file: 'AutoLabLean/L3_PostTrain.lean',
      theorem: 'unverified_rollout_gets_zero_reward & splitGuard_no_train_test_overlap',
      boundary: '`SplitGuard` enforces zero group/scaffold/canary overlap across splits, and multiplicative reward gating zeroes out all format/reasoning bonuses unless the domain verifier passes within `<think>` cap.',
      allowCase: ['Rollout { coreVerified=true, oracleStripped=true, thinkTokens=210 <= 512 }', 'ALLOW · Total reward = 1000 permille (900 task + 100 format)'],
      denyCase: ['Exploit rollout { coreVerified=false, thinkTokens=920, formatBonus=680 }', 'DENY  [labbench-posttrain :: think_length_cap] -> reward = 0'],
      code: `def gatedRewardPermille (r : RolloutRewardSpec) : Nat :=
  if r.coreScientificVerified && r.oracleFieldStripped &&
     decide (r.thinkTokens ≤ r.maxThinkTokens) then
    r.taskRewardPermille + r.formatBonusPermille
  else 0

theorem unverified_rollout_gets_zero_reward (r : RolloutRewardSpec)
    (hfail : r.coreScientificVerified = false ∨ r.oracleFieldStripped = false ∨
             r.maxThinkTokens < r.thinkTokens) :
    gatedRewardPermille r = 0`,
    },
    {
      layer: 'L3', repo: 'twinstep', file: 'AutoLabLean/L3_PostTrain.lean',
      theorem: 'violated_dag_edge_rejected',
      boundary: 'Candidate step reorderings must form a complete bijection of `0..n-1` and satisfy every RAW, WAR, and plate-barrier causal dependency edge `(u, v)`.',
      allowCase: ['order = [0 (transfer), 1 (mix), 2 (incubate 37C), 3 (read 520nm)]', 'ALLOW · Topological order satisfies all causal DAG edges'],
      denyCase: ['order = [0, 1, 3 (read), 2 (incubate)]  (violates barrier edge 2 -> 3)', 'DENY  [twinstep :: causal_dag_satisfied]'],
      code: `theorem violated_dag_edge_rejected (nSteps : Nat) (order : List Nat)
    (dagEdges : List (Nat × Nat)) (e : Nat × Nat)
    (he : e ∈ dagEdges) (hbad : dagEdgeSatisfied order e = false) :
    checkTwinStepOrder nSteps order dagEdges ≠ none`,
    },
    {
      layer: 'L3', repo: 'labfill', file: 'AutoLabLean/L3_PostTrain.lean',
      theorem: 'checkPackedBin_conserves_tokens',
      boundary: 'BF16 sequence-packed bins must keep every protocol slice within `binCap`, guarantee pairwise disjoint memory ranges (zero cross-sequence attention leak), and conserve total real tokens.',
      allowCase: ['binCap=512, slices=[0..180, 180..472], expectedTokens=472', 'ALLOW · 92.2% bin fill, disjoint slices, exact token sum'],
      denyCase: ['slices=[0..180, 170..300] (10-token overlap between seq 0 and seq 1)', 'DENY  [labfill :: packed_slices_non_overlapping]'],
      code: `theorem checkPackedBin_conserves_tokens (binCap expectedRealTokens : Nat)
    (slices : List PackedSlice)
    (hok : checkPackedBin binCap expectedRealTokens slices = none) :
    sumSliceLens slices = expectedRealTokens ∧
    ∀ s ∈ slices, s.offset + s.len ≤ binCap`,
    },
    {
      layer: 'L2', repo: 'lab-ears', file: 'AutoLabLean/L2_L1_L0_Embodied.lean',
      theorem: 'checkLabEars_strips_speech',
      boundary: 'Raw lab-room audio is never written to disk (`rawAudioSaved = false`), and every retained mel filter skirt `[loHz, hiHz]` must lie strictly outside the `[300, 3400] Hz` human voice band.',
      allowCase: ['rawAudioSaved=false, retainedBands=[[50, 280], [3500, 7800]] Hz', 'ALLOW · Zero raw audio kept, full speech band stripped'],
      denyCase: ['retainedBands=[[250, 500]] Hz (filter skirt overlaps 300-3400 Hz voice band)', 'DENY  [lab-ears :: full_skirt_speech_band_drop]'],
      code: `theorem checkLabEars_strips_speech (e : AcousticEventCheck)
    (hok : checkLabEars e = none) :
    e.rawAudioSaved = false ∧
    ∀ b ∈ e.retainedBands, b.hiHz ≤ 300 ∨ 3400 ≤ b.loHz`,
    },
    {
      layer: 'L1', repo: 'stepbot', file: 'AutoLabLean/L2_L1_L0_Embodied.lean',
      theorem: 'stepbot_never_underflows_distribute_source',
      boundary: 'Opentrons lowering enforces unique deck slots `1..11`, caps transfer volume at `min(pipetteMax, tipRackMax)`, and accounts for `distribute` blow-out `disposal_volume`.',
      allowCase: ['slots=[1,2,4], vol=100 uL <= min(300, 200), 2*100 + 10 disposal <= 250 uL source', 'ALLOW · Deterministic apiLevel 2.16 lowering certified'],
      denyCase: ['2 * 100 uL + 60 uL disposal_volume = 260 uL > 250 uL source reservoir', 'DENY  [stepbot :: distribute_disposal_volume_conservation]'],
      code: `theorem stepbot_never_underflows_distribute_source (c : StepbotCompileCheck)
    (hok : checkStepbot c = none) :
    c.nDistributeWells * c.transferVol + c.disposalVol ≤ c.sourceWellVol ∧
    c.transferVol ≤ Nat.min c.pipMaxTenthUL c.tipRackMaxTenthUL`,
    },
    {
      layer: 'L1', repo: 'lab-hands', file: 'AutoLabLean/L2_L1_L0_Embodied.lean',
      theorem: 'checkLabHands_guarantees_5mm_clearance',
      boundary: 'Swept arm trajectories must maintain `>= 5 mm` continuous Euclidean clearance from deck bottles, stay within `|q2| <= 2.60 rad`, bound open-meniscus slosh acceleration, and seat tips within `0.2 mm`.',
      allowCase: ['RRT-Connect + shortcut: minClearance=8 mm >= 5 mm, |q2|=1.85 rad, err=0.085 mm', 'ALLOW · Collision-free & slosh-safe trajectory'],
      denyCase: ['Straight joint interpolation: minClearance=2 mm < 5 mm bottle margin', 'DENY  [lab-hands :: continuous_obstacle_clearance]'],
      code: `theorem checkLabHands_guarantees_5mm_clearance (t : ArmTrajectoryCheck)
    (hok : checkLabHands t = none) :
    5 ≤ t.minClearanceMM ∧
    t.absElbowQ2Mrad ≤ 2600 ∧
    t.maxLateralAccMMS2 ≤ t.sloshLimitMMS2`,
    },
    {
      layer: 'L0', repo: 'lab-feet', file: 'AutoLabLean/L2_L1_L0_Embodied.lean',
      theorem: 'checkLabFeet_safe_for_edge',
      boundary: 'Edge quantized students must use `[2, 8]` bits, strictly positive quantization scales (`scaleMicro > 0`), fit within board SRAM byte budgets, and preserve teacher-student agreement.',
      allowCase: ['4-bit student: scaleMicro=12500 > 0, packed=1,520 B <= 4,096 B, agree=99.6%', 'ALLOW · Certified for benchtop MCU / SBC deployment'],
      denyCase: ['Degenerate layer with zero quantization scale (scaleMicro = 0)', 'DENY  [lab-feet :: nonzero_quantization_scale]'],
      code: `theorem checkLabFeet_safe_for_edge (e : EdgeStudentCheck)
    (hok : checkLabFeet e = none) :
    0 < e.scaleMicro ∧
    e.packedWeightBytes ≤ e.maxEdgeSramBytes ∧
    e.minAgreePermille ≤ e.agreementPermille`,
    },
  ];

  let STUDY = null;
  let activeExpKey = 'exp1_molecular_discovery';
  let activeRepo = 'lab-rehearsal';
  let activeWitness = 'deny';

  function fmtInline(text) {
    return esc(text || '').replace(/`([^`]+)`/g, '<code>$1</code>');
  }

  function el(tag, attrs = {}, text) {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v !== undefined && v !== null) n.setAttribute(k, String(v));
    }
    if (text !== undefined) n.textContent = text;
    return n;
  }

  /* ---- Section 01: Monoline Bounded Autonomy Sketch ---- */
  function renderTrustSketch() {
    const host = document.getElementById('trust-sketch-host');
    if (!host) return;
    const dark = document.documentElement.dataset.theme === 'dark';
    const ink = dark ? '#e2e8f0' : '#1e293b';
    const muted = dark ? '#94a3b8' : '#64748b';
    const accent = dark ? '#2dd4bf' : '#0d9488';
    const rose = dark ? '#fb7185' : '#e11d48';
    const amber = dark ? '#fbbf24' : '#d97706';

    const svg = el('svg', { viewBox: '0 0 1060 278', role: 'img' });

    // 1. Left Box: Untrusted Creative AI Policy
    svg.append(el('rect', { x: 24, y: 38, width: 256, height: 196, rx: 12, class: 'sk-box' }));
    svg.append(el('text', { x: 44, y: 66, fill: muted, 'font-size': 10, 'font-weight': '750', 'letter-spacing': '0.1em' }, 'OPEN PROPOSAL GENERATOR'));
    svg.append(el('text', { x: 44, y: 88, fill: ink, 'font-size': 14.5, 'font-weight': '740' }, 'Untrusted AI Policy π'));
    const leftItems = [
      '• Candidate hypotheses & claims',
      '• Molecular analogues & routes',
      '• SQL & multi-pool schedules',
      '• N-step pipetting & arm paths',
      '• RLVR rollouts & <think> traces',
    ];
    leftItems.forEach((txt, i) => {
      svg.append(el('text', { x: 44, y: 116 + i * 22, fill: muted, 'font-size': 11.6 }, txt));
    });

    // 2. Center Shield Wall: AutoLabLean Kernel
    svg.append(el('rect', { x: 392, y: 20, width: 246, height: 236, rx: 14, class: 'sk-box sk-active-fill' }));
    svg.append(el('text', { x: 515, y: 48, fill: accent, 'font-size': 10.2, 'font-weight': '780', 'text-anchor': 'middle', 'letter-spacing': '0.11em' }, 'HARD LEAN 4.36.0 BOUNDARY'));
    svg.append(el('text', { x: 515, y: 70, fill: ink, 'font-size': 15.5, 'font-weight': '780', 'text-anchor': 'middle' }, 'AutoLabLean Kernel'));
    const gates = [
      'L6  Conformal rank & kNN gate',
      'L5  Acyclic atoms & wait windows',
      'L4  96w conc. & 4-layer SQL gate',
      'L3  SplitGuard & 0-hack reward',
      'L2–L0  Voice drop, >=5mm & int4',
    ];
    gates.forEach((g, i) => {
      svg.append(el('rect', { x: 412, y: 84 + i * 30, width: 206, height: 23, rx: 5, class: 'sk-box' }));
      svg.append(el('text', {
        x: 515, y: 99 + i * 30, fill: ink, 'font-size': 10.8, 'font-weight': '640',
        'text-anchor': 'middle', 'font-family': '"SFMono-Regular", Consolas, monospace',
      }, g));
    });

    // 3. Right Box: Certified Trust Regime Manifold
    svg.append(el('rect', { x: 756, y: 38, width: 280, height: 196, rx: 12, class: 'sk-box' }));
    svg.append(el('text', { x: 776, y: 66, fill: accent, 'font-size': 10, 'font-weight': '750', 'letter-spacing': '0.1em' }, 'CERTIFIED TRUST REGIME'));
    svg.append(el('text', { x: 776, y: 88, fill: ink, 'font-size': 14.5, 'font-weight': '740' }, 'Autonomous Research Interior'));
    const rightItems = [
      '✓ 0.0% boundary crossings (proved)',
      '✓ Total liquid & capacity conserved',
      '✓ 97.6% empirical ESOL coverage',
      '✓ 97.5% valid protocols (Best-of-8)',
      '✓ 98.4% true RLVR policy accuracy',
    ];
    rightItems.forEach((txt, i) => {
      svg.append(el('text', { x: 776, y: 116 + i * 22, fill: ink, 'font-size': 11.8, 'font-weight': '560' }, txt));
    });

    // Arrows:
    // Top rejected arrow bouncing off the Lean wall + returning exact counterexample witness!
    svg.append(el('path', { d: 'M 280 96 H 386', stroke: rose, 'stroke-width': 1.8, fill: 'none', 'stroke-dasharray': '5 4' }));
    svg.append(el('polygon', { points: '388,96 380,92 380,100', fill: rose }));
    svg.append(el('text', { x: 334, y: 87, fill: rose, 'font-size': 10.2, 'font-weight': '700', 'text-anchor': 'middle' }, 'Out-of-bounds'));

    // Counterexample repair feedback arrow cleanly centered in [280, 392] alley
    svg.append(el('path', {
      d: 'M 392 204 H 288',
      stroke: amber, 'stroke-width': 1.8, fill: 'none',
    }));
    svg.append(el('polygon', { points: '282,204 290,199 290,209', fill: amber }));
    svg.append(el('text', { x: 336, y: 222, fill: amber, 'font-size': 9.8, 'font-weight': '700', 'text-anchor': 'middle' }, 'Rule witness → Repair'));

    // Certified pass-through arrow into Trust Regime Interior
    svg.append(el('path', { d: 'M 280 148 H 390', class: 'sk-edge-active' }));
    svg.append(el('path', { d: 'M 638 148 H 750', class: 'sk-edge-active' }));
    svg.append(el('polygon', { points: '754,148 745,143 745,153', fill: accent }));
    svg.append(el('text', { x: 696, y: 138, fill: accent, 'font-size': 10.5, 'font-weight': '750', 'text-anchor': 'middle' }, 'verifyCycle = .ok'));

    host.replaceChildren(svg);
  }

  /* ---- Section 02: 5-Task Empirical Study Explorer ---- */
  const EXP_META = [
    {
      key: 'exp1_molecular_discovery',
      tab: '1 · Molecular Discovery (ESOL)',
      summary: 'Selecting 25 bench candidates from 1,128 real Delaney ESOL organic compounds under a $25/g synthesis budget (5 seeds, 4,680 Lean kernel calls).',
      extract: exp => [
        {
          name: 'Ungated Point-Predictor',
          tone: 'fail',
          violation: `${exp.regimes.ungated.boundary_violation_pct}% boundary violations`,
          primaryLabel: 'Verified Soluble Hit Yield',
          primaryVal: exp.regimes.ungated.verified_hit_yield_pct,
          secondary: `MAE ${exp.regimes.ungated.prediction_mae} log(mol/L) · ${exp.regimes.ungated.empirical_coverage_pct}% coverage`,
        },
        {
          name: 'Partial Heuristic (SMILES + scalar price)',
          tone: 'hold',
          violation: `${exp.regimes.heuristic.boundary_violation_pct}% boundary violations`,
          primaryLabel: 'Verified Soluble Hit Yield',
          primaryVal: exp.regimes.heuristic.verified_hit_yield_pct,
          secondary: `MAE ${exp.regimes.heuristic.prediction_mae} log(mol/L) · ${exp.regimes.heuristic.empirical_coverage_pct}% coverage`,
        },
        {
          name: 'Lean 4 Trust Regime (AutoLabLean)',
          tone: 'pass',
          violation: `${exp.regimes.lean_trust.boundary_violation_pct}% boundary violations`,
          primaryLabel: 'Verified Soluble Hit Yield',
          primaryVal: exp.regimes.lean_trust.verified_hit_yield_pct,
          secondary: `MAE ${exp.regimes.lean_trust.prediction_mae} log(mol/L) (-59.8% error) · ${exp.regimes.lean_trust.empirical_coverage_pct}% coverage`,
        },
      ],
    },
    {
      key: 'exp2_protocol_synthesis',
      tab: '2 · Protocol Synthesis & Repair',
      summary: '200 multi-step wet-lab tasks x 8 noisy candidate protocols verified through native autolab-lean (~30,000 protocols/sec).',
      extract: exp => [
        {
          name: 'Ungated Top-1 Candidate',
          tone: 'fail',
          violation: `${exp.regimes.ungated_top1.hardware_fault_pct}% hardware faults`,
          primaryLabel: 'Valid Task Completion',
          primaryVal: exp.regimes.ungated_top1.valid_completion_pct,
          secondary: 'Sends unsealed 95 C, dead-vol underflow, or dirty-tip steps straight to robot',
        },
        {
          name: 'Coarse Bitmask / Capacity Heuristic',
          tone: 'hold',
          violation: `${exp.regimes.coarse_bitmask_heuristic.hardware_fault_pct}% hardware faults`,
          primaryLabel: 'Valid Task Completion',
          primaryVal: exp.regimes.coarse_bitmask_heuristic.valid_completion_pct,
          secondary: 'Catches gross overflow, misses B1->A1 conc. back-entry & >=80 C evaporation',
        },
        {
          name: 'Lean Shielded Best-of-8',
          tone: 'pass',
          violation: `${exp.regimes.lean_best_of_8.hardware_fault_pct}% hardware faults`,
          primaryLabel: 'Valid Task Completion',
          primaryVal: exp.regimes.lean_best_of_8.valid_completion_pct,
          secondary: 'Selects certified candidate via selectBestCertified',
        },
        {
          name: 'Lean Best-of-8 + Guided 1-Step Repair',
          tone: 'pass',
          violation: `${exp.regimes.lean_best_of_8_plus_guided_repair.hardware_fault_pct}% hardware faults`,
          primaryLabel: 'Valid Task Completion',
          primaryVal: exp.regimes.lean_best_of_8_plus_guided_repair.valid_completion_pct,
          secondary: 'Uses exact AutoLabLean rule witness to insert missing seal/thaw/tip-swap & re-verify',
        },
      ],
    },
    {
      key: 'exp3_fleet_scheduling',
      tab: '3 · Fleet Scheduling (labshift)',
      summary: '30 contended multi-instrument benchmark suites across 5 pools (liquid handler, incubator, reader, centrifuge, washer) with strict post-incubation max_wait bounds.',
      extract: exp => [
        {
          name: 'Ungated Greedy List Dispatch',
          tone: 'fail',
          violation: `${exp.regimes.ungated_greedy.window_violations} ruined incubation windows`,
          primaryLabel: 'Suite Feasibility (%)',
          primaryVal: exp.regimes.ungated_greedy.feasible_pct,
          secondary: `${exp.regimes.ungated_greedy.feasible_instances} feasible · ${exp.regimes.ungated_greedy.mean_makespan_min || exp.regimes.ungated_greedy.mean_feasible_makespan_min} min mean makespan`,
        },
        {
          name: 'Greedy + Local Window Repair',
          tone: 'pass',
          violation: `${exp.regimes.greedy_with_repair.window_violations} window violations`,
          primaryLabel: 'Suite Feasibility (%)',
          primaryVal: exp.regimes.greedy_with_repair.feasible_pct,
          secondary: `${exp.regimes.greedy_with_repair.feasible_instances} feasible · ${exp.regimes.greedy_with_repair.mean_makespan_min || exp.regimes.greedy_with_repair.mean_feasible_makespan_min} min mean makespan`,
        },
        {
          name: 'Lean-Certified CP-SAT Schedule',
          tone: 'pass',
          violation: `${exp.regimes.lean_gated_cpsat.window_violations} window violations`,
          primaryLabel: 'Suite Feasibility (%)',
          primaryVal: exp.regimes.lean_gated_cpsat.feasible_pct,
          secondary: `${exp.regimes.lean_gated_cpsat.feasible_instances} feasible · ${exp.regimes.lean_gated_cpsat.mean_makespan_min || exp.regimes.lean_gated_cpsat.mean_feasible_makespan_min} min mean makespan (-10.2% faster)`,
        },
      ],
    },
    {
      key: 'exp4_sql_verification',
      tab: '4 · Lab SQL Gate (lab-verify)',
      summary: '30 SQL candidates across 16 laboratory database tasks (including stacked DROPs, CTE scope traps, and COUNT vs COUNT DISTINCT semantic bugs).',
      extract: exp => [
        {
          name: 'Ungated Noisy Top-1',
          tone: 'fail',
          violation: `${exp.regimes.ungated_noisy_top1.wrong_sql_false_accept_pct}% wrong SQL accepted`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.ungated_noisy_top1.verified_answer_accuracy_pct,
          secondary: 'Executes unscreened top-1 query directly',
        },
        {
          name: 'Syntax + Read-Only + Schema (L1–L3)',
          tone: 'hold',
          violation: `${exp.regimes.syntax_readonly_schema_only_L1_L3.wrong_sql_false_accept_pct}% wrong SQL slipped through`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.syntax_readonly_schema_only_L1_L3.verified_answer_accuracy_pct,
          secondary: 'Blocks DROP/unknown columns, but lets semantic aggregate/join errors pass',
        },
        {
          name: 'Lean 4-Layer Default-Deny (L1–L4 + Counterexamples)',
          tone: 'pass',
          violation: `${exp.regimes.lean_4layer_default_deny_L1_L4.wrong_sql_false_accept_pct}% wrong SQL accepted`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.lean_4layer_default_deny_L1_L4.verified_answer_accuracy_pct,
          secondary: 'Zero false accepts across all 18 adversarial & semantic-bug queries',
        },
      ],
    },
    {
      key: 'exp5_rlvr_posttraining',
      tab: '5 · RLVR Post-Training (GRPO)',
      summary: '5-seed GRPO optimization (160 steps x 8 rollouts/step) when action space includes <think> length padding, ERR always-True, and oracle-copying exploits.',
      extract: exp => [
        {
          name: 'Untrained Initial Policy',
          tone: 'hold',
          violation: `${exp.regimes.untrained_init.reward_hack_exploit_pct}% exploit mass`,
          primaryLabel: 'True Verified Accuracy',
          primaryVal: exp.regimes.untrained_init.true_verified_accuracy_pct,
          secondary: 'Starting policy prior before RLVR updates',
        },
        {
          name: 'Soft Additive Format + Length Bonus (GRPO)',
          tone: 'fail',
          violation: `${exp.regimes.soft_additive_reward_grpo.reward_hack_exploit_pct}% exploit collapse`,
          primaryLabel: 'True Verified Accuracy',
          primaryVal: exp.regimes.soft_additive_reward_grpo.true_verified_accuracy_pct,
          secondary: 'Policy rapidly games verbose <think> & format rewards instead of domain truth',
        },
        {
          name: 'Lean Multiplicative Trust-Regime Gate (GRPO)',
          tone: 'pass',
          violation: `${exp.regimes.lean_trust_gated_grpo.reward_hack_exploit_pct}% exploit mass`,
          primaryLabel: 'True Verified Accuracy',
          primaryVal: exp.regimes.lean_trust_gated_grpo.true_verified_accuracy_pct,
          secondary: 'Theorem unverified_rollout_gets_zero_reward zeroes all exploit bonuses -> concentrates gradient on truth',
        },
      ],
    },
  ];

  function renderExperiments() {
    const tabsHost = document.getElementById('exp-tabs');
    const stage = document.getElementById('exp-stage');
    if (!tabsHost || !stage || !STUDY) return;

    tabsHost.innerHTML = EXP_META.map(m => `
      <button type="button" class="tab-btn ${m.key === activeExpKey ? 'active' : ''}" data-exp="${esc(m.key)}">
        ${esc(m.tab)}
      </button>`).join('');

    tabsHost.querySelectorAll('[data-exp]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeExpKey = btn.dataset.exp;
        renderExperiments();
      });
    });

    const meta = EXP_META.find(m => m.key === activeExpKey) || EXP_META[0];
    const expData = STUDY.experiments[meta.key];
    const rows = meta.extract(expData);

    stage.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid var(--line);">
        <div>
          <span class="small-label teal">${esc((expData.repos || []).join(' · '))}</span>
          <h3 style="font-size:19px;font-weight:740;margin-top:4px;">${esc(expData.task)}</h3>
          <p style="font-size:13.8px;color:var(--muted);margin-top:4px;">${esc(meta.summary)}</p>
        </div>
        <a class="button secondary" href="https://github.com/yaniguan/auto-lab/blob/main/benchmarks/trust_regime_study.py" target="_blank" rel="noopener">
          Benchmark Script ↗
        </a>
      </div>
      <div style="display:grid;gap:14px;">
        ${rows.map(r => `
          <div style="background:var(--surface2);border:1px solid var(--line);border-radius:11px;padding:14px 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">
              <strong style="font-size:14.5px;">${esc(r.name)}</strong>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                <span class="pill ${esc(r.tone)}">${esc(r.violation)}</span>
                <span style="font-size:13.5px;font-weight:740;color:var(--text);">${esc(r.primaryLabel)}: ${esc(r.primaryVal)}%</span>
              </div>
            </div>
            <div style="height:10px;background:var(--surface);border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-bottom:7px;">
              <div style="height:100%;width:${Math.max(2, Math.min(100, Number(r.primaryVal)))}%;background:${r.tone === 'pass' ? 'var(--accent)' : r.tone === 'hold' ? 'var(--amber)' : 'var(--rose)'};border-radius:999px;"></div>
            </div>
            <p style="font-size:12.6px;color:var(--muted);">${esc(r.secondary)}</p>
          </div>`).join('')}
      </div>`;
  }

  /* ---- Section 03: 14-Repo Lean 4 Guardrail Explorer ---- */
  function renderLeanExplorer() {
    const sb = document.getElementById('lean-sidebar-groups');
    const host = document.getElementById('lean-card-host');
    if (!sb || !host) return;

    const layers = ['L6', 'L5', 'L4', 'L3', 'L2', 'L1', 'L0'];
    sb.innerHTML = layers.map(code => {
      const items = LEAN_SPECS.filter(s => s.layer === code);
      return `
        <div class="sidebar-group">
          <div class="sidebar-group-label">${esc(code)} Guardrails</div>
          ${items.map(s => `
            <button type="button" class="sidebar-item ${s.repo === activeRepo ? 'active' : ''}" data-lean-repo="${esc(s.repo)}" style="justify-content:flex-start;gap:8px;">
              ${iconMarkup(s.repo, 16)}
              <span>${esc(s.repo)}</span>
            </button>`).join('')}
        </div>`;
    }).join('');

    sb.querySelectorAll('[data-lean-repo]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeRepo = btn.dataset.leanRepo;
        renderLeanExplorer();
      });
    });

    const spec = LEAN_SPECS.find(s => s.repo === activeRepo) || LEAN_SPECS[0];
    const isAllow = activeWitness === 'allow';
    const [wIn, wOut] = isAllow ? spec.allowCase : spec.denyCase;

    host.innerHTML = `
      <div class="dossier-header" style="margin-bottom:14px;padding-bottom:16px;">
        <div style="min-width:0;flex:1;">
          <span class="small-label teal">${esc(spec.layer)} · <code>lean/${esc(spec.file)}</code></span>
          <div style="display:flex;align-items:center;gap:10px;margin-top:5px;">
            <span style="color:var(--accent);display:inline-flex;">${iconMarkup(spec.repo, 28)}</span>
            <h2 style="margin:0;">${esc(spec.repo)}</h2>
          </div>
          <p style="font-size:13px;color:var(--muted);margin-top:6px;">Proved Theorem: <code>${esc(spec.theorem)}</code></p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="https://github.com/yaniguan/auto-lab/blob/main/lean/${esc(spec.file)}" target="_blank" rel="noopener">View .lean File ↗</a>
          <a class="button secondary" href="../repos/#${encodeURIComponent(spec.repo)}">Repo Story →</a>
        </div>
      </div>

      <div class="story-why-callout">
        <span class="story-why-label">Hard Guardrail (Cannot Be Crossed)</span>
        <p>${fmtInline(spec.boundary)}</p>
      </div>

      <section class="story-playground" aria-label="Compile-time #guard witness">
        <div class="playground-head">
          <div class="playground-kicker">
            <span><strong style="color:var(--accent);">Compile-Time <code>#guard</code> Witness</strong> · Toggle in-regime vs boundary-crossing input:</span>
            <span class="pill ${isAllow ? 'pass' : 'fail'}">${isAllow ? 'ALLOW · Certified' : 'DENY · Blocked at Wall'}</span>
          </div>
          <div class="demo-tabs">
            <button type="button" class="demo-tab-btn ${!isAllow ? 'active' : ''}" data-wit="deny">Boundary-Crossing Input (Blocked)</button>
            <button type="button" class="demo-tab-btn ${isAllow ? 'active' : ''}" data-wit="allow">In-Regime Input (Certified)</button>
          </div>
        </div>
        <div class="playground-body">
          <div class="io-block">
            <div class="io-bar"><span>Candidate Action</span></div>
            <pre class="io-pre">${esc(wIn)}</pre>
          </div>
          <div class="io-block">
            <div class="io-bar"><span>Lean 4 Kernel Verdict</span></div>
            <pre class="io-pre">${esc(wOut)}</pre>
          </div>
        </div>
      </section>

      <div>
        <span class="small-label purple" style="display:block;margin-bottom:8px;">Machine-Checked Lean 4.36.0 Specification &amp; Theorem</span>
        <pre class="code-block">${esc(spec.code)}</pre>
      </div>`;

    host.querySelectorAll('[data-wit]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeWitness = btn.dataset.wit;
        renderLeanExplorer();
      });
    });
  }

  async function init() {
    initThemeToggle(() => renderTrustSketch());
    renderTrustSketch();
    renderLeanExplorer();

    const resp = await fetch('../assets/trust-regime-data.json');
    STUDY = await resp.json();
    renderExperiments();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
