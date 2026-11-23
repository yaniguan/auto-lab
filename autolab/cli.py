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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
