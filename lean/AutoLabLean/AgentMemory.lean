import AutoLabLean.NovelDirections
/-!
# AutoLabLean.AgentMemory: Formal 4-Layer "Undergrad" Memory, Bottom Reasoning Traces & Dreaming

Inspired by Anthropic's *The Components of Agent Memory* (Transcripts -> Memory Notes ->
Structured Concept Wikis -> Bounded Injected Context + offline *Dreaming* consolidation)
and modeled after how a well-trained undergraduate laboratory researcher rapidly:
1. **Re-masters rusty protocols** untouched for months by re-reading causal *Bottom Reasoning Traces*
   and running a micro-rehearsal calibration (`checkSkillReadiness`);
2. **Onboards onto brand-new assays/instruments** via structural analogy to existing `ConceptWiki`
   schemas, bottom-trace first-principles transfer, and tool lookup (`checkNovelOnboarding`);
3. **Avoids context pollution and memory poisoning** via Lean-gated offline *Dreaming*
   (`dreamConsolidate`), proving strict token-budget compliance and zero uncertified write-back.
-/
namespace AutoLabLean

/-! ## Layer 0 -> Layer 3 Data Structures & Offline Dreaming Consolidation -/

/-- Layer-0 / Layer-1 candidate memory note distilled from an episodic transcript and its
    causal **Bottom Reasoning Trace** (`Symptom -> FirstPrincipleLaw -> CausalChain -> Fix`). -/
structure MemoryCandidate where
  noteId               : Nat
  conceptId            : Nat
  attributionCertified : Bool   -- Verified via `admitToScientificMemory` (never hardware noise!)
  hasFirstPrincipleLaw : Bool   -- Bottom trace states governing physical/chemical/statistical law
  hasCausalMechanism   : Bool   -- Bottom trace links symptom -> mechanism -> actionable boundary
  contradictedByNewer  : Bool   -- Flagged stale/wrong during offline Dreaming cross-check
  saliencePermille     : Nat    -- Predicted future-session utility ("memory as prediction")
  minSaliencePermille  : Nat    -- Minimum salience threshold for long-term retention
  tokenCost            : Nat    -- Prompt token footprint when injected into Layer 3
  deriving DecidableEq, Repr

/-- Exact predicate determining whether a memory candidate survives offline *Dreaming*. -/
def traceConsolidatable (m : MemoryCandidate) : Bool :=
  m.attributionCertified &&
  m.hasFirstPrincipleLaw &&
  m.hasCausalMechanism &&
  (!m.contradictedByNewer) &&
  decide (m.minSaliencePermille ≤ m.saliencePermille)

def sumMemoryTokens : List MemoryCandidate → Nat
  | []      => 0
  | m :: ms => m.tokenCost + sumMemoryTokens ms

/-- Greedy token-bounded packer loading consolidated notes into Layer-3 `InjectedBenchContext`. -/
def packIntoContext (budgetTokens : Nat) : List MemoryCandidate → List MemoryCandidate
  | [] => []
  | m :: rest =>
    if traceConsolidatable m then
      if _h : m.tokenCost ≤ budgetTokens then
        m :: packIntoContext (budgetTokens - m.tokenCost) rest
      else
        packIntoContext budgetTokens rest
    else
      packIntoContext budgetTokens rest

/-- Theorem M1 (Zero Poisoning or Rote Hallucination in Consolidated Memory):
    Any candidate lacking Lean attribution certification, lacking a bottom first-principle
    causal trace, or contradicted during Dreaming is NEVER admitted into active context. -/
theorem unverified_trace_never_consolidated (m : MemoryCandidate)
    (hbad : m.attributionCertified = false ∨ m.hasFirstPrincipleLaw = false ∨
            m.hasCausalMechanism = false ∨ m.contradictedByNewer = true) :
    traceConsolidatable m = false := by
  unfold traceConsolidatable
  rcases hbad with h | h | h | h <;> simp [h]

/-- Theorem M2 (Strict Context-Window Budget Bound — Anti-Context-Pollution):
    Offline Dreaming + `packIntoContext` mathematically guarantees that injected Layer-3
    memory never exceeds `budgetTokens`, preventing multi-session context bloat. -/
theorem packIntoContext_respects_budget (budgetTokens : Nat) (cands : List MemoryCandidate) :
    sumMemoryTokens (packIntoContext budgetTokens cands) ≤ budgetTokens := by
  induction cands generalizing budgetTokens with
  | nil =>
    simp [packIntoContext, sumMemoryTokens]
  | cons m rest ih =>
    unfold packIntoContext
    cases hok : traceConsolidatable m with
    | false =>
      simp only [Bool.false_eq_true, ↓reduceIte]
      exact ih budgetTokens
    | true =>
      simp only [↓reduceIte]
      by_cases hfit : m.tokenCost ≤ budgetTokens
      · simp only [hfit, ↓reduceDIte, sumMemoryTokens]
        have hsub := ih (budgetTokens - m.tokenCost)
        omega
      · simp only [hfit, ↓reduceDIte]
        exact ih budgetTokens

