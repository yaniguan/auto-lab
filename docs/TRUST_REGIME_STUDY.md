# Bounded Autonomous Discovery: Formalizing the Auto-Lab Trust Regime in Lean 4

## 1. Motivation: Separating Formal Invariants, Simulations, and Real Wet-Lab Data

Autonomous co-scientists and wet-lab robots face a structural tension between **open-ended exploration** and **irreversible physical, chemical, and epistemic hazards**:

- **Extrapolation Error on Unseen Scaffolds (`L6`)**: On real Delaney ESOL (`n = 1,128` compounds), a gradient-boosted regressor trained on small molecules (`MW <= 78th percentile`) achieves `0.558` log(mol/L) MAE (`92.7%` empirical 90% split-conformal coverage) inside its calibrated kNN trust region, whereas error jumps **2.45x** to `1.368` (`59.4%` coverage) outside the kNN threshold.
- **Stoichiometric & Unit Illusions (`L5`)**: Bimolecular SMARTS templates without acyclic (`!@`) bond constraints cleave endocyclic lactams and duplicate carbon atoms (`Analog-6`), while unpriced or non-`USD/g` catalog entries slip past scalar budget filters.
- **Physical Liquid-Handling & Scheduling Bugs (`L5`, `L4`, `L1`)**: Even real public protocols in `Opentrons/Protocols` contain parameter/labware mismatches that legacy Opentrons simulation permits silently—such as dispensing `250 uL` into a `200 uL` round-bottom well (`1adec6-2`), dispensing `200 uL` into a `100 uL` PCR plate (`384b23-plate-transfer`), or aspirating `1.0 uL` with a `20-300 uL` `P300` pipette (`6d901d-2`).
- **Semantic SQL & Reward Hacking (`L4`, `L3`)**: Over half (`55.6%`) of hand-authored wrong lab-database SQL queries pass syntax, read-only, and schema checks (`COUNT` vs `COUNT(DISTINCT ...)`), while softmax bandit policies under additive format bonuses collapse onto unverified shortcuts (`99.6%` exploit mass in 6-arm simulation; neural GPU RLVR run `PENDING`).

To address these failure modes transparently, Auto-Lab pairs a **machine-checked Lean 4 Trust Regime (`AutoLabLean`)** with **strict scientific accounting of what is measured on real data, what is checked by an independent simulator, what holds `"by construction"` as a gate invariant, and what remains a CPU simulation (`GPU PENDING`)**.

---

## 2. Formal Architecture (`lean/AutoLabLean/`)

`AutoLabLean` comprises **12 pure Lean 4 source files**, **50 machine-checked theorems** (`0` `sorry`, `0` `admit`, `0` `axiom`, `0` `native_decide`), and **27 compile-time `#guard` witnesses**, compiling into a native executable (`autolab-lean`) that evaluates candidate actions over `--batch-tsv`.

### 2.1 Per-Repository Guardrails (`L6 -> L0`)

