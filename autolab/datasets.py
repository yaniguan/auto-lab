"""Deterministic, SHA-256-verified dataset loaders for Auto-Lab benchmarks.

Uses only the Python standard library so `autolab-hub` retains zero mandatory
third-party runtime dependencies (`pyproject.toml`). Never falls back silently
to synthetic data: missing or corrupted files raise `RuntimeError`.
"""

from __future__ import annotations

import csv
import hashlib
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Sequence

from autolab.catalog import REPO_ROOT

ESOL_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv"
ESOL_SHA256 = "8c06a76f0c6487d29ab0f903e6a7a7139f189ab3c1178f159c8be8964602f189"
ESOL_EXPECTED_ROWS = 1128
ESOL_FEATURE_COLUMNS: tuple[str, ...] = (
    "Molecular Weight",
    "Number of H-Bond Donors",
    "Number of Rings",
    "Number of Rotatable Bonds",
    "Polar Surface Area",
    "Minimum Degree",
)
ESOL_TARGET_COLUMN = "measured log solubility in mols per litre"


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _verify_esol_file(path: Path, *, expected_sha256: str = ESOL_SHA256) -> None:
    if not path.is_file():
        raise RuntimeError(f"Delaney ESOL CSV does not exist: {path}")
    actual = compute_sha256(path)
    if actual.lower() != expected_sha256.lower():
        raise RuntimeError(
            f"SHA-256 mismatch for Delaney ESOL CSV at {path}: "
            f"expected {expected_sha256}, got {actual}"
        )


def resolve_esol_csv(
    *,
    cache_path: Path | None = None,
    search_roots: Sequence[Path] | None = None,
    allow_download: bool = True,
    expected_sha256: str = ESOL_SHA256,
) -> tuple[Path, str]:
    """Locate or deterministically download `delaney-processed.csv` with SHA-256 verification.

    Search order:
    1. Explicit `cache_path` (defaults to gitignored `<repo>/.cache/esol/delaney-processed.csv`).
    2. Sibling `lab-decide` / `assayfold` checkouts under `search_roots` (defaults to `<repo>/..`).
    3. HTTPS download from DeepChem MoleculeNet S3 into `cache_path` when `allow_download=True`.

    Raises `RuntimeError` if no verified copy can be obtained.
    """
    target_cache = cache_path if cache_path is not None else (REPO_ROOT / ".cache" / "esol" / "delaney-processed.csv")
    roots = list(search_roots) if search_roots is not None else [REPO_ROOT.parent]

    candidates: list[tuple[Path, str]] = [(target_cache, "cache:.cache/esol/delaney-processed.csv")]
    for root in roots:
        for sibling in ("lab-decide", "assayfold"):
            sib_dir = root / sibling
            if sib_dir.is_dir():
                direct = sib_dir / "data" / "delaney-processed.csv"
                if direct.is_file():
                    candidates.append((direct, f"sibling:{sibling}/data/delaney-processed.csv"))
                else:
                    for found in sorted(sib_dir.rglob("*delaney*.csv")):
                        if found.is_file():
                            rel = found.relative_to(root).as_posix()
                            candidates.append((found, f"sibling:{rel}"))

    for cand_path, label in candidates:
        if cand_path.is_file():
            _verify_esol_file(cand_path, expected_sha256=expected_sha256)
            return cand_path, label

    if not allow_download:
        raise RuntimeError(
            "Delaney ESOL dataset ('delaney-processed.csv') not found in local cache or sibling "
            "repositories ('lab-decide', 'assayfold'), and network download is disabled."
        )

    target_cache.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target_cache.parent),
        prefix=".delaney-processed.",
        suffix=".part",
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        req = urllib.request.Request(ESOL_URL, headers={"User-Agent": "autolab-hub/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp, tmp_path.open("wb") as out_fh:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out_fh.write(chunk)
        _verify_esol_file(tmp_path, expected_sha256=expected_sha256)
        os.replace(tmp_path, target_cache)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        if isinstance(exc, RuntimeError):
            raise
        raise RuntimeError(f"Failed to download verified Delaney ESOL CSV from {ESOL_URL}: {exc}") from exc

    return target_cache, "downloaded:.cache/esol/delaney-processed.csv"


def load_esol_dataset(
    *,
    cache_path: Path | None = None,
    search_roots: Sequence[Path] | None = None,
    allow_download: bool = True,
) -> tuple[list[list[float]], list[float], str]:
    """Load all 1,128 SHA-256-verified Delaney ESOL compounds without silent synthetic fallbacks."""
    csv_path, origin = resolve_esol_csv(
        cache_path=cache_path,
        search_roots=search_roots,
        allow_download=allow_download,
    )
    features: list[list[float]] = []
    targets: list[float] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = set(reader.fieldnames or ())
        missing_cols = [c for c in (*ESOL_FEATURE_COLUMNS, ESOL_TARGET_COLUMN) if c not in fieldnames]
        if missing_cols:
            raise RuntimeError(f"Delaney ESOL CSV at {csv_path} missing required columns: {missing_cols}")
        for row in reader:
            try:
                x_row = [float(row[col]) for col in ESOL_FEATURE_COLUMNS]
                y_val = float(row[ESOL_TARGET_COLUMN])
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"Invalid numeric cell in Delaney ESOL CSV at {csv_path}: {exc}") from exc
            features.append(x_row)
            targets.append(y_val)

    if len(features) != ESOL_EXPECTED_ROWS:
        raise RuntimeError(
            f"Expected {ESOL_EXPECTED_ROWS} rows in Delaney ESOL CSV at {csv_path}, got {len(features)}"
        )
    source_desc = f"real_esol ({len(features)} compounds, sha256={ESOL_SHA256[:12]}, via {origin})"
    return features, targets, source_desc
