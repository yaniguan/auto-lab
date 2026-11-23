"""4-Layer 'Well-Trained Undergraduate' Agent Memory with Bottom Reasoning Traces & Dreaming.

Architecture grounded in Anthropic's *The Components of Agent Memory* (Transcripts ->
Memory Notes -> Linked Concept Wikis -> Bounded Injected Context + offline *Dreaming*)
and verified at runtime by `AutoLabLean.AgentMemory` (`MEM_SKILL` & `MEM_NOVEL`).
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from autolab.trust_regime import LeanBatchKernel, TrustVerdict


@dataclass(frozen=True)
class BottomReasoningTrace:
    """Layer-0 causal derivation enabling rapid conceptual mastery & one-shot transfer."""

    trace_id: str
    concept_id: str
    symptom: str
    first_principle_law: str
    causal_chain: str
    lean_rule_witness: str
    parameter_scaling: dict[str, float]  # e.g. {"log_visc_dead_vol_slope": 0.30, ...}
    attribution_certified: bool = True


@dataclass
class EpisodicTranscript:
    """Layer-0 raw immutable session transcript paired with its Bottom Reasoning Trace."""

    episode_id: str
    day_index: int
    deck_epoch: int
    assay_name: str
    concept_id: str
    raw_events: list[str]
    outcome_status: str  # CERTIFIED_POSITIVE | CERTIFIED_NEGATIVE | EXECUTION_ARTIFACT | AMBIGUOUS
    bottom_trace: BottomReasoningTrace | None = None


@dataclass
class MemoryNote:
    """Layer-1 discrete lesson scored by predicted future-session utility ('memory as prediction')."""

    note_id: str
    concept_id: str
    summary: str
    source_trace_id: str
    attribution_certified: bool
    has_first_principle_law: bool
    has_causal_mechanism: bool
    contradicted_by_newer: bool
    salience_permille: int
    token_cost: int


@dataclass
class ConceptWikiCard:
    """Layer-2 structured undergraduate mental schema linking principles, tools, and bottom traces."""

    concept_id: str
    title: str
    mechanism_tags: set[str]
    governing_principle: str
    tool_bindings: list[str]
    linked_trace_ids: list[str]
    parameter_scaling: dict[str, float]
    last_practiced_day: int
    calibrated_deck_epoch: int


@dataclass
class DreamReport:
    """Telemetry emitted by an offline sleep-time *Dreaming* consolidation pass."""

    raw_candidates: int
    quarantined_unverified_or_rote: int
    contradicted_purged: int
    deduplicated_merged: int
    wiki_cards_updated: int
    injected_notes_count: int
    injected_tokens: int
    token_budget: int


class UndergradMemoryStore:
    """4-layer laboratory agent memory modeling a well-trained senior undergraduate."""

    def __init__(
        self,
        token_budget: int = 900,
        min_salience_permille: int = 500,
        stale_threshold_days: int = 30,
        min_analogy_permille: int = 600,
    ) -> None:
        self.token_budget = token_budget
        self.min_salience_permille = min_salience_permille
        self.stale_threshold_days = stale_threshold_days
        self.min_analogy_permille = min_analogy_permille

        self.transcripts: list[EpisodicTranscript] = []
        self.traces: dict[str, BottomReasoningTrace] = {}
        self.notes: list[MemoryNote] = []
        self.wiki: dict[str, ConceptWikiCard] = {}
        self.injected_context: list[MemoryNote] = []

    # ------------------------------------------------------------------
    # Layer 0 & Layer 1 Write Path
    # ------------------------------------------------------------------
    def record_episode(
        self,
        episode: EpisodicTranscript,
        note_summary: str,
        salience_permille: int,
        mechanism_tags: set[str],
        tool_bindings: list[str],
        contradicts_note_ids: list[str] | None = None,
    ) -> MemoryNote:
        self.transcripts.append(episode)
        if contradicts_note_ids:
            bad = set(contradicts_note_ids)
            for existing in self.notes:
                if existing.note_id in bad:
                    existing.contradicted_by_newer = True

        certified = episode.outcome_status in {
            "CERTIFIED_POSITIVE",
            "CERTIFIED_NEGATIVE",
            "VERIFIED_GUARDRAIL_LESSON",
        }
        bt = episode.bottom_trace
        if bt is not None and bt.attribution_certified and certified:
            self.traces[bt.trace_id] = bt

        has_law = bool(bt and bt.first_principle_law.strip())
        has_mech = bool(bt and bt.causal_chain.strip())
        tokens = max(18, len(note_summary.split()) * 2)
        note = MemoryNote(
            note_id=f"note-{len(self.notes) + 1:03d}",
            concept_id=episode.concept_id,
            summary=note_summary,
            source_trace_id=bt.trace_id if bt else "",
            attribution_certified=bool(certified and (bt.attribution_certified if bt else False)),
            has_first_principle_law=has_law,
            has_causal_mechanism=has_mech,
            contradicted_by_newer=False,
            salience_permille=salience_permille,
            token_cost=tokens,
        )
        self.notes.append(note)

        # Register provisional concept metadata if certified
        if note.attribution_certified and bt is not None:
            card = self.wiki.get(episode.concept_id)
            if card is None:
                self.wiki[episode.concept_id] = ConceptWikiCard(
                    concept_id=episode.concept_id,
                    title=episode.concept_id.replace("-", " ").title(),
                    mechanism_tags=set(mechanism_tags),
                    governing_principle=bt.first_principle_law,
                    tool_bindings=list(tool_bindings),
                    linked_trace_ids=[bt.trace_id],
                    parameter_scaling=dict(bt.parameter_scaling),
                    last_practiced_day=episode.day_index,
                    calibrated_deck_epoch=episode.deck_epoch,
                )
            else:
                card.mechanism_tags |= set(mechanism_tags)
                if bt.trace_id not in card.linked_trace_ids:
                    card.linked_trace_ids.append(bt.trace_id)
                card.parameter_scaling.update(bt.parameter_scaling)
                card.last_practiced_day = max(card.last_practiced_day, episode.day_index)
                card.calibrated_deck_epoch = episode.deck_epoch
        return note

    # ------------------------------------------------------------------
    # Offline "Dreaming" Consolidation (Mirrors `AutoLabLean.AgentMemory`)
    # ------------------------------------------------------------------
    def dream_consolidate(self) -> DreamReport:
        """Sleep-time consolidation: purge poisoned/rote/contradicted notes, deduplicate by
        concept_id keeping highest salience, refresh ConceptWiki, and pack Layer-3 within budget."""
        quarantined = 0
        contradicted = 0
        valid_by_concept: dict[str, MemoryNote] = {}
        deduped = 0

        for n in self.notes:
            if n.contradicted_by_newer:
                contradicted += 1
                continue
            if not (
                n.attribution_certified
                and n.has_first_principle_law
                and n.has_causal_mechanism
                and n.salience_permille >= self.min_salience_permille
            ):
                quarantined += 1
                continue
            prev = valid_by_concept.get(n.concept_id)
            if prev is None:
                valid_by_concept[n.concept_id] = n
            else:
                deduped += 1
                if n.salience_permille >= prev.salience_permille:
                    valid_by_concept[n.concept_id] = n

        ranked = sorted(
            valid_by_concept.values(),
            key=lambda x: (-x.salience_permille, x.token_cost, x.note_id),
        )
        packed: list[MemoryNote] = []
        rem = self.token_budget
        for cand in ranked:
            if cand.token_cost <= rem:
                packed.append(cand)
                rem -= cand.token_cost
        self.injected_context = packed

        return DreamReport(
            raw_candidates=len(self.notes),
            quarantined_unverified_or_rote=quarantined,
            contradicted_purged=contradicted,
            deduplicated_merged=deduped,
            wiki_cards_updated=len(self.wiki),
            injected_notes_count=len(packed),
            injected_tokens=sum(x.token_cost for x in packed),
            token_budget=self.token_budget,
        )

    def render_injected_markdown(self) -> str:
        """Render the lean top-layer `MEMORY.md` prompt block injected at session start."""
        lines = [
            f"# Active Lab Bench Memory ({sum(n.token_cost for n in self.injected_context)}/{self.token_budget} tok)",
            "",
        ]
        for n in self.injected_context:
            lines.append(
                f"- **[{n.concept_id}]** (salience `{n.salience_permille/1000:.2f}`, trace `{n.source_trace_id}`): {n.summary}"
            )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Workflow 1: Rusty-Skill Re-Onboarding ("Haven't Touched in Months")
    # ------------------------------------------------------------------
    def invoke_skill(
        self,
        concept_id: str,
        current_day: int,
        current_deck_epoch: int,
        physical_params: dict[str, float],
        auto_refresh_if_rusty: bool = True,
        kernel: LeanBatchKernel | None = None,
    ) -> dict[str, Any]:
        card = self.wiki[concept_id]
        days_elapsed = max(0, current_day - card.last_practiced_day)
        is_rusty = (days_elapsed > self.stale_threshold_days) or (
            card.calibrated_deck_epoch != current_deck_epoch
        )

        trace_reviewed = False
        micro_rehearsal_ok = False
        adapted_params = dict(physical_params)

        if is_rusty and auto_refresh_if_rusty:
            # 1. Drill down to Layer-0 Bottom Reasoning Trace to restore governing equation!
            if card.linked_trace_ids:
                bt = self.traces.get(card.linked_trace_ids[-1])
                if bt is not None:
                    trace_reviewed = True
                    adapted_params = _apply_first_principle_scaling(physical_params, bt.parameter_scaling)
            # 2. Run micro-scale twin calibration under current deck epoch
            micro_rehearsal_ok = _verify_adapted_twin(adapted_params)
            if micro_rehearsal_ok:
                card.last_practiced_day = current_day
                card.calibrated_deck_epoch = current_deck_epoch

        verdict = _verify_skill_readiness_lean_or_py(
            days_elapsed,
            self.stale_threshold_days,
            card.calibrated_deck_epoch if not (is_rusty and auto_refresh_if_rusty) else current_deck_epoch
            if not is_rusty
            else (card.calibrated_deck_epoch if not micro_rehearsal_ok else 0),
            current_deck_epoch if not (is_rusty and auto_refresh_if_rusty and micro_rehearsal_ok) else 0,
            days_override=days_elapsed,
            trace_reviewed=trace_reviewed,
            micro_ok=micro_rehearsal_ok,
            kernel=kernel,
        )
        return {
            "concept_id": concept_id,
            "days_since_last_use": days_elapsed,
            "was_rusty": is_rusty,
            "bottom_trace_reviewed": trace_reviewed,
            "micro_rehearsal_passed": micro_rehearsal_ok,
            "adapted_params": adapted_params,
            "lean_verdict": asdict(verdict),
        }

    # ------------------------------------------------------------------
    # Workflow 2: Novel-Assay Conceptual Transfer ("Facing Something New")
    # ------------------------------------------------------------------
    def onboard_novel_assay(
        self,
        assay_name: str,
        query_tags: set[str],
        raw_params: dict[str, float],
        use_bottom_trace: bool = True,
        query_lab_tools: bool = True,
        kernel: LeanBatchKernel | None = None,
    ) -> dict[str, Any]:
        # Structural analogy search across Layer-2 ConceptWiki
        best_card: ConceptWikiCard | None = None
        best_sim = 0
        for card in self.wiki.values():
            union = len(query_tags | card.mechanism_tags)
            inter = len(query_tags & card.mechanism_tags)
            sim = int(round(1000.0 * inter / max(1, union)))
            if sim > best_sim:
                best_sim = sim
                best_card = card

        trace_loaded = False
        adapted = dict(raw_params)
        if best_card is not None and use_bottom_trace and best_card.linked_trace_ids:
            bt = self.traces.get(best_card.linked_trace_ids[-1])
            if bt is not None:
                trace_loaded = True
                adapted = _apply_first_principle_scaling(adapted, bt.parameter_scaling)

        if query_lab_tools:
            # Tool lookup (`lab-automation-atlas` / `stepbot`) bounds tip, volatile air-gap & thermal caps
            adapted["seal_required"] = 1.0 if adapted.get("temp_c", 25.0) >= 80.0 else 0.0
            if adapted.get("vapor_pressure_kpa", 2.3) > 4.0:
                adapted["air_gap_ul"] = max(float(adapted.get("air_gap_ul", 0.0)), 3.5)
            adapted["flow_rate_ul_s"] = round(
                min(adapted.get("flow_rate_ul_s", 150.0), 150.0 / max(1.0, math.log10(max(1.0, adapted.get("viscosity_cp", 1.0)) * 10.0))),
                2,
            )

        twin_ok = _verify_adapted_twin(adapted)
        verdict = _verify_novel_onboarding_lean_or_py(
            seen_before=False,
            analogy_sim_permille=best_sim,
            min_analogy_permille=self.min_analogy_permille,
            trace_loaded=trace_loaded,
            tools_queried=query_lab_tools,
            twin_ok=twin_ok,
            kernel=kernel,
        )
        return {
            "assay_name": assay_name,
            "nearest_concept": best_card.concept_id if best_card else None,
            "analogy_sim_permille": best_sim,
            "bottom_trace_loaded": trace_loaded,
            "tool_specs_queried": query_lab_tools,
            "twin_dry_run_certified": twin_ok,
            "adapted_params": adapted,
            "lean_verdict": asdict(verdict),
        }

    def export_workspace(self, out_dir: Path) -> dict[str, str]:
        """Persist all 4 layers (`transcripts.jsonl`, `wiki/*.md`, `MEMORY.md`) to disk."""
        out_dir.mkdir(parents=True, exist_ok=True)
        t_path = out_dir / "transcripts.jsonl"
        with t_path.open("w", encoding="utf-8") as fh:
            for ep in self.transcripts:
                fh.write(json.dumps(asdict(ep)) + "\n")

        wiki_dir = out_dir / "wiki"
        wiki_dir.mkdir(exist_ok=True)
        for cid, card in self.wiki.items():
            md = [
                f"# {card.title} (`{cid}`)",
                "",
                f"- **Governing First-Principle Law**: {card.governing_principle}",
                f"- **Mechanism Tags**: {', '.join(sorted(card.mechanism_tags))}",
                f"- **Tool Bindings**: {', '.join(card.tool_bindings)}",
                f"- **Bottom Reasoning Traces**: {', '.join(card.linked_trace_ids)}",
                f"- **Last Practiced Day**: `{card.last_practiced_day}` (Deck Epoch `{card.calibrated_deck_epoch}`)",
            ]
            (wiki_dir / f"{cid}.md").write_text("\n".join(md) + "\n", encoding="utf-8")

        mem_md = out_dir / "MEMORY.md"
        mem_md.write_text(self.render_injected_markdown() + "\n", encoding="utf-8")
        return {
            "transcripts": str(t_path),
            "wiki_dir": str(wiki_dir),
            "injected_memory": str(mem_md),
        }


def _apply_first_principle_scaling(params: dict[str, float], scaling: dict[str, float]) -> dict[str, float]:
    out = dict(params)
    visc = max(1.0, float(out.get("viscosity_cp", 1.0)))
    base_dead = float(out.get("nominal_dead_vol_ul", 5.0))
    slope = float(scaling.get("log_visc_dead_vol_slope", 0.0))
    evap_slope = float(scaling.get("temp_evap_margin_ul_per_10c", 0.0))
    temp_c = float(out.get("temp_c", 25.0))
    vapor_kpa = float(out.get("vapor_pressure_kpa", 2.3))
    air_gap_coef = float(scaling.get("volatile_air_gap_ul_per_kpa", 0.0))

    req_dead = base_dead * (1.0 + slope * math.log10(visc)) + evap_slope * max(0.0, (temp_c - 37.0) / 10.0)
    out["effective_dead_vol_ul"] = round(req_dead, 2)
    out["source_vol_ul"] = round(max(float(out.get("source_vol_ul", 0.0)), float(out.get("transfer_total_ul", 0.0)) + req_dead + 2.0), 2)
    if air_gap_coef > 0.0 and vapor_kpa > 4.0:
        out["air_gap_ul"] = round(min(15.0, air_gap_coef * (vapor_kpa - 2.3)), 2)
    if temp_c >= 80.0 and scaling.get("require_thermal_seal", 0.0) > 0.5:
        out["seal_required"] = 1.0
    return out


def _verify_adapted_twin(params: dict[str, float]) -> bool:
    visc = max(1.0, float(params.get("viscosity_cp", 1.0)))
    true_film_dead = float(params.get("nominal_dead_vol_ul", 5.0)) * (1.0 + 0.30 * math.log10(visc))
    source_ok = float(params.get("source_vol_ul", 0.0)) >= float(params.get("transfer_total_ul", 0.0)) + true_film_dead
    seal_ok = (float(params.get("temp_c", 25.0)) < 80.0) or (float(params.get("seal_required", 0.0)) >= 1.0)
    drip_ok = (float(params.get("vapor_pressure_kpa", 2.3)) <= 4.0) or (float(params.get("air_gap_ul", 0.0)) >= 3.0)
    return bool(source_ok and seal_ok and drip_ok)


def _verify_skill_readiness_lean_or_py(
    days_elapsed: int,
    stale_thresh: int,
    cal_epoch: int,
    cur_epoch: int,
    *,
    days_override: int,
    trace_reviewed: bool,
    micro_ok: bool,
    kernel: LeanBatchKernel | None,
) -> TrustVerdict:
    if kernel is not None and kernel.available:
        line = (
            f"MEM_SKILL\t{days_override}\t{stale_thresh}\t{cal_epoch}\t{cur_epoch}\t"
            f"{1 if trace_reviewed else 0}\t{1 if micro_ok else 0}"
        )
        return kernel.eval_lines([line])[0]
    rusty = (days_override > stale_thresh) or (cal_epoch != cur_epoch)
    if not rusty:
        return TrustVerdict(True, "memory_skill", "valid", "fresh skill")
    if not trace_reviewed:
        return TrustVerdict(False, "lab-rehearsal", "rusty_skill_requires_bottom_trace", "missing bottom trace")
    if not micro_ok:
        return TrustVerdict(False, "lab-rehearsal", "rusty_skill_requires_micro_rehearsal", "failed micro rehearsal")
    return TrustVerdict(True, "memory_skill", "valid", "certified rusty refresh")


def _verify_novel_onboarding_lean_or_py(
    *,
    seen_before: bool,
    analogy_sim_permille: int,
    min_analogy_permille: int,
    trace_loaded: bool,
    tools_queried: bool,
    twin_ok: bool,
    kernel: LeanBatchKernel | None,
) -> TrustVerdict:
    if kernel is not None and kernel.available:
        line = (
            f"MEM_NOVEL\t{1 if seen_before else 0}\t{analogy_sim_permille}\t{min_analogy_permille}\t"
            f"{1 if trace_loaded else 0}\t{1 if tools_queried else 0}\t{1 if twin_ok else 0}"
        )
        return kernel.eval_lines([line])[0]
    if seen_before:
        return (
            TrustVerdict(True, "memory_novel", "valid", "known")
            if twin_ok
            else TrustVerdict(False, "lab-rehearsal", "known_skill_twin_verified", "failed twin")
        )
    if analogy_sim_permille < min_analogy_permille:
        return TrustVerdict(False, "lab-ask-why", "novel_requires_structural_analogy", "low analogy")
    if not trace_loaded:
        return TrustVerdict(False, "lab-ask-why", "novel_requires_bottom_reasoning_trace", "no bottom trace")
    if not tools_queried:
        return TrustVerdict(False, "lab-automation-atlas", "novel_requires_tool_spec_lookup", "no tool query")
    if not twin_ok:
        return TrustVerdict(False, "lab-rehearsal", "novel_requires_twin_dry_run", "failed twin")
    return TrustVerdict(True, "memory_novel", "valid", "certified novel onboarding")


def build_seed_undergrad_memory() -> UndergradMemoryStore:
    """Construct a realistic pre-populated undergraduate memory store with certified traces & noise."""
    store = UndergradMemoryStore(token_budget=260, min_salience_permille=500, stale_threshold_days=30)

    # 1. Certified Viscous Rheology Lesson + Bottom Reasoning Trace
    bt_visc = BottomReasoningTrace(
        trace_id="trace-visc-01",
        concept_id="viscous-liquid-handling",
        symptom="Multi-dispense of 80% glycerol underflowed on well 6 with nominal 5 uL dead reserve.",
        first_principle_law="Hagen-Poiseuille viscous wall-film retention scales dead volume as V_dead * (1 + 0.30 * log10(mu_cp)).",
        causal_chain="mu=60 cP slows blowout drainage -> ~12.7 uL film remains adhered -> source exhausts early.",
        lean_rule_witness="stepbot :: distribute_disposal_volume_conservation",
        parameter_scaling={"log_visc_dead_vol_slope": 0.32},
    )
    store.record_episode(
        EpisodicTranscript(
            episode_id="ep-001",
            day_index=10,
            deck_epoch=1,
            assay_name="glycerol_enzyme_stock_aliq",
            concept_id="viscous-liquid-handling",
            raw_events=["pick_tip(P300)", "aspirate(200, glycerol_80)", "underflow_alarm(well_6)"],
            outcome_status="VERIFIED_GUARDRAIL_LESSON",
            bottom_trace=bt_visc,
        ),
        note_summary="Scale source dead-volume reserve log-linearly with viscosity (log10 mu_cp) and slow blowout.",
        salience_permille=920,
        mechanism_tags={"pipetting", "high-viscosity", "dead-volume", "surfactant-or-polyol", "multi-dispense"},
        tool_bindings=["stepbot", "lab-rehearsal"],
    )

    # 2. Certified Volatile Solvent + Thermal Sealing Lesson
    bt_vol = BottomReasoningTrace(
        trace_id="trace-vol-02",
        concept_id="volatile-and-thermal-containment",
        symptom="Ethanol wash dripped in transit across deck and unsealed 92 C digest lost 38% volume.",
        first_principle_law="Raoult/Antoine headspace vapor pressure requires trailing air-gap above 4 kPa and mandatory plate seal >= 80 C.",
        causal_chain="High vapor pressure expands pipette headspace pushing droplets out; >=80 C open incubation boils meniscus.",
        lean_rule_witness="lab-rehearsal :: high_temp_requires_seal",
        parameter_scaling={"volatile_air_gap_ul_per_kpa": 0.85, "require_thermal_seal": 1.0, "temp_evap_margin_ul_per_10c": 1.5},
    )
    store.record_episode(
        EpisodicTranscript(
            episode_id="ep-002",
            day_index=25,
            deck_epoch=1,
            assay_name="ethanol_wash_and_thermolysis",
            concept_id="volatile-and-thermal-containment",
            raw_events=["aspirate(150, etoh_80)", "drip_detected(slot_4)", "incubate(92C, unsealed)"],
            outcome_status="VERIFIED_GUARDRAIL_LESSON",
            bottom_trace=bt_vol,
        ),
        note_summary="Add vapor-pressure-scaled trailing air-gap (>4 kPa) and enforce sealWell before >=80 C heating.",
        salience_permille=890,
        mechanism_tags={"pipetting", "volatile-solvent", "high-temp", "headspace-pressure", "thermal-cycling"},
        tool_bindings=["stepbot", "lab-rehearsal", "lab-automation-atlas"],
    )

    # 3. Uncertified Hardware Glitch (MUST be quarantined by Dreaming!)
    bt_poison = BottomReasoningTrace(
        trace_id="trace-bad-03",
        concept_id="false-catalyst-inactivity",
        symptom="Zero fluorescence readout on scaffold-7.",
        first_principle_law="Scaffold-7 is biochemically inactive.",
        causal_chain="Signal was zero.",
        lean_rule_witness="none",
        parameter_scaling={},
        attribution_certified=False,
    )
    store.record_episode(
        EpisodicTranscript(
            episode_id="ep-003",
            day_index=28,
            deck_epoch=1,
            assay_name="scaffold7_screen",
            concept_id="false-catalyst-inactivity",
            raw_events=["acoustic_anomaly_spike", "fluorescence=0.01"],
            outcome_status="EXECUTION_ARTIFACT",
            bottom_trace=bt_poison,
        ),
        note_summary="Never test scaffold-7 family again; completely inactive.",
        salience_permille=960,
        mechanism_tags={"screening"},
        tool_bindings=["lab-decide"],
    )

    store.dream_consolidate()
    return store