1. **`lab-ask-why` (`L6_Epistemic.lean`)**: `checkAskWhy_ok_iff` & `contested_claim_requires_experiment` - enforces `NOINFO` abstention below threshold and requires a falsifiable discriminating experiment whenever both supporting and contradicting evidence exist.
2. **`lab-decide` (`L6_Epistemic.lean`)**: `checkDecide_ok_iff`, `out_of_domain_always_abstains`, & `undersized_calib_always_abstains` - proves exact finite-sample rank $k = \lceil (n+1)(1-\alpha) \rceil \le n$ without clamping and blocks $d_{\text{kNN}}(x) > \tau_{\text{cal}}$.
3. **`buy-or-make` (`L5_Executive.lean`)**: `ring_cleavage_rejected` & `unpriced_never_passes_budget` - enforces acyclic (`!@`) cleavage, exact heavy-atom vector conservation, homogeneous `USD/g` complete pricing, and transitive source license compliance.
4. **`labshift` (`L5_Executive.lean`)**: `checkSchedule_ok_iff` & `missed_incubation_window_rejected` - certifies pool capacity, machine mutual exclusion, release/deadline bounds, and inter-step `[min_wait, max_wait]` windows.
5. **`lab-automation-atlas` (`L5_Executive.lean`)**: `eval_only_blocked_from_training` - enforces HTTPS/no-SSRF, explicit SPDX metadata, and hard benchmark-contamination blocking (`evalOnly` corpora cannot enter training).
6. **`lab-rehearsal` (`L4_TwinAndGate.lean`)**: `runRehearsalSteps_conserves`, `checkRehearsal_preserves_capacity`, & `failed_hash_always_blocked` - proves multi-step total liquid conservation, universal well capacity `vol <= cap`, dead-volume reserve, concentration-monotonic tip entry, `>= 80 C` seal precondition, and episodic recall fast-deny.
7. **`lab-verify` (`L4_TwinAndGate.lean`)**: `mutating_or_stacked_sql_denied` & `sorry_proof_always_denied` - enforces 4-layer SQL default-deny and zero-`sorry` proof verification.
8. **`labbench-posttrain` (`L3_PostTrain.lean`)**: `splitGuard_no_train_test_overlap` & `unverified_rollout_gets_zero_reward` - proves group/canary holdout disjointness and multiplicative zeroing of unverified, `<think>`-padded, or oracle-leaked rollouts.
9. **`twinstep` (`L3_PostTrain.lean`)**: `violated_dag_edge_rejected` - certifies bijective step permutations satisfying all RAW, WAR, and stage-barrier DAG edges.
10. **`labfill` (`L3_PostTrain.lean`)**: `checkPackedBin_conserves_tokens` - proves packed BF16 slices fit within `binCap`, never overlap across distinct sequences, and conserve exact real-token counts.
11. **`lab-ears` (`L2_L1_L0_Embodied.lean`)**: `checkLabEars_strips_speech` - proves zero raw audio persistence and zero filter-skirt overlap with `[300, 3400] Hz` human speech.
12. **`stepbot` (`L2_L1_L0_Embodied.lean`)**: `stepbot_never_underflows_distribute_source` - certifies unique OT-2 slots `1..11`, effective `min(pipMax, tipRackMax)` volume cap, and `n * vol + disposalVol <= sourceVol`.
13. **`lab-hands` (`L2_L1_L0_Embodied.lean`)**: `checkLabHands_guarantees_5mm_clearance` - certifies `>= 5 mm` continuous obstacle clearance, `|q2| <= 2.60 rad`, vessel-rim Z transit, slosh acceleration cap, and `<= 0.2 mm` tactile seating error.
14. **`lab-feet` (`L2_L1_L0_Embodied.lean`)**: `checkLabFeet_safe_for_edge` - certifies `[2, 8]` bit-width, strictly positive quantization scale (`scaleMicro > 0`), SRAM byte budget, and teacher-student agreement floor.
15. **`AgentMemory.lean` & `NovelDirections.lean`**: 12 additional theorems formalizing 4-way post-run causal attribution (`ATTRIB`), stepped `Chem-RRT` calibration shells (`FRONTIER`), epoch-bound `Lean-MCP` capability tokens (`MCP`), and 4-layer Undergrad Agent Memory + Dreaming.

---

## 3. What Is Real vs. Simulated

Every headline metric across `README.md` and this document is cross-checked in CI (`tests/test_benchmark_honesty.py`) against the committed JSON artifacts in `benchmarks/results/`:

