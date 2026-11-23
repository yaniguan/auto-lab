"""Typed registry and catalog loader for the 7-layer Auto-Lab architecture."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog" / "repos.json"
ISSUES_INDEX_PATH = REPO_ROOT / "catalog" / "issues_index.json"


@dataclass(frozen=True)
class LayerSpec:
    code: str
    order: int
    name: str
    brain_analogy: str
    color: str
    summary: str


LAYERS: tuple[LayerSpec, ...] = (
    LayerSpec(
        code="L6",
        order=6,
        name="Metacognitive & Epistemic Brain",
        brain_analogy="Prefrontal & Anterior Cingulate Cortex",
        color="purple",
        summary="Surfaces opposing scientific rationales, proposes discriminating experiments, and abstains outside calibrated conformal trust regions.",
    ),
    LayerSpec(
        code="L5",
        order=5,
        name="Executive Planning, Procurement & Scheduling",
        brain_analogy="Dorsolateral Prefrontal & Basal Ganglia",
        color="blue",
        summary="Triages make-vs-buy molecular availability with listed-price lower bounds, maps lab standards, and schedules shared instrument pools via CP-SAT.",
    ),
    LayerSpec(
        code="L4",
        order=4,
        name="Digital-Twin Rehearsal & Default-Deny Gate",
        brain_analogy="Premotor Simulation & Inhibitory Gate",
        color="teal",
        summary="Recalls historical failures, dry-runs deck operations in a digital twin, enforces default-deny checks (Lean, SQL, protocol), and writes outcomes back to memory.",
    ),
    LayerSpec(
        code="L3",
        order=3,
        name="Post-Training RLVR, Error Twins & GPU Packing",
        brain_analogy="Hippocampal Replay & Cerebellar Plasticity",
        color="amber",
        summary="Generates seeded protocol error twins, batches validation and packed BF16 training on a single GPU, and runs SFT -> DPO/MPO/TROPD -> PPO/GRPO/GDPO+DAPO with SplitGuard.",
    ),
    LayerSpec(
        code="L2",
        order=2,
        name="Multimodal Sensory & Protocol Cortex",
        brain_analogy="Auditory & Language Comprehension Cortex",
        color="blue",
        summary="Extracts structured amounts, temperatures, times, and speeds from wet-lab text and monitors machine acoustic anomalies with speech-band privacy filtering.",
    ),
    LayerSpec(
        code="L1",
        order=1,
        name="Protocol Compiler & Visuo-Tactile Manipulation",
        brain_analogy="Primary Motor & Somatosensory Cortex",
        color="teal",
        summary="Compiles declarative YAML/JSON steps into deterministic Opentrons API v2 code with volume tracking, and plans collision-free RRT paths with last-centimeter touch.",
    ),
    LayerSpec(
        code="L0",
        order=0,
        name="Edge Body & Quantized Runtime",
        brain_analogy="Spinal Cord & Peripheral Compute",
        color="purple",
        summary="Distills teacher models into compact students quantized to int8 and 4-bit so routine bench loops execute locally on low-power edge boards.",
    ),
)

CORE_REPO_NAMES: tuple[str, ...] = (
    "lab-ask-why",
    "lab-decide",
    "buy-or-make",
    "labshift",
    "lab-automation-atlas",
    "lab-rehearsal",
    "lab-verify",
    "lab-attrib",
    "labbench-posttrain",
    "twinstep",
    "labfill",
    "lab-ears",
    "stepbot",
    "lab-hands",
    "lab-feet",
)

COMPANION_REPOS: tuple[dict[str, str], ...] = (
    {
        "repo": "YLM",
        "url": "https://github.com/yaniguan/YLM",
        "page": "https://yaniguan.github.io/YLM/",
        "layer": "L6",
        "organ": "3D Geometry + Language Core Brain & LabLean Ledger",
        "summary": "SE(3)-equivariant cross-attention where text tokens query l >= 1 spherical tensors directly, plus the canonical LabLean 4 protocol specification.",
    },
    {
        "repo": "WignerFlow",
        "url": "https://github.com/yaniguan/WignerFlow",
        "page": "https://yaniguan.github.io/WignerFlow/",
        "layer": "L4",
        "organ": "50-fs Equivariant Physics World Model & [physics] Gate",
        "summary": "Integrator-free O(3)-equivariant flow matching jumping 50 fs/step, serving sub-second FrameSplit CPU rollouts and strict [physics] domain checks.",
    },
    {
        "repo": "ouroboros-ocsr",
        "url": "https://github.com/yaniguan/ouroboros-ocsr",
        "page": "https://yaniguan.github.io/ouroboros-ocsr/",
        "layer": "L2",
        "organ": "SE(2)-Equivariant Chemical Vision (Eyes)",
        "summary": "Reads rotated 2D chemical drawings from papers and patents into stereochemically aware SMILES verified against 3D conformers.",
    },
    {
        "repo": "assayfold",
        "url": "https://github.com/yaniguan/assayfold",
        "page": "",
        "layer": "L2",
        "organ": "License-Gated Open Science Data Schema & Ingestion",
        "summary": "Normalizes open protocols, reactions, QM9/DFT, LabPics images, and benchmarks into one SHA-256-sealed, UCUM-unit, SPDX-gated schema.",
    },
)


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or CATALOG_PATH
    if not target.exists():
        return []
    with target.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "repos" in data:
        return list(data["repos"])
    return list(data)


def load_issues_index(path: Path | None = None) -> dict[str, Any]:
    target = path or ISSUES_INDEX_PATH
    if not target.exists():
        return {"total_issues": 0, "repos": {}}
    with target.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def get_repo(name: str, path: Path | None = None) -> dict[str, Any]:
    norm = name.strip().lower()
    for item in load_catalog(path):
        if item["repo"].lower() == norm:
            return item
    raise KeyError(f"Unknown Auto-Lab repository: {name!r}")
