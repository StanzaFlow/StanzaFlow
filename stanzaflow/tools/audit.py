"""Audit functionality for StanzaFlow workflows."""

import tempfile
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


def audit_workflow(
    ir: dict[str, Any], target: str = "langgraph", verbose: bool = False
) -> dict[str, Any]:
    """Audit a workflow IR for issues, TODOs, and recommendations.

    Args:
        ir: StanzaFlow IR dictionary
        target: Target adapter to audit against
        verbose: Include detailed information

    Returns:
        Dict with issues, todos, recommendations, and statistics
    """
    results: dict[str, Any] = {
        "issues": [],
        "todos": [],
        "recommendations": [],
        "statistics": {},
        "summary": {},
    }

    workflow = ir.get("workflow", {})

    # Collect basic statistics
    _collect_statistics(workflow, results)

    # Basic workflow validation
    _check_workflow_structure(workflow, results)

    # Check adapter capabilities
    _check_adapter_capabilities(ir, target, results)

    # Check for adapter-specific issues
    if target == "langgraph":
        _check_langgraph_compatibility(workflow, results)

    # Check for unsupported patterns that need AI escapes
    _check_unsupported_patterns(workflow, results)

    # Check secrets configuration
    _check_secrets_configuration(workflow, results)

    # Generate code and check for TODOs
    _check_generated_code(ir, target, results, verbose)

    # Generate recommendations
    _generate_recommendations(workflow, results)

    # Generate summary
    _generate_summary(results)

    return results


def _collect_statistics(workflow: dict[str, Any], results: dict[str, Any]) -> None:
    """Collect workflow statistics for reporting."""
    agents = workflow.get("agents", [])
    secrets = workflow.get("secrets", [])
    escape_blocks = workflow.get("escape_blocks", [])

    total_steps = sum(len(agent.get("steps", [])) for agent in agents)

    # Count step attributes
    attribute_counts: dict[str, int] = {}
    for agent in agents:
        for step in agent.get("steps", []):
            for attr in step.get("attributes", {}):
                attribute_counts[attr] = attribute_counts.get(attr, 0) + 1

    # Get safe secrets summary (masked values)
    from stanzaflow.core.secrets import get_safe_secrets_summary

    ir = {"workflow": workflow}
    safe_secrets = get_safe_secrets_summary(ir)

    results["statistics"] = {
        "agents": len(agents),
        "total_steps": total_steps,
        "secrets": len(secrets),
        "escape_blocks": len(escape_blocks),
        "attribute_usage": attribute_counts,
        "avg_steps_per_agent": round(total_steps / len(agents), 1) if agents else 0,
        "secret_status": safe_secrets,  # Masked secret values for safe display
    }


def _check_adapter_capabilities(
    ir: dict[str, Any], target: str, results: dict[str, Any]
) -> None:
    """Check if adapter supports all features required by the workflow."""
    try:
        from stanzaflow.adapters import get_adapter

        adapter = get_adapter(target)
        capability_gaps = adapter.get_capability_gaps(ir)

        if capability_gaps:
            for gap in sorted(capability_gaps):
                results["issues"].append(
                    {
                        "severity": "warning",
                        "message": f"Adapter '{target}' does not support '{gap}' capability",
                        "details": f"This feature is required by the workflow but not implemented in {target}",
                    }
                )

                results["todos"].append(
                    {
                        "type": "Capability Gap",
                        "description": f"'{gap}' feature needs implementation or alternative adapter",
                        "location": f"{target} adapter",
                    }
                )
    except Exception:
        # If adapter loading fails, skip capability analysis
        pass


