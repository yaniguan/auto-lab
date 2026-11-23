# Four-Layer "Undergraduate" Agent Memory with Bottom Reasoning Traces & Dreaming

> **Formal Specification**: `lean/AutoLabLean/AgentMemory.lean` (6 machine-checked theorems, 6 `#guard` checks, `0 sorry`)  
> **Runtime & CLI**: `autolab/memory.py` · `autolab memory`  
> **Empirical Benchmark**: `python -m benchmarks.agent_memory_study` (`benchmarks/results/agent_memory_results.json`)

---

## 1. Design Philosophy: Why a Well-Trained Undergraduate?

Stateless laboratory agents fail across multi-week campaigns in two opposite ways:
1. **Amnesia**: Starting every session blank, repeating subtle rheology/sealing/stoichiometry failures.
2. **Over-Documentation Context Rot**: Passively appending thousands of raw sensor lines into prompt files (as documented in Anthropic's *The Components of Agent Memory*, Martin 2026), which buries true physical invariants under stale or unattributed hardware glitches.

By contrast, a **well-trained senior undergraduate researcher** can walk back into a wet lab after **6 months away from an instrument** ("rusty skill") or face a **brand-new reagent/assay** ("novel concept transfer") and succeed on the first run—because they pair a **lean mental index** with **causal derivations at the bottom of their lab notebook** and **active tool lookup**.

---

## 2. Four-Layer Architecture + Offline *Dreaming*

| Layer | Data Structure (`autolab/memory.py`) | Role in Rapid Mastery & Long-Term Retention |
| :--- | :--- | :--- |
| **Layer 0 (Bottom)** | `EpisodicTranscript` + **`BottomReasoningTrace`** | Immutable run history paired with a structured causal derivation (`Symptom -> FirstPrincipleLaw -> CausalChain -> LeanRuleWitness -> ParameterScaling`). Reading 1 bottom trace restores *why* an invariant holds (e.g., $\Delta V_{\text{dead}} \propto \log_{10}\mu$), enabling one-shot transfer to unseen viscosities rather than brittle magic-number memorization. |
| **Layer 1** | `MemoryNote` (*Memory as Prediction*) | Discrete mid-campaign lessons scored by predicted future-session salience (`saliencePermille`), strictly gated by `AutoLabLean` attribution (`attributionCertified = true`). |
| **Layer 2** | `ConceptWikiCard` (*Linked Mental Schemas*) | Interlinked markdown/JSON concept cards (`wiki/*.md`) mapping mechanism tags, governing equations, tool bindings (`stepbot`, `lab-rehearsal`, `lab-automation-atlas`, `lab-ask-why`), last-practiced timestamps, and calibrated deck epochs to Layer-0 Bottom Reasoning Traces. |
| **Layer 3 (Top)** | `InjectedBenchContext` (`MEMORY.md`) | Strictly token-capped (`sumMemoryTokens <= budgetTokens`) active bench brief loaded at session start. |
| **Sleep-Time Pass** | `dream_consolidate()` (*Dreaming*) | Offline consolidation pass that purges contradicted/uncertified notes, merges duplicate observations per `concept_id`, updates `ConceptWikiCard` links, and repacks `MEMORY.md` within the Lean token budget. |

---

## 3. Machine-Checked Lean 4.36.0 Guarantees (`AgentMemory.lean`)

1. **`unverified_trace_never_consolidated`**: Any episode suffering hardware/control corruption (`attributionCertified = false`), lacking a causal law (`hasFirstPrincipleLaw = false`), or superseded (`contradictedByNewer = true`) is rejected during Dreaming (`0` poisoned rules).
2. **`packIntoContext_respects_budget`** & **`packIntoContext_all_certified`**: Injected Layer-3 context never exceeds `budgetTokens`, and every injected note satisfies `traceConsolidatable = true`.
3. **`stale_skill_requires_trace_and_rehearsal`** & **`epoch_shifted_skill_requires_rehearsal`**: Any SOP untouched beyond `staleThresholdDays` or invoked after a physical deck epoch shift is blocked unless `bottomTraceReviewed = true` AND `microRehearsalPass = true`.
4. **`novel_task_never_executes_blindly`**: Any unseen assay (`seenBefore = false`) requires structural analogy (`minAnalogyPermille <= analogySimPermille`), bottom-trace causal loading (`analogBottomTraceLoaded = true`), live tool lookup (`toolSpecsQueried = true`), and twin dry-run certification (`twinDryRunCertified = true`).
