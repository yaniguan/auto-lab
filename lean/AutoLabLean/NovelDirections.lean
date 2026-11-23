import AutoLabLean.TrustRegime
/-!
# AutoLabLean.NovelDirections: Next-Generation Research Directions Beyond Static Pre-Gates

Synthesizing 2025-2026 frontier pain points across autonomous laboratories (`A-Lab` XRD
controversy, `Sakana v2` negative-result ambiguity, `La Agente Optima` mid-run sensor faults,
`Lean4Agent` workflow verification, and `plr-mcp`/`OpenLabAI` hardware MCP bottlenecks),
this module introduces and formally proves three completely new mechanisms:

1. **Diagnostic Epistemic Attribution (`AttributionOutcome`)**:
   Separates post-execution *hardware/control incompetence* (`.executionArtifact`) and
   *analytical non-identifiability* (`.ambiguousCharacterization`, the `A-Lab` XRD failure mode)
   from *Proof-Carrying Scientific Truth* (`.certifiedPositive` / `.certifiedNegative`).
2. **Stepped Frontier Calibration (`FrontierProbeSpec`)**:
   Resolves the exploration-vs-safety paradox of a static Trust Regime by permitting bounded,
   micro-scale (`<= 10 uL`), zero-synthesis (`isDirectBuy = true`) calibration stepping-stones
   exclusively inside a thin annular frontier shell `tau < d(x) <= (1 + eta) * tau`.
3. **Proof-Carrying Hardware-MCP Envelopes (`McpCapabilityEnvelope`)**:
   Eliminates per-run human approval bottlenecks on routine runs while mathematically blocking
   stale-state replay attacks and unapproved out-of-regime exceptions.
-/
namespace AutoLabLean

/-! ## Direction 1: Causal Blame Calculus & Proof-Carrying Negative Results -/

structure AssayTelemetry where
  preGateCertified          : Bool   -- Passed pre-execution AutoLabLean `verifyCycle`
  acousticNormal            : Bool   -- `lab-ears` anomaly score <= calibrated threshold
  scheduleWindowsRespected  : Bool   -- `labshift` actual wait <= max_wait
  tactileSeatedCleanly      : Bool   -- `lab-hands` radial error <= 0.2 mm
  posControlPassed          : Bool   -- On-plate positive control bracketed expected SNR
  negControlBlankClean      : Bool   -- On-plate negative blank showed zero carry-over
  spectralResidualPermille  : Nat    -- e.g. Rietveld R_wp or curve-fit residual
  maxResidualPermille       : Nat    -- Identifiability ceiling
  precursorOverlapPermille  : Nat    -- Unreacted precursor peak overlap (`A-Lab` guard!)
  maxOverlapPermille        : Nat    -- Maximum tolerable precursor overlap
  signalAboveActivityThresh : Bool   -- Whether measured biological/chemical effect >= hit floor
  deriving DecidableEq, Repr

inductive AttributionOutcome where
  | executionArtifact          -- Hardware, timing, or plate-control failure -> DO NOT update science model; retry!
  | ambiguousCharacterization  -- Clean run, but ambiguous XRD/spectrum -> DO NOT claim hit/null; run orthogonal assay!
  | certifiedPositive          -- Proof-carrying discovery hit -> admit to `assayfold` / `lab-decide`!
  | certifiedNegative          -- Proof-carrying negative result -> admit to `assayfold` / `lab-decide`!
  deriving DecidableEq, Repr

def executionClean (t : AssayTelemetry) : Bool :=
  t.preGateCertified &&
  t.acousticNormal &&
  t.scheduleWindowsRespected &&
  t.tactileSeatedCleanly &&
  t.posControlPassed &&
  t.negControlBlankClean

def characterizationIdentifiable (t : AssayTelemetry) : Bool :=
  decide (t.spectralResidualPermille ≤ t.maxResidualPermille ∧
          t.precursorOverlapPermille ≤ t.maxOverlapPermille)

/-- Exact 4-way causal attribution of an experimental wet-lab readout. -/
def attributeAssayOutcome (t : AssayTelemetry) : AttributionOutcome :=
  if !executionClean t then
    .executionArtifact
  else if !characterizationIdentifiable t then
    .ambiguousCharacterization
  else if t.signalAboveActivityThresh then
    .certifiedPositive
  else
    .certifiedNegative