def _check_workflow_structure(
    workflow: dict[str, Any], results: dict[str, Any]
) -> None:
    """Check basic workflow structure for issues."""

    # Check if workflow has a title
    if not workflow.get("title"):
        results["issues"].append(
            {
                "severity": "warning",
                "message": "Workflow has no title",
                "details": "Consider adding a title for better documentation",
            }
        )

    # Check if workflow has agents
    agents = workflow.get("agents", [])
    if not agents:
        results["issues"].append(
            {
                "severity": "error",
                "message": "Workflow has no agents",
                "details": "A workflow must have at least one agent to be useful",
            }
        )
        return

    # Check agent structure
    seen_agents = set()
    for i, agent in enumerate(agents):
        agent_name = agent.get("name", f"Agent{i+1}")

        if not agent.get("name"):
            results["issues"].append(
                {
                    "severity": "warning",
                    "message": f"Agent {i+1} has no name",
                    "details": "Agent names help with readability and debugging",
                }
            )

        steps = agent.get("steps", [])
        if not steps:
            results["issues"].append(
                {
                    "severity": "warning",
                    "message": f"Agent '{agent_name}' has no steps",
                    "details": "Empty agents might not be useful in the workflow",
                }
            )

        # Duplicate agent name detection
        if agent_name in seen_agents:
            results["issues"].append(
                {
                    "severity": "error",
                    "message": f"Duplicate agent name '{agent_name}'",
                    "details": "Agent names must be unique within a workflow",
                }
            )
        seen_agents.add(agent_name)

        # Check step structure
        seen_steps = set()
        for j, step in enumerate(steps):
            step_name = step.get("name")
            if not step_name:
                results["issues"].append(
                    {
                        "severity": "warning",
                        "message": f"Step {j+1} in agent '{agent_name}' has no name",
                        "details": "Step names help with readability and debugging",
                    }
                )
            else:
                if step_name in seen_steps:
                    results["issues"].append(
                        {
                            "severity": "error",
                            "message": f"Duplicate step name '{step_name}' in agent '{agent_name}'",
                            "details": "Step names must be unique within an agent.",
                        }
                    )
                seen_steps.add(step_name)


def _check_langgraph_compatibility(
    workflow: dict[str, Any], results: dict[str, Any]
) -> None:
    """Check for LangGraph-specific compatibility issues."""

    agents = workflow.get("agents", [])

    # Check for LangGraph-specific patterns
    for i, agent in enumerate(agents):
        agent_name = agent.get("name", f"Agent{i+1}")
        steps = agent.get("steps", [])

        for j, step in enumerate(steps):
            step_name = step.get("name", f"Step{j+1}")
            attributes = step.get("attributes", {})

            # Check for unsupported step attributes in current implementation
            unsupported_attrs = []
            for attr in attributes:
                if attr not in ["artifact", "retry", "timeout"]:
                    unsupported_attrs.append(attr)

            if unsupported_attrs:
                results["todos"].append(
                    {
                        "type": "Unsupported Attributes",
                        "description": f"Step '{step_name}' uses unsupported attributes: {', '.join(unsupported_attrs)}",
                        "location": f"Agent '{agent_name}', Step {j+1}",
                    }
                )


def _check_unsupported_patterns(
    workflow: dict[str, Any], results: dict[str, Any]
) -> None:
    """Check for patterns that require AI escapes."""

    agents = workflow.get("agents", [])

    # Currently our implementation only supports sequential workflows
    if len(agents) > 1:
        # Check if this looks like it needs branching/parallel logic
        has_complex_flow = False
        for agent in agents:
            steps = agent.get("steps", [])
            for step in steps:
                content = step.get("content", "")
                # Look for keywords that suggest complex flow control
                if any(
                    keyword in content.lower()
                    for keyword in ["if", "condition", "branch", "parallel", "fork"]
                ):
                    has_complex_flow = True
                    break
            if has_complex_flow:
                break

        if has_complex_flow:
            results["todos"].append(
                {
                    "type": "Complex Flow Control",
                    "description": "Workflow appears to need branching or parallel execution",
                    "location": "Multiple agents with conditional logic",
                }
            )

    # Check for other patterns that might need escapes
    for i, agent in enumerate(agents):
        agent_name = agent.get("name", f"Agent{i+1}")
        steps = agent.get("steps", [])

        for j, step in enumerate(steps):
            step_name = step.get("name", f"Step{j+1}")
            content = step.get("content", "")
            attributes = step.get("attributes", {})

            # Check for complex attributes that aren't implemented
            if "retry" in attributes:
                results["todos"].append(
                    {
                        "type": "Retry Logic",
                        "description": f"Step '{step_name}' needs retry logic implementation",
                        "location": f"Agent '{agent_name}', Step {j+1}",
                    }
                )

            if "timeout" in attributes:
                results["todos"].append(
                    {
                        "type": "Timeout Handling",
                        "description": f"Step '{step_name}' needs timeout handling implementation",
                        "location": f"Agent '{agent_name}', Step {j+1}",
                    }
                )


