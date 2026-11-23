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
    name_en: str
    name_zh: str
    brain_analogy_en: str
    brain_analogy_zh: str
    color: str
    summary_en: str
    summary_zh: str


LAYERS: tuple[LayerSpec, ...] = (
    LayerSpec(
        code="L6",
        order=6,
        name_en="Metacognitive & Epistemic Brain",
        name_zh="高层元认知与校准决策脑",
        brain_analogy_en="Prefrontal & Anterior Cingulate Cortex",
        brain_analogy_zh="前额叶与前扣带皮层（追问、校准与弃权）",
        color="purple",
        summary_en="Surfaces opposing scientific rationales, proposes discriminating experiments, and abstains outside conformal trust regions.",
        summary_zh="不盲目站队，检索正反双方证据并设计鉴别实验；仅在共形预测校准可信域内作答，域外明确拒答并随新数据安全扩张。",
    ),
    LayerSpec(
        code="L5",
        order=5,
        name_en="Executive Planning, Procurement & Fleet Scheduling",
        name_zh="执行规划、采购逆合成与多机排程层",
        brain_analogy_en="Dorsolateral Prefrontal & Basal Ganglia",
        brain_analogy_zh="背外侧前额叶与基底节（资源权衡与时序调度）",
        color="blue",
        summary_en="Triages make-vs-buy molecular availability with strict listed-price lower bounds, maps the automation ecosystem, and schedules multi-instrument time windows via CP-SAT.",
        summary_zh="基于公开目录实价估算分子采购或 N 步合成下界，维护自动化生态语义图谱，并用 CP-SAT 求解多仪器时间窗排程。",
    ),
    LayerSpec(
        code="L4",
        order=4,
        name_en="Digital-Twin Rehearsal & Default-Deny Verification",
        name_zh="数字孪生预演与默认拒绝安全门",
        brain_analogy_en="Premotor Simulation & Inhibitory Safety Gate",
        brain_analogy_zh="前运动皮层心理预演与基底节抑制门控",
        color="teal",
        summary_en="Recalls historical failures, dry-runs deck operations in a digital twin, enforces multi-layer default-deny checks (Lean, SQL, protocol), and writes outcomes back to episodic memory.",
        summary_zh="执行前检索历史事故、在数字孪生甲板预演体积与枪头状态、通过四层默认拒绝校验门（Lean/SQL/协议规则），并将结果写回情景记忆。",
    ),
    LayerSpec(
        code="L3",
        order=3,
        name_en="Post-Training RLVR, Error Twins & GPU Throughput",
        name_zh="突触可塑性、可验证强化学习后训练与吞吐引擎",
        brain_analogy_en="Hippocampal Replay & Cerebellar Plasticity Flywheel",
        brain_analogy_zh="海马体经验回放与小脑突触可塑性飞轮",
        color="amber",
        summary_en="Generates seeded protocol error twins, batches validation and packed BF16 training on a single GPU, and runs SFT -> DPO/MPO/TROPD -> PPO/GRPO/GDPO+DAPO with cryptographic SplitGuard.",
        summary_zh="确定性注入协议错误孪生对，将校验与序列打包 BF16 训练张量化，并通过防作弊可验证奖励模板运行全栈后训练。",
    ),
    LayerSpec(
        code="L2",
        order=2,
        name_en="Multimodal Sensory & Protocol Cortex",
        name_zh="听觉与协议多模态感知皮层",
        brain_analogy_en="Auditory & Language Comprehension Cortex",
        brain_analogy_zh="听觉皮层与语言理解区（协议槽位解析与仪器异响监测）",
        color="blue",
        summary_en="Extracts structured amounts, temperatures, times, and speeds from wet-lab text and monitors instrument acoustic anomalies with speech-band privacy filtering.",
        summary_zh="从湿实验文本提取体积、温度、时间与转速，并以滤除人声频段的隐私安全方式检测实验室仪器异常声学特征。",
    ),
    LayerSpec(
        code="L1",
        order=1,
        name_en="Protocol Compiler & Visuo-Tactile Manipulation",
        name_zh="确定性协议编译与灵巧触觉操作皮层",
        brain_analogy_en="Primary Motor & Somatosensory Cortex",
        brain_analogy_zh="初级运动皮层与躯体触觉皮层（硬件编译、避障与透明器皿触觉）",
        color="teal",
        summary_en="Compiles YAML/JSON steps into deterministic Opentrons Python API v2 code with volume accounting, and plans collision-free joint-space RRT paths with last-centimeter tactile sensing.",
        summary_zh="将声明式 YAML/JSON 编译为确定性 Opentrons API v2 协议并追踪孔板液量，同时规划无碰撞关节空间轨迹并用触觉补足透明器皿最后一厘米操作。",
    ),
    LayerSpec(
        code="L0",
        order=0,
        name_en="Edge Body & Quantized Runtime",
        name_zh="边缘算力躯干与量化蒸馏推理层",
        brain_analogy_en="Spinal Cord & Peripheral Nervous System",
        brain_analogy_zh="脊髓反射弧与外周边缘算力（蒸馏 + INT8/4-bit 台边推理）",
        color="purple",
        summary_en="Distills teacher models into compact students quantized to int8 and 4-bit so routine bench loops run locally on low-power CPU/NPU boards.",
        summary_zh="通过知识蒸馏与 INT8/4-bit 权重量化压缩模型，使常规实验闭环可在实验台旁低功耗单板机本地运行。",
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
        "organ_en": "3D Geometry + Language Core Brain & LabLean Ledger",
        "organ_zh": "三维等变分子语言核心大脑与 LabLean 账本",
        "summary_en": "SE(3)-equivariant cross-attention where text tokens query l >= 1 spherical tensors directly, plus the canonical LabLean 4 protocol specification.",
        "summary_zh": "文本直接查询 SE(3) 高阶球谐特征的三维化学语言模型，同时承载 LabLean 形式化协议语言与统一账本规范。",
    },
    {
        "repo": "WignerFlow",
        "url": "https://github.com/yaniguan/WignerFlow",
        "page": "https://yaniguan.github.io/WignerFlow/",
        "layer": "L4",
        "organ_en": "50-fs Equivariant Physics World Model & [physics] Gate",
        "organ_zh": "50 fs 等变分子动力学世界模型与物理门控",
        "summary_en": "Integrator-free O(3)-equivariant flow matching jumping 50 fs/step, serving sub-second FrameSplit CPU rollouts and strict [physics] domain checks.",
        "summary_zh": "无需数值积分器的 50 fs 大步长等变流匹配动力学，为推理大脑提供亚秒级 CPU 物理先验与严格域外拒答。",
    },
    {
        "repo": "ouroboros-ocsr",
        "url": "https://github.com/yaniguan/ouroboros-ocsr",
        "page": "https://yaniguan.github.io/ouroboros-ocsr/",
        "layer": "L2",
        "organ_en": "SE(2)-Equivariant Chemical Vision (Eyes)",
        "organ_zh": "SE(2) 旋转等变化学结构视觉皮层（眼睛）",
        "summary_en": "Reads rotated 2D chemical drawings from papers and patents into stereochemically aware SMILES verified against 3D conformers.",
        "summary_zh": "任意旋转角度下从文献与专利插图识别带立体化学信息的 SMILES，并与三维构象能量对齐。",
    },
    {
        "repo": "assayfold",
        "url": "https://github.com/yaniguan/assayfold",
        "page": "",
        "layer": "L2",
        "organ_en": "License-Gated Open Science Data Schema & Ingestion",
        "organ_zh": "许可证门控的开放实验数据统一底座",
        "summary_en": "Normalizes open protocols, reactions, QM9/DFT, LabPics images, and benchmarks into one SHA-256-sealed, UCUM-unit, SPDX-gated schema.",
        "summary_zh": "将开放科学协议、反应、量化计算与实验图像统一为带 SHA-256 签名、UCUM 单位归一化与商用许可证门控的标准记录。",
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