/-- Whether an experimental readout is safe to admit into scientific memory (`assayfold` / BO / RLVR). -/
def admitToScientificMemory (o : AttributionOutcome) : Bool :=
  match o with
  | .certifiedPositive => true
  | .certifiedNegative => true
  | _                  => false

/-- Theorem D1.1 (Zero Memory Poisoning from Execution/Control Failures):
    Any run suffering an acoustic fault, missed incubation window, tactile slip, or failed
    on-plate control is classified `.executionArtifact` and NEVER poisons scientific memory! -/
theorem corrupted_run_never_poisons_memory (t : AssayTelemetry)
    (hfault : t.preGateCertified = false ∨ t.acousticNormal = false ∨
              t.scheduleWindowsRespected = false ∨ t.tactileSeatedCleanly = false ∨
              t.posControlPassed = false ∨ t.negControlBlankClean = false) :
    attributeAssayOutcome t = .executionArtifact ∧
    admitToScientificMemory (attributeAssayOutcome t) = false := by
  have hex : executionClean t = false := by
    unfold executionClean
    rcases hfault with h | h | h | h | h | h <;> simp [h]
  unfold attributeAssayOutcome
  simp [hex, admitToScientificMemory]

/-- Theorem D1.2 (Formal `A-Lab` Characterization Safeguard):
    Even when robotic execution and controls succeed cleanly, if precursor peak overlap or
    spectral fit residual exceeds its identifiability bound, the agent can NEVER claim
    `.certifiedPositive` (nor `.certifiedNegative`)! -/
theorem unidentifiable_spectrum_never_certified (t : AssayTelemetry)
    (ham : t.maxResidualPermille < t.spectralResidualPermille ∨
           t.maxOverlapPermille < t.precursorOverlapPermille) :
    attributeAssayOutcome t ≠ .certifiedPositive ∧
    attributeAssayOutcome t ≠ .certifiedNegative := by
  have hid : characterizationIdentifiable t = false := by
    unfold characterizationIdentifiable
    apply decide_eq_false
    rcases ham with hr | ho <;> omega
  unfold attributeAssayOutcome
  cases executionClean t <;> simp [hid]

/-- Theorem D1.3 (Soundness of Proof-Carrying Negative Results):
    Every `.certifiedNegative` admitted into scientific memory is guaranteed to have passed
    all 6 execution/control checks AND both analytical identifiability bounds! -/
theorem certified_negative_sound (t : AssayTelemetry)
    (hneg : attributeAssayOutcome t = .certifiedNegative) :
    executionClean t = true ∧
    t.spectralResidualPermille ≤ t.maxResidualPermille ∧
    t.precursorOverlapPermille ≤ t.maxOverlapPermille ∧
    t.signalAboveActivityThresh = false := by
  unfold attributeAssayOutcome at hneg
  cases hex : executionClean t with
  | false => simp [hex] at hneg
  | true =>
    simp only [hex] at hneg
    cases hid : characterizationIdentifiable t with
    | false => simp [hid] at hneg
    | true =>
      simp only [hid] at hneg
      cases hsig : t.signalAboveActivityThresh with
      | true => simp [hsig] at hneg
      | false =>
        unfold characterizationIdentifiable at hid
        have ⟨hr, ho⟩ := of_decide_eq_true hid
        exact ⟨rfl, hr, ho, rfl⟩

/-! ## Direction 2: Stepped Frontier Calibration (Active Trust-Boundary Expansion) -/

inductive CampaignMode where
  | exploitation           -- Normal synthesis/production run: must stay strictly <= tau
  | frontierCalibration    -- Micro-scale stepping-stone probe: allowed in (tau, tau * (1 + eta))
  deriving DecidableEq, Repr

structure FrontierProbeSpec where
  mode                  : CampaignMode
  knnDistPermille       : Nat
  tauPermille           : Nat
  etaStepPermille       : Nat    -- e.g. 250 for a +25% annular stepping-stone shell
  maxEtaPermille        : Nat    -- hard cap on shell width (e.g. 350 = +35%)
  assayVolTenthUL       : Nat
  microVolCapTenthUL    : Nat    -- e.g. 100 (= 10.0 uL micro-assay cap for frontier probes)
  isDirectBuy           : Bool   -- Frontier probes must use cheap in-stock compounds (0 synthesis steps)
  usedAsPointPrediction : Bool   -- Must be `false` on frontier probes (calibration measurement only!)
  deriving DecidableEq, Repr

