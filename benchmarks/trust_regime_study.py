"""Empirical & Simulation Study: Evaluating `AutoLabLean` Across Five Layers.

Executes five reproducible, CPU-runnable benchmarks spanning the Auto-Lab stack,
piping candidate actions through the compiled native Lean 4.36.0 verifier
(`lean/.lake/build/bin/autolab-lean --batch-tsv`) while separating independent
ground-truth measurements from `"by construction"` gate-invariant checks:

1. L6 + L5 Bounded Molecular Discovery (1,128 real SHA-256-verified Delaney ESOL
   compounds evaluated against independent held-out measured `logS`; simulated
   procurement flags reported separately and labeled `"by construction"`).
2. L4 + L1 Wet-Lab Protocol Synthesis (200 x 8 simulated candidate protocols
   validated against `stepbot`'s independent Opentrons API v2 simulator in
   addition to `AutoLabLean` assay-invariant checks).
3. L5 Multi-Instrument Fleet Scheduling (`labshift` 30-instance benchmark suite:
   `ungated_greedy` vs `greedy_with_repair` vs OR-Tools `cpsat`; fail-closed if
   `labshift` is missing).
4. L4 Scientific Lab-Database SQL Verification (`lab-verify` 30-candidate
   adversarial stress suite with worst-case wrong-first ordering).
5. L3 6-Arm Bandit Policy Simulation (softmax policy over 6 hand-scored rollout
   archetypes; NOT neural LLM weight training - full GPU RLVR run is PENDING).
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = REPO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autolab.datasets import load_esol_dataset  # noqa: E402
from autolab.trust_regime import (  # noqa: E402
    LeanBatchKernel,
    audit_lean_sources,
    conformal_rank_permille,
    format_rehearsal_tsv,
    py_check_buymake,
    py_check_conformal,
    py_check_rehearsal,
)


# ---------------------------------------------------------------------------
# Experiment 1: L6 + L5 Molecular Discovery (Independent Real ESOL `logS`)
# ---------------------------------------------------------------------------
def run_exp1_molecular_campaign(kernel: LeanBatchKernel) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler

    features, targets, data_source = load_esol_dataset()
    X_all = np.asarray(features, dtype=float)
    y_all = np.asarray(targets, dtype=float)

    budget_k = 25
    budget_cents = 2500  # $25.00 / g
    soluble_hit_thresh = -2.8  # measured logS >= -2.8 log(mol/L) (~1.6 mM aqueous solubility)
    seeds = [11, 22, 33, 44, 55]

    metrics = {
        "ungated": {
            "mae": [],
            "coverage": [],
            "measured_hits": [],
            "ood_selected": [],
            "gate_violations_by_construction": [],
        },
        "heuristic": {
            "mae": [],
            "coverage": [],
            "measured_hits": [],
            "ood_selected": [],
            "gate_violations_by_construction": [],
        },
        "lean_trust": {
            "mae": [],
            "coverage": [],
            "measured_hits": [],
            "ood_selected": [],
            "gate_violations_by_construction": [],
        },
    }
    pool_diag = {
        "in_region_mae": [],
        "abstained_ood_mae": [],
        "in_region_coverage_90_pct": [],
        "abstained_ood_coverage_90_pct": [],
    }
    lean_parity_checks = 0
    cand_pool_sizes: list[int] = []

    for sd in seeds:
        rng = np.random.default_rng(sd)
        # Historical library: lower-MW compounds (MW <= 78th percentile); candidate pool includes heavy/multi-ring tail
        in_mask = X_all[:, 0] <= np.percentile(X_all[:, 0], 78)
        in_idx = np.where(in_mask)[0]
        out_idx = np.where(~in_mask)[0]
        rng.shuffle(in_idx)
        rng.shuffle(out_idx)

        n_tr = int(0.55 * len(in_idx))
        n_cal = int(0.20 * len(in_idx))
        tr_idx = in_idx[:n_tr]
        cal_idx = in_idx[n_tr : n_tr + n_cal]
        heldout_all_idx = np.concatenate([in_idx[n_tr + n_cal :], out_idx])

        scaler = StandardScaler().fit(X_all[tr_idx])
        X_tr_s = scaler.transform(X_all[tr_idx])
        X_cal_s = scaler.transform(X_all[cal_idx])

        model = GradientBoostingRegressor(random_state=sd, n_estimators=120, max_depth=3)
        model.fit(X_tr_s, y_all[tr_idx])

        nn = NearestNeighbors(n_neighbors=5).fit(X_tr_s)
        cal_dists = nn.kneighbors(X_cal_s)[0].mean(axis=1)
        tau_dist = float(np.quantile(cal_dists, 0.85))

        cal_res = np.abs(y_all[cal_idx] - model.predict(X_cal_s))
        n_c = len(cal_res)
        k_rank = conformal_rank_permille(n_c, 100)  # 90% nominal split-conformal coverage
        q_hat = float(np.sort(cal_res)[min(k_rank - 1, n_c - 1)])

        # 1. Pure real-data diagnostic across ALL held-out compounds (zero simulated procurement flags)
        X_ho_s = scaler.transform(X_all[heldout_all_idx])
        ho_dists = nn.kneighbors(X_ho_s)[0].mean(axis=1)
        ho_preds = model.predict(X_ho_s)
        y_ho = y_all[heldout_all_idx]
        ho_in = ho_dists <= tau_dist
        ho_lo = np.maximum(-15.0, ho_preds - q_hat)
        ho_hi = np.minimum(1.75, ho_preds + q_hat)
        pool_diag["in_region_mae"].append(float(np.mean(np.abs(y_ho[ho_in] - ho_preds[ho_in]))))
        pool_diag["abstained_ood_mae"].append(float(np.mean(np.abs(y_ho[~ho_in] - ho_preds[~ho_in]))))
        pool_diag["in_region_coverage_90_pct"].append(
            100.0 * float(np.mean((y_ho[ho_in] >= ho_lo[ho_in]) & (y_ho[ho_in] <= ho_hi[ho_in])))
        )
        pool_diag["abstained_ood_coverage_90_pct"].append(
            100.0 * float(np.mean((y_ho[~ho_in] >= ho_lo[~ho_in]) & (y_ho[~ho_in] <= ho_hi[~ho_in])))
        )

        # 2. Drug-like scaffold candidate pool (held-out compounds with MW >= 200 Da and >= 1 ring)
        pool_idx = np.array([idx for idx in heldout_all_idx if X_all[idx, 0] >= 200.0 and X_all[idx, 2] >= 1.0])
        cand_pool_sizes.append(int(len(pool_idx)))
        X_pool_s = scaler.transform(X_all[pool_idx])
        pool_dists = nn.kneighbors(X_pool_s)[0].mean(axis=1)
        preds = model.predict(X_pool_s)
        y_pool = y_all[pool_idx]

        # Simulated procurement metadata (explicitly separated from real experimental logS ground truth!)
        n_p = len(pool_idx)
        tsv_conformal: list[str] = []
        tsv_buymake: list[str] = []
        py_ok_flags: list[bool] = []
        heur_ok_flags: list[bool] = []

        for i in range(n_p):
            r_u = rng.random()
            is_buy = r_u < 0.35
            steps = 0 if is_buy else int(rng.choice([1, 2]))
            acyclic = True if is_buy else (rng.random() >= 0.18)
            t_cno = (12, 2, 2)
            d_cno = (0, 0, 1)
            r_cno = (12, 2, 3) if acyclic else (13, 2, 3)
            in_stock = True
            unit_trap = rng.random() < 0.15
            has_price = not (unit_trap and rng.random() < 0.5)
            cost_complete = not unit_trap
            usd_per_g = not unit_trap
            price_c = int(rng.integers(400, 3100)) if has_price else None
            all_perm = rng.random() >= 0.08

            dist_pm = int(round(pool_dists[i] * 1000))
            tau_pm = int(round(tau_dist * 1000))
            lo_m = max(-15000, int(round((preds[i] - q_hat) * 1000)))
            hi_m = min(1750, int(round((preds[i] + q_hat) * 1000)))

            c_verd = py_check_conformal(n_c, 100, dist_pm, tau_pm, lo_m, hi_m)
            b_verd = py_check_buymake(
                is_buy,
                steps,
                2,
                acyclic,
                t_cno,
                d_cno,
                r_cno,
                in_stock,
                cost_complete,
                usd_per_g,
                price_c,
                budget_cents,
                True,
                all_perm,
            )
            py_ok_flags.append(c_verd.allowed and b_verd.allowed)

            heur_price_ok = (price_c is None) or (price_c <= budget_cents)
            heur_ok_flags.append((steps <= 2) and in_stock and heur_price_ok)

            tsv_conformal.append(f"CONFORMAL\t{n_c}\t100\t{dist_pm}\t{tau_pm}\t{lo_m}\t{hi_m}\t-15000\t1750")
            tsv_buymake.append(
                f"BUYMAKE\t{int(is_buy)}\t{steps}\t2\t{int(acyclic)}\t"
                f"{t_cno[0]}\t{t_cno[1]}\t{t_cno[2]}\t{d_cno[0]}\t{d_cno[1]}\t{d_cno[2]}\t"
                f"{r_cno[0]}\t{r_cno[1]}\t{r_cno[2]}\t{int(in_stock)}\t{int(cost_complete)}\t"
                f"{int(usd_per_g)}\t{int(has_price)}\t{price_c or 0}\t1\t{budget_cents}\t1\t{int(all_perm)}"
            )

        lean_c = kernel.eval_lines(tsv_conformal)
        lean_b = kernel.eval_lines(tsv_buymake)
        lean_ok_flags = [lc.allowed and lb.allowed for lc, lb in zip(lean_c, lean_b)]
        assert lean_ok_flags == py_ok_flags, "Mismatch between compiled Lean 4 kernel and Python mirror!"
        lean_parity_checks += 2 * n_p

        # Honest ranking: NO artificial OOD optimism bonus added to the ungated arm!
        # All three arms rank candidates by the exact same raw GBDT predicted logS (`preds`).
        order_raw = list(np.argsort(-preds))
        order_ungated = order_raw[:budget_k]
        order_heur = [i for i in order_raw if heur_ok_flags[i]][:budget_k]
        order_lean = [i for i in order_raw if lean_ok_flags[i]][:budget_k]

        for key, chosen in [("ungated", order_ungated), ("heuristic", order_heur), ("lean_trust", order_lean)]:
            # Independent empirical ground-truth metrics against measured experimental logS:
            mae = float(np.mean(np.abs(y_pool[chosen] - preds[chosen])))
            cov = float(
                np.mean(
                    (y_pool[chosen] >= np.maximum(-15.0, preds[chosen] - q_hat))
                    & (y_pool[chosen] <= np.minimum(1.75, preds[chosen] + q_hat))
                )
            )
            measured_hits = float(np.mean(y_pool[chosen] >= soluble_hit_thresh))
            ood_frac = float(np.mean(pool_dists[chosen] > tau_dist))
            # Gate-invariant check (explicitly labeled by construction):
            gate_viols = sum(1 for i in chosen if not lean_ok_flags[i]) / max(1, len(chosen))

            metrics[key]["mae"].append(mae)
            metrics[key]["coverage"].append(cov * 100.0)
            metrics[key]["measured_hits"].append(measured_hits * 100.0)
            metrics[key]["ood_selected"].append(ood_frac * 100.0)
            metrics[key]["gate_violations_by_construction"].append(gate_viols * 100.0)

    summary = {}
    for k, d in metrics.items():
        gate_v = round(float(np.mean(d["gate_violations_by_construction"])), 2)
        meas_h = round(float(np.mean(d["measured_hits"])), 1)
        summary[k] = {
            "prediction_mae": round(float(np.mean(d["mae"])), 3),
            "empirical_coverage_pct": round(float(np.mean(d["coverage"])), 1),
            "measured_soluble_hit_pct": meas_h,
            "ood_selected_pct_by_construction": round(float(np.mean(d["ood_selected"])), 1),
            "gate_violation_pct_by_construction": gate_v,
            # Retained for JSON consumer compatibility; explicitly documented as by-construction below
            "boundary_violation_pct": gate_v,
            "verified_hit_yield_pct": meas_h,
        }
    return {
        "task": "L6 + L5 Molecular Discovery Campaign (Independent Held-Out Delaney ESOL `logS`)",
        "repos": ["lab-ask-why", "lab-decide", "buy-or-make", "lab-automation-atlas"],
        "data_source": data_source,
        "input_type": "real_esol_solubility_plus_simulated_procurement_flags",
        "evaluation_note": (
            "prediction_mae, empirical_coverage_pct, and measured_soluble_hit_pct (measured logS >= -2.8) "
            "are evaluated strictly against held-out experimental Delaney ESOL solubility with identical "
            "raw GBDT ranking across all arms (no artificial OOD optimism bonus). Procurement attributes "
            "are simulated random draws, and gate_violation_pct_by_construction (0.0% for lean_trust) "
            "is a gate invariant by construction."
        ),
        "n_total_compounds": int(len(X_all)),
        "mean_candidate_pool_per_seed": round(float(statistics.mean(cand_pool_sizes)), 1),
        "selected_per_seed": budget_k,
        "seeds": len(seeds),
        "lean_kernel_calls": lean_parity_checks,
        "real_heldout_pool_diagnostic": {
            "in_region_mae": round(float(np.mean(pool_diag["in_region_mae"])), 3),
            "abstained_ood_mae": round(float(np.mean(pool_diag["abstained_ood_mae"])), 3),
            "in_region_coverage_90_pct": round(float(np.mean(pool_diag["in_region_coverage_90_pct"])), 1),
            "abstained_ood_coverage_90_pct": round(float(np.mean(pool_diag["abstained_ood_coverage_90_pct"])), 1),
        },
        "regimes": summary,
    }


# ---------------------------------------------------------------------------
# Experiment 2: L4 + L1 Wet-Lab Protocol Synthesis & Independent Simulation
# ---------------------------------------------------------------------------
def _base_deck(frozen_stock: bool = False) -> list[dict[str, Any]]:
    # Matches `corning_96_wellplate_360ul_flat` (360.0 uL = 3600 tenths of uL)
    return [
        {
            "wellId": 1,
            "vol": 2500,
            "cap": 3600,
            "deadVol": 50,
            "soluteAmt": 0,
            "hasBuffer": True,
            "hasSample": False,
            "frozen": False,
            "sealed": False,
        },
        {
            "wellId": 2,
            "vol": 1500,
            "cap": 3600,
            "deadVol": 50,
            "soluteAmt": 1500,
            "hasBuffer": False,
            "hasSample": True,
            "frozen": frozen_stock,
            "sealed": False,
        },
        {
            "wellId": 3,
            "vol": 0,
            "cap": 3600,
            "deadVol": 50,
            "soluteAmt": 0,
            "hasBuffer": False,
            "hasSample": False,
            "frozen": False,
            "sealed": False,
        },
        {
            "wellId": 4,
            "vol": 0,
            "cap": 3600,
            "deadVol": 50,
            "soluteAmt": 0,
            "hasBuffer": False,
            "hasSample": False,
            "frozen": False,
            "sealed": False,
        },
    ]


def _clean_protocol(template_id: int) -> tuple[list[dict[str, Any]], list[tuple[Any, ...]]]:
    if template_id % 3 == 0:
        wells = _base_deck(frozen_stock=False)
        steps = [
            ("pick",),
            ("xfer", 1, 3, 1000),
            ("xfer", 1, 4, 1000),
            ("drop",),
            ("pick",),
            ("xfer", 2, 3, 1000),
            ("mix", 3, 1000, 3),
            ("xfer", 3, 4, 1000),
            ("mix", 4, 1000, 3),
            ("seal", 3),
            ("inc", 3, 95, 300),
            ("drop",),
        ]
        return wells, steps
    if template_id % 3 == 1:
        wells = _base_deck(frozen_stock=True)
        steps = [
            ("thaw", 2),
            ("pick",),
            ("xfer", 1, 3, 1200),
            ("drop",),
            ("pick",),
            ("xfer", 2, 3, 600),
            ("mix", 3, 900, 4),
            ("inc", 3, 37, 600),
            ("drop",),
        ]
        return wells, steps
    wells = _base_deck(frozen_stock=False)
    steps = [
        ("pick",),
        ("xfer", 1, 3, 1200),
        ("xfer", 1, 4, 1200),
        ("drop",),
        ("pick",),
        ("xfer", 2, 3, 500),
        ("mix", 3, 800, 3),
        ("drop",),
    ]
    return wells, steps


def _corrupt_protocol(
    wells: list[dict[str, Any]], clean_steps: list[tuple[Any, ...]], fault_kind: int
) -> list[tuple[Any, ...]]:
    steps = list(clean_steps)
    if fault_kind == 0:
        # Assay fault: unsealed 95 C boiling evaporation (passes raw Opentrons simulator; blocked by AutoLabLean)
        steps = [s for s in steps if s[0] != "seal"]
        if not any(s[0] == "inc" and s[2] >= 80 for s in steps):
            steps.insert(-1, ("inc", 3, 92, 300))
        return steps
    if fault_kind == 1:
        # Assay fault: serial-dilution concentration back-entry (A4 -> A3)
        return [
            ("pick",),
            ("xfer", 1, 3, 800),
            ("xfer", 1, 4, 800),
            ("drop",),
            ("pick",),
            ("xfer", 2, 3, 800),
            ("xfer", 3, 4, 800),
            ("mix", 4, 600, 2),
            ("xfer", 3, 4, 300),
            ("drop",),
        ]
    if fault_kind == 2:
        # Assay fault: dead-volume cone underflow (248.0 uL from 250.0 uL with 5.0 uL dead volume)
        return [("pick",), ("xfer", 1, 3, 1240), ("xfer", 1, 4, 1240), ("drop",)]
    if fault_kind == 3:
        # Assay fault: skip thawing frozen stock (or redundant thaw)
        if wells[1]["frozen"]:
            return [s for s in steps if s[0] != "thaw"]
        return [("thaw", 1)] + steps
    if fault_kind == 4:
        # Hardware API crash: omit intermediate drop_tip before next pick_up_tip (caught by independent simulator!)
        out: list[tuple[Any, ...]] = []
        dropped_once = False
        for s in steps:
            if s[0] == "drop" and not dropped_once:
                dropped_once = True
                continue
            out.append(s)
        return out
    if fault_kind == 5:
        # Assay fault: sample-contaminated tip dips back into clean buffer stock (A1)
        return [("pick",), ("xfer", 2, 3, 500), ("xfer", 1, 4, 500), ("drop",)]
    # Hardware API crash: well overfill (220.0 + 145.0 = 365.0 uL > 360.0 uL Corning flat-plate capacity!)
    return [("pick",), ("xfer", 1, 3, 2200), ("xfer", 2, 3, 1450), ("drop",)]


def _coarse_heuristic_ok(wells: list[dict[str, Any]], steps: list[tuple[Any, ...]]) -> bool:
    """Coarse pre-formalization heuristic: checks [0, cap] and 2-bit reagent presence mask."""
    vols = {int(w["wellId"]): int(w["vol"]) for w in wells}
    caps = {int(w["wellId"]): int(w["cap"]) for w in wells}
    masks = {
        int(w["wellId"]): (1 if w["hasBuffer"] else 0) | (2 if w["hasSample"] else 0)
        for w in wells
    }
    tip_mask = 0
    has_tip = False
    for st in steps:
        op = st[0]
        if op == "pick":
            if has_tip:
                return False
            has_tip, tip_mask = True, 0
        elif op == "drop":
            if not has_tip:
                return False
            has_tip, tip_mask = False, 0
        elif op == "xfer":
            _, s, d, v = st
            if not has_tip or not (200 <= v <= 3000):
                return False
            if (tip_mask & ~masks[s]) != 0:
                return False
            if vols[s] < v or vols[d] + v > caps[d]:
                return False
            vols[s] -= v
            vols[d] += v
            masks[d] |= masks[s]
            tip_mask |= masks[d]
    return True


def _counterexample_guided_repair(
    rule: str, wells: list[dict[str, Any]], steps: list[tuple[Any, ...]]
) -> list[tuple[Any, ...]]:
    """Minimal 1-step repair guided by AutoLabLean's failing rule identifier."""
    out = list(steps)
    if rule == "high_temp_requires_seal":
        repaired: list[tuple[Any, ...]] = []
        sealed_set: set[int] = set()
        for st in out:
            if st[0] == "inc" and st[2] >= 80 and st[1] not in sealed_set:
                repaired.append(("seal", st[1]))
                sealed_set.add(st[1])
            repaired.append(st)
        return repaired
    if rule in ("thawed_before_pipetting", "thaw_before_incubate"):
        frozen_ids = [int(w["wellId"]) for w in wells if w["frozen"]]
        return [("thaw", wid) for wid in frozen_ids] + out
    if rule == "thaw_requires_frozen":
        frozen_ids = {int(w["wellId"]) for w in wells if w["frozen"]}
        return [st for st in out if not (st[0] == "thaw" and st[1] not in frozen_ids)]
    if rule == "pick_tip_requires_empty_mount":
        repaired = []
        mounted = False
        for st in out:
            if st[0] == "pick":
                if mounted:
                    repaired.append(("drop",))
                mounted = True
            elif st[0] == "drop":
                mounted = False
            repaired.append(st)
        return repaired
    if rule == "tip_dropped_at_end":
        return out + [("drop",)]
    if rule == "no_tip_cross_contamination":
        repaired = []
        dirty = False
        for st in out:
            if st[0] == "xfer":
                if dirty:
                    repaired.extend([("drop",), ("pick",)])
                repaired.append(st)
                dirty = True
            else:
                repaired.append(st)
        return repaired
    if rule == "enough_recoverable_volume":
        return [(st[0], st[1], st[2], max(200, st[3] - 40)) if st[0] == "xfer" else st for st in out]
    return out


