"""Unit and live-simulation tests for `autolab.importers.opentrons_runlog`."""

from __future__ import annotations

import importlib.util
import json
import pytest

from autolab.importers.opentrons_runlog import (
    UnsupportedProtocolStepError,
    import_runlog,
    prepare_protobuild_python_source,
    simulate_and_import_protocol,
)
from autolab.trust_regime import LeanBatchKernel, py_check_rehearsal

HAS_OPENTRONS = importlib.util.find_spec("opentrons") is not None


def _pip(mount: str = "left", model: str = "p300_single_gen2", min_v: float = 20.0, max_v: float = 300.0, ch: int = 1) -> dict:
    return {"mount": mount, "model": model, "min_volume": min_v, "max_volume": max_v, "channels": ch}


def _well(
    slot: str,
    well: str,
    *,
    labware: str = "corning_96_wellplate_360ul_flat",
    max_volume: float = 360.0,
    module: str | None = None,
) -> dict:
    return {"slot": slot, "well": well, "labware": labware, "max_volume": max_volume, "module": module}


# ---------------------------------------------------------------------------
# Offline Mock-Runlog Tests (run in zero-dependency `pytest-cpu` CI)
# ---------------------------------------------------------------------------
def test_mock_runlog_protocol1_buffer_and_sample_mix() -> None:
    inst = _pip()
    res_a1 = _well("1", "A1", labware="nest_12_reservoir_15ml", max_volume=15000.0)
    tube_a1 = _well("2", "A1", labware="opentrons_24_tuberack_nest_1.5ml_snapcap", max_volume=1500.0)
    plate_a1 = _well("3", "A1")

    runlog = [
        {"level": 0, "payload": {"instrument": inst, "location": _well("4", "A1"), "text": "Picking up tip from A1 of Tip Rack on slot 4"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 100.0, "location": res_a1, "text": "Aspirating 100.0 uL from A1 of Reservoir on slot 1 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 100.0, "location": plate_a1, "text": "Dispensing 100.0 uL into A1 of Plate on slot 3 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin on slot 12"}},
        {"level": 0, "payload": {"instrument": inst, "location": _well("4", "B1"), "text": "Picking up tip from B1 of Tip Rack on slot 4"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 50.0, "location": tube_a1, "text": "Aspirating 50.0 uL from A1 of Tube Rack on slot 2 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 50.0, "location": plate_a1, "text": "Dispensing 50.0 uL into A1 of Plate on slot 3 at 92.86 uL/sec"}},
        {
            "level": 0,
            "payload": {"instrument": inst, "location": plate_a1, "volume": 80.0, "repetitions": 3, "text": "Mixing 3 times with a volume of 80.0 ul"},
        },
        # Child aspirate/dispense inside `mix` must NOT be duplicated as `xfer`:
        {"level": 1, "payload": {"instrument": inst, "volume": 80.0, "location": plate_a1, "text": "Aspirating 80.0 uL from A1 of Plate on slot 3 at 92.86 uL/sec"}},
        {"level": 1, "payload": {"instrument": inst, "volume": 80.0, "location": plate_a1, "text": "Dispensing 80.0 uL into A1 of Plate on slot 3 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin on slot 12"}},
    ]

    imp = import_runlog(runlog, protocol_id="mock_proto_1")
    assert (imp.pip_min, imp.pip_max) == (200, 3000)
    assert imp.steps == [
        ("pick",),
        ("xfer", 1, 3, 1000),
        ("drop",),
        ("pick",),
        ("xfer", 2, 3, 500),
        ("mix", 3, 800, 3),
        ("drop",),
    ]
    verdict = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps)
    assert verdict.allowed is True

    kernel = LeanBatchKernel()
    if kernel.available:
        lean_v = kernel.eval_lines([imp.to_tsv()])[0]
        assert (lean_v.allowed, lean_v.rule, lean_v.extra) == (verdict.allowed, verdict.rule, verdict.extra)


def test_mock_runlog_protocol2_thermocycler_seal_and_profile() -> None:
    inst = _pip(model="p20_single_gen2", min_v=1.0, max_v=20.0)
    mm_a1 = _well("1", "A1", labware="opentrons_24_tuberack_nest_1.5ml_snapcap", max_volume=1500.0)
    tc_a1 = _well("7", "A1", labware="nest_96_wellplate_100ul_pcr_full_skirt", max_volume=100.0, module="thermocycler")

    runlog = [
        {"level": 0, "payload": {"text": "Opening Thermocycler lid"}},
        {"level": 0, "payload": {"instrument": inst, "location": _well("4", "A1"), "text": "Picking up tip from A1 of Tip Rack on slot 4"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 15.0, "location": mm_a1, "text": "Aspirating 15.0 uL from A1 of Tube Rack on slot 1 at 7.56 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 15.0, "location": tc_a1, "text": "Dispensing 15.0 uL into A1 of PCR Plate on slot 7 at 7.56 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin on slot 12"}},
        {"level": 0, "payload": {"text": "Closing Thermocycler lid"}},
        {"level": 0, "payload": {"text": "Setting Thermocycler lid temperature to 105.0 C"}},
        {
            "level": 0,
            "payload": {
                "steps": [
                    {"temperature": 95.0, "hold_time_seconds": 30.0},
                    {"temperature": 60.0, "hold_time_seconds": 30.0},
                    {"temperature": 72.0, "hold_time_minutes": 1.0},
                ],
                "text": "Thermocycler starting 25 repetitions of cycle composed of the following steps: [...]",
            },
        },
    ]

    imp = import_runlog(runlog, protocol_id="mock_proto_2_pcr")
    assert imp.steps == [
        ("pick",),
        ("xfer", 1, 2, 150),
        ("drop",),
        ("seal", 2),
        ("inc", 2, 95, 30),
        ("inc", 2, 60, 30),
        ("inc", 2, 72, 60),
    ]
    verdict = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps)
    assert verdict.allowed is True


def test_mock_runlog_protocol3_unsealed_high_temp_denied() -> None:
    inst = _pip()
    src = _well("1", "A1", labware="nest_12_reservoir_15ml", max_volume=15000.0)
    tmod_well = _well("3", "A1", labware="opentrons_24_aluminumblock_nest_1.5ml_snapcap", max_volume=1500.0, module="temperature")

    runlog = [
        {"level": 0, "payload": {"instrument": inst, "location": _well("4", "A1"), "text": "Picking up tip from A1 of Tip Rack on slot 4"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 100.0, "location": src, "text": "Aspirating 100.0 uL from A1 of Reservoir on slot 1 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 100.0, "location": tmod_well, "text": "Dispensing 100.0 uL into A1 of Block on slot 3 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin on slot 12"}},
        {"level": 0, "payload": {"celsius": 95.0, "text": "Setting Temperature Module temperature to 95.0 C (rounded off to nearest integer)"}},
        {"level": 0, "payload": {"minutes": 5.0, "seconds": 0.0, "text": "Delaying for 5 minutes and 0.0 seconds"}},
    ]

    imp = import_runlog(runlog, protocol_id="mock_proto_3_unsealed_95c")
    assert imp.steps == [
        ("pick",),
        ("xfer", 1, 2, 1000),
        ("drop",),
        ("inc", 2, 95, 300),
    ]
    verdict = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps)
    assert verdict.allowed is False
    assert verdict.rule == "high_temp_requires_seal"


def test_mock_runlog_protocol4_air_gap_and_missing_drop_tip() -> None:
    inst = _pip()
    src = _well("1", "A1", labware="nest_12_reservoir_15ml", max_volume=15000.0)
    dst = _well("2", "A1")

    runlog = [
        {"level": 0, "payload": {"instrument": inst, "location": _well("4", "A1"), "text": "Picking up tip from A1 of Tip Rack on slot 4"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 50.0, "location": src, "text": "Aspirating 50.0 uL from A1 of Reservoir on slot 1 at 92.86 uL/sec"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 10.0, "height": None, "text": "Air gap of 10.0 uL"}},
        {"level": 0, "payload": {"instrument": inst, "volume": 60.0, "location": dst, "text": "Dispensing 60.0 uL into A1 of Plate on slot 2 at 92.86 uL/sec"}},
    ]

    imp = import_runlog(runlog, protocol_id="mock_proto_4_airgap")
    assert imp.steps == [("pick",), ("xfer", 1, 2, 500)]
    verdict = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps)
    assert verdict.allowed is False
    assert verdict.rule == "tip_dropped_at_end"


def test_mock_runlog_protocol5_distribute_blowout_to_source_conserves_liquid() -> None:
    inst = _pip()
    src = _well("1", "A1", labware="nest_12_reservoir_15ml", max_volume=15000.0)
    d1 = _well("2", "A1")
    d2 = _well("2", "A2")

    runlog = [
        {
            "level": 0,
            "payload": {"instrument": inst, "source": src, "dest": [d1, d2], "volume": 50.0, "text": "Distributing 50.0 from A1 to A1..A2"},
        },
        {"level": 1, "payload": {"instrument": inst, "location": _well("4", "A1"), "text": "Picking up tip from A1 of Tip Rack on slot 4"}},
        {"level": 1, "payload": {"instrument": inst, "volume": 120.0, "location": src, "text": "Aspirating 120.0 uL from A1 of Reservoir on slot 1 at 92.86 uL/sec"}},
        {"level": 1, "payload": {"instrument": inst, "volume": 50.0, "location": d1, "text": "Dispensing 50.0 uL into A1 of Plate on slot 2 at 92.86 uL/sec"}},
        {"level": 1, "payload": {"instrument": inst, "volume": 50.0, "location": d2, "text": "Dispensing 50.0 uL into A2 of Plate on slot 2 at 92.86 uL/sec"}},
        {"level": 1, "payload": {"instrument": inst, "location": src, "text": "Blowing out at A1 of Reservoir on slot 1"}},
        {"level": 1, "payload": {"instrument": inst, "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin on slot 12"}},
    ]

    imp = import_runlog(runlog, protocol_id="mock_proto_5_distribute")
    assert imp.steps == [
        ("pick",),
        ("xfer", 1, 2, 500),
        ("xfer", 1, 3, 500),
        ("drop",),
    ]
    verdict = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps)
    assert verdict.allowed is True


@pytest.mark.parametrize(
    ("bad_runlog", "expected_reason"),
    [
        ([{"level": 0, "payload": {"text": "Engaging Magnetic Module"}}], "magnetic_module_command"),
        ([{"level": 0, "payload": {"text": "Setting Heater-Shaker to Shake at 800 RPM"}}], "heater_shaker_agitation_command"),
        ([{"level": 0, "payload": {"text": "Returning tip"}}], "return_tip_not_modeled_in_rehearsal"),
        ([{"level": 0, "payload": {"text": "Opening the gripper jaw."}}], "gripper_or_stacker_labware_move"),
        (
            [
                {"level": 0, "payload": {"instrument": _pip("left"), "location": _well("4", "A1"), "text": "Picking up tip from A1"}},
                {"level": 0, "payload": {"instrument": _pip("right"), "location": _well("4", "B1"), "text": "Picking up tip from B1"}},
            ],
            "simultaneous_multi_pipette_tips",
        ),
        (
            [
                {"level": 0, "payload": {"instrument": _pip(), "location": _well("4", "A1"), "text": "Picking up tip from A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "volume": 120.0, "location": _well("1", "A1"), "text": "Aspirating 120.0 uL from A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "volume": 50.0, "location": _well("2", "A1"), "text": "Dispensing 50.0 uL into A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "location": {"kind": "trash"}, "text": "Blowing out into Trash Bin"}},
            ],
            "residual_disposal_volume_blown_out_to_trash",
        ),
        (
            [
                {"level": 0, "payload": {"instrument": _pip(), "location": _well("4", "A1"), "text": "Picking up tip from A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "volume": 50.0, "location": _well("1", "A1"), "text": "Aspirating 50.0 uL from A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "volume": 50.0, "location": _well("7", "A1", module="thermocycler"), "text": "Dispensing 50.0 uL into A1"}},
                {"level": 0, "payload": {"instrument": _pip(), "location": {"kind": "trash"}, "text": "Dropping tip into Trash Bin"}},
                {"level": 0, "payload": {"text": "Closing Thermocycler lid"}},
                {"level": 0, "payload": {"text": "Opening Thermocycler lid"}},
                {"level": 0, "payload": {"instrument": _pip(), "location": _well("4", "B1"), "text": "Picking up tip from B1"}},
                {"level": 0, "payload": {"instrument": _pip(), "volume": 25.0, "location": _well("7", "A1", module="thermocycler"), "text": "Aspirating 25.0 uL from A1"}},
            ],
            "thermocycler_reopen_unseal_not_in_rehearsal_dsl",
        ),
        (
            [{"level": 0, "payload": {"unknown_gadget": 123, "text": "Activating laser centrifuge"}}],
            "unrecognized_runlog_command",
        ),
    ],
)
def test_import_runlog_fails_closed_never_drops_unsupported_steps(
    bad_runlog: list[dict], expected_reason: str
) -> None:
    with pytest.raises(UnsupportedProtocolStepError) as exc_info:
        import_runlog(bad_runlog)
    assert exc_info.value.reason == expected_reason


def test_prepare_protobuild_injects_default_get_values() -> None:
    src, defs = prepare_protobuild_python_source(
        {
            "content": "metadata = {'apiLevel': '2.11'}\ndef run(ctx):\n    [vol] = get_values('vol')\n",
            "fields": [{"name": "vol", "default": 45}],
            "custom_labware_defs": [{"namespace": "custom_beta"}],
        }
    )
    assert "def get_values(*names):" in src
    assert len(defs) == 1


# ---------------------------------------------------------------------------
# Live CPU `opentrons.simulate` Tests (run whenever `opentrons>=8.0` is installed)
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_OPENTRONS, reason="opentrons>=8.0 extra not installed")
def test_live_opentrons_simulate_five_python_and_json_protocols() -> None:
    # 1. Clean buffer + sample transfer + mix (Python API v2.16)
    py_clean = """
metadata = {'apiLevel': '2.16'}

def run(protocol):
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    res = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '3')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '4')
    pip = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])
    pip.pick_up_tip()
    pip.aspirate(100, res['A1'])
    pip.dispense(100, plate['A1'])
    pip.drop_tip()
    pip.pick_up_tip()
    pip.aspirate(50, tubes['A1'])
    pip.dispense(50, plate['A1'])
    pip.mix(3, 80, plate['A1'])
    pip.drop_tip()
"""
    imp1 = simulate_and_import_protocol(py_clean, file_name="clean_assay.py", protocol_id="live_clean")
    assert imp1.steps == [
        ("pick",),
        ("xfer", 1, 3, 1000),
        ("drop",),
        ("pick",),
        ("xfer", 2, 3, 500),
        ("mix", 3, 800, 3),
        ("drop",),
    ]
    assert py_check_rehearsal(imp1.pip_min, imp1.pip_max, imp1.proto_hash, imp1.failed_hashes, imp1.wells, imp1.steps).allowed is True

    # 2. Thermocycler V2 sealed 95 C denaturation (Python API v2.16)
    py_tc = """
metadata = {'apiLevel': '2.16'}

def run(protocol):
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    res = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tc = protocol.load_module('thermocyclerModuleV2')
    pcr = tc.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    pip = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])
    tc.open_lid()
    pip.pick_up_tip()
    pip.aspirate(50, res['A1'])
    pip.dispense(50, pcr['A1'])
    pip.drop_tip()
    tc.close_lid()
    tc.set_block_temperature(95, hold_time_seconds=30)
"""
    imp2 = simulate_and_import_protocol(py_tc, file_name="tc_sealed.py", protocol_id="live_tc")
    assert ("seal", 2) in imp2.steps and ("inc", 2, 95, 30) in imp2.steps
    assert py_check_rehearsal(imp2.pip_min, imp2.pip_max, imp2.proto_hash, imp2.failed_hashes, imp2.wells, imp2.steps).allowed is True

    # 3. Cross-contamination: sample tip enters clean reservoir without drop_tip
    py_contam = """
metadata = {'apiLevel': '2.16'}

def run(protocol):
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    res = protocol.load_labware('nest_12_reservoir_15ml', '2')
    tubes = protocol.load_labware('opentrons_24_tuberack_nest_1.5ml_snapcap', '3')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '4')
    pip = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])
    pip.pick_up_tip()
    pip.aspirate(50, tubes['A1'])
    pip.dispense(50, plate['A1'])
    pip.aspirate(50, res['A1'])
    pip.dispense(50, plate['A2'])
    pip.drop_tip()
"""
    imp3 = simulate_and_import_protocol(py_contam, file_name="contam.py", protocol_id="live_contam")
    v3 = py_check_rehearsal(imp3.pip_min, imp3.pip_max, imp3.proto_hash, imp3.failed_hashes, imp3.wells, imp3.steps)
    assert v3.allowed is False and v3.rule == "no_tip_cross_contamination"

    # 4. Forgotten final drop_tip
    py_nodrop = """
metadata = {'apiLevel': '2.16'}

def run(protocol):
    tips = protocol.load_labware('opentrons_96_tiprack_300ul', '1')
    res = protocol.load_labware('nest_12_reservoir_15ml', '2')
    plate = protocol.load_labware('corning_96_wellplate_360ul_flat', '3')
    pip = protocol.load_instrument('p300_single_gen2', 'left', tip_racks=[tips])
    pip.pick_up_tip()
    pip.aspirate(50, res['A1'])
    pip.dispense(50, plate['A1'])
"""
    imp4 = simulate_and_import_protocol(py_nodrop, file_name="nodrop.py", protocol_id="live_nodrop")
    v4 = py_check_rehearsal(imp4.pip_min, imp4.pip_max, imp4.proto_hash, imp4.failed_hashes, imp4.wells, imp4.steps)
    assert v4.allowed is False and v4.rule == "tip_dropped_at_end"

    # 5. Magnetic module protocol -> fail-closed UnsupportedProtocolStepError
    py_mag = """
metadata = {'apiLevel': '2.16'}

def run(protocol):
    mag = protocol.load_module('magnetic module gen2', '1')
    mag.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')
    mag.engage(height_from_base=5)
"""
    with pytest.raises(UnsupportedProtocolStepError) as exc_info:
        simulate_and_import_protocol(py_mag, file_name="mag.py", protocol_id="live_mag")
    assert exc_info.value.reason == "magnetic_module_command"

    # 6. Real Opentrons JSON v3 protocol fixture from installed opentrons_shared_data / inline JSON v3
    import opentrons_shared_data

    shared_root = Path_from_str = __import__("pathlib").Path(opentrons_shared_data.__file__).resolve().parent
    json_fixture = shared_root / "data" / "protocol" / "fixtures" / "4" / "simpleV4.json"
    if json_fixture.is_file():
        imp6 = simulate_and_import_protocol(json_fixture, protocol_id="fixture_simpleV4_json")
        assert len(imp6.steps) >= 3
        assert imp6.steps[0] == ("pick",)