def frontierOuterRadius (tau etaPermille : Nat) : Nat :=
  tau + (tau * etaPermille) / 1000

def checkFrontierAction (p : FrontierProbeSpec) : Option RegimeViolation :=
  match p.mode with
  | .exploitation =>
    firstViolation
      [ (decide (p.knnDistPermille ≤ p.tauPermille),
          { repo := .labDecide, rule := "exploitation_inside_tau",
            detail := "exploitation run exceeds current calibrated trust radius tau" }) ]
  | .frontierCalibration =>
    firstViolation
      [ (decide (p.etaStepPermille ≤ p.maxEtaPermille),
          { repo := .labDecide, rule := "bounded_annular_shell_width",
            detail := "frontier stepping-stone expansion ratio eta exceeds safe shell cap" }),
        (decide (p.knnDistPermille ≤ frontierOuterRadius p.tauPermille p.etaStepPermille),
          { repo := .labDecide, rule := "within_stepping_stone_shell",
            detail := "candidate lies in deep OOD beyond the (1 + eta) * tau stepping-stone shell" }),
        (decide (p.assayVolTenthUL ≤ p.microVolCapTenthUL),
          { repo := .labRehearsal, rule := "frontier_micro_volume_cap",
            detail := "frontier calibration probe exceeds micro-scale reagent volume cap" }),
        (p.isDirectBuy,
          { repo := .buyOrMake, rule := "frontier_requires_direct_stock",
            detail := "multi-step synthesis forbidden outside calibrated trust zone; probe stock leaves first" }),
        (!p.usedAsPointPrediction,
          { repo := .labDecide, rule := "frontier_calibration_only",
            detail := "frontier probe cannot be consumed as a calibrated point prediction prior to assay" }) ]

/-- Theorem D2.1 (Deep OOD Blocked in All Modes):
    Any candidate beyond `frontierOuterRadius tau eta` is rejected in BOTH exploitation
    and frontier-calibration modes — blind leaps into deep OOD are impossible! -/
theorem deep_ood_always_blocked (p : FrontierProbeSpec)
    (hdeep : frontierOuterRadius p.tauPermille p.etaStepPermille < p.knnDistPermille) :
    checkFrontierAction p ≠ none := by
  intro hok
  cases hm : p.mode with
  | exploitation =>
    simp only [checkFrontierAction, hm, firstViolation_cons, firstViolation_nil,
               and_true, decide_eq_true_eq] at hok
    unfold frontierOuterRadius at hdeep
    omega
  | frontierCalibration =>
    simp only [checkFrontierAction, hm, firstViolation_cons, firstViolation_nil,
               and_true, decide_eq_true_eq] at hok
    rcases hok with ⟨_, hshell, _, _, _⟩
    omega

/-- Theorem D2.2 (Safe Micro-Scale Stepping-Stone Guarantee):
    Whenever an out-of-trust candidate (`tau < knnDist`) is accepted by `checkFrontierAction`,
    it is mathematically guaranteed to be in `.frontierCalibration` mode, within `(1+eta)*tau`,
    micro-volume capped (`assayVol ≤ microVolCap`), directly purchasable, and flagged calibration-only! -/
