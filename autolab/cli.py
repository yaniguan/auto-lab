"""Command-line interface for the Auto-Lab multi-repository hub."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from autolab.catalog import (
    COMPANION_REPOS,
    CORE_REPO_NAMES,
    LAYERS,
    REPO_ROOT,
    get_repo,
    load_catalog,
    load_issues_index,
)
from autolab.loop_demo import SCENARIOS, run_closed_loop_scenario
from autolab.memory import build_seed_undergrad_memory
from autolab.trust_regime import LeanBatchKernel, audit_lean_sources, find_autolab_lean_binary


def _cmd_layers(_args: argparse.Namespace) -> int:
    print("Auto-Lab 7-Layer Embodied Co-Scientist Hierarchy (Top-Down Brain -> Edge Body)\n")
    catalog = load_catalog()
    by_layer: dict[str, list[str]] = {layer.code: [] for layer in LAYERS}
    for r in catalog:
        by_layer.setdefault(r["layer"], []).append(r["repo"])

    for layer in LAYERS:
        members = ", ".join(by_layer.get(layer.code, [])) or "(loading)"
        print(f"[{layer.code}] {layer.name}  ({layer.brain_analogy})")
        print(f"     Repos : {members}")
        print(f"     Role  : {layer.summary}\n")

    print("Connected Companion Organs:")
    for comp in COMPANION_REPOS:
        print(f"  - [{comp['layer']}] {comp['repo']:16s} : {comp['organ']} ({comp['url']})")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    catalog = load_catalog()
    issues_idx = load_issues_index().get("repos", {})
    if args.layer:
        target = args.layer.strip().upper()
        catalog = [r for r in catalog if r["layer"].upper() == target]

    print(f"{'Layer':5s} | {'Repository':22s} | {'Issues':6s} | {'HEAD':10s} | Role")
    print("-" * 96)
    for r in catalog:
        icount = issues_idx.get(r["repo"], {}).get("count", r.get("issue_count", 0))
        head = str(r.get("commit_head", "-"))[:10]
        tagline = r.get("tagline", "")[:46]
        print(f"{r['layer']:5s} | {r['repo']:22s} | {icount:6d} | {head:10s} | {tagline}")
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    repo = get_repo(args.repo)
    if args.json:
        print(json.dumps(repo, indent=2, ensure_ascii=False))
        return 0

    print(f"=== {repo['repo']} ({repo['layer']} · {repo['layer_name']}) ===")
    print(f"URL     : {repo['url']}")
    print(f"Tagline : {repo['tagline']}\n")
    for key, label in (
        ("object", "1. Object"),
        ("data", "2. Data"),
        ("model", "3. Model"),
        ("training", "4. Training"),
        ("history", "5. History"),
    ):
        print(f"{label}:\n  {repo.get(key, '')}\n")
    print("6. Unique Properties:")
    for prop in repo.get("unique_properties", []):
        print(f"  - {prop}")
    return 0


def _cmd_loop(args: argparse.Namespace) -> int:
    report = run_closed_loop_scenario(
        args.scenario,
        strict_gate=not args.no_strict_gate,
        use_episodic_recall=not args.no_recall,
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0

    print(f"Scenario : {report['title']} (hash={report['protocol_hash']})")
    print(f"Outcome  : {report['final_status']} ({report['total_simulated_ms']} ms simulated)\n")
    for idx, step in enumerate(report["steps"], start=1):
        print(
            f"  {idx:02d}. [{step['layer']}] {step['repo']:28s} -> {step['verdict']:9s} | {step['summary']}"
        )
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    workspace_root = Path(args.root).resolve()
    print(f"Checking 14 sibling repositories under {workspace_root}\n")
    print(f"{'Repository':22s} | {'Present':7s} | {'Branch':14s} | {'HEAD':8s} | {'Clean':5s} | {'Profile Doc'}")
    print("-" * 88)
    missing = 0
    for name in CORE_REPO_NAMES:
        rdir = workspace_root / name
        if not (rdir / ".git").exists():
            print(f"{name:22s} | {'NO':7s} | {'-':14s} | {'-':8s} | {'-':5s} | -")
            missing += 1
            continue
        branch = subprocess.check_output(
            ["git", "-C", str(rdir), "rev-parse", "--abbrev-ref", "HEAD"], text=True
        ).strip()
        sha = subprocess.check_output(
            ["git", "-C", str(rdir), "rev-parse", "--short", "HEAD"], text=True
        ).strip()
        porcelain = subprocess.check_output(
            ["git", "-C", str(rdir), "status", "--porcelain"], text=True
        ).strip()
        has_doc = (rdir / "docs" / "ARCHITECTURE_AND_HISTORY.md").exists()
        print(
            f"{name:22s} | {'YES':7s} | {branch[:14]:14s} | {sha[:8]:8s} | "
            f"{'YES' if not porcelain else 'DIRTY':5s} | {'YES' if has_doc else 'NO'}"
        )
    return 1 if missing else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autolab",
        description="CLI for the 7-Layer Robot AI Auto-Lab infrastructure & post-training stack.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_layers = sub.add_parser("layers", help="Show the 7-layer Brain-to-Body architecture")
    p_layers.set_defaults(func=_cmd_layers)

    p_list = sub.add_parser("list", help="List all 14 core Auto-Lab repositories")
    p_list.add_argument("--layer", help="Filter by layer code (L0..L6)")
    p_list.set_defaults(func=_cmd_list)

    p_insp = sub.add_parser("inspect", help="Inspect Object/Data/Model/Training/History/Properties of a repo")
    p_insp.add_argument("repo", help="Repository name (e.g. labbench-posttrain, lab-decide)")
    p_insp.add_argument("--json", action="store_true", help="Emit raw JSON")
    p_insp.set_defaults(func=_cmd_inspect)

    p_loop = sub.add_parser("loop", help="Run a deterministic 7-layer closed-loop scenario trace")
    p_loop.add_argument(
        "--scenario",
        default="serial_dilution",
        choices=sorted(SCENARIOS.keys()),
        help="Scenario identifier",
    )
    p_loop.add_argument("--no-strict-gate", action="store_true", help="Disable strict L6/L4 blocking")
    p_loop.add_argument("--no-recall", action="store_true", help="Disable L4 episodic recall")
    p_loop.add_argument("--json", action="store_true", help="Emit JSON trace")
    p_loop.set_defaults(func=_cmd_loop)

    p_status = sub.add_parser("status", help="Check local checkout health of all 14 sibling repos")
    p_status.add_argument(
        "--root",
        default=str(REPO_ROOT.parent),
        help="Parent directory holding the 14 cloned repositories",
    )
    p_status.set_defaults(func=_cmd_status)

    p_trust = sub.add_parser("trust", help="Inspect the Lean 4 AutoLabLean Trust Regime & empirical lift")
    p_trust.add_argument("--json", action="store_true", help="Emit JSON summary")
    p_trust.set_defaults(func=_cmd_trust)

    p_mem = sub.add_parser("memory", help="Inspect & test the 4-layer Undergrad Agent Memory + Dreaming")
    p_mem.add_argument("--json", action="store_true", help="Emit JSON summary")
    p_mem.set_defaults(func=_cmd_memory)
    return parser


def _cmd_memory(args: argparse.Namespace) -> int:
    store = build_seed_undergrad_memory()
    dream = store.dream_consolidate()
    kernel = LeanBatchKernel()
    rusty_demo = store.invoke_skill(
        "viscous-liquid-handling",
        current_day=145,
        current_deck_epoch=2,
        physical_params={
            "viscosity_cp": 95.0,
            "nominal_dead_vol_ul": 5.0,
            "transfer_total_ul": 180.0,
            "source_vol_ul": 186.0,
        },
        auto_refresh_if_rusty=True,
        kernel=kernel,
    )
    novel_demo = store.onboard_novel_assay(
        "peg400_crowding_buffer_dispense",
        query_tags={"pipetting", "high-viscosity", "surfactant-or-polyol", "multi-dispense"},
        raw_params={
            "viscosity_cp": 115.0,
            "nominal_dead_vol_ul": 5.0,
            "transfer_total_ul": 150.0,
            "source_vol_ul": 155.0,
            "temp_c": 37.0,
        },
        use_bottom_trace=True,
        query_lab_tools=True,
        kernel=kernel,
    )
    payload = {
        "dream_consolidation": dream.__dict__,
        "injected_markdown": store.render_injected_markdown(),
        "rusty_skill_recovery": rusty_demo,
        "novel_assay_onboarding": novel_demo,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
        return 0
    print("=== Auto-Lab 4-Layer 'Undergrad' Agent Memory & Dreaming ===")
    print(
        f"Dreaming : {dream.raw_candidates} raw notes -> {dream.injected_notes_count} injected "
        f"({dream.injected_tokens}/{dream.token_budget} tok, {dream.quarantined_unverified_or_rote} poisoned/rote quarantined)"
    )
    print(f"Rusty SOP: {rusty_demo['concept_id']} after {rusty_demo['days_since_last_use']}d -> {rusty_demo['lean_verdict']['rule']}")
    print(
        f"Novel SOP: {novel_demo['assay_name']} -> analogy={novel_demo['nearest_concept']} "
        f"({novel_demo['analogy_sim_permille']} permille) -> {novel_demo['lean_verdict']['rule']}"
    )
    return 0


def _cmd_trust(args: argparse.Namespace) -> int:
    audit = audit_lean_sources()
    bin_path = find_autolab_lean_binary()
    results_file = REPO_ROOT / "benchmarks" / "results" / "trust_regime_results.json"
    study = json.loads(results_file.read_text(encoding="utf-8")) if results_file.exists() else None

    if args.json:
        print(
            json.dumps(
                {
                    "lean_audit": audit,
                    "binary_compiled": bin_path is not None,
                    "study": study["experiments"] if study else None,
                },
                indent=2,
            )
        )
        return 0 if audit["zero_sorry_verified"] else 1

    print("=== AutoLabLean Formal Trust Regime (leanprover/lean4:v4.36.0) ===")
    print(f"Files    : {audit['file_count']} Lean 4 modules")
    print(f"Theorems : {audit['theorem_count']} machine-checked theorems, {audit['guard_count']} #guard witnesses")
    print(f"Hygiene  : zero_sorry_verified={audit['zero_sorry_verified']} | native_binary={'READY' if bin_path else 'NOT_BUILT'}")
    if study:
        e1 = study["experiments"]["exp1_molecular_discovery"]["regimes"]
        e2 = study["experiments"]["exp2_protocol_synthesis"]["regimes"]
        e3 = study["experiments"]["exp3_fleet_scheduling"]["regimes"]
        e5 = study["experiments"]["exp5_rlvr_posttraining"]["regimes"]
        cpsat = e3.get("cpsat") or e3.get("lean_gated_cpsat", {})
        print("\nBenchmark Summary (see README 'What Is Real vs. Simulated' table):")
        print(
            f"  1. Real ESOL Held-Out logS    : MAE {e1['ungated']['prediction_mae']} -> {e1['lean_trust']['prediction_mae']}, "
            f"empirical 90% cov {e1['ungated']['empirical_coverage_pct']}% -> {e1['lean_trust']['empirical_coverage_pct']}% "
            f"(gate violations {e1['lean_trust']['boundary_violation_pct']}% by construction)"
        )
        print(
            f"  2. Protocol Synthesis (sim)   : independent stepbot sim faults "
            f"{e2['ungated_top1'].get('independent_sim_fault_pct', 'n/a')}% -> "
            f"{e2['lean_best_of_8_plus_guided_repair'].get('independent_sim_fault_pct', 0.0)}%, "
            f"Lean-certified completion {e2['ungated_top1']['valid_completion_pct']}% -> "
            f"{e2['lean_best_of_8_plus_guided_repair']['valid_completion_pct']}%"
        )
        print(
            f"  3. Fleet Scheduling (labshift): greedy {e3['ungated_greedy']['feasible_instances']} "
            f"({e3['ungated_greedy']['mean_makespan_min']}m) -> cpsat {cpsat.get('feasible_instances')} "
            f"({cpsat.get('mean_makespan_min')}m)"
        )
        print(
            f"  5. 6-Arm Bandit Sim (no LLM)  : verified arm mass {e5['soft_additive_reward_grpo']['true_verified_accuracy_pct']}% -> "
            f"{e5['lean_trust_gated_grpo']['true_verified_accuracy_pct']}% (GPU LLM RLVR: PENDING)"
        )
    ot_file = REPO_ROOT / "benchmarks" / "results" / "opentrons_library_rehearsal.json"
    if ot_file.exists():
        ot = json.loads(ot_file.read_text(encoding="utf-8"))
        s = ot.get("summary", {})
        print(
            f"  6. Real Opentrons Library     : {s.get('n_imported')}/{s.get('n_total')} imported, "
            f"{s.get('n_allowed')} allowed, {s.get('n_denied')} denied "
            f"(false-alarm rate on audited denies: {s.get('audited_false_alarm_rate_pct')}%)"
        )
    return 0 if audit["zero_sorry_verified"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
