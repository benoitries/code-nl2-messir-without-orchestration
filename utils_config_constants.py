#!/usr/bin/env python3
"""
Configuration file for NetLogo to PlantUML pipeline
Centralizes all file and directory path constants
"""

import os
from utils_api_key import get_api_key_for_model
import pathlib
from pathlib import Path
from typing import Dict, Set
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory (parent of this file)
BASE_DIR = pathlib.Path(__file__).resolve().parent

# API key will be selected dynamically based on the chosen model (set after DEFAULT_MODEL)

# Default persona set
DEFAULT_PERSONA_SET = "persona-v3-limited-agents"

# Input directories - use environment variables if set, otherwise use default paths
# Point to experimentation/input directories
BASE_DIR_PARENT = BASE_DIR.parent  # Go up one level to project root
INPUT_NETLOGO_DIR = Path(os.getenv("INPUT_NETLOGO_DIR", BASE_DIR_PARENT / "experimentation" / "input" / "input-netlogo"))
INPUT_VALID_EXAMPLES_DIR = Path(os.getenv("INPUT_VALID_EXAMPLES_DIR", BASE_DIR_PARENT / "experimentation" / "input" / "input-valid-examples"))
INPUT_PERSONA_DIR = Path(os.getenv("INPUT_PERSONA_DIR", BASE_DIR_PARENT / "experimentation" / "input" / "input-persona"))

# Output directory
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = OUTPUT_DIR / "logs"

# Persona files (default to DEFAULT_PERSONA_SET)
PERSONA_LUCIM_OPERATION_MODEL_GENERATOR = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "PSN_LUCIM_Operation_Model_Generator.md"
PERSONA_LUCIM_OPERATION_MODEL_AUDITOR = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "PSN_LUCIM_Operation_Model_Auditor.md"
PERSONA_LUCIM_SCENARIO_GENERATOR = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "PSN_LUCIM_Scenario_Generator.md"
PERSONA_LUCIM_PLANTUML_DIAGRAM_GENERATOR = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "PSN_LUCIM_PlantUML_Diagram_Generator.md"
PERSONA_LUCIM_PLANTUML_DIAGRAM_AUDITOR = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "PSN_LUCIM_PlantUML_Diagram_Auditor.md"

# Additional LUCIM rules and mapping files (scoped to DEFAULT_PERSONA_SET)
RULES_LUCIM_OPERATION_MODEL_FILE = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "RULES_LUCIM_Operation_model.md"
RULES_LUCIM_SCENARIO_FILE = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "RULES_LUCIM_Scenario.md"
RULES_LUCIM_PLANTUML_DIAGRAM_FILE = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "RULES_LUCIM_PlantUML_Diagram.md"
RULES_MAPPING_NETLOGO_TO_OPERATION_MODEL_FILE = INPUT_PERSONA_DIR / DEFAULT_PERSONA_SET / "RULES_MAPPING_NETLOGO_TO_OPERATION_MODEL.md"

# File patterns
NETLOGO_CODE_PATTERN = "*-netlogo-code.md"
NETLOGO_INTERFACE_PATTERN = "*-netlogo-interface-*.png"

# Available AI models (single source of truth)
# Note: Only update model names here.
AVAILABLE_MODELS = [
    "gpt-5-nano-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-2025-08-07",
    # Additional providers/models
    "gemini-flash-latest",          # latest gemini flash
    "gemini-2.5-pro",               # gemini 2.5 Pro
    "mistral-reasoning-latest",     # most recent reasoning Mistral
    "llama-reasoning-latest"        # most recent reasoning Llama
]

# Default model derived from AVAILABLE_MODELS
DEFAULT_MODEL = AVAILABLE_MODELS[1] if AVAILABLE_MODELS else ""

# API key selected dynamically based on the default model/provider
OPENAI_API_KEY = get_api_key_for_model(DEFAULT_MODEL) if DEFAULT_MODEL else ""

# Agent-specific configurations
# Each agent can be configured with:
# - model: The AI model to use (currently only "gpt-5" supported)
# - reasoning_effort: "minimal", "low", "medium", or "high"
# - reasoning_summary: "auto" or "manual"
# - text_verbosity: "low", "medium", or "high"
AGENT_CONFIGS = {
    "lucim_operation_model_generator": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    },
    "lucim_operation_model_auditor": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    },
    "lucim_scenario_generator": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    },
    "lucim_scenario_auditor": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    },
    "lucim_plantuml_diagram_generator": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    },
    "lucim_plantuml_diagram_auditor": {
        "model": DEFAULT_MODEL,
        "reasoning_effort": "medium",  # Default medium for consistency
        "reasoning_summary": "auto",
        "text_verbosity": "medium"
    }
}

# Timeouts and heartbeat (in seconds)
# Agent-level polling timeouts for OpenAI Responses API
# Default: None (no timeout) for all agents; CLI can override via presets
AGENT_TIMEOUTS = {
    "lucim_operation_model_generator": None,
    "lucim_operation_model_auditor": None,
    "lucim_scenario_generator": None,
    "lucim_scenario_auditor": None,
    "lucim_plantuml_diagram_generator": None,
    "lucim_plantuml_diagram_auditor": None,
}

