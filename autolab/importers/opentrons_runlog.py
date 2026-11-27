"""Fail-closed Opentrons runlog -> AutoLabLean `REHEARSAL` importer.

Simulates real Opentrons Python API v2 (`.py`) and JSON (`.json`) protocols on CPU
via `opentrons.simulate.simulate()` (optional `[real-data]` extra `opentrons>=8.0`),
or accepts an already-captured runlog list in offline unit tests (`import_runlog`),
and lowers the executed command tree into an initial `DeckState` (`wells`,
`pip_min`, `pip_max`, `proto_hash`, `failed_hashes`) plus `REHEARSAL` steps
(`pick`, `drop`, `xfer`, `mix`, `inc`, `seal`, `thaw`).

Strict fail-closed contract:
- Every command emitted by `opentrons.simulate` is classified explicitly.
- Commands or hardware capabilities outside the 7-operator `REHEARSAL` language
  (such as magnetic modules, heater-shaker agitation, robotic labware grippers,
  `return_tip`, `unseal` / reopening a sealed thermocycler before further steps,
  liquid disposal to trash, or simultaneous tips on multiple mounts) raise
  `UnsupportedProtocolStepError(reason)` and are NEVER dropped silently.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from autolab.trust_regime import format_rehearsal_tsv


class UnsupportedProtocolStepError(ValueError):
    """Raised when an Opentrons protocol uses a command or state outside `REHEARSAL`."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail or reason
        msg = f"{reason}: {detail}" if detail and detail != reason else reason
        super().__init__(msg)


@dataclass(frozen=True)
class ImportedRehearsalProtocol:
    """Lowered `REHEARSAL` deck & step sequence with full provenance."""

    pip_min: int
    pip_max: int
    proto_hash: int
    failed_hashes: tuple[int, ...]
    wells: list[dict[str, Any]]
    steps: list[tuple[Any, ...]]
    well_labels: dict[int, str] = field(default_factory=dict)
    channel_mode: str = "single"
    pipette_models: tuple[str, ...] = ()
    non_mutating_commands: tuple[str, ...] = ()

    def to_tsv(self) -> str:
        return format_rehearsal_tsv(
            self.pip_min,
            self.pip_max,
            self.proto_hash,
            self.failed_hashes,
            self.wells,
            self.steps,
        )


@dataclass
class _RunlogNode:
    index: int
    level: int
    name: str | None
    payload: Mapping[str, Any]
    children: list["_RunlogNode"] = field(default_factory=list)


@dataclass
class _WellMeta:
    key: tuple[str, str]
    slot_label: str
    labware_load_name: str
    well_name: str
    max_volume_ul: float
    labware_rows: int
    module_kind: str | None = None
    explicit_liquid_vol_ul: float | None = None
    explicit_has_buffer: bool | None = None
    explicit_has_sample: bool | None = None
    explicit_frozen: bool = False
    explicit_sealed: bool = False


_WELL_TEXT_RE = re.compile(
    r"^(?P<well>[A-Z]{1,2}\d{1,2})\s+of\s+(?P<labware>.+?)\s+on\s+(?:slot\s+)?(?P<slot>.+)$"
)
_HS_TEMP_RE = re.compile(r"to\s+(-?\d+(?:\.\d+)?)\s*°?C", re.IGNORECASE)
_LID_TEMP_RE = re.compile(r"to\s+(-?\d+(?:\.\d+)?)\s*°?C", re.IGNORECASE)


def _compute_proto_hash(seed_text: str) -> int:
    digest = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return (int(digest[:12], 16) % 900_000_000) + 1


def _build_command_tree(runlog: Sequence[Mapping[str, Any]]) -> list[_RunlogNode]:
    roots: list[_RunlogNode] = []
    stack: list[_RunlogNode] = []
    for idx, raw in enumerate(runlog):
        if not isinstance(raw, Mapping) or "payload" not in raw:
            raise UnsupportedProtocolStepError("malformed_runlog_entry", f"Entry {idx} missing payload")
        lvl = int(raw.get("level", 0))
        if lvl < 0:
            raise UnsupportedProtocolStepError("malformed_runlog_entry", f"Negative level {lvl} at entry {idx}")
        payload = raw["payload"]
        if not isinstance(payload, Mapping):
            raise UnsupportedProtocolStepError("malformed_runlog_entry", f"Entry {idx} payload is not a mapping")
        node = _RunlogNode(
            index=idx,
            level=lvl,
            name=str(raw["name"]) if raw.get("name") is not None else None,
            payload=payload,
        )
        while stack and stack[-1].level >= lvl:
            stack.pop()
        if stack:
            stack[-1].children.append(node)
        else:
            roots.append(node)
        stack.append(node)
    return roots


def _is_disposal_object(loc: Any) -> bool:
    if loc is None:
        return False
    cls_name = type(loc).__name__
    if cls_name in ("TrashBin", "WasteChute", "_MockTrash"):
        return True
    if isinstance(loc, Mapping) and loc.get("kind") in ("trash", "waste_chute"):
        return True
    if isinstance(loc, str) and ("trash" in loc.lower() or "waste chute" in loc.lower()):
        return True
    # Fixed trash labware check on Opentrons OT-2 (`opentrons_1_trash_1100ml_fixed` on slot 12)
    well_obj = getattr(loc, "labware", None)
    if well_obj is not None and hasattr(well_obj, "is_well"):
        try:
            if well_obj.is_well:
                well_obj = well_obj.as_well()
        except Exception:
            pass
    target = well_obj if hasattr(well_obj, "parent") else loc
    parent = getattr(target, "parent", None)
    load_name = str(getattr(parent, "load_name", "")).lower()
    if "trash" in load_name:
        return True
    try:
        params = parent._core.get_definition().get("parameters", {})
        if "quirks" in params and "fixedTrash" in params.get("quirks", []):
            return True
    except Exception:
        pass
    return False


