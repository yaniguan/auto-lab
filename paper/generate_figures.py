"""Generate publication-grade vector PDF figures for the Auto-Lab arXiv preprint.

Reads measured benchmark JSON outputs from `benchmarks/results/*.json` and emits crisp,
Type-42 vector PDFs into `paper/figures/` styled after flagship Anthropic / OpenAI reports.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
FIG_DIR = REPO_ROOT / "paper" / "figures"

# Editorial Palette
INK = "#0F172A"
SLATE = "#334155"
MUTED = "#64748B"
GRID = "#E2E8F0"
BG_CARD = "#F8FAFC"
TEAL = "#0D9488"
TEAL_LIGHT = "#CCFBF1"
INDIGO = "#4F46E5"
INDIGO_LIGHT = "#E0E7FF"
AMBER = "#D97706"
AMBER_LIGHT = "#FEF3C7"
ROSE = "#E11D48"
ROSE_LIGHT = "#FFE4E6"

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.8,
        "xtick.color": SLATE,
        "ytick.color": SLATE,
        "text.color": INK,
    }
)


def _despine(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _draw_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    *,
    fc: str = "#FFFFFF",
    ec: str = "#CBD5E1",
    lw: float = 1.1,
    title_color: str = INK,
    title_size: float = 8.6,
    sub_size: float = 7.3,
) -> None:
    box = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        zorder=2,
    )
    ax.add_patch(box)
    if subtitle:
        ax.text(
            x + w / 2,
            y + h * 0.64,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            zorder=3,
        )
        ax.text(
            x + w / 2,
            y + h * 0.29,
            subtitle,
            ha="center",
            va="center",
            fontsize=sub_size,
            color=SLATE,
            zorder=3,
        )
    else:
        ax.text(
            x + w / 2,
            y + h / 2,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            zorder=3,
        )


def make_fig1_architecture() -> None:
    """Page-1 Hero Schematic: 7-Layer Stack + Unified/Distributed Lean Kernel + 4-Layer Memory."""
    fig, ax = plt.subplots(figsize=(10.5, 2.95))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Column headers (well-separated so zero horizontal collision)
    headers = [
        (0.01, 0.285, "A. 7-Layer Organism (14 Repos)", SLATE),
        (0.345, 0.31, "B. Unified + Synced Lean 4 Kernel", TEAL),
        (0.70, 0.285, "C. 4-Layer 'Undergrad' Memory", INDIGO),
    ]
    for x, w, txt, col in headers:
        ax.text(x + w / 2, 0.955, txt, ha="center", va="center", fontsize=8.4, fontweight="bold", color=col)

    # Panel A: L6 -> L0 stack
    layers = [
        ("L6 Brain", "lab-ask-why · lab-decide"),
        ("L5 Executive", "buy-or-make · labshift · atlas"),
        ("L4 Twin & Gate", "lab-rehearsal · lab-verify"),
        ("L3 RLVR Flywheel", "labbench-posttrain · twinstep · labfill"),
        ("L2–L0 Body", "lab-ears · stepbot · lab-hands · lab-feet"),
    ]
    for idx, (ltitle, lrepos) in enumerate(layers):
        yy = 0.745 - idx * 0.168
        _draw_box(ax, 0.015, yy, 0.28, 0.135, ltitle, lrepos, fc=BG_CARD, ec="#94A3B8", title_size=8.2, sub_size=7.0)

    # Panel B: Center Shield Wall (`AutoLabLean`)
    outer = FancyBboxPatch(
        (0.35, 0.07),
        0.30,
        0.82,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        facecolor="#F0FDFA",
        edgecolor=TEAL,
        linewidth=1.6,
        zorder=1,
    )
    ax.add_patch(outer)
    ax.text(
        0.50,
        0.835,
        "AutoLabLean Hub + 14 Repo Sub-Kernels",
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color="#115E59",
    )
    ax.text(
        0.50,
        0.78,
        "50 Machine-Checked Theorems · 0 sorry",
        ha="center",
        va="center",
        fontsize=7.5,
        color=TEAL,
        fontweight="bold",
    )
    shield_items = [
        ("Pre-Execution Invariants", "Conformal kNN · Acyclic Atoms · 96w Conservation"),
        ("Frontier & Lean-MCP", "Annular Chem-RRT Shell · Epoch Capability Tokens"),
        ("Post-Run Blame (ATTRIB)", "Separates Robot Glitches & XRD Overlap from Truth"),
        ("Memory Hygiene Gate", "Token-Cap Packing · Rusty-SOP Rehearsal · Analogy"),
    ]
    for idx, (st, ss) in enumerate(shield_items):
        yy = 0.595 - idx * 0.165
        _draw_box(ax, 0.368, yy, 0.264, 0.132, st, ss, fc="#FFFFFF", ec=TEAL, lw=0.95, title_color="#0F766E", title_size=7.9, sub_size=6.65)

    # Panel C: 4-Layer Undergrad Memory Stack + Sleep-Time Dreaming
    mem_outer = FancyBboxPatch(
        (0.70, 0.07),
        0.285,
        0.82,
        boxstyle="round,pad=0.012,rounding_size=0.022",
        facecolor="#EEF2FF",
        edgecolor=INDIGO,
        linewidth=1.4,
        zorder=1,
    )
    ax.add_patch(mem_outer)
    mem_layers = [
        ("L3 · Injected Bench Brief", "MEMORY.md (<= Budget Cap · Rusty Check)"),
        ("L2 · Linked Concept Wiki", "Structural Analogy + Tool Bindings"),
        ("L1 · Salience Notes", "Memory-as-Prediction · Dream-Pruned"),
        ("L0 · Transcripts + Bottom Trace", "Symptom -> Law -> Mechanism -> Fix"),
    ]
    for idx, (mt, ms) in enumerate(mem_layers):
        yy = 0.71 - idx * 0.165
        is_bottom = idx == 3
        _draw_box(
            ax,
            0.716,
            yy,
            0.253,
            0.132,
            mt,
            ms,
            fc="#FFFBEB" if is_bottom else "#FFFFFF",
            ec=AMBER if is_bottom else INDIGO,
            lw=1.2 if is_bottom else 0.95,
            title_color="#B45309" if is_bottom else INDIGO,
            title_size=7.8,
            sub_size=6.65,
        )
    ax.text(
        0.842,
        0.115,
        "Sleep-Time Dreaming: Purge Noise · Deduplicate · Promote",
        ha="center",
        va="center",
        fontsize=6.95,
        fontweight="bold",
        color="#3730A3",
    )

    # Connecting bidirectional arrows between A <-> B <-> C
    arrow_kw = dict(arrowstyle="-|>,head_width=0.22,head_length=0.35", lw=1.35, color=TEAL)
    for yy in (0.68, 0.45, 0.22):
        ax.annotate("", xy=(0.348, yy), xytext=(0.298, yy), arrowprops=arrow_kw)
    arrow_mem = dict(arrowstyle="<->,head_width=0.20,head_length=0.32", lw=1.35, color=INDIGO)
    ax.annotate("", xy=(0.698, 0.56), xytext=(0.652, 0.56), arrowprops=arrow_mem)
    ax.annotate("", xy=(0.698, 0.30), xytext=(0.652, 0.30), arrowprops=arrow_mem)

    fig.tight_layout(pad=0.25)
    fig.savefig(FIG_DIR / "fig1_architecture.pdf", bbox_inches="tight")
    plt.close(fig)


def make_fig2_core_trust_lift(trust: dict) -> None:
    """4-panel empirical lift across Molecular Discovery, Protocol Synthesis, SQL Gate, and RLVR."""
    fig, axes = plt.subplots(1, 4, figsize=(10.4, 2.75))
    exps = trust["experiments"]

    # Panel A: ESOL Molecular Campaign MAE & Hit Yield
    ax = axes[0]
    e1 = exps["exp1_molecular_discovery"]["regimes"]
    labels = ["Ungated", "Heuristic", "AutoLabLean"]
    maes = [e1["ungated"]["prediction_mae"], e1["heuristic"]["prediction_mae"], e1["lean_trust"]["prediction_mae"]]
    cols = [ROSE, AMBER, TEAL]
    bars = ax.bar(labels, maes, color=cols, width=0.56, zorder=3)
    ax.set_title("A. ESOL Selected MAE ↓", fontsize=8.8, fontweight="bold", pad=7)
    ax.set_ylabel("MAE (log mol/L)", fontsize=8.0)
    ax.set_ylim(0, 1.22)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="x", labelsize=7.6, rotation=14)
    ax.tick_params(axis="y", labelsize=7.5)
    for b, v in zip(bars, maes):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.035, f"{v:.3f}", ha="center", va="bottom", fontsize=7.6, fontweight="bold")

    # Panel B: Protocol Synthesis & Guided Repair
    ax = axes[1]
    e2 = exps["exp2_protocol_synthesis"]["regimes"]
    labels = ["Top-1", "Bitmask", "Lean Bo8", "Bo8+Repair"]
    vals = [
        e2["ungated_top1"]["valid_completion_pct"],
        e2["coarse_bitmask_heuristic"]["valid_completion_pct"],
        e2["lean_best_of_8"]["valid_completion_pct"],
        e2["lean_best_of_8_plus_guided_repair"]["valid_completion_pct"],
    ]
    cols = [ROSE, AMBER, INDIGO, TEAL]
    bars = ax.bar(labels, vals, color=cols, width=0.58, zorder=3)
    ax.set_title("B. Valid Wet-Lab Protocols ↑", fontsize=8.8, fontweight="bold", pad=7)
    ax.set_ylabel("Valid Completion (%)", fontsize=8.0)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="x", labelsize=7.3, rotation=16)
    ax.tick_params(axis="y", labelsize=7.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=7.3, fontweight="bold")

    # Panel C: Lab SQL Verification Gate
    ax = axes[2]
    e4 = exps["exp4_sql_verification"]["regimes"]
    labels = ["Ungated", "L1–L3 Only", "Lean L1–L4"]
    acc = [
        e4["ungated_noisy_top1"]["verified_answer_accuracy_pct"],
        e4["syntax_readonly_schema_only_L1_L3"]["verified_answer_accuracy_pct"],
        e4["lean_4layer_default_deny_L1_L4"]["verified_answer_accuracy_pct"],
    ]
    fa = [
        e4["ungated_noisy_top1"]["wrong_sql_false_accept_pct"],
        e4["syntax_readonly_schema_only_L1_L3"]["wrong_sql_false_accept_pct"],
        e4["lean_4layer_default_deny_L1_L4"]["wrong_sql_false_accept_pct"],
    ]
    x = np.arange(len(labels))
    w = 0.34
    b1 = ax.bar(x - w / 2, acc, width=w, color=TEAL, label="Verified Acc ↑", zorder=3)
    b2 = ax.bar(x + w / 2, fa, width=w, color=ROSE, label="False Accept ↓", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.4, rotation=14)
    ax.set_ylim(0, 118)
    ax.set_title("C. Lab SQL Gate (lab-verify)", fontsize=8.8, fontweight="bold", pad=7)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="y", labelsize=7.5)
    ax.legend(frameon=False, fontsize=6.7, loc="upper right")
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 2.0, f"{h:.0f}%", ha="center", va="bottom", fontsize=6.8)

    # Panel D: GRPO Anti-Hack RLVR Post-Training
    ax = axes[3]
    e5 = exps["exp5_rlvr_posttraining"]["regimes"]
    labels = ["Init Prior", "Soft Bonus", "Lean Gated"]
    tacc = [
        e5["untrained_init"]["true_verified_accuracy_pct"],
        e5["soft_additive_reward_grpo"]["true_verified_accuracy_pct"],
        e5["lean_trust_gated_grpo"]["true_verified_accuracy_pct"],
    ]
    cols = [MUTED, ROSE, TEAL]
    bars = ax.bar(labels, tacc, color=cols, width=0.56, zorder=3)
    ax.set_title("D. GRPO True Accuracy ↑", fontsize=8.8, fontweight="bold", pad=7)
    ax.set_ylabel("Verified Accuracy (%)", fontsize=8.0)
    ax.set_ylim(0, 115)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="x", labelsize=7.5, rotation=14)
    ax.tick_params(axis="y", labelsize=7.5)
    for b, v in zip(bars, tacc):
        ax.text(b.get_x() + b.get_width() / 2, v + 2.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    fig.tight_layout(pad=0.6)
    fig.savefig(FIG_DIR / "fig2_core_trust_lift.pdf", bbox_inches="tight")
    plt.close(fig)


def make_fig3_frontier_directions(novel: dict) -> None:
    """3-panel summary of NovelDirections.lean: ATTRIB, Stepped Chem-RRT, and 72h Lean-MCP."""
    fig, axes = plt.subplots(1, 3, figsize=(10.2, 2.8))
    dirs = novel["directions"]

    # Panel A: Epistemic Attribution (ATTRIB)
    ax = axes[0]
    d1 = dirs["d1_epistemic_attribution"]["comparison"]
    cats = ["True Hits\nDiscovered ↑", "Poisoned Runs\nAdmitted ↓", "False Discovery\nRate (%) ↓"]
    naive_v = [
        d1["naive_sdl"]["verified_true_hits_discovered"],
        d1["naive_sdl"]["poisoned_records_admitted"],
        d1["naive_sdl"]["false_discovery_rate_pct"],
    ]
    lean_v = [
        d1["lean_attribution_sdl"]["verified_true_hits_discovered"],
        d1["lean_attribution_sdl"]["poisoned_records_admitted"],
        d1["lean_attribution_sdl"]["false_discovery_rate_pct"],
    ]
    x = np.arange(len(cats))
    w = 0.34
    b1 = ax.bar(x - w / 2, naive_v, width=w, color=ROSE, label="Raw Readout SDL", zorder=3)
    b2 = ax.bar(x + w / 2, lean_v, width=w, color=TEAL, label="Lean ATTRIB", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=7.3)
    ax.set_ylim(0, 82)
    ax.set_title("A. Post-Run Causal Blame (ATTRIB)", fontsize=8.8, fontweight="bold", pad=7)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.legend(frameon=False, fontsize=7.0, loc="upper right")
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1.5, f"{h:.1f}", ha="center", va="bottom", fontsize=7.0, fontweight="bold")

    # Panel B: Stepped Frontier Calibration (Chem-RRT vs Static Wall vs Greedy Leap)
    ax = axes[1]
    d2 = dirs["d2_stepped_frontier"]["comparison"]
    modes = ["Static Wall", "Greedy Leap", "Chem-RRT", "Shell Probe"]
    scaff = [
        d2["static_trust_wall_v1"]["certified_multiring_scaffolds_unlocked"],
        d2["unbounded_greedy_leap"]["certified_multiring_scaffolds_unlocked"],
        d2["goal_directed_chem_rrt_shell"]["certified_multiring_scaffolds_unlocked"],
        d2["undirected_shell_probes"]["certified_multiring_scaffolds_unlocked"],
    ]
    ood_runs = [
        d2["static_trust_wall_v1"]["uncalibrated_production_runs"],
        d2["unbounded_greedy_leap"]["uncalibrated_production_runs"],
        d2["goal_directed_chem_rrt_shell"]["uncalibrated_production_runs"],
        d2["undirected_shell_probes"]["uncalibrated_production_runs"],
    ]
    cols = [AMBER, ROSE, INDIGO, TEAL]
    bars = ax.bar(modes, scaff, color=cols, width=0.55, zorder=3)
    ax.set_title("B. Multi-Ring Scaffolds Unlocked ↑", fontsize=8.8, fontweight="bold", pad=7)
    ax.set_ylabel("Certified Novel Scaffolds", fontsize=7.9)
    ax.set_ylim(0, 68)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="x", labelsize=7.3, rotation=14)
    for b, sc, ood in zip(bars, scaff, ood_runs):
        tag = f"{sc:.1f}\n({ood:.0f} OOD!)" if ood > 0 else f"{sc:.1f}\n(0 OOD)"
        ax.text(b.get_x() + b.get_width() / 2, sc + 1.4, tag, ha="center", va="bottom", fontsize=6.7, fontweight="bold")

    # Panel C: 72-Hour Continuous Hardware-MCP Governance
    ax = axes[2]
    d3 = dirs["d3_lean_mcp"]["comparison"]
    m_labels = ["Prompt MCP", "Per-Run Click", "Lean-MCP"]
    done = [
        d3["advisory_prompt_mcp"]["protocols_completed_in_72h"],
        d3["per_run_human_approval_mcp"]["protocols_completed_in_72h"],
        d3["proof_carrying_lean_mcp"]["protocols_completed_in_72h"],
    ]
    pings = [
        d3["advisory_prompt_mcp"]["human_approval_interruptions"],
        d3["per_run_human_approval_mcp"]["human_approval_interruptions"],
        d3["proof_carrying_lean_mcp"]["human_approval_interruptions"],
    ]
    unsafe = [
        d3["advisory_prompt_mcp"]["unsafe_or_replay_executions"],
        d3["per_run_human_approval_mcp"]["unsafe_or_replay_executions"],
        d3["proof_carrying_lean_mcp"]["unsafe_or_replay_executions"],
    ]
    cols = [ROSE, AMBER, TEAL]
    bars = ax.bar(m_labels, done, color=cols, width=0.54, zorder=3)
    ax.set_title("C. 72h Completed Protocols (MCP) ↑", fontsize=8.8, fontweight="bold", pad=7)
    ax.set_ylabel("Runs Completed in 72h", fontsize=7.9)
    ax.set_ylim(0, 585)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.tick_params(axis="x", labelsize=7.5, rotation=12)
    for b, dn, pg, un in zip(bars, done, pings, unsafe):
        sub = f"{dn}\n({un} unsafe!)" if un > 0 else f"{dn}\n({pg} clicks)"
        ax.text(b.get_x() + b.get_width() / 2, dn + 10, sub, ha="center", va="bottom", fontsize=6.9, fontweight="bold")

    fig.tight_layout(pad=0.65)
    fig.savefig(FIG_DIR / "fig3_frontier_and_mcp.pdf", bbox_inches="tight")
    plt.close(fig)


def make_fig4_undergrad_memory(mem: dict) -> None:
    """3-panel empirical evaluation of the 4-Layer 'Undergrad' Agent Memory + Bottom Traces + Dreaming."""
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 2.85))

    # Panel A: Rusty-Skill & Novel-Assay Transfer Comparison
    ax = axes[0]
    r_pct = mem["rusty_skill_reonboarding"]["safe_execution_pct"]
    n_pct = mem["novel_assay_transfer"]["first_try_certified_transfer_pct"]
    regimes = ["Stateless", "Rote / Wiki\n(No Trace)", "Unpruned /\nNo Tools", "Undergrad\nTrace+Dream"]
    rusty_vals = [
        r_pct["stateless_no_memory"],
        r_pct["rote_summary_without_bottom_trace"],
        r_pct["append_only_unpruned_logs"],
        r_pct["undergrad_4layer_bottom_trace_dreaming"],
    ]
    novel_vals = [
        n_pct["stateless_zero_memory"],
        n_pct["wiki_analogy_without_bottom_trace"],
        n_pct["bottom_trace_physical_only_ungated"],
        n_pct["undergrad_full_trace_plus_tools_lean"],
    ]
    x = np.arange(len(regimes))
    w = 0.36
    b1 = ax.bar(x - w / 2 - 0.01, rusty_vals, width=w, color=INDIGO, label="Rusty SOP (>120d)", zorder=3)
    b2 = ax.bar(x + w / 2 + 0.01, novel_vals, width=w, color=TEAL, label="Unseen Assay (0-shot)", zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels(regimes, fontsize=6.9)
    ax.set_ylim(0, 122)
    ax.set_ylabel("Certified Safe Execution (%)", fontsize=7.9)
    ax.set_title("A. Rusty Re-Onboarding & Novel Transfer", fontsize=8.6, fontweight="bold", pad=7)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.legend(frameon=False, fontsize=6.7, loc="upper left")
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 2.2, f"{h:.0f}%", ha="center", va="bottom", fontsize=6.1, fontweight="bold")

    # Panel B: 60-Session Longitudinal Mastery Curve
    ax = axes[1]
    longi = mem["longitudinal_60_sessions"]
    xs = longi["sessions"]
    ax.plot(xs, longi["undergrad_dreaming_acc_pct"], "-o", color=TEAL, lw=2.1, ms=4.3, label="Undergrad + Trace + Dream")
    ax.plot(xs, longi["summary_no_trace_acc_pct"], "--s", color=AMBER, lw=1.7, ms=3.8, label="Summary Notes (No Trace)")
    ax.plot(xs, longi["append_only_acc_pct"], "-.^", color=ROSE, lw=1.8, ms=4.0, label="Append-Only Logs (Bloat)")
    ax.plot(xs, longi["stateless_acc_pct"], ":d", color=MUTED, lw=1.5, ms=3.6, label="Stateless Agent")
    ax.set_xlabel("Sequential Lab Session Index", fontsize=7.9)
    ax.set_ylabel("Task Success Rate (%)", fontsize=7.9)
    ax.set_ylim(0, 108)
    ax.set_title("B. 60-Session Compounding vs Context Rot", fontsize=8.6, fontweight="bold", pad=7)
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.legend(frameon=True, facecolor="#FFFFFF", edgecolor="none", framealpha=0.88, fontsize=6.1, loc="lower right")

    # Panel C: Context Token Footprint Over 60 Sessions
    ax = axes[2]
    t_append = [v / 1000.0 for v in longi["append_only_context_tokens"]]
    t_dream = [v / 1000.0 for v in longi["undergrad_dreaming_context_tokens"]]
    ax.plot(xs, t_append, "-^", color=ROSE, lw=2.0, ms=4.5, label="Append-Only Raw Logs")
    ax.plot(xs, t_dream, "-o", color=TEAL, lw=2.2, ms=4.5, label="Dream-Consolidated MEMORY.md")
    ax.axhline(0.42, color=INDIGO, ls="--", lw=1.1, label="Lean Budget Cap (0.42k tok)")
    ax.fill_between(xs, t_append, color=ROSE, alpha=0.09)
    ax.set_xlabel("Sequential Lab Session Index", fontsize=7.9)
    ax.set_ylabel("Injected Context Size (k tokens)", fontsize=7.9)
    ax.set_ylim(0, 22.0)
    ax.set_title("C. Prompt Token Footprint (180x Leaner)", fontsize=8.6, fontweight="bold", pad=7)
    ax.grid(True, color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.legend(frameon=False, fontsize=6.7, loc="upper left")
    ax.text(60, t_append[-1] + 0.6, f"{t_append[-1]:.1f}k", ha="right", fontsize=7.2, fontweight="bold", color=ROSE)
    ax.text(60, t_dream[-1] + 0.8, f"{longi['undergrad_dreaming_context_tokens'][-1]} tok", ha="right", fontsize=7.2, fontweight="bold", color=TEAL)

    fig.tight_layout(pad=0.65)
    fig.savefig(FIG_DIR / "fig4_undergrad_memory.pdf", bbox_inches="tight")
    plt.close(fig)


def make_fig5_twenty_ideas(ideas_payload: dict) -> None:
    """Horizontal Cleveland dumbbell plot of all 20 community-sourced implementations across 14 repos."""
    items = ideas_payload["ideas"]
    fig, ax = plt.subplots(figsize=(10.2, 5.55))

    y = np.arange(len(items))[::-1]
    labels = [f"#{it['id']:02d} [{it['layer']}] {it['repo']} :: {it['short_name']}" for it in items]
    base_scores = [float(it["baseline_score_pct"]) for it in items]
    ours_scores = [float(it["autolab_score_pct"]) for it in items]

    for yi, b, o in zip(y, base_scores, ours_scores):
        ax.plot([b, o], [yi, yi], color="#94A3B8", lw=1.7, zorder=2)
    ax.scatter(base_scores, y, color=ROSE, s=36, zorder=3, label="Community / Heuristic Baseline")
    ax.scatter(ours_scores, y, color=TEAL, s=42, zorder=4, label="Auto-Lab Formal + Embodied Extension")

    for yi, b, o, it in zip(y, base_scores, ours_scores, items):
        gain = o - b
        ax.text(
            min(103.5, max(b, o) + 1.6),
            yi,
            f"+{gain:.1f} pp ({it['metric_label']})",
            va="center",
            ha="left",
            fontsize=6.85,
            color=SLATE,
            fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.35, fontfamily="monospace")
    ax.set_xlim(-3, 166)
    ax.set_xlabel("Normalized Target Performance / Safety Score (%)", fontsize=8.4, fontweight="bold")
    ax.set_title(
        "Empirical Lift Across All 20 Community-Synthesized Extensions in the 14 Auto-Lab Sub-Repositories",
        fontsize=9.4,
        fontweight="bold",
        pad=22,
    )
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    _despine(ax)
    ax.legend(
        frameon=False,
        fontsize=7.8,
        ncol=2,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.005),
    )

    fig.tight_layout(pad=0.5)
    fig.savefig(FIG_DIR / "fig5_twenty_community_ideas.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    trust = json.loads((RESULTS_DIR / "trust_regime_results.json").read_text(encoding="utf-8"))
    novel = json.loads((RESULTS_DIR / "novel_directions_results.json").read_text(encoding="utf-8"))
    mem = json.loads((RESULTS_DIR / "agent_memory_results.json").read_text(encoding="utf-8"))

    make_fig1_architecture()
    make_fig2_core_trust_lift(trust)
    make_fig3_frontier_directions(novel)
    make_fig4_undergrad_memory(mem)

    ideas_file = RESULTS_DIR / "twenty_community_ideas_results.json"
    if ideas_file.exists():
        ideas = json.loads(ideas_file.read_text(encoding="utf-8"))
        make_fig5_twenty_ideas(ideas)
    print(f"Generated vector PDF figures in {FIG_DIR}")


if __name__ == "__main__":
    main()
