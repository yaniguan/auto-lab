"""Real Public Opentrons Protocol Library Rehearsal Study (`AutoLabLean` Issue #4).

Fetches a pinned, reproducible sample of 85 real public protocols on CPU from:
1. `Opentrons/Protocols` (pinned commit `2f447c936b49720d68154054e94d58e1d33ccba5`,
   `protoBuilds/*/*.apiv2.py.json` public Protocol Library entries)
2. `Opentrons/opentrons` (pinned commit `84a9956efccae8783f1a49ec14873222956f3284`,
   `shared-data/protocol/fixtures/*/*.json` Apache-2.0 JSON v3/v4/v5 protocol fixtures)

Caches raw downloads in gitignored `.cache/opentrons_protocols/`, simulates each
protocol on CPU via `opentrons.simulate.simulate()`, lowers the structured runlog
into `REHEARSAL` deck + steps (`autolab.importers.opentrons_runlog`, failing
closed with `UnsupportedProtocolStepError` on unsupported steps), executes every
imported protocol through the compiled Lean 4.36.0 binary (`autolab-lean --batch-tsv`),
verifies 100% parity with the Python mirror (`py_check_rehearsal`), and records a
code-grounded audit of all 23 denied real protocols (`true_hazard` vs
`abstraction_false_alarm`).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from autolab.importers.opentrons_runlog import (  # noqa: E402
    ImportedRehearsalProtocol,
    UnsupportedProtocolStepError,
    simulate_and_import_protobuild,
    simulate_and_import_protocol,
)
from autolab.trust_regime import LeanBatchKernel, audit_lean_sources, py_check_rehearsal  # noqa: E402

PINNED_REPOSITORIES: dict[str, dict[str, str]] = {
    "Opentrons/Protocols": {
        "git_url": "https://github.com/Opentrons/Protocols",
        "commit_sha": "2f447c936b49720d68154054e94d58e1d33ccba5",
        "upstream_license": "LicenseRef-Opentrons-Protocol-Library-Public (public library; no root SPDX file)",
    },
    "Opentrons/opentrons": {
        "git_url": "https://github.com/Opentrons/opentrons",
        "commit_sha": "84a9956efccae8783f1a49ec14873222956f3284",
        "upstream_license": "Apache-2.0",
    },
}

# Pinned 85-protocol sample (74 Python API v2 library protocols + 11 JSON v3/v4/v5 fixtures)
PINNED_PROTOCOLS: tuple[tuple[str, str, str], ...] = (
    ("protocol_library:00222e-dd", "Opentrons/Protocols", "protoBuilds/00222e-dd/00222e.ot2.apiv2.py.json"),
    ("protocol_library:0045f1", "Opentrons/Protocols", "protoBuilds/0045f1/0045f1.ot2.apiv2.py.json"),
    ("protocol_library:00a214-protocol-1", "Opentrons/Protocols", "protoBuilds/00a214-protocol-1/00a214-protocol-1.ot2.apiv2.py.json"),
    ("protocol_library:00a6e5", "Opentrons/Protocols", "protoBuilds/00a6e5/00a6e5.ot2.apiv2.py.json"),
    ("protocol_library:00c517-pt2", "Opentrons/Protocols", "protoBuilds/00c517-pt2/00c517-pt2.ot2.apiv2.py.json"),
    ("protocol_library:00f7b1_part10", "Opentrons/Protocols", "protoBuilds/00f7b1_part10/00f7b1_part10.ot2.apiv2.py.json"),
    ("protocol_library:010d6c", "Opentrons/Protocols", "protoBuilds/010d6c/010d6c.ot2.apiv2.py.json"),
    ("protocol_library:017860", "Opentrons/Protocols", "protoBuilds/017860/017860.ot2.apiv2.py.json"),
    ("protocol_library:019a7d", "Opentrons/Protocols", "protoBuilds/019a7d/019a7d.ot2.apiv2.py.json"),
    ("protocol_library:01b4a2", "Opentrons/Protocols", "protoBuilds/01b4a2/01b4a2.ot2.apiv2.py.json"),
    ("protocol_library:022a99", "Opentrons/Protocols", "protoBuilds/022a99/spheroidtransfer.ot2.apiv2.py.json"),
    ("protocol_library:02b308", "Opentrons/Protocols", "protoBuilds/02b308/pcr_prep.ot2.apiv2.py.json"),
    ("protocol_library:030dd8-amplify", "Opentrons/Protocols", "protoBuilds/030dd8-amplify/amplify.ot2.apiv2.py.json"),
    ("protocol_library:0451f3", "Opentrons/Protocols", "protoBuilds/0451f3/miniprep.ot2.apiv2.py.json"),
    ("protocol_library:04711e", "Opentrons/Protocols", "protoBuilds/04711e/04711e.ot2.apiv2.py.json"),
    ("protocol_library:04fed3", "Opentrons/Protocols", "protoBuilds/04fed3/04fed3.ot2.apiv2.py.json"),
    ("protocol_library:0556be-bmda", "Opentrons/Protocols", "protoBuilds/0556be-bmda/0556be-bmda.ot2.apiv2.py.json"),
    ("protocol_library:056f47", "Opentrons/Protocols", "protoBuilds/056f47/056f47.ot2.apiv2.py.json"),
    ("protocol_library:058124", "Opentrons/Protocols", "protoBuilds/058124/058124.ot2.apiv2.py.json"),
    ("protocol_library:05f673", "Opentrons/Protocols", "protoBuilds/05f673/05f673.ot2.apiv2.py.json"),
    ("protocol_library:060c4f", "Opentrons/Protocols", "protoBuilds/060c4f/060c4f.ot2.apiv2.py.json"),
    ("protocol_library:06ab09", "Opentrons/Protocols", "protoBuilds/06ab09/06ab09.ot2.apiv2.py.json"),
    ("protocol_library:06e5b6", "Opentrons/Protocols", "protoBuilds/06e5b6/protein_crystallization.ot2.apiv2.py.json"),
    ("protocol_library:075bee", "Opentrons/Protocols", "protoBuilds/075bee/075bee.ot2.apiv2.py.json"),
    ("protocol_library:079db2", "Opentrons/Protocols", "protoBuilds/079db2/079db2.ot2.apiv2.py.json"),
    ("protocol_library:08878b", "Opentrons/Protocols", "protoBuilds/08878b/08878b.ot2.apiv2.py.json"),
    ("protocol_library:08aeaa", "Opentrons/Protocols", "protoBuilds/08aeaa/08aeaa.ot2.apiv2.py.json"),
    ("protocol_library:08e3eb", "Opentrons/Protocols", "protoBuilds/08e3eb/08e3eb.ot2.apiv2.py.json"),
    ("protocol_library:0961d2-part1", "Opentrons/Protocols", "protoBuilds/0961d2-part1/0961d2-part1.ot2.apiv2.py.json"),
    ("protocol_library:09cdbe", "Opentrons/Protocols", "protoBuilds/09cdbe/cherrypick.ot2.apiv2.py.json"),
    ("protocol_library:0a9b58", "Opentrons/Protocols", "protoBuilds/0a9b58/0a9b58.ot2.apiv2.py.json"),
    ("protocol_library:0bd707", "Opentrons/Protocols", "protoBuilds/0bd707/0bd707.ot2.apiv2.py.json"),
    ("protocol_library:0df680", "Opentrons/Protocols", "protoBuilds/0df680/cherrypicking.ot2.apiv2.py.json"),
    ("protocol_library:0e525c", "Opentrons/Protocols", "protoBuilds/0e525c/0e525c.ot2.apiv2.py.json"),
    ("protocol_library:0f7910", "Opentrons/Protocols", "protoBuilds/0f7910/0f7910.ot2.apiv2.py.json"),
    ("protocol_library:131de0", "Opentrons/Protocols", "protoBuilds/131de0/cnv.ot2.apiv2.py.json"),
    ("protocol_library:154ec5", "Opentrons/Protocols", "protoBuilds/154ec5/154ec5.ot2.apiv2.py.json"),
    ("protocol_library:158d42", "Opentrons/Protocols", "protoBuilds/158d42/1584d2.ot2.apiv2.py.json"),
    ("protocol_library:1601a9", "Opentrons/Protocols", "protoBuilds/1601a9/1601a9.ot2.apiv2.py.json"),
    ("protocol_library:17cb2d", "Opentrons/Protocols", "protoBuilds/17cb2d/17cb2d.ot2.apiv2.py.json"),
    ("protocol_library:18050b", "Opentrons/Protocols", "protoBuilds/18050b/drug_screening.ot2.apiv2.py.json"),
    ("protocol_library:18e62e", "Opentrons/Protocols", "protoBuilds/18e62e/18e62e.ot2.apiv2.py.json"),
    ("protocol_library:1980cd", "Opentrons/Protocols", "protoBuilds/1980cd/1980cd.ot2.apiv2.py.json"),
    ("protocol_library:1adec6-2", "Opentrons/Protocols", "protoBuilds/1adec6-2/1adec6-2.ot2.apiv2.py.json"),
    ("protocol_library:1c8468", "Opentrons/Protocols", "protoBuilds/1c8468/1c8468.ot2.apiv2.py.json"),
    ("protocol_library:1dec68", "Opentrons/Protocols", "protoBuilds/1dec68/1dec68.ot2.apiv2.py.json"),
    ("protocol_library:1f8b55", "Opentrons/Protocols", "protoBuilds/1f8b55/1f8b55.ot2.apiv2.py.json"),
    ("protocol_library:269b21", "Opentrons/Protocols", "protoBuilds/269b21/pcr_prep.ot2.apiv2.py.json"),
    ("protocol_library:274d2a", "Opentrons/Protocols", "protoBuilds/274d2a/cherrypicking.ot2.apiv2.py.json"),
    ("protocol_library:2942dd", "Opentrons/Protocols", "protoBuilds/2942dd/2942dd.ot2.apiv2.py.json"),
    ("protocol_library:2ee5be", "Opentrons/Protocols", "protoBuilds/2ee5be/2ee5be.ot2.apiv2.py.json"),
    ("protocol_library:30174a", "Opentrons/Protocols", "protoBuilds/30174a/30174a.ot2.apiv2.py.json"),
    ("protocol_library:3359a5", "Opentrons/Protocols", "protoBuilds/3359a5/cherrypicking.ot2.apiv2.py.json"),
    ("protocol_library:33y0f3", "Opentrons/Protocols", "protoBuilds/33y0f3/33y0f3.ot2.apiv2.py.json"),
    ("protocol_library:37de37", "Opentrons/Protocols", "protoBuilds/37de37/37de37.ot2.apiv2.py.json"),
    ("protocol_library:384b23-plate-transfer", "Opentrons/Protocols", "protoBuilds/384b23-plate-transfer/384b23-plate-transfer.ot2.apiv2.py.json"),
    ("protocol_library:412ec7", "Opentrons/Protocols", "protoBuilds/412ec7/412ec7.ot2.apiv2.py.json"),
    ("protocol_library:4175de", "Opentrons/Protocols", "protoBuilds/4175de/4175de.ot2.apiv2.py.json"),
    ("protocol_library:422b1e", "Opentrons/Protocols", "protoBuilds/422b1e/422b1e.ot2.apiv2.py.json"),
    ("protocol_library:470d8c", "Opentrons/Protocols", "protoBuilds/470d8c/470d8c.ot2.apiv2.py.json"),
    ("protocol_library:4883fc", "Opentrons/Protocols", "protoBuilds/4883fc/normalization.ot2.apiv2.py.json"),
    ("protocol_library:49b828", "Opentrons/Protocols", "protoBuilds/49b828/49b828.ot2.apiv2.py.json"),
    ("protocol_library:4b76c0", "Opentrons/Protocols", "protoBuilds/4b76c0/4b76c0.ot2.apiv2.py.json"),
    ("protocol_library:4e4c0c", "Opentrons/Protocols", "protoBuilds/4e4c0c/4e4c0c.ot2.apiv2.py.json"),
    ("protocol_library:5191b6", "Opentrons/Protocols", "protoBuilds/5191b6/5191b6.ot2.apiv2.py.json"),
    ("protocol_library:543bf9", "Opentrons/Protocols", "protoBuilds/543bf9/543bf9.ot2.apiv2.py.json"),
    ("protocol_library:56b4ec", "Opentrons/Protocols", "protoBuilds/56b4ec/56b4ec.ot2.apiv2.py.json"),
    ("protocol_library:60d861-2", "Opentrons/Protocols", "protoBuilds/60d861-2/pcr_prep.ot2.apiv2.py.json"),
    ("protocol_library:6bc986-part-2", "Opentrons/Protocols", "protoBuilds/6bc986-part-2/6bc986-part-2.ot2.apiv2.py.json"),
    ("protocol_library:6c27ee", "Opentrons/Protocols", "protoBuilds/6c27ee/6c27ee.ot2.apiv2.py.json"),
    ("protocol_library:6cb818", "Opentrons/Protocols", "protoBuilds/6cb818/6cb818.ot2.apiv2.py.json"),
    ("protocol_library:6d901d-2", "Opentrons/Protocols", "protoBuilds/6d901d-2/6d901d-2.ot2.apiv2.py.json"),
    ("protocol_library:74312c", "Opentrons/Protocols", "protoBuilds/74312c/74312c.ot2.apiv2.py.json"),
    ("protocol_library:76c562", "Opentrons/Protocols", "protoBuilds/76c562/76c562.ot2.apiv2.py.json"),
    ("opentrons_fixture:3/simple.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/3/simple.json"),
    ("opentrons_fixture:3/testAllAtomicSingleV3.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/3/testAllAtomicSingleV3.json"),
    ("opentrons_fixture:4/pipetteMultiChannelProtocolV4.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/pipetteMultiChannelProtocolV4.json"),
    ("opentrons_fixture:4/simpleV4.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/simpleV4.json"),
    ("opentrons_fixture:4/testMagneticModuleV4.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/testMagneticModuleV4.json"),
    ("opentrons_fixture:4/testTemperatureModuleV4.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/testTemperatureModuleV4.json"),
    ("opentrons_fixture:4/testThermocyclerModuleV4.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/testThermocyclerModuleV4.json"),
    ("opentrons_fixture:4/transferSettings.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/4/transferSettings.json"),
    ("opentrons_fixture:5/multipleTipracks.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/5/multipleTipracks.json"),
    ("opentrons_fixture:5/multipleTipracksWithTC.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/5/multipleTipracksWithTC.json"),
    ("opentrons_fixture:5/simpleV5.json", "Opentrons/opentrons", "shared-data/protocol/fixtures/5/simpleV5.json"),
)

# Code-grounded manual audit of all 23 denied protocols in PINNED_PROTOCOLS
DENY_AUDIT_ANNOTATIONS: dict[str, tuple[str, str]] = {
    # --- 12 True Physical / Calibration Hazards (`true_hazard`) ---
    "protocol_library:1adec6-2": (
        "true_hazard",
        "Dispenses 250.0 uL per channel into `spl_96_wellplate_200ul_round[A1]` whose labware definition specifies a 200.0 uL maximum well capacity (+50.0 uL overfill missed by legacy Opentrons simulation).",
    ),
    "protocol_library:384b23-plate-transfer": (
        "true_hazard",
        "Default `vol_dispensed` transfers 200.0 uL from a 6x4 tube rack into `microamp_96_wellplate_100ul[A1]` whose maximum capacity is 100.0 uL (2.0x well overfill).",
    ),
    "protocol_library:5191b6": (
        "true_hazard",
        "Cumulative multi-reagent transfers into `opentrons_24_tuberack_nest_2ml_screwcap[A1]` (2,000.0 uL max capacity) exceed 2.0 mL on step 61 (+270.0 uL dispense causes tube overflow).",
    ),
    "protocol_library:74312c": (
        "true_hazard",
        "Transfers 10.0 uL of tetrahydrofuran twice into custom `pcb_board_250_wells[A1]`, whose custom labware definition declares a 2.0 uL micro-cavity capacity (5x single-dispense overfill).",
    ),
    "protocol_library:6d901d-2": (
        "true_hazard",
        "Default parameter bundle pairs `p300_multi_gen2` (calibrated minimum 20.0 uL) with a 1.0 uL CSV transfer on step 1, operating 20x below the pipette's minimum calibrated volume.",
    ),
    "protocol_library:6bc986-part-2": (
        "true_hazard",
        "Uses a `p50_multi` pipette (calibrated range 5.0-50.0 uL) to aspirate 4.0 uL of Proteinase K from `aspir8_1_reservoir_taped[A1]`, below the 5.0 uL minimum volume specification.",
    ),
    "protocol_library:0a9b58": (
        "true_hazard",
        "Routes a 10.5 uL sample transfer (`xfer 2 -> 3, 105 tenths`) through `p300_single_gen2` (20.0-200.0 uL filter-tip range), violating the 20.0 uL minimum calibrated P300 volume.",
    ),
    "protocol_library:0e525c": (
        "true_hazard",
        "Aspirates 180.0 uL followed by 160.0 uL (340.0 uL total) from a single `biorad_96_wellplate_200ul_pcr[A8]` well whose physical capacity is only 200.0 uL (impossible without undocumented mid-run refill).",
    ),
    "protocol_library:269b21": (
        "true_hazard",
        "Draws 4 x 5.0 uL = 20.0 uL out of `genmate_96_aluminumblock_20ul[A1]` (20.0 uL brim capacity), leaving 0.0 uL dead-volume margin and aspirating air on the final replicate.",
    ),
    "protocol_library:131de0": (
        "true_hazard",
        "Aspirates 3 x 10.0 uL = 30.0 uL per channel from `microampoptical_384_wellplate_30ul[A1]` (30.0 uL brim capacity), leaving zero dead-volume reserve in a 384-well optical plate.",
    ),
    "protocol_library:412ec7": (
        "true_hazard",
        "Attempts to aspirate 100.0 uL in a single stroke from `opentrons_96_aluminumblock_nest_wellplate_100ul[A1]` (100.0 uL max capacity), exhausting 100% of brim volume with zero dead-volume reserve.",
    ),
    "protocol_library:4883fc": (
        "true_hazard",
        "Splits a 67.0 uL sample normalization transfer (`33.5 + 33.5 uL` on `p50_single`) with `mix_after=(3, 50)` inside diluted well `B1` and re-enters concentrated sample stock `C1` with the same diluted tip.",
    ),
    # --- 11 DSL / Metadata Abstraction False Alarms (`abstraction_false_alarm`) ---
    "protocol_library:154ec5": (
        "abstraction_false_alarm",
        "Default example CSV includes a same-well `B2 -> B2` (6.0 uL) entry that lowers to `xfer(5, 5, 60)`; `REHEARSAL` enforces `src != dst` (`distinct_transfer_wells`) rather than treating same-well aspirate+dispense as a 1-stroke mix.",
    ),
    "protocol_library:543bf9": (
        "abstraction_false_alarm",
        "Pre-wets the `p50_single` tip in stock tube `B1` via explicit `aspirate(20.8) + dispense(20.8)` in `B1` before transferring; `REHEARSAL` rejects `src == dst` unless written as `pip.mix()`.",
    ),
    "protocol_library:60d861-2": (
        "abstraction_false_alarm",
        "`p20_multi_gen2.distribute()` returns 2.0 uL residual `disposal_volume` back into `nest_1_reservoir_195ml[A1]` via `dispense(2.0, rt_mix)`, which lowers to `xfer(49, 49, 20)` and trips `distinct_transfer_wells`.",
    ),
    "protocol_library:6cb818": (
        "abstraction_false_alarm",
        "Performs a manual 1-stroke `aspirate(20.0) + dispense(20.0)` mix in `nest_96_wellplate_320ul[A1]` after reagent addition instead of calling `pip.mix()`, tripping `distinct_transfer_wells`.",
    ),
    "protocol_library:00a214-protocol-1": (
        "abstraction_false_alarm",
        "Dispenses cell suspension from `.top()` (non-contact air dispense) above pre-wetted plate wells and reuses tips back into the cell reservoir; `REHEARSAL` models all `xfer` dispenses as meniscus-contacting.",
    ),
    "protocol_library:56b4ec": (
        "abstraction_false_alarm",
        "Splits an 80.0 uL transfer (`40.0 + 40.0 uL` on `p50_single`) from mixed intermediate tube `A1` into empty tube `A2`; integer floor division `(soluteAmt * v) // vol` rounds down by 1 unit on stroke 1, tripping strict concentration monotonicity on stroke 2.",
    ),
    "protocol_library:422b1e": (
        "abstraction_false_alarm",
        "Adds 2,000.0 uL titrant into `custom_beaker[A1]` and withdraws 2,000.0 uL; because API v2.x pre-2.14 lacks `Well.load_liquid` to declare the initial titrand already in the beaker, `REHEARSAL` infers `init_vol = 0` and flags a 5.0 uL dead-volume deficit.",
    ),
    "protocol_library:0961d2-part1": (
        "abstraction_false_alarm",
        "Adds 6.0 uL buffer to `Destination 1` (`biorad_96_wellplate_200ul_pcr[A1]`) containing undeclared pre-plated sample DNA (API v2.0) and mixes 6.0 uL; without `load_liquid`, inferred volume `6.0 uL` fails `deadVol (5.0 uL) + 6.0 <= 6.0`.",
    ),
    "protocol_library:158d42": (
        "abstraction_false_alarm",
        "Adds 50.0 uL diluent to a 1.5 mL tube holding undeclared starting RNA stock (API v2.11) and mixes 50.0 uL; without `load_liquid`, inferred volume `50.0 uL` fails `deadVol (5.0 uL) + 50.0 <= 50.0`.",
    ),
    "protocol_library:6c27ee": (
        "abstraction_false_alarm",
        "Transfers 30.0 uL into `corning_96_wellplate_360ul_flat[A1]` (pre-filled assay plate undeclared in API v2.8) and mixes 30.0 uL x 10 reps; inferred `30.0 uL` fails `deadVol (5.0 uL) + 30.0 <= 30.0`.",
    ),
    "protocol_library:76c562": (
        "abstraction_false_alarm",
        "Dispenses 5.0 uL into `nest_96_wellplate_100ul_pcr_full_skirt[A11]` (undeclared pre-staged diluent, plus conservative 5.0 uL default `deadVol` on a 100 uL PCR well) and mixes 5.0 uL x 3 reps.",
    ),
}


def _cache_path(cache_dir: Path, repo: str, sha: str, rel_path: str) -> Path:
    safe_name = f"{repo.replace('/', '__')}__{sha[:8]}__{rel_path.replace('/', '__')}"
    return cache_dir / safe_name


def _fetch_pinned_file(cache_dir: Path, repo: str, rel_path: str) -> tuple[Path, str]:
    sha = PINNED_REPOSITORIES[repo]["commit_sha"]
    dest = _cache_path(cache_dir, repo, sha, rel_path)
    if not dest.is_file():
        cache_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://raw.githubusercontent.com/{repo}/{sha}/{rel_path}"
        req = urllib.request.Request(url, headers={"User-Agent": "autolab-hub/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
    file_sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
    return dest, file_sha256


def _find_first_failing_step(imp: ImportedRehearsalProtocol) -> tuple[int, list[Any]]:
    lo, hi = 1, len(imp.steps)
    fail_k = len(imp.steps)
    while lo <= hi:
        mid = (lo + hi) // 2
        v = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps[:mid])
        if not v.allowed and v.rule != "tip_dropped_at_end":
            fail_k = mid
            hi = mid - 1
        else:
            lo = mid + 1
    vf = py_check_rehearsal(imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps[:fail_k])
    if vf.allowed or (vf.rule == "tip_dropped_at_end" and fail_k < len(imp.steps)):
        fail_k = len(imp.steps)
    return fail_k - 1, list(imp.steps[fail_k - 1])


def run_real_protocol_rehearsal(cache_dir: Path | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    audit = audit_lean_sources()
    if not audit["zero_sorry_verified"]:
        raise RuntimeError(f"Lean zero-sorry audit failed: {audit['violations']}")

    kernel = LeanBatchKernel()
    if not kernel.available:
        raise RuntimeError("Compiled `autolab-lean` binary not found; run `lake build` in `lean/` first.")

    eff_cache = cache_dir if cache_dir is not None else (REPO_ROOT / ".cache" / "opentrons_protocols")
    eff_cache.mkdir(parents=True, exist_ok=True)

    with ThreadPoolExecutor(max_workers=12) as pool:
        fetched = list(
            pool.map(
                lambda item: (*item, *_fetch_pinned_file(eff_cache, item[1], item[2])),
                PINNED_PROTOCOLS,
            )
        )

    protocol_rows: list[dict[str, Any]] = []
    imported_items: list[tuple[int, ImportedRehearsalProtocol, Any]] = []
    unsupported_counts: Counter[str] = Counter()

    for idx, (pid, repo, rel_path, local_path, file_sha256) in enumerate(fetched):
        repo_meta = PINNED_REPOSITORIES[repo]
        base_row: dict[str, Any] = {
            "protocol_id": pid,
            "repo": repo,
            "commit_sha": repo_meta["commit_sha"],
            "rel_path": rel_path,
            "upstream_license": repo_meta["upstream_license"],
            "file_sha256": file_sha256,
        }
        try:
            if repo == "Opentrons/Protocols" and rel_path.endswith(".py.json"):
                pb_obj = json.loads(local_path.read_text(encoding="utf-8"))
                meta = pb_obj.get("metadata") or {}
                base_row["title"] = meta.get("protocolName") or meta.get("title") or pid
                imp = simulate_and_import_protobuild(pb_obj, protocol_id=pid)
            else:
                base_row["title"] = pid
                imp = simulate_and_import_protocol(local_path, protocol_id=pid)

            py_v = py_check_rehearsal(
                imp.pip_min, imp.pip_max, imp.proto_hash, imp.failed_hashes, imp.wells, imp.steps
            )
            imported_items.append((idx, imp, py_v))
            base_row.update(
                {
                    "status": "allowed" if py_v.allowed else "denied",
                    "rule": py_v.rule,
                    "n_wells": len(imp.wells),
                    "n_steps": len(imp.steps),
                    "channel_mode": imp.channel_mode,
                    "pipette_models": list(imp.pipette_models),
                }
            )
        except UnsupportedProtocolStepError as exc:
            unsupported_counts[exc.reason] += 1
            base_row.update(
                {
                    "status": "unsupported",
                    "unsupported_reason": exc.reason,
                    "unsupported_detail": exc.detail,
                }
            )
        protocol_rows.append(base_row)

    # Batch-verify ALL imported real protocols through compiled `autolab-lean --batch-tsv`
    lean_verdicts = kernel.eval_lines([imp.to_tsv() for _, imp, _ in imported_items])
    parity_mismatches = 0
    deny_counts: Counter[str] = Counter()
    audited_denies: list[dict[str, Any]] = []

    for (row_idx, imp, py_v), lean_v in zip(imported_items, lean_verdicts):
        if (lean_v.allowed, lean_v.rule, lean_v.extra) != (py_v.allowed, py_v.rule, py_v.extra):
            parity_mismatches += 1
        if not lean_v.allowed:
            deny_counts[lean_v.rule] += 1
            row = protocol_rows[row_idx]
            pid = row["protocol_id"]
            if pid not in DENY_AUDIT_ANNOTATIONS:
                raise RuntimeError(f"Denied protocol {pid} ({lean_v.rule}) missing manual audit entry!")
            classification, explanation = DENY_AUDIT_ANNOTATIONS[pid]
            fail_idx, fail_step = _find_first_failing_step(imp)
            audited_denies.append(
                {
                    "protocol_id": pid,
                    "title": row.get("title", pid),
                    "repo": row["repo"],
                    "rel_path": row["rel_path"],
                    "rule": lean_v.rule,
                    "failing_step_index": fail_idx,
                    "failing_step": fail_step,
                    "classification": classification,
                    "explanation": explanation,
                }
            )

    if parity_mismatches != 0:
        raise RuntimeError(f"Lean <-> Python rehearsal parity failed on {parity_mismatches} real protocols!")

    n_total = len(protocol_rows)
    n_imported = len(imported_items)
    n_unsupported = n_total - n_imported
    n_allowed = sum(1 for r in protocol_rows if r["status"] == "allowed")
    n_denied = sum(1 for r in protocol_rows if r["status"] == "denied")

    n_false_alarm = sum(1 for a in audited_denies if a["classification"] == "abstraction_false_alarm")
    n_true_hazard = sum(1 for a in audited_denies if a["classification"] == "true_hazard")
    fa_rate = round(100.0 * n_false_alarm / max(1, len(audited_denies)), 1)

    return {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lean_toolchain": "leanprover/lean4:v4.36.0",
        "simulator_backend": "opentrons.simulate (CPU)",
        "runtime_sec": round(time.perf_counter() - t0, 2),
        "pinned_repositories": PINNED_REPOSITORIES,
        "summary": {
            "n_total": n_total,
            "n_imported": n_imported,
            "n_unsupported": n_unsupported,
            "imported_pct": round(100.0 * n_imported / n_total, 1),
            "n_allowed": n_allowed,
            "n_denied": n_denied,
            "allowed_of_imported_pct": round(100.0 * n_allowed / max(1, n_imported), 1),
            "denied_of_imported_pct": round(100.0 * n_denied / max(1, n_imported), 1),
            "lean_python_mirror_mismatches": parity_mismatches,
            "audited_denies_count": len(audited_denies),
            "audited_true_hazard_count": n_true_hazard,
            "audited_false_alarm_count": n_false_alarm,
            "audited_false_alarm_rate_pct": fa_rate,
        },
        "unsupported_by_reason": dict(sorted(unsupported_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "deny_counts_by_rule": dict(sorted(deny_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "audited_denies": audited_denies,
        "protocols": protocol_rows,
    }


def main() -> int:
    payload = run_real_protocol_rehearsal()
    out_path = REPO_ROOT / "benchmarks" / "results" / "opentrons_library_rehearsal.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "protocols"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
