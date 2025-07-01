"""Tests for stable node ID generation in graph tools."""

from stanzaflow.tools.graph import _generate_mermaid_diagram, _stable_id


class TestStableNodeIDs:
    """Test stable node ID generation."""

    def test_stable_id_consistency(self):
        """Test that stable IDs are consistent across calls."""
        name = "TestAgent"
        
        # Multiple calls should return the same ID
        id1 = _stable_id("agent", name)
        id2 = _stable_id("agent", name)
        id3 = _stable_id("agent", name)
        
        assert id1 == id2 == id3
        assert id1.startswith("agent_")
        assert len(id1) == 14  # "agent_" + 8 char hash

    def test_stable_id_uniqueness(self):
        """Test that different names produce different IDs."""
        id1 = _stable_id("agent", "Agent1")
        id2 = _stable_id("agent", "Agent2")
        id3 = _stable_id("step", "Agent1")  # Same name, different prefix
        
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_stable_id_collision_resistance(self):
        """Test that similar names don't collide."""
        id1 = _stable_id("agent", "DataProcessor")
        id2 = _stable_id("agent", "DataProcessor2")
        id3 = _stable_id("agent", "Data Processor")
        
        assert id1 != id2
        assert id1 != id3
        assert id2 != id3

    def test_mermaid_uses_stable_ids(self):
        """Test that Mermaid diagram generation uses stable IDs."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "DataProcessor",
                        "steps": [
                            {"name": "LoadData", "attributes": {}},
                            {"name": "ProcessData", "attributes": {"artifact": "output.txt"}},
                        ],
                    },
                    {
                        "name": "Reporter",
                        "steps": [
                            {"name": "GenerateReport", "attributes": {}},
                        ],
                    },
                ],
            },
        }

        mermaid = _generate_mermaid_diagram(ir)
        
        # Check that stable IDs are used
        agent1_id = _stable_id("AGENT", "DataProcessor")
        agent2_id = _stable_id("AGENT", "Reporter")
        step1_id = _stable_id("STEP", "DataProcessor:LoadData")
        step2_id = _stable_id("STEP", "DataProcessor:ProcessData")
        step3_id = _stable_id("STEP", "Reporter:GenerateReport")
        
        assert agent1_id in mermaid
        assert agent2_id in mermaid
        assert step1_id in mermaid
        assert step2_id in mermaid
        assert step3_id in mermaid

    def test_mermaid_stable_across_regeneration(self):
        """Test that Mermaid diagrams are stable across regenerations."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Stable Test",
                "agents": [
                    {
                        "name": "Agent1",
                        "steps": [
                            {"name": "Step1", "attributes": {}},
                            {"name": "Step2", "attributes": {}},
                        ],
                    },
                ],
            },
        }

        # Generate the same diagram multiple times
        mermaid1 = _generate_mermaid_diagram(ir)
        mermaid2 = _generate_mermaid_diagram(ir)
        mermaid3 = _generate_mermaid_diagram(ir)
        
        # Should be identical
        assert mermaid1 == mermaid2 == mermaid3

    def test_mermaid_name_change_stability(self):
        """Test that changing names produces different but stable IDs."""
        ir_original = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [
                    {
                        "name": "OriginalAgent",
                        "steps": [
                            {"name": "OriginalStep", "attributes": {}},
                        ],
                    },
                ],
            },
        }

        ir_renamed = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test",
                "agents": [
                    {
                        "name": "RenamedAgent",
                        "steps": [
                            {"name": "RenamedStep", "attributes": {}},
                        ],
                    },
                ],
            },
        }

        mermaid_original = _generate_mermaid_diagram(ir_original)
        mermaid_renamed = _generate_mermaid_diagram(ir_renamed)
        
        # Should be different
        assert mermaid_original != mermaid_renamed
        
        # But each should be stable
        assert mermaid_original == _generate_mermaid_diagram(ir_original)
        assert mermaid_renamed == _generate_mermaid_diagram(ir_renamed)

    def test_step_id_includes_agent_context(self):
        """Test that step IDs include agent context to prevent collisions."""
        # Two agents with steps having the same name
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Collision Test",
                "agents": [
                    {
                        "name": "Agent1",
                        "steps": [
                            {"name": "Process", "attributes": {}},
                        ],
                    },
                    {
                        "name": "Agent2",
                        "steps": [
                            {"name": "Process", "attributes": {}},
                        ],
                    },
                ],
            },
        }

        mermaid = _generate_mermaid_diagram(ir)
        
        # Get the step IDs
        step1_id = _stable_id("STEP", "Agent1:Process")
        step2_id = _stable_id("STEP", "Agent2:Process")
        
        # Should be different despite same step name
        assert step1_id != step2_id
        
        # Both should appear in the diagram
        assert step1_id in mermaid
        assert step2_id in mermaid

    def test_special_characters_in_names(self):
        """Test that special characters in names don't break ID generation."""
        names_with_special_chars = [
            "Agent-1",
            "Agent_2",
            "Agent 3",
            "Agent.4",
            "Agent@5",
            "Agent#6",
            "数据处理器",  # Unicode characters
            "Agent(7)",
        ]
        
        ids = []
        for name in names_with_special_chars:
            stable_id = _stable_id("agent", name)
            ids.append(stable_id)
            
            # Should be valid identifier-like format
            assert stable_id.startswith("agent_")
            assert len(stable_id) == 14
        
        # All IDs should be unique
        assert len(set(ids)) == len(ids)

    def test_empty_workflow_stable_ids(self):
        """Test stable ID generation for empty workflow."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Empty Workflow",
                "agents": [],
            },
        }

        mermaid1 = _generate_mermaid_diagram(ir)
        mermaid2 = _generate_mermaid_diagram(ir)
        
        # Should be stable even for empty workflow
        assert mermaid1 == mermaid2
        assert "START([Start])" in mermaid1
        assert "END([End])" in mermaid1
        assert "START --> END" in mermaid1 