/-- Theorem M3 (Soundness of Every Injected Memory Note):
    Every single note present in `packIntoContext budgetTokens cands` is guaranteed
    to satisfy `traceConsolidatable = true`. -/
theorem packIntoContext_all_certified (budgetTokens : Nat) (cands : List MemoryCandidate) :
    ∀ m ∈ packIntoContext budgetTokens cands, traceConsolidatable m = true := by
  induction cands generalizing budgetTokens with
  | nil =>
    intro m hm
    simp [packIntoContext] at hm
  | cons hd tl ih =>
    intro m hm
    unfold packIntoContext at hm
    cases hok : traceConsolidatable hd with
    | false =>
      simp only [hok, Bool.false_eq_true, ↓reduceIte] at hm
      exact ih budgetTokens m hm
    | true =>
      simp only [hok, ↓reduceIte] at hm
      by_cases hfit : hd.tokenCost ≤ budgetTokens
      · simp only [hfit, ↓reduceDIte, List.mem_cons] at hm
        rcases hm with rfl | hmem
        · exact hok
        · exact ih (budgetTokens - hd.tokenCost) m hmem
      · simp only [hfit, ↓reduceDIte] at hm
        exact ih budgetTokens m hm

/-! ## Rusty-Skill Re-Onboarding (Returning to an Old Instrument / SOP After Months) -/

structure SkillInvocationCheck where
  daysSinceLastUse    : Nat    -- Elapsed days since this SOP/instrument was last run
  staleThresholdDays  : Nat    -- e.g. 30 days forgetting-curve threshold
  calibratedDeckEpoch : Nat    -- Hardware calibration epoch when note was written
  currentDeckEpoch    : Nat    -- Current physical deck epoch
  bottomTraceReviewed : Bool   -- Agent retrieved & read Layer-0 causal Bottom Reasoning Trace
  microRehearsalPass  : Bool   -- Agent passed fresh `lab-rehearsal` twin/micro check
  deriving DecidableEq, Repr

def isSkillRusty (s : SkillInvocationCheck) : Bool :=
  decide (s.staleThresholdDays < s.daysSinceLastUse ∨
          s.calibratedDeckEpoch ≠ s.currentDeckEpoch)

def checkSkillReadiness (s : SkillInvocationCheck) : Option RegimeViolation :=
  if !isSkillRusty s then
    none
  else
    firstViolation
      [ (s.bottomTraceReviewed,
          { repo := .labRehearsal, rule := "rusty_skill_requires_bottom_trace",
            detail := "stale or epoch-shifted skill invoked without reviewing causal bottom reasoning trace" }),
        (s.microRehearsalPass,
          { repo := .labRehearsal, rule := "rusty_skill_requires_micro_rehearsal",
            detail := "stale or epoch-shifted skill invoked without passing fresh twin micro-rehearsal" }) ]

/-- Theorem M4 (Safe Re-Onboarding of Rusty Skills):
    Whenever an SOP has gone untouched beyond `staleThresholdDays`, full-scale execution is
    permitted ONLY if the agent both reviewed its causal Bottom Reasoning Trace AND passed
    a fresh micro-rehearsal calibration! -/
theorem stale_skill_requires_trace_and_rehearsal (s : SkillInvocationCheck)
    (hstale : s.staleThresholdDays < s.daysSinceLastUse)
    (hok : checkSkillReadiness s = none) :
    s.bottomTraceReviewed = true ∧ s.microRehearsalPass = true := by
  have hrust : isSkillRusty s = true := by
    unfold isSkillRusty
    exact decide_eq_true (Or.inl hstale)
  unfold checkSkillReadiness at hok
  simp only [hrust, Bool.not_true, Bool.false_eq_true, ↓reduceIte,
             firstViolation_cons, firstViolation_nil, and_true] at hok
  exact hok

/-- Theorem M5 (Hardware-Epoch Shift Forces Re-Calibration):
    If physical deck calibration changed (`calibratedDeckEpoch ≠ currentDeckEpoch`),
    cached procedural habits cannot execute blindly without bottom-trace review + rehearsal. -/
theorem epoch_shifted_skill_requires_rehearsal (s : SkillInvocationCheck)
    (hshift : s.calibratedDeckEpoch ≠ s.currentDeckEpoch)
    (hok : checkSkillReadiness s = none) :
    s.bottomTraceReviewed = true ∧ s.microRehearsalPass = true := by
  have hrust : isSkillRusty s = true := by
    unfold isSkillRusty
    exact decide_eq_true (Or.inr hshift)
  unfold checkSkillReadiness at hok
  simp only [hrust, Bool.not_true, Bool.false_eq_true, ↓reduceIte,
             firstViolation_cons, firstViolation_nil, and_true] at hok
  exact hok

