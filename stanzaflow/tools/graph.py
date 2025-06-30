"""Graph generation for StanzaFlow workflows."""

import subprocess
import tempfile
import shutil
import hashlib
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()

# Cache for tool availability checks
_MERMAID_AVAILABLE: Optional[bool] = None
_GRAPHVIZ_AVAILABLE: Optional[bool] = None
# Lock to guard cache mutation in multithreaded contexts
_CACHE_LOCK = threading.Lock()


def _reset_tool_cache() -> None:
    """Reset tool availability cache (for testing)."""
    global _MERMAID_AVAILABLE, _GRAPHVIZ_AVAILABLE
    _MERMAID_AVAILABLE = None
    _GRAPHVIZ_AVAILABLE = None


def generate_workflow_graph(ir: Dict[str, Any], output_path: Path, out_fmt: str = "svg") -> bool:
    """Generate a visual graph of the workflow.
    
    Args:
        ir: StanzaFlow IR dictionary
        output_path: Path to save the graph
        out_fmt: Output format (svg, png, pdf)
        
    Returns:
        bool: True if generated with preferred method, False if fallback used
    """
    # Generate Mermaid diagram
    mermaid_content = _generate_mermaid_diagram(ir)
    
    # Try Mermaid CLI first
    if _try_mermaid_cli(mermaid_content, output_path, out_fmt):
        return True
    
    # Fall back to Graphviz
    console.print("[yellow]Mermaid CLI not available, falling back to Graphviz...[/yellow]")
    return _try_graphviz_fallback(ir, output_path, out_fmt)


def _generate_mermaid_diagram(ir: Dict[str, Any]) -> str:
    """Generate Mermaid diagram from IR."""
    workflow = ir.get("workflow", {})
    title = workflow.get("title", "Untitled Workflow")
    agents = workflow.get("agents", [])
    
    lines = [
        "graph TD",
        f'    %% {title}',
        "",
    ]
    
    # Add start node
    lines.append('    START([Start])')
    
    if not agents:
        lines.extend([
            '    END([End])',
            '    START --> END',
        ])
        return "\n".join(lines)
    
    # Generate nodes for each agent
    prev_node = "START"
    for i, agent in enumerate(agents):
        agent_name = agent.get("name", f"Agent{i+1}")
        agent_id = _stable_id("AGENT", agent_name)
        
        # Agent node
        lines.append(f'    {agent_id}["{agent_name}"]')
        
        # Steps as sub-nodes
        steps = agent.get("steps", [])
        for j, step in enumerate(steps):
            step_name = step.get("name", f"Step{j+1}")
            step_id = _stable_id("STEP", f"{agent_name}:{step_name}")
            
            # Step node with attributes info
            attributes = step.get("attributes", {})
            attr_info = ""
            if attributes:
                attr_labels = []
                if "artifact" in attributes:
                    attr_labels.append(f"📄 {attributes['artifact']}")
                if "retry" in attributes:
                    attr_labels.append(f"🔄 retry:{attributes['retry']}")
                if "timeout" in attributes:
                    attr_labels.append(f"⏱️ {attributes['timeout']}s")
                if attr_labels:
                    attr_info = f"<br/><small>{' | '.join(attr_labels)}</small>"
            
            lines.append(f'    {step_id}["{step_name}{attr_info}"]')
        
        # Connect previous to current agent
        lines.append(f'    {prev_node} --> {agent_id}')
        
        # Connect agent to its first step
        if steps:
            lines.append(f'    {agent_id} --> STEP_{i}_0')
            
            # Connect steps sequentially
            for j in range(len(steps) - 1):
                lines.append(f'    STEP_{i}_{j} --> STEP_{i}_{j+1}')
            
            prev_node = f"STEP_{i}_{len(steps)-1}"
        else:
            prev_node = agent_id
    
    # Add end node
    lines.extend([
        '    END([End])',
        f'    {prev_node} --> END',
    ])
    
    return "\n".join(lines)


def _try_mermaid_cli(mermaid_content: str, output_path: Path, out_fmt: str) -> bool:
    """Try to render using Mermaid CLI."""
    global _MERMAID_AVAILABLE
    
    try:
        # Check if mmdc is available (cached)
        with _CACHE_LOCK:
            if _MERMAID_AVAILABLE is None:
                mmdc_path = shutil.which("mmdc")
                if not mmdc_path:
                    _MERMAID_AVAILABLE = False
                    return False
                try:
                    subprocess.run(["mmdc", "--version"], capture_output=True, check=True)
                    _MERMAID_AVAILABLE = True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    _MERMAID_AVAILABLE = False
                    return False
        
        if not _MERMAID_AVAILABLE:
            return False
        
        # Create temporary file for Mermaid content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_file:
            tmp_file.write(mermaid_content)
            tmp_path = Path(tmp_file.name)
        
        try:
            # Run Mermaid CLI
            cmd = [
                "mmdc", 
                "-i", str(tmp_path),
                "-o", str(output_path),
                "-t", "default",
                "--backgroundColor", "white"
            ]
            
            if out_fmt != "svg":
                cmd.extend(["-f", out_fmt])
            
            subprocess.run(cmd, check=True, capture_output=True)
            return True
            
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _try_graphviz_fallback(ir: Dict[str, Any], output_path: Path, out_fmt: str) -> bool:
    """Fall back to Graphviz rendering."""
    try:
        # Try to use the diagrams library first
        result = _try_diagrams_library(ir, output_path, out_fmt)
        if result:
            return True
    except ImportError:
        pass  # diagrams library not available
    except Exception:
        pass  # diagrams library failed
    
    # Fall back to raw Graphviz
    return _try_raw_graphviz(ir, output_path, out_fmt)


