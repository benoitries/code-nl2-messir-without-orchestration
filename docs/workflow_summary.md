# Single-Agent Workflow Summary

This document summarizes the workflow of the single `agent_netlogo_to_lucim` agent.

---

## Pipeline Overview
- **Agent**: `agent_netlogo_to_lucim.py`
- **Process**: A single, end-to-end execution that takes NetLogo source files and produces a LUCIM-compliant PlantUML diagram.
- **Output root**: `code-nl2-messir-without-orchestration/output/runs/<YYYY-MM-DD>/<HHMM>-<PERSONA-SET>/<case>-<model>/`
- **Artifacts**: The agent generates all intermediate and final artifacts in a single run, including AST, state machine, scenarios, diagrams, and audit reports.

---

## Agent I/O

### `agent_netlogo_to_lucim`

-   **Inputs**:
    -   NetLogo code file (`.md`).
    -   NetLogo interface screenshots (`.png`).
    -   All persona files from `input-persona/<PERSONA-SET>/`.
    -   All DSL files (`DSL_IL_SYN`, `DSL_IL_SEM`) from `input-persona/<PERSONA-SET>/`.
    -   The full LUCIM compliance rules document (`DSL_Target_LUCIM-full-definition-for-compliance.md`).
    -   Reference documents: removed (no iCrash PDFs).
    -   Configuration for the AI model, reasoning, and verbosity.

-   **Instructions Source (no fallbacks):**
    -   The agent composes its system prompt exclusively from centralized inputs (task file + persona/DSL files). The mandatory task file is `input-task/single-agent-task`.
    -   If the task file is missing or empty, the run fails fast with an explicit error. No embedded default prompt is used.

-   **Outputs**:
    -   `output-response.json`: The raw structured response from the AI model.
    -   `output-reasoning.md`: The chain-of-thought reasoning from the agent.
    -   `output-data.json`: Contains structured data for various stages (e.g., AST, scenarios, audit results).
    -   `diagram.puml`: The final, LUCIM-compliant PlantUML diagram.
    -   `corrected_diagram.puml`: The corrected diagram, if an audit-correction loop was necessary.
    -   `audit_report.json`: The final compliance verdict and list of any non-compliant rules.

---

## Notes
- The agent encapsulates the logic of the previous 8-stage pipeline.
- It is responsible for internally managing the flow of data between logical steps (parsing, mapping, generating, auditing, correcting).
- The complexity of passing data between different scripts is eliminated.