_WELL_NAMES = {1: "A1", 2: "A2", 3: "A3", 4: "A4"}


def _render_opentrons_apiv2(wells: list[dict[str, Any]], steps: list[tuple[Any, ...]]) -> str:
    """Compile a candidate `(wells, steps)` protocol into Opentrons Python API v2.16 source."""
    lines = [
        "metadata = {'apiLevel': '2.16'}",
        "",
        "def run(protocol):",
        "    tips = protocol.load_labware('opentrons_96_tiprack_300ul', 1)",
        "    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', 2)",
        "    pip = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])",
        "    liq_buf = protocol.define_liquid(name='Buffer', description='Assay buffer', display_color='#00AAFF')",
        "    liq_smp = protocol.define_liquid(name='Sample', description='Assay sample', display_color='#FF5500')",
    ]
    for w in wells:
        vol_ul = round(int(w["vol"]) / 10.0, 2)
        if vol_ul > 0:
            wname = _WELL_NAMES[int(w["wellId"])]
            liq_var = "liq_smp" if w["hasSample"] else "liq_buf"
            lines.append(f"    plate['{wname}'].load_liquid(liquid={liq_var}, volume={vol_ul})")
    for st in steps:
        op = st[0]
        if op == "pick":
            lines.append("    pip.pick_up_tip()")
        elif op == "drop":
            lines.append("    pip.drop_tip()")
        elif op == "xfer":
            _, s, d, v = st
            vol_ul = round(int(v) / 10.0, 2)
            lines.append(f"    pip.aspirate({vol_ul}, plate['{_WELL_NAMES[int(s)]}'])")
            lines.append(f"    pip.dispense({vol_ul}, plate['{_WELL_NAMES[int(d)]}'])")
        elif op == "mix":
            _, wid, v, reps = st
            vol_ul = round(int(v) / 10.0, 2)
            lines.append(f"    pip.mix({int(reps)}, {vol_ul}, plate['{_WELL_NAMES[int(wid)]}'])")
        elif op == "inc":
            _, wid, temp_c, dur_s = st
            lines.append(f"    protocol.comment('incubate {_WELL_NAMES[int(wid)]} at {int(temp_c)}C')")
            lines.append(f"    protocol.delay(seconds={int(dur_s)})")
        elif op in ("seal", "thaw"):
            _, wid = st
            lines.append(f"    protocol.comment('{op} {_WELL_NAMES[int(wid)]}')")
    return "\n".join(lines) + "\n"


