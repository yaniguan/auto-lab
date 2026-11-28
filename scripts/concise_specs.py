"""Hand-curated, ultra-concise scannable specs for all 15 Auto-Lab repositories.

Each field is strictly 1 short line (~8-16 words) so cards scan in 5 seconds.
"""

from __future__ import annotations

from typing import Any

CONCISE_SPECS: dict[str, dict[str, Any]] = {
    "lab-ask-why": {
        "hook": "Does not pick a winner—surfaces opposing evidence, conformal stance sets, and mind-changing tests.",
        "flow": ["Claim + 5,183 abstracts", "Hybrid RRF + 26-feat reranker", "Conformal stance + control wells"],
        "kpis": [["0.909", "SciFact hit@3 (reranker)"], ["8 / 14", "real / indexed corpora"], ["90.7%", "conformal stance cov"]],
        "short": {
            "object": "Surface supporting/contradicting rationales, conformal stance sets, and falsifiable control wells.",
            "data": "SciFact (0 train/dev overlap) + 8 real SHA-256 benchmarks (ConflictBank, FaithEval, SciVer, LitQA2) & 14-corpus registry.",
            "model": "2-stage Hybrid RRF (BM25 + 96d LSA + entity/negation) + 26-feature CrossFeatureReranker & SplitConformalStanceClassifier.",
            "training": "SciFact train-only fit (607 fit / 202 cal): lifts dev hit@3 0.818 -> 0.909 (set recall@3 0.876) & ConflictBank 100%.",
            "history": "6236123 SciFact BM25 -> b8a9d51 14-dataset registry -> 6f4887a hybrid reranker, conformal verifier & Lean 4 CI.",
            "property": "90.7% 3-way conformal stance coverage, 100% ConflictBank detection, and fail-closed CERTIFIED_NEGATIVE wire ingest.",
        },
    },
    "lab-decide": {
        "hook": "Answers inside its calibrated chemical manifold, abstains outside, and expands safely across BO rounds.",
        "flow": ["RDKit / HTE encodings", "GBDT/LGBM + CQR-r + Mahalanobis", "90% interval or L6_ABSTAIN"],
        "kpis": [["92.4%", "20-seed ESOL cov_in"], ["11 / 11", "informative real gates"], ["0.000", "campaign OOD picks"]],
        "short": {
            "object": "Gate experiment proposals and sequential BO campaigns by Mondrian conformal intervals and kNN distance.",
            "data": "SHA-pinned ESOL (561/224/169/169) + 11 real-CSV corpora (BigSolDB v2.2, CALiSol-23, FreeSolv, Doyle/Perera/Shields HTE).",
            "model": "Huber GBDT/LightGBM + Mondrian CQR-r + ensemble-Mahalanobis kNN + balanced group-packing splits (<=0.67 pp err).",
            "training": "11/11 real datasets gate_informative=True (5/5 seeds MAE_in < MAE_out) + 10-seed x 6-round BO campaigns.",
            "history": "41dae77 ESOL demo -> e37de97 11-dataset registry -> f72af29 balanced splits, HTE CQR, BO campaigns & ESOL wire.",
            "property": "0.000 OOD picks in 6-round BO (0.10 Doyle regret) and residual-gated ESOL ConformalTrustModel on autolab_wire.",
        },
    },
    "buy-or-make": {
        "hook": "Buy from catalog or synthesize via Retro*? Strict listed-price lower bounds, never invented costs.",
        "flow": ["Candidate SMILES", "PubChem + Retro* 44-SMARTS", "buyable | makeable | unknown"],
        "kpis": [["69.2%", "Retro* 5-step solve"], ["43.0%", "USPTO-50K top-10"], ["19", "SPDX-gated corpora"]],
        "short": {
            "object": "Triage buyable vs multi-step makeable molecules with conservative listed-catalog USD/g lower bounds.",
            "data": "19 SPDX-gated sources incl. PaRoutes n1/n5, SynPlanner, Syntheseus USPTO-50K (0 test leak), ChEMBL 37 & COCONUT 2.0.",
            "model": "Vendor lookup + Retro* best-first AND-OR search (44 atom-balanced SMARTS + USPTO train/val) + SA/SCScore.",
            "training": "Deterministic search + frozen MIT SCScore weights: lifts 240-target multi-step solve 2.1% -> 69.2% (10/10 convergent).",
            "history": "76991c8 v0.1 release -> 3be1f4a 19-source corpora -> ec33997 Retro* planner, PaRoutes/USPTO-50K bench & Lean 4 CI.",
            "property": "Missing prices stay null, stoichiometry is Lean-checked, and labshift/lab-attrib handoffs carry MOQ & precursor bases.",
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
        "flow": ["84 typed entries", "DNS-pinned SSRF + Lean SPDX", "Synced JSON & MD atlas"],
        "kpis": [["84", "typed entries (7 cats)"], ["335", "Lean #eval parity"], ["0", "copied vendor data"]],
        "short": {
            "object": "Ground platform capabilities, protocol IRs, compound SPDX expressions, and dataset governance.",
            "data": "84-entry atlas.json across 7 categories (robots, cloud labs, IRs, solvers PyJobShop/LeRobot, procurement & datasets).",
            "model": "Typed hardware/IR capability resolver + compound SPDX evaluator + DNS-pinned SSRF link auditor.",
            "training": "Zero parametric training; verified by Lean 4.36.0 #print axioms, 335-case parity, and weekly link CI.",
            "history": "f2e2e83 pointer map -> 3b7d259 70-entry 2026 atlas -> b6455d9 84 frontier entries, wire hardening & Lean 4 CI.",
            "property": "Default-deny SPDX AND/OR/WITH + parent-lineage taint and canonical HTTPS SSRF guards.",
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
        "flow": ["Telemetry + XRD/Raman/MS", "30-thm Lean + Pseudo-Voigt NNLS", "SHA-256 certified ledger"],
        "kpis": [["30", "Lean 4 theorems"], ["51", "pinned real spectra"], ["0.0%", "A-Lab & Raman FDR"]],
        "short": {
            "object": "Block corrupted runs and precursor ghost peaks from poisoning scientific memory or Chem-RRT calibration.",
            "data": "51 SHA-256-pinned real spectra (A-Lab GPSS .xrdml, RRUFF/DARA XRD, ROD Raman, MassSpecGym) + ESOL + 9 corpora.",
            "model": "30-theorem Lean 4 blame calculus + shift-tolerant Pseudo-Voigt L1-NNLS + MS/MS spectral entropy & EVOI router.",
            "training": "Deterministic formal gate failing closed (L4_ATTRIB_SCHEMA_REJECT) on malformed telemetry.",
            "history": "6b7f467 15th Repo & monograph -> b8df8ef 9-dataset registry -> 9a4b119 shift-Voigt L1-NNLS, 51 real spectra & 30 thms.",
            "property": "0.0% FDR (75% recall) on real A-Lab GPSS XRD, 82.4% MassSpecGym Top-1, and #print axioms audited in CI.",
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
