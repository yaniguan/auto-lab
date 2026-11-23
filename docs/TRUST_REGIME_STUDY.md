# Bounded Autonomous Discovery: Formalizing the 14-Repository Auto-Lab Trust Regime in Lean 4

## 1. Motivation: Why Prompt Guardrails & Soft Rewards Fail in Autonomous Wet Labs

Autonomous co-scientists and wet-lab robots face an inherent tension between **open-ended exploration** and **irreversible physical, chemical, and epistemic hazards**:

- **Extrapolation Lure (`L6`)**: Tree ensembles and neural regressors emit confident solubility or conductivity numbers on out-of-distribution macrocycles (`MAE = 0.978` vs `0.393` inside calibrated support), steering naive Bayesian/greedy optimizers straight into uncalibrated territory.
- **Stoichiometric & Unit Illusions (`L5`)**: Bimolecular SMARTS templates without acyclic (`!@`) bond constraints cleave endocyclic lactams and duplicate carbon atoms (`Analog-6`), while unpriced or non-`USD/g` catalog entries slip past scalar budget filters.
- **Subtle Physical Bookkeeping & Window Violations (`L5`, `L4`, `L1`)**: Coarse presence-bitmask checkers catch `sample -> buffer` contamination but miss serial-dilution back-transfers (`dilute H1 -> concentrated B1`), `5.0 uL` reservoir dead-volume underflows, `>= 80 °C` unsealed evaporation, `distribute` disposal-volume exhaustion, and missed post-incubation `max_wait` windows.
- **Semantic SQL & Reward Hacking (`L4`, `L3`)**: Half (`55.6%`) of wrong lab-database SQL queries pass syntax, read-only, and schema checks (`COUNT` vs `COUNT(DISTINCT ...)`), while RL policies trained with soft additive format/length rewards rapidly collapse onto reward hacking (`99.6%` exploit rate, `0.4%` true verified accuracy).

To resolve this tension, Auto-Lab enforces a **machine-checked Lean 4 Trust Regime (`AutoLabLean`)**:

> **Core Principle**: Hard safety, calibration, stoichiometric, temporal, and licensing invariants are specified and proved in Lean 4 (`leanprover/lean4:v4.36.0`) as an **impenetrable default-deny boundary** (`verifyCycle`). Outside the boundary, every action is deterministically blocked or abstained; *inside* the boundary, the autonomous agent explores freely, repairs candidates using exact Lean rule counterexamples, and optimizes policies without reward hacking.

---

## 2. Formal Architecture (`lean/AutoLabLean/`)

`AutoLabLean` comprises **10 pure Lean 4 source files**, **38 machine-checked theorems** (`0` `sorry`, `0` `admit`, `0` `axiom`, `0` `native_decide`), and **16 compile-time `#guard` witnesses**, compiling into a native executable (`autolab-lean`) that evaluates ~`30,000` candidate protocols/sec over `--batch-tsv`.

### 2.1 Per-Repository Guardrails (`L6 -> L0`)

