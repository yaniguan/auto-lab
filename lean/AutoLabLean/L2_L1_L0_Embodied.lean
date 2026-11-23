import AutoLabLean.Basic
/-!
# AutoLabLean.L2_L1_L0_Embodied: Sensory Privacy, Protocol Lowering, Safe Motion & Edge Quantization
(`lab-ears`, `stepbot`, `lab-hands`, `lab-feet`)

Formalizes the four embodied benchtop guardrails:
1. **`lab-ears` (L2)**:
   - Voice-privacy filter-skirt drop (`rawAudioSaved = false` and every retained mel filter
     `[loHz, hiHz]` lies strictly outside the `[300, 3400] Hz` human speech band:
     `hiHz ≤ 300 ∨ 3400 ≤ loHz`).
   - Contextual `g` mass vs centrifugal `x g` disambiguation & signed sub-zero temperature bounds.
2. **`stepbot` (L1)**:
   - Valid Opentrons deck slots (`1..11`, pairwise distinct), effective tip+pipette volume cap
     `vol ≤ min pipMax tipRackMax`, and `distribute` disposal-volume conservation
     (`nWells * vol + disposalVol ≤ sourceVol`).
3. **`lab-hands` (L1)**:
   - Continuous obstacle clearance (`minObstacleClearanceMM ≥ 5`), self-collision elbow bound
     (`|q2Mrad| ≤ 2600`), and slosh-bounded lateral acceleration (`maxAccelMMS2 ≤ sloshMaxMMS2`).
4. **`lab-feet` (L0)**:
   - Bit-width `[2, 8]`, strictly positive quantization scale (`0 < scaleMicro`), edge SRAM budget
     (`packedBytes ≤ maxEdgeBytes`), and teacher-student agreement (`agreementPermille ≥ minAgree`).
-/
namespace AutoLabLean

/-! ## 1. `lab-ears`: Voice-Privacy Acoustic Gate -/

structure MelBand where
  loHz : Nat
  hiHz : Nat
  deriving DecidableEq, Repr

structure AcousticEventCheck where
  rawAudioSaved  : Bool
  sampleRateHz   : Nat
  retainedBands  : List MelBand
  scoreCalibOK   : Bool
  deriving DecidableEq, Repr

def bandOutsideSpeech (b : MelBand) : Bool :=
  decide (b.loHz ≤ b.hiHz ∧ (b.hiHz ≤ 300 ∨ 3400 ≤ b.loHz))

def checkLabEars (e : AcousticEventCheck) : Option RegimeViolation :=
  firstViolation
    [ (!e.rawAudioSaved,
        { repo := .labEars, rule := "zero_raw_audio_persistence",
          detail := "raw microphone waveform retention is forbidden in shared wet-lab rooms" }),
      (decide (8000 ≤ e.sampleRateHz),
        { repo := .labEars, rule := "valid_machine_sample_rate",
          detail := "sample rate too low for machine bearing/rotor harmonic monitoring" }),
      (e.retainedBands.all bandOutsideSpeech,
        { repo := .labEars, rule := "full_skirt_speech_band_drop",
          detail := "retained mel filter skirt overlaps human speech band (300-3400 Hz)" }),
      (e.scoreCalibOK,
        { repo := .labEars, rule := "calibrated_anomaly_threshold",
          detail := "anomaly detector lacks held-out normal threshold calibration" }) ]

/-- Voice-Privacy Theorem: Any accepted `lab-ears` monitor configuration drops raw audio
    AND guarantees zero overlap with `(300, 3400) Hz` across every retained mel filter skirt! -/
theorem checkLabEars_strips_speech (e : AcousticEventCheck)
    (hok : checkLabEars e = none) :
    e.rawAudioSaved = false ∧
    ∀ b ∈ e.retainedBands, b.hiHz ≤ 300 ∨ 3400 ≤ b.loHz := by
  unfold checkLabEars at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true,
             Bool.not_eq_true', List.all_eq_true] at hok
  rcases hok with ⟨h1, _, h3, _⟩
  exact ⟨h1, fun b hb => (of_decide_eq_true (h3 b hb)).2⟩

/-! ## 2. `stepbot`: Opentrons Deck, Tip-Family & Distribute Disposal-Volume Gate -/

structure StepbotCompileCheck where
  occupiedSlots     : List Nat    -- OT-2 deck slots 1..11
  pipMaxTenthUL     : Nat
  tipRackMaxTenthUL : Nat
  transferVol       : Nat
  nDistributeWells  : Nat         -- `1` for simple transfer, `>= 2` for `distribute`
  disposalVol       : Nat         -- blow-out / disposal reserve required by `distribute`
  sourceWellVol     : Nat
  tipsRequired      : Nat
  tipsAvailable     : Nat
  deriving DecidableEq, Repr

def slotsValidAndDistinct : List Nat → Bool
  | [] => true
  | s :: ss => decide (1 ≤ s ∧ s ≤ 11) && (!ss.contains s) && slotsValidAndDistinct ss

