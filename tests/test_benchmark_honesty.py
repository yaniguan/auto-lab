"""Tests enforcing scientific honesty, fail-closed data/sibling loading, and zero README/JSON drift."""

from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from autolab.catalog import REPO_ROOT
from autolab.datasets import ESOL_SHA256, load_esol_dataset, resolve_esol_csv
from autolab.trust_regime import audit_lean_sources
from benchmarks.trust_regime_study import run_exp3_scheduling

RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"


def _resolve_dotted(obj: Any, dotted_path: str) -> Any:
    cur = obj
    for part in dotted_path.split("."):
        if isinstance(cur, dict):
            assert part in cur, f"Key {part!r} not found in {list(cur.keys())} while resolving {dotted_path!r}"
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            raise AssertionError(f"Cannot traverse {part!r} on {type(cur).__name__} in {dotted_path!r}")
    return cur


def _extract_numbers(text: str) -> list[float]:
    cleaned = re.sub(r"`([^`]*)`", r"\1", text)
    # Strip trailing units like 'min', '%', 'x', 's' after numbers
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", cleaned)]


def validate_what_is_real_table(markdown_text: str, results_dir: Path = RESULTS_DIR) -> int:
    """Parse the 'What Is Real vs. Simulated' markdown table and verify every row against JSON results."""
    allowed_labels = {"real_data", "independent_simulator", "simulation", "by_construction", "PENDING"}
    json_cache: dict[str, dict[str, Any]] = {}

    lines = markdown_text.splitlines()
    in_section = False
    table_rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            if "What Is Real vs. Simulated" in stripped or "What is Real vs. Simulated" in stripped:
                in_section = True
                continue
            if in_section and table_rows:
                break
        if in_section and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 6:
                if set("".join(cells)) <= {"-", ":", " "}:
                    continue
                if cells[0].lower().startswith("headline metric") or cells[0].lower() == "metric":
                    continue
                table_rows.append(cells)

    assert len(table_rows) >= 10, f"Expected >= 10 rows in 'What Is Real vs. Simulated' table, got {len(table_rows)}"

    for cells in table_rows:
        metric_col, value_col, script_col, json_key_col, n_col, basis_col = cells[:6]
        assert metric_col, "Empty metric description cell"
        assert n_col, f"Empty n cell for {metric_col}"
        assert any(lbl in basis_col for lbl in allowed_labels), (
            f"Row {metric_col!r} basis {basis_col!r} must include one of {sorted(allowed_labels)}"
        )

        # Verify script exists
        script_match = re.search(r"benchmarks/[A-Za-z0-9_]+\.py", script_col)
        assert script_match is not None, f"Row {metric_col!r} missing benchmarks/*.py script path in {script_col!r}"
        assert (REPO_ROOT / script_match.group(0)).is_file(), f"Missing script {script_match.group(0)}"

        # Resolve JSON key reference(s): `file.json:dotted.key` (supports `a -> b` pairs)
        refs = re.findall(r"([A-Za-z0-9_]+\.json):([A-Za-z0-9_.]+)", json_key_col)
        assert refs, f"Row {metric_col!r} has no `<file>.json:<dotted.key>` reference in {json_key_col!r}"

        expected_vals: list[float] = []
        for fname, dpath in refs:
            if fname not in json_cache:
                fpath = results_dir / fname
                assert fpath.is_file(), f"Missing results JSON {fpath}"
                json_cache[fname] = json.loads(fpath.read_text(encoding="utf-8"))
            raw_val = _resolve_dotted(json_cache[fname], dpath)
            if isinstance(raw_val, (int, float)) and not isinstance(raw_val, bool):
                expected_vals.append(float(raw_val))
            elif isinstance(raw_val, str):
                expected_vals.extend(_extract_numbers(raw_val))
            else:
                raise AssertionError(f"Unsupported JSON target {fname}:{dpath} -> {raw_val!r}")

        shown_nums = _extract_numbers(value_col)
        assert len(shown_nums) >= len(expected_vals), (
            f"Row {metric_col!r} value cell {value_col!r} has fewer numbers than JSON refs {expected_vals}"
        )
        for exp_v in expected_vals:
            assert any(abs(s - exp_v) < 1e-6 for s in shown_nums), (
                f"Drift detected in row {metric_col!r}: value cell {value_col!r} does not match JSON value {exp_v} "
                f"from {json_key_col!r}"
            )

    return len(table_rows)