| Headline Metric | Reported Value | Script | JSON Key | n | Input / Ground-Truth Basis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ESOL Held-Out Lead Prediction MAE** | `1.462 -> 0.604` log(mol/L) | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.ungated.prediction_mae -> trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.lean_trust.prediction_mae` | `1,128` real ESOL (`25`/seed x `5` seeds) | `real_data` (SHA-256 verified `delaney-processed.csv`; raw GBDT ranking, no OOD bonus) |
| **ESOL Empirical 90% Conformal Coverage** | `50.4% -> 91.2%` | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.ungated.empirical_coverage_pct -> trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.lean_trust.empirical_coverage_pct` | `1,128` real ESOL (`25`/seed x `5` seeds) | `real_data` (independent measured `logS` vs split-conformal interval) |
| **ESOL Measured Soluble Hit Rate (`logS >= -2.8`)** | `50.4% -> 32.2%` | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.ungated.measured_soluble_hit_pct -> trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.lean_trust.measured_soluble_hit_pct` | `1,128` real ESOL (`25`/seed x `5` seeds) | `real_data` (independent measured `logS`, decoupled from gate verdict) |
| **ESOL Full-Pool In-Region vs OOD MAE** | `0.558 -> 1.368` log(mol/L) | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp1_molecular_discovery.real_heldout_pool_diagnostic.in_region_mae -> trust_regime_results.json:experiments.exp1_molecular_discovery.real_heldout_pool_diagnostic.abstained_ood_mae` | `468` held-out/seed x `5` seeds | `real_data` (zero synthetic flags; pure `delaney-processed.csv`) |
| **Exp 1 Procurement + kNN Gate Rejections** | `89.6% -> 0.0%` | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.ungated.gate_violation_pct_by_construction -> trust_regime_results.json:experiments.exp1_molecular_discovery.regimes.lean_trust.gate_violation_pct_by_construction` | `25`/seed x `5` seeds | `simulation` + `by_construction` (simulated procurement flags; same Lean gate filters & scores) |
| **Real Opentrons Library Import Coverage** | `58 / 85` (`68.2%`) | `benchmarks/real_protocol_rehearsal.py` | `opentrons_library_rehearsal.json:summary.n_imported -> opentrons_library_rehearsal.json:summary.n_total` | `85` public `.py`/`.json` protocols | `real_data` + `independent_simulator` (`opentrons.simulate` CPU runlog; `27` fail-closed unsupported) |
| **Real Opentrons Allowed vs Denied Protocols** | `35` allowed / `23` denied | `benchmarks/real_protocol_rehearsal.py` | `opentrons_library_rehearsal.json:summary.n_allowed -> opentrons_library_rehearsal.json:summary.n_denied` | `58` imported real protocols | `real_data` (`autolab-lean --batch-tsv`; `0` Python-mirror mismatches) |
| **Real Opentrons Deny False-Alarm Rate** | `47.8%` (`11` false alarms / `12` true hazards) | `benchmarks/real_protocol_rehearsal.py` | `opentrons_library_rehearsal.json:summary.audited_false_alarm_rate_pct -> opentrons_library_rehearsal.json:summary.audited_true_hazard_count` | `23 / 23` denied real protocols | `real_data` (code-grounded manual audit of all 23 denied protocols) |
| **Exp 2 Independent `stepbot` Simulator Faults** | `18.5% -> 0.0%` | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp2_protocol_synthesis.regimes.ungated_top1.independent_sim_fault_pct -> trust_regime_results.json:experiments.exp2_protocol_synthesis.regimes.lean_best_of_8_plus_guided_repair.independent_sim_fault_pct` | `200` tasks x `8` cands | `simulation` + `independent_simulator` (3-template generator checked by `stepbot` API v2.16 simulator) |
| **Exp 2 Simulated Valid Completion (Bo8 + Repair)** | `22.0% -> 97.5%` | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp2_protocol_synthesis.regimes.ungated_top1.valid_completion_pct -> trust_regime_results.json:experiments.exp2_protocol_synthesis.regimes.lean_best_of_8_plus_guided_repair.valid_completion_pct` | `200` tasks x `8` cands | `simulation` + `by_construction` (`0.0%` Lean rule violations is by construction) |
| **Exp 3 Fleet Scheduling (`greedy` vs `cpsat`)** | `129.8 -> 116.4 min` (`24/30 -> 30/30`) | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp3_fleet_scheduling.regimes.ungated_greedy.mean_makespan_min -> trust_regime_results.json:experiments.exp3_fleet_scheduling.regimes.cpsat.mean_makespan_min` | `30` `labshift` instances | `simulation` (synthetic benchmark suite; `cpsat` is OR-Tools CP-SAT, not Lean) |
| **Exp 4 Lab SQL Wrong-Query False Accepts** | `55.6% -> 0.0%` (`31.2% -> 75.0%` acc) | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp4_sql_verification.regimes.syntax_readonly_schema_only_L1_L3.wrong_sql_false_accept_pct -> trust_regime_results.json:experiments.exp4_sql_verification.regimes.lean_4layer_default_deny_L1_L4.wrong_sql_false_accept_pct` | `16` pools / `30` queries (`18` wrong) | `simulation` (hand-authored adversarial wrong-first SQL suite + gold/counterexample DB check) |
| **Exp 5 6-Arm Bandit Policy Simulation** | `0.4% -> 98.4%` verified arm mass | `benchmarks/trust_regime_study.py` | `trust_regime_results.json:experiments.exp5_rlvr_posttraining.regimes.soft_additive_reward_grpo.true_verified_accuracy_pct -> trust_regime_results.json:experiments.exp5_rlvr_posttraining.regimes.lean_trust_gated_grpo.true_verified_accuracy_pct` | `6` arms x `5` seeds x `160` steps | `simulation` / `PENDING` (6-logit softmax toy, NOT LLM weight training; GPU RLVR `PENDING`) |
| **Direction 1 Post-Run Attribution (`ATTRIB`)** | `8.3% -> 0.0%` FDR (`52.2 -> 67.6` hits) | `benchmarks/novel_directions_study.py` | `novel_directions_results.json:directions.d1_epistemic_attribution.comparison.naive_sdl.false_discovery_rate_pct -> novel_directions_results.json:directions.d1_epistemic_attribution.comparison.lean_attribution_sdl.false_discovery_rate_pct` | `1,128` ESOL (`96` assays x `5` seeds) | `real_data` + `simulation` (real ESOL solubility + simulated separable fault telemetry) |
| **Direction 2 Stepped `Chem-RRT` Frontier** | `1.2 -> 30.8` (`54.4` undirected) scaffolds | `benchmarks/novel_directions_study.py` | `novel_directions_results.json:directions.d2_stepped_frontier.comparison.static_trust_wall_v1.certified_multiring_scaffolds_unlocked -> novel_directions_results.json:directions.d2_stepped_frontier.comparison.goal_directed_chem_rrt_shell.certified_multiring_scaffolds_unlocked` | `1,128` ESOL (`8` rounds x `5` seeds) | `real_data` + `by_construction` (real ESOL scaffolds; `0.0` uncalibrated runs by `FRONTIER`) |
| **Direction 3 `Lean-MCP` 72h Clock Simulation** | `88 -> 472` runs (`28 -> 0` replays) | `benchmarks/novel_directions_study.py` | `novel_directions_results.json:directions.d3_lean_mcp.comparison.per_run_human_approval_mcp.protocols_completed_in_72h -> novel_directions_results.json:directions.d3_lean_mcp.comparison.proof_carrying_lean_mcp.protocols_completed_in_72h` | `500` synthetic MCP calls | `simulation` + `by_construction` (discrete-event 72h lab clock simulation) |
| **Direction 4 Fixed Fault-Family Mutation Check** | `85.7% -> 57.1% -> 0.0%` evasion | `benchmarks/novel_directions_study.py` | `novel_directions_results.json:directions.d4_adversarial_coevolution.generations.gen0_volume_bounds_only.saboteur_evasion_pct -> novel_directions_results.json:directions.d4_adversarial_coevolution.generations.gen2_autolablean_formal.saboteur_evasion_pct` | `21` distinct cases (`140` draws) | `simulation` + `by_construction` (3 templates x 7 fixed fault types; not an adaptive adversary) |

---

## 4. Detailed Benchmark Results

### Experiment 1 · `L6 + L5` Molecular Discovery on Held-Out Delaney ESOL (`1,128` Real Compounds, SHA-256 Verified)

`autolab/datasets.py` resolves `delaney-processed.csv` (`sha256 = 8c06a76f0c64...`, `1,128` compounds) fail-closed with zero synthetic fallback. All three arms rank held-out drug-like candidates (`MW >= 200 Da, Rings >= 1`) by the **exact same raw GBDT predicted `logS`** (no artificial OOD optimism bonus):

| Regime | Real Held-Out MAE (`log mol/L`) | Empirical 90% Coverage | Measured Soluble Hits (`logS >= -2.8`) | Gate Violations (`by construction`) |
| :--- | :---: | :---: | :---: | :---: |
| **Ungated Raw GBDT Point-Predictor** | `1.462` | `50.4%` | `50.4%` | `89.6%` |
| **Partial Heuristic Filter** (SMILES + scalar price) | `1.412` | `54.4%` | `46.4%` | `84.0%` |
| **Lean 4 Gate (`AutoLabLean`)** | **`0.604` (`2.42x` lower error)** | **`91.2%`** | `32.2%` | **`0.0%` (by construction)** |

> **Honest Trade-Off**: Enforcing the kNN trust radius cuts real experimental `logS` prediction error from `1.462` to `0.604` and restores nominal 90% conformal coverage (`50.4% -> 91.2%`), while lowering raw soluble hit fraction among heavy rings (`50.4% -> 32.2%`) because uncalibrated high-MW extrapolations are abstained rather than gambled on.

### Experiment 2 · Real Public Opentrons Protocol Library Rehearsal (`85` Pinned Protocols via `opentrons.simulate`)

`autolab/importers/opentrons_runlog.py` simulates real `.py` and `.json` protocols on CPU via `opentrons.simulate.simulate()` and lowers the executed command tree into `REHEARSAL` steps, raising `UnsupportedProtocolStepError` rather than dropping unsupported commands silently (`benchmarks/real_protocol_rehearsal.py`):

- **Pinned Sample (`n = 85`)**: `74` Python API v2 entries from `Opentrons/Protocols` (`2f447c936b49720d68154054e94d58e1d33ccba5`) + `11` Apache-2.0 JSON v3/v4/v5 fixtures from `Opentrons/opentrons` (`84a9956efccae8783f1a49ec14873222956f3284`).
- **Import Coverage**: **`58 / 85` (`68.2%`) imported**; **`27 / 85` (`31.8%`) rejected fail-closed** (`magnetic_module_command`, `manual_human_pause_intervention`, `residual_disposal_volume_blown_out_to_trash`, `mixed_single_and_multichannel_pipettes`, `return_tip_not_modeled_in_rehearsal`, `undispensed_liquid_discarded_with_tip`, `simultaneous_multi_pipette_tips`).
- **Verdicts & Parity**: **`35 / 58` (`60.3%`) allowed**, **`23 / 58` (`39.7%`) denied** (`enough_recoverable_volume`: `5`, `distinct_transfer_wells`: `4`, `mix_sufficient_well_volume`: `4`, `no_well_overfill`: `4`, `no_tip_cross_contamination`: `3`, `pipette_volume_range`: `3`), with **`0` mismatches** between compiled `autolab-lean` and `py_check_rehearsal`.
- **Manual Audit of All `23` Denied Real Protocols**:
  - **`12 / 23` (`52.2%`) `true_hazard`** — genuine physical/calibration bugs missed by legacy Opentrons simulation, including `250 uL` dispensed into a `200 uL` round well (`1adec6-2`), `200 uL` dispensed into a `100 uL` PCR well (`384b23-plate-transfer`), `1.0 uL` aspirated on a `20-300 uL` `P300` pipette (`6d901d-2`), `340 uL` aspirated from a single `200 uL` well (`0e525c`), and diluted-tip re-entry into concentrated DNA stock (`4883fc`).
  - **`11 / 23` (`47.8%`) `abstraction_false_alarm`** — limitations of the 7-operator `REHEARSAL` DSL and pre-2.14 Opentrons metadata: undeclared pre-plated starting volumes (`0961d2-part1`, `158d42`, `422b1e`, `6c27ee`, `76c562`), same-well tip pre-wetting or `disposal_volume` return triggering `src != dst` (`154ec5`, `543bf9`, `60d861-2`, `6cb818`), `.top()` air-dispense (`00a214-protocol-1`), and integer floor-division solute rounding (`56b4ec`).

### Experiment 3 · Simulated Protocol Synthesis (`200 x 8` Candidates + Independent `stepbot` Simulator)

| Regime | Independent `stepbot` Simulator Faults | Lean Rule Violations (`by construction`) | Lean-Certified Completion |
| :--- | :---: | :---: | :---: |
| **Ungated Top-1** | `18.5%` | `78.0%` | `22.0%` |
| **Coarse Bitmask / Capacity Heuristic** | `0.0%` | `72.0%` | `28.0%` |
| **Lean 4 Shielded Best-of-8 (`selectBestCertified`)** | **`0.0%`** | **`0.0%` (by construction)** | **`87.0%`** |
| **Lean 4 Best-of-8 + Counterexample-Guided 1-Step Repair** | **`0.0%`** | **`0.0%` (by construction)** | **`97.5%`** |

### Experiment 4 · `L5` Multi-Instrument Fleet Scheduling (`30` `labshift` Synthetic Benchmark Suites)

`run_exp3_scheduling()` imports sibling `labshift` directly (raising `ImportError`/`RuntimeError` if missing):

| Solver (`labshift`) | Feasible Suites | `max_wait` Incubation Violations | Mean Makespan |
| :--- | :---: | :---: | :---: |
| **`ungated_greedy`** | `24 / 30` (`80.0%`) | `13` | `129.8 min` |
| **`greedy_with_repair`** | `30 / 30` (`100.0%`) | `0` | `129.2 min` |
| **`cpsat` (OR-Tools CP-SAT)** | **`30 / 30` (`100.0%`)** | **`0`** | **`116.4 min` (`-10.3%`)** |

### Experiment 5 · `L4` SQL Stress Suite (`lab-verify`) & `L3` 6-Arm Bandit Policy Simulation (`GPU PENDING`)

- **Adversarial SQL Suite (`16` pools, `30` hand-authored queries sorted wrong-first)**: `L1-L3` syntax/read-only/schema checks let `10 / 18` (`55.6%`) semantic-bug queries slip through (`31.2%` accuracy), whereas `L1-L4` reference + perturbation counterexample DB verification reduces false accepts to `0.0%` (`75.0%` accuracy).
- **6-Arm Bandit Policy Simulation (`NOT` neural LLM weight training; GPU RLVR run `PENDING`)**: Over 6 hand-scored rollout archetypes (`5` seeds x `160` steps), soft additive bonuses collapse onto exploit arms (`99.6%` exploit mass, `0.4%` verified arm mass), whereas Lean multiplicative reward gating concentrates `98.4%` probability mass on the 2 verified archetypes.

---

## 5. Reproducing Everything Locally

```bash
# 1. Build the Lean 4.36.0 formalization (50 theorems, 27 #guard checks, 0 sorry)
cd lean && lake build && lake exe autolab-lean && cd ..

# 2. Re-run core & novel-direction benchmarks (requires Delaney ESOL CSV + sibling repos)
python benchmarks/trust_regime_study.py
python benchmarks/novel_directions_study.py

# 3. Re-run real public Opentrons Protocol Library rehearsal (requires `pip install -e ".[real-data]"`)
python benchmarks/real_protocol_rehearsal.py

# 4. Run full verification & zero-drift test suite
AUTOLAB_REQUIRE_LEAN=1 AUTOLAB_REQUIRE_SIBLINGS=1 pytest -v
```
