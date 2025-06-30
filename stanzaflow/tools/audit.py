"""Audit functionality for StanzaFlow workflows."""

import re
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console

console = Console()


def audit_workflow(ir: Dict[str, Any], target: str = "langgraph", verbose: bool = False) -> Dict[str, Any]:
    """Audit a workflow IR for issues, TODOs, and recommendations.
    
    Args:
        ir: StanzaFlow IR dictionary
        target: Target adapter to audit against
        verbose: Include detailed information
        
    Returns:
        Dict with issues, todos, and recommendations
    """
    results = {
        "issues": [],
        "todos": [],
        "recommendations": []
    }
    
    workflow = ir.get("workflow", {})
    
    # Basic workflow validation
    _check_workflow_structure(workflow, results)
    
    # Check for adapter-specific issues
    if target == "langgraph":
        _check_langgraph_compatibility(workflow, results)
    
    # Check for unsupported patterns that need AI escapes
    _check_unsupported_patterns(workflow, results)
    
    # Generate code and check for TODOs
    _check_generated_code(ir, target, results, verbose)
    
    # Generate recommendations
    _generate_recommendations(workflow, results)
    
    return results


def _check_workflow_structure(workflow: Dict[str, Any], results: Dict[str, Any]) -> None:
    """Check basic workflow structure for issues."""
    
    # Check if workflow has a title
    if not workflow.get("title"):
        results["issues"].append({
            "severity": "warning",
            "message": "Workflow has no title",
            "details": "Consider adding a title for better documentation"
        })
    
    # Check if workflow has agents
    agents = workflow.get("agents", [])
    if not agents:
        results["issues"].append({
            "severity": "error",
            "message": "Workflow has no agents",
            "details": "A workflow must have at least one agent to be useful"
        })
        return
    
    # Check agent structure
    for i, agent in enumerate(agents):
        agent_name = agent.get("name", f"Agent{i+1}")
        
        if not agent.get("name"):
            results["issues"].append({
                "severity": "warning",
                "message": f"Agent {i+1} has no name",
                "details": "Agent names help with readability and debugging"
            })
        
        steps = agent.get("steps", [])
        if not steps:
            results["issues"].append({
                "severity": "warning",
                "message": f"Agent '{agent_name}' has no steps",
                "details": "Empty agents might not be useful in the workflow"
            })
        
        # Check step structure
        for j, step in enumerate(steps):
            if not step.get("name"):
                results["issues"].append({
                    "severity": "warning",
                    "message": f"Step {j+1} in agent '{agent_name}' has no name",
                    "details": "Step names help with readability and debugging"
                })


def _check_langgraph_compatibility(workflow: Dict[str, Any], results: Dict[str, Any]) -> None:
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
                results["todos"].append({
                    "type": "Unsupported Attributes",
                    "description": f"Step '{step_name}' uses unsupported attributes: {', '.join(unsupported_attrs)}",
                    "location": f"Agent '{agent_name}', Step {j+1}"
                })


def _check_unsupported_patterns(workflow: Dict[str, Any], results: Dict[str, Any]) -> None:
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
                if any(keyword in content.lower() for keyword in ["if", "condition", "branch", "parallel", "fork"]):
                    has_complex_flow = True
                    break
            if has_complex_flow:
                break
        
        if has_complex_flow:
            results["todos"].append({
                "type": "Complex Flow Control",
                "description": "Workflow appears to need branching or parallel execution",
                "location": "Multiple agents with conditional logic"
            })
    
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
                results["todos"].append({
                    "type": "Retry Logic",
                    "description": f"Step '{step_name}' needs retry logic implementation",
                    "location": f"Agent '{agent_name}', Step {j+1}"
                })
            
            if "timeout" in attributes:
                results["todos"].append({
                    "type": "Timeout Handling",
                    "description": f"Step '{step_name}' needs timeout handling implementation",
                    "location": f"Agent '{agent_name}', Step {j+1}"
                })


def _check_generated_code(ir: Dict[str, Any], target: str, results: Dict[str, Any], verbose: bool) -> None:
    """Generate code and check for TODOs."""
    
    try:
        if target == "langgraph":
            from stanzaflow.adapters.langgraph.emit import LangGraphEmitter
            
            # Use a temporary file to capture the generated code
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)
            
            try:
                emitter = LangGraphEmitter()
                emitter.emit(ir, tmp_path)
                
                # Read back the generated code
                with open(tmp_path, 'r') as f:
                    generated_code = f.read()
                
                # Check for TODO comments in generated code
                lines = generated_code.split('\n')
                todo_count = 0
                
                for line_no, line in enumerate(lines, 1):
                    if "TODO" in line or "FIXME" in line or "escape needed" in line:
                        todo_count += 1
                        if verbose:
                            results["todos"].append({
                                "type": "Generated Code TODO",
                                "description": line.strip(),
                                "location": f"Generated code line {line_no}"
                            })
                
                if todo_count > 0 and not verbose:
                    results["todos"].append({
                        "type": "Generated Code TODOs",
                        "description": f"Found {todo_count} TODO/FIXME comments in generated code",
                        "location": "Generated LangGraph code"
                    })
            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)
                
    except Exception as e:
        results["issues"].append({
            "severity": "error",
            "message": f"Failed to generate {target} code for audit",
            "details": str(e)
        })


def _generate_recommendations(workflow: Dict[str, Any], results: Dict[str, Any]) -> None:
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