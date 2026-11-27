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
        "flow": ["Jobs + wait windows", "Stdlib LNS or CP-SAT", "Conflict-free Gantt + gap%"],
        "kpis": [["20 / 20", "planted CP-SAT opt"], ["17 / 20", "stdlib LNS feas"], ["0", "window violations"]],
        "short": {
            "object": "Assign chained lab operations to shared instrument and robot-arm pools under wait bounds.",
            "data": "30 v1 + 20 planted hard instances + stepbot fixtures + JSSP, PSPLIB j30/j60 & Opentrons/WLP campaigns.",
            "model": "Sweep-line checker, Jackson/Carlier energetic lower bounds, stdlib LNS, OR-Tools CP-SAT & PyJobShop.",
            "training": "Zero-dep combinatorial optimizer & RLVR verifier with valid lower-bound gap% for every solver.",
            "history": "124a6d7 30-instance suite -> ebc7f19 Lean/wire & arm transit -> fc5bba5 planted tier, LNS, LB & open suites.",
            "property": "CP-SAT solves 30/30 v1 (116.4 m) & 20/20 planted (vs 0/20 greedy, 7/20 repair, 17/20 stdlib LNS).",
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
        "flow": ["24 split protocols", "6 injectors + graph localizer", "81.3% held-out ED"],
        "kpis": [["81.3%", "held-out test ED"], ["87.3%", "ProcessBench bal."], ["4", "public corpora"]],
        "short": {
            "object": "Generate split-isolated protocol corruptions, step-ordering DAGs, and zero-leakage fault predictions.",
            "data": "24 MIT protocols (8 train / 4 val / 12 test, 0 overlap) + WLP, BioProBench, BioPlanner & Opentrons.",
            "model": "Per-well stage-barrier flow DAG + 6 fault injectors + 26-feature learned StepGraphFaultVerifier.",
            "training": "Stdlib zero-leakage localizer lifts 20-seed unseen test ED 57.7% -> 81.3% (step_index 44.2% -> 70.7%).",
            "history": "8a17ea1 v0.1 release -> aa755c7 TwinStepLean & wire -> a781fc0 24-proto splits, learned verifier & 4 corpora.",
            "property": "Multi-stage ELISA/TMB assays pass cleanly; 100% causal DAG ordering satisfaction with 0 runtime deps.",
        },
    },
    "labfill": {
        "hook": "Fill the plate, fill the GPU—batch thousands of protocol checks and pack short sequences.",
        "flow": ["Variable-length steps", "120-bit checker + OBFD pack", "308/310 LabLean match"],
        "kpis": [["92.4%", "packed useful tok"], ["310 / 310", "LabLean CI compiled"], ["5", "public corpora"]],
        "short": {
            "object": "Batch overflow-free protocol checking, K=26 twin repair, DAG beam search, and O(N log N) OBFD packing.",
            "data": "0.1 uL protocols up to 10,000 mL + 5 public corpora (Opentrons, WLP, BioPlanner, SMolInstruct, ORD).",
            "model": "120-bit limb-split PyTorch checker + Segment-Tree OBFD packer + 4-layer d=256 ProtocolTransformer.",
            "training": "5-seed CPU packing ablation (25.0% -> 92.4% useful tokens, 3.36x BF16; physical GPU PENDING_GPU).",
            "history": "ae91eb3 5 recipes -> e122b53 cu_seqlens & wire -> 38f23ee 120-bit checker, 310-proto LabLean CI & OBFD.",
            "property": "0 overflow vs Python over 12k 300 mL pairs and 0 unexplained verdict diffs vs live YLM LabLean.",
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
        "flow": ["YAML / JSON steps", "Stroke & lineage compiler", "100% Opentrons 8.8.2 parity"],
        "kpis": [["311 / 311", "sim diff parity"], ["36 / 36", "public assays OK"], ["278", "passing tests"]],
        "short": {
            "object": "Lower declarative OT-2 (2.16) & Flex (2.18-2.20) YAML into deterministic Opentrons Python.",
            "data": "30 labware & 16 1-/8-channel pipettes, 4 rheology profiles, 3 examples & 36-assay public benchmark.",
            "model": "Two-stage 8.8.2 stroke splitter, 8-ch column/contact lineage tracker, AST codegen & Lean-MCP runtime.",
            "training": "Symbolic compiler verified 100% against opentrons.simulate 8.8.2 (3,607 actions, 971 tips).",
            "history": "4534ff1 initial compiler -> 11dd693 Flex 2.20, StepbotLean & wire -> ffd1347 100% 8.8.2 parity & 8-ch.",
            "property": "Rejects NaN/Inf, tracks bottom/top tip contact, and matches opentrons.simulate 8.8.2 action-for-action.",
        },
    },
    "lab-hands": {
        "hook": "6/7-DoF cobot planning, ZVD/EI slosh control, and active tactile search where clear glass fools cameras.",
        "flow": ["6/7-DoF UR5e & Panda", "Informed RRT* + TOPP-RA + EI", "99.0% active tactile insert"],
        "kpis": [["99.0%", "active tactile (495/500)"], ["10.2x", "EI slosh ringdown cut"], ["12", "open robot corpora"]],
        "short": {
            "object": "Plan collision-free 6/7-DoF SE(3) trajectories, suppress well slosh, and insert via tactile spiral search.",
            "data": "UR5e/Panda/Flex kinematics, 96/384-well Bessel slosh, 0.70 mm SBS chamfer & 12 LeRobot/Opentrons corpora.",
            "model": "PoE/DH + DLS IK + swept 3D capsules + Informed RRT*/TOPP-RA + ZV/ZVD/EI shapers + Bayesian tactile filter.",
            "training": "Zero-dep NumPy robotics stack validated against AutoBio/DROID FK (<1 um) & opentrons.simulate 8.8.2.",
            "history": "eb4d967 2D RRT -> 53d7ac4 ArmSE3/wire & 12 corpora -> e296fb5 6/7-DoF TOPP-RA, EI slosh & 99% tactile.",
            "property": "Recovers 80% flat-rim camera landings from 1.2% open-loop / 19.0% local shear to 99.0% active tactile.",
        },
    },
    "lab-feet": {
        "hook": "Distill teachers into W8A8/W4A8 students, export ONNX/C99, and adapt to multi-year sensor drift.",
        "flow": ["Teacher / SpectralResNet1D", "KL+CE + WHT/GPTQ W4A8", "ONNX qlinear + TTN+CRC"],
        "kpis": [["93.5%", "MNIST-1D 4-bit acc"], ["10", "SHA-256 edge corpora"], [">=99%", "ONNX/C99 parity"]],
        "short": {
            "object": "Compress lab models into W8A8/W4A8 C99 & ONNX runtimes with fail-closed drift monitoring.",
            "data": "10-seed digits + 10 SHA-256-pinned open corpora (36-mo UCI Gas Drift, CWRU, SERS Raman, NIR, 3 FT-IR).",
            "model": "MLP & 39.1k SpectralResNet1D + WHT+GPTQ W4A8 + ONNX qlinear (int32) + TTN+CRC drift adaptation.",
            "training": "10-seed KL+CE vs matched CE control (0.9748 vs 0.9756) + Batch-1 -> Batches 2..10 drift benchmarks.",
            "history": "a7b1532 distill/quantize -> 98a995b LFT1/wire & 7 corpora -> e6e0600 ONNX qlinear, WHT+GPTQ & 10 corpora.",
            "property": "Fail-closed wire calibration/accuracy floor + TTN+CRC lifts drifted Batches 4..9 to 66.0%-88.1% acc.",
        },
    },
}