def assert_readme_prose_matches_results(readme_text: str, results_dir: Path = RESULTS_DIR) -> None:
    """Verify headline numbers in README prose independently from the structured table."""
    validate_what_is_real_table(readme_text, results_dir=results_dir)
    prose_only = readme_text.split("### What Is Real vs. Simulated")[0]

    trust = json.loads((results_dir / "trust_regime_results.json").read_text(encoding="utf-8"))
    novel = json.loads((results_dir / "novel_directions_results.json").read_text(encoding="utf-8"))
    ot = json.loads((results_dir / "opentrons_library_rehearsal.json").read_text(encoding="utf-8"))

    thm_cnt = trust["lean_audit"]["theorem_count"]
    grd_cnt = trust["lean_audit"]["guard_count"]
    assert f"{thm_cnt} machine-checked theorems" in prose_only
    assert f"{grd_cnt} `#guard` witnesses" in prose_only

    e1 = trust["experiments"]["exp1_molecular_discovery"]["regimes"]
    assert f"{e1['ungated']['prediction_mae']} -> {e1['lean_trust']['prediction_mae']}" in prose_only
    assert f"{e1['ungated']['empirical_coverage_pct']}% -> {e1['lean_trust']['empirical_coverage_pct']}%" in prose_only

    e2 = trust["experiments"]["exp2_protocol_synthesis"]["regimes"]
    assert f"{e2['ungated_top1']['independent_sim_fault_pct']}% -> {e2['lean_best_of_8_plus_guided_repair']['independent_sim_fault_pct']}%" in prose_only
    assert str(e2["lean_best_of_8_plus_guided_repair"]["valid_completion_pct"]) in prose_only

    e3 = trust["experiments"]["exp3_fleet_scheduling"]["regimes"]
    assert f"{e3['ungated_greedy']['mean_makespan_min']} -> {e3['cpsat']['mean_makespan_min']} min" in prose_only

    e5 = trust["experiments"]["exp5_rlvr_posttraining"]["regimes"]
    assert f"{e5['soft_additive_reward_grpo']['true_verified_accuracy_pct']}% -> {e5['lean_trust_gated_grpo']['true_verified_accuracy_pct']}%" in prose_only

    d4 = novel["directions"]["d4_adversarial_coevolution"]
    assert f"{d4['distinct_cases']} distinct cases" in prose_only

    ots = ot["summary"]
    assert f"{ots['n_imported']}/{ots['n_total']}" in prose_only
    assert f"{ots['audited_false_alarm_rate_pct']}%" in prose_only


def test_run_exp3_scheduling_raises_when_labshift_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # 1. Missing package -> ImportError (never returns hardcoded "Measured benchmark summary")
    for mod_name in list(sys.modules):
        if mod_name == "labshift" or mod_name.startswith("labshift."):
            monkeypatch.delitem(sys.modules, mod_name, raising=False)
    monkeypatch.setitem(sys.modules, "labshift", None)
    monkeypatch.setitem(sys.modules, "labshift.bench", None)
    clean_sys_path = [p for p in sys.path if "labshift" not in p]
    monkeypatch.setattr(sys, "path", clean_sys_path)

    with pytest.raises(ImportError, match="labshift"):
        run_exp3_scheduling(labshift_root=tmp_path / "nonexistent_labshift")

    # 2. Package importable, but benchmark JSON directory missing -> RuntimeError
    fake_pkg = types.ModuleType("labshift")
    fake_bench = types.ModuleType("labshift.bench")
    fake_bench.collect_instance_paths = lambda _p: []  # type: ignore[attr-defined]
    fake_bench.solve_instance = lambda *_a, **_k: None  # type: ignore[attr-defined]
    fake_metrics = types.ModuleType("labshift.metrics")
    fake_metrics.compute_metrics = lambda *_a, **_k: None  # type: ignore[attr-defined]
    fake_models = types.ModuleType("labshift.models")
    fake_models.Instance = object  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "labshift", fake_pkg)
    monkeypatch.setitem(sys.modules, "labshift.bench", fake_bench)
    monkeypatch.setitem(sys.modules, "labshift.metrics", fake_metrics)
    monkeypatch.setitem(sys.modules, "labshift.models", fake_models)

    with pytest.raises(RuntimeError, match="Benchmark directory not found"):
        run_exp3_scheduling(labshift_root=tmp_path / "empty_labshift")


def test_esol_loader_fails_closed_without_synthetic_fallback(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="not found"):
        resolve_esol_csv(
            cache_path=tmp_path / "missing.csv",
            search_roots=[tmp_path / "no_siblings"],
            allow_download=False,
        )

    corrupt_csv = tmp_path / "corrupt.csv"
    corrupt_csv.write_text("Compound ID,measured log solubility in mols per litre\nfoo,-1.2\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        load_esol_dataset(
            cache_path=corrupt_csv,
            search_roots=[tmp_path / "no_siblings"],
            allow_download=False,
        )
    assert len(ESOL_SHA256) == 64


