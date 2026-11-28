/* Layered, Human-Readable Stories & Interactive Micro-Playgrounds for All 15 Auto-Lab Repos
 * Replaces rigid "1. Object / 2. Data..." form lists with:
 *   Layer 1: Plain-English "What & Why" + 3 clean metrics
 *   Layer 2: Interactive "Try an Example" scenario switcher (real inputs -> real outputs)
 *   Layer 3: Progressive-disclosure tabs (How it works & Data | Guarantee & Limits | Status & Next)
 */
(() => {
  'use strict';

  const STORIES = {
    'lab-ask-why': {
      headline: 'When two papers or labmates disagree, surface the evidence behind each claim and name the experiment that settles it.',
      why: 'Most AI co-scientists rush to pick a winner. In real research, prematurely crowning one hypothesis hides the assumptions that actually need testing at the bench.',
      metrics: [
        ['90.9%', 'gold rationale hit@3'],
        ['90.7%', 'conformal stance cov'],
        ['100%', 'ConflictBank detected'],
      ],
      playgroundPrompt: 'Pick a real scientific claim to see retrieved evidence & Socratic questions:',
      demos: [
        {
          tab: 'Claim A · Rare Variants (Supported)',
          verdict: 'SUPPORT · 2/3 gold hits',
          verdictTone: 'pass',
          inputLabel: 'Claim under debate',
          input: 'The 1,000 Genomes Project enables mapping of rare variants with larger penetrance effects than common variants.',
          outputLabel: 'Top retrieved evidence & discriminating prompt',
          output: `[Hit ★ s7] "Uncommon or rare genetic variants can easily create synthetic associations credited to common variants..."
[Hit ★ s2] "Variants much less common than the associated one may create synthetic associations..."

Ask-Why Experiment Prompt:
→ What observation in a fine-mapping cohort would falsify synthetic rare-variant association here?`,
        },
        {
          tab: 'Claim B · Thalassemia Anemia (Contradicted)',
          verdict: 'CONTRADICT · 2/3 gold hits',
          verdictTone: 'hold',
          inputLabel: 'Claim under debate',
          input: 'A high microerythrocyte count raises vulnerability to severe malarial anemia in homozygous alpha(+)-thalassemia.',
          outputLabel: 'Top retrieved evidence & discriminating prompt',
          output: `[Hit ★ s1] "Individuals homozygous for alpha(+)-thalassemia have microcytosis and an increased erythrocyte count."
[Hit ★ s10] "The increased erythrocyte count and microcytosis may contribute substantially to protection against severe malarial anemia."

Ask-Why Experiment Prompt:
→ Both sides agree microerythrocyte count rises—what hemoglobin-loss measurement separates protection from vulnerability?`,
        },
      ],
      tabs: {
        how: 'Combines a two-stage `FrontierHybridVerifier` (`Reciprocal Rank Fusion` of biomedical `BM25` + 96-dim subword LSA + `EntityNumericNegationIndex` followed by a 26-feature `CrossFeatureReranker` and `SplitConformalStanceClassifier`) with structured Socratic `why_questions` and control-well synthesis.',
        guarantee: 'Trained strictly on `SciFact` `train` (`0` dev overlap, eval docs excluded from IDF): lifts dev `hit@3` `0.818 -> 0.909`, reaches `90.7%` 3-way conformal coverage and `100.0%` `ConflictBank` detection, and fails closed on malformed negative certificates.',
        status: 'Merged on `main` (`6f4887a` + `LabAskWhyLean` CI): 8-corpus SHA-256-verified real benchmark (`SciFact`, `PubMedQA`, `ConflictBank`, `FaithEval-Inconsistent`, `CLAIMCHECK`, `SciVer`, `ChemBench`, `LitQA2`) and 14-dataset registry.',
      },
    },

    'lab-decide': {
      headline: 'Give calibrated error bars when a molecule is in familiar territory—and explicitly say "I don’t know" when it isn’t.',
      why: 'Standard regression models happily output confident solubility or yield numbers on chemistry completely outside their training set, wasting expensive bench runs.',
      metrics: [
        ['92.4%', '20-seed ESOL cov_in'],
        ['11 / 11', 'informative real gates'],
        ['0.000', 'campaign OOD picks'],
      ],
      playgroundPrompt: 'Query a candidate molecule against the calibrated ESOL trust gate:',
      demos: [
        {
          tab: 'Familiar Small Molecule (Answer)',
          verdict: 'TRUSTED · 90% Interval',
          verdictTone: 'pass',
          inputLabel: 'Candidate descriptors (ESOL)',
          input: 'MW = 180.2, Rotatable Bonds = 3, Rings = 1, H-Bond Donors = 1, TPSA = 63.6 Å²\n5-NN distance to training set = 0.41 (threshold <= 0.758)',
          outputLabel: 'Decision API response',
          output: `Status   : ANSWER (inside 80th-percentile calibration distance)
Interval : [-2.41, +0.63] log(mol/L)  (90% split conformal, q = ±1.522)
Expected : In-region test MAE is 0.656 (vs 0.892 outside). Safe to pass to planner.`,
        },
        {
          tab: 'Out-of-Domain Macrocycle (Abstain)',
          verdict: 'ABSTAIN · Uncalibrated',
          verdictTone: 'hold',
          inputLabel: 'Candidate descriptors',
          input: 'MW = 612.4, Rotatable Bonds = 11, Rings = 4, Fluorinated macrocycle\n5-NN distance to training set = 1.38 (exceeds threshold 0.758)',
          outputLabel: 'Decision API response',
          output: `Status   : ABSTAIN ("I don't know — outside calibrated region")
Reason   : Nearest training neighbors are too far (1.38 > 0.758); empirical coverage drops outside this boundary.
Next step: Queue 1 calibration measurement at the bench to expand the trusted region.`,
        },
        {
          tab: 'After 3 Lab Data Rounds',
          verdict: 'EXPANDED · 94.9% Coverage',
          verdictTone: 'pass',
          inputLabel: 'Active trust-region expansion',
          input: 'Add nearest out-of-region compounds into training across 3 rounds (676 -> 696 -> 716 -> 726 compounds)',
          outputLabel: 'Calibration trace',
          output: `Round 0 : 79.6% answered · 92.2% in-trust coverage · MAE 0.656
Round 2 : 94.6% answered · 93.8% in-trust coverage · MAE 0.640
Round 3 : Calibration holds near ≥90% target while in-region MAE stays ~0.64.`,
        },
      ],
      tabs: {
        how: 'Pairs Huber GBDT and `LightGBM` surrogates with Mondrian `cqr_r` intervals, `onehot_morgan` HTE encodings, train-only `ensemble_mahalanobis` kNN gating, deterministic balanced group-packing splits (`<= 0.67` pp error), and 6-round sequential BO campaigns (`tr_conformal_ucb`, `lightgbm_cqr_tr_ucb`).',
        guarantee: 'Achieves `11/11` `gate_informative = True` (`5/5` seeds `MAE_in < MAE_out`) across all 11 real CSV benchmarks, scores `autolab_wire` candidates with the frozen SHA-pinned ESOL model (`n_calib = 169`, `thr = 0.6750`), and never widens `tau` on high-residual entries.',
        status: 'Merged on `main` (`f72af29`, 23 Lean 4.36.0 `#print axioms` theorems): 20-seed ESOL (`92.4%` inside cov), 11-dataset real-CSV benchmark, and 10-seed BO campaigns (`0.000` OOD picks, `0.10` Doyle B-H regret).',
      },
    },

    'buy-or-make': {
      headline: 'Before planning a synthesis, check if you can simply buy the molecule—or make it in two steps from cheap catalog building blocks.',
      why: 'An autonomous lab shouldn’t spend two days synthesizing a compound sold for $15, nor trust hallucinated vendor prices when public catalogs omit pricing.',
      metrics: [
        ['69.2%', 'Retro* 5-step solve'],
        ['43.0%', 'USPTO-50K top-10'],
        ['Strict null', 'never invents prices'],
      ],
      playgroundPrompt: 'Test how candidate molecules are triaged:',
      demos: [
        {
          tab: 'Aspirin (Directly Buyable)',
          verdict: 'BUYABLE · In Catalogs',
          verdictTone: 'pass',
          inputLabel: 'Candidate SMILES',
          input: 'CC(=O)Oc1ccccc1C(=O)O   (max_steps = 2)',
          outputLabel: 'Triage result',
          output: `Status      : buyable (0 synthesis steps needed)
Vendors     : Listed by >= 25 chemical depositors in PubChem PUG-View
Listed cost : $0.42 / g (when local priced catalog supplied; null on unpriced public feeds)
SA / SCScore: SA = 1.58 · SCScore = 1.82`,
        },
        {
          tab: 'Novel Biphenyl Amide (2-Step Makeable)',
          verdict: 'MAKEABLE · <= 2 Steps',
          verdictTone: 'pass',
          inputLabel: 'Candidate SMILES',
          input: 'COc1ccc(C(=O)Nc2ccc(-c3ccccn3)cc2)cc1   (not in vendor stock)',
          outputLabel: 'Triage result',
          output: `Status      : makeable (1–2 step amide / Suzuki disconnection to purchasable leaves)
Leaves      : 4-methoxybenzoic acid [in stock] + 4-(pyridin-2-yl)aniline [in stock]
Cost bound  : Conservative leaf-only USD/g lower bound (excludes solvent, yield & labor)`,
        },
        {
          tab: 'Malformed SMILES (Rejected)',
          verdict: 'INVALID · Blocked Early',
          verdictTone: 'fail',
          inputLabel: 'Candidate SMILES',
          input: 'C1CC(invalid_ring',
          outputLabel: 'Triage result',
          output: `Status      : invalid (rejected by RDKit sanitization before any network or route call)
Guarantee   : Unverified molecules stay "unknown" or "invalid"—never guessed as makeable.`,
        },
      ],
      tabs: {
        how: 'Combines SQLite-cached PubChem/local vendor stock lookup with a `Retro*` best-first AND-OR multi-step planner (`44` atom-balanced acyclic/unimolecular SMARTS templates + train/val `USPTO-50K` lookup), unit-aware `USD/g` & MOQ cost bounds, and `SAscore`/`SCScore`.',
        guarantee: 'Missing catalog prices stay `null`, `USPTO-50K` test reactions have `0` index leakage, `BuyOrMakeLean` Lean 4.36.0 theorems audit stoichiometry and budget soundness in CI, and wire outputs stamp explicit `data_source` provenance.',
        status: 'Merged on `main` (`ec33997` + `BuyOrMakeLean` CI): `Retro*` lifts 240-target `PaRoutes n1/n5` + `SynPlanner` solve rate `2.1% -> 69.2%` (`10/10` convergent) and 500-target `USPTO-50K` top-10 `16.6% -> 43.0%` across 19 SPDX-gated sources.',
      },
    },

    'labshift': {
      headline: 'Pack multi-step jobs onto shared lab instruments without missing incubation windows.',
      why: 'In a wet lab, finishing a 37 °C incubation and waiting 40 minutes because the plate reader is busy ruins the assay—naive first-come scheduling violates max-wait limits.',
      metrics: [
        ['30 / 30', 'CP-SAT feasible suites'],
        ['0 vs 13', 'window violations vs greedy'],
        ['116.7 m', 'mean makespan (vs 129.8 m)'],
      ],
      playgroundPrompt: 'Compare greedy dispatch vs OR-Tools CP-SAT under contention:',
      demos: [
        {
          tab: 'Greedy List Scheduler (Fails Windows)',
          verdict: 'INFEASIBLE · 13 Window Violations',
          verdictTone: 'fail',
          inputLabel: '30-instance multi-instrument suite (5 pools: L, I, R, C, W)',
          input: 'labshift bench --solver greedy benchmarks/   (contended medium_04 instance)',
          outputLabel: 'Checker verdict',
          output: `Suite feasible : 24 / 30 (fails 6 of 10 medium instances!)
medium_04      : 4 max_wait violations (plates sit idle after incubation waiting for reader)
Mean makespan  : 129.8 min  (0.012 s total CPU time)`,
        },
        {
          tab: 'OR-Tools CP-SAT Solver (Clears All 30)',
          verdict: '30/30 FEASIBLE · 0 Violations',
          verdictTone: 'pass',
          inputLabel: 'Exact interval-variable CP-SAT formulation (5 s cap)',
          input: 'labshift bench --solver cpsat --time-limit 5 benchmarks/',
          outputLabel: 'Checker verdict & ASCII Gantt',
          output: `Suite feasible : 30 / 30 (OPTIMAL on all small & half of medium; FEASIBLE on all large)
medium_04      : OPTIMAL makespan 136 min (vs 165 min greedy), 0 window violations
job_01 Gantt   : L[0–18] -> L[18–28] -> I[29–56] -> R[58–62]  (all min/max waits respected)`,
        },
      ],
      tabs: {
        how: 'Models chained wet-lab operations across shared station and `robot_arm` pools (`liquid_handler`, `incubator`, `plate_reader`, `centrifuge`, `washer`, `raman_spectrometer`, `lc_ms`) with release/deadline bounds, `min_wait`/`max_wait` windows, Jackson/Carlier energetic lower bounds, stdlib `solve_lns`, OR-Tools CP-SAT, and `PyJobShop`.',
        guarantee: 'Independent sweep-line checker validates every solver output and reports feasible-only summary means plus a valid lower-bound `gap%` for every solver—ready both as a fleet scheduler and an RLVR verifier.',
        status: 'Merged on `main` (`fc5bba5`): 30-instance v1 suite (`CP-SAT` `30/30`, `116.4m`), 20-instance planted hard tier (`CP-SAT` `20/20 OPT` vs `17/20` stdlib `LNS` vs `7/20` `greedy_repair`), native `stepbot` import, and JSSP/PSPLIB/Opentrons benchmarks.',
      },
    },

    'lab-automation-atlas': {
      headline: 'Keep a clean, link-checked map of real liquid handlers, cloud labs, open protocol languages, and benchmarks.',
      why: 'Lab automation standards are fragmented across vendor silos and academic formats; this index maps what already exists so we build adapters instead of reinventing formats.',
      metrics: [
        ['84', 'typed entries (7 cats)'],
        ['335', 'Lean #eval parity'],
        ['Weekly', 'DNS-pinned SSRF check'],
      ],
      playgroundPrompt: 'Browse the four layers of the open automation ecosystem:',
      demos: [
        {
          tab: 'Robots & Cloud Labs',
          verdict: 'Hardware & Foundries',
          verdictTone: 'pass',
          inputLabel: 'Benchtop liquid handlers & remote cloud foundries',
          input: 'Physical execution targets surveyed for Auto-Lab compilers',
          outputLabel: 'Indexed platforms',
          output: `Benchtop : Opentrons (OT-2, Flex) · Hamilton · Tecan · Automata · Biosero
Cloud    : Emerald Cloud Lab · Strateos · Ginkgo Bioworks · U of Toronto Acceleration Consortium`,
        },
        {
          tab: 'Open Software & DSLs',
          verdict: '12 Open Standards',
          verdictTone: 'pass',
          inputLabel: 'Protocol representations, device buses & orchestrators',
          input: 'Open-source stacks connected to stepbot, labshift & lab-decide',
          outputLabel: 'Indexed software',
          output: `Protocols & Control : Opentrons Python API v2 · PyLabRobot · Autoprotocol · LabOP · XDL · SiLA 2
Orchestration & BO  : WEI · Bluesky · Aquarium · Atlas (BO) · Google OR-Tools (CP-SAT)`,
        },
        {
          tab: 'Open Protocol Datasets',
          verdict: '6 Public Corpora',
          verdictTone: 'pass',
          inputLabel: 'Training and evaluation corpora (license-noted)',
          input: 'Sources feeding assayfold, lab-ears, and labbench-posttrain',
          outputLabel: 'Indexed datasets',
          output: `Corpora    : Wet Lab Protocols (WLP, MIT) · protocols.io · Bio-protocol
Benchmarks : LAB-Bench (CC-BY-SA-4.0, eval-only) · BioProBench (non-commercial) · BioPlanner`,
        },
      ],
      tabs: {
        how: 'Resolves hardware capability profiles and protocol IRs from an 84-entry `atlas.json` across 7 categories, evaluates compound SPDX (`AND`/`OR`/`WITH`) + `parent_licenses` lineage in 1-to-1 parity with `LabAtlasLean`, and runs DNS-pinned HTTPS SSRF link audits.',
        guarantee: 'Strictly pointer-only (`0` redistributed data, `0` vendor rankings), blocking `eval_only`, non-commercial, and non-canonical IPv4/IPv6 URLs before training or autonomous ingestion.',
        status: 'Merged on `main` (`b6455d9` + `LabAtlasLean` `#print axioms` & 335-case `#eval` parity CI): 84 verified entries across liquid handlers, cloud foundries, protocol IRs, `PyJobShop`/`LeRobot` solvers, procurement, and 2024-2026 open datasets.',
      },
    },

    'lab-rehearsal': {
      headline: 'Dry-run every pipetting protocol on a virtual 96-well deck—and remember past mistakes before running again.',
      why: 'Sending an unchecked LLM protocol straight to a liquid handler risks overflowing wells, aspirating air from empty troughs, or contaminating stock reagents with a used tip.',
      metrics: [
        ['5-Stage', 'Recall -> Twin -> Gate -> Run -> Log'],
        ['4 / 4', 'seeded fault types blocked'],
        ['0', 'bad commands sent to robot'],
      ],
      playgroundPrompt: 'Run a protocol through the virtual 96-well rehearsal loop:',
      demos: [
        {
          tab: 'Valid 8-Well Serial Dilution',
          verdict: 'PASS · 43 Commands Sent',
          verdictTone: 'pass',
          inputLabel: 'good_serial_dilution.json (20–300 uL single-channel pipette)',
          input: 'Distribute buffer, serially dilute sample A1 -> H1 with mixes, drop tips cleanly.',
          outputLabel: '5-stage rehearsal trace',
          output: `RECALL   : Passed previously in run #5
REHEARSE : 2 tips used · 8 plate wells filled (100 uL each) · tip off at end
VERIFY   : PASS (0 violations)
RUN      : Sent 43 commands to executor -> A1..H1 = 100 uL
WRITE    : Appended pass record to memory/runs.jsonl`,
        },
        {
          tab: 'Dirty Tip Reused in Buffer',
          verdict: 'BLOCKED · Cross-Contamination',
          verdictTone: 'fail',
          inputLabel: 'broken_tip_reuse.json',
          input: 'Dispense sample into A1, keep same tip attached, dip back into clean buffer reservoir:1.',
          outputLabel: '5-stage rehearsal trace',
          output: `RECALL   : WARNING — failed before in run #4 (no_tip_reuse)!
REHEARSE : Caught tip carrying ['sample'] entering res:1 containing ['buffer']
VERIFY   : FAIL (step 4 no_tip_reuse)
RUN      : BLOCKED by verify gate — 0 commands sent to the robot`,
        },
        {
          tab: 'Well Overfill (400 uL > 300 uL)',
          verdict: 'BLOCKED · Volume Overflow',
          verdictTone: 'fail',
          inputLabel: 'broken_overfill.json',
          input: 'Dispense 200 uL twice into 300 uL-capacity well plate:A1.',
          outputLabel: '5-stage rehearsal trace',
          output: `RECALL   : WARNING — failed before in run #3 (no_overfill)
VERIFY   : FAIL — step 5 plate:A1 would hold 400 uL > 300 uL max capacity
RUN      : BLOCKED by verify gate — 0 commands sent · logged to runs.jsonl`,
        },
      ],
      tabs: {
        how: 'Simulates 1- and 8-channel 96-well pipetting plus thermal evaporation (`incubate`/`seal`/`thaw`), hashes exact and skeleton trajectories against `runs.jsonl`, re-rehearses compiled `stepbot` IR via `from_stepbot`, and checks parity with the compiled Lean 4 `lab-rehearsal-check` binary.',
        guarantee: 'Never silently caps over-capacity volumes (`requested_volume_not_rehearsable`), blocks any `from_stepbot` round-trip volume/tip mismatch, and preserves distinct deck slots on multi-labware Opentrons fixtures.',
        status: 'Merged on `main` (`a889b23` + live `lab-rehearsal-check` Lean 4.36.0 differential CI): 6 bundled fixtures (`5/5` fault classes blocked), 12-run episodic ledger, and 14-dataset 2024-2026 protocol twin converters.',
      },
    },

    'lab-verify': {
      headline: 'Put a strict default-deny checker in front of model-generated SQL, Lean proofs, and lab protocols.',
      why: 'Half of plausible-looking wrong SQL queries parse cleanly, are read-only, and use valid table names—yet still return the wrong scientific answer.',
      metrics: [
        ['22 / 22', 'lab SQL agreement'],
        ['931 + 232', 'real EHRSQL-2024'],
        ['0', 'custom Lean axioms'],
      ],
      playgroundPrompt: 'Send a model-generated SQL query through the 4-layer gate:',
      demos: [
        {
          tab: 'Stacked DROP Injection (Stopped @ L2)',
          verdict: 'DENIED · Layer 2 Read-Only',
          verdictTone: 'fail',
          inputLabel: 'Candidate SQL',
          input: 'SELECT * FROM experiments; DROP TABLE samples;',
          outputLabel: '4-Layer Gate trace',
          output: `Layer 1 · Parse (sqlglot) : PASS
Layer 2 · Read-Only AST   : FAIL — 2 statements detected (Select, Drop)
Verdict                   : DENIED before touching the database.`,
        },
        {
          tab: 'Hallucinated Column (Stopped @ L3)',
          verdict: 'DENIED · Layer 3 Schema',
          verdictTone: 'fail',
          inputLabel: 'Candidate SQL',
          input: 'SELECT id FROM instruments WHERE calibrated_on > "2026-01-01";',
          outputLabel: '4-Layer Gate trace',
          output: `Layer 1 · Parse           : PASS
Layer 2 · Read-Only AST   : PASS
Layer 3 · Schema Check    : FAIL — unknown column "calibrated_on" in instruments`,
        },
        {
          tab: 'COUNT vs COUNT DISTINCT (Stopped @ L4)',
          verdict: 'DENIED · Layer 4 Execution',
          verdictTone: 'hold',
          inputLabel: 'Subtle semantic bug (passes syntax, read-only & schema!)',
          input: 'SELECT COUNT(experiment_id) FROM samples;   -- asks how many distinct experiments have samples',
          outputLabel: '4-Layer Gate trace',
          output: `Layers 1–3 (Parse / Read-Only / Schema) : ALL PASS (looks completely valid!)
Layer 4 · Execution / Property Match    : FAIL — returned (14,) vs reference (5,)
Key lesson: Syntax + schema gates alone let 7/14 wrong queries through; execution verification catches all 7.`,
        },
      ],
      tabs: {
        how: 'Runs candidate SQL through a 4-layer gate (`sqlglot` parse, AST + authorizer read-only, schema/join check, and Hopcroft-Karp float multiset + tie-aware `ORDER BY`), compiles Lean 4 proofs under `#print axioms`, and mints/verifies Ed25519/HMAC `lean-mcp/v1` capability envelopes.',
        guarantee: 'Rejects `"lean-mcp-dev-secret-v1"` by default, requires role-separated cryptographic supervisor co-signatures for frontier exceptions, and verifies NULL/date safety across 3 counterexample mutant DBs.',
        status: 'Merged on `main` (`a286050` + Lean 4.36.0 `#print axioms` CI): `22/22` lab SQL agreement, `931/931` answerable + `232/232` unanswerable abstentions on 317,875-row MIMIC-IV `EHRSQL-2024`, and 16 open SQL/Lean adapters.',
      },
    },

    'labbench-posttrain': {
      headline: 'Turn raw language models into verified Scientist and Operator policies without benchmark leakage or reward hacking.',
      why: 'In RL for science, models quickly learn to game naive rewards—writing long `<think>` essays or guessing formats—unless bonuses are strictly gated on code-checked scientific truth.',
      metrics: [
        ['49,139', 'multi-origin lab records'],
        ['0', 'cross-split group leaks'],
        ['8', 'anti-hack reward templates'],
      ],
      playgroundPrompt: 'Inspect the four pillars of the `labrl` post-training pipeline:',
      demos: [
        {
          tab: '1 · Leak-Free Data (SplitGuard)',
          verdict: '0 Cross-Split Groups',
          verdictTone: 'pass',
          inputLabel: '49,139 records across 20 chemistry, assay & robot sources',
          input: '40,790 train / 4,189 val / 4,160 test + 20,517 robot frames + LAB-Bench canary guard',
          outputLabel: 'Provenance & contamination rules',
          output: `Origins kept separate : measurement (29,399) · compute (13,990) · ml_prediction (5,667) · human (83)
SplitGuard            : Cryptographic holdout check + hard block on training over CC-BY-SA LAB-Bench`,
        },
        {
          tab: '2 · SFT -> MPO -> GDPO Pipeline',
          verdict: 'Dual-Engine SDK (`labrl`)',
          verdictTone: 'pass',
          inputLabel: 'CLI / Python SDK execution',
          input: 'labrl pipeline --corpus calisol23 --methods sft,dpo,mpo,ppo,grpo --smoke',
          outputLabel: 'Stage progression',
          output: `Stage 1 : SFT checkpoint (reference anchor for Reverse-KL)
Stage 2 : Offline DPO / Hybrid MPO (DPO + BCO + SFT) / On-Policy Distillation (TROPD)
Stage 3 : Online PPO (causal GAE / VAPO) & Multi-Reward GDPO + DAPO`,
        },
        {
          tab: '3 · Anti-Hack Verified Rewards',
          verdict: 'Exploit-Audited',
          verdictTone: 'pass',
          inputLabel: 'BioProBench (PQA / ORD / ERR / GEN) & CALiSol-23 electrolyte conductivity',
          input: 'python -m bioenvs.audit   # test scripted exploit policies against reward functions',
          outputLabel: 'Reward gating behavior',
          output: `Format / reasoning bonus : 0.0 unless core scientific/protocol checker passes first
<think> length cap       : Penalizes verbose scratchpad padding
Operator constraints     : Scores workspace AABB, joint limits & swept-point obstacle clearance`,
        },
      ],
      tabs: {
        how: 'Unifies Scientist and Operator post-training inside `labrl` (`TorchLocalEngine` + pinned `yaniguan/RL` `NeMoRLEngine`) with per-token `k3` and `sequence_exact` Reverse-KL SFT anchoring, 8 `VerifiedRewardTemplate` classes, and `LabPostTrainLean` GDPO/KL checks.',
        guarantee: 'Zero `cid|` fallbacks and zero cross-split scaffold/DOI leaks across 49,139 records, fail-closed `L3_WIRE_SCHEMA_REJECT` wire validation separating `CERTIFIED_POSITIVE` SFT from `CERTIFIED_NEGATIVE` DPO/MPO disproofs, and explicit `PENDING` status on A100/H100 runs (`#49`, `#18`).',
        status: 'Merged on `main` (`8dd44de` + `LabPostTrainLean` CI): 15/15 CPU smoke jobs, PubChem-resolved Lab v0 splits, pinned `yaniguan/RL` launch contract, `sequence_exact` Reverse-KL, and 9-corpus 2026 Open Science registry.',
      },
    },

    'twinstep': {
      headline: 'Automatically create "spot-the-mistake" and step-ordering pairs from valid liquid-handling protocols.',
      why: 'Real wet-lab failure logs are scarce. Deterministically injecting realistic errors (like flipping uL to mL or reading before incubating) gives post-training unlimited labeled contrast pairs.',
      metrics: [
        ['6', 'typed error injectors'],
        ['100%', 'DAG constraint satisfaction'],
        ['0', 'external runtime deps'],
      ],
      playgroundPrompt: 'Click an error injector to see how a clean protocol mutates into a labeled twin:',
      demos: [
        {
          tab: 'wrong_unit (uL -> mL)',
          verdict: 'CAUGHT · 1000x Volume Bug',
          verdictTone: 'fail',
          inputLabel: 'Original clean step (step 1)',
          input: '{"op": "transfer", "source": "stock:dye", "dest": "plate1:A1", "volume": 100, "unit": "uL"}',
          outputLabel: 'Generated corrupted twin & baseline check',
          output: `Mutated  : {"op": "transfer", ..., "volume": 100, "unit": "mL"}   (label: wrong_unit, step_index: 1)
Baseline : FLAGGED (100 mL exceeds [1, 300] uL well transfer bound — 100% recall on wrong_unit)`,
        },
        {
          tab: 'swap_order (Read Before Incubate)',
          verdict: 'CAUGHT · Causal Violation',
          verdictTone: 'fail',
          inputLabel: 'Original order (steps 3 -> 4)',
          input: 'Step 3: incubate plate1 at 37 °C for 30 min  ->  Step 4: read fluorescence at 520 nm',
          outputLabel: 'Generated corrupted twin & baseline check',
          output: `Mutated  : Step 3: read plate1 (520 nm)  ->  Step 4: incubate 37 °C (label: swap_order)
Baseline : FLAGGED (stage-barrier violation: plate read precedes incubation)`,
        },
        {
          tab: 'Subtle In-Range Drift (Needs Model)',
          verdict: 'MISSED BY RULES · RL Target',
          verdictTone: 'hold',
          inputLabel: 'Why learned models are needed beyond static rules',
          input: 'Incubation shifted 37 °C -> 62 °C, or independent buffer transfer dropped',
          outputLabel: 'Benchmark insight (twinstep eval)',
          output: `Rule baseline : 66.7%–72.2% overall accuracy (misses plausible in-range corruptions without reference context)
Step ordering : 100% pairwise causal constraint satisfaction via topological sort.`,
        },
      ],
      tabs: {
        how: 'Validates 96/384-well workflows (`transfer`, `mix`, `incubate`, `wash`, `read`), builds per-well stage-barrier dependency DAGs, runs 6 seeded fault injectors across 24 split-isolated protocols (`8 train / 4 val / 12 test`), and trains a zero-leakage stdlib graph-feature fault localizer.',
        guarantee: 'Pure Python standard-library runtime (`dependencies = []`) with zero train/test protocol overlap, clean multi-stage ELISA/TMB dataflow rules, and 100% causal DAG step-ordering satisfaction.',
        status: 'Merged on `main` (`a781fc0`, 96 passing tests): 20-seed held-out test ED `57.7% -> 81.3%` (`87.3%` ProcessBench balanced, `70.7%` `step_index`) plus `WLP`, `BioProBench`, `BioPlanner`, and `Opentrons` public corpora.',
      },
    },

    'labfill': {
      headline: 'Check thousands of protocols in one PyTorch batch—and stop wasting 70% of GPU compute on padding tokens.',
      why: 'Protocol traces are short and uneven (8 to 512 tokens). Naive padded batches leave GPUs mostly multiplying zeros instead of learning protocol logic.',
      metrics: [
        ['5.42x', 'packed BF16 tok/s speedup'],
        ['92.1%', 'useful tokens (vs 30.6%)'],
        ['225.8k', 'protocols/s validated'],
      ],
      playgroundPrompt: 'Compare how sequence batching & tensorized recipes perform:',
      demos: [
        {
          tab: 'Recipe 4 · Fill One GPU (Packing)',
          verdict: '5.42x Real Tokens/s',
          verdictTone: 'pass',
          inputLabel: '4-layer d=256 Transformer on lognormal 8..512 token protocol streams',
          input: 'Compare naive padded FP32 batching against length-bucketing and BF16 sequence packing',
          outputLabel: 'Measured 1-thread Xeon AMX-BF16 ablation',
          output: `Padded FP32 baseline   : 1,510 real tok/s · only 30.6% useful tokens (69.4% wasted on pad!)
Length bucketed FP32   : 3,150 real tok/s · 58.9% useful tokens (2.09x)
Sequence packed + BF16 : 8,181 real tok/s · 92.1% useful tokens (5.42x speedup)`,
        },
        {
          tab: 'Recipe 1 & 5 · Batched Check & Plate Twin',
          verdict: '225.8k proto/s · 3,823 plates/s',
          verdictTone: 'pass',
          inputLabel: 'Vectorized 24-step protocol rules & 128 parallel 96-well dry-runs',
          input: 'Check volume, pipette range, tip, thaw, seal, temp & centrifuge rules in one tensor op',
          outputLabel: 'Measured throughput',
          output: `Batched Torch Checker (B=16,384) : 225,851 protocols/s (1.24x plain Python on 1 CPU thread; built for GPU)
Batched 96-Well Rehearsal        : 3,823 plates/s (128 plates x 104 steps in 33.5 ms, volume conserved)`,
        },
        {
          tab: 'Recipe 2 · Generate, Check & Repair',
          verdict: '163k cand/s Filtering',
          verdictTone: 'pass',
          inputLabel: 'Filter N=4,096 sampled candidates & try K=24 single-edit repairs in parallel',
          input: 'python recipes/02_twins_and_repair.py',
          outputLabel: 'Measured filter & repair',
          output: `Generate-Check-Keep : 163,078 candidates/s (0.0% false positives on valid protocols)
Intent-safe repair  : Repairs wrong_pipette, missing_tip, skip_thaw, sealed_plate, bad_temp at ~4,500 proto/s.`,
        },
      ],
      tabs: {
        how: 'Implements five PyTorch recipes—120-bit overflow-free batched protocol checking (up to `10,000 mL`), `K=26` twin repair with `exact_recovery_rate`, DAG beam search, Ding et al. (2024) `O(N log N)` Segment-Tree OBFD sequence packing, and 96-well plate rehearsal.',
        guarantee: 'Continuously verified in CI against live `YLM` `LabLean` (`310/310` compiled, `308/310` verdict match, `0` unexplained diffs) and `12,000` random `300 mL` reservoir pairs, with 5-seed `[min, max]` intervals and GPU columns marked `PENDING_GPU`.',
        status: 'Merged on `main` (`38f23ee`, 86 passing tests): 120-bit checker, compact twin/DPO `step_index`, live 310-protocol `LabLean` CI, `O(N log N)` OBFD across 5 public corpora (`SMolInstruct` `98.8%`, `ORD` `90.8%`), and `PENDING_GPU` A100/H100 harness.',
      },
    },

    'lab-ears': {
      headline: 'Read numbers cleanly out of protocol prose—and hear when a benchtop centrifuge or pump starts sounding wrong.',
      why: 'Instructions arrive as messy text ("spin at 12,000 rpm for 5 min at 4 °C"), while worn bearings or unbalanced rotors often hum abnormally before an instrument fails.',
      metrics: [
        ['0.876', 'WLP BIOES micro-F1'],
        ['< 20 ms', 'latency per 10 s clip'],
        ['300–3400 Hz', 'speech band dropped'],
      ],
      playgroundPrompt: 'Switch between the written-protocol channel and the machine-audio channel:',
      demos: [
        {
          tab: 'Written Protocol Slot Extraction',
          verdict: 'Time F1 0.91 · Amount F1 0.79',
          verdictTone: 'pass',
          inputLabel: 'Raw Wet Lab Protocols (WLP) sentence',
          input: '"Add 250 uL lysis buffer, incubate at 65 °C for 15 min, then centrifuge at 12,000 x g for 2 min."',
          outputLabel: 'Extracted structured spans',
          output: `Amount      : "250 uL"        (test F1 = 0.789 across 1,011 gold spans)
Temperature : "65 °C"         (test F1 = 0.774 across 509 gold spans)
Time        : "15 min", "2 min" (test F1 = 0.907 across 810 gold spans)
Speed       : "12,000 x g"    (test F1 = 0.748 across 155 gold spans)`,
        },
        {
          tab: 'Privacy-Safe Machine Sound Anomaly',
          verdict: 'FLAGGED · Speech Stripped',
          verdictTone: 'hold',
          inputLabel: '10 s contact-mic clip during step 4 (16 kHz WAV, normal-only training)',
          input: '64-bin log-mel spectrogram with --speech-band drop (removes 300–3400 Hz human voice band)',
          outputLabel: 'Emitted run-ledger JSONL event',
          output: `{"schema": "lab-ears/audio-event/v1", "instrument_id": "centrifuge-01", "step": 4,
 "detector": "gaussian", "score": 12.5, "threshold": 10.0, "flagged": true,
 "speech_band_dropped": true, "raw_audio_kept": false}   // < 6 ms on 1 CPU thread`,
        },
      ],
      tabs: {
        how: 'Pairs a zero-leakage 17-state `PA-II` `BIOES` sequence tagger (`0.876` exact / `0.897` overlap test micro-F1; `0.875` on SHA-unseen protocols) and regex baseline on WLP with window-matched `2 s` streaming `Gaussian`/`kNN`/`Autoencoder` detectors and harmonic-speech-rejecting cavitation interlocks.',
        guarantee: 'Fail-closed `L2_SPEECH_PRIVACY_BLOCK` wire gate rejecting any attached acoustic or interlock event lacking `speech_band_dropped: True`, `raw_audio_saved: False`, and `retained_bands_hz: [[0, 255], [3464, 8000]]`.',
        status: 'Merged on `main` (`eab305f` + `LabEarsLean` CI): zero-leakage WLP `BIOES` tagger, window-matched streaming calibration, harmonic-speech interlock rejection, and 12-dataset 2024-2026 sensory registry.',
      },
    },

    'stepbot': {
      headline: 'Compile short, readable YAML step lists into deterministic Opentrons Python protocols—and simulate every uL before bench time.',
      why: 'Hand-writing 120 lines of imperative Opentrons Python boilerplate for a serial dilution invites off-by-one well typos, tip exhaustion, and well overflows.',
      metrics: [
        ['apiLevel 2.16', 'deterministic Python output'],
        ['86–131', 'simulated commands verified'],
        ['Dual check', 'real Opentrons or built-in mock'],
      ],
      playgroundPrompt: 'See how high-level YAML compiles and catches liquid errors:',
      demos: [
        {
          tab: '2-Fold Serial Dilution YAML -> Python',
          verdict: 'OK · 100 Sim Commands',
          verdictTone: 'pass',
          inputLabel: 'Input YAML (examples/dilution_series.yaml)',
          input: `steps:
  - dilution_series:
      source: reservoir:A1
      diluent: reservoir:A2
      first_well: plate:A1
      n: 8
      factor: 2.0
      final_volume: 100`,
          outputLabel: 'Compiled Opentrons API v2 & simulator check',
          output: `Lowered to : diluent distribute -> stock transfer -> 7 serial transfers w/ mix_after -> excess trash discard
Generated  : metadata = {"apiLevel": "2.16"} · deterministic slot & mount ordering
Simulator  : OK (opentrons: 100 commands | built-in --mock: 86 commands)`,
        },
        {
          tab: 'Compile-Time Well Overflow Catch',
          verdict: 'REJECTED AT COMPILE TIME',
          verdictTone: 'fail',
          inputLabel: 'Invalid YAML exceeding Corning 96-well 360 uL capacity',
          input: 'steps:\n  - transfer: {src: reservoir:A1, dst: plate:A1, volume: 250}\n  - transfer: {src: reservoir:A2, dst: plate:A1, volume: 200}',
          outputLabel: 'Compiler diagnostic',
          output: `CompileError : Step 2 would bring plate:A1 to 450.0 uL, exceeding labware capacity 360.0 uL.
Result       : Rejected before any .py file is emitted or run on an OT-2.`,
        },
      ],
      tabs: {
        how: 'Validates OT-2 (`2.16`) and Flex (`2.18–2.20`) decks, `30` labware specs, `16` 1-/8-channel pipettes, canonical two-stage 8.8.2 stroke splits, destination-contact lineage (`bottom` vs `top`), and 4 liquid rheology profiles into deterministic Python.',
        guarantee: 'Rejects `NaN`/`Infinity` across all numeric fields, enforces `lean-mcp/v1` epoch/nonce dispatch, and achieves `100.0%` action-and-tip parity (`ALLOWED_DIFFERENCES = {}`) between `MockProtocolContext` and live `opentrons.simulate` `8.8.2`.',
        status: 'Merged on `main` (`ffd1347`, 278 passing tests, `mypy --strict` 0 errors): `311/311` seeded protocols + `36/36` public multi-step wet-lab assays (`3,607` actions, `971` tips) verified 100% against `opentrons.simulate` `8.8.2`.',
      },
    },

    'lab-hands': {
      headline: 'Plan collision-free pipette paths around bottles on crowded decks—and prepare last-centimeter touch for clear glass.',
      why: 'Straight-line arm moves smash pipette tips into tall reagent bottles, and RGB-D depth cameras fail on transparent tubes, menisci, and clear 96-well plates.',
      metrics: [
        ['100 / 100', 'obstacle-free RRT trials'],
        ['10 of 10', 'straight moves would crash'],
        ['70.6 ms', 'mean CPU plan + shortcut'],
      ],
      playgroundPrompt: 'Compare naive joint interpolation against RRT + path shortcutting:',
      demos: [
        {
          tab: 'Reach Well F5 Past Reagent Bottle',
          verdict: '100% CLEAR · 2.08 rad Path',
          verdictTone: 'pass',
          inputLabel: '2-link planar arm holding pipette tip -> SBS 96-well plate (9 mm pitch)',
          input: 'Target well #65 -> F5 (row-major) / A9 (column-major), obstructed by reagent bottle & rack wall',
          outputLabel: 'Motion planner comparison (10 wells x 10 seeds)',
          output: `Straight joint-space move : COLLISION on 10 of 10 target wells!
Goal-biased RRT           : 100 / 100 trials succeeded (mean 70.6 ms, max 278.4 ms on CPU)
Path shortcutting         : Trims jerky RRT path from 2.44 rad -> 2.08 rad smooth clearance.`,
        },
        {
          tab: 'Why Touch Lives With Hands',
          verdict: 'Visuo-Tactile Roadmap',
          verdictTone: 'hold',
          inputLabel: 'The transparent-vessel blindspot in wet labs',
          input: 'Clear glass vials, pipette tip seating, and screw-cap torque lack reliable depth edges',
          outputLabel: 'Curated open datasets & policies in repo',
          output: `Transparent depth : TransCG · ClearGrasp · Vector-LabPics
Tactile sensing   : DIGIT / Touch-Slide · Sparsh · GelSight · Touch-and-Go
Learned policies  : ACT · Diffusion Policy · OpenVLA · pi0 · cuRobo · AutoBio pipette sim`,
        },
      ],
      tabs: {
        how: 'Implements 6-DoF UR5e, 7-DoF Franka Panda, and 4-DoF Opentrons Flex PoE/DH kinematics, 3D capsule-AABB continuous swept collision checking, `RRT-Connect` + `Informed RRT*` + `TOPP-RA`, 2D nonlinear Bessel slosh + `ZV`/`ZVD`/`EI` shapers, and active spiral Bayesian tactile insertion.',
        guarantee: 'Evaluates all 4 insertion regimes on the exact same `0.70 mm` SBS chamfer and 3D Whitney/Coulomb contact mechanics (`99.0%` active spiral vs `1.2%` open-loop & `19.0%` local shear), and validates canonical LeRobot `(T, 7)` & Opentrons `(T, 3)` mm shapes.',
        status: 'Merged on `main` (`e296fb5`, 80 passing tests + `LabHandsLean`): UR5e/Panda `TOPP-RA` (`100%` 3D success), `EI` slosh (`10.2x` ringdown cut), `495/500` active tactile insertion, and 12 open robot/depth/tactile corpora.',
      },
    },

    'lab-feet': {
      headline: 'Compress large teachers into tiny int8 and 4-bit students so routine lab checks run on a cheap board next to the bench.',
      why: 'A benchtop monitor or safety reflex shouldn’t stall when cloud Wi-Fi hiccups or burn expensive A100 hours on routine local classifications.',
      metrics: [
        ['35x', 'fewer parameters (85k -> 2.4k)'],
        ['250x', 'smaller weights (340 KB -> 1.36 KB)'],
        ['3.86 us', 'median batch-1 CPU pass'],
      ],
      playgroundPrompt: 'Compare the teacher against distilled and quantized students:',
      demos: [
        {
          tab: 'Teacher vs Student (35x Smaller)',
          verdict: '97.4% Acc · 2.5x Faster',
          verdictTone: 'pass',
          inputLabel: 'MLP (256, 256) teacher vs single-layer (32) student',
          input: 'python demo/distill_quantize.py   (2,000 single-sample batch-1 forward passes on CPU)',
          outputLabel: 'Measured accuracy & latency',
          output: `Teacher (256,256) FP32     : 97.78% acc · 85,002 params · 340,008 B · 9.51 us
Student (32) hard-label    : 97.41% acc ·  2,410 params ·   9,640 B · 3.82 us
Student (32) distilled T=4 : 96.85% acc ·  2,410 params ·   9,640 B · 3.83 us (honestly notes hard-label beat T=4 here!)`,
        },
        {
          tab: 'INT8 & 4-Bit Weight Quantization',
          verdict: '0.0% Drop @ INT8 · 1.36 KB @ 4-Bit',
          verdictTone: 'pass',
          inputLabel: 'Symmetric per-tensor weight quantization on distilled student',
          input: 'Pack weights + fp32 biases + 1 fp32 scale per tensor; check agreement with FP32 student',
          outputLabel: 'Footprint & agreement',
          output: `Distilled INT8  : 96.85% acc · 2,544 B (1.0000 agreement with FP32 student!)
Distilled 4-bit : 96.48% acc · 1,360 B (0.9889 agreement · 250x smaller than teacher)
Honest caveat   : NumPy dequantizes before matmul—storage drops 250x; real runtime speedup needs llama.cpp / ExecuTorch.`,
        },
      ],
      tabs: {
        how: 'Compares hybrid `T^2`-scaled `KL+CE` against matched same-trainer `CE` controls over 10 seeds, quantizes MLP and `39.1k`-param `SpectralResNet1D` models via `WHT+GPTQ W4A8`, exports freestanding C99 & ONNX `opset >= 21` `qlinear` (`int32` output), and evaluates `TTN+CRC` drift adaptation.',
        guarantee: 'Enforces fail-closed `autolab_wire` calibration and accuracy floors, separates `(dequantized fp32 timing)` from `(int32)` passes, and verifies `0.000000` diff against `onnxruntime` (`>= 0.99` C99 parity) in CI.',
        status: 'Merged on `main` (`e6e0600`, 45 passing tests + `LabFeetLean`): `0.9352` 4-bit `SpectralResNet1D` on `MNIST-1D`, `66.0%–88.1%` `TTN+CRC` accepted accuracy across drifted UCI Gas Batches `4..9`, and 10 SHA-256-pinned open corpora.',
      },
    },

    'lab-attrib': {
      headline: 'After a wet-lab run finishes, separate robot glitches and unreacted precursor peaks from proof-carrying scientific truth.',
      why: 'Pre-execution gates keep a robot from crashing, but raw readouts still lie: a dry pipette draw looks like a negative biochemical result, and overlapping precursor peaks look like a brand-new crystal phase.',
      metrics: [
        ['30', 'Lean 4 theorems (0 sorry)'],
        ['51', 'pinned real spectra'],
        ['0.0%', 'A-Lab & Raman FDR'],
      ],
      playgroundPrompt: 'Inspect how lab-attrib classifies post-run telemetry and spectra before touching scientific memory:',
      demos: [
        {
          tab: 'Unreacted Precursor XRD (Quarantined)',
          verdict: 'AMBIGUOUS · Route to Raman/TEM',
          verdictTone: 'hold',
          inputLabel: 'Clean robot run, but multi-peak diffractogram matches precursors A+B',
          input: 'executionClean = true · NNLS precursor overlap = 96.4% (> 12.0% cap) · missing 41.5° target line',
          outputLabel: 'LabAttribLean verdict & EVOI router',
          output: `Outcome  : AMBIGUOUS_CHARACTERIZATION (admitToScientificMemory = false)
Theorem  : unidentifiable_spectrum_never_certified (blocks A-Lab ghost-phase false positive!)
Next step: EVOI router selects low-cost Raman check instead of writing a false hit.`,
        },
        {
          tab: 'Cavitation Glitch vs True Negative',
          verdict: 'PROOF-CARRYING NEGATIVE',
          verdictTone: 'pass',
          inputLabel: 'Clean acoustic, timing, tactile & +/- controls with flat optical signal',
          input: 'acousticNormal=true · waitWindow<=15m · posCtrl=PASS · blank=CLEAN · R_wp=4.2% · signal < hitFloor',
          outputLabel: 'Certified ledger receipt',
          output: `Outcome  : CERTIFIED_NEGATIVE (admitToScientificMemory = true)
Theorem  : certified_negative_sound (all 6 physical controls + 2 identifiability bounds verified)
Ledger   : Appended with SHA-256 chain receipt -> safe constraint for BO & RLVR.`,
        },
      ],
      tabs: {
        how: 'Combines a 30-theorem Lean 4.36.0 blame calculus (`LabAttribLean`, `#print axioms` audited) with shift-tolerant Golden-Section + Pseudo-Voigt `L1-NNLS` XRD/Raman deconvolution, MS/MS Spectral Entropy + 2-component chimera detection, `EVOI` routing, and SHA-256 `CertifiedLedger` chains.',
        guarantee: 'Benchmarked on 51 SHA-256-pinned real spectra (`A-Lab GPSS` XRD `0.0%` FDR & `75.0%` recall, `RRUFF/ROD` Raman `0.0%` FDR, `MassSpecGym` `82.4%` Top-1), while failing closed (`L4_ATTRIB_SCHEMA_REJECT`) on malformed wire telemetry.',
        status: 'Merged on `main` (`9a4b119` + 30-theorem `LabAttribLean` CI): 51-asset real spectra benchmark, 9-round ESOL stepping-stone campaigns, 5-page LaTeX monograph (`paper/main.pdf`), and 9 open characterization datasets.',
      },
    },
  };

  window.AutoLabStories = { STORIES };
})();
