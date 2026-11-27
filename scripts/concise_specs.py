"""Hand-curated, ultra-concise scannable specs for all 15 Auto-Lab repositories.

Each field is strictly 1 short line (~8-16 words) so cards scan in 5 seconds.
"""

from __future__ import annotations

from typing import Any

CONCISE_SPECS: dict[str, dict[str, Any]] = {
    "lab-ask-why": {
        "hook": "Does not pick a winner—surfaces the evidence on each side and names the test that settles it.",
        "flow": ["Claim + abstracts", "BM25 rationale ranker", "Opposing reasons + 'why' test"],
        "kpis": [["0.789", "SciFact recall@3"], ["14", "open QA corpora"], ["0", "LLM calls in baseline"]],
        "short": {
            "object": "Surface supporting/contradicting sentences and ask what experiment changes minds.",
            "data": "SciFact dev (209 pairs) + 14-corpus 2019-2026 registry (LABBench2, PeerQA-XT, SciVer, ConflictBank, ChemBench).",
            "model": "Pure-NumPy BM25 sentence ranker + 3 structured Socratic question templates.",
            "training": "Zero-training lexical baseline (0.789 recall@3 vs 0.528 random).",
            "history": "6236123 SciFact probe -> 40af81d Lean/wire audit -> b8a9d51 14-dataset 2026 registry.",
            "property": "Treats SUPPORT (0.80) and CONTRADICT (0.78) symmetrically; blocks eval_only training.",
        },
    },
    "lab-decide": {
        "hook": "Answers only inside its calibrated zone, says 'I don't know' outside, and grows with new data.",
        "flow": ["6 RDKit descriptors", "GBDT + kNN trust gate", "90% interval or ABSTAIN"],
        "kpis": [["92.2%", "in-trust coverage"], ["0.656", "in-trust MAE"], ["11", "calibration corpora"]],
        "short": {
            "object": "Gate experiment proposals by conformal uncertainty and distance to training data.",
            "data": "Delaney ESOL (1,128) + 10 open calibration corpora (BigSolDB v2.2, AqSolDB, CALiSol-23, ADME, BH-HTE-OOD 2026).",
            "model": "Gradient boosting + split conformal (90%) + 5-NN 80th-pct trust boundary.",
            "training": "Supervised GBDT fit + 3 active boundary-expansion rounds.",
            "history": "41dae77 ESOL conformal demo -> 6957f12 Lean/wire audit -> e37de97 11-dataset 2026 registry.",
            "property": "Lower error inside trust zone (0.66 vs 0.89 MAE) with strict leakage-column exclusion.",
        },
    },
    "buy-or-make": {
        "hook": "Buy it now or make it in N steps? Strict catalog lower bounds, never invented prices.",
        "flow": ["Candidate SMILES", "PubChem + 2-step SMARTS", "buyable | makeable | unknown"],
        "kpis": [["5 ms", "cached / mol"], ["19", "SPDX-gated corpora"], ["null", "when unlisted"]],
        "short": {
            "object": "Classify molecules as buyable, makeable in <= N steps, or unknown with cost bounds.",
            "data": "PubChem + 19 SPDX-gated sources incl. PaRoutes 2.0, ChEMBL 37, SureChEMBL, COCONUT 2.0, ORDerly, Syntheseus & SynPlanner.",
            "model": "Vendor lookup + 14 RDKit SMARTS disconnections (or AiZynthFinder) + SA/SCScore.",
            "training": "Deterministic search + pretrained MIT SCScore weights (no training in repo).",
            "history": "76991c8 v0.1 release -> 5fd1afb Lean/wire audit -> 3be1f4a 19-source 2026 corpora.",
            "property": "Missing prices stay null; mixed currencies are never silently compared.",
        },
    },
    "labshift": {
        "hook": "Schedule multi-step wet-lab jobs across shared instruments without breaking wait windows.",
        "flow": ["Jobs + wait windows", "Greedy or OR-Tools CP-SAT", "Conflict-free Gantt"],
        "kpis": [["30 / 30", "CP-SAT feasible"], ["116.7 m", "mean makespan"], ["0", "window violations"]],
        "short": {
            "object": "Assign chained lab operations to shared instrument pools under min/max wait bounds.",
            "data": "30 seeded synthetic benchmarks (small / medium / large, seeds 1000..1209).",
            "model": "Exact sweep-line checker + myopic greedy baseline + CP-SAT interval solver.",
            "training": "Combinatorial optimization (no neural training; ready as RLVR verifier).",
            "history": "124a6d7 30-instance suite -> 6985986 arm transit & greedy_repair -> ebc7f19 Lean/wire & >100-job CP-SAT.",
            "property": "CP-SAT clears all 13 max_wait violations left by greedy scheduling.",
        },
    },
    "lab-automation-atlas": {
        "hook": "A checked, zero-hype map of lab robots, cloud foundries, protocol DSLs, and open datasets.",
        "flow": ["Ecosystem URLs", "Weekly HTTP link check", "70-entry JSON & MD atlas"],
        "kpis": [["70", "checked entries"], ["17", "open datasets"], ["0", "copied vendor data"]],
        "short": {
            "object": "Index liquid handlers, cloud labs, open automation software, and protocol corpora.",
            "data": "70-entry pointer atlas (17 open datasets incl. FineBio, ChemBench, BixBench, MassSpecGym, OMAT24, COD/ROD, DROID).",
            "model": "Human-curated ontology + automated URL health script (no ML model).",
            "training": "None (reference atlas; grounds tool & dataset selection across Auto-Lab).",
            "history": "f2e2e83 link-checked release -> cab4852 Lean/wire audit -> 3b7d259 70-entry 2026 atlas.",
            "property": "Pointer-only MIT index: copies zero external data and ranks zero vendors.",
        },
    },
    "lab-rehearsal": {
        "hook": "Recall past crashes, dry-run on a virtual 96-well deck, block bad runs, write outcomes back.",
        "flow": ["JSON step list", "Recall + 96-well twin", "PASS to robot or BLOCK + log"],
        "kpis": [["4 / 4", "fault classes caught"], ["14", "protocol datasets"], ["100%", "recall warning"]],
        "short": {
            "object": "Catch volume, empty-well, overfill, and tip-reuse errors before touching hardware.",
            "data": "5 bundled JSON protocols + runs.jsonl + 14-dataset catalog (Opentrons v6-v8, FineBio, BioPlanner, BioProBench, Matterix).",
            "model": "Stateful 96-well + 12-reservoir + 20-300 uL pipette bookkeeping twin.",
            "training": "Episodic memory write-back (runs.jsonl flags repeat failures before rehearsal).",
            "history": "8219695 5-stage rehearsal loop -> 9f64121 Lean/wire audit -> 4013323 14-dataset 2026 twin converters.",
            "property": "Default-deny gate: zero commands reach the executor if any rule fails.",
        },
    },
    "lab-verify": {
        "hook": "Trust nothing a model emits until a mechanical checker says yes: SQL, Lean, and protocols.",
        "flow": ["Candidate SQL / spec", "Parse -> ReadOnly -> Schema -> Exec", "PASS or first failed layer"],
        "kpis": [["22 / 22", "gate agreement"], ["16", "SQL/Lean benchmarks"], ["0", "false passes"]],
        "short": {
            "object": "Filter LLM-generated SQL, Lean proofs, and protocols behind a strict default-deny gate.",
            "data": "30-row lab SQLite suite (22 queries) + 16 open SQL/Lean benchmarks (Spider 2.0-Lite, BIRD, EHRSQL-2024, PutnamBench, ProofNet).",
            "model": "4-layer gate: sqlglot parse -> read-only AST -> schema check -> execution match + lean-mcp/v1.",
            "training": "Deterministic verifier (serves as exact binary reward gate for RLVR).",
            "history": "3255ec7 4-layer SQL gate -> a5f9aec Lean-MCP audit -> 0c29ffc 16-benchmark 2026 adapters.",
            "property": "Proves syntax/schema alone miss 50% of wrong queries; execution checks catch all 7.",
        },
    },
    "lab-attrib": {
        "hook": "Separate robot glitches and precursor ghost peaks from proof-carrying negative truth after every run.",
        "flow": ["Post-run telemetry + XRD", "Lean 4 blame + NNLS", "SHA-256 certified ledger"],
        "kpis": [["25", "Lean 4 theorems"], ["0.0%", "false discovery rate"], ["9", "open spectra corpora"]],
        "short": {
            "object": "Prevent post-run hardware glitches and precursor peak overlap from poisoning scientific memory.",
            "data": "1,128-compound ESOL campaigns + 11-phase XRD/Raman panel + 9 open corpora (RRUFF, COD, MP-20, A-Lab GPSS, MassSpecGym, NMR).",
            "model": "4-way Lean 4 blame calculus + NNLS precursor deconvolver + EVOI orthogonal assay router.",
            "training": "Deterministic formal gate exporting verified positive/negative pairs for BO & RLVR.",
            "history": "6b7f467 15th Core Repo & monograph -> 0118a9c wire audit -> b8df8ef 9-dataset spectra registry.",
            "property": "0.0% FDR and 0 poisoned ledger entries while unlocking 31.0 multi-ring hits.",
        },
    },
    "labbench-posttrain": {
        "hook": "Post-training stack turning raw models into verified Scientist and Operator policies.",
        "flow": ["49k records + verifiers", "SFT -> MPO/TROPD -> GDPO/DAPO", "Checked policy adapters"],
        "kpis": [["49,139", "leak-free records"], ["9", "2026 science corpora"], ["0", "cross-split groups"]],
        "short": {
            "object": "Train and score Scientist & Operator models against code-checked lab & physics rewards.",
            "data": "49,139 Lab v0 records, CALiSol-23, BioProBench, LAB-Bench + 9-corpus 2024-2026 registry (MassSpecGym, SMolInstruct, ORD, BixBench).",
            "model": "labrl SDK: TorchLocalEngine (CPU/1xGPU) + NeMoRLEngine (8xA100 recipes).",
            "training": "SFT -> DPO/MPO/TROPD -> PPO/GRPO/GDPO+DAPO (CPU smoke run; full GPU PENDING).",
            "history": "101933a BioProBench -> 94f0cf5 rewards -> 2e015d6 Lean/wire audit -> fbdd731 2026 open science registry.",
            "property": "SplitGuard blocks group leakage & LAB-Bench/BixBench canaries; rewards gate bonuses on truth.",
        },
    },
    "twinstep": {
        "hook": "Deterministic error twins for protocol steps—teaching models to spot mistakes and order DAGs.",
        "flow": ["Clean JSON/YAML steps", "6 seeded error injectors", "Error-twin + DAG JSONL"],
        "kpis": [["6", "error injectors"], ["100%", "DAG constraint sat"], ["0", "runtime deps"]],
        "short": {
            "object": "Generate labeled protocol corruptions and step-ordering pairs from valid workflows.",
            "data": "3 seed protocols (serial dilution, wash-and-read, mix-incubate-read) -> N JSONL pairs.",
            "model": "6 typed injectors + transitive-reduced well-flow DAG + rule-based baseline.",
            "training": "Data generator & reference-blind baseline (66.7%-72.2% detection; feeds DPO/RLVR).",
            "history": "8a17ea1 v0.1 release -> 996a282 multi-fault & DPO export -> aa755c7 TwinStepLean & wire twins.",
            "property": "Stdlib-only runtime; scores ordering on minimal causal constraints, not rigid index.",
        },
    },
    "labfill": {
        "hook": "Fill the plate, fill the GPU—batch thousands of protocol checks and pack short sequences.",
        "flow": ["Variable-length steps", "Tensorized rules + BF16 packing", "5.42x real tokens/s"],
        "kpis": [["5.42x", "packed BF16 tok/s"], ["92.1%", "useful tokens"], ["225.8k", "proto/s checked"]],
        "short": {
            "object": "Batch protocol checking, twin repair, DAG beam search, plate dry-runs, and GPU packing.",
            "data": "Synthetic 24-step protocols, 96-well plates, and lognormal 8..512 token streams.",
            "model": "Vectorized PyTorch rule tensors + 4-layer d=256 Transformer packing benchmark.",
            "training": "9-way throughput ablation on Xeon 1T (30.6% -> 92.1% useful tokens; GPU pending).",
            "history": "ae91eb3 5 recipes -> f969496 FlexAttention & LabLean bridge -> e122b53 cu_seqlens, BFD & wire packing.",
            "property": "Fast PyTorch pre-filter aligned with YLM LabLean; cuts padding waste by 3x.",
        },
    },
    "lab-ears": {
        "hook": "Listen to protocol text and bench machines—pull clean parameters and flag strange sounds.",
        "flow": ["Protocol text · 16 kHz WAV", "Regex parser · Log-mel AE", "Checked slots · Audio alert"],
        "kpis": [["0.75-0.91", "WLP slot F1"], ["< 20 ms", "per 10 s clip"], ["300-3400 Hz", "speech dropped"]],
        "short": {
            "object": "Extract Amount/Temp/Time/Speed from text and detect abnormal instrument sounds.",
            "data": "WLP (125 test protocols) + DCASE 2023-2026, IMAD-DS 2024, MIMII, ChemBench, BioProBench & ProtoAct (14 corpora on main).",
            "model": "Regex span extractor + 64-bin log-mel Gaussian, kNN & Autoencoder on main.",
            "training": "Rule-based text parser; normal-only unsupervised acoustic detectors (~19 s CPU).",
            "history": "ba743be WLP baseline -> d3ba222 acoustic-anomaly & wire merge -> 079b9bb 12-dataset 2026 registry.",
            "property": "Privacy-first audio: drops 300-3400 Hz speech band and never stores raw WAVs.",
        },
    },
    "stepbot": {
        "hook": "Compile tiny YAML/JSON step files into deterministic Opentrons Python protocols and simulate.",
        "flow": ["YAML / JSON steps", "Volume-checked compiler", "Opentrons API 2.16 .py"],
        "kpis": [["2.16", "target apiLevel"], ["40", "passing unit tests"], ["86-131", "sim commands"]],
        "short": {
            "object": "Lower declarative transfer/mix/dilution YAML into readable Opentrons v2 Python.",
            "data": "3 bundled workflows (dilution_series, plate_fill, reservoir_mix) + OT-2 catalog.",
            "model": "Static deck/slot/tip/volume validator + deterministic AST codegen + dual simulator.",
            "training": "Deterministic compiler (zero ML; pairs with LLM planners as execution target).",
            "history": "4534ff1 initial compiler -> 5012e29 lineage & manifest -> 11dd693 Flex 2.20, StepbotLean & wire telemetry.",
            "property": "Works with real opentrons.simulate or built-in zero-dependency MockProtocolContext.",
        },
    },
    "lab-hands": {
        "hook": "Collision-free bench motion plus last-centimeter touch where clear glass fools cameras.",
        "flow": ["Target well (A1..H12)", "2-link/SE3 IK + RRT + shortcut", "Obstacle-free joint path"],
        "kpis": [["100 / 100", "RRT success"], ["70.6 ms", "mean plan CPU"], ["12", "open robot corpora"]],
        "short": {
            "object": "Plan safe pipette-to-well arm trajectories and audit visuo-tactile manipulation.",
            "data": "SBS 96-well geometry + 12 open 2024-2026 corpora (FineBio, DROID, AutoBio, LayeredDepth, ClearPose, TactX, FeelSight).",
            "model": "Analytic 2-link & 6-DoF ArmSE3 IK + AABB/slosh safety auditors + goal-biased RRT.",
            "training": "Sampling-based geometric planner today; ACT / Diffusion Policy roadmap next.",
            "history": "eb4d967 96-well RRT demo -> 2ac55e2 ArmSE3/wire audit -> 53d7ac4 12-dataset 2026 registry.",
            "property": "Solves 100/100 trials where straight joint moves collide on 10/10 target wells.",
        },
    },
    "lab-feet": {
        "hook": "Distill big teachers into tiny int8 and 4-bit students that run right next to the bench.",
        "flow": ["Teacher MLP (85k)", "T=4 distill + int8/4-bit pack", "Student (2.4k, 1.36 KB)"],
        "kpis": [["35x", "fewer params"], ["3.86 us", "batch-1 CPU"], ["7", "edge sensor corpora"]],
        "short": {
            "object": "Compress lab models via distillation and low-bit quantization for cheap edge boards.",
            "data": "8x8 digits probe + 7 open edge corpora (UCI 36-mo Gas Drift, CWRU/Hydraulic vibration, SERS Raman 2026, Ethanol NIR).",
            "model": "Teacher MLP (256,256) -> Student MLP (32) + symmetric int8 & SAFE_HOLD drift int4.",
            "training": "Hard-label CE (0.974 acc) vs KL+CE distillation + temporal-drift abstention.",
            "history": "a7b1532 distill/quantize probe -> 8b0338a Lean/wire audit -> 98a995b 7-dataset 2026 registry.",
            "property": "250x smaller footprint (340 KB -> 1.36 KB) with SAFE_HOLD abstention under sensor drift.",
        },
    },
}
