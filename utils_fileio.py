#!/usr/bin/env python3
"""
Orchestrator File I/O Utilities
File I/O operations and path management for the NetLogo orchestrator.
"""

import base64
import json
import logging
import os
import pathlib
from typing import Dict, Any, List, Optional

from utils_config_constants import INPUT_NETLOGO_DIR, INPUT_ICRASH_DIR, MESSIR_RULES_FILE, LOG_DIR, OUTPUT_DIR
from utils_path import get_run_base_dir

# Configure logging
logger = logging.getLogger(__name__)

def find_files(directory, extension):
    """Find all files in a directory with a given extension."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]

def get_netlogo_cases():
    """Returns a list of available NetLogo case study names."""
    files = find_files(INPUT_NETLOGO_DIR, "-netlogo-code.md")
    # Extract the base name, e.g., "3d-solids" from "3d-solids-netlogo-code.md"
    return sorted([os.path.basename(f).replace("-netlogo-code.md", "") for f in files])

def read_file_content(filepath):
    """Reads and returns the content of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return ""

def read_netlogo_case_content(case_name):
    """Reads the content of a specific NetLogo case file."""
    filepath = os.path.join(INPUT_NETLOGO_DIR, f"{case_name}-netlogo-code.md")
    return read_file_content(filepath)

def write_json(filepath, data):
    """Writes a dictionary to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Successfully wrote JSON to {filepath}")
    except Exception as e:
        logger.error(f"Failed to write JSON to {filepath}: {e}")

def write_file_content(filepath, content):
    """Writes string content to a file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully wrote content to {filepath}")
    except Exception as e:
        logger.error(f"Failed to write content to {filepath}: {e}")

def create_run_output_directory(run_name, case, model, persona_set):
    """Creates a unique directory for the agent run outputs."""
    dir_name = f"{run_name}-{case}-{model}-{persona_set}"
    output_path = os.path.join(OUTPUT_DIR, dir_name)
    os.makedirs(output_path, exist_ok=True)
    return output_path

def load_and_encode_images(case_name, logger):
    """Finds, loads, and base64-encodes NetLogo interface images for a given case."""
    encoded_images = []
    image_dir = INPUT_NETLOGO_DIR
    
    for i in range(1, 3):  # Check for interface-1.png and interface-2.png
        image_filename = f"{case_name}-netlogo-interface-{i}.png"
        image_filepath = os.path.join(image_dir, image_filename)
        
        if os.path.exists(image_filepath):
            try:
                with open(image_filepath, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    encoded_images.append(encoded_string)
                    logger.info(f"Successfully loaded and encoded image: {image_filename}")
            except Exception as e:
                logger.warning(f"Could not read or encode image {image_filename}: {e}")
        else:
            logger.info(f"Interface image not found, skipping: {image_filename}")
            
    return encoded_images
