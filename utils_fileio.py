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

from utils_config_constants import INPUT_NETLOGO_DIR, LUCIM_RULES_FILE, LOG_DIR, OUTPUT_DIR
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

def create_run_output_directory(run_name, case, model, persona_set, reasoning=None, verbosity=None):
    """Create the per-run output directory under the canonical runs/ hierarchy.

    Layout:
      output/runs/<YYYY-MM-DD>/<HHMM>-<PERSONA-SET>/<case>-<model>-reason-<reasoning>-verb-<verbosity>/
    """
    # Fallback defaults to keep behavior consistent if None is passed
    reasoning = reasoning or "medium"
    verbosity = verbosity or "medium"

    # Delegate path construction to the centralized helper to avoid drift
    run_base_dir = get_run_base_dir(
        timestamp_str=run_name,
        base_name=case,
        model_name=model,
        reasoning_effort=reasoning,
        text_verbosity=verbosity,
        persona_set=persona_set,
    )

    # Ensure directory exists and return as string for callers using os.path.join
    pathlib.Path(run_base_dir).mkdir(parents=True, exist_ok=True)
    return str(run_base_dir)

def write_input_instructions_before_api(output_dir: str, system_prompt: str) -> None:
    """
    Write input-instructions.md file BEFORE making API call.
    This ensures the file is available for debugging even if the API call fails.
    
    Args:
        output_dir: Directory where to write the file
        system_prompt: Complete system prompt to write to file
    """
    try:
        input_instructions_path = os.path.join(output_dir, "input-instructions.md")
        write_file_content(input_instructions_path, system_prompt)
        logger.info(f"Successfully wrote complete system prompt to: {input_instructions_path}")
    except Exception as e:
        logger.error(f"Failed to write input-instructions.md before API call: {e}")
        raise

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


def extract_plantuml_from_response(raw_response_dict: Dict[str, Any], output_dir: str, logger: logging.Logger) -> Optional[str]:
    """
    Extract PlantUML diagram text from raw_response.json structure.
    
    Args:
        raw_response_dict: The raw response dictionary from the API
        output_dir: Output directory (for logging context)
        logger: Logger instance
        
    Returns:
        PlantUML text as string, or None if not found
    """
    try:
        # Navigate to output[1].content[0].text (message content, not reasoning)
        output_items = raw_response_dict.get("output", [])
        if not output_items:
            logger.info("No output items found in raw_response.json")
            return None
        
        # Look for message type output (not reasoning)
        message_output = None
        for output_item in output_items:
            if output_item.get("type") == "message":
                message_output = output_item
                break
        
        if not message_output:
            logger.info("No message output found in raw_response.json")
            return None
            
        content_items = message_output.get("content", [])
        if not content_items:
            logger.info("No content items found in message output")
            return None
            
        text_content = content_items[0].get("text", "")
        if not text_content:
            logger.info("No text content found in message output")
            return None
            
        # Parse JSON string to dict
        try:
            parsed_data = json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from text content: {e}")
            # Fallback: search for PlantUML directly in text
            if "@startuml" in text_content and "@enduml" in text_content:
                logger.info("Found PlantUML content in raw text (non-JSON)")
                return text_content
            return None
            
        # Extract from typical.plantuml (primary path)
        plantuml_text = None
        if isinstance(parsed_data, dict):
            typical = parsed_data.get("typical", {})
            if isinstance(typical, dict):
                plantuml_text = typical.get("plantuml", "")
            
            # Fallback: recursive search for PlantUML content
            if not plantuml_text or "@startuml" not in plantuml_text:
                def find_plantuml_recursive(obj: Any) -> Optional[str]:
                    """Recursively search for PlantUML content."""
                    if isinstance(obj, str) and "@startuml" in obj and "@enduml" in obj:
                        return obj
                    if isinstance(obj, dict):
                        for key in ("plantuml", "diagram", "uml", "content", "text"):
                            val = obj.get(key)
                            if isinstance(val, str) and "@startuml" in val and "@enduml" in val:
                                return val
                        # Recursively search nested values
                        for val in obj.values():
                            found = find_plantuml_recursive(val)
                            if found:
                                return found
                    if isinstance(obj, list):
                        for item in obj:
                            found = find_plantuml_recursive(item)
                            if found:
                                return found
                    return None
                
                plantuml_text = find_plantuml_recursive(parsed_data)
        
        # Validate PlantUML content
        if plantuml_text and isinstance(plantuml_text, str):
            if "@startuml" in plantuml_text and "@enduml" in plantuml_text:
                logger.info("Successfully extracted PlantUML diagram from response")
                return plantuml_text.strip()
            else:
                logger.warning("Extracted text does not contain valid PlantUML markers")
                return None
        else:
            logger.info("No PlantUML content found in response")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting PlantUML from response: {e}", exc_info=True)
        return None