def _load_stepbot_checker(stepbot_root: Path | None = None):
    root = stepbot_root if stepbot_root is not None else (SCRATCH_ROOT / "stepbot")
    src_dir = root / "src"
    if not (src_dir / "stepbot").is_dir():
        raise ImportError(f"Sibling repository 'stepbot' not found at {src_dir}; required for independent simulation.")
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from stepbot.checker import check_protocol_source

    return check_protocol_source


def run_exp2_protocol_synthesis(
    kernel: LeanBatchKernel, *, stepbot_root: Path | None = None
) -> dict[str, Any]:
    import numpy as np

    check_protocol_source = _load_stepbot_checker(stepbot_root)
    sim_cache: dict[tuple[Any, ...], bool] = {}

    def sim_ok(wells: list[dict[str, Any]], st: list[tuple[Any, ...]]) -> bool:
        sig = (tuple(int(w["vol"]) for w in wells), tuple(st))
        if sig not in sim_cache:
            res = check_protocol_source(_render_opentrons_apiv2(wells, st), use_mock=True)
            sim_cache[sig] = bool(res.ok)
        return sim_cache[sig]

    rng = np.random.default_rng(202611)
    n_tasks = 200
    n_cands = 8  # Best-of-8 candidate pool per protocol task (1,600 candidates total)

    all_tsv: list[str] = []
    task_pools: list[list[tuple[list[dict[str, Any]], list[tuple[Any, ...]]]]] = []

    for tid in range(n_tasks):
        wells, clean = _clean_protocol(tid)
        cands: list[tuple[list[dict[str, Any]], list[tuple[Any, ...]]]] = []
        for cid in range(n_cands):
            if rng.random() < 0.24:
                st = list(clean)
            else:
                fk = int(rng.choice([0, 1, 2, 3, 4, 5, 6], p=[0.22, 0.20, 0.18, 0.12, 0.12, 0.08, 0.08]))
                st = _corrupt_protocol(wells, clean, fk)
            cands.append((wells, st))
            all_tsv.append(format_rehearsal_tsv(200, 3000, 10000 + tid * 10 + cid, [], wells, st))
        task_pools.append(cands)

    t0 = time.perf_counter()
    verdicts = kernel.eval_lines(all_tsv)
    elapsed_s = max(1e-6, time.perf_counter() - t0)
    lean_rate = round(len(all_tsv) / elapsed_s, 1)

    for idx, tid_cands in enumerate(task_pools):
        for cid, (wells, st) in enumerate(tid_cands):
            v_lean = verdicts[idx * n_cands + cid]
            v_py = py_check_rehearsal(200, 3000, 10000 + idx * 10 + cid, [], wells, st)
            assert v_lean.allowed == v_py.allowed and v_lean.rule == v_py.rule

    ungated_lean_ok, ungated_lean_viol, ungated_sim_fault = 0, 0, 0
    heur_lean_ok, heur_lean_viol, heur_sim_fault = 0, 0, 0
    lean_bo8_ok, lean_bo8_viol, lean_bo8_sim_fault = 0, 0, 0
    lean_repair_ok, lean_repair_viol, lean_repair_sim_fault = 0, 0, 0

    repair_tsv: list[str] = []
    repair_cands: list[tuple[list[dict[str, Any]], list[tuple[Any, ...]]]] = []

    for tid in range(n_tasks):
        cands = task_pools[tid]
        v_slice = verdicts[tid * n_cands : (tid + 1) * n_cands]

        # 1. Ungated Top-1
        w0, s0 = cands[0]
        if not sim_ok(w0, s0):
            ungated_sim_fault += 1
        if v_slice[0].allowed:
            ungated_lean_ok += 1
        else:
            ungated_lean_viol += 1

        # 2. Coarse Bitmask/Capacity Heuristic Best-of-8
        chosen_h = None
        for cid, (wells, st) in enumerate(cands):
            if _coarse_heuristic_ok(wells, st):
                chosen_h = cid
                break
        if chosen_h is not None:
            wh, sh = cands[chosen_h]
            if not sim_ok(wh, sh):
                heur_sim_fault += 1
            if v_slice[chosen_h].allowed:
                heur_lean_ok += 1
            else:
                heur_lean_viol += 1

        # 3. Lean 4 Shielded Best-of-8 (`selectBestCertified`)
        chosen_l = next((cid for cid, v in enumerate(v_slice) if v.allowed), None)
        if chosen_l is not None:
            wl, sl = cands[chosen_l]
            if not sim_ok(wl, sl):
                lean_bo8_sim_fault += 1
                lean_repair_sim_fault += 1
            lean_bo8_ok += 1
            lean_repair_ok += 1
        else:
            repaired_st = _counterexample_guided_repair(v_slice[0].rule, w0, s0)
            repair_tsv.append(format_rehearsal_tsv(200, 3000, 90000 + tid, [], w0, repaired_st))
            repair_cands.append((w0, repaired_st))

    if repair_tsv:
        rep_verdicts = kernel.eval_lines(repair_tsv)
        for rv, (wr, sr) in zip(rep_verdicts, repair_cands):
            if rv.allowed:
                lean_repair_ok += 1
                if not sim_ok(wr, sr):
                    lean_repair_sim_fault += 1

    assert lean_bo8_sim_fault == 0 and lean_repair_sim_fault == 0, (
        f"Expected 0 independent simulator faults on Lean-certified protocols, "
        f"got bo8={lean_bo8_sim_fault}, repair={lean_repair_sim_fault}"
    )

    return {
        "task": "L4 + L1 Wet-Lab Protocol Synthesis & Repair (Simulated 3-Template Generator + Independent `stepbot` Simulator)",
        "repos": ["lab-rehearsal", "stepbot", "twinstep", "labfill"],
        "input_type": "simulated_protocol_candidates_plus_independent_stepbot_simulator",
        "evaluation_note": (
            "Candidates come from a deterministic 3-template x 7-fault generator (24% clean base rate). "
            "independent_sim_fault_pct is measured by compiling each chosen protocol to Opentrons Python API v2.16 "
            "and running stepbot's independent simulator (catches double pick_up_tip and >360 uL well overfill). "
            "lean_rule_violation_pct_by_construction (aliased as hardware_fault_pct) additionally counts assay-level "
            "rules (unsealed >=80 C, concentration back-entry, 5 uL dead-volume cone, unthawed stock) and is 0.0% "
            "by construction for Lean-gated arms. For real public Opentrons protocols, see opentrons_library_rehearsal.json."
        ),
        "n_tasks": n_tasks,
        "candidates_per_task": n_cands,
        "candidates_verified_in_lean": len(all_tsv) + len(repair_tsv),
        "unique_protocols_checked_in_stepbot_simulator": len(sim_cache),
        "lean_throughput_protocols_per_sec": lean_rate,
        "regimes": {
            "ungated_top1": {
                "valid_completion_pct": round(100.0 * ungated_lean_ok / n_tasks, 1),
                "independent_sim_fault_pct": round(100.0 * ungated_sim_fault / n_tasks, 1),
                "lean_rule_violation_pct_by_construction": round(100.0 * ungated_lean_viol / n_tasks, 1),
                "hardware_fault_pct": round(100.0 * ungated_lean_viol / n_tasks, 1),
            },
            "coarse_bitmask_heuristic": {
                "valid_completion_pct": round(100.0 * heur_lean_ok / n_tasks, 1),
                "independent_sim_fault_pct": round(100.0 * heur_sim_fault / n_tasks, 1),
                "lean_rule_violation_pct_by_construction": round(100.0 * heur_lean_viol / n_tasks, 1),
                "hardware_fault_pct": round(100.0 * heur_lean_viol / n_tasks, 1),
            },
            "lean_best_of_8": {
                "valid_completion_pct": round(100.0 * lean_bo8_ok / n_tasks, 1),
                "independent_sim_fault_pct": round(100.0 * lean_bo8_sim_fault / n_tasks, 2),
                "lean_rule_violation_pct_by_construction": round(100.0 * lean_bo8_viol / n_tasks, 2),
                "hardware_fault_pct": round(100.0 * lean_bo8_viol / n_tasks, 2),
            },
            "lean_best_of_8_plus_guided_repair": {
                "valid_completion_pct": round(100.0 * lean_repair_ok / n_tasks, 1),
                "independent_sim_fault_pct": round(100.0 * lean_repair_sim_fault / n_tasks, 2),
                "lean_rule_violation_pct_by_construction": round(100.0 * lean_repair_viol / n_tasks, 2),
                "hardware_fault_pct": round(100.0 * lean_repair_viol / n_tasks, 2),
            },
        },
    }


