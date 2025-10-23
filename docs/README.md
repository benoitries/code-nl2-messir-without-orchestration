# NetLogo to LUCIM Single-Agent Conversion System

A streamlined AI system that automatically converts NetLogo agent-based models into LUCIM-compliant PlantUML diagrams using a single, powerful AI agent.

## 🚀 Overview

This project implements a single-step pipeline that transforms NetLogo simulation models into standardized  PlantUML diagrams. The system uses one AI agent to handle the entire workflow, from parsing the NetLogo code to generating a LUCIM-compliant, audited, and corrected diagram.

### Key Features

- **Single-Agent Architecture**: A single, consolidated AI agent handles the entire conversion process.
- **Automated End-to-End Conversion**: From NetLogo code to a final, compliant PlantUML diagram.
- **LUCIM Compliance**: Ensures generated diagrams follow LUCIM-UCI standards through built-in auditing and correction loops.
- **Multiple AI Model Support**: Compatible with various large language models.
- **Simplified Workflow**: Removes the complexity of a multi-agent orchestration pipeline.

### Workflow Summary

For a concise overview of the agent's workflow, see:

- `docs/orchestrator_workflow_summary.md` (renamed to `docs/workflow_summary.md` for clarity)

## 🏗️ Architecture

### The Single-Agent Pipeline

The agent performs the following logical steps internally:
1.  **Code and Image Parsing**: Extracts and structures NetLogo code components and analyzes UI screenshots.
2.  **Semantic Analysis**: Analyzes behavioral patterns and agent interactions.
3.  **LUCIM Mapping**: Maps NetLogo concepts to LUCIM entities and relationships.
4.  **Scenario Generation**: Generates LUCIM scenario descriptions.
5.  **PlantUML Generation**: Creates PlantUML diagram code from the scenarios.
6.  **Compliance Auditing**: Validates the diagram against LUCIM/UCI rules.
7.  **Correction Loop**: If non-compliant, fixes the diagram and re-audits until compliance is achieved or a limit is reached.
8.  **Final Output**: Produces the final, compliant PlantUML diagram and an audit report.

## 📁 Project Structure

```
code-nl2-messir-without-orchestration/
├── agent_netlogo_to_lucim.py              # Main conversion agent
├── utils_*.py                             # Utility functions
├── scripts/                               # Helper scripts for running the agent
├── requirements.txt                       # Python dependencies
├── input-netlogo/                         # NetLogo case studies
├── input-persona/                         # AI agent personas and rules
├── input-icrash/                          # Reference materials
├── input-images/                          # Supporting images
└── output/                                # Generated results
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- An API key for a compatible large language model provider (e.g., OpenAI)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd code-nl2-messir-without-orchestration
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API keys:**
    Set your API key as an environment variable:
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```

## 🚀 Usage

### Quick Start

Run the agent with a single command:
```bash
python3 scripts/run_default.py
```

This will run the conversion on a default NetLogo case study and persist the outputs in the `output/` directory, organized by run date and time.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/amazing-feature`).
3.  Commit your changes (`git commit -m 'Add amazing feature'`).
4.  Push to the branch (`git push origin feature/amazing-feature`).
5.  Open a Pull Request.

## 📄 License

This project is licensed under the MIT License.