def _detect_module_kind(parent_obj: Any) -> tuple[str, str | None]:
    """Return `(slot_label, module_kind)` for a labware's parent (deck slot, adapter, or module)."""
    cur = parent_obj
    mod_kind: str | None = None
    visited = 0
    while cur is not None and visited < 6:
        visited += 1
        if isinstance(cur, (int, str)):
            return str(cur), mod_kind
        cls_low = type(cur).__name__.lower()
        repr_low = repr(cur).lower()
        for tag, kind in (
            ("thermocycler", "thermocycler"),
            ("temperature", "temperature"),
            ("tempdeck", "temperature"),
            ("heatershaker", "heater_shaker"),
            ("heater-shaker", "heater_shaker"),
            ("magnetic", "magnetic"),
            ("magdeck", "magnetic"),
        ):
            if tag in cls_low or tag in repr_low:
                mod_kind = mod_kind or kind
                break
        nxt = getattr(cur, "parent", None)
        if nxt is None or nxt is cur:
            return str(cur), mod_kind
        cur = nxt
    return str(parent_obj), mod_kind


def _extract_well_meta(loc: Any, registry: dict[tuple[str, str], _WellMeta]) -> tuple[str, str]:
    """Unwrap an Opentrons `Well`, `Location`, or mock dict/string into a canonical `(slot, well)` key."""
    if loc is None:
        raise UnsupportedProtocolStepError("missing_well_location", "Command location is None")
    if _is_disposal_object(loc):
        raise UnsupportedProtocolStepError("unexpected_disposal_location", f"Expected well, got disposal {loc!r}")

    # 1. Mock dictionary location (used in zero-dependency offline unit tests)
    if isinstance(loc, Mapping):
        slot_lbl = str(loc.get("slot", "1"))
        wname = str(loc["well"])
        key = (slot_lbl, wname)
        if key not in registry:
            registry[key] = _WellMeta(
                key=key,
                slot_label=slot_lbl,
                labware_load_name=str(loc.get("labware", "mock_96_wellplate")),
                well_name=wname,
                max_volume_ul=float(loc.get("max_volume", 300.0)),
                labware_rows=int(loc.get("rows", 8)),
                module_kind=loc.get("module"),
                explicit_liquid_vol_ul=(float(loc["initial_volume"]) if "initial_volume" in loc else None),
                explicit_has_buffer=loc.get("has_buffer"),
                explicit_has_sample=loc.get("has_sample"),
                explicit_frozen=bool(loc.get("frozen", False)),
                explicit_sealed=bool(loc.get("sealed", False)),
            )
        return key

    # 2. Live Opentrons `Location` or `Well`
    well_obj = loc
    if hasattr(loc, "labware") and not hasattr(loc, "well_name"):
        lw_holder = loc.labware
        if hasattr(lw_holder, "as_well"):
            try:
                well_obj = lw_holder.as_well()
            except Exception as exc:
                raise UnsupportedProtocolStepError(
                    "non_well_location_target", f"Location does not point to a single well: {loc!r}"
                ) from exc
        else:
            well_obj = lw_holder

    if hasattr(well_obj, "well_name") and hasattr(well_obj, "max_volume"):
        wname = str(well_obj.well_name)
        lw = getattr(well_obj, "parent", None)
        load_name = str(getattr(lw, "load_name", "unknown_labware"))
        slot_lbl, mod_kind = _detect_module_kind(getattr(lw, "parent", "1"))
        rows = 8
        try:
            cols = lw.columns()
            if cols and len(cols[0]) > 0:
                rows = len(cols[0])
        except Exception:
            pass
        key = (f"{slot_lbl}:{load_name}", wname)
        if key not in registry:
            registry[key] = _WellMeta(
                key=key,
                slot_label=slot_lbl,
                labware_load_name=load_name,
                well_name=wname,
                max_volume_ul=float(well_obj.max_volume),
                labware_rows=rows,
                module_kind=mod_kind,
            )
        return key

    # 3. Formatted string fallback
    if isinstance(loc, str):
        m = _WELL_TEXT_RE.match(loc.strip())
        if m:
            slot_lbl = m.group("slot").strip()
            lw_name = m.group("labware").strip()
            wname = m.group("well").strip()
            key = (f"{slot_lbl}:{lw_name}", wname)
            if key not in registry:
                registry[key] = _WellMeta(
                    key=key,
                    slot_label=slot_lbl,
                    labware_load_name=lw_name,
                    well_name=wname,
                    max_volume_ul=300.0,
                    labware_rows=8,
                )
            return key

    raise UnsupportedProtocolStepError("unrecognized_location_object", f"Cannot resolve well from {loc!r}")


def _extract_instrument_info(inst: Any) -> tuple[str, str, float, float, int]:
    """Return `(mount_id, model_name, min_vol_ul, max_vol_ul, channels)`."""
    if isinstance(inst, Mapping):
        mount = str(inst.get("mount", "left"))
        model = str(inst.get("model", "p300_single_gen2"))
        min_v = float(inst.get("min_volume", 20.0))
        max_v = float(inst.get("max_volume", 300.0))
        ch = int(inst.get("channels", 1))
        return mount, model, min_v, max_v, ch

    mount = str(getattr(inst, "mount", "left"))
    model = str(getattr(inst, "name", getattr(inst, "model", "unknown_pipette")))
    min_v = float(getattr(inst, "min_volume", 1.0))
    max_v = float(getattr(inst, "max_volume", 300.0))
    tip_racks = getattr(inst, "tip_racks", None) or []
    rack_caps: list[float] = []
    for rack in tip_racks:
        try:
            wells = rack.wells()
            if wells:
                rack_caps.append(float(wells[0].max_volume))
        except Exception:
            pass
    if rack_caps:
        max_v = min(max_v, min(rack_caps))
    ch = int(getattr(inst, "channels", 1))
    return mount, model, min_v, max_v, ch


