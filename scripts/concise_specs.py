"""Hand-curated, ultra-concise scannable specs for all 15 Auto-Lab repositories.

Each field is strictly 1 short line (~8-16 words) so cards scan in 5 seconds.
"""

from __future__ import annotations

from typing import Any

CONCISE_SPECS: dict[str, dict[str, Any]] = {
    "lab-ask-why": {
        "hook": "Does not pick a winner—surfaces opposing evidence, conformal stance sets, and mind-changing tests.",
        "flow": ["Claim + 5,183 abstracts", "Sparse Hybrid / BGE+DeBERTa NLI", "Conformal stance + control wells"],
        "kpis": [["0.909", "SciFact hit@3 (hybrid)"], ["0.000", "neg-ctrl conflict FPR"], ["0.900", "BGE+NLI doc_recall@5"]],
        "short": {
            "object": "Surface supporting/contradicting rationales, conformal stance sets, and falsifiable control wells.",
            "data": "SciFact (0 train/dev overlap, 181 docs excluded) + 8 real SHA-256 benchmarks & 14-corpus registry.",
            "model": "<1.5 GB NumPy FrontierHybridVerifier + bilateral conflict scorer + CPU NeuralBiEncoderNliVerifier (BGE + DeBERTa-v3).",
            "training": "SciFact train-only fit (607/202): 0.909 hit@3 (0.340 Official F1), 0.900 neural doc_recall@5 & 0.000 neg-ctrl FPR.",
            "history": "6236123 SciFact BM25 -> 6f4887a hybrid reranker -> 7f945fa checkAskWhy wire gate, neg-ctrl conflict & BGE+DeBERTa NLI.",
            "property": "0.000 single-passage negative-control FPR (0.975 ConflictBank AUROC) and zero silent wire fallback.",
        },
    },
    "lab-decide": {
        "hook": "Answers inside its calibrated chemical manifold, abstains outside, and expands safely across BO rounds.",
        "flow": ["1,416d RDKit 2D+Morgan / HTE", "FrontierEnsemble + CQR-r", "90% interval or L6_ABSTAIN"],
        "kpis": [["0.422", "ESOL MAE (-38.5% vs Delaney)"], ["11 / 11", "informative real gates"], ["0.000", "campaign OOD picks"]],
        "short": {
            "object": "Gate experiment proposals and sequential BO campaigns by Mondrian conformal intervals and kNN distance.",
            "data": "SHA-pinned ESOL (561/224/169/169) + 11 real-CSV corpora (AqSolDB, BigSolDB v2.2, FreeSolv, Doyle/Perera/Shields HTE).",
            "model": "1,416d rdkit_2d_morgan + FrontierEnsembleRegressor (Ridge + KRR + LGBM) + Tanimoto-Mahalanobis CQR-r.",
            "training": "20-seed ESOL MAE 0.422 (MAE_in 0.378, R^2 0.918, -38.5% vs Delaney 0.686), 11/11 informative gates & 10-seed BO.",
            "history": "41dae77 ESOL demo -> f72af29 balanced splits & BO -> 93db11e rdkit_2d_morgan FrontierEnsembleRegressor & Delaney bench.",
            "property": "Beats Delaney (2004) on both random (-38.5%) & scaffold splits with 0.000 OOD BO picks (0.10 Doyle regret).",
        },
    },
    "buy-or-make": {
        "hook": "Buy from catalog or synthesize via Retro*? Strict listed-price lower bounds, never invented costs.",
        "flow": ["Candidate SMILES", "PubChem + 100-SMARTS Retro*", "buyable | makeable | unknown"],
        "kpis": [["30.0%", "0-leak Retro* (43.8% n5)"], ["49.4%", "USPTO-50K top-10"], ["175", "Lean gate parity cases"]],
        "short": {
            "object": "Triage in-stock buyable vs multi-step makeable molecules with conservative listed-catalog USD/g lower bounds.",
            "data": "19/19 SHA-pinned SPDX sources incl. PaRoutes n1/n5, SynPlanner, Syntheseus USPTO-50K (0 target/test leak) & ChEMBL 37.",
            "model": "In-stock vendor lookup + zero-target-leakage Retro* AND-OR search (100 atom-balanced SMARTS + held-out lookup).",
            "training": "Zero-leakage Retro* lifts 240-target solve 2.1% -> 30.0% (43.8% PaRoutes n5) & USPTO-50K top-10 16.6% -> 49.4%.",
            "history": "76991c8 v0.1 -> ec33997 Retro* -> 0d69702 0-leak PaRoutes/USPTO bench, in_stock/MOQ honesty & 175-case Lean parity.",
            "property": "Out-of-stock offers never count as buyable, unpriced never pass budget, and USD/g never conflates with MOQ cash.",
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
        "hook": "A checked, zero-hype map of lab robots, cloud foundries, protocol DSLs, solvers, and open datasets.",
        "flow": ["84 typed entries", "Canonical URL + Lean SPDX", "Synced JSON & MD atlas"],
        "kpis": [["84", "typed entries (7 cats)"], ["260", "compiled Lean #guards"], ["160+", "eval_only URL variants"]],
        "short": {
            "object": "Ground platform capabilities, protocol IRs, compound SPDX expressions, and dataset governance.",
            "data": "84-entry atlas.json across 7 categories (robots, cloud labs, IRs, solvers PyJobShop/LeRobot, procurement & datasets).",
            "model": "Canonical URL normalizer (hf.co/.git/arXiv) + SPDX-to-purpose validator + DNS-pinned SSRF link auditor.",
            "training": "Zero parametric training; verified by Lean 4.36.0 260 compiled #guards, 335-case #eval parity & weekly link CI.",
            "history": "f2e2e83 pointer map -> b6455d9 84 entries -> 34cf0c6 canonical URL block, default-deny SPDX & 260 Lean #guards.",
            "property": "Blocks 160+ eval_only URL variants, default-denies missing licenses, and validates SPDX-to-purpose alignment.",
        },
    },
    "lab-rehearsal": {
        "hook": "Recall past crashes, dry-run on a virtual 96-well deck, verify compiled round-trip parity, write back.",
        "flow": ["Steps / Opentrons JSON", "Recall + 96w twin + round-trip", "PASS to stepbot or BLOCK"],
        "kpis": [["5 / 5", "fault fixtures blocked"], ["14", "protocol datasets"], ["100%", "round-trip parity"]],
        "short": {
            "object": "Catch volume, empty-well, overfill, tip-reuse, evaporation, and compile-drift bugs pre-execution.",
            "data": "6 bundled JSON protocols + 12-run runs.jsonl + 14-dataset 2024-2026 simulator catalog (Opentrons v6-v8, FineBio).",
            "model": "Stateful 1-/8-ch 96-well + evaporation twin with from_stepbot round-trip verifier & Lean 4 lab-rehearsal-check.",
            "training": "Content- and skeleton-hashed episodic write-back + lab-attrib transient retry reconciliation.",
            "history": "8219695 5-stage loop -> 4013323 14-dataset converters -> a889b23 non-capping wire, round-trip gate & Lean 4 CI.",
            "property": "Never silently caps over-capacity volumes and re-rehearses compiled stepbot IR before minting.",
        },
    },
    "lab-verify": {
        "hook": "Trust nothing a model emits until a mechanical checker says yes: SQL, Lean 4 axioms, and Lean-MCP.",
        "flow": ["SQL / Lean / MCP token", "4-layer SQL + #print axioms", "PASS or fail-closed BLOCK"],
        "kpis": [["22 / 22", "lab SQL agreement"], ["931 + 232", "real EHRSQL-2024"], ["0", "custom axioms"]],
        "short": {
            "object": "Enforce default-deny verification over lab/clinical SQL, compiled Lean 4 proofs, and lean-mcp/v1 dispatch.",
            "data": "30-row lab DB (22 queries + 3 mutant DBs) + real MIMIC-IV v2.2 EHRSQL-2024 (317,875 rows) + 16 open benchmarks.",
            "model": "4-layer SQL gate (Hopcroft-Karp float multiset + tie-aware ORDER BY), live Lean #print axioms & Ed25519/HMAC MCP.",
            "training": "Symbolic/execution verifier rejecting insecure dev keys and requiring role-separated supervisor co-signatures.",
            "history": "3255ec7 SQL gate -> 0c29ffc 16-benchmark adapters -> a286050 Lean axiom gate, real EHRSQL-2024 & fail-closed MCP.",
            "property": "931/931 answerable + 232/232 unanswerable on real EHRSQL-2024 and zero false passes across all 4 SQL layers.",
        },
    },
    "lab-attrib": {
        "hook": "Separate robot glitches and shifted precursor peaks from proof-carrying negative truth after every run.",
        "flow": ["Explicit QC + XRD/Raman/MS", "31-thm Lean + Pseudo-Voigt NNLS", "SHA-256 certified ledger"],
        "kpis": [["31", "Lean 4 theorems"], ["72", "pinned real spectra"], ["15", "A-Lab CERTIFIED_NEG"]],
        "short": {
            "object": "Block corrupted, telemetry-free, and precursor-overlapped runs from poisoning scientific memory or calibration.",
            "data": "72 SHA-256-pinned real spectra (352-run A-Lab GPSS, RRUFF/DARA XRD, 14 indep. Raman, MassSpecGym) + ESOL + 9 corpora.",
            "model": "31-theorem Lean 4 blame calculus + fit-calibrated Rwp + Pseudo-Voigt L1-NNLS + Q1/residual MS/MS chimera gate.",
            "training": "Default-deny wire gate (MISSING_EXPERIMENTAL_EVIDENCE) + equal-budget & imperfect-sensor closed-loop sweeps.",
            "history": "6b7f467 15th Repo -> 9a4b119 Voigt-NNLS -> 7404d0d default-deny wire, 72 real spectra, 15 A-Lab negs & 31 thms.",
            "property": "0.0% FDR (75% recall, 15 CERTIFIED_NEGATIVEs) on real A-Lab GPSS and 0 poisoned entries at 180 equal budget.",
        },
    },
    "labbench-posttrain": {
        "hook": "Post-training stack turning raw models into verified Scientist and Operator policies without leakage.",
        "flow": ["49k records + SplitGuard", "SFT -> MPO/TROPD -> GDPO/DAPO", "Sequence-exact KL + RLVR"],
        "kpis": [["49,139", "0-leakage records"], ["9", "2026 science corpora"], ["15 / 15", "CPU smoke jobs"]],
        "short": {
            "object": "Train and score Scientist & Operator policies against code-checked lab, electrolyte & protocol rewards.",
            "data": "49,139 Lab v0 records (0 cid| fallbacks, 0 group leak), CALiSol-23, BioProBench, LAB-Bench & 9-corpus 2026 registry.",
            "model": "labrl v0.2 SDK: TorchLocalEngine + pinned yaniguan/RL NeMoRLEngine + 8 VerifiedRewardTemplates + LabPostTrainLean.",
            "training": "SFT -> DPO/MPO/TROPD -> PPO/GDPO+DAPO with per-token & sequence_exact Reverse-KL (full A100/H100 PENDING).",
            "history": "94f0cf5 rewards -> fbdd731 2026 registry -> 8dd44de PubChem CIDs, RL fork contract, sequence KL, wire & Lean CI.",
            "property": "Fail-closed L3_WIRE_SCHEMA_REJECT separates CERTIFIED_POSITIVE SFT from CERTIFIED_NEGATIVE DPO/MPO disproofs.",
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
        "hook": "Extract wet-lab quantities via zero-leakage BIOES tagging and monitor machine sound without recording speech.",
        "flow": ["Protocol text · 16 kHz WAV", "PA-II BIOES · Streaming mel", "0.876 F1 · Privacy-gated alert"],
        "kpis": [["0.876", "WLP BIOES micro-F1"], ["2 s / 10 s", "matched stream cal"], ["300-3400 Hz", "speech dropped"]],
        "short": {
            "object": "Extract Amount/Temp/Time/Speed spans cleanly and detect cavitation/bearing faults under speech privacy.",
            "data": "WLP train/dev/test (SHA-deduped) + DCASE 2023-2026, IMAD-DS, MIMII, ChemBench, BioProBench & ProtoAct (12 corpora).",
            "model": "Zero-leakage 17-state PA-II BIOES tagger + regex baseline + window-matched streaming Gaussian/kNN/AE & interlock.",
            "training": "WLP train-only PA-II fit (0.876 exact / 0.897 overlap test micro-F1; 0.875 unseen-SHA) + normal-only acoustic fit.",
            "history": "ba743be WLP regex -> 079b9bb 12-dataset registry -> eab305f BIOES tagger, streaming cal, harmonic speech & wire privacy.",
            "property": "Rejects harmonic speech false halts and fails closed (L2_SPEECH_PRIVACY_BLOCK) if privacy fields are missing.",
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
