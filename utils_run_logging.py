#!/usr/bin/env python3
"""
Orchestrator Logging Utilities
Centralized logging and print functions for the NetLogo orchestrator.
"""

import logging
from typing import Dict, Any, List
from utils_format import FormatUtils


class OrchestratorLogger:
    """Centralized logging utilities for the orchestrator."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize the orchestrator logger.
        
        Args:
            logger: The logger instance to use
        """
        self.logger = logger

    def build_overall_summary(self,
                              run_name: str,
                              base_name: str,
                              model_name: str,
                              persona_set: str,
                              reasoning_effort: str,
                              text_verbosity: str,
                              start_time_seconds: float,
                              end_time_seconds: float,
                              tokens: Dict[str, int],
                              output_dir: str,
                              artifacts: List[str]) -> str:
        """Build an OVERALL SUMMARY text block.

        Args:
            run_name: Timestamp-like run identifier (e.g., 20251022_145318)
            base_name: Case name
            model_name: Model used
            persona_set: Persona set used
            reasoning_effort: minimal|low|medium|high
            text_verbosity: low|medium|high
            start_time_seconds: epoch seconds at start
            end_time_seconds: epoch seconds at end
            tokens: dict with input_tokens, output_tokens, total_tokens, reasoning_tokens
            output_dir: path where artifacts were written
            artifacts: list of artifact filenames relative to output_dir

        Returns:
            A markdown formatted summary block.
        """
        from datetime import datetime
        duration = max(0.0, end_time_seconds - start_time_seconds)
        visible_output = max(tokens.get("output_tokens", 0) - tokens.get("reasoning_tokens", 0), 0)
        lines: List[str] = []
        lines.append("\n==================== OVERALL SUMMARY ====================")
        lines.append(f"Run: {run_name}")
        lines.append(f"Case: {base_name}")
        lines.append(f"Model: {model_name}")
        lines.append(f"Persona: {persona_set}")
        lines.append(f"Reasoning: {reasoning_effort}")
        lines.append(f"Verbosity: {text_verbosity}")
        lines.append("")
        lines.append(f"Start: {datetime.fromtimestamp(start_time_seconds).isoformat(sep=' ', timespec='seconds')}")
        lines.append(f"End:   {datetime.fromtimestamp(end_time_seconds).isoformat(sep=' ', timespec='seconds')}")
        lines.append(f"Duration: {FormatUtils.format_duration(duration)}")
        lines.append("")
        lines.append("Token usage:")
        lines.append(f"  • Input Tokens: {tokens.get('input_tokens', 0):,}")
        lines.append(f"  • Output Tokens: {tokens.get('output_tokens', 0):,} (reasoning={tokens.get('reasoning_tokens', 0):,}, visible={visible_output:,})")
        lines.append(f"  • Total Tokens: {tokens.get('total_tokens', 0):,}")
        lines.append("")
        if artifacts:
            lines.append("Artifacts:")
            for a in artifacts:
                lines.append(f"  • {a}")
        else:
            lines.append("Artifacts: none detected")
        # Compliance metrics (if both initial and final audits are present among artifacts, or at least one)
        try:
            import os, json
            final_path = os.path.join(output_dir, "plantuml_lucim_final_auditor_output.json")
            initial_path = os.path.join(output_dir, "plantuml_lucim_auditor_output.json")
            initial_data = None
            final_data = None
            if os.path.exists(initial_path):
                with open(initial_path, "r", encoding="utf-8") as f:
                    initial_data = json.load(f)
            if os.path.exists(final_path):
                with open(final_path, "r", encoding="utf-8") as f:
                    final_data = json.load(f)

            if final_data and initial_data:
                from utils_metrics import compute_audit_confusion_metrics  # shared pattern across projects
                metrics = compute_audit_confusion_metrics(initial_data, final_data, positive_label="compliant")
                lines.append("")
                lines.append("Auditor metrics (positive = compliant):")
                lines.append(
                    f"  • TP={metrics['tp']} FP={metrics['fp']} TN={metrics['tn']} FN={metrics['fn']} (universe={metrics['universe_size']})"
                )
                lines.append(
                    "  • Precision={:.2%} Recall={:.2%} Specificity={:.2%} Accuracy={:.2%} F1={:.2%}".format(
                        metrics["precision"], metrics["recall"], metrics["specificity"], metrics["accuracy"], metrics["f1"]
                    )
                )
            elif final_data:
                # Print simple counts when only one audit is present
                data = final_data.get("data", {}) if isinstance(final_data, dict) else {}
                ncr = data.get("non-compliant-rules", []) or []
                lines.append("")
                lines.append("Audit summary:")
                lines.append(f"  • Verdict: {str(data.get('verdict', 'unknown')).upper()}")
                lines.append(f"  • Non-compliant rules: {len(ncr)}")
                cov = data.get("coverage", {}) if isinstance(data.get("coverage"), dict) else {}
                lines.append(
                    f"  • Coverage: total={cov.get('total_rules_in_dsl','?')} evaluated={len(cov.get('evaluated', []) or [])} n/a={len(cov.get('not_applicable', []) or [])}"
                )
        except Exception:
            # Do not break summary on metrics extraction errors
            pass
        lines.append("========================================================\n")
        return "\n".join(lines)

    def persist_overall_summary(self, output_dir: str, summary_text: str) -> None:
        """Persist the overall summary to overall_summary.md in output_dir."""
        import os
        from utils_fileio import write_file_content
        filepath = os.path.join(output_dir, "overall_summary.md")
        write_file_content(filepath, summary_text)
        self.logger.info(f"Wrote OVERALL SUMMARY file: {filepath}")
    
    def log_agent_start(self, agent_name: str) -> None:
        """Log the start of an agent execution."""
        self.logger.info(f"🚀 Starting {agent_name} agent execution...")
    
    def log_agent_completion(self, agent_name: str, duration: float, 
                           tokens_used: int = 0, input_tokens: int = 0, 
                           output_tokens: int = 0, reasoning_tokens: int = 0) -> None:
        """
        Log the completion of an agent execution with token usage.
        
        Args:
            agent_name: Name of the agent
            duration: Execution duration in seconds
            tokens_used: Total tokens used
            input_tokens: Input tokens
            output_tokens: Output tokens
            reasoning_tokens: Reasoning tokens
        """
        self.logger.info(f"✅ {agent_name} completed in {FormatUtils.format_duration(duration)}")
        
        if tokens_used > 0:
            # Calculate visible output tokens
            visible_output_tokens = max(output_tokens - reasoning_tokens, 0)
            total_output_tokens = visible_output_tokens + reasoning_tokens
            
            self.logger.info(f"   Input Tokens = {input_tokens:,}")
            self.logger.info(f"   Output Tokens = {total_output_tokens:,} (reasoning = {reasoning_tokens:,}, visibleOutput={visible_output_tokens:,})")
            self.logger.info(f"   Total Tokens = {tokens_used:,}")
        else:
            self.logger.info(f"   Token usage: Not available")
    
    def log_agent_error(self, agent_name: str, duration: float, error: str) -> None:
        """Log an agent execution error."""
        self.logger.error(f"❌ {agent_name} failed after {FormatUtils.format_duration(duration)}: {error}")
    
    def log_file_warning(self, message: str) -> None:
        """Log a file-related warning."""
        self.logger.warning(message)
    
    def log_config_success(self, message: str) -> None:
        """Log a configuration success message."""
        self.logger.info(f"OK: {message}")
    
    def log_config_warning(self, message: str) -> None:
        """Log a configuration warning message."""
        self.logger.warning(f"[WARNING] {message}")
    
    def log_heartbeat(self, base_name: str) -> None:
        """Log a heartbeat message during parallel processing."""
        self.logger.info(f"[heartbeat] Parallel first stage still running for {base_name}...")
    
    def log_early_exit(self, reason: str) -> None:
        """Log an early exit from the orchestration."""
        self.logger.info(f"Step 6 verdict is compliant. Ending flow gracefully. {reason}")
    
    def log_workflow_status(self, base_name: str, results: Dict[str, Any]) -> None:
        """
        Log the workflow status for a base name.
        
        Args:
            base_name: The base name being processed
            results: The results dictionary
        """
        # Determine success status for each step
        netlogo_abstract_syntax_extractor_success = results.get("ast", {}).get("data") is not None
        behavior_extractor_success = results.get("semantics", {}).get("data") is not None
        lucim_environment_success = results.get("lucim_operation_synthesizer", {}).get("data") is not None
        scenario_success = results.get("lucim_scenario_synthesizer", {}).get("data") is not None
        plantuml_writer_success = results.get("plantuml_writer", {}).get("data") is not None
        plantuml_lucim_auditor_success = results.get("plantuml_lucim_auditor", {}).get("data") is not None
        plantuml_lucim_corrector_success = results.get("plantuml_lucim_corrector", {}).get("data") is not None
        plantuml_lucim_final_auditor_success = results.get("plantuml_lucim_final_auditor", {}).get("data") is not None
        
        # Check if optional steps were executed
        plantuml_lucim_corrector_executed = "plantuml_lucim_corrector" in results
        plantuml_lucim_final_auditor_executed = "plantuml_lucim_final_auditor" in results
        
        self.logger.info(f"{base_name} results:")
        self.logger.info(f"  Step 1 - Syntax Parser: {'✓' if netlogo_abstract_syntax_extractor_success else '✗'}")
        self.logger.info(f"  Step 2 - NetLogo Behavior Extractor: {'✓' if behavior_extractor_success else '✗'}")
        self.logger.info(f"  Step 3 - LUCIM Operation Synthesizer: {'✓' if lucim_environment_success else '✗'}")
        self.logger.info(f"  Step 4 - Scenario Writer: {'✓' if scenario_success else '✗'}")
        self.logger.info(f"  Step 5 - PlantUML Writer: {'✓' if plantuml_writer_success else '✗'}")
        self.logger.info(f"  Step 6 - PlantUML LUCIM Auditor: {'✓' if plantuml_lucim_auditor_success else '✗'}")
        
        if plantuml_lucim_corrector_executed:
            self.logger.info(f"  Step 7 - PlantUML LUCIM Corrector: {'✓' if plantuml_lucim_corrector_success else '✗'}")
        if plantuml_lucim_final_auditor_executed:
            self.logger.info(f"  Step 8 - PlantUML LUCIM Final Auditor: {'✓' if plantuml_lucim_final_auditor_success else '✗'}")
        else:
            self.logger.info(f"  Step 7 - PlantUML LUCIM Corrector: SKIPPED (diagrams already compliant)")
    
    def log_error_details(self, results: Dict[str, Any]) -> None:
        """Log detailed error information for failed steps."""
        for step_name, result in results.items():
            if result and isinstance(result, dict) and result.get("errors"):
                error_count = len(result["errors"])
                self.logger.warning(f"    {step_name} errors: {error_count} found")
    
    def log_execution_timing(self, execution_times: Dict[str, float]) -> None:
        """Log execution timing breakdown."""
        self.logger.info(f"\n⏱️  EXECUTION TIMING:")
        total_time = execution_times.get("total_orchestration", 0)
        self.logger.info(f"   Total Orchestration Time: {FormatUtils.format_duration(total_time)}")
        
        # Calculate and display individual agent times
        total_agent_time = 0
        agent_times = []
        
        for agent_name, duration in execution_times.items():
            if agent_name != "total_orchestration" and duration > 0:
                agent_times.append((agent_name, duration))
                total_agent_time += duration
        
        # Sort agents by execution time (descending)
        agent_times.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.info(f"   Total Agent Execution Time: {FormatUtils.format_duration(total_agent_time)}")
        self.logger.info(f"   Overhead Time: {FormatUtils.format_duration(total_time - total_agent_time)}")
        
        if agent_times:
            self.logger.info(f"   \n   📈 AGENT TIMING BREAKDOWN:")
            for agent_name, agent_time in agent_times:
                percentage = (agent_time / total_agent_time * 100) if total_agent_time > 0 else 0
                self.logger.info(f"      {agent_name}: {FormatUtils.format_duration(agent_time)} ({percentage:.1f}%)")
    
    def log_detailed_agent_status(self, results: Dict[str, Any]) -> None:
        """Log detailed agent status information."""
        self.logger.info(f"\n🔍 DETAILED AGENT STATUS:")
        
        # Determine status for each agent
        netlogo_abstract_syntax_extractor_success = results.get("ast", {}).get("data") is not None
        behavior_extractor_success = results.get("semantics", {}).get("data") is not None
        lucim_environment_success = results.get("lucim_operation_synthesizer", {}).get("data") is not None
        scenario_success = results.get("lucim_scenario_synthesizer", {}).get("data") is not None
        plantuml_writer_success = results.get("plantuml_writer", {}).get("data") is not None
        plantuml_lucim_auditor_success = results.get("plantuml_lucim_auditor", {}).get("data") is not None
        plantuml_lucim_corrector_success = results.get("plantuml_lucim_corrector", {}).get("data") is not None
        plantuml_lucim_final_auditor_success = results.get("plantuml_lucim_final_auditor", {}).get("data") is not None
        
        # Check if optional steps were executed
        plantuml_lucim_corrector_executed = "plantuml_lucim_corrector" in results
        plantuml_lucim_final_auditor_executed = "plantuml_lucim_final_auditor" in results
        
        self.logger.info(f"   Step 1 - Syntax Parser Agent: {'✓ SUCCESS' if netlogo_abstract_syntax_extractor_success else '✗ FAILED'}")
        self.logger.info(f"   Step 2 - NetLogo Behavior Extractor Agent: {'✓ SUCCESS' if behavior_extractor_success else '✗ FAILED'}")
        self.logger.info(f"   Step 3 - LUCIM Operation Synthesizer Agent: {'✓ SUCCESS' if lucim_environment_success else '✗ FAILED'}")
        self.logger.info(f"   Step 4 - Scenario Writer Agent: {'✓ SUCCESS' if scenario_success else '✗ FAILED'}")
        self.logger.info(f"   Step 5 - PlantUML Writer Agent: {'✓ SUCCESS' if plantuml_writer_success else '✗ FAILED'}")
        self.logger.info(f"   Step 6 - PlantUML LUCIM Auditor Agent: {'✓ SUCCESS' if plantuml_lucim_auditor_success else '✗ FAILED'}")
        
        if not plantuml_lucim_corrector_executed:
            self.logger.info(f"   Step 7 - PlantUML LUCIM Corrector Agent: ⏭️  SKIPPED (diagrams already compliant)")
        else:
            self.logger.info(f"   Step 7 - PlantUML LUCIM Corrector Agent: {'✓ SUCCESS' if plantuml_lucim_corrector_success else '✗ FAILED'}")
        
        if not plantuml_lucim_final_auditor_executed:
            self.logger.info(f"   Step 8 - PlantUML LUCIM Final Auditor Agent: ⏭️  SKIPPED (corrector was skipped or not required)")
        else:
            self.logger.info(f"   Step 8 - PlantUML LUCIM Final Auditor Agent: {'✓ SUCCESS' if plantuml_lucim_final_auditor_success else '✗ FAILED'}")
    
    def log_output_files(self, base_name: str, timestamp: str, model: str, results: Dict[str, Any]) -> None:
        """Log information about generated output files."""
        self.logger.info(f"\n📁 OUTPUT FILES GENERATED:")
        
        for result_key, result_data in results.items():
            if result_data and isinstance(result_data, dict):
                agent_type = result_data.get("agent_type", "unknown")
                if agent_type == "netlogo_abstract_syntax_extractor":
                    self.logger.info(f"   • Syntax Parser: {base_name}_{timestamp}_{model}_1a_netlogo_abstract_syntax_extractor_v1_*.md")
                elif agent_type == "behavior_extractor":
                    self.logger.info(f"   • NetLogo Behavior Extractor: {base_name}_{timestamp}_{model}_1b_behavior_extractor_v1_*.json/md")
                elif agent_type == "lucim_operation_synthesizer":
                    self.logger.info(f"   • LUCIM Operation Synthesizer: {base_name}_{timestamp}_{model}_2_lucim_v1_*.json/md")
                elif agent_type == "scenario_writer":
                    self.logger.info(f"   • Scenarios: {base_name}_{timestamp}_{model}_3_scenario_v1_*.md")
                elif agent_type == "plantuml_writer":
                    self.logger.info(f"   • PlantUML Diagrams: {base_name}_{timestamp}_{model}_4_plantuml_*.json/md/.puml")
                elif agent_type == "plantuml_lucim_auditor":
                    self.logger.info(f"   • PlantUML LUCIM Audit: {base_name}_{timestamp}_{model}_5_lucim_audit_*.json/md/.puml")
                elif agent_type == "plantuml_lucim_corrector":
                    self.logger.info(f"   • PlantUML LUCIM Corrector: {base_name}_{timestamp}_{model}_7_lucim_corrector_*.json/md/.puml")
                elif agent_type == "plantuml_lucim_final_auditor":
                    self.logger.info(f"   • PlantUML LUCIM Final Auditor: {base_name}_{timestamp}_{model}_8_lucim_final_auditor_*.json/md/.puml")
    
    def log_pipeline_completion(self, successful_agents: int, total_agents: int) -> None:
        """Log pipeline completion status."""
        self.logger.info(f"\n🎯 PIPELINE COMPLETION:")
        if successful_agents == total_agents:
            self.logger.info(f"   🎉 FULL SUCCESS: All {total_agents} agents completed successfully!")
            self.logger.info(f"   📋 Final output includes LUCIM-compliant PlantUML sequence diagrams")
        elif successful_agents >= 6:  # At least core pipeline completed (all 6 agents)
            self.logger.info(f"   ⚠️  PARTIAL SUCCESS: {successful_agents}/{total_agents} agents completed")
            self.logger.info(f"   📋 Some outputs available, but pipeline incomplete")
        else:
            self.logger.info(f"   ❌ PIPELINE FAILED: Only {successful_agents}/{total_agents} agents completed")
            self.logger.info(f"   📋 Limited outputs available")
    
    def log_compliance_status(self, final_compliance: Dict[str, Any]) -> None:
        """Log final compliance status."""
        self.logger.info(f"\n🔍 COMPLIANCE STATUS:")
        if final_compliance["status"] == "VERIFIED":
            self.logger.info(f"   ✅ FINAL COMPLIANCE: VERIFIED")
            self.logger.info(f"   🎯 Result: Final audit confirms LUCIM compliance")
        elif final_compliance["status"] == "NON-COMPLIANT":
            self.logger.info(f"   ❌ FINAL COMPLIANCE: NON-COMPLIANT")
            self.logger.info(f"   📊 Result: One or more LUCIM rules were violated")
        else:
            self.logger.info(f"   ❓ COMPLIANCE STATUS: UNKNOWN")
            self.logger.info(f"   ⚠️  Result: No authoritative compliance verdict available")
