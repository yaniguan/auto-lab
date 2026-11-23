/-!
# AutoLabLean.Basic: Shared Types & Fixed-Point Physical Units Across L6-L0

Every physical, statistical, and economic quantity in the Auto-Lab Trust Regime
is represented in exact integer fixed-point arithmetic (per-mille `10^-3`, tenths of
a microliter `0.1 uL`, milligrams, seconds, milliradians, integer cents) so that
every guardrail is decidable without IEEE-754 rounding drift.
-/
namespace AutoLabLean

/-- Neural / embodied layer identifier from L6 (Brain) down to L0 (Edge Feet). -/
inductive LayerId where
  | L6 | L5 | L4 | L3 | L2 | L1 | L0
  deriving DecidableEq, Repr

/-- Canonical repository identifier for all 15 Auto-Lab core repositories. -/
inductive RepoId where
  | labAskWhy
  | labDecide
  | buyOrMake
  | labshift
  | labAutomationAtlas
  | labRehearsal
  | labVerify
  | labAttrib
  | labbenchPosttrain
  | twinstep
  | labfill
  | labEars
  | stepbot
  | labHands
  | labFeet
  deriving DecidableEq, Repr

def RepoId.name : RepoId → String
  | .labAskWhy          => "lab-ask-why"
  | .labDecide          => "lab-decide"
  | .buyOrMake          => "buy-or-make"
  | .labshift           => "labshift"
  | .labAutomationAtlas => "lab-automation-atlas"
  | .labRehearsal       => "lab-rehearsal"
  | .labVerify          => "lab-verify"
  | .labAttrib          => "lab-attrib"
  | .labbenchPosttrain  => "labbench-posttrain"
  | .twinstep           => "twinstep"
  | .labfill            => "labfill"
  | .labEars            => "lab-ears"
  | .stepbot            => "stepbot"
  | .labHands           => "lab-hands"
  | .labFeet            => "lab-feet"

def RepoId.layer : RepoId → LayerId
  | .labAskWhy          => .L6
  | .labDecide          => .L6
  | .buyOrMake          => .L5
  | .labshift           => .L5
  | .labAutomationAtlas => .L5
  | .labRehearsal       => .L4
  | .labVerify          => .L4
  | .labAttrib          => .L4
  | .labbenchPosttrain  => .L3
  | .twinstep           => .L3
  | .labfill            => .L3
  | .labEars            => .L2
  | .stepbot            => .L1
  | .labHands           => .L1
  | .labFeet            => .L0

/-- Structured boundary violation reporting the exact repository, rule, and detail. -/
structure RegimeViolation where
  repo   : RepoId
  rule   : String
  detail : String
  deriving DecidableEq, Repr

def RegimeViolation.format (v : RegimeViolation) : String :=
  s!"[{v.repo.name} :: {v.rule}] {v.detail}"

/-- License posture harmonized across `buy-or-make`, `lab-automation-atlas`,
    `lab-rehearsal`, `lab-verify`, and `assayfold`. -/
inductive LicenseClass where
  | permissive      -- MIT, BSD-3-Clause, Apache-2.0, CC0, CC-BY-4.0
  | shareAlike      -- CC-BY-SA-4.0 (e.g., ORD, Spider, LAB-Bench)
  | nonCommercial   -- CC-BY-NC-*, academic non-commercial corpora
  | evalOnly        -- Benchmark canary corpora forbidden in training
  | customTerms     -- Unpriced vendor feeds or unlicensed repositories
  deriving DecidableEq, Repr

/-- Whether a license class permits unrestricted commercial autonomous training/synthesis. -/
def LicenseClass.commercialTrainOK : LicenseClass → Bool
  | .permissive => true
  | _           => false

/-- Return the first violation in a list of `(holds, violation)` checks. -/
def firstViolation : List (Bool × RegimeViolation) → Option RegimeViolation
  | [] => none
  | (true, _) :: rest => firstViolation rest
  | (false, v) :: _ => some v

@[simp] theorem firstViolation_nil : firstViolation [] = none := rfl

@[simp] theorem firstViolation_cons (b : Bool) (v : RegimeViolation)
    (rest : List (Bool × RegimeViolation)) :
    firstViolation ((b, v) :: rest) = none ↔ b = true ∧ firstViolation rest = none := by
  cases b <;> simp [firstViolation]

theorem firstViolation_none_iff (checks : List (Bool × RegimeViolation)) :
    firstViolation checks = none ↔ ∀ p ∈ checks, p.1 = true := by
  induction checks with
  | nil => simp [firstViolation]
  | cons hd tl ih =>
    rcases hd with ⟨b, v⟩
    cases b with
    | false =>
      simp [firstViolation]
    | true =>
      simp [firstViolation, ih]

end AutoLabLean
