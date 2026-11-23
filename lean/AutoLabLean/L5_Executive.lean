import AutoLabLean.Basic
/-!
# AutoLabLean.L5_Executive: Procurement, Scheduling & Ecosystem Gates
(`buy-or-make`, `labshift`, `lab-automation-atlas`)

Formalizes the three L5 executive planning guardrails:
1. **`buy-or-make`**:
   - Retrosynthetic disconnections must cleave only acyclic bonds (`bondIsAcyclic = true`,
     preventing cyclic lactam/lactone atom duplication) AND conserve exact heavy-atom counts
     (`sum(reactantAtoms) = targetAtoms + leavingGroupDelta`).
   - Budget filtering (`costCents ≤ budgetCents`) requires complete leaf pricing
     (`costComplete = true`), non-null price (`priceCents.isSome`), AND homogeneous `USD/g`
     normalization (`isUsdPerGram = true`).
   - Transitive license check across target stock, reaction lookup DB (`ORD` ShareAlike),
     and leaf building blocks.
2. **`labshift`**:
   - Multi-instrument jobshop intervals must satisfy `release ≤ start`, `start + dur ≤ deadline`,
     inter-step `minWait ≤ wait ≤ maxWait` (zero ruined incubations), `machineIdx < poolCap`,
     and pairwise mutual exclusion on every shared `(pool, machineIdx)`.
3. **`lab-automation-atlas`**:
   - External resources used in autonomous commercial training must satisfy `httpsOnly`,
     `spdxKnown`, `commercialTrainOK`, and `¬evalOnly`.
-/
namespace AutoLabLean

/-! ## 1. `buy-or-make`: Stoichiometric Atom Conservation, Strict Pricing & License Gate -/

structure AtomVec where
  c   : Nat
  n   : Nat
  o   : Nat
  s   : Nat
  hal : Nat
  deriving DecidableEq, Repr

def AtomVec.add (a b : AtomVec) : AtomVec :=
  { c := a.c + b.c, n := a.n + b.n, o := a.o + b.o, s := a.s + b.s, hal := a.hal + b.hal }

def sumAtoms : List AtomVec → AtomVec
  | [] => { c := 0, n := 0, o := 0, s := 0, hal := 0 }
  | x :: xs => AtomVec.add x (sumAtoms xs)

structure MakeOrBuyProposal where
  isDirectBuy      : Bool
  steps            : Nat
  maxSteps         : Nat
  bondIsAcyclic    : Bool            -- `true` for buyable or `!@`-constrained templates
  targetAtoms      : AtomVec
  leavingDelta     : AtomVec         -- leaving group added on hydrolysis/cleavage (e.g. H2O -> O=1)
  reactantAtoms    : List AtomVec
  allLeavesInStock : Bool
  costComplete     : Bool
  isUsdPerGram     : Bool
  priceCents       : Option Nat      -- `none` when public feed has no price (strict null!)
  budgetCents      : Option Nat      -- `some B` when budget filter active
  sourceLicenses   : List LicenseClass
  commercialMode   : Bool
  deriving DecidableEq, Repr

def routeStoichiometryOK (p : MakeOrBuyProposal) : Bool :=
  if p.isDirectBuy then
    p.steps == 0
  else
    decide (1 ≤ p.steps ∧ p.steps ≤ p.maxSteps) &&
    p.bondIsAcyclic &&
    p.allLeavesInStock &&
    decide (sumAtoms p.reactantAtoms = AtomVec.add p.targetAtoms p.leavingDelta)

def budgetPolicyOK (p : MakeOrBuyProposal) : Bool :=
  match p.budgetCents with
  | none => true
  | some B =>
    match p.priceCents with
    | none => false
    | some c => p.costComplete && p.isUsdPerGram && decide (c ≤ B)

def licensePolicyOK (p : MakeOrBuyProposal) : Bool :=
  if p.commercialMode then
    p.sourceLicenses.all LicenseClass.commercialTrainOK
  else
    p.sourceLicenses.all (fun l => l != .evalOnly)

