import AutoLabLean.Basic
/-!
# AutoLabLean.L3_PostTrain: Leak-Free Splits, Anti-Hack RLVR Rewards, DAGs & Sequence Packing
(`labbench-posttrain`, `twinstep`, `labfill`)

Formalizes:
1. **`labbench-posttrain`**:
   - `SplitGuard`: pairwise disjoint group/scaffold/DOI IDs across `train`, `val`, `test`,
     plus strict separation from `canaryIds` (`LAB-Bench` contamination hard block).
   - `AntiHackReward`: multiplicative verification gate where format/reasoning bonuses are
     strictly `0` unless `coreScientificVerified = true`, `thinkTokens ≤ maxThinkTokens`,
     and `oracleFieldStripped = true`.
2. **`twinstep`**:
   - Causal dependency DAG (`(u, v)` edges across RAW/WAR/WAW liquid & stage barriers) and
     topological ordering check (`pos[u] < pos[v]`).
3. **`labfill`**:
   - Packed BF16 sequence bins (`offset + len ≤ binCap`, pairwise non-overlapping slices,
     and exact real-token count conservation).
-/
namespace AutoLabLean

/-! ## 1. `labbench-posttrain`: SplitGuard & Multiplicative Anti-Hack Reward -/

def listsDisjoint (xs ys : List Nat) : Bool :=
  xs.all (fun x => !ys.contains x)

structure SplitManifest where
  trainGroups  : List Nat
  valGroups    : List Nat
  testGroups   : List Nat
  canaryGroups : List Nat
  deriving DecidableEq, Repr

def checkSplitGuard (m : SplitManifest) : Option RegimeViolation :=
  firstViolation
    [ (listsDisjoint m.trainGroups m.valGroups &&
       listsDisjoint m.trainGroups m.testGroups &&
       listsDisjoint m.valGroups m.testGroups,
        { repo := .labbenchPosttrain, rule := "splitguard_zero_group_leak",
          detail := "shared molecule scaffold, DOI, or protocol group leaked across train/val/test" }),
      (listsDisjoint m.trainGroups m.canaryGroups &&
       listsDisjoint m.valGroups m.canaryGroups,
        { repo := .labbenchPosttrain, rule := "canary_eval_holdout",
          detail := "LAB-Bench canary item detected inside training or validation split" }) ]

structure RolloutRewardSpec where
  coreScientificVerified : Bool
  oracleFieldStripped    : Bool
  thinkTokens            : Nat
  maxThinkTokens         : Nat
  taskRewardPermille     : Nat
  formatBonusPermille    : Nat
  deriving DecidableEq, Repr

/-- Multiplicative anti-hack reward composer:
    unverified rollouts, oracle leaks, or `<think>` padding receive strictly `0`. -/
def gatedRewardPermille (r : RolloutRewardSpec) : Nat :=
  if r.coreScientificVerified && r.oracleFieldStripped && decide (r.thinkTokens ≤ r.maxThinkTokens) then
    r.taskRewardPermille + r.formatBonusPermille
  else
    0

def checkRolloutGate (r : RolloutRewardSpec) : Option RegimeViolation :=
  firstViolation
    [ (r.oracleFieldStripped,
        { repo := .labbenchPosttrain, rule := "no_oracle_prompt_leak",
          detail := "task record still exposes oracle_formulation or gold answer to policy" }),
      (decide (r.thinkTokens ≤ r.maxThinkTokens),
        { repo := .labbenchPosttrain, rule := "think_length_cap",
          detail := "scratchpad <think> length exceeds anti-verbosity cap" }),
      (r.coreScientificVerified,
        { repo := .labbenchPosttrain, rule := "core_verifier_passed",
          detail := "candidate rollout failed domain code/physics checker; bonus gated to 0" }) ]

/-- Anti-Reward-Hacking Theorem: Any rollout that fails the core scientific checker,
    exceeds `<think>` budget, or leaks the oracle field earns strictly `0` total reward
    regardless of how large `formatBonusPermille` is! -/
theorem unverified_rollout_gets_zero_reward (r : RolloutRewardSpec)
    (hfail : r.coreScientificVerified = false ∨
             r.oracleFieldStripped = false ∨
             r.maxThinkTokens < r.thinkTokens) :
    gatedRewardPermille r = 0 := by
  unfold gatedRewardPermille
  rcases hfail with hc | ho | ht
  · simp [hc]
  · simp [ho]
  · have hnd : decide (r.thinkTokens ≤ r.maxThinkTokens) = false :=
      decide_eq_false (by omega)
    simp [hnd]

/-- SplitGuard Zero-Leakage Theorem: if `checkSplitGuard m = none`, no group ID can appear
    in both `trainGroups` and `testGroups` (nor in `trainGroups` and `canaryGroups`). -/