def test_no_personal_paths_and_honest_benchmark_metadata() -> None:
    personal_re = re.compile(r"C:\\Users\\|/Users/yanig|Users\\\\yanig", re.IGNORECASE)
    scan_files = [
        REPO_ROOT / "README.md",
        *(REPO_ROOT / "autolab").rglob("*.py"),
        *(REPO_ROOT / "benchmarks").rglob("*.py"),
        *(REPO_ROOT / "benchmarks").rglob("*.json"),
        *(REPO_ROOT / "docs").rglob("*.md"),
        *(REPO_ROOT / "site").rglob("*.js"),
        *(REPO_ROOT / "site").rglob("*.html"),
    ]
    for path in scan_files:
        if path.is_file():
            txt = path.read_text(encoding="utf-8")
            assert personal_re.search(txt) is None, f"Hardcoded personal path found in {path}"

    audit = audit_lean_sources()
    trust = json.loads((RESULTS_DIR / "trust_regime_results.json").read_text(encoding="utf-8"))
    novel = json.loads((RESULTS_DIR / "novel_directions_results.json").read_text(encoding="utf-8"))

    # Zero Lean theorem/guard drift between live `.lean` files and committed results JSONs
    assert trust["lean_audit"]["theorem_count"] == audit["theorem_count"] == 50
    assert trust["lean_audit"]["guard_count"] == audit["guard_count"] == 27
    assert novel["lean_audit"]["theorem_count"] == audit["theorem_count"] == 50
    assert novel["lean_audit"]["guard_count"] == audit["guard_count"] == 27

    # Site assets must stay synced with benchmarks/results/
    site_trust = json.loads((REPO_ROOT / "site" / "assets" / "trust-regime-data.json").read_text(encoding="utf-8"))
    site_novel = json.loads((REPO_ROOT / "site" / "assets" / "novel-directions-data.json").read_text(encoding="utf-8"))
    assert site_trust == trust
    assert site_novel == novel

    # Issue #1 renamings & labels
    e3_regimes = trust["experiments"]["exp3_fleet_scheduling"]["regimes"]
    assert "cpsat" in e3_regimes and "lean_gated_cpsat" not in e3_regimes

    e5 = trust["experiments"]["exp5_rlvr_posttraining"]
    assert e5["simulation_only"] is True
    assert "6-arm bandit" in e5["task"] and "PENDING" in e5["task"]

    d4 = novel["directions"]["d4_adversarial_coevolution"]
    assert d4["distinct_cases"] == 21


def test_opentrons_library_rehearsal_results_integrity() -> None:
    ot_path = RESULTS_DIR / "opentrons_library_rehearsal.json"
    assert ot_path.is_file(), f"Missing {ot_path}"
    ot = json.loads(ot_path.read_text(encoding="utf-8"))

    repos = ot["pinned_repositories"]
    assert re.fullmatch(r"[0-9a-f]{40}", repos["Opentrons/Protocols"]["commit_sha"])
    assert re.fullmatch(r"[0-9a-f]{40}", repos["Opentrons/opentrons"]["commit_sha"])

    s = ot["summary"]
    assert s["n_total"] >= 60
    assert s["n_imported"] + s["n_unsupported"] == s["n_total"]
    assert s["n_allowed"] + s["n_denied"] == s["n_imported"]
    assert s["lean_python_mirror_mismatches"] == 0
    assert sum(ot["unsupported_by_reason"].values()) == s["n_unsupported"]
    assert sum(ot["deny_counts_by_rule"].values()) == s["n_denied"]
    assert len(ot["protocols"]) == s["n_total"]

    for proto in ot["protocols"]:
        assert proto.get("protocol_id")
        assert proto.get("upstream_license")
        assert proto.get("commit_sha")

    audited = ot["audited_denies"]
    assert len(audited) >= 20
    denied_ids = {p["protocol_id"]: p["rule"] for p in ot["protocols"] if p["status"] == "denied"}
    for item in audited:
        pid = item["protocol_id"]
        assert pid in denied_ids, f"Audited protocol {pid} is not a denied protocol"
        assert item["rule"] == denied_ids[pid]
        assert item["classification"] in {"true_hazard", "abstraction_false_alarm"}
        assert len(item["explanation"].strip()) >= 30

    n_fa = sum(1 for item in audited if item["classification"] == "abstraction_false_alarm")
    expected_fa_pct = round(100.0 * n_fa / len(audited), 1)
    assert s["audited_denies_count"] == len(audited)
    assert s["audited_false_alarm_count"] == n_fa
    assert s["audited_true_hazard_count"] == len(audited) - n_fa
    assert s["audited_false_alarm_rate_pct"] == expected_fa_pct


def test_readme_and_docs_zero_number_drift() -> None:
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    study_doc_text = (REPO_ROOT / "docs" / "TRUST_REGIME_STUDY.md").read_text(encoding="utf-8")

    assert_readme_prose_matches_results(readme_text)
    validate_what_is_real_table(study_doc_text)

    # Verify the drift detector actively fails when a README headline number is tampered with!
    tampered = readme_text.replace("116.6 min", "112.9 min", 1)
    assert tampered != readme_text
    with pytest.raises(AssertionError):
        assert_readme_prose_matches_results(tampered)
