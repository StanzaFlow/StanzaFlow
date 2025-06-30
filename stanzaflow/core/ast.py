"""AST and compiler for StanzaFlow."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from lark import Lark, Token, Tree
from lark.exceptions import LarkError

from stanzaflow.core.exceptions import ParseError


@dataclass
class StepAttribute:
    """Represents a step attribute (artifact, retry, etc.)."""
    
    key: str
    value: Union[str, int]


@dataclass
class Step:
    """Represents a workflow step."""
    
    name: str
    attributes: List[StepAttribute] = field(default_factory=list)
    
    def get_attribute(self, key: str) -> Optional[StepAttribute]:
        """Get attribute by key."""
        return next((attr for attr in self.attributes if attr.key == key), None)


@dataclass
class Agent:
    """Represents a workflow agent."""
    
    name: str
    steps: List[Step] = field(default_factory=list)


@dataclass
class EscapeBlock:
    """Represents an escape block."""
    
    target: str
    code: str


@dataclass
class SecretBlock:
    """Represents a secret declaration."""
    
    env_var: str


@dataclass
class Workflow:
    """Represents a complete workflow."""
    
    title: str
    agents: List[Agent] = field(default_factory=list)
    escape_blocks: List[EscapeBlock] = field(default_factory=list)
    secret_blocks: List[SecretBlock] = field(default_factory=list)


class StanzaFlowTransformer:
    """Transforms Lark parse tree to StanzaFlow AST."""
    
    def transform(self, tree: Tree) -> Workflow:
        """Transform parse tree to workflow AST."""
        workflow = Workflow(title="")
        
        # Handle start -> workflow structure
        if tree.data == "start":
            tree = tree.children[0]  # Get the workflow tree
        
        for child in tree.children:
            if isinstance(child, Tree):
                if child.data == "heading":
                    workflow.title = self._extract_heading(child)
                elif child.data == "content":
                    # Process content children
                    for content_child in child.children:
                        if isinstance(content_child, Tree):
                            if content_child.data == "agent_block":
                                agent = self._transform_agent_block(content_child)
                                workflow.agents.append(agent)
                            elif content_child.data == "escape_block":
                                escape = self._transform_escape_block(content_child)
                                workflow.escape_blocks.append(escape)
                            elif content_child.data == "secret_block":
                                secret = self._transform_secret_block(content_child)
                                workflow.secret_blocks.append(secret)
        
        return workflow
    
    def _extract_heading(self, tree: Tree) -> str:
        """Extract heading text."""
        # The heading should contain a HEADING token
        for child in tree.children:
            if isinstance(child, Token) and child.type == "HEADING":
                # Remove '# ' prefix
                return child.value.strip().lstrip('# ').strip()
        return ""
    
    def _transform_agent_block(self, tree: Tree) -> Agent:
        """Transform agent block to Agent."""
        agent_header = tree.children[0]
        agent_name = self._extract_agent_name(agent_header)
        
        agent = Agent(name=agent_name)
        
        # Process steps
        for child in tree.children[1:]:
            if isinstance(child, Tree) and child.data == "step":
                step = self._transform_step(child)
                agent.steps.append(step)
        
        return agent
    
    def _extract_agent_name(self, tree: Tree) -> str:
        """Extract agent name from agent header."""
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "agent_name":
                # Extract from the tree's first token
                if child.children and isinstance(child.children[0], Token):
                    return child.children[0].value.strip()
            elif isinstance(child, Token) and child.type == "agent_name":
                return child.value.strip()
        return ""
    
    def _transform_step(self, tree: Tree) -> Step:
        """Transform step to Step."""
        # Structure: step_header step_name
        step_name_tree = tree.children[1]  # step_name tree
        step_name = ""
        
        if isinstance(step_name_tree, Tree) and step_name_tree.data == "step_name":
            # Extract from the tree's first token
            if step_name_tree.children and isinstance(step_name_tree.children[0], Token):
                step_name = step_name_tree.children[0].value.strip()
        elif isinstance(step_name_tree, Token):
            step_name = step_name_tree.value.strip()
        
        step = Step(name=step_name)
        
        # Collect attributes from remaining children
        step.attributes = self._transform_step_body(tree)
        
        return step
    
    def _extract_step_name(self, tree: Tree) -> str:
        """Extract step name from step header."""
        for child in tree.children:
            if isinstance(child, Token) and child.type == "step_name":
                return child.value.strip()
        return ""
    
    def _transform_step_body(self, tree: Tree) -> List[StepAttribute]:
        """Transform step body to list of attributes."""
        attributes = []
        
        for child in tree.children:
            if isinstance(child, Tree) and child.data == "step_attr":
                attr = self._transform_step_attribute(child)
                if attr:
                    attributes.append(attr)
        
        return attributes
    
    def _transform_step_attribute(self, tree: Tree) -> Optional[StepAttribute]:
        """Transform step attribute."""
        # Structure: one of the ATTR_* tokens
        for child in tree.children:
            if isinstance(child, Token):
                attr_type = child.type
                line = child.value.strip()
                
                # Unified regex parsing: key: value (allows whitespace around colon)
                import re
                match = re.match(r"^(?P<key>[a-zA-Z_]+)\s*:\s*(?P<val>.+)$", line)
                if not match:
                    continue
                key = match.group("key").lower()
                raw_val = match.group("val").strip()

                if key == "artifact":
                    return StepAttribute(key="artifact", value=raw_val)
                if key == "retry":
                    if raw_val.isdigit():
                        return StepAttribute(key="retry", value=int(raw_val))
                if key == "timeout":
                    if raw_val.isdigit():
                        return StepAttribute(key="timeout", value=int(raw_val))
                if key in {"on_error", "branch", "finally"}:
                    return StepAttribute(key=key, value=raw_val)
        
        return None
    
    def _transform_escape_block(self, tree: Tree) -> EscapeBlock:
        """Transform escape block."""
        target = ""
        code = ""
        
        for child in tree.children:
            if isinstance(child, Token):
                if child.type == "escape_target":
                    target = child.value.strip()
                elif child.type == "CODE_BLOCK":
                    code = child.value.strip()
            elif isinstance(child, Tree) and child.data == "escape_target":
                # Extract token inside the tree
                if child.children and isinstance(child.children[0], Token):
                    target = child.children[0].value.strip()
        
        return EscapeBlock(target=target, code=code)
    
    def _transform_secret_block(self, tree: Tree) -> SecretBlock:
        """Transform secret block."""
        env_var = ""
        
        for child in tree.children:
            if isinstance(child, Token) and child.type == "ENV_VAR":
                env_var = child.value.strip()
        
        return SecretBlock(env_var=env_var)


class StanzaFlowCompiler:
    """Compiles .sf.md files to IR."""
    
    def __init__(self) -> None:
        """Initialize compiler with Lark grammar."""
        grammar_path = Path(__file__).parent / "stz_grammar.lark"
        with open(grammar_path, "r") as f:
            grammar = f.read()
        
        self.parser = Lark(grammar, start="start", parser="earley")
        self.transformer = StanzaFlowTransformer()
    
    def parse_file(self, file_path: Path) -> Workflow:
        """Parse .sf.md file to workflow AST."""
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.parse_string(content, str(file_path))
        except Exception as e:
            raise ParseError(f"Failed to read file {file_path}: {e}")
    
    def parse_string(self, content: str, source: str = "<string>") -> Workflow:
        """Parse string content to workflow AST."""
        try:
            tree = self.parser.parse(content)
            workflow = self.transformer.transform(tree)
            return workflow
        except LarkError as e:
            raise ParseError(f"Parse error in {source}: {e}")
        except Exception as e:
            raise ParseError(f"Unexpected error parsing {source}: {e}")
    
    def workflow_to_ir(self, workflow: Workflow) -> Dict[str, Any]:  # pragma: no cover
        """Convert workflow AST to IR 0.2."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": workflow.title,
                "agents": [],
                "escape_blocks": [],
                "secrets": []
            }
        }
        
        # Convert agents
        for agent in workflow.agents:
            agent_ir = {
                "name": agent.name,
                "steps": []
            }
            
            for step in agent.steps:
                step_ir = {
                    "name": step.name,
                    "attributes": {}
                }
                
                for attr in step.attributes:
                    step_ir["attributes"][attr.key] = attr.value
                
                agent_ir["steps"].append(step_ir)
            
            ir["workflow"]["agents"].append(agent_ir)
        
        # Convert escape blocks
        for escape in workflow.escape_blocks:
            escape_ir = {
                "target": escape.target,
                "code": escape.code
            }
            ir["workflow"]["escape_blocks"].append(escape_ir)
        
        # Convert secrets
        for secret in workflow.secret_blocks:
            secret_ir = {
                "env_var": secret.env_var
            }
            ir["workflow"]["secrets"].append(secret_ir)
        
        return ir
    
    def compile_file(self, file_path: Path) -> Dict[str, Any]:  # pragma: no cover
        """Compile .sf.md file to IR 0.2."""
        workflow = self.parse_file(file_path)
        return self.workflow_to_ir(workflow)
    
    def compile_string(self, content: str, source: str = "<string>") -> Dict[str, Any]:  # pragma: no cover
        """Compile string content to IR 0.2."""
        workflow = self.parse_string(content, source)
        return self.workflow_to_ir(workflow) 