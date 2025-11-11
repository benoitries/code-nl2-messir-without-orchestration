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

    # Validate API key based on selected model before doing anything else
    # Note: selected_model is determined later, so we'll validate after model selection
    # But we keep the structure here for backward compatibility
    api_key_validated = False

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
    logger.info(f"=== SINGLE-CALL MODE: v3 ADK Compatible ===")
    logger.info(f"Selected Case: {selected_case}")
    logger.info(f"Selected Persona Set: {selected_persona_set}")
    logger.info(f"Selected Model: {selected_model}")
    logger.info(f"Selected Reasoning: {selected_reasoning}")
    logger.info(f"Selected Verbosity: {selected_verbosity}")

    # Check API key presence for the selected model (no validation)
    try:
        from utils_api_key import get_provider_for_model, get_api_key_for_model
        provider = get_provider_for_model(selected_model)
        logger.info(f"Detected provider: {provider} for model: {selected_model}")
        _ = get_api_key_for_model(selected_model)
        logger.info(f"✓ API key found for provider: {provider}")
    except Exception as e:
        logger.error(f"Missing API key for selected model/provider: {e}", exc_info=True)
        sys.exit(1)

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
    # SINGLE-CALL MODE: Build v3 ADK-compatible composite prompt
    logger.info("Building v3 ADK-compatible composite prompt for single-call mode...")
    logger.info("=== SINGLE-CALL MODE ENABLED ===")
    
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

    # Build v3 ADK-compatible composite prompt for single-call mode
    def _build_v3_adk_composite_prompt():
        """Build a composite prompt that requests all 3 stages in a single LLM call."""
        ordered_blocks = []
        
        # Load v3 ADK personas and rules
        persona_dir = cfg.INPUT_PERSONA_DIR / selected_persona_set
        
        # Stage 1: LUCIM Operation Model Generator
        persona_op_model = _safe_read(str(persona_dir / "PSN_LUCIM_Operation_Model_Generator.md"))
        if persona_op_model:
            ordered_blocks.append("=== STAGE 1: LUCIM OPERATION MODEL GENERATION ===")
            ordered_blocks.append(persona_op_model)
        
        # Load NetLogo to LUCIM mapping
        mapping_file = persona_dir / "RULES_MAPPING_NETLOGO_TO_OPERATION_MODEL.md"
        netlogo_mapping = _safe_read(str(mapping_file))
        if netlogo_mapping:
            ordered_blocks.append(f"<NETLOGO-TO-LUCIM-MAPPING>\n{netlogo_mapping}\n</NETLOGO-TO-LUCIM-MAPPING>")
        
        # Load LUCIM Operation Model rules
        rules_op_model = _safe_read(str(persona_dir / "RULES_LUCIM_Operation_model.md"))
        if rules_op_model:
            ordered_blocks.append(f"<LUCIM-OPERATION-MODEL-RULES>\n{rules_op_model}\n</LUCIM-OPERATION-MODEL-RULES>")
        
        # Stage 2: LUCIM Scenario Generator
        persona_scenario = _safe_read(str(persona_dir / "PSN_LUCIM_Scenario_Generator.md"))
        if persona_scenario:
            ordered_blocks.append("\n=== STAGE 2: LUCIM SCENARIO GENERATION ===")
            ordered_blocks.append(persona_scenario)
        
        # Load Scenario rules
        rules_scenario = _safe_read(str(persona_dir / "RULES_LUCIM_Scenario.md"))
        if rules_scenario:
            ordered_blocks.append(f"<LUCIM-SCENARIO-RULES>\n{rules_scenario}\n</LUCIM-SCENARIO-RULES>")
        
        # Stage 3: LUCIM PlantUML Diagram Generator
        persona_plantuml = _safe_read(str(persona_dir / "PSN_LUCIM_PlantUML_Diagram_Generator.md"))
        if persona_plantuml:
            ordered_blocks.append("\n=== STAGE 3: LUCIM PLANTUML DIAGRAM GENERATION ===")
            ordered_blocks.append(persona_plantuml)
        
        # Load PlantUML Diagram rules
        rules_plantuml = _safe_read(str(persona_dir / "RULES_LUCIM_PlantUML_Diagram.md"))
        if rules_plantuml:
            ordered_blocks.append(f"<LUCIM-PLANTUML-DIAGRAM-RULES>\n{rules_plantuml}\n</LUCIM-PLANTUML-DIAGRAM-RULES>")
        
        # Add NetLogo source code
        ordered_blocks.append(f"\n<NETLOGO-SOURCE-CODE>\n{netlogo_code_content}\n</NETLOGO-SOURCE-CODE>")
        if "netlogo_images" in input_contents and input_contents["netlogo_images"]:
            ordered_blocks.append(
                f"<NETLOGO-INTERFACE-IMAGES>\ncount={len(input_contents['netlogo_images'])}\n</NETLOGO-INTERFACE-IMAGES>"
            )
        
        # Add output format instructions for structured response
        output_format = """
=== OUTPUT FORMAT REQUIREMENTS ===

You must produce a single JSON response with the following structure:

{
  "operation_model": {
    "data": <LUCIM Operation Model JSON object>,
    "errors": []
  },
  "scenario": {
    "data": {
      "scenario": {
        "name": "<scenario name>",
        "description": "<scenario description>",
        "messages": [<array of scenario messages>]
      }
    },
    "errors": []
  },
  "plantuml_diagram": {
    "data": {
      "plantuml-diagram": "<PlantUML diagram text between @startuml and @enduml>"
    },
    "errors": []
  }
}

CRITICAL: 
- The operation_model.data must be a valid JSON object (no Markdown fences, no text outside JSON)
- The scenario.data must follow the LUCIM Scenario JSON format
- The plantuml_diagram.data["plantuml-diagram"] must contain the complete PlantUML diagram text (including @startuml and @enduml markers, no Markdown fences)
- All three stages must be completed in this single response
"""
        ordered_blocks.append(output_format)
        
        return "\n\n".join([b for b in ordered_blocks if b and str(b).strip()])
    
    # Build the composite prompt
    system_prompt = _build_v3_adk_composite_prompt()

    # Write input-instructions.md BEFORE API call for debugging
    fileio.write_input_instructions_before_api(output_dir, system_prompt)

    # --- 3. Call the AI model ---
    import time
    run_start = time.time()
    logger.info(f"Sending request to AI model: {selected_model}...")
    try:
        from utils_api_key import get_provider_for_model, create_openai_client, get_gemini_api_key
        from utils_openai_client import get_openai_client
        
        provider = get_provider_for_model(selected_model)
        
        # Detect specific model families for better error messages
        model_lower = selected_model.lower()
        is_mistral = "mistral" in model_lower
        is_llama = "llama" in model_lower
        
        if provider == "gemini":
            # For Gemini models, we need to use Google's API
            # Note: The single agent currently only supports OpenAI Responses API
            # This is a limitation that should be addressed in a future update
            logger.error(
                f"Gemini models are not yet fully supported in the single agent. "
                f"Please use the orchestrator with ADK (orchestrator_persona_v3_adk.py) "
                f"for Gemini model support, or use an OpenAI model instead."
            )
            raise ValueError(
                f"Gemini provider detected but single agent only supports OpenAI Responses API. "
                f"Model: {selected_model}, Provider: {provider}"
            )
        elif provider == "router":
            # For OpenRouter models (Mistral, Llama, etc.), we need to use OpenRouter API
            model_type = ""
            if is_mistral:
                model_type = "Mistral"
            elif is_llama:
                model_type = "Llama"
            else:
                model_type = "OpenRouter"
            
            logger.error(
                f"{model_type} models (via OpenRouter) are not yet fully supported in the single agent. "
                f"Please use the orchestrator with ADK (orchestrator_persona_v3_adk.py) "
                f"for {model_type} model support, or use an OpenAI model instead."
            )
            raise ValueError(
                f"OpenRouter provider detected ({model_type} model) but single agent only supports OpenAI Responses API. "
                f"Model: {selected_model}, Provider: {provider}"
            )
        else:
            # OpenAI provider - use standard OpenAI client
            client = get_openai_client()

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
            f"Single-call API completed successfully. Token usage: "
            f"Input: {usage['input_tokens']}, Output: {usage['output_tokens']}, Total: {usage['total_tokens']}"
        )
        logger.info(f"Single-call mode: Exactly 1 LLM call performed for all 3 stages")

    except Exception as e:
        logger.error(f"API call failed: {e}", exc_info=True)
        sys.exit(1)

    # --- 4. Process and save the output artifacts (SINGLE-CALL MODE) ---
    logger.info("Processing single-call response and extracting 3-stage artifacts...")
    try:
        import json
        from pathlib import Path
        
        # Save the raw API response
        raw_response_dict = response.to_dict()
        fileio.write_json(os.path.join(output_dir, "raw_response.json"), raw_response_dict)
        
        # Extract and save the main text content
        output_text = openai_client.get_output_text(response)
        if output_text:
            fileio.write_file_content(os.path.join(output_dir, "output_full_text.md"), output_text)
            logger.info("Saved full text output.")
        
        # Parse the structured JSON response to extract 3 artifacts
        def _parse_single_call_response(response_text: str) -> dict:
            """Parse the single-call response to extract operation model, scenario, and PlantUML."""
            artifacts = {
                "operation_model": None,
                "scenario": None,
                "plantuml_diagram": None
            }
            
            if not response_text or not isinstance(response_text, str):
                logger.error("Response text is empty or invalid")
                return artifacts
            
            try:
                # Try to parse as JSON first
                # Look for JSON block in the response (handle markdown code fences)
                json_text = response_text
                
                # Remove markdown code fences if present
                if "```json" in json_text:
                    start = json_text.find("```json") + 7
                    end = json_text.find("```", start)
                    if end > start:
                        json_text = json_text[start:end].strip()
                elif "```" in json_text:
                    start = json_text.find("```") + 3
                    end = json_text.find("```", start)
                    if end > start:
                        json_text = json_text[start:end].strip()
                
                # Find JSON boundaries
                json_start = json_text.find("{")
                json_end = json_text.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_content = json_text[json_start:json_end]
                    parsed = json.loads(json_content)
                    
                    # Schema validation: check for required top-level keys
                    required_keys = ["operation_model", "scenario", "plantuml_diagram"]
                    missing_keys = [k for k in required_keys if k not in parsed]
                    if missing_keys:
                        logger.warning(f"Missing required keys in response: {missing_keys}")
                    
                    # Extract operation model with schema guard
                    if "operation_model" in parsed:
                        op_model = parsed["operation_model"]
                        if isinstance(op_model, dict) and "data" in op_model:
                            artifacts["operation_model"] = op_model
                        else:
                            logger.warning("operation_model missing 'data' key or invalid structure")
                    
                    # Extract scenario with schema guard
                    if "scenario" in parsed:
                        scenario = parsed["scenario"]
                        if isinstance(scenario, dict) and "data" in scenario:
                            artifacts["scenario"] = scenario
                        else:
                            logger.warning("scenario missing 'data' key or invalid structure")
                    
                    # Extract PlantUML diagram with schema guard
                    if "plantuml_diagram" in parsed:
                        puml = parsed["plantuml_diagram"]
                        if isinstance(puml, dict) and "data" in puml:
                            puml_data = puml["data"]
                            if isinstance(puml_data, dict) and "plantuml-diagram" in puml_data:
                                artifacts["plantuml_diagram"] = puml
                            else:
                                logger.warning("plantuml_diagram.data missing 'plantuml-diagram' key")
                        else:
                            logger.warning("plantuml_diagram missing 'data' key or invalid structure")
                    
                    logger.info("Successfully parsed structured JSON response with schema validation.")
                    return artifacts
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse structured JSON response: {e}")
            
            # Fallback: try to extract from text patterns
            logger.info("Attempting fallback extraction from text patterns...")
            
            # Try to extract PlantUML (look for @startuml...@enduml)
            plantuml_start = response_text.find("@startuml")
            plantuml_end = response_text.find("@enduml")
            if plantuml_start >= 0 and plantuml_end > plantuml_start:
                plantuml_text = response_text[plantuml_start:plantuml_end + len("@enduml")]
                artifacts["plantuml_diagram"] = {
                    "data": {"plantuml-diagram": plantuml_text},
                    "errors": []
                }
                logger.info("Extracted PlantUML diagram from text patterns.")
            
            return artifacts
        
        # Parse the response
        parsed_artifacts = _parse_single_call_response(output_text if output_text else "")
        
        # Create stage directories (matching v3 ADK structure)
        stage1_dir = os.path.join(output_dir, "1_lucim_operation_model", "iter-1", "1-generator")
        stage2_dir = os.path.join(output_dir, "2_lucim_scenario", "iter-1", "1-generator")
        stage3_dir = os.path.join(output_dir, "3_lucim_plantuml_diagram", "iter-1", "1-generator")
        
        os.makedirs(stage1_dir, exist_ok=True)
        os.makedirs(stage2_dir, exist_ok=True)
        os.makedirs(stage3_dir, exist_ok=True)
        
        # Save Stage 1: Operation Model
        if parsed_artifacts["operation_model"]:
            op_model_data = parsed_artifacts["operation_model"].get("data")
            if op_model_data:
                # Save as JSON (raw text content)
                if isinstance(op_model_data, dict):
                    op_model_text = json.dumps(op_model_data, indent=2, ensure_ascii=False)
                else:
                    op_model_text = str(op_model_data)
                fileio.write_file_content(os.path.join(stage1_dir, "output-data.json"), op_model_text)
                logger.info("Saved operation model to Stage 1 directory.")
        
        # Save Stage 2: Scenario
        if parsed_artifacts["scenario"]:
            scenario_data = parsed_artifacts["scenario"].get("data")
            if scenario_data:
                # Save as JSON (raw text content)
                if isinstance(scenario_data, dict):
                    scenario_text = json.dumps(scenario_data, indent=2, ensure_ascii=False)
                else:
                    scenario_text = str(scenario_data)
                fileio.write_file_content(os.path.join(stage2_dir, "output-data.json"), scenario_text)
                logger.info("Saved scenario to Stage 2 directory.")
        
        # Save Stage 3: PlantUML Diagram
        if parsed_artifacts["plantuml_diagram"]:
            puml_data = parsed_artifacts["plantuml_diagram"].get("data", {})
            if isinstance(puml_data, dict) and "plantuml-diagram" in puml_data:
                puml_text = puml_data["plantuml-diagram"]
                # Save as .puml file
                fileio.write_file_content(os.path.join(stage3_dir, "diagram.puml"), puml_text)
                # Also save as output-data.json (raw text)
                fileio.write_file_content(os.path.join(stage3_dir, "output-data.json"), puml_text)
                logger.info("Saved PlantUML diagram to Stage 3 directory.")
        
        # --- 5. Run deterministic audits (no LLM calls) ---
        logger.info("Running deterministic audits on extracted artifacts...")
        try:
            # Import deterministic auditors
            from utils_audit_operation_model import audit_operation_model
            from utils_audit_scenario import audit_scenario
            from utils_audit_diagram import audit_diagram
            
            # Audit Stage 1: Operation Model
            if parsed_artifacts["operation_model"]:
                op_model_data = parsed_artifacts["operation_model"].get("data")
                if op_model_data and isinstance(op_model_data, dict):
                    op_model_raw = json.dumps(op_model_data, indent=2, ensure_ascii=False)
                    audit_result = audit_operation_model(op_model_data, op_model_raw)
                    
                    # Save audit result
                    audit_dir = os.path.join(output_dir, "1_lucim_operation_model", "iter-1", "2-auditor")
                    os.makedirs(audit_dir, exist_ok=True)
                    
                    # Format audit result as output-data.json (plain text)
                    audit_text = json.dumps({
                        "verdict": "compliant" if audit_result.get("verdict") else "non-compliant",
                        "non-compliant-rules": [v.get("id") for v in audit_result.get("violations", [])],
                        "violations": audit_result.get("violations", [])
                    }, indent=2, ensure_ascii=False)
                    fileio.write_file_content(os.path.join(audit_dir, "output-data.json"), audit_text)
                    logger.info(f"Operation Model audit: {'COMPLIANT' if audit_result.get('verdict') else 'NON-COMPLIANT'}")
            
            # Audit Stage 2: Scenario
            if parsed_artifacts["scenario"]:
                scenario_data = parsed_artifacts["scenario"].get("data")
                if scenario_data:
                    scenario_raw = json.dumps(scenario_data, indent=2, ensure_ascii=False) if isinstance(scenario_data, dict) else str(scenario_data)
                    # Pass operation model for scenario audit if available
                    op_model_for_audit = parsed_artifacts["operation_model"].get("data") if parsed_artifacts["operation_model"] else None
                    audit_result = audit_scenario(scenario_data, scenario_raw, operation_model=op_model_for_audit)
                    
                    # Save audit result
                    audit_dir = os.path.join(output_dir, "2_lucim_scenario", "iter-1", "2-auditor")
                    os.makedirs(audit_dir, exist_ok=True)
                    
                    audit_text = json.dumps({
                        "verdict": "compliant" if audit_result.get("verdict") else "non-compliant",
                        "non-compliant-rules": [v.get("id") for v in audit_result.get("violations", [])],
                        "violations": audit_result.get("violations", [])
                    }, indent=2, ensure_ascii=False)
                    fileio.write_file_content(os.path.join(audit_dir, "output-data.json"), audit_text)
                    logger.info(f"Scenario audit: {'COMPLIANT' if audit_result.get('verdict') else 'NON-COMPLIANT'}")
            
            # Audit Stage 3: PlantUML Diagram
            if parsed_artifacts["plantuml_diagram"]:
                puml_data = parsed_artifacts["plantuml_diagram"].get("data", {})
                if isinstance(puml_data, dict) and "plantuml-diagram" in puml_data:
                    puml_text = puml_data["plantuml-diagram"]
                    puml_raw = puml_text
                    
                    # Pass operation model and scenario for diagram audit
                    op_model_for_audit = parsed_artifacts["operation_model"].get("data") if parsed_artifacts["operation_model"] else None
                    scenario_for_audit = parsed_artifacts["scenario"].get("data") if parsed_artifacts["scenario"] else None
                    
                    audit_result = audit_diagram(
                        puml_text,
                        puml_raw,
                        svg_path=None,  # No SVG validation in single-call mode
                        operation_model=op_model_for_audit,
                        scenario=scenario_for_audit
                    )
                    
                    # Save audit result
                    audit_dir = os.path.join(output_dir, "3_lucim_plantuml_diagram", "iter-1", "2-auditor")
                    os.makedirs(audit_dir, exist_ok=True)
                    
                    # Format matches orchestrator format
                    audit_data = audit_result.get("data", {})
                    audit_text = json.dumps(audit_data, indent=2, ensure_ascii=False)
                    fileio.write_file_content(os.path.join(audit_dir, "output-data.json"), audit_text)
                    logger.info(f"PlantUML Diagram audit: {audit_data.get('verdict', 'unknown').upper()}")
        
        except Exception as audit_error:
            logger.error(f"Error during deterministic audits: {audit_error}", exc_info=True)
            # Continue execution even if audits fail

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

    logger.info(f"--- Agent Run Finished: {run_name} (Single-Call Mode) ---")

if __name__ == "__main__":
    main()