# Orchestrator watchdog for parallel first stage (syntax + semantics)
# Default: None (no watchdog); CLI can override via presets
ORCHESTRATOR_PARALLEL_TIMEOUT = None
HEARTBEAT_SECONDS = 30  # periodic log while waiting


def ensure_directories():
    """Ensure all required directories exist"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    # Only create input directories if they don't exist and are not pointing to external directories
    if not INPUT_NETLOGO_DIR.exists():
        INPUT_NETLOGO_DIR.mkdir(exist_ok=True)
    if not INPUT_PERSONA_DIR.exists():
        INPUT_PERSONA_DIR.mkdir(exist_ok=True)
    # INPUT_VALID_EXAMPLES_DIR is a symlink, don't try to create it


def get_agent_config(agent_name: str) -> dict:
    """Get the complete configuration for a specific agent"""
    return AGENT_CONFIGS.get(agent_name, AGENT_CONFIGS.get("lucim_operation_model_generator", {}))

def get_reasoning_config(agent_name: str) -> dict:
    """Get the complete API configuration for an agent including reasoning, text and model"""
    agent_config = get_agent_config(agent_name)
    model_name = agent_config["model"]

    api_config = {
        "model": model_name
    }

    api_config["reasoning"] = {
        "effort": agent_config["reasoning_effort"],
        "summary": agent_config["reasoning_summary"]
    }

    api_config["text"] = {
        "verbosity": agent_config.get("text_verbosity", "medium")
    }

    return api_config



 

# Unified Agent Response Schema (common fields only; agent-specific structures live in persona/DSL files)
AGENT_RESPONSE_SCHEMA = {
    "common_fields": {
        "agent_type": str,
        "model": str,
        "timestamp": str,
        "base_name": str,
        # Accept integer or string step numbers, and allow None during early wiring
        "step_number": (int, str, type(None)),
        "reasoning_summary": str,
        "errors": list,
        # Allow data to be absent/None when upstream returns empty content
        "data": (dict, type(None))
    }
}

def validate_agent_response(agent_type: str, response: dict) -> list:
    """Validate that response contains required common fields with correct types.

    Agent-specific data structure requirements are defined in input-persona files and are
    not duplicated here to avoid drift. Downstream agents should validate content based on
    those authoritative references when needed.
    """
    errors = []

    for field, field_type in AGENT_RESPONSE_SCHEMA["common_fields"].items():
        if field not in response:
            errors.append(f"Missing required field: {field}")
        # If schema permits multiple types, isinstance handles tuple typing
        elif not isinstance(response[field], field_type):
            errors.append(f"Field {field} must be of type {field_type}")

    return errors


# Response Schema Constants (moved from response_schema_expected.py)
# Expected top-level key sets for each agent's response.json.
# These sets enforce exact presence: not less, not more.

COMMON_KEYS = {
    "agent_type",
    "model",
    "timestamp",
    "base_name",
    "step_number",
    "reasoning_summary",
    "data",
    "errors",
    "tokens_used",
    "input_tokens",
    "visible_output_tokens",
    "reasoning_tokens",
    "total_output_tokens",
    # Include raw_usage as existing agents store it in reasoning payload, not in response.json
}

# Some agents might include raw_response dump for auditing
OPTIONAL_KEYS = {"raw_response"}

AGENT_KEYS: Dict[str, Set[str]] = {
    "lucim_operation_model_generator": COMMON_KEYS | OPTIONAL_KEYS,
    "lucim_operation_model_auditor": COMMON_KEYS | OPTIONAL_KEYS,
    "lucim_scenario_generator": COMMON_KEYS | OPTIONAL_KEYS,
    "lucim_scenario_auditor": COMMON_KEYS | OPTIONAL_KEYS,
    "lucim_plantuml_diagram_generator": COMMON_KEYS | OPTIONAL_KEYS,
    "lucim_plantuml_diagram_auditor": COMMON_KEYS | OPTIONAL_KEYS,
}


def expected_keys_for_agent(agent_type: str) -> Set[str]:
    """Get expected keys for a specific agent type."""
    return AGENT_KEYS.get(agent_type, COMMON_KEYS | OPTIONAL_KEYS)


def get_persona_file_paths(persona_set: str = DEFAULT_PERSONA_SET) -> Dict[str, Path]:
    """
    Get persona file paths for a specific persona set.
    
    Args:
        persona_set: Name of the persona set (subfolder in input-persona)
        
    Returns:
        Dictionary mapping persona file names to their paths
    """
    persona_dir = INPUT_PERSONA_DIR / persona_set
    
    return {
        # v3 pipeline does not include legacy syntax/behavior agents
        "lucim_operation_model_generator": persona_dir / "PSN_3_LUCIMEnvironmentSynthesizer.md",
        "lucim_operation_model_auditor": persona_dir / "PSN_4_LUCIMScenarioSynthesizer.md",
        "lucim_scenario_generator": persona_dir / "PSN_4_LUCIMScenarioSynthesizer.md",
        "lucim_scenario_auditor": persona_dir / "PSN_5_PlantUMLWriter.md",
        "lucim_plantuml_diagram_generator": persona_dir / "PSN_6_PlantUMLWriter.md",
        "lucim_plantuml_diagram_auditor": persona_dir / "PSN_7_PlantUMLWriter.md",
    }
