#!/usr/bin/env python3
"""
Orchestrator UI Utilities
Terminal UI interaction and user prompts for the NetLogo orchestrator.
"""

from typing import List
import os
from utils_config_constants import AVAILABLE_MODELS, DEFAULT_MODEL, INPUT_PERSONA_DIR
import utils_fileio as fileio

def select_netlogo_case() -> str:
    """Handle NetLogo case selection UI."""
    base_names = fileio.get_netlogo_cases()
    if not base_names:
        return ""

    print("\nAvailable NetLogo Models:")
    print("="*40)
    for i, base_name in enumerate(base_names, 1):
        print(f"{i:2d}. {base_name}")
    
    print("\nEnter the number of the NetLogo model to process (or 'q' to quit):")
    
    while True:
        try:
            user_input = input("NetLogo Model > ").strip()
            
            if user_input.lower() == 'q':
                print("Exiting...")
                return ""
            
            number = int(user_input)
            if 1 <= number <= len(base_names):
                return base_names[number - 1]
            else:
                print(f"Error: Invalid number. Available options: 1-{len(base_names)}")
        except ValueError:
            print("Error: Please enter a valid number or 'q' to quit:")

def select_model() -> str:
    """Handle model selection UI."""
    print("\nAI Model Selection")
    print("="*50)
    print("Available AI Models:")
    for i, model in enumerate(AVAILABLE_MODELS, 1):
        print(f"{i}. {model}")
    
    print(f"\nEnter the number of the AI model to use (press Enter for default: {DEFAULT_MODEL}):")
    
    while True:
        try:
            model_input = input("Model > ").strip()
            
            if model_input == "":
                return DEFAULT_MODEL
            
            model_number = int(model_input)
            if 1 <= model_number <= len(AVAILABLE_MODELS):
                return AVAILABLE_MODELS[model_number - 1]
            else:
                print(f"Error: Invalid number. Options: 1-{len(AVAILABLE_MODELS)}")
        except ValueError:
            print("Error: Please enter a valid number or press Enter.")

def select_reasoning_effort() -> str:
    """Handle reasoning effort selection UI."""
    options = ["minimal", "low", "medium", "high"]
    print("\nReasoning Effort Selection")
    print("="*50)
    for i, effort in enumerate(options, 1):
        print(f"{i}. {effort.title()}")
    print("Enter choice (press Enter for default 'medium'):")
    
    while True:
        user_input = input("Reasoning effort > ").strip()
        if user_input == "":
            return "medium"
        try:
            choice = int(user_input)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"Error: Invalid choice. Options: 1-{len(options)}")
        except ValueError:
            print("Error: Please enter a valid number.")

def select_text_verbosity() -> str:
    """Handle text verbosity selection UI."""
    options = ["low", "medium", "high"]
    print("\nText Verbosity Selection")
    print("="*50)
    for i, verbosity in enumerate(options, 1):
        print(f"{i}. {verbosity.title()}")
    print("Enter choice (press Enter for default 'medium'):")

    while True:
        user_input = input("Text verbosity > ").strip()
        if user_input == "":
            return "medium"
        try:
            choice = int(user_input)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"Error: Invalid choice. Options: 1-{len(options)}")
        except ValueError:
            print("Error: Please enter a valid number.")

def _get_available_persona_sets() -> List[str]:
    if not INPUT_PERSONA_DIR.exists():
        return []
    
    persona_sets = []
    for item in INPUT_PERSONA_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            persona_sets.append(item.name)
    
    return sorted(persona_sets)

def select_persona_set() -> str:
    """Interactive selection of persona set."""
    available_persona_sets = _get_available_persona_sets()
    
    if not available_persona_sets:
        print("No persona sets found.")
        return "persona-v2-after-ng-meeting"

    print("\nAvailable Persona Sets:")
    print("=" * 50)
    for i, persona_set in enumerate(available_persona_sets, 1):
        print(f"  {i}. {persona_set}")
    
    # Prefer persona-v2-after-ng-meeting as default if available, otherwise fallback to persona-v1
    default_persona = "persona-v2-after-ng-meeting" if "persona-v2-after-ng-meeting" in available_persona_sets else "persona-v1"
    print(f"Default: {default_persona} (press Enter to use default)")
    
    while True:
        try:
            choice = input(f"Select persona set > ").strip()
            
            if not choice:
                return default_persona
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(available_persona_sets):
                return available_persona_sets[choice_num - 1]
            else:
                print(f"Please enter a number between 1 and {len(available_persona_sets)}")
        except ValueError:
            print("Please enter a valid number or press Enter.")