theorem accepted_outside_tau_is_bounded_probe (p : FrontierProbeSpec)
    (hout : p.tauPermille < p.knnDistPermille)
    (hok : checkFrontierAction p = none) :
    p.mode = .frontierCalibration ∧
    p.knnDistPermille ≤ frontierOuterRadius p.tauPermille p.etaStepPermille ∧
    p.assayVolTenthUL ≤ p.microVolCapTenthUL ∧
    p.isDirectBuy = true ∧
    p.usedAsPointPrediction = false := by
  cases hm : p.mode with
  | exploitation =>
    simp only [checkFrontierAction, hm, firstViolation_cons, firstViolation_nil,
               and_true, decide_eq_true_eq] at hok
    omega
  | frontierCalibration =>
    simp only [checkFrontierAction, hm, firstViolation_cons, firstViolation_nil,
               and_true, decide_eq_true_eq, Bool.not_eq_true'] at hok
    rcases hok with ⟨_, hshell, hvol, hbuy, hcal⟩
    exact ⟨rfl, hshell, hvol, hbuy, hcal⟩

/-! ## Direction 3: Proof-Carrying Hardware-MCP Envelopes (`Lean-MCP`) -/

structure McpHardwareEnvelope where
  tokenEpoch          : Nat    -- Deck state epoch bound into the token
  currentDeckEpoch    : Nat    -- Live physical deck state epoch
  leanProofValid      : Bool   -- Verified by `AutoLabLean`
  isFrontierException : Bool   -- Requests manual override outside standard spec
  humanSupervisorSign : Bool   -- Explicit cryptographic co-signature by human operator
  deriving DecidableEq, Repr

def checkMcpHardwareCall (e : McpHardwareEnvelope) : Option RegimeViolation :=
  firstViolation
    [ (decide (e.tokenEpoch == e.currentDeckEpoch),
        { repo := .stepbot, rule := "mcp_epoch_freshness",
          detail := "stale MCP capability token replayed against an updated deck state" }),
      (decide ((e.leanProofValid && !e.isFrontierException) ∨
               (e.isFrontierException && e.humanSupervisorSign)),
        { repo := .labVerify, rule := "mcp_proof_or_cosigned_exception",
          detail := "hardware MCP call lacks both a valid Lean proof certificate and human co-signature" }) ]

/-- Theorem D3.1 (Zero-Click Autonomy Inside Regime, Mandatory Human Gate Outside):
    A hardware MCP call with `humanSupervisorSign = false` is permitted to execute
    if and only if `tokenEpoch == currentDeckEpoch`, `leanProofValid = true`, and
    `isFrontierException = false`! -/
theorem autonomous_mcp_requires_fresh_lean_proof (e : McpHardwareEnvelope)
    (hnoHuman : e.humanSupervisorSign = false) :
    checkMcpHardwareCall e = none ↔
      (e.tokenEpoch = e.currentDeckEpoch ∧ e.leanProofValid = true ∧ e.isFrontierException = false) := by
  unfold checkMcpHardwareCall
  simp [firstViolation_cons, firstViolation_nil, hnoHuman]

-- Compile-time `#guard` witnesses for all 3 novel directions!
#guard attributeAssayOutcome
         { preGateCertified := true, acousticNormal := false, scheduleWindowsRespected := true,
           tactileSeatedCleanly := true, posControlPassed := true, negControlBlankClean := true,
           spectralResidualPermille := 40, maxResidualPermille := 100,
           precursorOverlapPermille := 30, maxOverlapPermille := 150, signalAboveActivityThresh := false }
       == .executionArtifact

#guard attributeAssayOutcome
         { preGateCertified := true, acousticNormal := true, scheduleWindowsRespected := true,
           tactileSeatedCleanly := true, posControlPassed := true, negControlBlankClean := true,
           spectralResidualPermille := 80, maxResidualPermille := 100,
           precursorOverlapPermille := 420, maxOverlapPermille := 150, signalAboveActivityThresh := true }
       == .ambiguousCharacterization

#guard attributeAssayOutcome
         { preGateCertified := true, acousticNormal := true, scheduleWindowsRespected := true,
           tactileSeatedCleanly := true, posControlPassed := true, negControlBlankClean := true,
           spectralResidualPermille := 45, maxResidualPermille := 100,
           precursorOverlapPermille := 35, maxOverlapPermille := 150, signalAboveActivityThresh := false }
       == .certifiedNegative

#guard (checkFrontierAction
         { mode := .frontierCalibration, knnDistPermille := 900, tauPermille := 758,
           etaStepPermille := 250, maxEtaPermille := 350, assayVolTenthUL := 80,
           microVolCapTenthUL := 100, isDirectBuy := true, usedAsPointPrediction := false }).isNone == true

#guard (checkFrontierAction
         { mode := .frontierCalibration, knnDistPermille := 1400, tauPermille := 758,
           etaStepPermille := 250, maxEtaPermille := 350, assayVolTenthUL := 80,
           microVolCapTenthUL := 100, isDirectBuy := true, usedAsPointPrediction := false }).isSome == true

end AutoLabLean
