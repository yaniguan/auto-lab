"""Hand-curated, ultra-concise scannable specs for all 14 Auto-Lab repositories.

Each field is strictly 1 short line (~8-16 words) so cards scan in 5 seconds.
"""

from __future__ import annotations

from typing import Any

CONCISE_SPECS: dict[str, dict[str, Any]] = {
    "lab-ask-why": {
        "hook": "Does not pick a winner—surfaces the evidence on each side and names the test that settles it.",
        "flow": ["Claim + abstracts", "BM25 rationale ranker", "Opposing reasons + 'why' test"],
        "kpis": [["0.789", "SciFact recall@3"], ["188", "claims"], ["0", "LLM calls in baseline"]],
        "short": {
            "object": "Surface supporting/contradicting sentences and ask what experiment changes minds.",
            "data": "SciFact dev (188 claims, 209 claim-abstract pairs, CC BY-NC 2.0).",
            "model": "Pure-NumPy BM25 sentence ranker + 3 structured Socratic question templates.",
            "training": "Zero-training lexical baseline (0.789 recall@3 vs 0.528 random).",
            "history": "6236123 initial SciFact probe -> bbef3b6 L6 brain spec.",
            "property": "Treats SUPPORT (0.80) and CONTRADICT (0.78) symmetrically; never crowns a winner.",
        },
    },
    "lab-decide": {
        "hook": "Answers only inside its calibrated zone, says 'I don't know' outside, and grows with new data.",
        "flow": ["6 RDKit descriptors", "GBDT + kNN trust gate", "90% interval or ABSTAIN"],
        "kpis": [["92.2%", "in-trust coverage"], ["0.656", "in-trust MAE"], ["20.4%", "abstained"]],
        "short": {
            "object": "Gate experiment proposals by conformal uncertainty and distance to training data.",
            "data": "Delaney ESOL solubility (1,128 molecules: 676 train / 226 cal / 226 test).",
            "model": "Gradient boosting + split conformal (90%) + 5-NN 80th-pct trust boundary.",
            "training": "Supervised GBDT fit + 3 active boundary-expansion rounds.",
            "history": "41dae77 ESOL conformal demo -> 6b03cfc L6 calibration profile.",
            "property": "Lower error inside trust zone (0.66 vs 0.89 MAE) with explicit abstention outside.",
        },
    },
    "buy-or-make": {
        "hook": "Buy it now or make it in N steps? Strict catalog lower bounds, never invented prices.",
        "flow": ["Candidate SMILES", "PubChem + 2-step SMARTS", "buyable | makeable | unknown"],
        "kpis": [["5 ms", "cached / mol"], ["14", "retro templates"], ["null", "when unlisted"]],
        "short": {
            "object": "Classify molecules as buyable, makeable in <= N steps, or unknown with cost bounds.",
            "data": "Live PubChem vendors + optional ZINC/eMolecules/ORD/USPTO (strict license table).",
            "model": "Vendor lookup + 14 RDKit SMARTS disconnections (or AiZynthFinder) + SA/SCScore.",
            "training": "Deterministic search + pretrained MIT SCScore weights (no training in repo).",
            "history": "76991c8 v0.1 release -> bbfa649 cost/currency review PR #2 -> ff8e530.",
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
            "history": "124a6d7 30-instance suite -> 58ec7f2 flow-tie note PR #2 -> 6b78480.",
            "property": "CP-SAT clears all 13 max_wait violations left by greedy scheduling.",
        },
    },
    "lab-automation-atlas": {
        "hook": "A checked, zero-hype map of lab robots, cloud foundries, protocol DSLs, and open datasets.",
        "flow": ["Ecosystem URLs", "Weekly HTTP link check", "4 curated reference tables"],
        "kpis": [["27", "checked entries"], ["4", "taxonomy tables"], ["0", "copied vendor data"]],
        "short": {
            "object": "Index liquid handlers, cloud labs, open automation software, and protocol corpora.",
            "data": "Curated pointer tables (Opentrons, PyLabRobot, SiLA 2, LabOP, XDL, WLP, BioProBench).",
            "model": "Human-curated ontology + automated URL health script (no ML model).",
            "training": "None (reference atlas; grounds tool & dataset selection across Auto-Lab).",
            "history": "f2e2e83 link-checked release (2026-11-18) -> 7c65b97 L5 ontology spec.",
            "property": "Pointer-only MIT index: copies zero external data and ranks zero vendors.",
        },
    },
    "lab-rehearsal": {
        "hook": "Recall past crashes, dry-run on a virtual 96-well deck, block bad runs, write outcomes back.",
        "flow": ["JSON step list", "Recall + 96-well twin", "PASS to robot or BLOCK + log"],
        "kpis": [["4 / 4", "fault classes caught"], ["43", "steps in dilution"], ["100%", "recall warning"]],
        "short": {
            "object": "Catch volume, empty-well, overfill, and tip-reuse errors before touching hardware.",
            "data": "5 bundled JSON protocols (1 valid serial dilution + 4 seeded fault cases) + runs.jsonl.",
            "model": "Stateful 96-well + 12-reservoir + 20-300 uL pipette bookkeeping twin.",
            "training": "Episodic memory write-back (runs.jsonl flags repeat failures before rehearsal).",
            "history": "8219695 5-stage rehearsal loop -> 5e47a8f L4 safety profile.",
            "property": "Default-deny gate: zero commands reach the executor if any rule fails.",
        },
    },
    "lab-verify": {
        "hook": "Trust nothing a model emits until a mechanical checker says yes: SQL, Lean, and protocols.",
        "flow": ["Candidate SQL / spec", "Parse -> ReadOnly -> Schema -> Exec", "PASS or first failed layer"],
        "kpis": [["22 / 22", "gate agreement"], ["0", "false passes"], ["7 / 14", "caught at Layer 4"]],
        "short": {
            "object": "Filter LLM-generated SQL, Lean proofs, and protocols behind a strict default-deny gate.",
            "data": "Synthetic SQLite lab DB (12 experiments, 14 samples, 4 instruments, 22 candidates).",
            "model": "4-layer gate: sqlglot parse -> read-only AST -> schema check -> execution match.",
            "training": "Deterministic verifier (serves as exact binary reward gate for RLVR).",
            "history": "3255ec7 4-layer SQL gate & curated resources -> 775c3e9 L4 spec.",
            "property": "Proves syntax/schema alone miss 50% of wrong queries; execution checks catch all 7.",
        },
    },
    "labbench-posttrain": {
        "hook": "Post-training stack turning raw models into verified Scientist and Operator policies.",
        "flow": ["49k records + verifiers", "SFT -> MPO/TROPD -> GDPO/DAPO", "Checked policy adapters"],
        "kpis": [["49,139", "leak-free records"], ["8", "anti-hack templates"], ["0", "cross-split groups"]],
        "short": {
            "object": "Train and score Scientist & Operator models against code-checked lab & physics rewards.",
            "data": "49,139 records (20 sources), BioProBench (4 tasks), CALiSol-23, eval-only LAB-Bench.",
            "model": "labrl SDK: TorchLocalEngine (CPU/1xGPU) + NeMoRLEngine (8xA100 recipes).",
            "training": "SFT -> DPO/MPO/TROPD -> PPO/GRPO/GDPO+DAPO (CPU smoke run; full GPU PENDING).",
            "history": "101933a BioProBench -> Milestones 1-3 -> 6cb46a7 labrl -> 94f0cf5 rewards -> a879d9d.",
            "property": "SplitGuard blocks group leakage & LAB-Bench canary; rewards gate bonuses on truth.",
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
            "history": "8a17ea1 v0.1 release -> d598c32 unique-twin & wash fixes PR #2 -> b9b83fd.",
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
            "history": "ae91eb3 5 recipes -> PR #2 CPU tables (d1a7510) & PR #4 fixes (55eb158) -> 68d329e.",
            "property": "Fast PyTorch pre-filter aligned with YLM LabLean; cuts padding waste by 3x.",
        },
    },
    "lab-ears": {
        "hook": "Listen to protocol text and bench machines—pull clean parameters and flag strange sounds.",
        "flow": ["Protocol text · 16 kHz WAV", "Regex parser · Log-mel AE", "Checked slots · Audio alert"],
        "kpis": [["0.75–0.91", "WLP slot F1"], ["< 20 ms", "per 10 s clip"], ["300–3400 Hz", "speech dropped"]],
        "short": {
            "object": "Extract Amount/Temp/Time/Speed from text and detect abnormal instrument sounds.",
            "data": "Wet Lab Protocols (125 test protocols, MIT) + DCASE 2023 fan/valve/bearing (PR #2).",
            "model": "Regex span extractor (main) + 64-bin log-mel Gaussian, kNN & Autoencoder (PR #2).",
            "training": "Rule-based on main; normal-only unsupervised AE fit (~19 s CPU on PR #2).",
            "history": "ba743be WLP baseline -> 5476541 DCASE acoustic anomaly PR #2 -> 082f2e1.",
            "property": "Privacy-first audio: drops 300-3400 Hz speech band and never stores raw WAVs.",
        },
    },
    "stepbot": {
        "hook": "Compile tiny YAML/JSON step files into deterministic Opentrons Python protocols and simulate.",
        "flow": ["YAML / JSON steps", "Volume-checked compiler", "Opentrons API 2.16 .py"],
        "kpis": [["2.16", "target apiLevel"], ["40", "passing unit tests"], ["86–131", "sim commands"]],
        "short": {
            "object": "Lower declarative transfer/mix/dilution YAML into readable Opentrons v2 Python.",
            "data": "3 bundled workflows (dilution_series, plate_fill, reservoir_mix) + OT-2 catalog.",
            "model": "Static deck/slot/tip/volume validator + deterministic AST codegen + dual simulator.",
            "training": "Deterministic compiler (zero ML; pairs with LLM planners as execution target).",
            "history": "4534ff1 initial compiler -> ef6865f liquid-volume & apiLevel PR #2 -> 9b18549.",
            "property": "Works with real opentrons.simulate or built-in zero-dependency MockProtocolContext.",
        },
    },
    "lab-hands": {
        "hook": "Collision-free bench motion plus last-centimeter touch where clear glass fools cameras.",
        "flow": ["Target well (A1..H12)", "2-link IK + RRT + shortcut", "Obstacle-free joint path"],
        "kpis": [["100 / 100", "RRT success"], ["70.6 ms", "mean plan CPU"], ["2.08 rad", "shortcut path"]],
        "short": {
            "object": "Plan safe pipette-to-well arm trajectories and curate visuo-tactile manipulation.",
            "data": "SBS 96-well geometry (9 mm pitch) + curated Open-X, AutoBio, TransCG, DIGIT index.",
            "model": "Analytic 2-link IK + AABB link-collision checker + goal-biased RRT + shortcutting.",
            "training": "Sampling-based geometric planner today; ACT / Diffusion Policy roadmap next.",
            "history": "eb4d967 96-well RRT demo & tactile catalog -> 8213dab L1 motor spec.",
            "property": "Solves 100/100 trials where straight joint moves collide on 10/10 target wells.",
        },
    },
    "lab-feet": {
        "hook": "Distill big teachers into tiny int8 and 4-bit students that run right next to the bench.",
        "flow": ["Teacher MLP (85k)", "T=4 distill + int8/4-bit pack", "Student (2.4k, 1.36 KB)"],
        "kpis": [["35x", "fewer params"], ["3.86 us", "batch-1 CPU"], ["1.36 KB", "4-bit weights"]],
        "short": {
            "object": "Compress lab models via distillation and low-bit quantization for cheap edge boards.",
            "data": "Bundled 8x8 digits probe (1,257 train / 540 test) + edge runtime reference index.",
            "model": "Teacher MLP (256,256) -> Student MLP (32) + symmetric per-tensor int8 & int4.",
            "training": "Hard-label CE (0.974 acc) vs T=4 logit MSE distillation (0.969 acc; int8 0.0% drop).",
            "history": "a7b1532 distill/quantize CPU probe -> 6a600de L0 edge runtime spec.",
            "property": "250x smaller footprint (340 KB -> 1.36 KB); honestly notes NumPy dequantizes before matmul.",
        },
    },
}