theorem splitGuard_no_train_test_overlap (m : SplitManifest) (g : Nat)
    (hok : checkSplitGuard m = none)
    (htrain : g ∈ m.trainGroups) :
    g ∉ m.testGroups ∧ g ∉ m.canaryGroups := by
  unfold checkSplitGuard at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, Bool.and_eq_true,
             listsDisjoint, List.all_eq_true] at hok
  rcases hok with ⟨⟨⟨_, hnotTestB⟩, _⟩, ⟨hnotCanB, _⟩⟩
  have hnotTest := hnotTestB g htrain
  have hnotCan  := hnotCanB g htrain
  simp only [Bool.not_eq_true', List.contains_eq_mem, decide_eq_false_iff_not] at hnotTest hnotCan
  exact ⟨hnotTest, hnotCan⟩

/-! ## 2. `twinstep`: Causal Dependency DAG & Step-Ordering Gate -/

def indexOfStep (stepId : Nat) : List Nat → Option Nat
  | [] => none
  | x :: xs =>
    if x = stepId then some 0
    else (indexOfStep stepId xs).map (· + 1)

def dagEdgeSatisfied (order : List Nat) (edge : Nat × Nat) : Bool :=
  match indexOfStep edge.1 order, indexOfStep edge.2 order with
  | some pu, some pv => decide (pu < pv)
  | _, _ => false

def checkTwinStepOrder (nSteps : Nat) (order : List Nat) (dagEdges : List (Nat × Nat)) :
    Option RegimeViolation :=
  firstViolation
    [ (decide (order.length = nSteps) && (List.range nSteps).all (fun i => order.contains i),
        { repo := .twinstep, rule := "bijective_step_permutation",
          detail := "candidate ordering is not a complete permutation of protocol steps 0..n-1" }),
      (dagEdges.all (dagEdgeSatisfied order),
        { repo := .twinstep, rule := "causal_dag_satisfied",
          detail := "step order violates a RAW, WAR, or stage-barrier dependency edge" }) ]

theorem violated_dag_edge_rejected (nSteps : Nat) (order : List Nat)
    (dagEdges : List (Nat × Nat)) (e : Nat × Nat)
    (he : e ∈ dagEdges) (hbad : dagEdgeSatisfied order e = false) :
    checkTwinStepOrder nSteps order dagEdges ≠ none := by
  intro hok
  unfold checkTwinStepOrder at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true, List.all_eq_true] at hok
  have heok := hok.2 e he
  rw [hbad] at heok
  contradiction

/-! ## 3. `labfill`: Packed Sequence Non-Overlap & Token Conservation -/

structure PackedSlice where
  seqId  : Nat
  offset : Nat
  len    : Nat
  deriving DecidableEq, Repr

def slicesDisjoint (a b : PackedSlice) : Bool :=
  decide (a.seqId = b.seqId ∨ a.offset + a.len ≤ b.offset ∨ b.offset + b.len ≤ a.offset)

def sumSliceLens : List PackedSlice → Nat
  | [] => 0
  | s :: ss => s.len + sumSliceLens ss

def checkPackedBin (binCap expectedRealTokens : Nat) (slices : List PackedSlice) :
    Option RegimeViolation :=
  firstViolation
    [ (slices.all (fun s => decide (0 < s.len ∧ s.offset + s.len ≤ binCap)),
        { repo := .labfill, rule := "packed_slice_within_bin_cap",
          detail := "packed sequence slice has zero length or overflows bin capacity" }),
      (slices.all (fun a => slices.all (fun b => slicesDisjoint a b)),
        { repo := .labfill, rule := "packed_slices_non_overlapping",
          detail := "two distinct sequences overlap in packed token buffer (cross-sequence leak)" }),
      (decide (sumSliceLens slices = expectedRealTokens),
        { repo := .labfill, rule := "packed_real_token_conservation",
          detail := "packed bin token count does not match input protocol token sum" }) ]

theorem checkPackedBin_conserves_tokens (binCap expectedRealTokens : Nat)
    (slices : List PackedSlice)
    (hok : checkPackedBin binCap expectedRealTokens slices = none) :
    sumSliceLens slices = expectedRealTokens ∧
    ∀ s ∈ slices, s.offset + s.len ≤ binCap := by
  unfold checkPackedBin at hok
  simp only [firstViolation_cons, firstViolation_nil, and_true,
             List.all_eq_true, decide_eq_true_eq] at hok
  rcases hok with ⟨h1, _, h3⟩
  exact ⟨h3, fun s hs => (h1 s hs).2⟩

end AutoLabLean