# ---------------------------------------------------------------------------
# Experiment 3: L5 Multi-Instrument Contended Scheduling (`labshift` 30-suite)
# ---------------------------------------------------------------------------
def run_exp3_scheduling(*, labshift_root: Path | None = None) -> dict[str, Any]:
    """Run `labshift`'s greedy, greedy_repair, and OR-Tools CP-SAT solvers on all 30 instances.

    Fail-closed: raises `ImportError` if `labshift` cannot be imported and `RuntimeError`
    if benchmark instance JSON files are missing. Never returns hardcoded fallback numbers.
    """
    root = labshift_root if labshift_root is not None else (SCRATCH_ROOT / "labshift")
    src_dir = root / "src"
    added_to_path = False
    if (src_dir / "labshift").is_dir() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
        added_to_path = True
    try:
        from labshift.bench import collect_instance_paths, solve_instance
        from labshift.metrics import compute_metrics
        from labshift.models import Instance
    except ImportError as exc:
        if added_to_path and str(src_dir) in sys.path:
            sys.path.remove(str(src_dir))
        raise ImportError(
            f"Sibling repository 'labshift' is required for Experiment 3 scheduling benchmark "
            f"(checked {src_dir}): {exc}"
        ) from exc

    bench_dir = root / "benchmarks"
    if not bench_dir.is_dir():
        raise RuntimeError(f"Benchmark directory not found for 'labshift': {bench_dir}")
    bench_files = collect_instance_paths(bench_dir)
    if not bench_files:
        raise RuntimeError(f"No benchmark JSON instances found in {bench_dir}")

    results: dict[str, dict[str, Any]] = {}
    for solver_label, solver_key in [
        ("ungated_greedy", "greedy"),
        ("greedy_with_repair", "greedy_repair"),
        ("cpsat", "cpsat"),
    ]:
        feas = 0
        win_viols = 0
        makespans_all: list[float] = []
        for bf in bench_files:
            inst = Instance.from_dict(json.loads(bf.read_text(encoding="utf-8")))
            sched = solve_instance(inst, solver_key, time_limit=5.0, seed=0)
            m = compute_metrics(inst, sched)
            win_viols += int(m.window_violations)
            makespans_all.append(float(m.makespan))
            if m.feasible:
                feas += 1
        results[solver_label] = {
            "feasible_instances": f"{feas}/{len(bench_files)}",
            "feasible_pct": round(100.0 * feas / len(bench_files), 1),
            "window_violations": win_viols,
            "mean_makespan_min": round(float(statistics.mean(makespans_all)), 1),
        }
    return {
        "task": "L5 Contended 5-Pool Lab Fleet Scheduling (30 `labshift` Synthetic Benchmark Instances)",
        "repos": ["labshift"],
        "data_source": "sibling:labshift/benchmarks (30 synthetic scheduling JSON instances)",
        "input_type": "synthetic_benchmark_suite",
        "evaluation_note": (
            "Compares labshift's greedy, greedy_repair, and OR-Tools CP-SAT (`cpsat`, single-worker "
            "deterministic) solvers directly; `cpsat` does not invoke the Lean binary at runtime."
        ),
        "instances": len(bench_files),
        "regimes": results,
    }