def _classify_node(node: _RunlogNode) -> str:
    """Classify an Opentrons runlog node into a canonical command kind (never returning None)."""
    name = node.name or ""
    payload = node.payload
    text = str(payload.get("text", "")).strip()

    if name:
        short = name.removeprefix("command.")
        return short

    # Exact structural & text signatures from `opentrons.legacy_commands`:
    if ("source" in payload and ("dest" in payload or "destination" in payload)) or (
        "instrument" in payload and text.startswith(("Transferring ", "Distributing ", "Consolidating "))
    ):
        return "COMPOSITE_TRANSFER"
    if "repetitions" in payload and "volume" in payload and (
        text.startswith(("Mixing ", "Dynamically mixing ")) or "location" in payload or "aspirate_start_location" in payload
    ):
        return "MIX"
    if text.startswith("Picking up tip from "):
        return "PICK_UP_TIP"
    if text.startswith("Dropping tip into "):
        return "DROP_TIP_IN_DISPOSAL_LOCATION" if _is_disposal_object(payload.get("location")) else "DROP_TIP"
    if text == "Returning tip" or text.startswith("Returning tip"):
        return "RETURN_TIP"
    if text.startswith("Aspirating "):
        return "ASPIRATE"
    if text.startswith("Dispensing "):
        if _is_disposal_object(payload.get("location")):
            return "DISPENSE_IN_DISPOSAL_LOCATION"
        return "DISPENSE"
    if text.startswith("Blowing out "):
        if _is_disposal_object(payload.get("location")):
            return "BLOW_OUT_IN_DISPOSAL_LOCATION"
        return "BLOW_OUT"
    if text.startswith("Air gap"):
        return "AIR_GAP"
    if text == "Touching tip" or text.startswith("Touching tip"):
        return "TOUCH_TIP"
    if text.startswith("Homing pipette plunger"):
        return "HOME"
    if text.startswith("Moving to "):
        if "absolute_axes" in payload:
            return "ROBOT_MOVE_AXES_TO"
        if "relative_axes" in payload:
            return "ROBOT_MOVE_RELATIVE_TO"
        return "MOVE_TO"
    if text.startswith("Delaying for ") or ("minutes" in payload and "seconds" in payload):
        return "DELAY"
    if text.startswith("Pausing robot operation") or "userMessage" in payload:
        return "PAUSE"
    if text == "Resuming robot operation":
        return "RESUME"
    if text.startswith("Sealing to "):
        return "SEAL"
    if text.startswith("Unsealing from "):
        return "UNSEAL"
    if text.startswith("Pressurize pipette"):
        return "PRESSURIZE"
    if text.startswith("Configure pipette on ") and "layout" in text:
        return "CONFIGURE_NOZZLE_LAYOUT"
    if text.startswith("Configure pipette on ") and "to handle" in text:
        return "CONFIGURE_FOR_VOLUME"

    # Module commands (`opentrons.legacy_commands.module_commands`)
    if text in ("Engaging Magnetic Module", "Disengaging Magnetic Module", "Calibrating Magnetic Module"):
        return "MAGDECK"
    if text.startswith("Setting Temperature Module temperature") or (
        "celsius" in payload and "Setting" in text
    ):
        return "TEMPDECK_SET_TEMP"
    if text.startswith("Waiting for Temperature Module to reach temperature") or (
        "celsius" in payload and "Waiting" in text
    ):
        return "TEMPDECK_AWAIT_TEMP"
    if text == "Deactivating Temperature Module":
        return "TEMPDECK_DEACTIVATE"
    if text == "Closing Thermocycler lid":
        return "THERMOCYCLER_CLOSE"
    if text == "Opening Thermocycler lid":
        return "THERMOCYCLER_OPEN"
    if text.startswith("Setting Thermocycler well block temperature") or (
        "temperature" in payload and "hold_time" in payload
    ):
        return "THERMOCYCLER_SET_BLOCK_TEMP"
    if text.startswith("Starting to set Thermocycler well block temperature"):
        return "THERMOCYCLER_START_SET_BLOCK_TEMP"
    if "steps" in payload and "repetitions" in text and "thermocycler" in text.lower():
        return "THERMOCYCLER_EXECUTE_PROFILE"
    if text in (
        "Waiting for hold time duration",
        "Waiting for Thermocycler to reach target",
        "Waiting for Thermocycler lid to reach target temperature",
        "Deactivating Thermocycler lid heating",
        "Deactivating Thermocycler well block heating",
        "Deactivating Thermocycler",
    ) or text.startswith(("Setting Thermocycler lid temperature", "Starting to set Thermocycler lid temperature")):
        return "THERMOCYCLER_AUX"
    if text.startswith("Setting Target Temperature of Heater-Shaker"):
        return "HEATER_SHAKER_SET_TARGET_TEMPERATURE"
    if text == "Waiting for Heater-Shaker to reach target temperature":
        return "HEATER_SHAKER_WAIT_FOR_TEMPERATURE"
    if text in ("Deactivating Heater", "Latching labware on Heater-Shaker", "Unlatching labware on Heater-Shaker"):
        return "HEATER_SHAKER_AUX"
    if "Shake at " in text or text == "Deactivating Shaker":
        return "HEATER_SHAKER_SHAKE"
    if any(
        text.startswith(pfx)
        for pfx in (
            "Opening the gripper jaw",
            "Closing the gripper jaw",
            "Moving labware",
            "Configuring ",
            "Retrieving labware from ",
            "Storing labware to ",
            "Emptying ",
            "Filling ",
        )
    ):
        return "GRIPPER_OR_STACKER"
    if text.startswith("Capturing an image") or "resolution" in payload:
        return "CAPTURE_IMAGE"
    if text.startswith(("Waiting for tasks", "Creating background timer")):
        return "TASK_SYNC"

    # Notice: `protocol.comment(msg)` sets `payload = {"text": msg}` with ONLY the `"text"` key!
    if set(payload.keys()) == {"text"}:
        return "COMMENT"

    raise UnsupportedProtocolStepError("unrecognized_runlog_command", f"Unrecognized command payload: {text[:80]!r}")