def _try_diagrams_library(ir: Dict[str, Any], output_path: Path, out_fmt: str) -> bool:
    """Try using the diagrams library for rendering."""
    try:
        from diagrams import Diagram
        from diagrams.programming.flowchart import StartEnd, Process
        
        workflow = ir.get("workflow", {})
        title = workflow.get("title", "Untitled Workflow")
        agents = workflow.get("agents", [])
        
        # Create diagram
        with Diagram(title, filename=str(output_path.with_suffix("")), direction="TB"):
            start = StartEnd("Start")
            
            if not agents:
                end = StartEnd("End")
                start >> end
                return True
            
            prev_node = start
            for agent in agents:
                agent_name = agent.get("name", "Agent")
                agent_node = Process(agent_name)
                prev_node >> agent_node
                prev_node = agent_node
            
            end = StartEnd("End")
            prev_node >> end
        
        return True
        
    except ImportError:
        return False


def _try_raw_graphviz(ir: Dict[str, Any], output_path: Path, out_fmt: str) -> bool:
    """Fall back to raw Graphviz DOT format."""
    try:
        workflow = ir.get("workflow", {})
        title = workflow.get("title", "Untitled Workflow")
        agents = workflow.get("agents", [])
        
        # Generate DOT content
        dot_lines = [
            "digraph workflow {",
            "    rankdir=TB;",
            f'    label="{title}";',
            "    labelloc=t;",
            "    node [shape=box, style=rounded];",
            "",
            '    start [label="Start", shape=ellipse];',
        ]
        
        if not agents:
            dot_lines.extend([
                '    end [label="End", shape=ellipse];',
                '    start -> end;',
                "}"
            ])
        else:
            prev_node = "start"
            for i, agent in enumerate(agents):
                agent_name = agent.get("name", f"Agent{i+1}")
                agent_id = _stable_id("agent", agent_name)
                
                # Escape quotes in agent name
                escaped_name = agent_name.replace('"', '\\"')
                dot_lines.append(f'    {agent_id} [label="{escaped_name}"];')
                dot_lines.append(f'    {prev_node} -> {agent_id};')
                prev_node = agent_id
            
            dot_lines.extend([
                '    end [label="End", shape=ellipse];',
                f'    {prev_node} -> end;',
                "}"
            ])
        
        dot_content = "\n".join(dot_lines)
        
        # Try to render with dot command
        global _GRAPHVIZ_AVAILABLE
        try:
            # Check if dot is available (cached)
            with _CACHE_LOCK:
                if _GRAPHVIZ_AVAILABLE is None:
                    dot_path = shutil.which("dot")
                    if not dot_path:
                        _GRAPHVIZ_AVAILABLE = False
                    else:
                        try:
                            subprocess.run(["dot", "-V"], capture_output=True, check=True)
                            _GRAPHVIZ_AVAILABLE = True
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            _GRAPHVIZ_AVAILABLE = False
            
            if not _GRAPHVIZ_AVAILABLE:
                # No Graphviz CLI available, fall through to text fallback
                raise subprocess.CalledProcessError(1, ["dot"])
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as tmp_file:
                tmp_file.write(dot_content)
                tmp_path = Path(tmp_file.name)
            
            try:
                cmd = ["dot", f"-T{out_fmt}", str(tmp_path), "-o", str(output_path)]
                subprocess.run(cmd, check=True, capture_output=True)
                return True
            finally:
                tmp_path.unlink(missing_ok=True)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # No Graphviz CLI, save as text but preserve original path for user feedback
            text_output_path = output_path.with_suffix(".txt")
            
            with open(text_output_path, "w") as f:
                f.write("# Workflow Graph (Text Fallback)\n\n")
                f.write(f"## {title}\n\n")
                
                if not agents:
                    f.write("Start → End\n")
                else:
                    f.write("Start")
                    for agent in agents:
                        agent_name = agent.get("name", "Agent")
                        f.write(f" → {agent_name}")
                    f.write(" → End\n")
                
                # Add the Mermaid source for reference
                f.write("\n\n## Mermaid Source\n\n")
                f.write("```mermaid\n")
                mermaid_content = _generate_mermaid_diagram(ir)
                f.write(mermaid_content)
                f.write("\n```\n")
            
            console.print(
                f"[yellow]Graphviz not available or rendering failed—saved text representation to: {text_output_path}[/yellow]"
            )
            console.print(
                "💡 Install Mermaid CLI (mmdc) or Graphviz for full SVG/PNG rendering capabilities."
            )
            return True
            
    except Exception:
        return False 


# Helper to create stable node IDs avoiding collisions
def _stable_id(prefix: str, name: str) -> str:
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{digest}" 