import AutoLabLean.Basic
/-!
# AutoLabLean.L6_Epistemic: Metacognitive & Conformal Trust Regime (`lab-ask-why`, `lab-decide`)

Formalizes the two L6 brain guardrails:
1. **`lab-ask-why`**: Symmetric evidence retrieval & Socratic abstention.
   - If maximum retrieval score `< noinfoThreshPermille`, the agent MUST abstain (`NOINFO`)
     rather than inventing rationales.
   - If both supporting and contradicting evidence exist (`supportHits > 0 ∧ contradictHits > 0`),
     proposing a bench action requires an explicit falsifiable discriminating check
     (`hasDiscriminatingExperiment = true`).
2. **`lab-decide`**: Finite-sample split conformal calibration & kNN distance gate.
   - Exact finite-sample order-statistic rank:
     `conformalRank n alphaPermille = ceil((n + 1) * (1000 - alphaPermille) / 1000)`.
   - Never clamps `k > n`: if `n == 0` or `conformalRank n alphaPermille > n`, MUST abstain.
   - Never extrapolates outside the calibrated kNN support: `knnDistPermille ≤ tauDistPermille`.
   - Clamps physical predictions `[loMilliLogS, hiMilliLogS]` inside `[physMin, physMax]`.
-/
namespace AutoLabLean

/-! ## 1. `lab-ask-why`: Epistemic Symmetry & NOINFO Abstention -/

structure EpistemicProbe where
  topScorePermille            : Nat
  noinfoThreshPermille        : Nat
  supportHits                 : Nat
  contradictHits              : Nat
  hasDiscriminatingExperiment : Bool
  deriving DecidableEq, Repr

/-- Declarative specification of a valid L6 epistemic probe. -/
structure EpistemicProbeOK (p : EpistemicProbe) : Prop where
  enoughEvidence    : p.noinfoThreshPermille ≤ p.topScorePermille
  nonEmptyRationale : 0 < p.supportHits + p.contradictHits
  contestedResolved : (0 < p.supportHits ∧ 0 < p.contradictHits) →
                        p.hasDiscriminatingExperiment = true

def checkAskWhy (p : EpistemicProbe) : Option RegimeViolation :=
  firstViolation
    [ (decide (p.noinfoThreshPermille ≤ p.topScorePermille),
        { repo := .labAskWhy, rule := "noinfo_abstain",
          detail := "retrieval evidence below NOINFO threshold; must abstain" }),
      (decide (0 < p.supportHits + p.contradictHits),
        { repo := .labAskWhy, rule := "nonempty_rationale",
          detail := "zero supporting or contradicting rationale sentences retrieved" }),
      (decide (¬(0 < p.supportHits ∧ 0 < p.contradictHits) ∨ p.hasDiscriminatingExperiment = true),
        { repo := .labAskWhy, rule := "contested_requires_experiment",
          detail := "both support and contradict evidence present without a discriminating experiment" }) ]

theorem checkAskWhy_ok_iff (p : EpistemicProbe) :
    checkAskWhy p = none ↔ EpistemicProbeOK p := by
  unfold checkAskWhy
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq]
  constructor
  · rintro ⟨h1, h2, h3⟩
    refine ⟨h1, h2, ?_⟩
    intro hcont
    rcases h3 with hneg | hexp
    · exact absurd hcont hneg
    · exact hexp
  · rintro ⟨h1, h2, h3⟩
    refine ⟨h1, h2, ?_⟩
    by_cases hc : 0 < p.supportHits ∧ 0 < p.contradictHits
    · exact Or.inr (h3 hc)
    · exact Or.inl hc

/-- Anti-confirmation theorem: a contested claim with opposing evidence cannot pass
    `checkAskWhy` unless it carries a discriminating experiment. -/
theorem contested_claim_requires_experiment (p : EpistemicProbe)
    (hok : checkAskWhy p = none)
    (hsup : 0 < p.supportHits) (hcon : 0 < p.contradictHits) :
    p.hasDiscriminatingExperiment = true :=
  ((checkAskWhy_ok_iff p).mp hok).contestedResolved ⟨hsup, hcon⟩

/-! ## 2. `lab-decide`: Finite-Sample Conformal Calibration & Trust Region -/

/-- Exact integer ceiling `ceil((n + 1) * (1000 - alphaPermille) / 1000)`. -/
def conformalRank (n alphaPermille : Nat) : Nat :=
  ((n + 1) * (1000 - alphaPermille) + 999) / 1000