def _ul_to_tenths(volume_ul: float, context: str) -> int:
    if isinstance(volume_ul, bool) or not isinstance(volume_ul, (int, float)) or not math.isfinite(float(volume_ul)):
        raise UnsupportedProtocolStepError("invalid_volume_value", f"Non-finite volume {volume_ul!r} in {context}")
    tenths = int(round(float(volume_ul) * 10.0))
    if tenths <= 0:
        raise UnsupportedProtocolStepError("non_positive_volume", f"Volume {volume_ul} uL -> {tenths} tenths <= 0 in {context}")
    return tenths


def import_runlog(
    runlog: Sequence[Mapping[str, Any]],
    *,
    protocol_id: str = "opentrons_protocol",
    initial_liquids: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    failed_hashes: Sequence[int] = (),
    allow_pause: bool = False,
) -> ImportedRehearsalProtocol:
    """Lower an Opentrons simulation runlog into an `ImportedRehearsalProtocol`.

    Raises `UnsupportedProtocolStepError` on any unsupported step or hardware mode.
    Never drops unsupported steps silently.
    """
    if not runlog:
        raise UnsupportedProtocolStepError("empty_runlog", "Protocol simulation produced zero runlog commands")

    roots = _build_command_tree(runlog)
    well_registry: dict[tuple[str, str], _WellMeta] = {}
    pipettes_seen: dict[str, tuple[str, float, float, int]] = {}
    channels_seen: set[int] = set()
    mounted_tips: set[str] = set()
    barrel_queue: list[tuple[tuple[str, str], int]] = []
    air_gap_tenths = 0

    # Symbolic steps temporarily hold `(slot_key, well_name)` keys until deterministic well IDs are assigned
    raw_steps: list[tuple[Any, ...]] = []
    non_mutating: list[str] = []

    tc_sealed = False
    tc_reopened_after_seal = False
    active_temp_by_module: dict[str, int] = {}

    def _module_well_keys(mod_kind: str) -> list[tuple[str, str]]:
        keys = [k for k, m in well_registry.items() if m.module_kind == mod_kind]
        return sorted(keys)

    def _guard_not_reopened_tc(target_key: tuple[str, str]) -> None:
        meta = well_registry[target_key]
        if meta.module_kind == "thermocycler" and tc_reopened_after_seal:
            raise UnsupportedProtocolStepError(
                "thermocycler_reopen_unseal_not_in_rehearsal_dsl",
                "Thermocycler lid was closed (sealed) and later reopened before additional plate operations; "
                "REHEARSAL has `seal` but no `unseal` operator",
            )

    def _record_pipette(inst: Any) -> str:
        mount, model, min_v, max_v, ch = _extract_instrument_info(inst)
        if ch not in (1, 8):
            raise UnsupportedProtocolStepError(
                "unsupported_pipette_channel_count", f"Pipette {model} has {ch} channels (only 1 or 8 supported)"
            )
        channels_seen.add(ch)
        if len(channels_seen) > 1:
            raise UnsupportedProtocolStepError(
                "mixed_single_and_multichannel_pipettes",
                "Protocol mixes 1-channel and 8-channel pipettes across shared deck state",
            )
        prev = pipettes_seen.get(mount)
        if prev is None:
            pipettes_seen[mount] = (model, min_v, max_v, ch)
        else:
            pipettes_seen[mount] = (model, min(prev[1], min_v), max(prev[2], max_v), ch)
        return mount

    def _visit(node: _RunlogNode) -> None:
        nonlocal air_gap_tenths, tc_sealed, tc_reopened_after_seal

        kind = _classify_node(node)
        p = node.payload
        text = str(p.get("text", "")).strip()

        if kind in (
            "COMPOSITE_TRANSFER",
            "TRANSFER",
            "DISTRIBUTE",
            "CONSOLIDATE",
            "TRANSFER_WITH_LIQUID_CLASS",
            "DISTRIBUTE_WITH_LIQUID_CLASS",
            "CONSOLIDATE_WITH_LIQUID_CLASS",
        ):
            if node.children:
                for ch in node.children:
                    _visit(ch)
                return
            # Leaf mock transfer without expanded children
            if "source" in p and ("dest" in p or "destination" in p) and "volume" in p:
                if "instrument" in p:
                    _record_pipette(p["instrument"])
                src_loc = p["source"]
                dst_loc = p.get("dest", p.get("destination"))
                if isinstance(src_loc, (list, tuple)) and len(src_loc) == 1:
                    src_loc = src_loc[0]
                if isinstance(dst_loc, (list, tuple)) and len(dst_loc) == 1:
                    dst_loc = dst_loc[0]
                if isinstance(src_loc, (list, tuple)) or isinstance(dst_loc, (list, tuple)):
                    raise UnsupportedProtocolStepError(
                        "unexpanded_multiwell_composite_transfer",
                        "Composite multi-well transfer has no expanded atomic child commands",
                    )
                s_key = _extract_well_meta(src_loc, well_registry)
                d_key = _extract_well_meta(dst_loc, well_registry)
                _guard_not_reopened_tc(s_key)
                _guard_not_reopened_tc(d_key)
                v_tenth = _ul_to_tenths(float(p["volume"]), "transfer")
                raw_steps.append(("xfer", s_key, d_key, v_tenth))
                return
            raise UnsupportedProtocolStepError("empty_composite_transfer", text)

        if kind == "PICK_UP_TIP":
            mount = _record_pipette(p["instrument"]) if "instrument" in p else "left"
            other_mounts = mounted_tips - {mount}
            if other_mounts:
                raise UnsupportedProtocolStepError(
                    "simultaneous_multi_pipette_tips",
                    f"Mount {mount!r} picked up a tip while {sorted(other_mounts)!r} still holds a tip",
                )
            mounted_tips.add(mount)
            raw_steps.append(("pick",))
            return

        if kind in ("DROP_TIP", "DROP_TIP_IN_DISPOSAL_LOCATION"):
            mount = _record_pipette(p["instrument"]) if "instrument" in p else "left"
            if barrel_queue:
                rem = sum(v for _, v in barrel_queue)
                raise UnsupportedProtocolStepError(
                    "undispensed_liquid_discarded_with_tip",
                    f"Pipette dropped tip while still holding {rem / 10.0:.1f} uL of aspirated liquid",
                )
            air_gap_tenths = 0
            mounted_tips.discard(mount)
            raw_steps.append(("drop",))
            return

        if kind == "RETURN_TIP":
            raise UnsupportedProtocolStepError(
                "return_tip_not_modeled_in_rehearsal",
                "Returning used tips to the tip rack is rejected because REHEARSAL `pick` assumes clean tips",
            )

        if kind == "ASPIRATE":
            if "instrument" in p:
                _record_pipette(p["instrument"])
            if _is_disposal_object(p.get("location")):
                raise UnsupportedProtocolStepError("aspirate_from_trash_unsupported", text)
            s_key = _extract_well_meta(p.get("location"), well_registry)
            _guard_not_reopened_tc(s_key)
            v_tenth = _ul_to_tenths(float(p["volume"]), "aspirate")
            if barrel_queue and barrel_queue[-1][0] == s_key:
                barrel_queue[-1] = (s_key, barrel_queue[-1][1] + v_tenth)
            else:
                barrel_queue.append((s_key, v_tenth))
            return

        if kind == "AIR_GAP":
            if "instrument" in p:
                _record_pipette(p["instrument"])
            vol = p.get("volume")
            if vol is not None and float(vol) > 0:
                air_gap_tenths += int(round(float(vol) * 10.0))
            non_mutating.append("AIR_GAP")
            return

        if kind == "DISPENSE":
            if "instrument" in p:
                _record_pipette(p["instrument"])
            d_key = _extract_well_meta(p.get("location"), well_registry)
            _guard_not_reopened_tc(d_key)
            disp_tenth = _ul_to_tenths(float(p["volume"]), "dispense")
            if air_gap_tenths > 0:
                used_air = min(air_gap_tenths, disp_tenth)
                air_gap_tenths -= used_air
                disp_tenth -= used_air
            if disp_tenth == 0:
                return
            total_avail = sum(v for _, v in barrel_queue)
            if disp_tenth > total_avail:
                # Allow 0.1 uL (1 tenth) float rounding slack when multi-dispense splits e.g. 33.33 uL
                if disp_tenth - total_avail == 1 and barrel_queue:
                    disp_tenth = total_avail
                else:
                    raise UnsupportedProtocolStepError(
                        "dispense_exceeds_aspirated_barrel_volume",
                        f"Dispensed {disp_tenth / 10.0:.1f} uL into {d_key}, but barrel holds {total_avail / 10.0:.1f} uL",
                    )
            remaining = disp_tenth
            while remaining > 0 and barrel_queue:
                s_key, avail = barrel_queue[0]
                chunk = min(avail, remaining)
                raw_steps.append(("xfer", s_key, d_key, chunk))
                remaining -= chunk
                if chunk == avail:
                    barrel_queue.pop(0)
                else:
                    barrel_queue[0] = (s_key, avail - chunk)
            return

        if kind == "DISPENSE_IN_DISPOSAL_LOCATION":
            raise UnsupportedProtocolStepError(
                "liquid_dispense_to_trash_unsupported",
                f"Dispensing liquid into trash/waste chute cannot conserve deck volume: {text}",
            )

        if kind in ("BLOW_OUT", "BLOW_OUT_IN_DISPOSAL_LOCATION"):
            if "instrument" in p:
                _record_pipette(p["instrument"])
            air_gap_tenths = 0
            if barrel_queue:
                # If residual disposal volume is blown back into its exact source well, net liquid is conserved!
                loc = p.get("location")
                if kind == "BLOW_OUT" and loc is not None and not _is_disposal_object(loc):
                    b_key = _extract_well_meta(loc, well_registry)
                    if all(s_key == b_key for s_key, _ in barrel_queue):
                        barrel_queue.clear()
                        non_mutating.append("BLOW_OUT_TO_SOURCE")
                        return
                rem = sum(v for _, v in barrel_queue)
                raise UnsupportedProtocolStepError(
                    "residual_disposal_volume_blown_out_to_trash",
                    f"Blow-out discarded {rem / 10.0:.1f} uL of residual disposal volume outside source well",
                )
            non_mutating.append(kind)
            return

        if kind == "MIX":
            if "instrument" in p:
                _record_pipette(p["instrument"])
            if barrel_queue:
                raise UnsupportedProtocolStepError(
                    "mix_with_nonempty_barrel",
                    "Mix invoked while pipette barrel already holds un-dispensed liquid",
                )
            loc = p.get("location") or p.get("aspirate_start_location")
            if loc is None and node.children:
                loc = node.children[0].payload.get("location")
            w_key = _extract_well_meta(loc, well_registry)
            _guard_not_reopened_tc(w_key)
            v_tenth = _ul_to_tenths(float(p["volume"]), "mix")
            reps = int(p["repetitions"])
            raw_steps.append(("mix", w_key, v_tenth, reps))
            return

        if kind == "SEAL":
            w_key = _extract_well_meta(p.get("location"), well_registry)
            raw_steps.append(("seal", w_key))
            return

        if kind == "UNSEAL":
            raise UnsupportedProtocolStepError(
                "unseal_not_in_rehearsal_dsl", "REHEARSAL step language has `seal` but no `unseal` operator"
            )

        if kind == "THERMOCYCLER_CLOSE":
            tc_keys = _module_well_keys("thermocycler")
            if not tc_keys:
                non_mutating.append("THERMOCYCLER_CLOSE_EMPTY")
                tc_sealed = True
                return
            for k in tc_keys:
                raw_steps.append(("seal", k))
            tc_sealed = True
            return

        if kind == "THERMOCYCLER_OPEN":
            if tc_sealed:
                tc_reopened_after_seal = True
            non_mutating.append("THERMOCYCLER_OPEN")
            return

        if kind in ("THERMOCYCLER_SET_BLOCK_TEMP", "THERMOCYCLER_START_SET_BLOCK_TEMP"):
            temp_c = int(round(float(p["temperature"])))
            active_temp_by_module["thermocycler"] = temp_c
            hold = p.get("hold_time")
            tc_keys = _module_well_keys("thermocycler")
            if hold is not None and float(hold) > 0 and tc_keys:
                dur_s = max(1, int(round(float(hold))))
                for k in tc_keys:
                    raw_steps.append(("inc", k, temp_c, dur_s))
            return

        if kind in ("THERMOCYCLER_EXECUTE_PROFILE", "THERMOCYCLER_START_EXECUTE_PROFILE"):
            tc_keys = _module_well_keys("thermocycler")
            prof_steps = p.get("steps") or []
            if not tc_keys:
                raise UnsupportedProtocolStepError(
                    "thermocycler_profile_without_pipetted_wells",
                    "Thermocycler profile executed without any tracked wells on the thermocycler plate",
                )
            for pst in prof_steps:
                t_c = int(round(float(pst["temperature"])))
                h_s = float(pst.get("hold_time_seconds") or 0.0) + 60.0 * float(pst.get("hold_time_minutes") or 0.0)
                dur_s = max(1, int(round(h_s))) if h_s > 0 else 1
                for k in tc_keys:
                    raw_steps.append(("inc", k, t_c, dur_s))
            return

        if kind in ("TEMPDECK_SET_TEMP", "TEMPDECK_AWAIT_TEMP"):
            temp_c = int(round(float(p["celsius"])))
            active_temp_by_module["temperature"] = temp_c
            t_keys = _module_well_keys("temperature")
            if kind == "TEMPDECK_AWAIT_TEMP" and t_keys:
                for k in t_keys:
                    raw_steps.append(("inc", k, temp_c, 60))
            return

        if kind == "TEMPDECK_DEACTIVATE":
            active_temp_by_module.pop("temperature", None)
            non_mutating.append(kind)
            return

        if kind == "HEATER_SHAKER_SET_TARGET_TEMPERATURE":
            m = _HS_TEMP_RE.search(text)
            if not m and "celsius" not in p:
                raise UnsupportedProtocolStepError("unparseable_heater_shaker_temperature", text)
            temp_c = int(round(float(p["celsius"]) if "celsius" in p else float(m.group(1))))
            active_temp_by_module["heater_shaker"] = temp_c
            return

        if kind == "HEATER_SHAKER_WAIT_FOR_TEMPERATURE":
            if "heater_shaker" in active_temp_by_module:
                hs_keys = _module_well_keys("heater_shaker")
                for k in hs_keys:
                    raw_steps.append(("inc", k, active_temp_by_module["heater_shaker"], 60))
            return

        if kind == "DELAY":
            dur_s = int(round(float(p.get("minutes", 0.0)) * 60.0 + float(p.get("seconds", 0.0))))
            if dur_s > 0 and active_temp_by_module:
                for mod_k, temp_c in sorted(active_temp_by_module.items()):
                    for w_key in _module_well_keys(mod_k):
                        raw_steps.append(("inc", w_key, temp_c, dur_s))
            else:
                non_mutating.append("DELAY")
            return

        if kind == "PAUSE":
            if not allow_pause:
                raise UnsupportedProtocolStepError(
                    "manual_human_pause_intervention",
                    f"Protocol pauses for manual off-deck operator action: {text[:80]}",
                )
            non_mutating.append("PAUSE")
            return

        if kind in (
            "TOUCH_TIP",
            "HOME",
            "MOVE_TO",
            "MOVE_TO_DISPOSAL_LOCATION",
            "ROBOT_MOVE_TO",
            "ROBOT_MOVE_AXES_TO",
            "ROBOT_MOVE_RELATIVE_TO",
            "COMMENT",
            "RESUME",
            "THERMOCYCLER_AUX",
            "HEATER_SHAKER_AUX",
            "CONFIGURE_FOR_VOLUME",
            "TASK_SYNC",
        ):
            non_mutating.append(kind)
            return

        if kind == "MAGDECK":
            raise UnsupportedProtocolStepError("magnetic_module_command", text)
        if kind in (
            "HEATER_SHAKER_SHAKE",
            "HEATER_SHAKER_SET_SHAKE_SPEED",
            "HEATER_SHAKER_SET_AND_WAIT_FOR_SHAKE_SPEED",
            "HEATER_SHAKER_DEACTIVATE_SHAKER",
        ):
            raise UnsupportedProtocolStepError("heater_shaker_agitation_command", text)
        if kind in (
            "GRIPPER_OR_STACKER",
            "MOVE_LABWARE",
            "ROBOT_OPEN_GRIPPER_JAW",
            "ROBOT_CLOSE_GRIPPER_JAW",
            "FLEX_STACKER_SET_STORED_LABWARE",
            "FLEX_STACKER_RETRIEVE",
            "FLEX_STACKER_STORE",
            "FLEX_STACKER_EMPTY",
            "FLEX_STACKER_FILL",
        ):
            raise UnsupportedProtocolStepError("gripper_or_stacker_labware_move", text)
        if kind == "CONFIGURE_NOZZLE_LAYOUT":
            raise UnsupportedProtocolStepError("partial_nozzle_layout_command", text)
        if kind == "PRESSURIZE":
            raise UnsupportedProtocolStepError("resin_tip_pressurize_command", text)
        if kind == "CAPTURE_IMAGE":
            raise UnsupportedProtocolStepError("camera_capture_command", text)

        raise UnsupportedProtocolStepError("unsupported_command", f"{kind}: {text[:80]}")

    for root in roots:
        _visit(root)

    if barrel_queue:
        rem = sum(v for _, v in barrel_queue)
        raise UnsupportedProtocolStepError(
            "unmatched_aspirate_at_end_of_run",
            f"Run ended with {rem / 10.0:.1f} uL of aspirated liquid never dispensed",
        )

    if not raw_steps:
        raise UnsupportedProtocolStepError(
            "no_rehearsal_steps_emitted", "Protocol contained only comments/homing and zero pipetting or thermal steps"
        )

    if not pipettes_seen:
        pip_min, pip_max = 10, 3000
        active_channels = 1
        pip_models: tuple[str, ...] = ()
    else:
        pip_min = max(1, int(round(min(v[1] for v in pipettes_seen.values()) * 10.0)))
        pip_max = max(pip_min, int(round(max(v[2] for v in pipettes_seen.values()) * 10.0)))
        active_channels = next(iter(channels_seen)) if channels_seen else 1
        pip_models = tuple(sorted({v[0] for v in pipettes_seen.values()}))

    # Merge any caller-supplied initial liquid specifications
    if initial_liquids:
        for k, spec in initial_liquids.items():
            if k in well_registry:
                wm = well_registry[k]
                if "volume_ul" in spec:
                    wm.explicit_liquid_vol_ul = float(spec["volume_ul"])
                if "has_buffer" in spec:
                    wm.explicit_has_buffer = bool(spec["has_buffer"])
                if "has_sample" in spec:
                    wm.explicit_has_sample = bool(spec["has_sample"])
                if "frozen" in spec:
                    wm.explicit_frozen = bool(spec["frozen"])
                if "sealed" in spec:
                    wm.explicit_sealed = bool(spec["sealed"])

    # Assign deterministic 1-based well IDs sorted by `(slot_key, well_name)`
    sorted_keys = sorted(well_registry.keys())
    key_to_id = {k: idx + 1 for idx, k in enumerate(sorted_keys)}
    id_to_label = {
        key_to_id[k]: f"{well_registry[k].slot_label}:{well_registry[k].labware_load_name}[{well_registry[k].well_name}]"
        for k in sorted_keys
    }

    # Compute minimum pre-staged starting volume needed per well when protocol omits `Well.load_liquid`
    running_delta: dict[tuple[str, str], int] = {k: 0 for k in sorted_keys}
    min_delta: dict[tuple[str, str], int] = {k: 0 for k in sorted_keys}
    max_mix_deficit: dict[tuple[str, str], int] = {k: 0 for k in sorted_keys}
    first_touch_op: dict[tuple[str, str], str] = {}

    for st in raw_steps:
        op = st[0]
        if op == "xfer":
            _, sk, dk, v = st
            first_touch_op.setdefault(sk, "src")
            first_touch_op.setdefault(dk, "dst")
            running_delta[sk] -= v
            if running_delta[sk] < min_delta[sk]:
                min_delta[sk] = running_delta[sk]
            running_delta[dk] += v
        elif op == "mix":
            _, wk, v, _ = st
            first_touch_op.setdefault(wk, "mix")
            needed = v - running_delta[wk]
            if needed > max_mix_deficit[wk]:
                max_mix_deficit[wk] = needed

    wells_out: list[dict[str, Any]] = []
    for k in sorted_keys:
        wm = well_registry[k]
        wid = key_to_id[k]
        # For 8-channel pipettes dipping all 8 nozzles into a 1-row trough, scale trough capacity per nozzle
        divisor = active_channels if (active_channels > 1 and wm.labware_rows == 1) else 1
        cap_tenth = max(10, int(round(wm.max_volume_ul * 10.0 / divisor)))
        dead_tenth = min(50, max(0, cap_tenth // 20))

        if wm.explicit_liquid_vol_ul is not None:
            init_vol = max(0, int(round(wm.explicit_liquid_vol_ul * 10.0 / divisor)))
        else:
            req_draw = max(-min_delta[k], max_mix_deficit[k])
            if req_draw > 0:
                # Cap pre-staged volume at `cap_tenth`: if a protocol tries to draw more from one well
                # than its physical capacity allows, `AutoLabLean` will catch `enough_recoverable_volume`!
                init_vol = min(cap_tenth, req_draw + dead_tenth)
            else:
                init_vol = 0

        lw_low = wm.labware_load_name.lower()
        is_bulk_reservoir = ("reservoir" in lw_low) or (wm.max_volume_ul >= 5000.0)
        if wm.explicit_has_buffer is not None or wm.explicit_has_sample is not None:
            has_buf = bool(wm.explicit_has_buffer)
            has_smp = bool(wm.explicit_has_sample)
        elif init_vol == 0:
            has_buf, has_smp = False, False
        elif is_bulk_reservoir:
            has_buf, has_smp = True, False
        else:
            has_buf, has_smp = False, True

        solute_amt = init_vol if (has_smp and init_vol > 0) else 0
        wells_out.append(
            {
                "wellId": wid,
                "vol": init_vol,
                "cap": cap_tenth,
                "deadVol": dead_tenth,
                "soluteAmt": solute_amt,
                "hasBuffer": has_buf,
                "hasSample": has_smp,
                "frozen": wm.explicit_frozen,
                "sealed": wm.explicit_sealed,
            }
        )

    lowered_steps: list[tuple[Any, ...]] = []
    for st in raw_steps:
        op = st[0]
        if op in ("pick", "drop"):
            lowered_steps.append((op,))
        elif op == "xfer":
            _, sk, dk, v = st
            lowered_steps.append(("xfer", key_to_id[sk], key_to_id[dk], int(v)))
        elif op == "mix":
            _, wk, v, reps = st
            lowered_steps.append(("mix", key_to_id[wk], int(v), int(reps)))
        elif op == "inc":
            _, wk, temp_c, dur_s = st
            # Clamp negative sub-zero setpoints to 0 so `parseNat` parses cleanly and `incubate_temp_duration_bounds` fires!
            lowered_steps.append(("inc", key_to_id[wk], max(0, int(temp_c)), max(0, int(dur_s))))
        elif op in ("seal", "thaw"):
            _, wk = st
            lowered_steps.append((op, key_to_id[wk]))

    return ImportedRehearsalProtocol(
        pip_min=pip_min,
        pip_max=pip_max,
        proto_hash=_compute_proto_hash(protocol_id),
        failed_hashes=tuple(int(x) for x in failed_hashes),
        wells=wells_out,
        steps=lowered_steps,
        well_labels=id_to_label,
        channel_mode="8_channel_per_nozzle" if active_channels == 8 else "single",
        pipette_models=pip_models,
        non_mutating_commands=tuple(non_mutating),
    )


def prepare_protobuild_python_source(protobuild_obj: Mapping[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Extract runnable Python source + custom labware defs from an `Opentrons/Protocols` `protoBuilds/*.py.json`."""
    content = str(protobuild_obj["content"])
    fields = protobuild_obj.get("fields") or []
    defaults: dict[str, Any] = {}
    for fld in fields:
        if not isinstance(fld, Mapping) or "name" not in fld:
            continue
        fname = str(fld["name"])
        if "default" in fld:
            defaults[fname] = fld["default"]
        elif fld.get("options"):
            defaults[fname] = fld["options"][0].get("value")
        else:
            defaults[fname] = ""

    if "get_values(" in content and "def get_values" not in content:
        defaults_json = json.dumps(defaults)
        shim = (
            f"def get_values(*names):\n"
            f"    import json as _json\n"
            f"    _vals = _json.loads({defaults_json!r})\n"
            f"    return [_vals[n] for n in names]\n\n"
        )
        # Keep `from __future__ import ...` lines at the very top of the file if present
        lines = content.splitlines(keepends=True)
        insert_at = 0
        while insert_at < len(lines) and (
            lines[insert_at].lstrip().startswith(("#", "from __future__")) or not lines[insert_at].strip()
        ):
            insert_at += 1
        content = "".join(lines[:insert_at]) + shim + "".join(lines[insert_at:])

    raw_custom = protobuild_obj.get("custom_labware_defs") or []
    if isinstance(raw_custom, Mapping):
        custom_defs = [dict(v) for v in raw_custom.values() if isinstance(v, Mapping)]
    else:
        custom_defs = [dict(v) for v in raw_custom if isinstance(v, Mapping)]
    return content, custom_defs


def _require_opentrons_simulate():
    try:
        import enum
        from opentrons import simulate as ot_simulate
        import opentrons.hardware_control.modules.types as _ot_hw_mod_types
        import opentrons_shared_data.module.types as _ot_mod_types

        # Python 3.11+ changed `(str, Enum).__str__` from `.value` to `ClassName.MEMBER`, which breaks
        # legacy `opentrons` (<2.14) module definition lookup (`f".../{model}.json"`). Restore `str.__str__` in memory.
        for _mod in (_ot_mod_types, _ot_hw_mod_types):
            for _obj in vars(_mod).values():
                if isinstance(_obj, type) and issubclass(_obj, str) and issubclass(_obj, enum.Enum):
                    _obj.__str__ = str.__str__  # type: ignore[method-assign]
    except ImportError as exc:
        raise ImportError(
            "Optional dependency `opentrons>=8.0` is required to simulate Opentrons protocol files on CPU. "
            "Install via `pip install -e '.[real-data]'`."
        ) from exc
    return ot_simulate


def simulate_and_import_protocol(
    protocol_path_or_source: Path | str,
    *,
    file_name: str | None = None,
    protocol_id: str | None = None,
    custom_labware_defs: Sequence[Mapping[str, Any]] | None = None,
    custom_labware_paths: Sequence[str | Path] | None = None,
    initial_liquids: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    failed_hashes: Sequence[int] = (),
    allow_pause: bool = False,
) -> ImportedRehearsalProtocol:
    """Simulate a real `.py` or `.json` Opentrons protocol on CPU via `opentrons.simulate.simulate()`
    and lower its structured runlog into `REHEARSAL` deck + steps."""
    ot_simulate = _require_opentrons_simulate()

    if isinstance(protocol_path_or_source, Path) or (
        isinstance(protocol_path_or_source, str)
        and "\n" not in protocol_path_or_source
        and Path(protocol_path_or_source).is_file()
    ):
        path = Path(protocol_path_or_source)
        raw_text = path.read_text(encoding="utf-8")
        eff_name = file_name or path.name
        eff_id = protocol_id or path.stem
    else:
        raw_text = str(protocol_path_or_source)
        eff_name = file_name or ("protocol.json" if raw_text.lstrip().startswith("{") else "protocol.py")
        eff_id = protocol_id or eff_name

    lw_dirs = [str(p) for p in (custom_labware_paths or ())]
    with tempfile.TemporaryDirectory(prefix="autolab_ot_lw_") as tmp_dir:
        if custom_labware_defs:
            for idx, lw_def in enumerate(custom_labware_defs):
                out_lw = Path(tmp_dir) / f"custom_lw_{idx}.json"
                out_lw.write_text(json.dumps(dict(lw_def)), encoding="utf-8")
            lw_dirs.append(tmp_dir)

        buf = io.StringIO(raw_text)
        with contextlib.redirect_stdout(io.StringIO()):
            runlog, _ = ot_simulate.simulate(
                buf,
                file_name=eff_name,
                custom_labware_paths=lw_dirs if lw_dirs else None,
                propagate_logs=False,
                log_level="error",
            )

    return import_runlog(
        runlog,
        protocol_id=eff_id,
        initial_liquids=initial_liquids,
        failed_hashes=failed_hashes,
        allow_pause=allow_pause,
    )


def simulate_and_import_protobuild(
    protobuild_path_or_obj: Path | Mapping[str, Any],
    *,
    protocol_id: str | None = None,
    allow_pause: bool = False,
) -> ImportedRehearsalProtocol:
    """Simulate and import a pre-parsed `Opentrons/Protocols` `protoBuilds/<slug>/<name>.py.json` bundle."""
    if isinstance(protobuild_path_or_obj, Path):
        obj = json.loads(protobuild_path_or_obj.read_text(encoding="utf-8"))
        eff_id = protocol_id or protobuild_path_or_obj.stem
    else:
        obj = protobuild_path_or_obj
        eff_id = protocol_id or "protobuild_protocol"

    py_src, custom_defs = prepare_protobuild_python_source(obj)
    return simulate_and_import_protocol(
        py_src,
        file_name=f"{eff_id}.py",
        protocol_id=eff_id,
        custom_labware_defs=custom_defs,
        allow_pause=allow_pause,
    )