structure MakeOrBuyOK (p : MakeOrBuyProposal) : Prop where
  stoichOK  : routeStoichiometryOK p = true
  budgetOK  : budgetPolicyOK p = true
  licenseOK : licensePolicyOK p = true

def checkBuyOrMake (p : MakeOrBuyProposal) : Option RegimeViolation :=
  firstViolation
    [ (routeStoichiometryOK p,
        { repo := .buyOrMake, rule := "acyclic_atom_balanced_route",
          detail := "route violates acyclic (!@) bond constraint, max_steps, stock leaves, or heavy-atom conservation" }),
      (budgetPolicyOK p,
        { repo := .buyOrMake, rule := "strict_homogeneous_budget",
          detail := "missing/incomplete price or non-USD/g unit cannot pass numeric budget gate" }),
      (licensePolicyOK p,
        { repo := .buyOrMake, rule := "transitive_license_gate",
          detail := "target, reaction-DB, or leaf source license incompatible with requested mode" }) ]

theorem checkBuyOrMake_ok_iff (p : MakeOrBuyProposal) :
    checkBuyOrMake p = none ↔ MakeOrBuyOK p := by
  unfold checkBuyOrMake
  simp only [firstViolation_cons, firstViolation_nil, and_true]
  constructor
  · rintro ⟨h1, h2, h3⟩; exact ⟨h1, h2, h3⟩
  · rintro ⟨h1, h2, h3⟩; exact ⟨h1, h2, h3⟩

/-- Hard boundary theorem: A synthesis disconnection that cleaves an endocyclic ring bond
    (`bondIsAcyclic = false`, as in `Analog-6` lactam cleavage) is provably rejected. -/
theorem ring_cleavage_rejected (p : MakeOrBuyProposal)
    (hmake : p.isDirectBuy = false) (hring : p.bondIsAcyclic = false) :
    checkBuyOrMake p ≠ none := by
  intro hok
  have hs := ((checkBuyOrMake_ok_iff p).mp hok).stoichOK
  simp [routeStoichiometryOK, hmake, hring] at hs

/-- Hard boundary theorem: An unpriced candidate (`priceCents = none`) or incomplete leaf cost
    (`costComplete = false`) can NEVER pass an active budget gate (`budgetCents = some B`). -/
theorem unpriced_never_passes_budget (p : MakeOrBuyProposal) (B : Nat)
    (hbud : p.budgetCents = some B) (hunpriced : p.priceCents = none ∨ p.costComplete = false) :
    checkBuyOrMake p ≠ none := by
  intro hok
  have hb := ((checkBuyOrMake_ok_iff p).mp hok).budgetOK
  rcases hunpriced with hp | hc
  · simp [budgetPolicyOK, hbud, hp] at hb
  · cases hpc : p.priceCents <;> simp [budgetPolicyOK, hbud, hpc, hc] at hb

/-! ## 2. `labshift`: Multi-Instrument Contended Schedule & Incubation Windows -/

structure ScheduledOp where
  opId       : Nat
  poolId     : Nat
  machineIdx : Nat
  poolCap    : Nat
  startMin   : Nat
  durMin     : Nat
  releaseMin : Nat
  deadlineMin : Nat
  deriving DecidableEq, Repr

def ScheduledOp.endMin (o : ScheduledOp) : Nat := o.startMin + o.durMin

/-- Inter-step precedence and incubation max-wait link `(predIdx, succIdx, minWait, maxWait)`. -/
structure WaitLink where
  predEndMin  : Nat
  succStartMin : Nat
  minWaitMin  : Nat
  maxWaitMin  : Nat
  deriving DecidableEq, Repr

def opBoundsOK (o : ScheduledOp) : Bool :=
  decide (0 < o.durMin ∧ o.machineIdx < o.poolCap ∧
          o.releaseMin ≤ o.startMin ∧ o.endMin ≤ o.deadlineMin)

def waitLinkOK (w : WaitLink) : Bool :=
  decide (w.predEndMin + w.minWaitMin ≤ w.succStartMin ∧
          w.succStartMin ≤ w.predEndMin + w.maxWaitMin)