1. **`lab-ask-why` (`L6_Epistemic.lean`)**: `checkAskWhy_ok_iff` & `contested_claim_requires_experiment` — enforces `NOINFO` abstention below threshold and requires a falsifiable discriminating experiment whenever both supporting and contradicting evidence exist.
2. **`lab-decide` (`L6_Epistemic.lean`)**: `checkDecide_ok_iff`, `out_of_domain_always_abstains`, & `undersized_calib_always_abstains` — proves exact finite-sample rank $k = \lceil (n+1)(1-\alpha) \rceil \le n$ without clamping and blocks $d_{\text{kNN}}(x) > \tau_{\text{cal}}$.
3. **`buy-or-make` (`L5_Executive.lean`)**: `ring_cleavage_rejected` & `unpriced_never_passes_budget` — enforces acyclic (`!@`) cleavage, exact heavy-atom vector conservation $\sum \text{atoms}(\text{reactants}) = \text{atoms}(\text{target}) + \Delta_{\text{LG}}$, homogeneous `USD/g` complete pricing, and transitive source license compliance.
4. **`labshift` (`L5_Executive.lean`)**: `checkSchedule_ok_iff` & `missed_incubation_window_rejected` — certifies pool capacity, machine mutual exclusion, release/deadline bounds, and inter-step `[min_wait, max_wait]` windows.
5. **`lab-automation-atlas` (`L5_Executive.lean`)**: `eval_only_blocked_from_training` — enforces HTTPS/no-SSRF, explicit SPDX metadata, and hard benchmark-contamination blocking (`evalOnly` corpora cannot enter training).
6. **`lab-rehearsal` (`L4_TwinAndGate.lean`)**: `runRehearsalSteps_conserves`, `checkRehearsal_preserves_capacity`, & `failed_hash_always_blocked` — proves multi-step total liquid conservation, universal well capacity `vol <= cap`, dead-volume reserve, concentration-monotonic tip entry, `>= 80 °C` seal precondition, and episodic recall fast-deny.
7. **`lab-verify` (`L4_TwinAndGate.lean`)**: `mutating_or_stacked_sql_denied` & `sorry_proof_always_denied` — enforces 4-layer SQL default-deny (single statement, AST + authorizer read-only, lexical schema + no implicit cross join, reference + perturbation counterexample execution) and zero-`sorry` proof verification.
8. **`labbench-posttrain` (`L3_PostTrain.lean`)**: `splitGuard_no_train_test_overlap` & `unverified_rollout_gets_zero_reward` — proves group/canary holdout disjointness and multiplicative zeroing of unverified, `<think>`-padded, or oracle-leaked rollouts.
9. **`twinstep` (`L3_PostTrain.lean`)**: `violated_dag_edge_rejected` — certifies bijective step permutations satisfying all RAW, WAR, and stage-barrier DAG edges.
10. **`labfill` (`L3_PostTrain.lean`)**: `checkPackedBin_conserves_tokens` — proves packed BF16 slices fit within `binCap`, never overlap across distinct sequences, and conserve exact real-token counts.
11. **`lab-ears` (`L2_L1_L0_Embodied.lean`)**: `checkLabEars_strips_speech` — proves zero raw audio persistence and zero filter-skirt overlap with `[300, 3400] Hz` human speech.
12. **`stepbot` (`L2_L1_L0_Embodied.lean`)**: `stepbot_never_underflows_distribute_source` — certifies unique OT-2 slots `1..11`, effective `min(pipMax, tipRackMax)` volume cap, and `n * vol + disposalVol <= sourceVol`.
13. **`lab-hands` (`L2_L1_L0_Embodied.lean`)**: `checkLabHands_guarantees_5mm_clearance` — certifies `>= 5 mm` continuous obstacle clearance, `|q2| <= 2.60 rad`, vessel-rim Z transit, slosh acceleration cap, and `<= 0.2 mm` tactile seating error.
14. **`lab-feet` (`L2_L1_L0_Embodied.lean`)**: `checkLabFeet_safe_for_edge` — certifies `[2, 8]` bit-width, strictly positive quantization scale (`scaleMicro > 0`), SRAM byte budget, and teacher-student agreement floor.

### 2.2 Master Composition & Bounded Autonomy Theorems (`TrustRegime.lean`)

- **`verifyCycle_ok_iff` (Soundness & Completeness)**: `(∃ w', verifyCycle w c = .ok w') ↔ ∃ deck', InTrustRegime w c deck'`.
- **`shieldedTrajectory_never_crosses_boundary` (Multi-Step Inductive Shield)**: For *any* untrusted sequence of proposed cycles `cs : List ResearchCycle`, `runShieldedTrajectory` preserves `WorldSafe` (`AllWellsFit`, exact `totalWellsVol` conservation, and `tip = .noTip`) across arbitrary horizon $T$.
- **`selectBestCertified_always_valid` & `selectBestCertified_dominates_all_valid` (Certified Best-of-$N$ Optimality)**: Selecting the highest-utility candidate in a batch certified by `verifyCycle` guarantees zero boundary crossings while attaining utility $\ge$ every feasible candidate in the batch.

---

## 3. Empirical Study: How the Lean Trust Regime Improves Task Performance

All five experiments are reproduced by `python benchmarks/trust_regime_study.py`, which invokes the compiled `autolab-lean` Lean 4.36.0 executable directly via `--batch-tsv`.

