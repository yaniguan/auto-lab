#!/usr/bin/env python3
"""Compile 15-repo profiles, issue audits, and closed-loop traces into catalog/, docs/, and site/."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from autolab.catalog import COMPANION_REPOS, CORE_REPO_NAMES, LAYERS  # noqa: E402
from autolab.loop_demo import SCENARIOS, run_closed_loop_scenario  # noqa: E402
from scripts.concise_specs import CONCISE_SPECS  # noqa: E402


def git_head_info(repo_dir: Path) -> tuple[str, str]:
    if not (repo_dir / ".git").exists():
        return "main", "-"
    rc, origin_main_sha = subprocess.getstatusoutput(
        f'git -C "{repo_dir}" rev-parse --verify --short=7 origin/main'
    )
    if rc == 0 and origin_main_sha.strip():
        return "main", origin_main_sha.strip()
    sha = subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "--short=7", "HEAD"], text=True
    ).strip()
    return "main", sha


def build_all(scratch_json_dir: Path, workspace_root: Path) -> None:
    catalog_dir = REPO_ROOT / "catalog"
    docs_dir = REPO_ROOT / "docs"
    site_assets_dir = REPO_ROOT / "site" / "assets"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    site_assets_dir.mkdir(parents=True, exist_ok=True)

    layer_lookup = {l.code: l for l in LAYERS}
    repos_out: list[dict[str, Any]] = []
    issues_repos: dict[str, Any] = {}
    manifest_entries: list[dict[str, Any]] = []
    total_issues = 0

    for name in CORE_REPO_NAMES:
        prof_path = scratch_json_dir / f"profile_{name}.json"
        iss_path = scratch_json_dir / f"issues_{name}.json"
        if not prof_path.exists():
            raise FileNotFoundError(f"Missing profile JSON: {prof_path}")
        if not iss_path.exists():
            raise FileNotFoundError(f"Missing issues JSON: {iss_path}")

        prof = json.loads(prof_path.read_text(encoding="utf-8"))
        issues_raw = json.loads(iss_path.read_text(encoding="utf-8"))
        if len(issues_raw) < 20:
            raise ValueError(f"{name} has only {len(issues_raw)} issues (< 20 required)")

        repo_dir = workspace_root / name
        branch, head_sha = git_head_info(repo_dir)
        prof["repo"] = name
        prof["url"] = f"https://github.com/yaniguan/{name}"
        layer_code = prof["layer"].split()[0].strip()
        prof["layer"] = layer_code
        prof["layer_name"] = layer_lookup[layer_code].name
        prof["commit_head"] = head_sha
        prof["issue_count"] = len(issues_raw)
        if name in CONCISE_SPECS:
            prof["concise"] = CONCISE_SPECS[name]
        repos_out.append(prof)

        compact_items = []
        for idx, it in enumerate(issues_raw, start=1):
            compact_items.append(
                {
                    "index": idx,
                    "number": it.get("number"),
                    "url": it.get("url"),
                    "title": it["title"],
                    "category": it.get("category", "bug"),
                    "severity": it.get("severity", "medium"),
                    "files": it.get("files", []),
                }
            )
        issues_repos[name] = {
            "count": len(compact_items),
            "items": compact_items,
        }
        total_issues += len(compact_items)

        manifest_entries.append(
            {
                "repo": name,
                "layer": layer_code,
                "git_url": f"https://github.com/yaniguan/{name}.git",
                "default_branch": branch,
                "head_sha": head_sha,
                "local_relative_path": f"../{name}",
                "profile_doc": "docs/ARCHITECTURE_AND_HISTORY.md",
                "issue_count": len(compact_items),
            }
        )

    # 1. Write catalog JSONs
    (catalog_dir / "repos.json").write_text(
        json.dumps({"version": "0.1.0", "repos": repos_out}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    issues_index_obj = {"total_issues": total_issues, "repos": issues_repos}
    (catalog_dir / "issues_index.json").write_text(
        json.dumps(issues_index_obj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (catalog_dir / "workspace.manifest.json").write_text(
        json.dumps({"hub": "auto-lab", "repositories": manifest_entries}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 2. Precompute closed-loop scenario combinations for static GitHub Pages
    scenarios_data: dict[str, Any] = {}
    for sc_id in SCENARIOS:
        for strict in (True, False):
            for recall in (True, False):
                key = f"{sc_id}__{1 if strict else 0}__{1 if recall else 0}"
                scenarios_data[key] = run_closed_loop_scenario(
                    sc_id, strict_gate=strict, use_episodic_recall=recall
                )

    site_payload = {
        "layers": [asdict(l) for l in LAYERS],
        "repos": repos_out,
        "companions": list(COMPANION_REPOS),
        "scenarios": scenarios_data,
        "issues": issues_index_obj,
    }
    (site_assets_dir / "autolab-data.json").write_text(
        json.dumps(site_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # 3. Generate docs/REPO_MATRIX.md
    md_lines = [
        "# Complete 15-Repository Technical Matrix",
        "",
        "Every repository in the Auto-Lab stack documents **Object**, **Data**, **Model**, **Training**, **History**, and **Unique Properties** in both its `README.md` and `docs/ARCHITECTURE_AND_HISTORY.md`.",
        "",
        "| Layer | Repository | Object | Data | Model | Training | Unique Property |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in repos_out:
        prop0 = (r.get("unique_properties") or ["-"])[0]
        md_lines.append(
            f"| `{r['layer']}` | [{r['repo']}]({r['url']}) | { _one_line(r['object']) } | "
            f"{ _one_line(r['data']) } | { _one_line(r['model']) } | { _one_line(r['training']) } | { _one_line(prop0) } |"
        )
    md_lines.append("")
    for r in repos_out:
        md_lines.extend(
            [
                f"## `{r['layer']}` · [{r['repo']}]({r['url']})",
                "",
                f"- **Tagline**: {r['tagline']}",
                f"- **Object**: {r['object']}",
                f"- **Data**: {r['data']}",
                f"- **Model**: {r['model']}",
                f"- **Training**: {r['training']}",
                f"- **History**: {r['history']}",
                "- **Unique Properties**:",
                *[f"  - {p}" for p in r.get("unique_properties", [])],
                f"- **Deep Profile**: [`{r['repo']}/docs/ARCHITECTURE_AND_HISTORY.md`]({r['url']}/blob/main/docs/ARCHITECTURE_AND_HISTORY.md)",
                "",
            ]
        )
    (docs_dir / "REPO_MATRIX.md").write_text("\n".join(md_lines), encoding="utf-8")

    # 4. Generate docs/ISSUES_AUDIT_INDEX.md
    audit_lines = [
        "# Deep Codebase Audit & GitHub Issues Index",
        "",
        f"Total code-grounded issues filed across all 15 Auto-Lab repositories: **{total_issues}** (`>= 10` per repository).",
        "",
        "| Layer | Repository | Tracked Audit Issues | Live Tracker |",
        "|---|---|---:|---|",
    ]
    for r in repos_out:
        name = r["repo"]
        cnt = issues_repos[name]["count"]
        audit_lines.append(
            f"| `{r['layer']}` | [{name}]({r['url']}) | **{cnt}** | [{name}/issues]({r['url']}/issues) |"
        )
    audit_lines.append("")

    for r in repos_out:
        name = r["repo"]
        audit_lines.extend(
            [
                f"## [{name}]({r['url']}/issues) ({issues_repos[name]['count']} Issues)",
                "",
                "| # | Category | Severity | Issue Title | Grounded Files |",
                "|---:|---|---|---|---|",
            ]
        )
        for it in issues_repos[name]["items"]:
            num_cell = (
                f"[#{it['number']}]({it['url']})"
                if it.get("number") and it.get("url")
                else f"{it['index']}"
            )
            files_str = ", ".join(f"`{f}`" for f in it.get("files", []))
            audit_lines.append(
                f"| {num_cell} | `{it['category']}` | **{it['severity']}** | { _escape_pipe(it['title']) } | { _escape_pipe(files_str) } |"
            )
        audit_lines.append("")
    (docs_dir / "ISSUES_AUDIT_INDEX.md").write_text("\n".join(audit_lines), encoding="utf-8")
    print(f"Built catalog, docs, and site data for {len(repos_out)} repos ({total_issues} total issues).")


def _one_line(text: str, limit: int = 135) -> str:
    clean = " ".join(str(text).split()).replace("|", "\\|")
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def _escape_pipe(text: str) -> str:
    return str(text).replace("|", "\\|")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch-dir", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, default=REPO_ROOT.parent)
    args = parser.parse_args()
    build_all(args.scratch_dir.resolve(), args.workspace_root.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