def pairDisjointOK (a b : ScheduledOp) : Bool :=
  decide (a.opId = b.opId ∨ a.poolId ≠ b.poolId ∨ a.machineIdx ≠ b.machineIdx ∨
          a.endMin ≤ b.startMin ∨ b.endMin ≤ a.startMin)

def allPairsDisjoint (ops : List ScheduledOp) : Bool :=
  ops.all (fun a => ops.all (fun b => pairDisjointOK a b))

structure ScheduleOK (ops : List ScheduledOp) (links : List WaitLink) : Prop where
  boundsHold   : ∀ o ∈ ops, opBoundsOK o = true
  windowsHold  : ∀ w ∈ links, waitLinkOK w = true
  noCollisions : allPairsDisjoint ops = true

def checkSchedule (ops : List ScheduledOp) (links : List WaitLink) : Option RegimeViolation :=
  firstViolation
    [ (ops.all opBoundsOK,
        { repo := .labshift, rule := "op_release_deadline_capacity",
          detail := "scheduled operation violates positive duration, pool capacity, release time, or deadline" }),
      (links.all waitLinkOK,
        { repo := .labshift, rule := "inter_step_wait_window",
          detail := "inter-step delay violates [min_wait, max_wait] incubation window" }),
      (allPairsDisjoint ops,
        { repo := .labshift, rule := "machine_mutual_exclusion",
          detail := "two distinct operations overlap on the same instrument instance" }) ]

theorem checkSchedule_ok_iff (ops : List ScheduledOp) (links : List WaitLink) :
    checkSchedule ops links = none ↔ ScheduleOK ops links := by
  unfold checkSchedule
  simp only [firstViolation_cons, firstViolation_nil, and_true, List.all_eq_true]
  constructor
  · rintro ⟨h1, h2, h3⟩; exact ⟨h1, h2, h3⟩
  · rintro ⟨h1, h2, h3⟩; exact ⟨h1, h2, h3⟩

/-- Hard boundary theorem: Any schedule with a missed `max_wait` incubation window is rejected. -/
theorem missed_incubation_window_rejected (ops : List ScheduledOp) (links : List WaitLink)
    (w : WaitLink) (hw : w ∈ links) (hover : w.predEndMin + w.maxWaitMin < w.succStartMin) :
    checkSchedule ops links ≠ none := by
  intro hok
  have hwin := ((checkSchedule_ok_iff ops links).mp hok).windowsHold w hw
  unfold waitLinkOK at hwin
  have hdec := of_decide_eq_true hwin
  omega

/-! ## 3. `lab-automation-atlas`: Registry Security & Benchmark Contamination Gate -/

structure AtlasResource where
  httpsOnly    : Bool
  noPrivateIp  : Bool
  spdxKnown    : Bool
  licenseClass : LicenseClass
  forTraining  : Bool
  commercial   : Bool
  deriving DecidableEq, Repr

def checkAtlasResource (r : AtlasResource) : Option RegimeViolation :=
  firstViolation
    [ (r.httpsOnly && r.noPrivateIp,
        { repo := .labAutomationAtlas, rule := "https_ssrf_guard",
          detail := "external resource URL must use HTTPS and must not target private/loopback IPs" }),
      (r.spdxKnown,
        { repo := .labAutomationAtlas, rule := "explicit_spdx_license",
          detail := "resource lacks a verified SPDX or explicit custom license record" }),
      (decide (¬r.forTraining ∨ r.licenseClass ≠ .evalOnly),
        { repo := .labAutomationAtlas, rule := "eval_only_contamination_guard",
          detail := "eval_only benchmark (e.g. LAB-Bench) cannot enter training pipelines" }),
      (decide (¬(r.forTraining ∧ r.commercial) ∨ r.licenseClass.commercialTrainOK = true),
        { repo := .labAutomationAtlas, rule := "commercial_training_license_guard",
          detail := "non-permissive or non-commercial corpus blocked from commercial training" }) ]

theorem eval_only_blocked_from_training (r : AtlasResource)
    (htr : r.forTraining = true) (hev : r.licenseClass = .evalOnly) :
    checkAtlasResource r ≠ none := by
  intro hok
  unfold checkAtlasResource at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨_, _, h3, _⟩
  simp [htr, hev] at h3

end AutoLabLean
