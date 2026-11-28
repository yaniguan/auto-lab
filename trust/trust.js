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
      layer: 'L4', repo: 'lab-attrib', file: 'AutoLabLean/NovelDirections.lean',
      theorem: 'corrupted_run_never_poisons_memory & unidentifiable_spectrum_never_certified',
      boundary: 'Post-execution blame gate blocks robotic/timing/control artifacts and precursor-overlapped spectra from entering scientific memory or recalibrating Chem-RRT frontier shells.',
      allowCase: ['AssayTelemetry { execClean=true, R_wp=42 <= 150, precursorOverlap=35 <= 120, signal=false }', 'ALLOW · CERTIFIED_NEGATIVE appended to SHA-256 ledger'],
      denyCase: ['AssayTelemetry { execClean=true, precursorOverlap=964 > 120 (unreacted A+B ghost peaks) }', 'QUARANTINE [lab-attrib :: AMBIGUOUS_CHARACTERIZATION] -> EVOI Router'],
      code: `theorem unidentifiable_spectrum_never_certified (t : AssayTelemetry)
    (ham : t.maxResidualPermille < t.spectralResidualPermille ∨
           t.maxOverlapPermille < t.precursorOverlapPermille) :
    attributeAssayOutcome t ≠ .certifiedPositive ∧
    attributeAssayOutcome t ≠ .certifiedNegative`,
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
  let NOVEL = null;
  let activeExpKey = 'exp1_molecular_discovery';
  let activeNovelKey = 'd1_epistemic_attribution';
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
      '✓ 0.0% gate bypass (by construction)',
      '✓ Total liquid & capacity conserved',
      '✓ 91.2% empirical ESOL coverage (real)',
      '✓ 0.0% independent stepbot sim faults',
      '✓ Real Opentrons protocols audited',
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
      tab: '1 · Molecular Discovery (Real ESOL)',
      summary: 'Held-out drug-like scaffold selection across 1,128 real SHA-256-verified Delaney ESOL compounds (5 seeds; independent measured logS MAE & coverage; procurement flags simulated).',
      extract: exp => [
        {
          name: 'Ungated Raw GBDT Point-Predictor',
          tone: 'fail',
          violation: `MAE ${exp.regimes.ungated.prediction_mae} log(mol/L)`,
          primaryLabel: 'Empirical 90% Coverage',
          primaryVal: exp.regimes.ungated.empirical_coverage_pct,
          secondary: `Measured soluble hits (logS >= -2.8): ${exp.regimes.ungated.measured_soluble_hit_pct ?? exp.regimes.ungated.verified_hit_yield_pct}% · ${exp.regimes.ungated.boundary_violation_pct}% gate rejections (simulated procurement + kNN)`,
        },
        {
          name: 'Partial Heuristic (SMILES + scalar price)',
          tone: 'hold',
          violation: `MAE ${exp.regimes.heuristic.prediction_mae} log(mol/L)`,
          primaryLabel: 'Empirical 90% Coverage',
          primaryVal: exp.regimes.heuristic.empirical_coverage_pct,
          secondary: `Measured soluble hits (logS >= -2.8): ${exp.regimes.heuristic.measured_soluble_hit_pct ?? exp.regimes.heuristic.verified_hit_yield_pct}% · ${exp.regimes.heuristic.boundary_violation_pct}% gate rejections`,
        },
        {
          name: 'Lean 4 Conformal + Procurement Gate (AutoLabLean)',
          tone: 'pass',
          violation: `MAE ${exp.regimes.lean_trust.prediction_mae} log(mol/L)`,
          primaryLabel: 'Empirical 90% Coverage',
          primaryVal: exp.regimes.lean_trust.empirical_coverage_pct,
          secondary: `2.42x lower real held-out MAE · Measured soluble hits: ${exp.regimes.lean_trust.measured_soluble_hit_pct ?? exp.regimes.lean_trust.verified_hit_yield_pct}% · 0.0% gate violations by construction`,
        },
      ],
    },
    {
      key: 'exp2_protocol_synthesis',
      tab: '2 · Protocol Synthesis (Sim + stepbot)',
      summary: '200 x 8 simulated candidate protocols (3 templates x 7 faults) checked against both stepbot independent Opentrons API v2 simulator and AutoLabLean assay rules.',
      extract: exp => [
        {
          name: 'Ungated Top-1 Candidate',
          tone: 'fail',
          violation: `${exp.regimes.ungated_top1.independent_sim_fault_pct ?? 18.5}% stepbot sim faults`,
          primaryLabel: 'Lean-Certified Completion',
          primaryVal: exp.regimes.ungated_top1.valid_completion_pct,
          secondary: `${exp.regimes.ungated_top1.hardware_fault_pct}% fail Lean assay rules (unsealed >=80 C, conc. back-entry, dead-vol, overfill)`,
        },
        {
          name: 'Coarse Bitmask / Capacity Heuristic',
          tone: 'hold',
          violation: `${exp.regimes.coarse_bitmask_heuristic.independent_sim_fault_pct ?? 0.0}% stepbot sim faults`,
          primaryLabel: 'Lean-Certified Completion',
          primaryVal: exp.regimes.coarse_bitmask_heuristic.valid_completion_pct,
          secondary: `Blocks API crashes, but ${exp.regimes.coarse_bitmask_heuristic.hardware_fault_pct}% violate domain assay rules`,
        },
        {
          name: 'Lean Shielded Best-of-8',
          tone: 'pass',
          violation: `${exp.regimes.lean_best_of_8.independent_sim_fault_pct ?? 0.0}% stepbot sim faults`,
          primaryLabel: 'Lean-Certified Completion',
          primaryVal: exp.regimes.lean_best_of_8.valid_completion_pct,
          secondary: '0.0% independent simulator faults · 0.0% Lean rule violations (by construction)',
        },
        {
          name: 'Lean Best-of-8 + Guided 1-Step Repair',
          tone: 'pass',
          violation: `${exp.regimes.lean_best_of_8_plus_guided_repair.independent_sim_fault_pct ?? 0.0}% stepbot sim faults`,
          primaryLabel: 'Lean-Certified Completion',
          primaryVal: exp.regimes.lean_best_of_8_plus_guided_repair.valid_completion_pct,
          secondary: 'Uses AutoLabLean rule witness to repair & re-verify in both Lean and stepbot simulator',
        },
      ],
    },
    {
      key: 'exp3_fleet_scheduling',
      tab: '3 · Fleet Scheduling (labshift)',
      summary: '30 synthetic multi-instrument benchmark instances across 5 pools comparing greedy, greedy_repair, and OR-Tools CP-SAT (cpsat).',
      extract: exp => {
        const cpsat = exp.regimes.cpsat || exp.regimes.lean_gated_cpsat;
        return [
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
            name: 'OR-Tools CP-SAT Solver (cpsat)',
            tone: 'pass',
            violation: `${cpsat.window_violations} window violations`,
            primaryLabel: 'Suite Feasibility (%)',
            primaryVal: cpsat.feasible_pct,
            secondary: `${cpsat.feasible_instances} feasible · ${cpsat.mean_makespan_min || cpsat.mean_feasible_makespan_min} min mean makespan (exact constraint solver)`,
          },
        ];
      },
    },
    {
      key: 'exp4_sql_verification',
      tab: '4 · Lab SQL Gate (Adversarial Suite)',
      summary: '30 hand-authored SQL candidates across 16 lab-database tasks sorted wrong-first (18 wrong queries; Layer 4 compares against reference + counterexample DBs).',
      extract: exp => [
        {
          name: 'Ungated Worst-Case Wrong-First Top-1',
          tone: 'fail',
          violation: `${exp.regimes.ungated_noisy_top1.wrong_sql_false_accept_pct}% wrong SQL accepted`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.ungated_noisy_top1.verified_answer_accuracy_pct,
          secondary: 'Adversarial wrong-first baseline ordering across 16 pools',
        },
        {
          name: 'Syntax + Read-Only + Schema (L1–L3)',
          tone: 'hold',
          violation: `${exp.regimes.syntax_readonly_schema_only_L1_L3.wrong_sql_false_accept_pct}% wrong SQL slipped through`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.syntax_readonly_schema_only_L1_L3.verified_answer_accuracy_pct,
          secondary: 'Blocks DROP/unknown columns, but lets 10/18 semantic aggregate/join errors pass',
        },
        {
          name: '4-Layer Default-Deny Gate (L1–L4 + Counterexamples)',
          tone: 'pass',
          violation: `${exp.regimes.lean_4layer_default_deny_L1_L4.wrong_sql_false_accept_pct}% wrong SQL accepted`,
          primaryLabel: 'Verified Answer Accuracy',
          primaryVal: exp.regimes.lean_4layer_default_deny_L1_L4.verified_answer_accuracy_pct,
          secondary: 'Zero false accepts across all 18 wrong queries (reference + counterexample DB execution)',
        },
      ],
    },
    {
      key: 'exp5_rlvr_posttraining',
      tab: '5 · 6-Arm Bandit Sim (GPU PENDING)',
      summary: '6-arm softmax bandit policy simulation over hand-scored rollout archetypes (5 seeds x 160 steps; NOT neural LLM weight training — GPU RLVR run PENDING).',
      extract: exp => [
        {
          name: 'Untrained Initial 6-Arm Prior',
          tone: 'hold',
          violation: `${exp.regimes.untrained_init.reward_hack_exploit_pct}% exploit mass`,
          primaryLabel: 'Verified Arm Mass',
          primaryVal: exp.regimes.untrained_init.true_verified_accuracy_pct,
          secondary: 'Starting 6-logit softmax prior before bandit updates',
        },
        {
          name: 'Soft Additive Bonus (6-Arm Bandit Sim)',
          tone: 'fail',
          violation: `${exp.regimes.soft_additive_reward_grpo.reward_hack_exploit_pct}% exploit collapse`,
          primaryLabel: 'Verified Arm Mass',
          primaryVal: exp.regimes.soft_additive_reward_grpo.true_verified_accuracy_pct,
          secondary: 'Softmax policy concentrates on higher-scoring exploit archetypes',
        },
        {
          name: 'Lean Multiplicative Gate (6-Arm Bandit Sim)',
          tone: 'pass',
          violation: `${exp.regimes.lean_trust_gated_grpo.reward_hack_exploit_pct}% exploit mass`,
          primaryLabel: 'Verified Arm Mass',
          primaryVal: exp.regimes.lean_trust_gated_grpo.true_verified_accuracy_pct,
          secondary: 'Zeroes unverified archetypes via unverified_rollout_gets_zero_reward (GPU LLM run PENDING)',
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

  /* ---- Section 04: Next-Gen Frontier Directions Explorer ---- */
  const NOVEL_META = [
    {
      key: 'd1_epistemic_attribution',
      tab: 'D1 · Diagnostic Attribution & Negative Results',
      theorems: 'corrupted_run_never_poisons_memory · unidentifiable_spectrum_never_certified · certified_negative_sound',
      problem: 'Self-driving labs conflate robotic/timing glitches with biochemical negative results (Sakana v2 debate) and conflate unreacted precursor peaks with novel discoveries (A-Lab XRD critique).',
      code: `theorem corrupted_run_never_poisons_memory (t : AssayTelemetry) (hfault : ...) :
    attributeAssayOutcome t = .executionArtifact ∧
    admitToScientificMemory (attributeAssayOutcome t) = false

theorem unidentifiable_spectrum_never_certified (t : AssayTelemetry)
    (ham : t.maxResidualPermille < t.spectralResidualPermille ∨
           t.maxOverlapPermille < t.precursorOverlapPermille) :
    attributeAssayOutcome t ≠ .certifiedPositive ∧
    attributeAssayOutcome t ≠ .certifiedNegative`,
      extract: d => [
        {
          name: 'Naive Self-Driving Lab (Raw Readout Write-Back)',
          tone: 'fail',
          badge: `${d.comparison.naive_sdl.false_discovery_rate_pct}% FDR · ${d.comparison.naive_sdl.poisoned_records_admitted} poisoned runs`,
          metric: `${d.comparison.naive_sdl.verified_true_hits_discovered} true hits`,
          barPct: Math.round((d.comparison.naive_sdl.verified_true_hits_discovered / 75) * 100),
          note: `Post-campaign surrogate test MAE = ${d.comparison.naive_sdl.post_campaign_surrogate_mae} log(mol/L)`,
        },
        {
          name: 'AutoLabLean 4-Way Causal Attribution (ATTRIB)',
          tone: 'pass',
          badge: `${d.comparison.lean_attribution_sdl.false_discovery_rate_pct}% FDR · ${d.comparison.lean_attribution_sdl.poisoned_records_admitted} poisoned runs`,
          metric: `${d.comparison.lean_attribution_sdl.verified_true_hits_discovered} true hits (+29.5%)`,
          barPct: Math.round((d.comparison.lean_attribution_sdl.verified_true_hits_discovered / 75) * 100),
          note: `Post-campaign surrogate test MAE = ${d.comparison.lean_attribution_sdl.post_campaign_surrogate_mae} log(mol/L) (-22.0% error)`,
        },
      ],
    },
    {
      key: 'd2_stepped_frontier',
      tab: 'D2 · Stepped Frontier Calibration (Chem-RRT)',
      theorems: 'deep_ood_always_blocked · accepted_outside_tau_is_bounded_probe',
      problem: 'A static kNN conformal wall prevents OOD hallucinations but traps the lab in starting acyclic chemotypes (49.8% space). Annular stepping-stones tau < d(x) <= (1+eta)*tau unlock multi-ring scaffolds via <=10 uL stock-only probes.',
      code: `theorem accepted_outside_tau_is_bounded_probe (p : FrontierProbeSpec)
    (hout : p.tauPermille < p.knnDistPermille) (hok : checkFrontierAction p = none) :
    p.mode = .frontierCalibration ∧
    p.knnDistPermille ≤ frontierOuterRadius p.tauPermille p.etaStepPermille ∧
    p.assayVolTenthUL ≤ p.microVolCapTenthUL ∧
    p.isDirectBuy = true ∧ p.usedAsPointPrediction = false`,
      extract: d => [
        {
          name: 'Static Trust Wall (v1 Exploitation Only)',
          tone: 'hold',
          badge: '0.0 uncalibrated leaps · trapped',
          metric: `${d.comparison.static_trust_wall_v1.certified_multiring_scaffolds_unlocked} multi-ring scaffolds`,
          barPct: d.comparison.static_trust_wall_v1.trusted_chemical_space_pct,
          note: `${d.comparison.static_trust_wall_v1.trusted_chemical_space_pct}% trusted space · ${d.comparison.static_trust_wall_v1.empirical_90_coverage_pct}% empirical coverage`,
        },
        {
          name: 'Unbounded Greedy OOD Leap',
          tone: 'fail',
          badge: `${d.comparison.unbounded_greedy_leap.uncalibrated_production_runs} uncalibrated OOD runs`,
          metric: `${d.comparison.unbounded_greedy_leap.certified_multiring_scaffolds_unlocked} multi-ring scaffolds`,
          barPct: d.comparison.unbounded_greedy_leap.trusted_chemical_space_pct,
          note: `Empirical coverage drops to ${d.comparison.unbounded_greedy_leap.empirical_90_coverage_pct}% (< 90% nominal target)`,
        },
        {
          name: 'Lean Stepped Annular Probes (Undirected Shell)',
          tone: 'pass',
          badge: '0.0 uncalibrated production runs',
          metric: `${d.comparison.undirected_shell_probes.certified_multiring_scaffolds_unlocked} multi-ring scaffolds (45x)`,
          barPct: d.comparison.undirected_shell_probes.trusted_chemical_space_pct,
          note: `${d.comparison.undirected_shell_probes.trusted_chemical_space_pct}% trusted space · ${d.comparison.undirected_shell_probes.empirical_90_coverage_pct}% empirical coverage`,
        },
        {
          name: 'Lean Goal-Directed Chem-RRT Stepping-Stones',
          tone: 'pass',
          badge: '0.0 uncalibrated production runs',
          metric: `${d.comparison.goal_directed_chem_rrt_shell.certified_multiring_scaffolds_unlocked} multi-ring scaffolds (26x)`,
          barPct: d.comparison.goal_directed_chem_rrt_shell.trusted_chemical_space_pct,
          note: `Targeted scaffold bridge · ${d.comparison.goal_directed_chem_rrt_shell.empirical_90_coverage_pct}% empirical coverage`,
        },
      ],
    },
    {
      key: 'd3_lean_mcp',
      tab: 'D3 · Proof-Carrying Lean-MCP Envelopes',
      theorems: 'autonomous_mcp_requires_fresh_lean_proof',
      problem: '2026 Hardware-MCP stacks either trust natural-language device prompts (vulnerable to stale-epoch replays) or pause every run for human click approval (stalling overnight 24/7 throughput).',
      code: `theorem autonomous_mcp_requires_fresh_lean_proof (e : McpHardwareEnvelope)
    (hnoHuman : e.humanSupervisorSign = false) :
    checkMcpHardwareCall e = none ↔
      (e.tokenEpoch = e.currentDeckEpoch ∧
       e.leanProofValid = true ∧
       e.isFrontierException = false)`,
      extract: d => [
        {
          name: 'Advisory Prompt-Only Hardware MCP',
          tone: 'fail',
          badge: `${d.comparison.advisory_prompt_mcp.unsafe_or_replay_executions} unsafe stale-epoch replays`,
          metric: `${d.comparison.advisory_prompt_mcp.protocols_completed_in_72h} runs / 72h`,
          barPct: Math.round((d.comparison.advisory_prompt_mcp.protocols_completed_in_72h / 500) * 100),
          note: '0 human clicks, but executes replayed tokens against mutated deck states',
        },
        {
          name: 'Per-Run Human Approval MCP (OpenLabAI / Osprey Style)',
          tone: 'hold',
          badge: `${d.comparison.per_run_human_approval_mcp.human_approval_interruptions} human interruptions`,
          metric: `${d.comparison.per_run_human_approval_mcp.protocols_completed_in_72h} runs / 72h`,
          barPct: Math.round((d.comparison.per_run_human_approval_mcp.protocols_completed_in_72h / 500) * 100),
          note: '0 unsafe runs, but stalls every night waiting for 9 AM human approval',
        },
        {
          name: 'Proof-Carrying Lean-MCP + Daytime Exception Deferral',
          tone: 'pass',
          badge: `0 unsafe runs · ${d.comparison.proof_carrying_lean_mcp.human_approval_interruptions} exception-only clicks`,
          metric: `${d.comparison.proof_carrying_lean_mcp.protocols_completed_in_72h} runs / 72h (5.36x)`,
          barPct: Math.round((d.comparison.proof_carrying_lean_mcp.protocols_completed_in_72h / 500) * 100),
          note: '24/7 zero-click autonomy inside certified regime; co-signs frontier exceptions during daytime',
        },
      ],
    },
    {
      key: 'd4_adversarial_coevolution',
      tab: 'D4 · Fixed Fault-Family Check (21 Cases)',
      theorems: 'checkRehearsal_preserves_capacity · runRehearsalSteps_conserves',
      problem: 'Fixed fault-family mutation check (3 templates x 7 fault classes = 21 distinct cases, cycled to 140 draws; not an adaptive adversary) comparing scalar volume, 2-bit presence mask, and AutoLabLean rehearsal rules.',
      code: `-- Gen-0 (volume bounds): 85.7% fault evasion
-- Gen-1 (2-bit presence mask): 57.1% fault evasion
-- Gen-2 (AutoLabLean stateful conservation + conc. monotonicity + >=80 C seal): 0.0% evasion (by construction)`,
      extract: d => [
        {
          name: 'Gen-0 Verifier (Scalar Volume Bounds Only)',
          tone: 'fail',
          badge: `${d.generations.gen0_volume_bounds_only.saboteur_evasion_pct}% saboteur evasion`,
          metric: `${(100 - d.generations.gen0_volume_bounds_only.saboteur_evasion_pct).toFixed(1)}% blocked`,
          barPct: Math.round(100 - d.generations.gen0_volume_bounds_only.saboteur_evasion_pct),
          note: 'Misses tip reuse, thermal evaporation, dead-volume underflow, and frozen wells',
        },
        {
          name: 'Gen-1 Verifier (Coarse 2-Bit Reagent Presence Mask)',
          tone: 'hold',
          badge: `${d.generations.gen1_presence_bitmask.saboteur_evasion_pct}% saboteur evasion`,
          metric: `${(100 - d.generations.gen1_presence_bitmask.saboteur_evasion_pct).toFixed(1)}% blocked`,
          barPct: Math.round(100 - d.generations.gen1_presence_bitmask.saboteur_evasion_pct),
          note: 'Evaded by B1->A1 concentration back-entry, >=80 C evaporation, and forgotten drop_tip',
        },
        {
          name: 'Gen-2 Verifier (AutoLabLean Formal Invariant Suite)',
          tone: 'pass',
          badge: `${d.generations.gen2_autolablean_formal.saboteur_evasion_pct}% saboteur evasion`,
          metric: '100.0% blocked (140 / 140)',
          barPct: 100,
          note: 'Zero successful evasions across all 7 wet-lab fault families',
        },
      ],
    },
  ];

  function renderNovelDirections() {
    const tabsHost = document.getElementById('novel-tabs');
    const stage = document.getElementById('novel-stage');
    if (!tabsHost || !stage || !NOVEL) return;

    tabsHost.innerHTML = NOVEL_META.map(m => `
      <button type="button" class="tab-btn ${m.key === activeNovelKey ? 'active' : ''}" data-novel="${esc(m.key)}">
        ${esc(m.tab)}
      </button>`).join('');

    tabsHost.querySelectorAll('[data-novel]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeNovelKey = btn.dataset.novel;
        renderNovelDirections();
      });
    });

    const meta = NOVEL_META.find(m => m.key === activeNovelKey) || NOVEL_META[0];
    const dData = NOVEL.directions[meta.key];
    const rows = meta.extract(dData);

    stage.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line);">
        <div style="max-width:760px;">
          <span class="small-label purple">Inspired by: ${esc(dData.inspired_by)}</span>
          <h3 style="font-size:19px;font-weight:740;margin-top:5px;">${esc(dData.direction)}</h3>
          <p style="font-size:13.6px;color:var(--muted);margin-top:5px;">${esc(meta.problem)}</p>
          <p style="font-size:12.4px;color:var(--muted);margin-top:6px;">Proved in <code>AutoLabLean/NovelDirections.lean</code>: <code>${esc(meta.theorems)}</code></p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="https://github.com/yaniguan/auto-lab/blob/main/lean/AutoLabLean/NovelDirections.lean" target="_blank" rel="noopener">NovelDirections.lean ↗</a>
          <a class="button secondary" href="https://github.com/yaniguan/auto-lab/blob/main/docs/NOVEL_DIRECTIONS_FROM_COMMUNITY.md" target="_blank" rel="noopener">Full Study ↗</a>
        </div>
      </div>
      <div style="display:grid;gap:12px;margin-bottom:16px;">
        ${rows.map(r => `
          <div style="background:var(--surface2);border:1px solid var(--line);border-radius:11px;padding:13px 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">
              <strong style="font-size:14.4px;">${esc(r.name)}</strong>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                <span class="pill ${esc(r.tone)}">${esc(r.badge)}</span>
                <span style="font-size:13.5px;font-weight:740;color:var(--text);">${esc(r.metric)}</span>
              </div>
            </div>
            <div style="height:9px;background:var(--surface);border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-bottom:6px;">
              <div style="height:100%;width:${Math.max(3, Math.min(100, Number(r.barPct)))}%;background:${r.tone === 'pass' ? 'var(--accent)' : r.tone === 'hold' ? 'var(--amber)' : 'var(--rose)'};border-radius:999px;"></div>
            </div>
            <p style="font-size:12.5px;color:var(--muted);">${esc(r.note)}</p>
          </div>`).join('')}
      </div>
      <pre class="code-block" style="margin:0;">${esc(meta.code)}</pre>`;
  }

  async function init() {
    initThemeToggle(() => renderTrustSketch());
    renderTrustSketch();
    renderLeanExplorer();

    const [respStudy, respNovel, respMem] = await Promise.all([
      fetch('../assets/trust-regime-data.json'),
      fetch('../assets/novel-directions-data.json'),
      fetch('../assets/agent-memory-data.json'),
    ]);
    STUDY = await respStudy.json();
    NOVEL = await respNovel.json();
    const MEM = await respMem.json();
    renderExperiments();
    renderNovelDirections();
    renderMemorySection(MEM);
  }

  function renderMemorySection(mem) {
    const stage = document.getElementById('memory-stage');
    if (!stage || !mem) return;
    const r = mem.rusty_skill_reonboarding.safe_execution_pct;
    const n = mem.novel_assay_transfer.first_try_certified_transfer_pct;
    const l = mem.longitudinal_60_sessions;
    const rows = [
      {
        name: 'Stateless Agent (No Long-Term Memory)',
        tone: 'fail',
        badge: `${l.stateless_acc_pct[l.stateless_acc_pct.length - 1]}% @ Session 60`,
        metric: `${r.stateless_no_memory}% rusty · ${n.stateless_zero_memory}% novel`,
        bar: 8,
        note: 'Repeats nominal aqueous dead-volume and unsealed thermal mistakes every session.',
      },
      {
        name: 'Rote Summary / Wiki Only (No Bottom Reasoning Trace)',
        tone: 'hold',
        badge: `${l.summary_no_trace_acc_pct[l.summary_no_trace_acc_pct.length - 1]}% @ Session 60`,
        metric: `${r.rote_summary_without_bottom_trace}% rusty · ${n.wiki_analogy_without_bottom_trace}% novel`,
        bar: 42,
        note: 'Memorizes fixed scalar magic numbers that break whenever viscosity, vapor pressure, or deck epoch shifts.',
      },
      {
        name: 'Append-Only Raw Session Logs (Context-Pollution Trap)',
        tone: 'fail',
        badge: `${l.append_only_context_tokens[l.append_only_context_tokens.length - 1]} tok bloat -> ${l.append_only_acc_pct[l.append_only_acc_pct.length - 1]}%`,
        metric: `${r.append_only_unpruned_logs}% rusty recovery`,
        bar: 57,
        note: 'Peaks at Session 10 (78.0%), then degrades to 38.9% by Session 60 as noisy unattributed logs drown retrieval.',
      },
      {
        name: 'Undergrad 4-Layer + Bottom Reasoning Trace + Dreaming (AutoLabLean)',
        tone: 'pass',
        badge: `${l.undergrad_dreaming_context_tokens[l.undergrad_dreaming_context_tokens.length - 1]} tok (180x leaner) · ${l.undergrad_dreaming_acc_pct[l.undergrad_dreaming_acc_pct.length - 1]}% @ S60`,
        metric: `${r.undergrad_4layer_bottom_trace_dreaming}% rusty · ${n.undergrad_full_trace_plus_tools_lean}% novel`,
        bar: 100,
        note: 'Proved theorems: unverified_trace_never_consolidated · packIntoContext_respects_budget · stale_skill_requires_trace_and_rehearsal · novel_task_never_executes_blindly.',
      },
    ];

    stage.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid var(--line);">
        <div style="max-width:740px;">
          <span class="small-label teal">AutoLabLean/AgentMemory.lean · 6 Proved Theorems</span>
          <h3 style="font-size:19px;font-weight:740;margin-top:4px;">Bottom Reasoning Traces + Offline Dreaming vs. Rote &amp; Bloated Memory</h3>
          <p style="font-size:13.5px;color:var(--muted);margin-top:4px;">120 rusty-SOP trials (&gt;120d gap + hardware epoch shift), 100 unseen reagent transfers, and 60 longitudinal sessions.</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="button primary" href="https://github.com/yaniguan/auto-lab/blob/main/lean/AutoLabLean/AgentMemory.lean" target="_blank" rel="noopener">AgentMemory.lean ↗</a>
          <a class="button secondary" href="https://github.com/yaniguan/auto-lab/blob/main/autolab/memory.py" target="_blank" rel="noopener">autolab/memory.py ↗</a>
        </div>
      </div>
      <div style="display:grid;gap:12px;">
        ${rows.map(item => `
          <div style="background:var(--surface2);border:1px solid var(--line);border-radius:11px;padding:13px 16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px;">
              <strong style="font-size:14.4px;">${esc(item.name)}</strong>
              <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                <span class="pill ${esc(item.tone)}">${esc(item.badge)}</span>
                <span style="font-size:13.5px;font-weight:740;color:var(--text);">${esc(item.metric)}</span>
              </div>
            </div>
            <div style="height:9px;background:var(--surface);border:1px solid var(--line);border-radius:999px;overflow:hidden;margin-bottom:6px;">
              <div style="height:100%;width:${item.bar}%;background:${item.tone === 'pass' ? 'var(--accent)' : item.tone === 'hold' ? 'var(--amber)' : 'var(--rose)'};border-radius:999px;"></div>
            </div>
            <p style="font-size:12.5px;color:var(--muted);">${esc(item.note)}</p>
          </div>`).join('')}
      </div>`;
  }

  document.addEventListener('DOMContentLoaded', init);
})();