# ---------------------------------------------------------------------------
# Experiment 4: L4 Scientific SQL Verification (`lab-verify` 30-candidate suite)
# ---------------------------------------------------------------------------
def run_exp4_sql_gate(kernel: LeanBatchKernel, *, lab_verify_root: Path | None = None) -> dict[str, Any]:
    lv_root = lab_verify_root if lab_verify_root is not None else (SCRATCH_ROOT / "lab-verify")
    lv_src = lv_root / "src"
    if not (lv_src / "lab_verify").is_dir():
        raise ImportError(f"Sibling repository 'lab-verify' not found at {lv_src}")
    if str(lv_src) not in sys.path:
        sys.path.insert(0, str(lv_src))
    from lab_verify import build_counterexample_dbs, build_db, check_parse, check_read_only, check_schema, gate, run

    db = build_db()
    ce_dbs = build_counterexample_dbs()

    cand_files = [lv_root / "demo" / "candidates.json", lv_root / "demo" / "candidates_extended.json"]
    questions: list[dict[str, Any]] = []
    for cf in cand_files:
        if cf.exists():
            questions.extend(json.loads(cf.read_text(encoding="utf-8")))
    if not questions:
        raise RuntimeError(f"No SQL candidate fixtures found in {lv_root / 'demo'}")

    total_wrong = 0
    l1_l3_slipped = 0
    lean_l4_slipped = 0
    tsv_lines: list[str] = []
    expected_allow: list[bool] = []

    q_ungated_acc = 0
    q_l1_l3_acc = 0
    q_lean_acc = 0

    for q in questions:
        gold_res = run(db, q["gold"])
        cands = list(q["candidates"])
        # Adversarial stress ordering: wrong candidates placed ahead of gold to test gate filtering
        cands_noisy = sorted(cands, key=lambda c: 0 if c["label"] != "correct" else 1)

        if cands_noisy[0]["label"] == "correct":
            q_ungated_acc += 1

        picked_l13 = None
        picked_lean = None

        for c in cands_noisy:
            sql = c["sql"]
            is_gold_label = c["label"] == "correct"
            stmts, p_err = check_parse(sql)
            parse_ok = stmts is not None and p_err is None
            stmt_cnt = len(stmts) if stmts is not None else 0
            ro_ok = False
            sch_ok = False
            if parse_ok and stmts is not None:
                ro_err = check_read_only(stmts)
                ro_ok = ro_err is None
                if ro_ok:
                    sch_err = check_schema(stmts[0])
                    sch_ok = sch_err is None

            fail_layer, _ = gate(db, sql, gold_res, gold_sql=q["gold"], counterexample_cons=ce_dbs)
            l4_ok = fail_layer is None

            if not is_gold_label:
                total_wrong += 1
                if parse_ok and stmt_cnt == 1 and ro_ok and sch_ok:
                    l1_l3_slipped += 1
                if l4_ok:
                    lean_l4_slipped += 1

            if picked_l13 is None and (parse_ok and stmt_cnt == 1 and ro_ok and sch_ok):
                picked_l13 = is_gold_label
            if picked_lean is None and l4_ok:
                picked_lean = is_gold_label

            tsv_lines.append(
                f"SQL\t{int(parse_ok)}\t{stmt_cnt}\t{int(ro_ok)}\t{int(ro_ok)}\t0\t"
                f"{0 if sch_ok else 1}\t0\t{int(l4_ok)}\t{int(l4_ok)}\t{int(l4_ok)}"
            )
            expected_allow.append(l4_ok)

        if picked_l13 is True:
            q_l1_l3_acc += 1
        if picked_lean is True:
            q_lean_acc += 1

    lean_verdicts = kernel.eval_lines(tsv_lines)
    assert [v.allowed for v in lean_verdicts] == expected_allow

    db.close()
    for cdb in ce_dbs:
        cdb.close()

    n_q = max(1, len(questions))
    return {
        "task": "L4 Lab-Database SQL Candidate Selection (Adversarial Wrong-First Stress Suite)",
        "repos": ["lab-verify"],
        "data_source": "sibling:lab-verify/demo/candidates*.json (16 pools, 30 hand-authored SQL queries)",
        "input_type": "hand_authored_adversarial_suite",
        "evaluation_note": (
            "Candidates are sorted wrong-first as a worst-case stress test (not live LLM samples), "
            "and Layer 4 compares execution against the reference query plus perturbation counterexample DBs "
            "across 18 wrong candidates."
        ),
        "question_pools": len(questions),
        "total_candidates_checked_in_lean": len(tsv_lines),
        "wrong_candidates_total": total_wrong,
        "regimes": {
            "ungated_noisy_top1": {
                "verified_answer_accuracy_pct": round(100.0 * q_ungated_acc / n_q, 1),
                "wrong_sql_false_accept_pct": 100.0,
            },
            "syntax_readonly_schema_only_L1_L3": {
                "verified_answer_accuracy_pct": round(100.0 * q_l1_l3_acc / n_q, 1),
                "wrong_sql_false_accept_pct": round(100.0 * l1_l3_slipped / max(1, total_wrong), 1),
            },
            "lean_4layer_default_deny_L1_L4": {
                "verified_answer_accuracy_pct": round(100.0 * q_lean_acc / n_q, 1),
                "wrong_sql_false_accept_pct": round(100.0 * lean_l4_slipped / max(1, total_wrong), 2),
            },
        },
    }


