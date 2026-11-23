<p>
  <a href="https://antigravity.google/"><img src="assets/google-antigravity-logo.svg" alt="Google Antigravity" height="40" align="left"></a>
  <sub>This project uses API credits from the Google Antigravity for Science program. Thank you, Google Antigravity!</sub>
</p>
<br clear="left">

<div align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/autolab_mark_dark.svg">
  <img src="assets/autolab_mark_light.svg" alt="Auto-Lab logo" width="96">
</picture>

# Auto-Lab

**A 7-layer embodied brain, default-deny safety nervous system, and verifiable RL post-training stack for autonomous wet laboratories.**

**Project Website & Interactive Lab:** [https://yaniguan.github.io/auto-lab/](https://yaniguan.github.io/auto-lab/) · [Lean 4 Trust Regime & Papers](https://yaniguan.github.io/auto-lab/trust/) · [Interactive Sandbox](https://yaniguan.github.io/auto-lab/studio/) · [15-Repo Cards](https://yaniguan.github.io/auto-lab/repos/)

[![Project Studio](https://img.shields.io/badge/project_page-live_7--layer_studio-b5d88e?style=flat&labelColor=101820)](https://yaniguan.github.io/auto-lab/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![tests](https://github.com/yaniguan/auto-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/yaniguan/auto-lab/actions/workflows/tests.yml)
[![Repositories](https://img.shields.io/badge/core_repositories-15-7c3aed.svg)](#the-15-core-repositories)

</div>

## Why a Layered Brain & Nervous System?

Wiring a free-form language model directly to a liquid handler or robotic arm fails in real laboratories: uncalibrated models hallucinate reagent volumes, omit wash steps, reuse contaminated pipette tips, violate inter-step incubation windows, and game naive scalar RL rewards.

**Auto-Lab** decomposes an autonomous robot co-scientist into **seven explicit cognitive, executive, inhibitory, sensory, motor, edge, and post-training layers (`L6` → `L0`)** across **15 modular repositories** (plus 4 connected companion repositories for 3D equivariant reasoning, generative MD, chemical vision, and unified data ingestion):

```mermaid
flowchart TB
    L6["L6 · Metacognitive & Epistemic Brain<br/>lab-ask-why · lab-decide (+ YLM)"]
    L5["L5 · Executive Planning, Make-vs-Buy & Fleet Scheduling<br/>buy-or-make · labshift · lab-automation-atlas"]
    L4["L4 · Twin Rehearsal, Default-Deny Gate & Post-Run Attribution<br/>lab-rehearsal · lab-verify · lab-attrib (+ WignerFlow)"]
    L2["L2 · Multimodal Sensory & Protocol Cortex<br/>lab-ears (+ ouroboros-ocsr · assayfold)"]
    L1["L1 · Lean-MCP Protocol Compiler & Tactile Manipulation<br/>stepbot · lab-hands"]
    L0["L0 · Edge Distillation & Quantized Runtime<br/>lab-feet"]
    L3["L3 · RLVR Post-Training, Error Twins & GPU Packing Flywheel<br/>labbench-posttrain (labrl) · twinstep · labfill"]

    L2 --> L6
    L6 --> L5
    L5 --> L4
    L4 -- "lean-mcp/v1 PASS only" --> L1
    L1 --> L0
    L0 == "post-run telemetry & spectra" ==> L4
    L4 == "SHA-256 certified +/- & twin pairs" ==> L3
    L4 -. "attributed Chem-RRT shells" .-> L6
    L3 == "aligned & distilled checkpoints" ==> L6
    L3 == "int8 / 4-bit students" ==> L0
```

## Quickstart

Clone the hub, install the zero-dependency `autolab` CLI, and pull or inspect all 15 sibling repositories:

```bash
git clone https://github.com/yaniguan/auto-lab.git && cd auto-lab
pip install -e ".[dev]"

# Clone or fetch all 15 Auto-Lab repositories into the parent workspace directory
python scripts/sync_all.py --action clone-or-fetch

# Inspect the 7-layer Brain -> Body hierarchy and per-repo dossiers
autolab layers
autolab list
autolab inspect lab-attrib
autolab inspect labbench-posttrain

# Run deterministic 7-layer closed-loop traces (GO vs L4 Block vs L6 Abstain vs lab-attrib Ghost-Peak Quarantine)
autolab loop --scenario serial_dilution
autolab loop --scenario broken_tip_reuse
autolab loop --scenario precursor_ghost_peak
autolab loop --scenario uncalibrated_molecule

# Run hub integrity & cross-repo lean-mcp/v1 wire tests
pytest
```

## The 15 Core Repositories

Every repository documents **Object**, **Data**, **Model**, **Training**, **History**, and **Unique Properties** in both its `README.md` and `docs/ARCHITECTURE_AND_HISTORY.md` (see [`docs/REPO_MATRIX.md`](docs/REPO_MATRIX.md) and [`docs/ISSUES_AUDIT_INDEX.md`](docs/ISSUES_AUDIT_INDEX.md)):

| Layer | Repository | Anatomical / System Role | Key Measured Baseline / Invariant | Dossier & Tracker |
|---|---|---|---|---|
| **L6 Brain** | [`lab-ask-why`](https://github.com/yaniguan/lab-ask-why) | Socratic co-scientist for opposing claims | `0.789` BM25 rationale `recall@3` on SciFact dev (`SUPPORT` & `CONTRADICT`) | [Profile](https://github.com/yaniguan/lab-ask-why/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-ask-why/issues) |
| **L6 Brain** | [`lab-decide`](https://github.com/yaniguan/lab-decide) | Calibrated decision API with abstention | `92.2%` in-region split-conformal coverage (`MAE 0.656` vs `0.892` outside) on ESOL | [Profile](https://github.com/yaniguan/lab-decide/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-decide/issues) |
| **L5 Exec** | [`buy-or-make`](https://github.com/yaniguan/buy-or-make) | Make-vs-buy molecular triage & cost bounds | Strict `listed_catalog` USD/g leaf lower bounds (`null` when unlisted; `0.005 s/mol` cached) | [Profile](https://github.com/yaniguan/buy-or-make/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/buy-or-make/issues) |
| **L5 Exec** | [`labshift`](https://github.com/yaniguan/labshift) | Multi-instrument time-window scheduler | OR-Tools `CP-SAT` `30/30` feasible (`116.7m` makespan) vs Greedy `24/30` (`13` window viol.) | [Profile](https://github.com/yaniguan/labshift/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/labshift/issues) |
| **L5 Exec** | [`lab-automation-atlas`](https://github.com/yaniguan/lab-automation-atlas) | Semantic map of platforms, DSLs & datasets | Link-checked catalog of liquid handlers, cloud labs, protocol standards & open corpora | [Profile](https://github.com/yaniguan/lab-automation-atlas/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-automation-atlas/issues) |
| **L4 Gate** | [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal) | Episodic recall + 96-well twin dry-run | `Recall → Rehearse → Verify → Run → Write-Back` (`runs.jsonl` blocks all 4 seeded fault classes) | [Profile](https://github.com/yaniguan/lab-rehearsal/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-rehearsal/issues) |
| **L4 Gate** | [`lab-verify`](https://github.com/yaniguan/lab-verify) | Default-deny Lean / SQL / `Lean-MCP` gate | 4-layer SQL gate (`22/22`, `0` false passes) + epoch-bound `lean-mcp/v1` runtime gate | [Profile](https://github.com/yaniguan/lab-verify/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-verify/issues) |
| **L4 Gate** | [`lab-attrib`](https://github.com/yaniguan/lab-attrib) | Post-run blame, NNLS XRD & negative ledger | 25 Lean 4 theorems (`0 sorry`), `0.0%` FDR, `+44.9%` ESOL multi-ring hits, SHA-256 ledger | [Profile](https://github.com/yaniguan/lab-attrib/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Paper](https://github.com/yaniguan/lab-attrib/blob/main/paper/main.pdf) |
| **L3 RLVR** | [`labbench-posttrain`](https://github.com/yaniguan/labbench-posttrain) | Scientist + Operator + `labrl` RLVR SDK | `49,139` records (`0` group leak), `SFT → DPO/MPO/TROPD → PPO/GRPO/GDPO+DAPO`, 8 anti-hack templates | [Profile](https://github.com/yaniguan/labbench-posttrain/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/labbench-posttrain/issues) |
| **L3 RLVR** | [`twinstep`](https://github.com/yaniguan/twinstep) | Seeded-error protocol twins & ordering DAGs | Deterministic 6-type error injection + topological dependency baseline (`100%` constraint sat.) | [Profile](https://github.com/yaniguan/twinstep/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/twinstep/issues) |
| **L3 RLVR** | [`labfill`](https://github.com/yaniguan/labfill) | Batched protocol checking & GPU packing | Sequence packing + `bf16` hits `92.1%` useful tokens (`5.42×` CPU tok/s; `225.8k` proto/s check) | [Profile](https://github.com/yaniguan/labfill/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/labfill/issues) |
| **L2 Ears** | [`lab-ears`](https://github.com/yaniguan/lab-ears) | Protocol span parsing & acoustic monitoring | `F1 0.75–0.91` on WLP slots + DCASE 2023 machine anomaly baseline (`300–3400 Hz` speech drop) | [Profile](https://github.com/yaniguan/lab-ears/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-ears/issues) |
| **L1 Motor** | [`stepbot`](https://github.com/yaniguan/stepbot) | YAML/JSON → Opentrons Python API v2 compiler | Deterministic `apiLevel 2.16` codegen + compile-time volume/tip checks + dual simulator | [Profile](https://github.com/yaniguan/stepbot/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/stepbot/issues) |
| **L1 Motor** | [`lab-hands`](https://github.com/yaniguan/lab-hands) | Bench manipulation, RRT & last-cm touch | `100/100` collision-free SBS 96-well RRT + path shortcutting (`70.6 ms` mean CPU) | [Profile](https://github.com/yaniguan/lab-hands/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-hands/issues) |
| **L0 Feet** | [`lab-feet`](https://github.com/yaniguan/lab-feet) | Edge distillation & `int8` / `4-bit` runtime | `35×` parameter reduction (`85k → 2.4k`), `int8` (`0.0%` acc loss) & `4-bit` (`3.86 µs` CPU) | [Profile](https://github.com/yaniguan/lab-feet/blob/main/docs/ARCHITECTURE_AND_HISTORY.md) · [Issues](https://github.com/yaniguan/lab-feet/issues) |

### Connected Companion Organs in `@yaniguan`

| Layer | Companion Repo | Role in the Co-Scientist Organism |
|---|---|---|
| **L6 Brain** | [`YLM`](https://github.com/yaniguan/YLM) ([Studio](https://yaniguan.github.io/YLM/)) | SE(3)-equivariant 3D molecule + language reasoner (`0.960` force cosine across 32 rotations) & home of LabLean |
| **L4 Gate** | [`WignerFlow`](https://github.com/yaniguan/WignerFlow) ([Studio](https://yaniguan.github.io/WignerFlow/)) | 50-fs integrator-free equivariant MD & strict `[physics]` surrogate gate for `YLM` |
| **L2 Eyes** | [`ouroboros-ocsr`](https://github.com/yaniguan/ouroboros-ocsr) ([Studio](https://yaniguan.github.io/ouroboros-ocsr/)) | SE(2)-equivariant chemical structure recognition bridging 2D figures to 3D conformers |
| **L2 Data** | [`assayfold`](https://github.com/yaniguan/assayfold) | Unified SHA-256-sealed, UCUM-normalized, SPDX-license-gated schema across 12 open lab datasets |

## Repository Layout

```text
auto-lab/
├── autolab/                      # Zero-dependency hub package & `autolab` CLI
│   ├── catalog.py                # Typed 7-layer registry & JSON catalog loaders
│   ├── loop_demo.py              # Deterministic L2 -> L6 -> L5 -> L4 -> L1 -> L0 -> L3 trace simulator
│   ├── trust_regime.py           # Runtime bridge to compiled `autolab-lean --batch-tsv`
│   ├── memory.py                 # 4-Layer 'Undergrad' Agent Memory + Bottom Reasoning Traces + Dreaming
│   └── cli.py                    # `autolab layers | list | inspect | loop | status | trust | memory`
├── catalog/
│   ├── repos.json                # Verified Object, Data, Model, Training, History, Properties for all 15 repos
│   ├── issues_index.json         # Structured index of all 300+ deep audit issues & live URLs
│   └── workspace.manifest.json   # Git URLs, branches, HEAD SHAs, and sibling checkout layout
├── docs/
│   ├── BRAIN_HIERARCHY.md        # Architectural specification of Layers L6 -> L0
│   ├── POSTTRAIN_FLYWHEEL.md     # Execution-to-RLVR data & post-training flywheel
│   ├── REPO_MATRIX.md            # Side-by-side 15-repository dossier matrix
│   ├── TRUST_REGIME_STUDY.md     # Formal Lean 4 Trust Regime & 5-task empirical study
│   ├── NOVEL_DIRECTIONS_FROM_COMMUNITY.md # 4 next-gen directions synthesized from 2025-2026 discourse
│   ├── AGENT_MEMORY_ARCHITECTURE.md # 4-Layer Undergrad Memory, Bottom Reasoning Traces & Dreaming
│   └── ISSUES_AUDIT_INDEX.md     # Master index of all filed GitHub Issues across the audited repos
├── lean/                         # AutoLabLean Hub Kernel: Lean 4.36.0 (50 theorems, 0 sorry; synced to 15 sub-repos)
│   ├── AutoLabLean/              # L6 -> L0 specs, bounded autonomy, frontiers & agent memory theorems
│   ├── Main.lean                 # Native `autolab-lean` showcase & `--batch-tsv` runtime verifier
│   └── lakefile.toml             # Zero-dependency Lake build configuration
├── paper/                        # Standalone arXiv Technical Preprint (LaTeX + Type-42 vector figures + compiled PDF)
│   ├── main.tex                  # Manuscript source
│   ├── autolab_preprint.sty      # Modern editorial preprint layout & Page-1 banner
│   ├── generate_figures.py       # Reproducible matplotlib vector PDF generator
│   └── main.pdf                  # Compiled 9-page preprint PDF (+ lab-attrib monograph in site/assets/)
├── benchmarks/
│   ├── trust_regime_study.py     # Reproducible 5-task empirical study via compiled `autolab-lean`
│   ├── novel_directions_study.py # Empirical evaluation of the 4 next-gen frontier directions
│   ├── agent_memory_study.py     # Rusty-SOP, novel-assay transfer & 60-session Dreaming memory study
│   ├── twenty_community_ideas_study.py # Unified harness running all 20 sub-repo `community_extensions/`
│   └── results/                  # Measured JSON metrics
├── scripts/
│   ├── sync_all.py               # Clone, fetch, or check git cleanliness across all 15 repos
│   └── build_site_data.py        # Compiles catalog/ and audit data into docs/ and site/assets/
├── site/                         # Multi-page GitHub Pages website
│   ├── index.html                # Overview, Monoline Robot Sketch & 19-Repo Topology
│   ├── trust/index.html          # Interactive Lean 4 Trust Regime & Empirical Lift Explorer
│   ├── studio/index.html         # Interactive Closed-Loop, Post-Train & Conformal Sandboxes
│   ├── repos/index.html          # Interactive 15-Repository Problem Stories & Live Examples
│   ├── audit/index.html          # Maintainer Issue Backlog Explorer
│   ├── shared.js                 # Shared theme persistence, data loader & SVG chart primitives
│   └── styles.css                # Clean daylight-first editorial stylesheet
└── tests/
    └── test_autolab.py           # Pytest suite verifying Lean proofs, cross-repo lean-mcp/v1 parity, CLI, and site assets
```

## Formal Trust Regime (`AutoLabLean`), Undergraduate Memory & Preprints

Every hard physical, statistical, stoichiometric, temporal, security, privacy, licensing, post-run attribution, and memory-hygiene guardrail across the 15 repositories is formalized centrally in [`lean/`](lean/) (`leanprover/lean4:v4.36.0`, **50 machine-checked theorems**, **27 `#guard` witnesses**, **0 `sorry`**), mirrored as standalone Lake packages (`<repo>/lean/`) across all 15 sub-repositories (**165+ sub-repo theorems**, including 25 in [`lab-attrib`](https://github.com/yaniguan/lab-attrib)), and documented in two standalone LaTeX monographs ([`paper/main.pdf`](paper/main.pdf) and [`lab-attrib/paper/main.pdf`](https://yaniguan.github.io/auto-lab/assets/lab_attrib_preprint.pdf)):

- **Bounded Molecular Discovery (`1,128` real Delaney ESOL compounds)**: Boundary violations drop from `72.0%` to **`0.0%`**, selected-run MAE drops **2.49x** (`0.978 -> 0.393` log mol/L), empirical 90% coverage reaches **`97.6%`**, and verified soluble hit yield climbs from `28.0%` to **`100.0%`**.
- **Wet-Lab Protocol Synthesis & Counterexample Repair (`200 x 8` candidates @ `30,048` proto/s)**: Catastrophic hardware faults drop from `78.0%` to **`0.0%`**, while valid task completion rises from `22.0%` (ungated) / `23.5%` (coarse heuristic) to **`87.0%`** (Lean Best-of-8) and **`97.5%`** (with Lean counterexample-guided 1-step repair).
- **Contended Fleet Scheduling (`30` `labshift` suites)**: Suite feasibility improves from `24/30` (`13` incubation window violations) to **`30/30` (`0` violations)** with **`10.2%` shorter mean makespan** (`129.8 -> 116.5 min`).
- **Lab SQL Verification (`lab-verify`) & Anti-Hack RLVR (`labbench-posttrain`)**: Wrong-SQL false accepts drop from `55.6%` (`L1–L3` syntax/schema only) to **`0.0%`**, and 5-seed `GRPO` true verified accuracy climbs from `0.4%` (`99.6%` exploit collapse under soft rewards) to **`98.4%`** under multiplicative Lean reward gating.
- **Next-Gen Frontier Directions (`NovelDirections.lean`)**: (1) *Diagnostic Epistemic Attribution* cuts post-execution false discoveries **`8.3% -> 0.0%`** and lifts verified hits **`+29.5%`** (`52.2 -> 67.6`); (2) *Stepped Frontier Calibration (`Chem-RRT`)* unlocks **`30.8–54.4`** novel multi-ring scaffolds (vs `1.2` static) with **`0.0`** uncalibrated leaps; (3) *Proof-Carrying `Lean-MCP` Envelopes* deliver **`5.36x`** higher 72h protocol throughput than per-run human approval (`472` vs `88`) with **`0`** unsafe/replay runs; and (4) *Adversarial Saboteur-Verifier Co-Evolution* drives protocol evasion from **`85.7% -> 0.0%`**.

## Scientific Honesty & Status

- **CPU vs GPU**: Every benchmark reported in `auto-lab` and its 15 child repositories distinguishes completed CPU measurements (`labfill`, `labshift`, `twinstep`, `stepbot`, `buy-or-make`, `lab-ears`, `lab-decide`, `lab-verify`, `lab-rehearsal`, `lab-attrib`, `lab-hands`, `lab-feet`, and `labbench-posttrain` smoke runs) from full A100/H100 post-training campaigns, which remain explicitly marked `PENDING` until executed.
- **License Discipline**: Non-commercial benchmarks and datasets (`BioProBench`, `SciFact`, `TransCG`, `Touch-Slide`) and ShareAlike evaluation suites (`LAB-Bench` with canary strings) retain their upstream licenses and are never laundered into MIT/commercial exports.

## Citation

```bibtex
@misc{guan2026autolab,
  title  = {Auto-Lab: A Multi-Layer Embodied Brain, Default-Deny Safety Harness, and Verifiable Post-Training Stack for Autonomous Wet Laboratories},
  author = {Guan, Yani},
  year   = {2026},
  url    = {https://github.com/yaniguan/auto-lab},
  note   = {Project Studio: https://yaniguan.github.io/auto-lab/}
}
```

## License

Code and documentation in `auto-lab`: MIT ([LICENSE](LICENSE)). Linked datasets and upstream tools retain their own licenses.
