"""Frontier Study: Four Novel Research Directions Synthesized from 2025-2026 Ecosystem Gaps.

Invokes the compiled `autolab-lean --batch-tsv` Lean 4.36.0 executable (`ATTRIB`,
`FRONTIER`, `MCP`, `REHEARSAL`) across four quantitative experiments:

1. Direction 1 - Diagnostic Epistemic Attribution & Proof-Carrying Negative Results
   (real Delaney ESOL compounds + simulated separable fault telemetry)
2. Direction 2 - Stepped Frontier Calibration (`(1 + eta) * tau` micro-scale stepping-stones
   expanding trusted chemical space across real Delaney ESOL scaffolds)
3. Direction 3 - Proof-Carrying `Lean-MCP` Hardware Envelopes (72h discrete-event clock
   simulation vs per-run human approval gates)
4. Direction 4 - Fixed Fault-Family Mutation Check (21 distinct cases: 3 templates x 7
   fault classes, evaluated across 140 cyclic draws against Gen-0 / Gen-1 / Gen-2 verifiers)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = REPO_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autolab.datasets import load_esol_dataset  # noqa: E402
from autolab.trust_regime import LeanBatchKernel, audit_lean_sources, conformal_rank_permille  # noqa: E402


def _load_esol_arrays() -> tuple[Any, Any, str]:
    import numpy as np

    features, targets, source_desc = load_esol_dataset()
    return np.asarray(features, dtype=float), np.asarray(targets, dtype=float), source_desc


# ---------------------------------------------------------------------------
# Direction 1: Causal Blame Calculus & Proof-Carrying Negative Results
# ---------------------------------------------------------------------------
def run_direction1_epistemic_attribution(kernel: LeanBatchKernel) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler

    X, y, src = _load_esol_arrays()
    seeds = [7, 17, 27, 37, 47]
    rounds = 6
    batch_per_round = 16  # 96 assays per campaign
    hit_thresh = -0.8     # Selective high-solubility hit bar (~top 18% of ESOL: log mol/L >= -0.8)

    stats = {
        "naive_sdl": {"false_discovery_pct": [], "poisoned_negatives": [], "final_test_mae": [], "true_hits_found": []},
        "lean_attribution_sdl": {"false_discovery_pct": [], "poisoned_negatives": [], "final_test_mae": [], "true_hits_found": []},
    }
    total_lean_calls = 0

    for sd in seeds:
        rng = np.random.default_rng(sd)
        perm = rng.permutation(len(X))
        init_idx = perm[:120]
        test_idx = perm[120:280]
        pool_master = list(perm[280:])

        for mode in ("naive_sdl", "lean_attribution_sdl"):
            rng_m = np.random.default_rng(sd * 100 + (1 if mode == "lean_attribution_sdl" else 0))
            tr_X = list(X[init_idx])
            tr_y = list(y[init_idx])
            avail = list(pool_master)
            claimed_hits: list[int] = []
            poisoned_count = 0

            for _r in range(rounds):
                scaler = StandardScaler().fit(np.asarray(tr_X))
                reg = GradientBoostingRegressor(random_state=sd, n_estimators=90, max_depth=3)
                reg.fit(scaler.transform(np.asarray(tr_X)), np.asarray(tr_y))

                preds = reg.predict(scaler.transform(X[avail]))
                pick_pos = list(np.argsort(-preds)[:batch_per_round])
                chosen_ids = [avail[p] for p in pick_pos]
                for cid in chosen_ids:
                    avail.remove(cid)

                # Simulate physical execution + analytical characterization on the chosen batch.
                # Note: fault telemetry is drawn from separable threshold regimes to test 4-way routing.
                tsv_lines: list[str] = []
                sim_obs: list[tuple[int, float, bool, bool]] = []
                for cid in chosen_ids:
                    u = rng_m.random()
                    if u < 0.20:
                        ac_ok = int(rng_m.random() >= 0.5)
                        pos_ok = 0 if ac_ok == 1 else 1
                        res_p, ovl_p = 45, 40
                        y_meas = -7.5 + float(rng_m.normal(0, 0.2))
                        is_exec_fault, is_ambig = True, False
                    elif u < 0.35:
                        ac_ok, pos_ok = 1, 1
                        res_p = int(rng_m.integers(110, 220))
                        ovl_p = int(rng_m.integers(240, 480))
                        y_meas = -0.3 + float(rng_m.normal(0, 0.15))
                        is_exec_fault, is_ambig = False, True
                    else:
                        ac_ok, pos_ok = 1, 1
                        res_p, ovl_p = int(rng_m.integers(20, 85)), int(rng_m.integers(15, 110))
                        y_meas = float(y[cid] + rng_m.normal(0, 0.12))
                        is_exec_fault, is_ambig = False, False

                    sig_hi = int(y_meas >= hit_thresh)
                    tsv_lines.append(f"ATTRIB\t1\t{ac_ok}\t1\t1\t{pos_ok}\t1\t{res_p}\t100\t{ovl_p}\t150\t{sig_hi}")
                    sim_obs.append((cid, y_meas, is_exec_fault, is_ambig))

                verdicts = kernel.eval_lines(tsv_lines)
                total_lean_calls += len(tsv_lines)

                for (cid, y_meas, is_exec_fault, _is_ambig), v in zip(sim_obs, verdicts):
                    tag = v.rule
                    if mode == "naive_sdl":
                        tr_X.append(X[cid])
                        tr_y.append(y_meas)
                        if is_exec_fault:
                            poisoned_count += 1
                        if y_meas >= hit_thresh:
                            claimed_hits.append(cid)
                    else:
                        if tag == "EXECUTION_ARTIFACT":
                            avail.append(cid)
                        elif tag == "AMBIGUOUS_CHARACTERIZATION":
                            y_orth = float(y[cid] + rng_m.normal(0, 0.10))
                            tr_X.append(X[cid])
                            tr_y.append(y_orth)
                            if y_orth >= hit_thresh:
                                claimed_hits.append(cid)
                        elif tag == "CERTIFIED_POSITIVE":
                            tr_X.append(X[cid])
                            tr_y.append(y_meas)
                            claimed_hits.append(cid)
                        elif tag == "CERTIFIED_NEGATIVE":
                            tr_X.append(X[cid])
                            tr_y.append(y_meas)

            scaler_f = StandardScaler().fit(np.asarray(tr_X))
            reg_f = GradientBoostingRegressor(random_state=sd, n_estimators=90, max_depth=3)
            reg_f.fit(scaler_f.transform(np.asarray(tr_X)), np.asarray(tr_y))
            final_mae = float(np.mean(np.abs(y[test_idx] - reg_f.predict(scaler_f.transform(X[test_idx])))))

            false_hits = sum(1 for cid in claimed_hits if y[cid] < hit_thresh - 0.25)
            true_hits = len({cid for cid in claimed_hits if y[cid] >= hit_thresh - 0.25})
            fdr = 100.0 * false_hits / max(1, len(claimed_hits))

            stats[mode]["false_discovery_pct"].append(fdr)
            stats[mode]["poisoned_negatives"].append(poisoned_count)
            stats[mode]["final_test_mae"].append(final_mae)
            stats[mode]["true_hits_found"].append(true_hits)

    return {
        "direction": "Direction 1 - Diagnostic Epistemic Attribution & Certified Negative Results",
        "inspired_by": "A-Lab XRD characterization debate, Sakana AI Scientist-v2 negative results, La Agente Optima sensor faults",
        "data_source": src,
        "input_type": "real_esol_plus_simulated_separable_telemetry",
        "evaluation_note": (
            "Compound descriptors and true solubility come from real Delaney ESOL (n=1,128); "
            "post-run acoustic/control/spectral fault telemetry is simulated from separable "
            "distributions, so 0.0% poisoned admission under ATTRIB reflects exact routing on modeled faults."
        ),
        "lean_kernel_calls": total_lean_calls,
        "comparison": {
            k: {
                "false_discovery_rate_pct": round(float(np.mean(d["false_discovery_pct"])), 1),
                "poisoned_records_admitted": round(float(np.mean(d["poisoned_negatives"])), 1),
                "post_campaign_surrogate_mae": round(float(np.mean(d["final_test_mae"])), 3),
                "verified_true_hits_discovered": round(float(np.mean(d["true_hits_found"])), 1),
            }
            for k, d in stats.items()
        },
    }


# ---------------------------------------------------------------------------
# Direction 2: Stepped Frontier Calibration (Active Trust-Boundary Expansion)
# ---------------------------------------------------------------------------
def run_direction2_stepped_frontier(kernel: LeanBatchKernel) -> dict[str, Any]:
    import numpy as np
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.neighbors import NearestNeighbors
    from sklearn.preprocessing import StandardScaler

    X, y, src = _load_esol_arrays()
    small_idx = np.where((X[:, 0] <= 175.0) & (X[:, 2] <= 1.0))[0]
    rest_idx = np.where(~((X[:, 0] <= 175.0) & (X[:, 2] <= 1.0)))[0]
    target_proto = np.array([265.0, 1.5, 2.5, 3.0, 65.0, 1.0])

    seeds = [11, 21, 31, 41, 51]
    rounds = 8
    probes_per_round = 22
    eta_pm = 320  # +32% certified annular stepping-stone shell (<= 350 cap)

    out = {
        "static_trust_wall_v1": {"trusted_space_pct": [], "novel_multiring_hits": [], "uncalibrated_prod_runs": [], "prod_coverage_pct": []},
        "undirected_shell_probes": {"trusted_space_pct": [], "novel_multiring_hits": [], "uncalibrated_prod_runs": [], "prod_coverage_pct": []},
        "goal_directed_chem_rrt_shell": {"trusted_space_pct": [], "novel_multiring_hits": [], "uncalibrated_prod_runs": [], "prod_coverage_pct": []},
        "unbounded_greedy_leap": {"trusted_space_pct": [], "novel_multiring_hits": [], "uncalibrated_prod_runs": [], "prod_coverage_pct": []},
    }
    lean_calls = 0

    for sd in seeds:
        rng = np.random.default_rng(sd)
        s_perm = rng.permutation(small_idx)
        r_perm = rng.permutation(rest_idx)
        eval_holdout = r_perm[:140]
        cand_pool_0 = list(r_perm[140:])

        for mode in out:
            known = list(s_perm[:140])
            pool = list(cand_pool_0)
            uncal_prod = 0

            for _r in range(rounds):
                rng_r = np.random.default_rng(sd * 10 + _r)
                rng_r.shuffle(known)
                n_cal = max(25, int(0.25 * len(known)))
                tr_ids = known[:-n_cal]
                cal_ids = known[-n_cal:]

                scaler = StandardScaler().fit(X[tr_ids])
                scaler.scale_ = np.where(scaler.scale_ < 0.5, 1.0, scaler.scale_)
                nn = NearestNeighbors(n_neighbors=min(5, len(tr_ids))).fit(scaler.transform(X[tr_ids]))
                cal_d = nn.kneighbors(scaler.transform(X[cal_ids]))[0].mean(axis=1)
                tau = float(np.quantile(cal_d, 0.90))
                tau_pm = max(100, int(round(tau * 1000)))

                pool_s = scaler.transform(X[pool])
                pool_d = nn.kneighbors(pool_s)[0].mean(axis=1)
                target_s = scaler.transform(target_proto.reshape(1, -1))[0]

                if mode == "static_trust_wall_v1":
                    tsv = [f"FRONTIER\t0\t{int(round(d * 1000))}\t{tau_pm}\t{eta_pm}\t350\t250\t100\t1\t0" for d in pool_d]
                    verdicts = kernel.eval_lines(tsv)
                    lean_calls += len(tsv)
                    legal = [pool[i] for i, v in enumerate(verdicts) if v.allowed][:probes_per_round]
                    for cid in legal:
                        pool.remove(cid)
                        known.append(cid)
                elif mode == "unbounded_greedy_leap":
                    dist_to_goal = np.linalg.norm(pool_s - target_s, axis=1)
                    goal_order = np.argsort(dist_to_goal)[:probes_per_round]
                    picked = [pool[i] for i in goal_order]
                    uncal_prod += sum(1 for i in goal_order if pool_d[i] > tau)
                    for cid in picked:
                        pool.remove(cid)
                        known.append(cid)
                else:
                    tsv = [f"FRONTIER\t1\t{int(round(d * 1000))}\t{tau_pm}\t{eta_pm}\t350\t80\t100\t1\t0" for d in pool_d]
                    verdicts = kernel.eval_lines(tsv)
                    lean_calls += len(tsv)
                    shell_idxs = [i for i, v in enumerate(verdicts) if v.allowed]
                    if mode == "undirected_shell_probes":
                        shell_idxs.sort(key=lambda i: -pool_d[i])
                    else:
                        dist_to_goal = np.linalg.norm(pool_s - target_s, axis=1)
                        shell_idxs.sort(key=lambda i: float(dist_to_goal[i]))
                    picked = [pool[i] for i in shell_idxs[:probes_per_round]]
                    for cid in picked:
                        pool.remove(cid)
                        known.append(cid)

            rng_f = np.random.default_rng(sd + 999)
            known_arr = rng_f.permutation(known)
            n_cal_f = max(30, int(0.25 * len(known_arr)))
            tr_f, cal_f = known_arr[:-n_cal_f], known_arr[-n_cal_f:]

            sc_f = StandardScaler().fit(X[tr_f])
            sc_f.scale_ = np.where(sc_f.scale_ < 0.5, 1.0, sc_f.scale_)
            reg_f = GradientBoostingRegressor(random_state=sd, n_estimators=100, max_depth=3)
            reg_f.fit(sc_f.transform(X[tr_f]), y[tr_f])
            nn_f = NearestNeighbors(n_neighbors=5).fit(sc_f.transform(X[tr_f]))
            tau_f = float(np.quantile(nn_f.kneighbors(sc_f.transform(X[cal_f]))[0].mean(axis=1), 0.90))

            cal_res = np.abs(y[cal_f] - reg_f.predict(sc_f.transform(X[cal_f])))
            k_rk = conformal_rank_permille(len(cal_res), 100)
            q_f = float(np.sort(cal_res)[min(k_rk - 1, len(cal_res) - 1)])

            all_d = nn_f.kneighbors(sc_f.transform(X))[0].mean(axis=1)
            trusted_pct = 100.0 * float(np.mean(all_d <= tau_f))

            hold_d = nn_f.kneighbors(sc_f.transform(X[eval_holdout]))[0].mean(axis=1)
            in_hold = eval_holdout[hold_d <= tau_f]
            if len(in_hold) > 0:
                cov = 100.0 * float(np.mean(np.abs(y[in_hold] - reg_f.predict(sc_f.transform(X[in_hold]))) <= q_f))
            else:
                cov = 100.0

            novel_hits = int(np.sum((all_d <= tau_f) & (X[:, 0] >= 220.0) & (X[:, 2] >= 2.0) & (y >= -3.5)))

            out[mode]["trusted_space_pct"].append(trusted_pct)
            out[mode]["novel_multiring_hits"].append(novel_hits)
            out[mode]["uncalibrated_prod_runs"].append(uncal_prod)
            out[mode]["prod_coverage_pct"].append(cov)

    return {
        "direction": "Direction 2 - Stepped Frontier Calibration (Active Trust-Boundary Expansion)",
        "inspired_by": "Resolving the static guardrail vs novel-scaffold discovery paradox in self-driving labs",
        "data_source": src,
        "input_type": "real_esol_active_learning_simulation",
        "evaluation_note": (
            "Descriptors and measured logS come from real Delaney ESOL (n=1,128); "
            "0.0 uncalibrated production runs for shell regimes is enforced by construction via FRONTIER."
        ),
        "lean_kernel_calls": lean_calls,
        "comparison": {
            k: {
                "trusted_chemical_space_pct": round(float(np.mean(d["trusted_space_pct"])), 1),
                "certified_multiring_scaffolds_unlocked": round(float(np.mean(d["novel_multiring_hits"])), 1),
                "uncalibrated_production_runs": round(float(np.mean(d["uncalibrated_prod_runs"])), 1),
                "empirical_90_coverage_pct": round(float(np.mean(d["prod_coverage_pct"])), 1),
            }
            for k, d in out.items()
        },
    }


# ---------------------------------------------------------------------------
# Direction 3: Proof-Carrying `Lean-MCP` Envelopes vs Per-Run Human Approval
# ---------------------------------------------------------------------------
def run_direction3_lean_mcp(kernel: LeanBatchKernel) -> dict[str, Any]:
    import numpy as np

    rng = np.random.default_rng(20261123)
    n_calls = 500
    exec_min = 6.0

    tsv_lean: list[str] = []
    call_kinds: list[str] = []
    for i in range(n_calls):
        u = rng.random()
        cur_ep = 1000 + i
        if u < 0.88:
            call_kinds.append("routine_valid")
            tsv_lean.append(f"MCP\t{cur_ep}\t{cur_ep}\t1\t0\t0")
        elif u < 0.94:
            call_kinds.append("stale_replay_bug")
            tsv_lean.append(f"MCP\t{cur_ep - 1}\t{cur_ep}\t1\t0\t0")
        else:
            call_kinds.append("frontier_exception")
            tsv_lean.append(f"MCP\t{cur_ep}\t{cur_ep}\t0\t1\t0")

    verdicts = kernel.eval_lines(tsv_lean)

    def sim_clock(mode: str) -> dict[str, Any]:
        t_min = 0.0
        completed = 0
        human_pings = 0
        unsafe_exec = 0
        if mode == "proof_carrying_lean_mcp":
            deferred_exceptions = 0
            for kind, verd in zip(call_kinds, verdicts):
                if t_min >= 4320.0:
                    break
                if verd.allowed:
                    t_min += exec_min
                    completed += 1
                elif kind == "stale_replay_bug":
                    t_min += 0.01
                elif kind == "frontier_exception":
                    day_offset = t_min % 1440.0
                    if day_offset < 480.0:
                        human_pings += 1
                        t_min += 10.0 + exec_min
                        completed += 1
                    else:
                        deferred_exceptions += 1
                while deferred_exceptions > 0 and (t_min % 1440.0) < 480.0 and t_min < 4320.0:
                    human_pings += 1
                    t_min += 10.0 + exec_min
                    completed += 1
                    deferred_exceptions -= 1
            return {
                "protocols_completed_in_72h": completed,
                "human_approval_interruptions": human_pings,
                "unsafe_or_replay_executions": unsafe_exec,
            }

        for kind, _verd in zip(call_kinds, verdicts):
            if t_min >= 4320.0:
                break
            if mode == "advisory_prompt_mcp":
                if kind == "stale_replay_bug":
                    unsafe_exec += 1
                t_min += exec_min
                if kind in ("routine_valid", "frontier_exception"):
                    completed += 1
            elif mode == "per_run_human_approval_mcp":
                day_offset = t_min % 1440.0
                if day_offset >= 480.0:
                    t_min += 1440.0 - day_offset
                if t_min >= 4320.0:
                    break
                human_pings += 1
                t_min += 10.0
                if kind != "stale_replay_bug":
                    t_min += exec_min
                    completed += 1
        return {
            "protocols_completed_in_72h": completed,
            "human_approval_interruptions": human_pings,
            "unsafe_or_replay_executions": unsafe_exec,
        }

    return {
        "direction": "Direction 3 - Proof-Carrying `Lean-MCP` Hardware Envelopes (72-Hour Lab Clock Simulation)",
        "inspired_by": "2026 MCP lab harnesses (plr-mcp, LabMCP, OpenLabAI, Osprey, Anthropic Model Hardware Standard)",
        "input_type": "simulation",
        "evaluation_note": (
            "Discrete-event 72-hour clock simulation over 500 synthetic MCP requests "
            "(88% routine, 6% stale-epoch replay, 6% frontier exception); 0 unsafe runs is by construction."
        ),
        "lean_kernel_calls": len(tsv_lean),
        "comparison": {
            "advisory_prompt_mcp": sim_clock("advisory_prompt_mcp"),
            "per_run_human_approval_mcp": sim_clock("per_run_human_approval_mcp"),
            "proof_carrying_lean_mcp": sim_clock("proof_carrying_lean_mcp"),
        },
    }


# ---------------------------------------------------------------------------
# Direction 4: Fixed Fault-Family Mutation Check (21 Distinct Cases)
# ---------------------------------------------------------------------------
def run_direction4_adversarial_coevolution(kernel: LeanBatchKernel) -> dict[str, Any]:
    from autolab.trust_regime import format_rehearsal_tsv
    from benchmarks.trust_regime_study import _clean_protocol, _coarse_heuristic_ok, _corrupt_protocol

    gen0_evade = 0
    gen1_evade = 0
    tsv_lines: list[str] = []
    distinct_signatures: set[tuple[Any, ...]] = set()

    for i in range(140):
        wells, clean = _clean_protocol(i)
        fk = i % 7
        bad_steps = _corrupt_protocol(wells, clean, fk)
        distinct_signatures.add((i % 3, fk, tuple(bad_steps)))
        tsv_lines.append(format_rehearsal_tsv(200, 3000, 50000 + i, [], wells, bad_steps))

        vols = {int(w["wellId"]): int(w["vol"]) for w in wells}
        caps = {int(w["wellId"]): int(w["cap"]) for w in wells}
        g0_ok = True
        for st in bad_steps:
            if st[0] == "xfer":
                _, s, d, v = st
                if vols[s] < v or vols[d] + v > caps[d]:
                    g0_ok = False
                    break
                vols[s] -= v
                vols[d] += v
        if g0_ok:
            gen0_evade += 1

        if _coarse_heuristic_ok(wells, bad_steps):
            gen1_evade += 1

    lean_v = kernel.eval_lines(tsv_lines)
    gen2_evade = sum(1 for v in lean_v if v.allowed)

    return {
        "direction": "Direction 4 - Fixed Fault-Family Mutation Check (21 Distinct Cases)",
        "inspired_by": "Lean4Agent / LeanEvolve (arXiv:2606.06523), BenchBench-Protocol, and RLVR verifier-gaming debates",
        "input_type": "simulation",
        "distinct_cases": len(distinct_signatures),
        "adversarial_mutations_tested": len(tsv_lines),
        "evaluation_note": (
            "Fixed fault-family mutation check over 3 clean templates x 7 fault classes = 21 distinct "
            "cases (cycled to 140 draws; not an adaptive adversary). Gen-2 0.0% evasion is by construction "
            "against the 7 modeled fault classes."
        ),
        "generations": {
            "gen0_volume_bounds_only": {"saboteur_evasion_pct": round(100.0 * gen0_evade / len(tsv_lines), 1)},
            "gen1_presence_bitmask": {"saboteur_evasion_pct": round(100.0 * gen1_evade / len(tsv_lines), 1)},
            "gen2_autolablean_formal": {"saboteur_evasion_pct": round(100.0 * gen2_evade / len(tsv_lines), 2)},
        },
    }


def main() -> int:
    t0 = time.perf_counter()
    audit = audit_lean_sources()
    assert audit["zero_sorry_verified"], f"Zero-sorry violation: {audit['violations']}"
    kernel = LeanBatchKernel()
    assert kernel.available, "Run `lake build` in `lean/` first"

    d1 = run_direction1_epistemic_attribution(kernel)
    d2 = run_direction2_stepped_frontier(kernel)
    d3 = run_direction3_lean_mcp(kernel)
    d4 = run_direction4_adversarial_coevolution(kernel)

    payload = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lean_audit": {
            "file_count": audit["file_count"],
            "theorem_count": audit["theorem_count"],
            "guard_count": audit["guard_count"],
            "zero_sorry_verified": audit["zero_sorry_verified"],
        },
        "runtime_sec": round(time.perf_counter() - t0, 2),
        "directions": {
            "d1_epistemic_attribution": d1,
            "d2_stepped_frontier": d2,
            "d3_lean_mcp": d3,
            "d4_adversarial_coevolution": d4,
        },
    }

    out_path = REPO_ROOT / "benchmarks" / "results" / "novel_directions_results.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    site_path = REPO_ROOT / "site" / "assets" / "novel-directions-data.json"
    site_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