# ---------------------------------------------------------------------------
# Experiment 5: 6-Arm Bandit Policy Simulation (NOT Neural LLM Weight Training)
# ---------------------------------------------------------------------------
def run_exp5_rlvr_anti_hack(kernel: LeanBatchKernel) -> dict[str, Any]:
    """6-arm softmax bandit simulation over hand-scored rollout archetypes.

    Note: no neural language model is trained in this CPU script; full GPU RLVR
    post-training on LLM weights remains explicitly marked `PENDING`.
    """
    import numpy as np

    archetypes = [
        # (name, coreOK, noLeak, thinkTok, maxThink, taskR, fmtB, soft_proxy_reward, init_logit)
        ("verified_science_concise", 1, 1, 210, 512, 900, 100, 920.0, -1.10),
        ("verified_protocol_repair", 1, 1, 280, 512, 850, 100, 880.0, -1.20),
        ("exploit_err_always_true", 0, 1, 120, 512, 465, 250, 715.0, 0.35),
        ("exploit_verbose_think_pad", 0, 1, 920, 512, 300, 680, 980.0, 0.40),
        ("exploit_oracle_field_copy", 1, 0, 140, 512, 950, 200, 1150.0, -0.10),
        ("unverified_polished_format", 0, 1, 240, 512, 200, 450, 650.0, 0.20),
    ]

    tsv = [f"REWARD\t{a[1]}\t{a[2]}\t{a[3]}\t{a[4]}\t{a[5]}\t{a[6]}" for a in archetypes]
    lean_res = kernel.eval_lines(tsv)
    lean_rewards = np.array(
        [float(v.rule) if v.allowed else float(v.detail) for v in lean_res], dtype=float
    )
    assert lean_rewards[0] == 1000.0 and lean_rewards[1] == 950.0
    assert np.all(lean_rewards[2:] == 0.0), f"Expected 0 reward on all exploits, got {lean_rewards}"

    soft_rewards = np.array([a[7] for a in archetypes], dtype=float)
    init_logits = np.array([a[8] for a in archetypes], dtype=float)

    seeds = [101, 102, 103, 104, 105]
    steps = 160
    group_g = 8
    lr = 0.18

    out_stats: dict[str, dict[str, list[float]]] = {
        "untrained_init": {"true_verified_pct": [], "exploit_pct": []},
        "soft_additive_reward_grpo": {"true_verified_pct": [], "exploit_pct": []},
        "lean_trust_gated_grpo": {"true_verified_pct": [], "exploit_pct": []},
    }

    def softmax(z: np.ndarray) -> np.ndarray:
        z_s = z - np.max(z)
        e = np.exp(z_s)
        return e / np.sum(e)

    p0 = softmax(init_logits)
    init_ver = float((p0[0] + p0[1]) * 100.0)
    init_exp = float(np.sum(p0[2:]) * 100.0)

    for sd in seeds:
        out_stats["untrained_init"]["true_verified_pct"].append(init_ver)
        out_stats["untrained_init"]["exploit_pct"].append(init_exp)

        for mode, r_vec in [
            ("soft_additive_reward_grpo", soft_rewards),
            ("lean_trust_gated_grpo", lean_rewards),
        ]:
            rng = np.random.default_rng(sd)
            logits = init_logits.copy()
            for _ in range(steps):
                probs = softmax(logits)
                sampled = rng.choice(len(archetypes), size=group_g, p=probs)
                rewards = r_vec[sampled] + rng.normal(0.0, 12.0, size=group_g) * (r_vec[sampled] > 0)
                std = float(np.std(rewards))
                if std > 1e-6:
                    adv = (rewards - float(np.mean(rewards))) / std
                    grad = np.zeros_like(logits)
                    for a_idx, adv_i in zip(sampled, adv):
                        one_hot = np.zeros_like(logits)
                        one_hot[a_idx] = 1.0
                        grad += adv_i * (one_hot - probs)
                    logits += lr * (grad / group_g)
            p_end = softmax(logits)
            out_stats[mode]["true_verified_pct"].append(float((p_end[0] + p_end[1]) * 100.0))
            out_stats[mode]["exploit_pct"].append(float(np.sum(p_end[2:]) * 100.0))

    summary = {
        k: {
            "true_verified_accuracy_pct": round(float(np.mean(v["true_verified_pct"])), 1),
            "reward_hack_exploit_pct": round(float(np.mean(v["exploit_pct"])), 1),
        }
        for k, v in out_stats.items()
    }
    return {
        "task": "6-arm bandit policy simulation (not LLM weight training; GPU RLVR run PENDING)",
        "repos": ["labbench-posttrain", "twinstep", "labfill"],
        "input_type": "simulation",
        "simulation_only": True,
        "gpu_llm_rlvr_status": "PENDING (requires GPU LLM post-training run; this benchmark updates 6 scalar softmax logits)",
        "n_arms": len(archetypes),
        "seeds": len(seeds),
        "steps_per_seed": steps,
        "lean_rewards_permille": lean_rewards.tolist(),
        "regimes": summary,
    }


