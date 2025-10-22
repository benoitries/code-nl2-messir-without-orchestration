#!/usr/bin/env python3
"""
Path utilities for orchestrator and agents.

Provides centralized construction of run directories following the
new layout:

  output/runs/<YYYY-MM-DD>/<HHMM>/<case>-<model-name>-reason-<reasoning-value>-verb-<verbosity-value>/<NN-stage>/

This builder is deterministic and should be the single source of truth
for output folder computation across modules.
"""

import pathlib
from datetime import datetime
from typing import Optional

from utils_config_constants import OUTPUT_DIR


def build_combination_folder_name(
    base_name: str,
    model_name: str,
    reasoning_effort: str,
    text_verbosity: str,
) -> str:
    """Return the combination folder name for a given case/model/reasoning/verbosity.

    Example: "boiling-<model>-reason-medium-verb-high"
    """
    return f"{base_name}-{model_name}-reason-{reasoning_effort}-verb-{text_verbosity}"


def get_run_base_dir(
    timestamp_str: str,
    base_name: str,
    model_name: str,
    reasoning_effort: str,
    text_verbosity: str,
    persona_set: str = "persona-v1",
) -> pathlib.Path:
    """Compute the base directory for a run combination.

    Args:
        timestamp: Timestamp string formatted as YYYYMMDD_HHMM
        case_name: Case identifier (base name)
        model_name: Model name (from AVAILABLE_MODELS)
        reasoning_effort: minimal|low|medium|high
        text_verbosity: low|medium|high
        persona_set: Persona set name (default: persona-v1)
        output_dir: Override for OUTPUT_DIR mainly for testing

    Returns:
        Path to: OUTPUT_DIR/runs/YYYY-MM-DD/HHMM-<PERSONA_SET_NAME>/<combination-folder>
    """
    dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
    run_date = dt.strftime("%Y-%m-%d")
    run_time = dt.strftime("%H%M")

    # New fine-grained path: output/runs/<YYYY-MM-DD>/<HHMM>-<PERSONA_SET>/<case>-<model>-reason-<effort>-verb-<verbosity>/
    run_dir = (
        OUTPUT_DIR
        / "runs"
        / run_date
        / f"{run_time}-{persona_set}"
    )
    combo = build_combination_folder_name(base_name, model_name, reasoning_effort, text_verbosity)
    return run_dir / combo


