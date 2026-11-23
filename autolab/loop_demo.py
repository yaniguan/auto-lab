"""Deterministic 7-Layer Closed-Loop Lab Simulation across the Auto-Lab stack.

Demonstrates how a single wet-lab goal traverses:
  L2 (lab-ears) -> L6 (lab-ask-why + lab-decide) -> L5 (buy-or-make + labshift)
  -> L4 (lab-rehearsal + lab-verify) -> L1 (stepbot + lab-hands) -> L0 (lab-feet)
  -> L3 (twinstep + labfill + labbench-posttrain write-back).
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TraceStep:
    layer: str
    repo: str
    stage: str
    verdict: str  # PASS | ABSTAIN | BLOCK | TRIAGE | SCHEDULED | LEARNED
    latency_ms: float
    summary: str
    artifact: dict[str, Any]


SCENARIOS: dict[str, dict[str, Any]] = {
    "serial_dilution": {
        "id": "serial_dilution",
        "title": "Clean 8-Well 2-Fold Serial Dilution + Absorbance Read",
        "goal_text": "Prepare 100 uL 2-fold aspirin dye serial dilution across A1-H1 at 25 C for 10 min, then read 450 nm absorbance.",
        "candidate_smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "knn_distance": 0.412,
        "knn_threshold": 0.758,
        "conformal_interval_logS": [-2.41, 0.63],
        "buyable": True,
        "listed_price_usd_per_g": 0.42,
        "route_steps": 0,
        "budget_usd": 25.0,
        "max_wait_min": 15,
        "greedy_wait_min": 9,
        "cpsat_makespan_min": 66,
        "rehearsal_violations": [],
        "prior_failures": [],
        "sql_layers_passed": 4,
        "opentrons_commands": 86,
        "rrt_shortcut_rad": 2.08,
        "edge_int8_us": 3.86,
        "rlvr_reward": 1.0,
    },
    "broken_tip_reuse": {
        "id": "broken_tip_reuse",
        "title": "Cross-Contaminating Tip Reuse in Buffer Reservoir",
        "goal_text": "Transfer 100 uL sample into A1, keep tip, and aspirate 100 uL buffer from reservoir:1 into A2.",
        "candidate_smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "knn_distance": 0.412,
        "knn_threshold": 0.758,
        "conformal_interval_logS": [-2.41, 0.63],
        "buyable": True,
        "listed_price_usd_per_g": 0.42,
        "route_steps": 0,
        "budget_usd": 25.0,
        "max_wait_min": 15,
        "greedy_wait_min": 8,
        "cpsat_makespan_min": 62,
        "rehearsal_violations": [
            "step 4 no_tip_reuse: tip carrying ['sample'] reused in res:1 containing ['buffer']"
        ],
        "prior_failures": ["run #4 (no_tip_reuse)"],
        "sql_layers_passed": 4,
        "opentrons_commands": 0,
        "rrt_shortcut_rad": 0.0,
        "edge_int8_us": 3.86,
        "rlvr_reward": -1.0,
    },
    "uncalibrated_molecule": {
        "id": "uncalibrated_molecule",
        "title": "Out-of-Domain Fluorinated Macrocycle Solubility Proposal",
        "goal_text": "Predict aqueous solubility of perfluorinated macrocycle candidate and launch 37 C assay at 1200 rpm for 30 min.",
        "candidate_smiles": "FC1(F)CCCC(F)(F)CCCC(F)(F)CCCC1(F)F",
        "knn_distance": 1.384,
        "knn_threshold": 0.758,
        "conformal_interval_logS": [-7.95, -4.91],
        "buyable": False,
        "listed_price_usd_per_g": None,
        "route_steps": None,
        "budget_usd": 25.0,
        "max_wait_min": 20,
        "greedy_wait_min": 11,
        "cpsat_makespan_min": 74,
        "rehearsal_violations": [],
        "prior_failures": [],
        "sql_layers_passed": 4,
        "opentrons_commands": 0,
        "rrt_shortcut_rad": 0.0,
        "edge_int8_us": 3.86,
        "rlvr_reward": 0.25,
    },
    "over_budget_analog": {
        "id": "over_budget_analog",
        "title": "Novel Biphenyl Amide Analog — 2-Step Makeable Triage",
        "goal_text": "Screen biphenyl amide analog at 50 uL across 4 wells, incubate 37 C for 30 min, wash 3 cycles with 200 uL buffer.",
        "candidate_smiles": "COc1ccc(C(=O)Nc2ccc(-c3ccccn3)cc2)cc1",
        "knn_distance": 0.641,
        "knn_threshold": 0.758,
        "conformal_interval_logS": [-4.82, -1.78],
        "buyable": False,
        "listed_price_usd_per_g": None,
        "route_steps": 2,
        "est_leaf_cost_usd_per_g": 18.60,
        "budget_usd": 25.0,
        "max_wait_min": 10,
        "greedy_wait_min": 17,
        "cpsat_makespan_min": 105,
        "rehearsal_violations": [],
        "prior_failures": [],
        "sql_layers_passed": 4,
        "opentrons_commands": 109,
        "rrt_shortcut_rad": 2.14,
        "edge_int8_us": 3.86,
        "rlvr_reward": 0.92,
    },
}


def run_closed_loop_scenario(
    scenario_id: str = "serial_dilution",
    *,
    strict_gate: bool = True,
    use_episodic_recall: bool = True,
) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario {scenario_id!r}. Choose from {sorted(SCENARIOS)}")

    sc = SCENARIOS[scenario_id]
    digest = hashlib.sha256(sc["goal_text"].encode("utf-8")).hexdigest()[:12]
    steps: list[TraceStep] = []

    steps.append(
        TraceStep(
            layer="L2",
            repo="lab-ears",
            stage="Protocol Span & Acoustic Check",
            verdict="PASS",
            latency_ms=4.2,
            summary="Extracted Amount/Temperature/Time/Speed spans; centrifuge-01 log-mel score below threshold (speech band dropped).",
            artifact={
                "protocol_hash": digest,
                "slots": {"Amount": "100 uL", "Temperature": "25-37 C", "Time": "10-30 min"},
                "acoustic_flagged": False,
                "speech_band_dropped": True,
            },
        )
    )

    steps.append(
        TraceStep(
            layer="L6",
            repo="lab-ask-why",
            stage="Socratic Evidence & Discriminating Test",
            verdict="PASS",
            latency_ms=6.8,
            summary="Retrieved top-3 supporting/contradicting rationale sentences (BM25) and formulated falsifiable control question.",
            artifact={
                "support_recall_at_3": 0.797,
                "contradict_recall_at_3": 0.775,
                "discriminating_question": "Does blank buffer control in H1 remain at baseline OD450 without carryover?",
            },
        )
    )

    in_trust = sc["knn_distance"] <= sc["knn_threshold"]
    if not in_trust and strict_gate:
        steps.append(
            TraceStep(
                layer="L6",
                repo="lab-decide",
                stage="Conformal Trust-Region Gate",
                verdict="ABSTAIN",
                latency_ms=1.9,
                summary=(
                    f"kNN distance {sc['knn_distance']:.3f} > 80th-pct calibration threshold "
                    f"{sc['knn_threshold']:.3f}: abstaining and queuing calibration acquisition."
                ),
                artifact={
                    "knn_distance": sc["knn_distance"],
                    "threshold": sc["knn_threshold"],
                    "trusted": False,
                    "action": "abstain_and_request_calibration_measurement",
                },
            )
        )
        steps.append(
            TraceStep(
                layer="L3",
                repo="labbench-posttrain",
                stage="Calibrated Abstention Reward Write-Back",
                verdict="LEARNED",
                latency_ms=11.4,
                summary="Logged honest epistemic abstention (+0.25 anti-hallucination reward) without touching wet-lab hardware.",
                artifact={"reward": sc["rlvr_reward"], "bench_commands_sent": 0},
            )
        )
        return _finalize(sc, digest, "ABSTAINED_AT_L6", steps)

    steps.append(
        TraceStep(
            layer="L6",
            repo="lab-decide",
            stage="Conformal Trust-Region Gate",
            verdict="PASS" if in_trust else "TRIAGE",
            latency_ms=1.9,
            summary=(
                f"Inside calibrated kNN trust region ({sc['knn_distance']:.3f} <= {sc['knn_threshold']:.3f}); "
                f"90% split-conformal interval {sc['conformal_interval_logS']} logS."
            ),
            artifact={
                "knn_distance": sc["knn_distance"],
                "threshold": sc["knn_threshold"],
                "interval_90pct": sc["conformal_interval_logS"],
            },
        )
    )

    proc_status = "buyable" if sc["buyable"] else ("makeable" if sc.get("route_steps") else "unknown")
    steps.append(
        TraceStep(
            layer="L5",
            repo="buy-or-make",
            stage="Availability & Listed-Price Triage",
            verdict="PASS" if proc_status in ("buyable", "makeable") else "BLOCK",
            latency_ms=5.0,
            summary=(
                f"Candidate classified as '{proc_status}' "
                + (
                    f"(listed ${sc['listed_price_usd_per_g']:.2f}/g)."
                    if sc["buyable"]
                    else f"({sc.get('route_steps')}-step SMARTS route, leaf lower bound ${sc.get('est_leaf_cost_usd_per_g', 0.0):.2f}/g <= ${sc['budget_usd']:.2f})."
                )
            ),
            artifact={
                "smiles": sc["candidate_smiles"],
                "status": proc_status,
                "n_steps": sc.get("route_steps"),
                "price_basis": "listed_catalog",
            },
        )
    )

    greedy_ok = sc["greedy_wait_min"] <= sc["max_wait_min"]
    steps.append(
        TraceStep(
            layer="L5",
            repo="labshift",
            stage="Multi-Instrument Window Scheduling",
            verdict="SCHEDULED",
            latency_ms=14.6,
            summary=(
                f"CP-SAT found zero-violation schedule (makespan {sc['cpsat_makespan_min']} min)"
                + (
                    ""
                    if greedy_ok
                    else f", repairing greedy max_wait violation ({sc['greedy_wait_min']}m > {sc['max_wait_min']}m)."
                )
            ),
            artifact={
                "solver": "cpsat",
                "makespan_min": sc["cpsat_makespan_min"],
                "window_violations": 0,
                "greedy_would_violate": not greedy_ok,
            },
        )
    )

    violations = list(sc["rehearsal_violations"])
    recalled = list(sc["prior_failures"]) if use_episodic_recall else []
    if violations and strict_gate:
        steps.append(
            TraceStep(
                layer="L4",
                repo="lab-rehearsal",
                stage="Recall + 96-Well Digital Twin Rehearsal",
                verdict="BLOCK",
                latency_ms=2.3,
                summary=(
                    (f"RECALL warning {recalled}; " if recalled else "")
                    + f"Verify gate blocked execution ({len(violations)} violation: {violations[0]})."
                ),
                artifact={
                    "recalled_runs": recalled,
                    "violations": violations,
                    "commands_sent_to_robot": 0,
                },
            )
        )
        steps.append(
            TraceStep(
                layer="L3",
                repo="twinstep + labbench-posttrain",
                stage="Negative Twin & Episodic Memory Write-Back",
                verdict="LEARNED",
                latency_ms=15.2,
                summary="Appended blocked run to runs.jsonl, emitted labeled error-twin pair, and scored -1.0 safety violation penalty for DPO/GDPO.",
                artifact={
                    "episodic_ledger": "memory/runs.jsonl",
                    "twin_label": "no_tip_reuse",
                    "rlvr_reward": sc["rlvr_reward"],
                },
            )
        )
        return _finalize(sc, digest, "BLOCKED_AT_L4_GATE", steps)

    steps.append(
        TraceStep(
            layer="L4",
            repo="lab-rehearsal + lab-verify",
            stage="Digital Twin Dry-Run & 4-Layer Default-Deny Gate",
            verdict="PASS",
            latency_ms=3.4,
            summary=f"0 liquid-handling violations across 96-well twin; SQL ledger audit passed all {sc['sql_layers_passed']}/4 layers.",
            artifact={
                "rehearsal_violations": 0,
                "sql_gate_layers": ["parse", "read_only", "schema", "execution_match"],
            },
        )
    )

    steps.append(
        TraceStep(
            layer="L1",
            repo="stepbot + lab-hands",
            stage="Opentrons v2 Compilation & Collision-Free RRT",
            verdict="PASS",
            latency_ms=71.8,
            summary=(
                f"Compiled {sc['opentrons_commands']} deterministic apiLevel 2.16 commands and shortcut 2-link RRT trajectory to {sc['rrt_shortcut_rad']:.2f} rad."
            ),
            artifact={
                "api_level": "2.16",
                "simulated_commands": sc["opentrons_commands"],
                "rrt_path_rad": sc["rrt_shortcut_rad"],
            },
        )
    )

    steps.append(
        TraceStep(
            layer="L0",
            repo="lab-feet",
            stage="Quantized Bench-Side Policy Runtime",
            verdict="PASS",
            latency_ms=0.4,
            summary=f"Executed local int8 student monitor ({sc['edge_int8_us']:.2f} us median forward pass, 35x parameter reduction).",
            artifact={"quantization": "int8", "median_latency_us": sc["edge_int8_us"]},
        )
    )

    steps.append(
        TraceStep(
            layer="L3",
            repo="labfill + labbench-posttrain",
            stage="Sequence-Packed BF16 Replay & RLVR Update",
            verdict="LEARNED",
            latency_ms=18.9,
            summary=(
                f"Packed verified execution trace (92.1% useful tokens, 5.42x CPU BF16 throughput) into SplitGuard-checked labrl reward={sc['rlvr_reward']:.2f}."
            ),
            artifact={
                "useful_token_pct": 92.1,
                "split_guard": "zero_group_leakage",
                "rlvr_reward": sc["rlvr_reward"],
            },
        )
    )

    return _finalize(sc, digest, "EXECUTED_AND_WRITTEN_BACK", steps)


def _finalize(
    sc: dict[str, Any],
    digest: str,
    final_status: str,
    steps: list[TraceStep],
) -> dict[str, Any]:
    total_ms = round(sum(s.latency_ms for s in steps), 2)
    return {
        "scenario_id": sc["id"],
        "title": sc["title"],
        "protocol_hash": digest,
        "final_status": final_status,
        "total_simulated_ms": total_ms,
        "layers_traversed": [s.layer for s in steps],
        "steps": [asdict(s) for s in steps],
    }