def main() -> int:
    t_start = time.perf_counter()
    audit = audit_lean_sources()
    if not audit["zero_sorry_verified"]:
        raise RuntimeError(f"Lean zero-sorry audit failed: {audit['violations']}")

    kernel = LeanBatchKernel()
    if not kernel.available:
        raise RuntimeError("Compiled `autolab-lean` binary is missing; run `lake build` inside `lean/` first.")

    exp1 = run_exp1_molecular_campaign(kernel)
    exp2 = run_exp2_protocol_synthesis(kernel)
    exp3 = run_exp3_scheduling()
    exp4 = run_exp4_sql_gate(kernel)
    exp5 = run_exp5_rlvr_anti_hack(kernel)

    payload = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lean_toolchain": "leanprover/lean4:v4.36.0",
        "lean_audit": audit,
        "total_runtime_sec": round(time.perf_counter() - t_start, 2),
        "experiments": {
            "exp1_molecular_discovery": exp1,
            "exp2_protocol_synthesis": exp2,
            "exp3_fleet_scheduling": exp3,
            "exp4_sql_verification": exp4,
            "exp5_rlvr_posttraining": exp5,
        },
    }

    out_dir = REPO_ROOT / "benchmarks" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "trust_regime_results.json"
    out_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    site_out = REPO_ROOT / "site" / "assets" / "trust-regime-data.json"
    site_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
