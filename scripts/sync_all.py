#!/usr/bin/env python3
"""Clone, fetch, or inspect all 15 Auto-Lab repositories side-by-side."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autolab.catalog import CORE_REPO_NAMES, REPO_ROOT  # noqa: E402


def run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clone, fetch, or check status of all 15 Auto-Lab sibling repositories."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT.parent,
        help="Target workspace directory containing all sibling repos (default: parent of auto-lab)",
    )
    parser.add_argument(
        "--action",
        choices=("status", "fetch", "clone-or-fetch"),
        default="status",
        help="Action to run across all 15 repositories",
    )
    parser.add_argument(
        "--org",
        default="yaniguan",
        help="GitHub owner/organization (default: yaniguan)",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    failures = 0
    for name in CORE_REPO_NAMES:
        dest = root / name
        url = f"https://github.com/{args.org}/{name}.git"
        if args.action == "clone-or-fetch" and not (dest / ".git").exists():
            print(f"[clone] {url} -> {dest}")
            rc, out = run_git(["clone", url, str(dest)])
            if rc != 0:
                print(f"  ERROR: {out}", file=sys.stderr)
                failures += 1
                continue
        elif not (dest / ".git").exists():
            print(f"[missing] {name:22s} (run with --action clone-or-fetch)")
            failures += 1
            continue

        if args.action in ("fetch", "clone-or-fetch"):
            rc, out = run_git(["fetch", "--all", "--prune"], cwd=dest)
            if rc != 0:
                print(f"[fetch-err] {name}: {out}", file=sys.stderr)
                failures += 1
                continue

        _, branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=dest)
        _, sha = run_git(["rev-parse", "--short", "HEAD"], cwd=dest)
        _, dirty = run_git(["status", "--porcelain"], cwd=dest)
        state = "clean" if not dirty else f"dirty ({len(dirty.splitlines())} files)"
        print(f"[ok] {name:22s} | branch={branch:14s} | head={sha:8s} | {state}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