structure ConformalQuery where
  nCalib           : Nat   -- calibration sample size `n`
  alphaPermille    : Nat   -- miscoverage target in per-mille (e.g., 100 for 90% coverage)
  knnDistPermille  : Nat   -- standardized kNN distance of candidate molecule
  tauDistPermille  : Nat   -- calibrated trust-region distance boundary
  loMilli          : Int   -- lower interval bound (10^-3 log mol/L)
  hiMilli          : Int   -- upper interval bound (10^-3 log mol/L)
  physMinMilli     : Int   -- physical solubility lower bound (e.g., -15000)
  physMaxMilli     : Int   -- physical solubility upper bound (e.g., +1750)
  deriving DecidableEq, Repr

/-- Declarative specification of a valid, in-domain conformal decision. -/
structure ConformalDecisionOK (q : ConformalQuery) : Prop where
  alphaValid      : 0 < q.alphaPermille ∧ q.alphaPermille < 1000
  calibNonEmpty   : 0 < q.nCalib
  rankWithinCalib : conformalRank q.nCalib q.alphaPermille ≤ q.nCalib
  insideTrustZone : q.knnDistPermille ≤ q.tauDistPermille
  intervalOrdered : q.loMilli ≤ q.hiMilli
  withinPhysMin   : q.physMinMilli ≤ q.loMilli
  withinPhysMax   : q.hiMilli ≤ q.physMaxMilli

def checkDecide (q : ConformalQuery) : Option RegimeViolation :=
  firstViolation
    [ (decide (0 < q.alphaPermille ∧ q.alphaPermille < 1000),
        { repo := .labDecide, rule := "alpha_in_open_unit_interval",
          detail := "alphaPermille must lie strictly in (0, 1000)" }),
      (decide (0 < q.nCalib),
        { repo := .labDecide, rule := "nonempty_calibration_set",
          detail := "calibration set size nCalib must be positive" }),
      (decide (conformalRank q.nCalib q.alphaPermille ≤ q.nCalib),
        { repo := .labDecide, rule := "finite_sample_conformal_rank",
          detail := "ceil((n+1)*(1-alpha)) exceeds nCalib; interval is infinite -> must ABSTAIN" }),
      (decide (q.knnDistPermille ≤ q.tauDistPermille),
        { repo := .labDecide, rule := "knn_trust_boundary",
          detail := "candidate distance exceeds calibrated kNN trust threshold -> must ABSTAIN" }),
      (decide (q.loMilli ≤ q.hiMilli),
        { repo := .labDecide, rule := "interval_well_ordered",
          detail := "lower conformal bound exceeds upper bound" }),
      (decide (q.physMinMilli ≤ q.loMilli ∧ q.hiMilli ≤ q.physMaxMilli),
        { repo := .labDecide, rule := "physical_solubility_bounds",
          detail := "prediction interval violates physical solubility range [physMin, physMax]" }) ]

theorem checkDecide_ok_iff (q : ConformalQuery) :
    checkDecide q = none ↔ ConformalDecisionOK q := by
  unfold checkDecide
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq]
  constructor
  · rintro ⟨h1, h2, h3, h4, h5, h6a, h6b⟩
    exact ⟨h1, h2, h3, h4, h5, h6a, h6b⟩
  · rintro ⟨h1, h2, h3, h4, h5, h6a, h6b⟩
    exact ⟨h1, h2, h3, h4, h5, h6a, h6b⟩

/-- Hard boundary theorem 1: Out-of-domain molecules (`knnDist > tauDist`) are
    provably NEVER accepted by `checkDecide`. -/
theorem out_of_domain_always_abstains (q : ConformalQuery)
    (hood : q.tauDistPermille < q.knnDistPermille) :
    checkDecide q ≠ none := by
  intro hok
  have hd := ((checkDecide_ok_iff q).mp hok).insideTrustZone
  omega

/-- Hard boundary theorem 2: Under-sized calibration sets (`k > n`, e.g. `n = 5` at 90% coverage)
    are provably NEVER silently clamped; `checkDecide` rejects them. -/
theorem undersized_calib_always_abstains (q : ConformalQuery)
    (hsmall : q.nCalib < conformalRank q.nCalib q.alphaPermille) :
    checkDecide q ≠ none := by
  intro hok
  have hr := ((checkDecide_ok_iff q).mp hok).rankWithinCalib
  omega

/-- Whenever `alphaPermille < 1000`, the finite-sample conformal rank is strictly `>= 1`. -/
theorem conformalRank_pos (n alphaPermille : Nat) (ha : alphaPermille < 1000) :
    1 ≤ conformalRank n alphaPermille := by
  unfold conformalRank
  have hpos : 0 < (n + 1) * (1000 - alphaPermille) :=
    Nat.mul_pos (Nat.succ_pos n) (by omega)
  omega

end AutoLabLean