def extract_audit_from_response(raw_response_dict: Dict[str, Any], output_dir: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Extract audit report from raw_response.json structure.
    
    Args:
        raw_response_dict: The raw response dictionary from the API
        output_dir: Output directory (for logging context)
        logger: Logger instance
        
    Returns:
        Audit data as dict with 'verdict' and 'non-compliant-rules', or None if not found
    """
    try:
        # Navigate to output[1].content[0].text (message content, not reasoning)
        output_items = raw_response_dict.get("output", [])
        if not output_items:
            logger.info("No output items found in raw_response.json for audit extraction")
            return None
        
        # Look for message type output (not reasoning)
        message_output = None
        for output_item in output_items:
            if output_item.get("type") == "message":
                message_output = output_item
                break
        
        if not message_output:
            logger.info("No message output found in raw_response.json for audit extraction")
            return None
            
        content_items = message_output.get("content", [])
        if not content_items:
            logger.info("No content items found in message output for audit extraction")
            return None
            
        text_content = content_items[0].get("text", "")
        if not text_content:
            logger.info("No text content found in message output for audit extraction")
            return None
            
        # Parse JSON string to dict
        try:
            parsed_data = json.loads(text_content)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from text content for audit: {e}")
            return None
            
        # Search for audit structure with 'verdict' and 'non-compliant-rules'
        def find_audit_recursive(obj: Any) -> Optional[Dict[str, Any]]:
            """Recursively search for audit data structure."""
            if isinstance(obj, dict):
                # Check if this dict has audit structure
                if "verdict" in obj:
                    # Found potential audit structure
                    audit_data = {
                        "verdict": obj.get("verdict", ""),
                        "non-compliant-rules": obj.get("non-compliant-rules", [])
                    }
                    # Validate it has at least verdict
                    if audit_data["verdict"]:
                        return audit_data
                
                # Check common nested paths
                for key in ("data", "typical", "audit", "result"):
                    val = obj.get(key)
                    if isinstance(val, dict):
                        found = find_audit_recursive(val)
                        if found:
                            return found
                
                # Recursively search all nested dicts
                for val in obj.values():
                    found = find_audit_recursive(val)
                    if found:
                        return found
                        
            if isinstance(obj, list):
                for item in obj:
                    found = find_audit_recursive(item)
                    if found:
                        return found
                        
            return None
        
        audit_data = find_audit_recursive(parsed_data)
        
        if audit_data:
            logger.info(f"Successfully extracted audit report: verdict={audit_data.get('verdict')}")
            return audit_data
        else:
            logger.info("No audit data found in response")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting audit from response: {e}", exc_info=True)
        return None


def save_extracted_artifacts(output_dir: str, plantuml_text: Optional[str], audit_data: Optional[Dict[str, Any]], logger: logging.Logger) -> None:
    """
    Save extracted PlantUML and audit artifacts to files.
    
    Args:
        output_dir: Directory where to save files
        plantuml_text: PlantUML diagram text (optional)
        audit_data: Audit data dict with 'verdict' and 'non-compliant-rules' (optional)
        logger: Logger instance
    """
    # Save PlantUML diagram
    if plantuml_text:
        try:
            puml_filepath = os.path.join(output_dir, "diagram.puml")
            write_file_content(puml_filepath, plantuml_text)
            logger.info(f"Successfully saved PlantUML diagram to: {puml_filepath}")
        except Exception as e:
            logger.error(f"Failed to save PlantUML diagram: {e}", exc_info=True)
    else:
        logger.info("No PlantUML content to save; skipping diagram.puml creation")
    
    # Save audit report as Markdown
    if audit_data:
        try:
            verdict = audit_data.get("verdict", "unknown")
            non_compliant_rules = audit_data.get("non-compliant-rules", [])
            
            # Format as readable Markdown
            markdown_lines = [
                "# LUCIM Compliance Audit Report",
                "",
                f"## Verdict: {verdict.upper()}",
                "",
            ]
            
            if non_compliant_rules:
                markdown_lines.append("## Non-Compliant Rules")
                markdown_lines.append("")
                for i, rule in enumerate(non_compliant_rules, 1):
                    rule_name = rule.get("rule", "Unknown rule")
                    line_num = rule.get("line", "?")
                    message = rule.get("msg", "No description")
                    markdown_lines.append(f"### {i}. {rule_name}")
                    markdown_lines.append(f"**Line:** {line_num}")
                    markdown_lines.append(f"**Issue:** {message}")
                    markdown_lines.append("")
            else:
                markdown_lines.append("No non-compliant rules found.")
                markdown_lines.append("")
            
            audit_content = "\n".join(markdown_lines)
            audit_filepath = os.path.join(output_dir, "audit.md")
            write_file_content(audit_filepath, audit_content)
            logger.info(f"Successfully saved audit report to: {audit_filepath}")
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}", exc_info=True)
    else:
        logger.info("No audit data to save; skipping audit.md creation")

    # Persist machine-readable audit JSONs expected by analysis tools
    try:
        if audit_data:
            # Always write final audit JSON
            audit_final_path = os.path.join(output_dir, "audit_final.json")
            write_json(audit_final_path, audit_data)
            logger.info(f"Successfully wrote JSON audit to: {audit_final_path}")

            # If no initial audit JSON exists yet, mirror the same data as initial
            audit_initial_path = os.path.join(output_dir, "audit_initial.json")
            if not os.path.exists(audit_initial_path):
                write_json(audit_initial_path, audit_data)
                logger.info(f"No initial audit found; mirrored final audit to: {audit_initial_path}")
        else:
            logger.info("No audit data to save as JSON; skipping audit_final.json / audit_initial.json")
    except Exception as e:
        logger.warning(f"Could not persist JSON audit artifacts: {e}")

    # Provide baseline diagram variant when only a single diagram exists
    try:
        diagram_path = os.path.join(output_dir, "diagram.puml")
        diagram_initial_path = os.path.join(output_dir, "diagram_initial.puml")
        if os.path.exists(diagram_path) and not os.path.exists(diagram_initial_path):
            content = read_file_content(diagram_path)
            write_file_content(diagram_initial_path, content)
            logger.info(f"Created baseline initial diagram: {diagram_initial_path}")
    except Exception as e:
        logger.warning(f"Could not create baseline initial diagram: {e}")