### Experiment 1 · `L6 + L5` Autonomous Molecular Discovery Campaign (`1,128` Real Delaney ESOL Compounds, 5 Seeds)

| Regime | Boundary Violations | Selected Bench MAE (`log mol/L`) | Empirical 90% Coverage | Verified Soluble Hit Yield |
| :--- | :---: | :---: | :---: | :---: |
| **Ungated Greedy Point-Predictor** | `72.0%` | `0.978` | `76.0%` | `28.0%` |
| **Partial Heuristic Filter** (SMILES + raw scalar price) | `59.2%` | `0.957` | `78.4%` | `40.8%` |
| **Lean 4 Trust Regime (`AutoLabLean`)** | **`0.0%`** | **`0.393` (`-59.8%` error)** | **`97.6%`** | **`100.0%` (`3.57x` yield)** |

### Experiment 2 · `L4 + L1` Wet-Lab Protocol Synthesis & Counterexample-Guided Repair (`200` Tasks $\times$ `8` Candidates = `1,626` Lean Checks @ `30,048` proto/s)

| Regime | Catastrophic Hardware Faults | Valid End-to-End Task Completion |
| :--- | :---: | :---: |
| **Ungated Top-1** | `78.0%` | `22.0%` |
| **Coarse Bitmask / Capacity Heuristic** (misses dead-vol, conc. order, `>=80 C` seal) | `76.5%` | `23.5%` |
| **Lean 4 Shielded Best-of-8 (`selectBestCertified`)** | **`0.0%`** | **`87.0%`** |
| **Lean 4 Best-of-8 + Counterexample-Guided 1-Step Repair** | **`0.0%`** | **`97.5%` (`4.43x` lift)** |

### Experiment 3 · `L5` Contended Multi-Instrument Scheduling (`30` `labshift` Suites across 5 Instrument Pools)

| Regime | Feasible Suites | `max_wait` Incubation Violations | Mean Makespan |
| :--- | :---: | :---: | :---: |
| **Ungated Greedy List Scheduler** | `24 / 30` (`80.0%`) | `13` ruined incubations | `129.8 min` |
| **Greedy + Local Repair** | `30 / 30` (`100.0%`) | `0` | `129.2 min` |
| **Lean-Certified CP-SAT Schedule** | **`30 / 30` (`100.0%`)** | **`0`** | **`116.5 min` (`-10.2%` faster)** |

### Experiment 4 · `L4` Scientific Lab-Database SQL Selection (`lab-verify` 16 Pools / 30 Candidates)

| Regime | False-Accept Rate on Wrong/Unsafe SQL | Verified Answer Accuracy |
| :--- | :---: | :---: |
| **Ungated Noisy Top-1** | `100.0%` | `6.2%` |
| **Syntax + Read-Only + Schema Only (`L1–L3`)** | `55.6%` (`10 / 18` wrong queries slip through) | `31.2%` |
| **Lean 4-Layer Default-Deny Gate (`L1–L4` + Counterexample DBs)** | **`0.0%`** | **`75.0%` (`2.40x` over L1–L3)** |

### Experiment 5 · `L3` RLVR Post-Training (`GRPO`, 5 Seeds $\times$ 160 Steps)

| Regime | Final Policy Reward-Hack Exploit Rate | True Verified Scientific Accuracy |
| :--- | :---: | :---: |
| **Untrained Initial Policy** | `88.8%` | `11.2%` |
| **Soft Additive Format + Length Bonus (`GRPO`)** | `99.6%` (collapses onto `<think>` & `always-True` exploits) | `0.4%` |
| **Lean Multiplicative Trust-Regime Gate (`GRPO`)** | **`1.6%`** | **`98.4%`** |

---

## 4. Reproducing Everything Locally

```bash
# 1. Build the Lean 4.36.0 formalization (38 theorems, 0 sorry) & run the 14-repo showcase
cd lean && lake build && lake exe autolab-lean && cd ..

# 2. Re-run all 5 empirical experiments through the compiled Lean 4 binary
python benchmarks/trust_regime_study.py

# 3. Inspect via CLI
autolab trust
```
