#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Default run script for the single-agent NetLogo to LUCIM conversion.
Launches the agent in non-interactive mode with default parameters.
"""

import os
import subprocess
import sys

def main():
    """Sets up the environment and runs the agent with default settings."""
    
    # Ensure the script is run from the project root's context
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    agent_script = os.path.join(project_root, "agent_netlogo_to_lucim.py")
    
    if not os.path.exists(agent_script):
        print(f"Error: Agent script not found at {agent_script}")
        sys.exit(1)
        
    # Check for OpenAI API key
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it before running: export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)

    # Check if task file exists (fail-fast policy)
    task_file_path = os.path.join(project_root, "input-task", "single-agent-task")
    if not os.path.exists(task_file_path):
        print(f"Error: Mandatory task instructions file not found: {task_file_path}")
        print("Please create it under experimentation/input/input-task/ and ensure symlinks are in place.")
        sys.exit(2)
    else:
        print(f"Found task instructions file: {task_file_path}")

    print("--- Starting Default Agent Run ---")
    
    # Run the agent with default non-interactive settings
    # It will use the first available case, default persona set, and first available model.
    command = [
        sys.executable,
        agent_script,
        "--non-interactive",
        # Optional: Specify defaults explicitly if needed
        # "--case", "3d-solids",
        # "--model", "gpt-4o-mini",
    ]
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
        
        # Stream output in real-time
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        
        if process.returncode != 0:
            print(f"\n--- Agent run failed with exit code {process.returncode} ---")
        else:
            print("\n--- Agent run completed successfully ---")
            
    except Exception as e:
        print(f"\nAn error occurred while running the agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