/-! ## Zero-Shot / Few-Shot Novel-Concept Onboarding ("Undergrad Facing Something New") -/

structure NovelOnboardingCheck where
  seenBefore              : Bool   -- Whether exact assay/instrument exists in procedural memory
  analogySimPermille      : Nat    -- Structural analogy score to nearest `ConceptWiki` node
  minAnalogyPermille      : Nat    -- Minimum structural isomorphism threshold (e.g. 600)
  analogBottomTraceLoaded : Bool   -- Loaded causal derivation from analogous concept's bottom trace
  toolSpecsQueried        : Bool   -- Grounded unknown parameters via `atlas` / `ask-why` / `decide`
  twinDryRunCertified     : Bool   -- Adapted protocol passed `lab-rehearsal` + `lab-verify`
  deriving DecidableEq, Repr

def checkNovelOnboarding (n : NovelOnboardingCheck) : Option RegimeViolation :=
  if n.seenBefore then
    firstViolation
      [ (n.twinDryRunCertified,
          { repo := .labRehearsal, rule := "known_skill_twin_verified",
            detail := "known SOP failed pre-run digital twin check" }) ]
  else
    firstViolation
      [ (decide (n.minAnalogyPermille ≤ n.analogySimPermille),
          { repo := .labAskWhy, rule := "novel_requires_structural_analogy",
            detail := "unseen assay lacks structural analogy in ConceptWiki; escalate or probe micro-scale" }),
        (n.analogBottomTraceLoaded,
          { repo := .labAskWhy, rule := "novel_requires_bottom_reasoning_trace",
            detail := "unseen assay attempted without loading causal bottom reasoning trace of nearest concept" }),
        (n.toolSpecsQueried,
          { repo := .labAutomationAtlas, rule := "novel_requires_tool_spec_lookup",
            detail := "unseen assay attempted without querying instrument/reagent specs via lab tools" }),
        (n.twinDryRunCertified,
          { repo := .labRehearsal, rule := "novel_requires_twin_dry_run",
            detail := "adapted novel protocol failed digital-twin dry-run verification" }) ]

/-- Theorem M6 (Undergrad Novel-Task Onboarding Soundness):
    When facing an unseen assay/instrument (`seenBefore = false`), the agent can NEVER
    guess blindly: approval guarantees structural analogy, causal bottom-trace transfer,
    explicit tool lookup, and digital-twin verification! -/
theorem novel_task_never_executes_blindly (n : NovelOnboardingCheck)
    (hnew : n.seenBefore = false)
    (hok : checkNovelOnboarding n = none) :
    n.minAnalogyPermille ≤ n.analogySimPermille ∧
    n.analogBottomTraceLoaded = true ∧
    n.toolSpecsQueried = true ∧
    n.twinDryRunCertified = true := by
  unfold checkNovelOnboarding at hok
  simp only [hnew, Bool.false_eq_true, ↓reduceIte, firstViolation_cons,
             firstViolation_nil, and_true, decide_eq_true_eq] at hok
  rcases hok with ⟨hsim, htr, htool, htwin⟩
  exact ⟨hsim, htr, htool, htwin⟩

/-! ## Compile-Time `#guard` Witnesses for Agent Memory -/

def demoGoodNote : MemoryCandidate :=
  { noteId := 1, conceptId := 10, attributionCertified := true,
    hasFirstPrincipleLaw := true, hasCausalMechanism := true, contradictedByNewer := false,
    saliencePermille := 860, minSaliencePermille := 500, tokenCost := 140 }

def demoPoisonNote : MemoryCandidate :=
  { demoGoodNote with noteId := 2, attributionCertified := false, saliencePermille := 990 }

#guard (packIntoContext 250 [demoPoisonNote, demoGoodNote]).length == 1
#guard sumMemoryTokens (packIntoContext 250 [demoPoisonNote, demoGoodNote]) == 140
#guard (checkSkillReadiness { daysSinceLastUse := 95, staleThresholdDays := 30,
                              calibratedDeckEpoch := 4, currentDeckEpoch := 4,
                              bottomTraceReviewed := true, microRehearsalPass := true }).isNone
#guard (checkSkillReadiness { daysSinceLastUse := 95, staleThresholdDays := 30,
                              calibratedDeckEpoch := 4, currentDeckEpoch := 4,
                              bottomTraceReviewed := false, microRehearsalPass := true }).isSome
#guard (checkNovelOnboarding { seenBefore := false, analogySimPermille := 780,
                               minAnalogyPermille := 600, analogBottomTraceLoaded := true,
                               toolSpecsQueried := true, twinDryRunCertified := true }).isNone
#guard (checkNovelOnboarding { seenBefore := false, analogySimPermille := 780,
                               minAnalogyPermille := 600, analogBottomTraceLoaded := false,
                               toolSpecsQueried := true, twinDryRunCertified := true }).isSome

end AutoLabLean
