#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main script for the NetLogo to LUCIM conversion agent.
This single agent handles the entire pipeline from NetLogo code to a compliant PlantUML diagram.
"""

import os
import sys
import argparse
from datetime import datetime
import base64
import re

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import utility modules
try:
    import utils_config_constants as cfg
    import utils_logging as log
    import utils_openai_client as openai_client
    import utils_fileio as fileio
    import utils_format as fmt
    import utils_plantuml as plantuml
    import utils_ui as ui
except ImportError as e:
    print(f"Error: Failed to import utility modules. Make sure they are in the project root. Details: {e}")
    sys.exit(1)

def build_api_input(input_contents):
    """Builds the list of messages for the AI model's 'input' field."""

    # Combine all text inputs (task instructions should head the list)
    text_parts = []
    if "task_instructions" in input_contents and input_contents["task_instructions"]:
        text_parts.append(input_contents["task_instructions"])
    for key, content in input_contents.items():
        if key not in ["netlogo_images"]:
            text_parts.append(f"\n--- {key.upper()} ---\n{content}")
    
    full_text_prompt = "\n".join(text_parts)
    
    # Create the message structure for the 'input' field
    user_content = [{"type": "input_text", "text": full_text_prompt}]
    
    # Add images to the message content
    if "netlogo_images" in input_contents:
        for img_base64 in input_contents["netlogo_images"]:
            # Responses API expects 'input_image' with an image URL; use data URL with base64
            user_content.append({
                "type": "input_image",
                "image_url": f"data:image/png;base64,{img_base64}"
            })
            
    return [{"role": "user", "content": user_content}]

