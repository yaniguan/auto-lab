"""Auto-Lab Hub: 7-Layer Embodied Co-Scientist Infrastructure & Post-Training Stack."""

from autolab.catalog import (
    COMPANION_REPOS,
    CORE_REPO_NAMES,
    LAYERS,
    get_repo,
    load_catalog,
    load_issues_index,
)
from autolab.loop_demo import SCENARIOS, run_closed_loop_scenario

__all__ = [
    "COMPANION_REPOS",
    "CORE_REPO_NAMES",
    "LAYERS",
    "SCENARIOS",
    "get_repo",
    "load_catalog",
    "load_issues_index",
    "run_closed_loop_scenario",
]

__version__ = "0.1.0"
