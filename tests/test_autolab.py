"""Unit tests for the Auto-Lab hub package, closed-loop simulator, catalog, and static site."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pytest

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
    TrustVerdict,
    audit_lean_sources,
    format_rehearsal_tsv,
    py_check_conformal,
    py_check_rehearsal,
)


def _skip_or_fail(reason: str, require_env: str) -> None:
    """Skip the test, or fail it when `require_env=1` says this check must run (set in CI)."""
    import os

    __tracebackhide__ = True  # report the calling test's line, not this helper's
    if os.environ.get(require_env) == "1":
        pytest.fail(f"{reason} ({require_env}=1)", pytrace=False)
    pytest.skip(reason)


def test_seven_layers_ordered_top_down() -> None:
    assert len(LAYERS) == 7
    codes = [layer.code for layer in LAYERS]
    assert codes == ["L6", "L5", "L4", "L3", "L2", "L1", "L0"]
    assert len(CORE_REPO_NAMES) == 15
    assert "lab-attrib" in CORE_REPO_NAMES
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
    assert any(s["repo"] == "lab-attrib" and s["verdict"] == "PASS" for s in makeable["steps"])

    ghost = run_closed_loop_scenario("precursor_ghost_peak", strict_gate=True)
    assert ghost["final_status"] == "QUARANTINED_AT_L4_ATTRIB"
    assert any(s["repo"] == "lab-attrib" and s["verdict"] == "BLOCK" for s in ghost["steps"])

    assert len(SCENARIOS) == 5


def test_catalog_and_issues_integrity_when_built() -> None:
    import re

    catalog_file = REPO_ROOT / "catalog" / "repos.json"
    manifest_file = REPO_ROOT / "catalog" / "workspace.manifest.json"
    site_data = REPO_ROOT / "site" / "assets" / "autolab-data.json"
    assert catalog_file.exists()

    repos = load_catalog()
    assert len(repos) == 15
    seen = {r["repo"] for r in repos}
    assert seen == set(CORE_REPO_NAMES)

    assert manifest_file.exists()
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest.get("hub") == "auto-lab"
    manifest_repos = manifest.get("repositories", [])
    assert [m["repo"] for m in manifest_repos] == list(CORE_REPO_NAMES)
    manifest_by_repo = {m["repo"]: m for m in manifest_repos}

    for r in repos:
        for required_field in ("object", "data", "model", "training", "history", "unique_properties"):
            assert r.get(required_field), f"{r['repo']} missing {required_field}"
        assert get_repo(r["repo"])["url"].startswith("https://github.com/yaniguan/")
        m_entry = manifest_by_repo[r["repo"]]
        assert m_entry["default_branch"] == "main"
        assert re.fullmatch(r"[0-9a-f]{7}", m_entry["head_sha"]), f"Invalid head_sha for {r['repo']}: {m_entry['head_sha']}"
        assert r["commit_head"] == m_entry["head_sha"], f"SHA drift for {r['repo']}: {r['commit_head']} vs {m_entry['head_sha']}"

    issues = load_issues_index()
    assert issues["total_issues"] >= 481
    assert issues.get("round1_issues") == 322
    assert issues.get("round2_issues") >= 95
    assert issues.get("round3_issues") >= 64
    assert issues.get("closed_issues") >= 478
    assert issues.get("open_issues") == 3
    assert issues.get("open_pending_gpu_issues") == [
        "labfill#35",
        "labbench-posttrain#49",
        "labbench-posttrain#18",
    ]
    for name in CORE_REPO_NAMES:
        if name == "lab-attrib":
            assert issues["repos"][name]["count"] >= 14
        else:
            assert issues["repos"][name]["count"] >= 32
    assert issues["repos"]["assayfold"]["count"] >= 4

    assert site_data.exists()
    payload = json.loads(site_data.read_text(encoding="utf-8"))
    assert len(payload["repos"]) == 15
    assert payload["repos"] == repos
    assert payload["companions"] == list(COMPANION_REPOS)
    assert len(payload["layers"]) == 7
    assert payload["issues"]["total_issues"] == issues["total_issues"]
    assert payload["issues"]["repos"]["lab-attrib"]["count"] >= 10


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
    assert trust_json["lean_audit"]["theorem_count"] >= 50

    assert cli_main(["memory", "--json"]) == 0
    mem_json = json.loads(capsys.readouterr().out)
    assert mem_json["dream_consolidation"]["quarantined_unverified_or_rote"] >= 1
    assert mem_json["rusty_skill_recovery"]["lean_verdict"]["allowed"] is True
    assert mem_json["novel_assay_onboarding"]["lean_verdict"]["allowed"] is True


def test_lean_trust_regime_audit_and_parity() -> None:
    audit = audit_lean_sources()
    assert audit["zero_sorry_verified"] is True, f"Violations: {audit['violations']}"
    assert audit["file_count"] == 12
    assert audit["theorem_count"] >= 50
    assert audit["guard_count"] >= 27

    # Check empirical study results JSON
    study_path = REPO_ROOT / "benchmarks" / "results" / "trust_regime_results.json"
    assert study_path.exists()
    study = json.loads(study_path.read_text(encoding="utf-8"))
    assert study["experiments"]["exp1_molecular_discovery"]["regimes"]["lean_trust"]["boundary_violation_pct"] == 0.0
    assert study["experiments"]["exp2_protocol_synthesis"]["regimes"]["lean_best_of_8_plus_guided_repair"]["hardware_fault_pct"] == 0.0

    novel_path = REPO_ROOT / "benchmarks" / "results" / "novel_directions_results.json"
    assert novel_path.exists()
    novel = json.loads(novel_path.read_text(encoding="utf-8"))
    assert novel["directions"]["d1_epistemic_attribution"]["comparison"]["lean_attribution_sdl"]["false_discovery_rate_pct"] == 0.0
    assert novel["directions"]["d2_stepped_frontier"]["comparison"]["undirected_shell_probes"]["uncalibrated_production_runs"] == 0.0
    assert novel["directions"]["d3_lean_mcp"]["comparison"]["proof_carrying_lean_mcp"]["unsafe_or_replay_executions"] == 0
    assert novel["directions"]["d4_adversarial_coevolution"]["generations"]["gen2_autolablean_formal"]["saboteur_evasion_pct"] == 0.0

    # When `autolab-lean` is compiled locally or in CI, verify exact kernel parity!
    kernel = LeanBatchKernel()
    if not kernel.available:
        _skip_or_fail("autolab-lean binary not built (run `lake build` in lean/)", "AUTOLAB_REQUIRE_LEAN")

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

    # Verify NovelDirections.lean batch commands (ATTRIB, FRONTIER, MCP)
    a_neg, a_xrd, f_ok, f_deep, m_ok, m_stale = kernel.eval_lines(
        [
            "ATTRIB\t1\t1\t1\t1\t1\t1\t80\t150\t40\t120\t0",
            "ATTRIB\t1\t1\t1\t1\t1\t1\t80\t150\t310\t120\t1",
            "FRONTIER\t1\t890\t750\t250\t350\t80\t100\t1\t0",
            "FRONTIER\t1\t1200\t750\t250\t350\t80\t100\t1\t0",
            "MCP\t42\t42\t1\t0\t0",
            "MCP\t41\t42\t1\t0\t0",
        ]
    )
    assert a_neg.rule == "CERTIFIED_NEGATIVE" and a_neg.extra == "1"
    assert a_xrd.rule == "AMBIGUOUS_CHARACTERIZATION" and a_xrd.extra == "0"
    assert f_ok.allowed is True
    assert f_deep.allowed is False and f_deep.rule == "within_stepping_stone_shell"
    assert m_ok.allowed is True
    assert m_stale.allowed is False and m_stale.rule == "mcp_epoch_freshness"

    ms_ok, ms_rusty_deny, mn_ok, mn_blind_deny = kernel.eval_lines(
        [
            "MEM_SKILL\t120\t30\t2\t2\t1\t1",
            "MEM_SKILL\t120\t30\t2\t2\t0\t1",
            "MEM_NOVEL\t0\t750\t600\t1\t1\t1",
            "MEM_NOVEL\t0\t750\t600\t0\t1\t1",
        ]
    )
    assert ms_ok.allowed is True
    assert ms_rusty_deny.allowed is False and ms_rusty_deny.rule == "rusty_skill_requires_bottom_trace"
    assert mn_ok.allowed is True
    assert mn_blind_deny.allowed is False and mn_blind_deny.rule == "novel_requires_bottom_reasoning_trace"


# Probe inputs from issue #2. The old batch parser read bad numbers as 0 and dropped steps it
# could not parse, so most of these were allowed.
_PROBE_WELLS = [
    {"wellId": 1, "vol": 2500, "cap": 3000, "deadVol": 50, "soluteAmt": 0, "hasBuffer": True, "hasSample": False, "frozen": False, "sealed": False},
    {"wellId": 2, "vol": 1500, "cap": 3000, "deadVol": 50, "soluteAmt": 1500, "hasBuffer": False, "hasSample": True, "frozen": False, "sealed": False},
    {"wellId": 3, "vol": 0, "cap": 3000, "deadVol": 50, "soluteAmt": 0, "hasBuffer": False, "hasSample": False, "frozen": False, "sealed": False},
]
_CONFORMAL_PROBES = [  # (kNN distance, expected rule)
    (1384, "knn_trust_boundary"),
    (1384.0, "malformed_input"),
    ("1,384", "malformed_input"),
]
_REHEARSAL_PROBES = [  # (wells, steps, expected rule)
    (_PROBE_WELLS, [("pick",), ("xfer", 1, 3), ("drop",)], "malformed_input"),
    (_PROBE_WELLS, [("pick",), ("aspirate", 1, 99999), ("drop",)], "malformed_input"),
    (_PROBE_WELLS, [("pick",), ("xfer", 1, 3, 500), ("inc", 3, 95, 300), ("drop",)], "high_temp_requires_seal"),
    (_PROBE_WELLS, [("pick",), ("xfer", 1, 3, 500), ("incubate", 3, 95, 300), ("drop",)], "malformed_input"),
    ([{**_PROBE_WELLS[0], "vol": -5}, *_PROBE_WELLS[1:]], [("pick",), ("drop",)], "malformed_input"),
    # Well 1 is over capacity and listed twice: `initDeckOK` checks well IDs before capacity.
    ([{**_PROBE_WELLS[0], "vol": 3500}, *_PROBE_WELLS], [("pick",), ("drop",)], "unique_well_ids"),
    (_PROBE_WELLS, [], "valid"),  # zero steps, so the TSV line ends with an empty field
]
_PROBE_RULES = [probe[-1] for probe in _CONFORMAL_PROBES + _REHEARSAL_PROBES]
_SQL_PROBES = ["SQL\t1\t1\t1\t1\tyes\t0\t0\t1\t1\t1", "SQL\t1\t1\t1\t1\t0\ttwo\t0\t1\t1\t1"]


def _conformal_args(dist: object) -> tuple[object, ...]:
    return (180, 100, dist, 758, -2410, 630, -15000, 1750)


def _conformal_tsv(dist: object) -> str:
    return "\t".join(str(x) for x in ("CONFORMAL", *_conformal_args(dist)))


def _probe_py_verdicts() -> list[TrustVerdict]:
    verdicts = [py_check_conformal(*_conformal_args(dist)) for dist, _ in _CONFORMAL_PROBES]
    verdicts += [py_check_rehearsal(200, 3000, 101, [], wells, steps) for wells, steps, _ in _REHEARSAL_PROBES]
    return verdicts


def _lean_kernel_or_skip() -> LeanBatchKernel:
    __tracebackhide__ = True
    kernel = LeanBatchKernel()
    if not kernel.available:
        _skip_or_fail("autolab-lean binary not built (run `lake build` in lean/)", "AUTOLAB_REQUIRE_LEAN")
    return kernel


def test_python_mirror_denies_malformed_input() -> None:
    verdicts = _probe_py_verdicts()
    assert [(v.allowed, v.rule) for v in verdicts] == [(rule == "valid", rule) for rule in _PROBE_RULES]
    # Input is checked before any rule, as in the Lean parser, so the rule names match.
    late_typo = py_check_rehearsal(200, 3000, 101, [101], _PROBE_WELLS, [("pick",), ("drop",), ("spin", 3)])
    assert late_typo.rule == "malformed_input"


def test_lean_batch_tsv_denies_malformed_input() -> None:
    kernel = _lean_kernel_or_skip()
    lines = [_conformal_tsv(dist) for dist, _ in _CONFORMAL_PROBES]
    lines += [format_rehearsal_tsv(200, 3000, 101, [], wells, steps) for wells, steps, _ in _REHEARSAL_PROBES]
    lean = kernel.eval_lines(lines)
    assert [(v.allowed, v.rule) for v in lean] == [(rule == "valid", rule) for rule in _PROBE_RULES]
    assert [(v.allowed, v.rule, v.extra) for v in lean] == [(v.allowed, v.rule, v.extra) for v in _probe_py_verdicts()]
    assert lean[-1].detail == "accepted by the compiled Lean checker"
    assert [v.rule for v in kernel.eval_lines(_SQL_PROBES)] == ["malformed_input"] * len(_SQL_PROBES)
    # Only the line ending is stripped, so a CRLF line still parses.
    assert kernel.eval_lines([_conformal_tsv(410) + "\r"])[0].allowed is True


def _random_rehearsal_case(rng: random.Random) -> tuple:
    """A small random deck and protocol. About one case in five gets one malformed field."""
    ids = rng.sample(range(1, 6), rng.randint(1, 4))
    if rng.random() < 0.1:
        ids.append(ids[0])
    wells = []
    for wid in ids:
        cap = rng.choice([1000, 3000])
        wells.append(
            {"wellId": wid, "vol": rng.randint(0, cap + 100), "cap": cap, "deadVol": rng.choice([0, 50]),
             "soluteAmt": rng.choice([0, rng.randint(1, 1500)]), "hasBuffer": rng.random() < 0.5,
             "hasSample": rng.random() < 0.5, "frozen": rng.random() < 0.15, "sealed": rng.random() < 0.15}
        )
    wids = ids + [9]  # well 9 is never on the deck
    steps: list[tuple] = [("pick",)] if rng.random() < 0.8 else []
    for _ in range(rng.randint(0, 6)):
        op = rng.choice(["pick", "drop", "xfer", "xfer", "mix", "inc", "seal", "thaw"])
        if op in ("pick", "drop"):
            steps.append((op,))
        elif op == "xfer":
            steps.append((op, rng.choice(wids), rng.choice(wids), rng.choice([100, 500, 1000, 2900])))
        elif op == "mix":
            steps.append((op, rng.choice(wids), rng.choice([100, 500, 1000]), rng.randint(0, 3)))
        elif op == "inc":
            steps.append((op, rng.choice(wids), rng.choice([2, 37, 85, 99]), rng.choice([0, 300])))
        else:
            steps.append((op, rng.choice(wids)))
    if rng.random() < 0.8:
        steps.append(("drop",))
    pip = rng.choice([(200, 3000)] * 18 + [(0, 3000), (500, 100)])
    proto_hash = rng.randint(1, 40)
    failed = [rng.randint(1, 40) for _ in range(rng.randint(0, 2))]
    if rng.random() < 0.2:
        kind = rng.randrange(5)
        bad = rng.choice([-5, 1384.0, True])
        if kind == 0 and steps:
            i = rng.randrange(len(steps))
            steps[i] = (rng.choice(["incubate", "aspirate", "INC"]), *steps[i][1:])
        elif kind == 1 and steps:
            i = rng.randrange(len(steps))
            steps[i] = steps[i][:-1] if len(steps[i]) > 1 else (*steps[i], 1)
        elif kind == 2:
            rng.choice(wells)[rng.choice(["wellId", "vol", "cap", "deadVol", "soluteAmt"])] = bad
        elif kind == 3:
            pip = (bad, pip[1])
        else:
            failed.append(bad)
    return (*pip, proto_hash, failed, wells, steps)


def test_lean_and_python_rehearsal_agree_on_random_protocols() -> None:
    kernel = _lean_kernel_or_skip()
    rng = random.Random(2026)
    cases = [_random_rehearsal_case(rng) for _ in range(10_000)]
    py = [py_check_rehearsal(*case) for case in cases]
    lean = kernel.eval_lines([format_rehearsal_tsv(*case) for case in cases])
    verdict_mismatches = sum(p.allowed != q.allowed for p, q in zip(py, lean))
    rule_mismatches = sum(p.rule != q.rule for p, q in zip(py, lean))
    volume_mismatches = sum(p.extra != q.extra for p, q in zip(py, lean))
    assert (verdict_mismatches, rule_mismatches, volume_mismatches) == (0, 0, 0)
    # The cases reach allowed runs, malformed input and both initial-deck checks whose order now matches.
    rules = Counter(v.rule for v in py)
    for rule in ("valid", "malformed_input", "unique_well_ids", "initial_state_within_capacity"):
        assert rules[rule] >= 100, rules


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
        "assets/novel-directions-data.json",
        "assets/agent-memory-data.json",
        "assets/autolab_preprint.pdf",
        "assets/lab_attrib_preprint.pdf",
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

    audit_html = (site / "audit" / "index.html").read_text(encoding="utf-8")
    audit_js = (site / "audit" / "audit.js").read_text(encoding="utf-8")
    assert 'id="filter-round"' in audit_html and "?v=13" in audit_html
    assert "filter-round" in audit_js and "populateDynamicCategoryFilter" in audit_js

    cjk_re = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
    scan_paths = [
        *site.rglob("*"),
        *(REPO_ROOT / "catalog").rglob("*.json"),
        REPO_ROOT / "README.md",
        *(REPO_ROOT / "autolab").rglob("*.py"),
        *(REPO_ROOT / "benchmarks").rglob("*.py"),
        *(REPO_ROOT / "benchmarks").rglob("*.json"),
        *(REPO_ROOT / "docs").rglob("*.md"),
        *(REPO_ROOT / "paper").rglob("*.tex"),
        *(REPO_ROOT / "paper").rglob("*.sty"),
        *(REPO_ROOT / "paper").rglob("*.py"),
        *[p for p in (REPO_ROOT / "lean").rglob("*") if ".lake" not in p.parts],
    ]
    for p in scan_paths:
        if p.is_file() and p.suffix in {".html", ".js", ".css", ".json", ".svg", ".md", ".py", ".lean"}:
            if p.name == "test_autolab.py":
                continue
            text = p.read_text(encoding="utf-8")
            match = cjk_re.search(text)
            assert match is None, f"Found disallowed CJK character {match.group(0)!r} in {p}"


def test_cross_repo_lean_mcp_and_lab_attrib_integration() -> None:
    """When sibling repositories are checked out locally, verify live wire interoperability:
    1) `lab-verify` mints a `lean-mcp/v1` token over `stepbot`'s compiled Opentrons Python script,
       `StepbotMcpExecutor` executes it, advances `current_deck_epoch` 1 -> 2, and blocks replay/tampering.
    2) `lab-attrib` certifies clean negative runs and quarantines precursor-overlapped runs.
    """
    import sys

    scratch_root = REPO_ROOT.parent
    stepbot_src = scratch_root / "stepbot" / "src"
    verify_src = scratch_root / "lab-verify" / "src"
    attrib_src = scratch_root / "lab-attrib" / "src"

    missing = [src.parent.name for src in (stepbot_src, verify_src, attrib_src) if not src.exists()]
    if missing:
        _skip_or_fail(f"sibling repos not checked out next to the hub: {', '.join(missing)}", "AUTOLAB_REQUIRE_SIBLINGS")

    for p in (str(stepbot_src), str(verify_src)):
        if p not in sys.path:
            sys.path.insert(0, p)

    from lab_verify.mcp_gate import LeanMcpGate
    from stepbot.mcp_runtime import (
        McpSecurityViolation,
        StepbotMcpExecutor,
        compile_with_mcp_envelope,
    )

    plate_yaml = scratch_root / "stepbot" / "examples" / "plate_fill.yaml"
    bundle = compile_with_mcp_envelope(plate_yaml, secret_key="cross-repo-test-key", deck_epoch=1)

    # Direction A: stepbot-minted envelope verified by lab-verify's stateful gate!
    gate_a = LeanMcpGate(secret_key="cross-repo-test-key", initial_deck_epoch=1, check_lean_kernel=False)
    verdict_a = gate_a.verify(bundle.envelope, actual_protocol=bundle.python_code, mutates_deck_state=True)
    assert verdict_a.passed is True
    assert gate_a.current_deck_epoch == 2

    # Direction B: lab-verify-minted envelope dispatched in stepbot's executor!
    gate_b = LeanMcpGate(secret_key="cross-repo-test-key", initial_deck_epoch=1, check_lean_kernel=False)
    minted = gate_b.mint(
        bundle.python_code,
        lean_proof_valid=True,
        envelope_bounds=bundle.envelope["envelope_bounds"],
    )
    verdict_b = gate_b.verify(minted, actual_protocol=bundle.python_code, mutates_deck_state=True)
    assert verdict_b.passed is True
    assert gate_b.current_deck_epoch == 2

    executor = StepbotMcpExecutor(secret_key="cross-repo-test-key", current_deck_epoch=1, use_mock=True)
    receipt = executor.dispatch(bundle.python_code, minted.to_dict(), simulate=True)
    assert receipt["ok"] is True
    assert receipt["executed_epoch"] == 1
    assert executor.current_deck_epoch == 2

    # Replay of the consumed token must fail immediately with McpSecurityViolation
    replayed = False
    try:
        executor.dispatch(bundle.python_code, minted.to_dict(), simulate=True)
    except McpSecurityViolation as exc:
        replayed = exc.rule in {"mcp_epoch_freshness", "mcp_nonce_single_use"}
    assert replayed is True

    if str(attrib_src) not in sys.path:
        sys.path.insert(0, str(attrib_src))

    from lab_attrib.blame import (
        AssayTelemetry,
        AttributionOutcome,
        attribute_assay_outcome,
    )

    clean_neg = AssayTelemetry(
        dispense_error_permille=12,
        aspiration_clean=True,
        incubation_window_clean=True,
        seal_intact=True,
        positive_control_passed=True,
        blank_uncontaminated=True,
        detector_calibrated=True,
        precursor_overlap_permille=35,
        spectral_residual_permille=42,
        snr_tenths=85,
        target_signal_present=False,
    )
    ghost_overlap = AssayTelemetry(
        dispense_error_permille=12,
        aspiration_clean=True,
        incubation_window_clean=True,
        seal_intact=True,
        positive_control_passed=True,
        blank_uncontaminated=True,
        detector_calibrated=True,
        precursor_overlap_permille=340,
        spectral_residual_permille=42,
        snr_tenths=85,
        target_signal_present=True,
    )
    assert attribute_assay_outcome(clean_neg) is AttributionOutcome.CERTIFIED_NEGATIVE
    assert attribute_assay_outcome(ghost_overlap) is AttributionOutcome.AMBIGUOUS_CHARACTERIZATION


def test_fifteen_repo_full_wire_pipeline() -> None:
    """Verify the 15-repository `autolab-wire/v1` end-to-end integration pipeline.

    Checks the committed `benchmarks/results/fifteen_repo_wire_results.json` report on
    every checkout (including hub-only CI), and executes all 6 live 15-repository wire
    scenarios when all sibling `<repo>/autolab_wire.py` modules are present locally.
    """
    import importlib.util
    import sys

    results_path = REPO_ROOT / "benchmarks" / "results" / "fifteen_repo_wire_results.json"
    assert results_path.exists(), f"Missing {results_path}"
    recorded = json.loads(results_path.read_text(encoding="utf-8"))
    assert recorded["schema_version"] == "autolab-wire/v1"
    assert recorded["repo_count"] == 15
    assert set(recorded["repos"]) == set(CORE_REPO_NAMES)
    assert recorded["scenario_count"] == 6
    assert recorded["all_passed"] is True
    rec_s1 = recorded["scenarios"]["1_full_happy_path_and_round2_recalibration"]
    assert rec_s1["distance_source"] == "fitted_esol_model"
    assert rec_s1["decide_model_encoding"] == "rdkit_2d_morgan"
    assert rec_s1["decide_surrogate"] == "frontier_ensemble"
    assert rec_s1["ask_why_stance_calibrated"] is True
    assert rec_s1["ask_why_unrelated_abstained"] is True
    assert rec_s1["atlas_equivalent_url_variants_blocked"] >= 4
    assert rec_s1["atlas_missing_spdx_blocked"] is True
    assert rec_s1["buy_or_make_oos_and_unpriced_blocked"] is True
    assert rec_s1["attribution_defaulted_fields"] == []
    assert rec_s1["round1_effective_n_calib"] == 169 and rec_s1["round2_effective_n_calib"] == 170
    assert recorded["scenarios"]["4_l1_lean_mcp_stale_epoch_block"]["dev_secret_rejected"] is True
    assert (
        recorded["scenarios"]["5_l4_postrun_precursor_ghost_peak_quarantine"][
            "missing_evidence_quarantine_verified"
        ]
        is True
    )
    assert recorded["scenarios"]["6_l3_splitguard_canary_block"]["strict_allowlist_enforced"] is True

    wire_script = REPO_ROOT / "benchmarks" / "fifteen_repo_wire_check.py"
    spec = importlib.util.spec_from_file_location("_autolab_fifteen_repo_wire_check", wire_script)
    assert spec is not None and spec.loader is not None
    wire_check = importlib.util.module_from_spec(spec)
    sys.modules["_autolab_fifteen_repo_wire_check"] = wire_check
    spec.loader.exec_module(wire_check)

    missing = [repo for repo, path in wire_check.sibling_wire_paths().items() if not path.is_file()]
    if missing:
        _skip_or_fail(
            f"autolab_wire.py missing in {len(missing)} sibling repos: {', '.join(missing)}", "AUTOLAB_REQUIRE_SIBLINGS"
        )
    for req_pkg in ("sklearn", "rdkit", "torch"):
        if importlib.util.find_spec(req_pkg) is None:
            _skip_or_fail(
                f"sibling wire runtime package {req_pkg!r} is not installed in this environment",
                "AUTOLAB_REQUIRE_SIBLINGS",
            )

    live = wire_check.run_all_six_scenarios()
    assert live["all_passed"] is True
    assert live["scenario_count"] == 6
    s1 = live["scenarios"]["1_full_happy_path_and_round2_recalibration"]
    assert s1["trace_len"] == 15
    assert s1["bottom_reasoning_traces_len"] == 15
    assert s1["executed_epoch"] == 1 and s1["next_deck_epoch"] == 2
    assert s1["attribution_outcome"] == "CERTIFIED_POSITIVE"
    assert s1["gated_reward"] == 1.0 and s1["admitted_to_sft_rlvr"] is True
    assert s1["round1_effective_n_calib"] == 169 and s1["round2_effective_n_calib"] == 170
    assert s1["round1_effective_threshold"] == pytest.approx(0.675015, abs=1e-5)
    assert s1["round2_effective_threshold"] == pytest.approx(0.682118, abs=1e-5)
    assert s1["round2_effective_threshold"] > s1["round1_effective_threshold"]

    assert live["scenarios"]["2_l6_ood_abstention"]["halt_reason"] == "L6_ABSTAIN"
    assert live["scenarios"]["2_l6_ood_abstention"]["gated_reward"] == 0.25
    assert live["scenarios"]["3_l4_prerun_dirty_tip_block"]["halt_reason"] == "L4_REHEARSAL_BLOCK"
    assert (
        live["scenarios"]["4_l1_lean_mcp_stale_epoch_block"]["halt_reason"]
        == "L1_MCP_BLOCK:mcp_epoch_freshness"
    )
    assert (
        live["scenarios"]["5_l4_postrun_precursor_ghost_peak_quarantine"]["halt_reason"]
        == "L4_ATTRIB_QUARANTINE"
    )
    assert (
        live["scenarios"]["6_l3_splitguard_canary_block"]["halt_reason"]
        == "L3_SPLITGUARD_CANARY_BLOCK"
    )