def parse_and_save_artifacts(output_text, output_dir, logger):
    """Parses the AI's text output to extract and save diagrams and audits."""
    import re

    artifacts = {
        "diagram_initial": r"\[START_INITIAL_DIAGRAM\](.*?)\[END_INITIAL_DIAGRAM\]",
        "audit_initial": r"\[START_INITIAL_AUDIT\](.*?)\[END_INITIAL_AUDIT\]",
        "diagram_corrected": r"\[START_CORRECTED_DIAGRAM\](.*?)\[END_CORRECTED_DIAGRAM\]",
        "audit_final": r"\[START_FINAL_AUDIT\](.*?)\[END_FINAL_AUDIT\]",
    }

    for name, pattern in artifacts.items():
        match = re.search(pattern, output_text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            extension = ".puml" if "diagram" in name else ".json"
            filepath = os.path.join(output_dir, f"{name}{extension}")
            fileio.write_file_content(filepath, content)
            logger.info(f"Extracted and saved artifact: {name}{extension}")
        else:
            logger.info(f"Artifact not found in output: {name}")

def main():
    """
    Main function to run the NetLogo to LUCIM conversion agent.
    """
    # Ensure all necessary directories exist before proceeding
    cfg.ensure_directories()

    # Validate OpenAI API key before doing anything else using robust validation
    try:
        from utils_api_key import validate_openai_key
        if not validate_openai_key():
            sys.exit(1)
    except ImportError:
        # Fallback to old validation
        if not openai_client.validate_openai_key():
            sys.exit(1)

    parser = argparse.ArgumentParser(description="Run the NetLogo to LUCIM conversion agent.")
    parser.add_argument("--case", type=str, help="The NetLogo case study to process.")
    parser.add_argument("--persona_set", type=str, help="The persona set to use.")
    parser.add_argument("--model", type=str, help="The AI model to use.")
    parser.add_argument("--reasoning", type=str, choices=["minimal", "low", "medium", "high"], help="Reasoning effort.")
    parser.add_argument("--verbosity", type=str, choices=["low", "medium", "high"], help="Text verbosity.")
    parser.add_argument("--non-interactive", action="store_true", help="Run without interactive prompts.")

    args = parser.parse_args()

    run_name = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Selections will be populated either by args or interactive prompts
    selected_case = args.case
    selected_persona_set = args.persona_set
    selected_model = args.model
    selected_reasoning = args.reasoning
    selected_verbosity = args.verbosity

    # Interactive selections if not provided via args
    if not args.non_interactive:
        selected_case = selected_case or ui.select_netlogo_case()
        selected_persona_set = selected_persona_set or ui.select_persona_set()
        selected_model = selected_model or ui.select_model()
        selected_reasoning = selected_reasoning or ui.select_reasoning_effort()
        selected_verbosity = selected_verbosity or ui.select_text_verbosity()
    else:
        # Fallback to defaults for non-interactive mode if args are missing
        available_cases = fileio.get_netlogo_cases()
        selected_case = selected_case or (available_cases[0] if available_cases else "3d-solids")
        selected_persona_set = selected_persona_set or cfg.DEFAULT_PERSONA_SET
        selected_model = selected_model or "gpt-5-nano-2025-08-07"
        selected_reasoning = selected_reasoning or "medium"
        selected_verbosity = selected_verbosity or "medium"

    # Handle case where no case was selected
    if not selected_case:
        available_cases = fileio.get_netlogo_cases()
        if available_cases:
            selected_case = available_cases[0]
            print(f"No case selected, using default: {selected_case}")
        else:
            print("No NetLogo cases found. Please check the input directory.")
            sys.exit(1)

    # Setup logging after all parameters are determined
    logger = log.setup_run_logger(
        base_name=selected_case,
        model_name=selected_model,
        timestamp=run_name,
        reasoning_effort=selected_reasoning,
        text_verbosity=selected_verbosity,
        persona_set=selected_persona_set
    )

    logger.info(f"--- Starting Agent Run: {run_name} ---")
    logger.info(f"Selected Case: {selected_case}")
    logger.info(f"Selected Persona Set: {selected_persona_set}")
    logger.info(f"Selected Model: {selected_model}")
    logger.info(f"Selected Reasoning: {selected_reasoning}")
    logger.info(f"Selected Verbosity: {selected_verbosity}")

    # --- 1. Create Output Directory ---
    output_dir = fileio.create_run_output_directory(
        run_name, selected_case, selected_model, selected_persona_set,
        reasoning=selected_reasoning, verbosity=selected_verbosity
    )
    logger.info(f"Created output directory: {output_dir}")

    # --- 2. Load Input Files ---
    logger.info("Loading input files...")
    try:
        # Load NetLogo code
        netlogo_code_content = fileio.read_netlogo_case_content(selected_case)
        logger.info(f"Successfully loaded NetLogo case: {selected_case}")

        # Load all persona and DSL files
        persona_path = os.path.join(cfg.INPUT_PERSONA_DIR, selected_persona_set)
        all_persona_files = fileio.find_files(persona_path, ".md")

        input_contents = {
            "netlogo_code": netlogo_code_content
        }

        for file_path in all_persona_files:
            file_name = os.path.basename(file_path)
            content = fileio.read_file_content(file_path)
            input_contents[file_name] = content
            logger.info(f"Loaded input file: {file_name}")

        # Load NetLogo interface images as base64 strings
        encoded_images = fileio.load_and_encode_images(selected_case, logger)
        if encoded_images:
            input_contents["netlogo_images"] = encoded_images

        # Load task instructions from single-agent-task file
        task_instructions = None
        try:
            task_file_path = os.path.join(project_root, "input-task", "single-agent-task")
            if os.path.exists(task_file_path):
                task_instructions = fileio.read_file_content(task_file_path)
                logger.info("Successfully loaded task instructions from single-agent-task")
            else:
                logger.error("Mandatory TASK instructions file not found at input-task/single-agent-task")
        except Exception as e:
            logger.error(f"Failed to load task instructions: {e}")

    except Exception as e:
        logger.error(f"Failed to load input files: {e}", exc_info=True)
        sys.exit(1)

    # --- 2. Build the complete system prompt ---
    logger.info("Building the complete system prompt for the AI model...")
    if not task_instructions or not str(task_instructions).strip():
        logger.error("Mandatory TASK instructions are missing. Expected file at input-task/single-agent-task. Aborting.")
        sys.exit(2)

    # Build system prompt with an explicit, multi-agent-aligned order
    def _safe_read(path: str) -> str:
        try:
            return fileio.read_file_content(path) if path and os.path.exists(path) else ""
        except Exception:
            return ""

    def _load_step_task(step_index: int) -> str:
        """Load the per-stage task content from input-task/step-<n>-task as a single line.
        Returns an empty string if the file is missing or unreadable.
        """
        try:
            step_fname = f"step-{step_index}-task"
            step_path = os.path.join(project_root, "input-task", step_fname)
            if os.path.exists(step_path):
                content = fileio.read_file_content(step_path).strip()
                # Remove optional <TASK> wrappers if present
                content = re.sub(r"</?TASK>", "", content)
                # Normalize whitespace to keep it on a single line for compact prompts
                one_line = re.sub(r"\s+", " ", content).strip()
                return one_line
        except Exception:
            pass
        return ""

    def _load_step_2a_task() -> str:
        """Load the per-stage task content from input-task/step-2a-task as a single line.
        Returns an empty string if the file is missing or unreadable.
        """
        try:
            step_path = os.path.join(project_root, "input-task", "step-2a-task")
            if os.path.exists(step_path):
                content = fileio.read_file_content(step_path).strip()
                content = re.sub(r"</?TASK>", "", content)
                one_line = re.sub(r"\s+", " ", content).strip()
                return one_line
        except Exception:
            pass
        return ""

    def _inject_stage_tasks_into_task_instructions(text: str) -> str:
        """Insert a 'Task: <content>' line just before the '- Persona:' line for each stage (1..8).
        The insertion preserves indentation and does not modify existing lines.
        """
        if not text:
            return text

        updated = text
        for step_idx in range(1, 9):
            step_task = _load_step_task(step_idx)
            if not step_task:
                continue  # Skip insertion if no task file

            # Pattern: find the stage header line, then the first '- Persona:' line following it
            # Capture the indentation used by the Persona bullet to reuse for the Task line
            pattern = (
                rf"(\n\s*{step_idx}\)\s[^\n]*\n)(\s*-\s*Persona:)"
            )

            def _repl(match: re.Match) -> str:
                header = match.group(1)
                persona_marker = match.group(2)
                indent_match = re.match(r"(\s*)-\s*Persona:", persona_marker)
                indent = indent_match.group(1) if indent_match else "   "
                task_line = f"{indent}- Task: {step_task}\n"
                return f"{header}{task_line}{persona_marker}"

            # Only replace the first occurrence for each stage to avoid multiple insertions
            updated = re.sub(pattern, _repl, updated, count=1, flags=re.MULTILINE)

        return updated

    # Resolve canonical persona/DSL paths
    persona_paths = cfg.get_persona_file_paths(selected_persona_set)

    ordered_blocks = []

    # 1) TASK (mandatory) with dynamic per-stage Task injections
    injected_task_instructions = _inject_stage_tasks_into_task_instructions(str(task_instructions))
    ordered_blocks.append(injected_task_instructions.strip())

    # 2) Stage 1 — Syntax Parser
    #    Persona → IL-SYN Description → IL-SYN Mapping → Case/Code/Images
    ordered_blocks.append(_safe_read(str(persona_paths.get("netlogo_abstract_syntax_extractor"))))
    ordered_blocks.append(_safe_read(str(persona_paths.get("dsl_il_syn_description"))))
    ordered_blocks.append(_safe_read(str(persona_paths.get("dsl_il_syn_mapping"))))

    #    Inputs for stage 1
    ordered_blocks.append(f"<CASE-STUDY-NAME>\n{selected_case}\n</CASE-STUDY-NAME>")
    ordered_blocks.append(f"<NETLOGO-SOURCE-CODE>\n```text\n{netlogo_code_content}\n```\n</NETLOGO-SOURCE-CODE>")
    if "netlogo_images" in input_contents and input_contents["netlogo_images"]:
        ordered_blocks.append(
            f"<NETLOGO-INTERFACE-IMAGES>\ncount={len(input_contents['netlogo_images'])}\n</NETLOGO-INTERFACE-IMAGES>"
        )

    # 2a) Interface Image Analyzer — add persona 2a and task step-2a
    persona_2a_path = os.path.join(cfg.INPUT_PERSONA_DIR, selected_persona_set, "PSN_2a_NetlogoInterfaceImageAnalyzer.md")
    persona_2a_text = _safe_read(persona_2a_path)
    step_2a_task = _load_step_2a_task()
    if persona_2a_text or step_2a_task:
        stage_2a_blocks = []
        # Stage header for clarity in the prompt
        stage_2a_blocks.append("2a) NetLogo Interface Image Analyzer")
        if step_2a_task:
            stage_2a_blocks.append(f"- Task: {step_2a_task}")
        if persona_2a_text:
            stage_2a_blocks.append(persona_2a_text)
        ordered_blocks.append("\n".join(stage_2a_blocks))

    # 3) Stage 2 — Semantics Parser
    #    Persona → IL-SEM Description → IL-SEM Mapping
    # Prefer PSN_2b if present; otherwise fallback to existing mapping
    persona_2b_path = os.path.join(cfg.INPUT_PERSONA_DIR, selected_persona_set, "PSN_2b_NetlogoBehaviorExtractor.md")
    persona_2b_text = _safe_read(persona_2b_path)
    if persona_2b_text:
        ordered_blocks.append(persona_2b_text)
    else:
        ordered_blocks.append(_safe_read(str(persona_paths.get("behavior_extractor"))))
    ordered_blocks.append(_safe_read(str(persona_paths.get("dsl_il_sem_description"))))
    ordered_blocks.append(_safe_read(str(persona_paths.get("dsl_il_sem_mapping"))))

    # 4) Stage 3 — LUCIM Environment Synthesizer
    #    Persona → LUCIM DSL (rules)
    ordered_blocks.append(_safe_read(str(persona_paths.get("lucim_environment_synthesizer"))))
    ordered_blocks.append(_safe_read(str(persona_paths.get("lucim_rules"))))

    # 5) Stage 4 — LUCIM Scenario Synthesizer (Persona)
    ordered_blocks.append(_safe_read(str(persona_paths.get("lucim_scenario_synthesizer"))))

    # 6) Stage 5 — PlantUML Writer (Persona)
    ordered_blocks.append(_safe_read(str(persona_paths.get("plantuml_writer"))))

    # 7) Stage 6 — PlantUML Auditor (Persona)
    ordered_blocks.append(_safe_read(str(persona_paths.get("plantuml_auditor"))))

    # 8) Stage 7 — PlantUML Corrector (Persona)
    ordered_blocks.append(_safe_read(str(persona_paths.get("plantuml_corrector"))))

    # Note: Stage 8 reuses the auditor; we do not duplicate content.

    # Create single system_prompt variable for both API call and file generation
    system_prompt = "\n\n".join([b for b in ordered_blocks if b and str(b).strip()])

    # Write input-instructions.md BEFORE API call for debugging
    fileio.write_input_instructions_before_api(output_dir, system_prompt)

    # --- 3. Call the AI model ---
    import time
    run_start = time.time()
    logger.info(f"Sending request to AI model: {selected_model}...")
    try:
        client = openai_client.OpenAI()

        # Define API configuration for the Responses API
        api_config = {
            "model": selected_model,
            "instructions": system_prompt,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": system_prompt}]}],
        }

        # Call the API and wait for the response
        response = openai_client.create_and_wait(client, api_config)

        # Log token usage
        usage = openai_client.get_usage_tokens(response)
        logger.info(
            f"API call successful. Token usage: "
            f"Input: {usage['input_tokens']}, Output: {usage['output_tokens']}, Total: {usage['total_tokens']}"
        )

    except Exception as e:
        logger.error(f"API call failed: {e}", exc_info=True)
        sys.exit(1)

    # --- 4. Process and save the output artifacts ---
    logger.info("Processing and saving output artifacts...")
    try:
        # Save the raw API response
        raw_response_dict = response.to_dict()
        fileio.write_json(os.path.join(output_dir, "raw_response.json"), raw_response_dict)

        # Extract PlantUML and audit from raw_response.json
        logger.info("Extracting PlantUML diagram and audit report from response...")
        plantuml_text = fileio.extract_plantuml_from_response(raw_response_dict, output_dir, logger)
        audit_data = fileio.extract_audit_from_response(raw_response_dict, output_dir, logger)
        
        # Save extracted artifacts
        fileio.save_extracted_artifacts(output_dir, plantuml_text, audit_data, logger)

        # Extract and save the main text content
        output_text = openai_client.get_output_text(response)
        if output_text:
            fileio.write_file_content(os.path.join(output_dir, "output_full_text.md"), output_text)
            logger.info("Saved full text output.")

            # Parse and save individual artifacts
            parse_and_save_artifacts(output_text, output_dir, logger)
        else:
            logger.warning("No text output found in the API response.")

    except Exception as e:
        logger.error(f"Failed to process or save outputs: {e}", exc_info=True)
        sys.exit(1)

    # --- 5. Build and print OVERALL SUMMARY ---
    from utils_run_logging import OrchestratorLogger
    run_end = time.time()
    # Detect artifacts that we created in this run directory
    try:
        artifacts = []
        for fname in os.listdir(output_dir):
            if fname.endswith((".json", ".md", ".puml")):
                artifacts.append(fname)
        artifacts.sort()
    except Exception:
        artifacts = []

    ol = OrchestratorLogger(logger)
    summary_text = ol.build_overall_summary(
        run_name=run_name,
        base_name=selected_case,
        model_name=selected_model,
        persona_set=selected_persona_set,
        reasoning_effort=selected_reasoning,
        text_verbosity=selected_verbosity,
        start_time_seconds=run_start,
        end_time_seconds=run_end,
        tokens=usage,
        output_dir=output_dir,
        artifacts=artifacts,
    )
    # Print to console and persist alongside artifacts
    print(summary_text)
    try:
        ol.persist_overall_summary(output_dir, summary_text)
    except Exception as e:
        logger.warning(f"Could not persist overall summary: {e}")

    logger.info(f"--- Agent Run Finished: {run_name} ---")

if __name__ == "__main__":
    main()
