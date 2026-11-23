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
from autolab.trust_regime import (
    LeanBatchKernel,
    audit_lean_sources,
    format_rehearsal_tsv,
    py_check_conformal,
    py_check_rehearsal,
)


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

    assert cli_main(["trust", "--json"]) == 0
    trust_json = json.loads(capsys.readouterr().out)
    assert trust_json["lean_audit"]["zero_sorry_verified"] is True
    assert trust_json["lean_audit"]["theorem_count"] >= 35


def test_lean_trust_regime_audit_and_parity() -> None:
    audit = audit_lean_sources()
    assert audit["zero_sorry_verified"] is True, f"Violations: {audit['violations']}"
    assert audit["file_count"] == 10
    assert audit["theorem_count"] >= 38
    assert audit["guard_count"] >= 16

    # Check empirical study results JSON
    study_path = REPO_ROOT / "benchmarks" / "results" / "trust_regime_results.json"
    assert study_path.exists()
    study = json.loads(study_path.read_text(encoding="utf-8"))
    assert study["experiments"]["exp1_molecular_discovery"]["regimes"]["lean_trust"]["boundary_violation_pct"] == 0.0
    assert study["experiments"]["exp2_protocol_synthesis"]["regimes"]["lean_best_of_8_plus_guided_repair"]["hardware_fault_pct"] == 0.0

    # When `autolab-lean` is compiled locally or in CI, verify exact kernel parity!
    kernel = LeanBatchKernel()
    if kernel.available:
        v_ok, v_ood, v_small = kernel.eval_lines(
            [
                "CONFORMAL\t180\t100\t410\t758\t-2410\t630\t-15000\t1750",
                "CONFORMAL\t180\t100\t1380\t758\t-2410\t630\t-15000\t1750",
                "CONFORMAL\t5\t100\t410\t758\t-2410\t630\t-15000\t1750",
            ]
        )
        assert v_ok.allowed is py_check_conformal(180, 100, 410, 758, -2410, 630).allowed is True
        assert v_ood.allowed is py_check_conformal(180, 100, 1380, 758, -2410, 630).allowed is False
        assert v_small.allowed is py_check_conformal(5, 100, 410, 758, -2410, 630).allowed is False

        wells = [
            {"wellId": 1, "vol": 2500, "cap": 3000, "deadVol": 50, "soluteAmt": 0, "hasBuffer": True, "hasSample": False, "frozen": False, "sealed": False},
            {"wellId": 2, "vol": 1500, "cap": 3000, "deadVol": 50, "soluteAmt": 1500, "hasBuffer": False, "hasSample": True, "frozen": False, "sealed": False},
            {"wellId": 3, "vol": 0, "cap": 3000, "deadVol": 50, "soluteAmt": 0, "hasBuffer": False, "hasSample": False, "frozen": False, "sealed": False},
        ]
        good_steps = [("pick",), ("xfer", 1, 3, 1000), ("drop",), ("pick",), ("xfer", 2, 3, 500), ("seal", 3), ("inc", 3, 95, 300), ("drop",)]
        bad_steps = [("pick",), ("xfer", 2, 3, 500), ("xfer", 1, 3, 500), ("drop",)]
        r_good, r_bad = kernel.eval_lines(
            [
                format_rehearsal_tsv(200, 3000, 101, [], wells, good_steps),
                format_rehearsal_tsv(200, 3000, 102, [], wells, bad_steps),
            ]
        )
        assert r_good.allowed is py_check_rehearsal(200, 3000, 101, [], wells, good_steps).allowed is True
        assert r_bad.allowed is py_check_rehearsal(200, 3000, 102, [], wells, bad_steps).allowed is False
        assert r_bad.rule == "no_tip_cross_contamination"


def test_site_files_present() -> None:
    import re

    site = REPO_ROOT / "site"
    required = (
        "index.html",
        "styles.css",
        "shared.js",
        "scheme_icons.js",
        "repo_stories.js",
        "home.js",
        ".nojekyll",
        "trust/index.html",
        "trust/trust.js",
        "assets/trust-regime-data.json",
        "studio/index.html",
        "studio/studio.js",
        "repos/index.html",
        "repos/repos.js",
        "audit/index.html",
        "audit/audit.js",
    )
    for rel in required:
        assert (site / rel).exists(), f"Missing site/{rel}"

    stories_text = (site / "repo_stories.js").read_text(encoding="utf-8")
    for repo_name in CORE_REPO_NAMES:
        assert f"'{repo_name}':" in stories_text, f"Missing story entry for {repo_name}"

    repos_js = (site / "repos" / "repos.js").read_text(encoding="utf-8")
    assert "1 · Object" not in repos_js and "bento-6" not in repos_js

    cjk_re = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
    scan_paths = [
        *site.rglob("*"),
        REPO_ROOT / "README.md",
        *(REPO_ROOT / "autolab").rglob("*.py"),
        *(REPO_ROOT / "benchmarks").rglob("*.py"),
        *(REPO_ROOT / "docs").rglob("*.md"),
        *[p for p in (REPO_ROOT / "lean").rglob("*") if ".lake" not in p.parts],
    ]
    for p in scan_paths:
        if p.is_file() and p.suffix in {".html", ".js", ".css", ".json", ".svg", ".md", ".py", ".lean"}:
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
        test_lean_trust_regime_audit_and_parity()
        test_site_files_present()
        buf = io.StringIO()
        with redirect_stdout(buf):
            test_cli_commands_smoke(_CapsysShim(buf))

