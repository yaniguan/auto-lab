# `AutoLabLean` — 7-Layer, 14-Repository Formal Trust Regime in Lean 4

`AutoLabLean` (`leanprover/lean4:v4.36.0`, zero external dependencies) formalizes the hard physical, statistical, stoichiometric, temporal, security, privacy, and licensing guardrails of all **14 Auto-Lab repositories** (`L6` down to `L0`) into a single machine-checked **Trust Regime** (`verifyCycle` / `InTrustRegime`).

- **Toolchain**: `leanprover/lean4:v4.36.0` (matches `yaniguan/YLM/lean` `LabLean`)
- **Proof Hygiene**: **50 machine-checked theorems**, **27 compile-time `#guard` witnesses**, **`0` `sorry`**, **`0` `admit`**, **`0` `axiom`**, **`0` `native_decide`**
- **Hub + Spoke Synchronization**: Maintained centrally here in `auto-lab/lean/` as the unified cross-layer kernel AND mirrored as standalone `lean/` packages (`LabAskWhyLean` .. `LabFeetLean`) inside each of the 14 sub-repositories
- **Runtime Executable**: `lake exe autolab-lean` (showcase mode + `--batch-tsv` high-throughput stdin RPC called directly from Python at ~15,000–30,000 checks/sec)

## Module Map (`L6 -> L0`)

| File | Covered Repositories | Key Formalized Guardrails & Proved Theorems |
| :--- | :--- | :--- |
| `AutoLabLean/Basic.lean` | Shared across `L6`–`L0` | Fixed-point physical units (`0.1 uL`, `Permille`, `Cents`), `RegimeViolation`, `LicenseClass`, `firstViolation_none_iff` |
| `AutoLabLean/L6_Epistemic.lean` | `lab-ask-why`, `lab-decide` | `NOINFO` abstention, symmetric contested-claim experiment requirement (`contested_claim_requires_experiment`), exact finite-sample conformal rank `ceil((n+1)*(1-alpha))` without clamping (`undersized_calib_always_abstains`), kNN trust boundary (`out_of_domain_always_abstains`) |
| `AutoLabLean/L5_Executive.lean` | `buy-or-make`, `labshift`, `lab-automation-atlas` | Acyclic `!@` bond cleavage + exact heavy-atom vector conservation (`ring_cleavage_rejected`), strict-null & homogeneous `USD/g` budget (`unpriced_never_passes_budget`), multi-instrument mutual exclusion & `[min_wait, max_wait]` incubation windows (`missed_incubation_window_rejected`), `evalOnly` contamination block (`eval_only_blocked_from_training`) |
| `AutoLabLean/L4_TwinAndGate.lean` | `lab-rehearsal`, `lab-verify` | Multi-step 96-well deck state machine with dead-volume reserve, solute concentration monotonicity (`A1 -> H1`, blocking `H1 -> B1` back-entry), `>= 80 C` seal precondition, episodic failed-hash fast-deny (`failed_hash_always_blocked`), **Total Liquid Conservation** (`runRehearsalSteps_conserves`), **Universal Capacity Invariant** (`checkRehearsal_preserves_capacity`), 4-layer SQL default-deny (`mutating_or_stacked_sql_denied`), zero-`sorry` proof gate (`sorry_proof_always_denied`) |
| `AutoLabLean/L3_PostTrain.lean` | `labbench-posttrain`, `twinstep`, `labfill` | `SplitGuard` group/canary holdout (`splitGuard_no_train_test_overlap`), multiplicative anti-hack RLVR reward (`unverified_rollout_gets_zero_reward`), causal RAW/WAR/barrier DAG topological order (`violated_dag_edge_rejected`), packed BF16 non-overlap & token conservation (`checkPackedBin_conserves_tokens`) |
| `AutoLabLean/L2_L1_L0_Embodied.lean` | `lab-ears`, `stepbot`, `lab-hands`, `lab-feet` | Full-skirt `[300, 3400] Hz` speech-band drop & zero raw audio persistence (`checkLabEars_strips_speech`), Opentrons `1..11` slots + tip cap + `distribute` disposal conservation (`stepbot_never_underflows_distribute_source`), `>= 5 mm` continuous arm clearance & slosh limit (`checkLabHands_guarantees_5mm_clearance`), positive quant scale & edge SRAM budget (`checkLabFeet_safe_for_edge`) |
| `AutoLabLean/TrustRegime.lean` | All 14 Repositories | `verifyCycle_ok_iff` (Soundness & Completeness), **`shieldedTrajectory_never_crosses_boundary`** (Multi-step inductive safety under arbitrary untrusted policies), **`selectBestCertified_always_valid`** & **`selectBestCertified_dominates_all_valid`** (Certified Best-of-`N` optimality) |
| `AutoLabLean/NovelDirections.lean` | Cross-Stack Frontier Extensions | **Diagnostic Epistemic Attribution** (`corrupted_run_never_poisons_memory`, `unidentifiable_spectrum_never_certified`, `certified_negative_sound`), **Stepped Frontier Calibration** (`deep_ood_always_blocked`, `accepted_outside_tau_is_bounded_probe`), and **Proof-Carrying `Lean-MCP` Envelopes** (`autonomous_mcp_requires_fresh_lean_proof`) |
| `AutoLabLean/AgentMemory.lean` | 4-Layer "Undergrad" Memory | **Offline Dreaming Hygiene & Budget Cap** (`unverified_trace_never_consolidated`, `packIntoContext_respects_budget`, `packIntoContext_all_certified`), **Rusty-Skill Calibration** (`stale_skill_requires_trace_and_rehearsal`, `epoch_shifted_skill_requires_rehearsal`), and **Zero-Shot Novel Onboarding** (`novel_task_never_executes_blindly`) |
| `AutoLabLean/Examples.lean` | All 14 Repositories | Compile-time `#guard` verification of a full 14-repo `ResearchCycle` plus per-repo boundary-crossing counterexamples |

## Quickstart

```bash
cd lean
lake build
lake exe autolab-lean
```
