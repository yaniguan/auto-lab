"""Unit tests for the Auto-Lab hub package, closed-loop simulator, catalog, and static site."""

from __future__ import annotations

import json
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
from autolab.cli import main as cli_main
from autolab.loop_demo import SCENARIOS, run_closed_loop_scenario


def test_seven_layers_ordered_top_down() -> None:
    assert len(LAYERS) == 7
    codes = [layer.code for layer in LAYERS]
    assert codes == ["L6", "L5", "L4", "L3", "L2", "L1", "L0"]
    assert len(CORE_REPO_NAMES) == 14
    assert len(COMPANION_REPOS) == 4


def test_closed_loop_scenarios_behave_honestly() -> None:
    ok = run_closed_loop_scenario("serial_dilution", strict_gate=True)
    assert ok["final_status"] == "EXECUTED_AND_WRITTEN_BACK"
    assert ok["steps"][-1]["verdict"] == "LEARNED"

    blocked = run_closed_loop_scenario("broken_tip_reuse", strict_gate=True)
    assert blocked["final_status"] == "BLOCKED_AT_L4_GATE"
    assert any(s["verdict"] == "BLOCK" and s["layer"] == "L4" for s in blocked["steps"])

    abstained = run_closed_loop_scenario("uncalibrated_molecule", strict_gate=True)
    assert abstained["final_status"] == "ABSTAINED_AT_L6"
    assert any(s["verdict"] == "ABSTAIN" and s["layer"] == "L6" for s in abstained["steps"])

    makeable = run_closed_loop_scenario("over_budget_analog", strict_gate=True)
    assert makeable["final_status"] == "EXECUTED_AND_WRITTEN_BACK"
    assert len(SCENARIOS) == 4


def test_catalog_and_issues_integrity_when_built() -> None:
    catalog_file = REPO_ROOT / "catalog" / "repos.json"
    issues_file = REPO_ROOT / "catalog" / "issues_index.json"
    site_data = REPO_ROOT / "site" / "assets" / "autolab-data.json"
    if not catalog_file.exists():
        return

    repos = load_catalog()
    assert len(repos) == 14
    seen = {r["repo"] for r in repos}
    assert seen == set(CORE_REPO_NAMES)

    for r in repos:
        for required_field in ("object", "data", "model", "training", "history", "unique_properties"):
            assert r.get(required_field), f"{r['repo']} missing {required_field}"
        assert get_repo(r["repo"])["url"].startswith("https://github.com/yaniguan/")

    issues = load_issues_index()
    assert issues["total_issues"] >= 280
    for name in CORE_REPO_NAMES:
        assert issues["repos"][name]["count"] >= 20

    assert site_data.exists()
    payload = json.loads(site_data.read_text(encoding="utf-8"))
    assert len(payload["repos"]) == 14
    assert len(payload["layers"]) == 7


def test_cli_commands_smoke(capsys) -> None:
    assert cli_main(["layers"]) == 0
    out = capsys.readouterr().out
    assert "[L6]" in out and "[L0]" in out

    assert cli_main(["loop", "--scenario", "broken_tip_reuse", "--json"]) == 0
    loop_json = json.loads(capsys.readouterr().out)
    assert loop_json["final_status"] == "BLOCKED_AT_L4_GATE"


def test_site_files_present() -> None:
    import re

    site = REPO_ROOT / "site"
    required = (
        "index.html",
        "styles.css",
        "shared.js",
        "scheme_icons.js",
        "home.js",
        ".nojekyll",
        "studio/index.html",
        "studio/studio.js",
        "repos/index.html",
        "repos/repos.js",
        "audit/index.html",
        "audit/audit.js",
    )
    for rel in required:
        assert (site / rel).exists(), f"Missing site/{rel}"

    cjk_re = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
    for p in [*site.rglob("*"), REPO_ROOT / "README.md", *(REPO_ROOT / "autolab").rglob("*.py")]:
        if p.is_file() and p.suffix in {".html", ".js", ".css", ".json", ".svg", ".md", ".py"}:
            if p.name == "test_autolab.py":
                continue
            text = p.read_text(encoding="utf-8")
            match = cjk_re.search(text)
            assert match is None, f"Found disallowed CJK character {match.group(0)!r} in {p}"


import io
import unittest
from contextlib import redirect_stdout


class _CapsysShim:
    def __init__(self, buf: io.StringIO) -> None:
        self._buf = buf

    def readouterr(self):
        val = self._buf.getvalue()
        self._buf.seek(0)
        self._buf.truncate(0)
        return type("Out", (), {"out": val, "err": ""})()


class TestAutoLabStdlib(unittest.TestCase):
    def test_all(self) -> None:
        test_seven_layers_ordered_top_down()
        test_closed_loop_scenarios_behave_honestly()
        test_catalog_and_issues_integrity_when_built()
        test_site_files_present()
        buf = io.StringIO()
        with redirect_stdout(buf):
            test_cli_commands_smoke(_CapsysShim(buf))

