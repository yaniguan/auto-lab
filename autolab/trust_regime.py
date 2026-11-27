"""Auto-Lab Formal Trust Regime Runtime Bridge (`AutoLabLean` <-> Python).

Connects Python autonomous research agents directly to the compiled Lean 4
executable (`lean/.lake/build/bin/autolab-lean --batch-tsv`), providing a
machine-checked hard boundary across all 14 Auto-Lab repositories (L6 -> L0),
plus an exact pure-Python mirror verified for 100% parity against the Lean binary.
"""

from __future__ import annotations

import math
import numbers
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from autolab.catalog import REPO_ROOT

LEAN_DIR = REPO_ROOT / "lean"

FORBIDDEN_LEAN_TOKENS = re.compile(r"\b(?:sorry|admit|native_decide)\b|^\s*axiom\b", re.MULTILINE)


@dataclass(frozen=True)
class TrustVerdict:
    allowed: bool
    repo: str
    rule: str
    detail: str
    extra: str = ""


def find_autolab_lean_binary() -> Path | None:
    candidates = [
        LEAN_DIR / ".lake" / "build" / "bin" / "autolab-lean.exe",
        LEAN_DIR / ".lake" / "build" / "bin" / "autolab-lean",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def audit_lean_sources(lean_root: Path = LEAN_DIR) -> dict[str, Any]:
    """Scan all `.lean` files in `lean/` to verify zero `sorry`, `admit`, `axiom`, or `native_decide`."""
    files = sorted(p for p in lean_root.rglob("*.lean") if ".lake" not in p.parts)
    theorem_re = re.compile(r"^\s*(?:theorem|lemma)\s+([A-Za-z0-9_']+)", re.MULTILINE)
    guard_re = re.compile(r"^\s*#guard\b", re.MULTILINE)

    theorems: list[str] = []
    guard_count = 0
    violations: list[str] = []

    for f in files:
        raw = f.read_text(encoding="utf-8")
        # Strip block comments, line comments, and string literals before scanning Lean tactic/decl tokens
        no_block = re.sub(r"/-.*?-/", "", raw, flags=re.DOTALL)
        no_comments = re.sub(r"--.*$", "", no_block, flags=re.MULTILINE)
        code_only = re.sub(r'"(?:\\.|[^"\\])*"', '""', no_comments)
        for m in FORBIDDEN_LEAN_TOKENS.finditer(code_only):
            violations.append(f"{f.relative_to(lean_root)}: forbidden `{m.group(0).strip()}`")
        theorems.extend(theorem_re.findall(code_only))
        guard_count += len(guard_re.findall(code_only))

    return {
        "lean_files": [str(f.relative_to(lean_root)).replace("\\", "/") for f in files],
        "file_count": len(files),
        "theorem_count": len(theorems),
        "theorems": theorems,
        "guard_count": guard_count,
        "zero_sorry_verified": len(violations) == 0 and len(theorems) > 0,
        "violations": violations,
    }


def conformal_rank_permille(n_calib: int, alpha_permille: int) -> int:
    return ((n_calib + 1) * (1000 - alpha_permille) + 999) // 1000


# The mirrors deny the inputs that the strict `--batch-tsv` parser in `lean/Main.lean` rejects,
# with the same `malformed_input` rule: Nat fields must be ints >= 0 and Int fields must be ints.
# Bools are not accepted as numbers, because they format as `True` / `False`.
_STEP_LEN = {"pick": 1, "drop": 1, "seal": 2, "thaw": 2, "xfer": 4, "mix": 4, "inc": 4}  # tuple length, op included
_WELL_NAT_KEYS = ("wellId", "vol", "cap", "deadVol", "soluteAmt")
_WELL_FLAG_KEYS = ("hasBuffer", "hasSample", "frozen", "sealed")


def _is_int(x: Any) -> bool:
    return isinstance(x, numbers.Integral) and not isinstance(x, bool)


def _is_nat(x: Any) -> bool:
    return _is_int(x) and x >= 0


def _rehearsal_input_error(
    pip_min: Any,
    pip_max: Any,
    proto_hash: Any,
    failed_hashes: Sequence[Any],
    wells: Sequence[dict[str, Any]],
    steps: Sequence[tuple[Any, ...]],
) -> str | None:
    """Return why the Lean parser would reject this rehearsal input, or None if it parses."""
    for x in (pip_min, pip_max, proto_hash, *failed_hashes):
        if not _is_nat(x):
            return f"expected a natural number, got {x!r}"
    for w in wells:
        if not (all(_is_nat(w.get(k)) for k in _WELL_NAT_KEYS) and all(k in w for k in _WELL_FLAG_KEYS)):
            return f"bad well spec: {w!r}"
    for st in steps:
        if not (st and isinstance(st[0], str) and _STEP_LEN.get(st[0]) == len(st)):
            return f"unknown step or wrong field count: {st!r}"
        if not all(_is_nat(x) for x in st[1:]):
            return f"expected natural numbers in step {st!r}"
    return None


def py_check_conformal(
    n_calib: int,
    alpha_permille: int,
    knn_dist_permille: int,
    tau_dist_permille: int,
    lo_milli: int,
    hi_milli: int,
    phys_min_milli: int = -15000,
    phys_max_milli: int = 1750,
) -> TrustVerdict:
    if not (
        all(_is_nat(x) for x in (n_calib, alpha_permille, knn_dist_permille, tau_dist_permille))
        and all(_is_int(x) for x in (lo_milli, hi_milli, phys_min_milli, phys_max_milli))
    ):
        return TrustVerdict(False, "lab-decide", "malformed_input", "non-integer field, or negative count or distance")
    if not (0 < alpha_permille < 1000):
        return TrustVerdict(False, "lab-decide", "alpha_in_open_unit_interval", "alphaPermille must lie in (0, 1000)")
    if n_calib <= 0:
        return TrustVerdict(False, "lab-decide", "nonempty_calibration_set", "nCalib must be positive")
    if conformal_rank_permille(n_calib, alpha_permille) > n_calib:
        return TrustVerdict(False, "lab-decide", "finite_sample_conformal_rank", "ceil((n+1)*(1-alpha)) > nCalib")
    if knn_dist_permille > tau_dist_permille:
        return TrustVerdict(False, "lab-decide", "knn_trust_boundary", "candidate exceeds kNN trust threshold")
    if lo_milli > hi_milli:
        return TrustVerdict(False, "lab-decide", "interval_well_ordered", "lower bound exceeds upper bound")
    if not (phys_min_milli <= lo_milli and hi_milli <= phys_max_milli):
        return TrustVerdict(False, "lab-decide", "physical_solubility_bounds", "interval outside physical range")
    return TrustVerdict(True, "lab-decide", "valid", "certified inside conformal trust region")


def py_check_buymake(
    is_buy: bool,
    steps: int,
    max_steps: int,
    acyclic: bool,
    target_cno: tuple[int, int, int],
    delta_cno: tuple[int, int, int],
    reactant_cno: tuple[int, int, int],
    in_stock: bool,
    cost_complete: bool,
    usd_per_g: bool,
    price_cents: int | None,
    budget_cents: int | None,
    commercial_mode: bool,
    all_permissive: bool,
) -> TrustVerdict:
    if is_buy:
        stoich_ok = steps == 0
    else:
        exp_cno = (
            target_cno[0] + delta_cno[0],
            target_cno[1] + delta_cno[1],
            target_cno[2] + delta_cno[2],
        )
        stoich_ok = (1 <= steps <= max_steps) and acyclic and in_stock and (reactant_cno == exp_cno)
    if not stoich_ok:
        return TrustVerdict(False, "buy-or-make", "acyclic_atom_balanced_route", "stoichiometry or acyclic check failed")

    if budget_cents is not None:
        if price_cents is None or (not cost_complete) or (not usd_per_g) or (price_cents > budget_cents):
            return TrustVerdict(False, "buy-or-make", "strict_homogeneous_budget", "budget or unit/null-price check failed")

    if commercial_mode and not all_permissive:
        return TrustVerdict(False, "buy-or-make", "transitive_license_gate", "non-permissive source blocked in commercial mode")

    return TrustVerdict(True, "buy-or-make", "valid", "certified buy-or-make candidate")


def py_check_rehearsal(
    pip_min: int,
    pip_max: int,
    proto_hash: int,
    failed_hashes: Sequence[int],
    wells: Sequence[dict[str, Any]],
    steps: Sequence[tuple[Any, ...]],
) -> TrustVerdict:
    bad_input = _rehearsal_input_error(pip_min, pip_max, proto_hash, failed_hashes, wells, steps)
    if bad_input is not None:
        return TrustVerdict(False, "lab-rehearsal", "malformed_input", bad_input)
    if proto_hash in failed_hashes:
        return TrustVerdict(False, "lab-rehearsal", "episodic_recall_fast_deny", "hash previously failed")
    seen_ids: set[int] = set()
    wmap: dict[int, dict[str, Any]] = {}
    for w in wells:
        wid = int(w["wellId"])
        if wid in seen_ids:
            return TrustVerdict(False, "lab-rehearsal", "unique_well_ids", "duplicate well ID")
        seen_ids.add(wid)
        wmap[wid] = dict(w)
    # Same order as `initDeckOK`: every well ID is checked before any capacity.
    for w in wells:
        if not (0 <= int(w["vol"]) <= int(w["cap"]) and 0 <= int(w["deadVol"]) <= int(w["cap"])):
            return TrustVerdict(False, "lab-rehearsal", "initial_state_within_capacity", "invalid initial well capacity")
    if not (0 < pip_min <= pip_max):
        return TrustVerdict(False, "lab-rehearsal", "valid_pipette_spec", "invalid pipette range")

    tip_mode = "none"  # "none" | "clean" | "used"
    tip_vol, tip_sol, tip_buf, tip_samp = 0, 0, False, False

    def tip_may_enter(target: dict[str, Any]) -> bool:
        if tip_mode == "none":
            return False
        if tip_mode == "clean":
            return True
        class_ok = ((not tip_samp) or bool(target["hasSample"])) and (
            (not tip_buf) or bool(target["hasBuffer"]) or bool(target["hasSample"])
        )
        if tip_sol == 0:
            conc_ok = True
        else:
            conc_ok = (
                tip_vol > 0
                and int(target["vol"]) > 0
                and int(target["soluteAmt"]) * tip_vol <= tip_sol * int(target["vol"])
            )
        return class_ok and conc_ok

    for st in steps:
        op = st[0]
        if op == "pick":
            if tip_mode != "none":
                return TrustVerdict(False, "lab-rehearsal", "pick_tip_requires_empty_mount", "tip already mounted")
            tip_mode = "clean"
        elif op == "drop":
            if tip_mode == "none":
                return TrustVerdict(False, "lab-rehearsal", "drop_tip_requires_mounted_tip", "no tip mounted")
            tip_mode = "none"
        elif op == "xfer":
            _, s_id, d_id, v = st
            if s_id not in wmap or d_id not in wmap:
                return TrustVerdict(False, "lab-rehearsal", "known_well_id", "unknown well ID")
            src, dst = wmap[s_id], wmap[d_id]
            if s_id == d_id:
                return TrustVerdict(False, "lab-rehearsal", "distinct_transfer_wells", "src == dst")
            if not (pip_min <= v <= pip_max):
                return TrustVerdict(False, "lab-rehearsal", "pipette_volume_range", "out of pipette range")
            if src["frozen"] or dst["frozen"]:
                return TrustVerdict(False, "lab-rehearsal", "thawed_before_pipetting", "frozen container")
            if src["sealed"] or dst["sealed"]:
                return TrustVerdict(False, "lab-rehearsal", "unsealed_before_pipetting", "sealed container")
            if not tip_may_enter(src):
                return TrustVerdict(False, "lab-rehearsal", "no_tip_cross_contamination", "tip contamination")
            if int(src["deadVol"]) + v > int(src["vol"]):
                return TrustVerdict(False, "lab-rehearsal", "enough_recoverable_volume", "source underflow")
            if int(dst["vol"]) + v > int(dst["cap"]):
                return TrustVerdict(False, "lab-rehearsal", "no_well_overfill", "destination overflow")
            moved_sol = 0 if int(src["vol"]) == 0 else (int(src["soluteAmt"]) * v) // int(src["vol"])
            src["vol"] = int(src["vol"]) - v
            src["soluteAmt"] = int(src["soluteAmt"]) - moved_sol
            dst["vol"] = int(dst["vol"]) + v
            dst["soluteAmt"] = int(dst["soluteAmt"]) + moved_sol
            dst["hasBuffer"] = bool(dst["hasBuffer"]) or bool(src["hasBuffer"])
            dst["hasSample"] = bool(dst["hasSample"]) or bool(src["hasSample"])
            tip_mode = "used"
            tip_vol, tip_sol = int(dst["vol"]), int(dst["soluteAmt"])
            tip_buf, tip_samp = bool(dst["hasBuffer"]), bool(dst["hasSample"])
        elif op == "mix":
            _, w_id, v, reps = st
            if w_id not in wmap:
                return TrustVerdict(False, "lab-rehearsal", "known_well_id", "unknown well ID")
            w = wmap[w_id]
            if reps <= 0:
                return TrustVerdict(False, "lab-rehearsal", "positive_mix_reps", "reps <= 0")
            if not (pip_min <= v <= pip_max):
                return TrustVerdict(False, "lab-rehearsal", "mix_barrel_volume_range", "mix volume out of range")
            if w["frozen"] or w["sealed"]:
                return TrustVerdict(False, "lab-rehearsal", "mix_open_thawed_well", "frozen or sealed")
            if not tip_may_enter(w):
                return TrustVerdict(False, "lab-rehearsal", "no_mix_cross_contamination", "mix contamination")
            if int(w["deadVol"]) + v > int(w["vol"]):
                return TrustVerdict(False, "lab-rehearsal", "mix_sufficient_well_volume", "insufficient well volume")
            tip_mode = "used"
            tip_vol, tip_sol = int(w["vol"]), int(w["soluteAmt"])
            tip_buf, tip_samp = bool(w["hasBuffer"]), bool(w["hasSample"])
        elif op == "inc":
            _, w_id, temp_c, dur_s = st
            if w_id not in wmap:
                return TrustVerdict(False, "lab-rehearsal", "known_well_id", "unknown well ID")
            w = wmap[w_id]
            if not (dur_s > 0 and 4 <= temp_c <= 98):
                return TrustVerdict(False, "lab-rehearsal", "incubate_temp_duration_bounds", "bad temp or duration")
            if w["frozen"]:
                return TrustVerdict(False, "lab-rehearsal", "thaw_before_incubate", "frozen incubate")
            if temp_c >= 80 and not w["sealed"]:
                return TrustVerdict(False, "lab-rehearsal", "high_temp_requires_seal", "unsealed >= 80 C")
        elif op == "seal":
            _, w_id = st
            if w_id not in wmap:
                return TrustVerdict(False, "lab-rehearsal", "known_well_id", "unknown well ID")
            if wmap[w_id]["sealed"]:
                return TrustVerdict(False, "lab-rehearsal", "not_already_sealed", "already sealed")
            wmap[w_id]["sealed"] = True
        elif op == "thaw":
            _, w_id = st
            if w_id not in wmap:
                return TrustVerdict(False, "lab-rehearsal", "known_well_id", "unknown well ID")
            if not wmap[w_id]["frozen"]:
                return TrustVerdict(False, "lab-rehearsal", "thaw_requires_frozen", "already thawed")
            wmap[w_id]["frozen"] = False
        else:
            return TrustVerdict(False, "lab-rehearsal", "malformed_input", f"unknown step {op!r}")

    if tip_mode != "none":
        return TrustVerdict(False, "lab-rehearsal", "tip_dropped_at_end", "tip still mounted")
    tot = sum(int(w["vol"]) for w in wmap.values())
    return TrustVerdict(True, "lab-rehearsal", "valid", "certified rehearsal", str(tot))


def format_rehearsal_tsv(
    pip_min: int,
    pip_max: int,
    proto_hash: int,
    failed_hashes: Sequence[int],
    wells: Sequence[dict[str, Any]],
    steps: Sequence[tuple[Any, ...]],
) -> str:
    f_csv = ",".join(str(x) for x in failed_hashes)
    w_spec = ";".join(
        f"{w['wellId']}:{w['vol']}:{w['cap']}:{w['deadVol']}:{w['soluteAmt']}:"
        f"{int(bool(w['hasBuffer']))}:{int(bool(w['hasSample']))}:{int(bool(w['frozen']))}:{int(bool(w['sealed']))}"
        for w in wells
    )
    s_tokens: list[str] = []
    for st in steps:
        s_tokens.append(":".join(str(x) for x in st))
    s_spec = ";".join(s_tokens)
    return f"REHEARSAL\t{pip_min}\t{pip_max}\t{proto_hash}\t{f_csv}\t{w_spec}\t{s_spec}"


class LeanBatchKernel:
    """High-throughput batch verifier backed by the compiled `autolab-lean --batch-tsv` binary."""

    def __init__(self, binary_path: Path | None = None) -> None:
        self.binary_path = binary_path or find_autolab_lean_binary()

    @property
    def available(self) -> bool:
        return self.binary_path is not None and self.binary_path.is_file()

    def eval_lines(self, lines: Sequence[str]) -> list[TrustVerdict]:
        if not lines:
            return []
        if not self.available:
            raise RuntimeError("Compiled `autolab-lean` binary not found; run `lake build` in `lean/`.")
        payload = "\n".join(lines) + "\n"
        proc = subprocess.run(
            [str(self.binary_path), "--batch-tsv"],
            input=payload,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
        out_lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        if len(out_lines) != len(lines):
            raise RuntimeError(f"Lean batch output mismatch: sent {len(lines)} lines, got {len(out_lines)}")
        verdicts: list[TrustVerdict] = []
        for raw in out_lines:
            parts = raw.split("\t")
            if parts[0] == "OK":
                extra = parts[3] if len(parts) > 3 else ""
                verdicts.append(TrustVerdict(True, parts[1], parts[2], "accepted by the compiled Lean checker", extra))
            else:
                detail = parts[3] if len(parts) > 3 else ""
                verdicts.append(TrustVerdict(False, parts[1], parts[2], detail))
        return verdicts