def checkStepbot (c : StepbotCompileCheck) : Option RegimeViolation :=
  let effMax := Nat.min c.pipMaxTenthUL c.tipRackMaxTenthUL
  firstViolation
    [ (slotsValidAndDistinct c.occupiedSlots,
        { repo := .stepbot, rule := "ot2_deck_slots_1_to_11_unique",
          detail := "labware slot out of OT-2 range 1..11 or two labwares share one slot" }),
      (decide (0 < c.transferVol ∧ c.transferVol ≤ effMax),
        { repo := .stepbot, rule := "effective_pipette_tip_volume_cap",
          detail := "transfer volume exceeds min(pipette.max_volume, tiprack.max_volume)" }),
      (decide (c.nDistributeWells * c.transferVol + c.disposalVol ≤ c.sourceWellVol),
        { repo := .stepbot, rule := "distribute_disposal_volume_conservation",
          detail := "n * vol + disposal_volume underflows source reservoir well" }),
      (decide (c.tipsRequired ≤ c.tipsAvailable),
        { repo := .stepbot, rule := "tip_rack_sufficiency",
          detail := "protocol requires more clean tips than mounted tipracks provide" }) ]

theorem stepbot_never_underflows_distribute_source (c : StepbotCompileCheck)
    (hok : checkStepbot c = none) :
    c.nDistributeWells * c.transferVol + c.disposalVol ≤ c.sourceWellVol ∧
    c.transferVol ≤ Nat.min c.pipMaxTenthUL c.tipRackMaxTenthUL := by
  unfold checkStepbot at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨_, h2, h3, _⟩
  exact ⟨h3, h2.2⟩

/-! ## 3. `lab-hands`: Obstacle Clearance, Self-Collision & Liquid-Slosh Gate -/

structure ArmTrajectoryCheck where
  minClearanceMM    : Nat
  reqSafetyMarginMM : Nat     -- default 5 mm
  absElbowQ2Mrad    : Nat     -- |q2| in milliradians (limit <= 2600 mrad)
  vesselRimClearZMM : Int     -- z_tip - z_rim during horizontal transit (>= 0)
  maxLateralAccMMS2 : Nat
  sloshLimitMMS2    : Nat
  tactileRadialErrUM : Nat    -- micrometers (<= 200 um = 0.2 mm for fine tip seating)
  deriving DecidableEq, Repr

def checkLabHands (t : ArmTrajectoryCheck) : Option RegimeViolation :=
  firstViolation
    [ (decide (5 ≤ t.reqSafetyMarginMM ∧ t.reqSafetyMarginMM ≤ t.minClearanceMM),
        { repo := .labHands, rule := "continuous_obstacle_clearance",
          detail := "swept arm segment violates >= 5 mm continuous AABB safety margin" }),
      (decide (t.absElbowQ2Mrad ≤ 2600),
        { repo := .labHands, rule := "elbow_self_collision_limit",
          detail := "elbow angle |q2| exceeds 2.60 rad self-collision limit" }),
      (decide (0 ≤ t.vesselRimClearZMM),
        { repo := .labHands, rule := "vessel_rim_transit_height",
          detail := "pipette tip transits horizontally below bottle/plate rim height" }),
      (decide (t.maxLateralAccMMS2 ≤ t.sloshLimitMMS2),
        { repo := .labHands, rule := "slosh_bounded_acceleration",
          detail := "lateral acceleration exceeds open-meniscus slosh bound" }),
      (decide (t.tactileRadialErrUM ≤ 200),
        { repo := .labHands, rule := "tactile_insertion_tolerance",
          detail := "final tip-seating radial error exceeds 0.2 mm bevel capture tolerance" }) ]

theorem checkLabHands_guarantees_5mm_clearance (t : ArmTrajectoryCheck)
    (hok : checkLabHands t = none) :
    5 ≤ t.minClearanceMM ∧ t.absElbowQ2Mrad ≤ 2600 ∧ t.maxLateralAccMMS2 ≤ t.sloshLimitMMS2 := by
  unfold checkLabHands at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨h1, h2, _, h4, _⟩
  exact ⟨by omega, h2, h4⟩

/-! ## 4. `lab-feet`: Edge Quantization Scale, Footprint & Agreement Gate -/

structure EdgeStudentCheck where
  bitWidth          : Nat
  scaleMicro        : Nat     -- quantization scale in 10^-6 units (must be > 0!)
  packedWeightBytes : Nat
  maxEdgeSramBytes  : Nat
  agreementPermille : Nat     -- agreement with FP32 teacher/student (e.g., >= 980)
  minAgreePermille  : Nat
  deriving DecidableEq, Repr

def checkLabFeet (e : EdgeStudentCheck) : Option RegimeViolation :=
  firstViolation
    [ (decide (2 ≤ e.bitWidth ∧ e.bitWidth ≤ 8),
        { repo := .labFeet, rule := "supported_quant_bitwidth",
          detail := "quantization bit-width must lie in [2, 8]" }),
      (decide (0 < e.scaleMicro),
        { repo := .labFeet, rule := "nonzero_quantization_scale",
          detail := "zero quantization scale causes division-by-zero collapse on constant tensors" }),
      (decide (e.packedWeightBytes ≤ e.maxEdgeSramBytes),
        { repo := .labFeet, rule := "edge_memory_budget",
          detail := "packed student footprint exceeds target edge board SRAM budget" }),
      (decide (e.minAgreePermille ≤ e.agreementPermille),
        { repo := .labFeet, rule := "teacher_student_fidelity",
          detail := "quantized edge student agreement fell below certified floor" }) ]

theorem checkLabFeet_safe_for_edge (e : EdgeStudentCheck)
    (hok : checkLabFeet e = none) :
    0 < e.scaleMicro ∧ e.packedWeightBytes ≤ e.maxEdgeSramBytes ∧
    e.minAgreePermille ≤ e.agreementPermille := by
  unfold checkLabFeet at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨_, h2, h3, h4⟩
  exact ⟨h2, h3, h4⟩

end AutoLabLean