def _check_generated_code(
    ir: dict[str, Any], target: str, results: dict[str, Any], verbose: bool
) -> None:
    """Generate code and check for TODOs."""

    try:
        if target == "langgraph":
            from stanzaflow.adapters.langgraph.emit import LangGraphEmitter

            # Use a temporary file to capture the generated code
            with tempfile.NamedTemporaryFile(
                mode="w+", suffix=".py", delete=False
            ) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                emitter = LangGraphEmitter()
                emitter.emit(ir, tmp_path)

                # Read back the generated code
                with open(tmp_path) as f:
                    generated_code = f.read()

                # Check for TODO comments in generated code
                lines = generated_code.split("\n")
                todo_count = 0

                for line_no, line in enumerate(lines, 1):
                    if "TODO" in line or "FIXME" in line or "escape needed" in line:
                        todo_count += 1
                        if verbose:
                            results["todos"].append(
                                {
                                    "type": "Generated Code TODO",
                                    "description": line.strip(),
                                    "location": f"Generated code line {line_no}",
                                }
                            )

                if todo_count > 0 and not verbose:
                    results["todos"].append(
                        {
                            "type": "Generated Code TODOs",
                            "description": f"Found {todo_count} TODO/FIXME comments in generated code",
                            "location": "Generated LangGraph code",
                        }
                    )
            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)

    except Exception as e:
        results["issues"].append(
            {
                "severity": "error",
                "message": f"Failed to generate {target} code for audit",
                "details": str(e),
            }
        )


def _generate_recommendations(
    workflow: dict[str, Any], results: dict[str, Any]
) -> None:
    """Generate helpful recommendations based on the workflow."""

    agents = workflow.get("agents", [])

    # Recommend adding documentation
    if not workflow.get("description"):
        results["recommendations"].append(
            "Add a description to your workflow for better documentation"
        )

    # Recommend naming conventions
    unnamed_count = 0
    for agent in agents:
        if not agent.get("name"):
            unnamed_count += 1
        steps = agent.get("steps", [])
        for step in steps:
            if not step.get("name"):
                unnamed_count += 1

    if unnamed_count > 0:
        results["recommendations"].append(
            f"Consider naming all agents and steps ({unnamed_count} unnamed items found)"
        )

    # Recommend step attributes for robustness
    has_no_attributes = True
    for agent in agents:
        steps = agent.get("steps", [])
        for step in steps:
            if step.get("attributes"):
                has_no_attributes = False
                break
        if not has_no_attributes:
            break

    if has_no_attributes and len(agents) > 0:
        results["recommendations"].append(
            "Consider adding retry/timeout attributes to critical steps for robustness"
        )

    # Recommend testing
    results["recommendations"].append(
        "Test your compiled workflow with sample data before production use"
    )


def _check_secrets_configuration(
    workflow: dict[str, Any], results: dict[str, Any]
) -> None:
    """Check secrets configuration for issues."""
    secrets = workflow.get("secrets", [])

    if not secrets:
        return

    seen_vars = set()
    for secret in secrets:
        env_var = secret.get("env_var")
        if not env_var:
            results["issues"].append(
                {
                    "severity": "error",
                    "message": "Secret block missing environment variable name",
                    "details": "Each !env block must specify a variable name",
                }
            )
            continue

        if env_var in seen_vars:
            results["issues"].append(
                {
                    "severity": "warning",
                    "message": f"Duplicate secret declaration for '{env_var}'",
                    "details": "Environment variables should only be declared once",
                }
            )
        seen_vars.add(env_var)

        # Check naming conventions
        if not env_var.isupper():
            results["recommendations"].append(
                f"Consider using uppercase for environment variable '{env_var}' (conventional style)"
            )

        if not env_var.replace("_", "").isalnum():
            results["issues"].append(
                {
                    "severity": "warning",
                    "message": f"Environment variable '{env_var}' contains special characters",
                    "details": "Environment variables should only contain letters, numbers, and underscores",
                }
            )


def _generate_summary(results: dict[str, Any]) -> None:
    """Generate audit summary."""
    issues = results["issues"]
    todos = results["todos"]
    stats = results["statistics"]

    # Count by severity
    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")

    # Determine overall health
    if error_count > 0:
        health = "poor"
    elif warning_count > 3:
        health = "fair"
    elif warning_count > 0 or len(todos) > 5:
        health = "good"
    else:
        health = "excellent"

    results["summary"] = {
        "health": health,
        "total_issues": len(issues),
        "error_count": error_count,
        "warning_count": warning_count,
        "todo_count": len(todos),
        "recommendation_count": len(results["recommendations"]),
        "complexity_score": _calculate_complexity_score(stats),
    }


def _calculate_complexity_score(stats: dict[str, Any]) -> str:
    """Calculate workflow complexity score."""
    agents = stats.get("agents", 0)
    steps = stats.get("total_steps", 0)
    attributes = sum(stats.get("attribute_usage", {}).values())

    # Simple scoring algorithm
    score = agents * 2 + steps + attributes * 0.5

    if score < 5:
        return "simple"
    elif score < 15:
        return "moderate"
    elif score < 30:
        return "complex"
    else:
        return "very complex"
