"""Tests for audit functionality."""

from stanzaflow.tools.audit import audit_workflow


class TestAuditTool:
    """Test audit tool functionality."""

    def test_audit_basic_workflow(self):
        """Test auditing a basic workflow."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Test Workflow",
                "agents": [
                    {
                        "name": "TestAgent",
                        "steps": [
                            {"name": "TestStep", "attributes": {"artifact": "test.txt"}}
                        ],
                    }
                ],
                "secrets": [],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(ir, "langgraph", verbose=True)

        # Should have statistics
        assert "statistics" in results
        stats = results["statistics"]
        assert stats["agents"] == 1
        assert stats["total_steps"] == 1
        assert stats["secrets"] == 0
        assert stats["escape_blocks"] == 0
        assert stats["avg_steps_per_agent"] == 1.0
        assert "artifact" in stats["attribute_usage"]
        assert stats["attribute_usage"]["artifact"] == 1

        # Should have summary
        assert "summary" in results
        summary = results["summary"]
        assert summary["health"] in ["excellent", "good", "fair", "poor"]
        assert "complexity_score" in summary
        assert summary["complexity_score"] in ["simple", "moderate", "complex", "very complex"]

    def test_audit_complex_workflow(self):
        """Test auditing a complex workflow."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Complex Workflow",
                "agents": [
                    {
                        "name": "Agent1",
                        "steps": [
                            {
                                "name": "Step1",
                                "attributes": {"artifact": "out1.txt", "retry": 3},
                            },
                            {
                                "name": "Step2",
                                "attributes": {"timeout": 30, "branch": "condition"},
                            },
                        ],
                    },
                    {
                        "name": "Agent2",
                        "steps": [
                            {
                                "name": "Step3",
                                "attributes": {"artifact": "out2.txt"},
                            }
                        ],
                    },
                ],
                "secrets": [
                    {"env_var": "API_KEY"},
                    {"env_var": "SECRET_TOKEN"},
                ],
                "escape_blocks": [
                    {"target": "langgraph", "code": "custom_logic()"}
                ],
            },
        }

        results = audit_workflow(ir, "langgraph", verbose=True)

        # Check statistics
        stats = results["statistics"]
        assert stats["agents"] == 2
        assert stats["total_steps"] == 3
        assert stats["secrets"] == 2
        assert stats["escape_blocks"] == 1
        assert stats["avg_steps_per_agent"] == 1.5

        # Check attribute usage
        attr_usage = stats["attribute_usage"]
        assert attr_usage["artifact"] == 2
        assert attr_usage["retry"] == 1
        assert attr_usage["timeout"] == 1
        assert attr_usage["branch"] == 1

        # Should have capability gap for branching
        issues = results["issues"]
        has_branching_issue = any(
            "branch" in issue.get("message", "").lower() for issue in issues
        )
        assert has_branching_issue

    def test_audit_workflow_with_issues(self):
        """Test auditing a workflow with various issues."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "",  # Missing title
                "agents": [
                    {
                        "name": "Agent1",
                        "steps": [
                            {"name": "Step1", "attributes": {}},
                            {"name": "Step1", "attributes": {}},  # Duplicate step name
                        ],
                    },
                    {
                        "name": "Agent1",  # Duplicate agent name
                        "steps": [],  # No steps
                    },
                ],
                "secrets": [
                    {"env_var": "api_key"},  # Lowercase (should recommend uppercase)
                    {"env_var": "API_KEY"},
                    {"env_var": "API_KEY"},  # Duplicate
                ],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(ir, "langgraph", verbose=True)

        issues = results["issues"]
        
        # Should detect missing title
        has_title_issue = any("title" in issue.get("message", "").lower() for issue in issues)
        assert has_title_issue

        # Should detect duplicate agent name
        has_duplicate_agent = any(
            "duplicate agent" in issue.get("message", "").lower() for issue in issues
        )
        assert has_duplicate_agent

        # Should detect duplicate step name
        has_duplicate_step = any(
            "duplicate step" in issue.get("message", "").lower() for issue in issues
        )
        assert has_duplicate_step

        # Should detect empty agent
        has_empty_agent = any("no steps" in issue.get("message", "").lower() for issue in issues)
        assert has_empty_agent

        # Should detect duplicate secret
        has_duplicate_secret = any(
            "duplicate secret" in issue.get("message", "").lower() for issue in issues
        )
        assert has_duplicate_secret

        # Should recommend uppercase for env var
        recommendations = results["recommendations"]
        has_uppercase_rec = any("uppercase" in rec.lower() for rec in recommendations)
        assert has_uppercase_rec

        # Health should be poor due to errors
        summary = results["summary"]
        assert summary["health"] == "poor"

    def test_audit_secrets_configuration(self):
        """Test auditing secrets configuration."""
        ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Secrets Test",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ],
                "secrets": [
                    {"env_var": "GOOD_SECRET"},
                    {"env_var": "bad_secret"},  # Should recommend uppercase
                    {"env_var": "INVALID-SECRET"},  # Contains dash
                    {"env_var": "GOOD_SECRET"},  # Duplicate
                    {},  # Missing env_var
                ],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(ir, "langgraph", verbose=True)

        issues = results["issues"]
        recommendations = results["recommendations"]

        # Should find issues with invalid characters
        has_invalid_chars = any(
            "special characters" in issue.get("message", "") for issue in issues
        )
        assert has_invalid_chars

        # Should find duplicate secret
        has_duplicate = any("duplicate secret" in issue.get("message", "").lower() for issue in issues)
        assert has_duplicate

        # Should find missing env_var
        has_missing_var = any(
            "missing environment variable" in issue.get("message", "").lower() for issue in issues
        )
        assert has_missing_var

        # Should recommend uppercase
        has_uppercase_rec = any("uppercase" in rec.lower() for rec in recommendations)
        assert has_uppercase_rec

    def test_complexity_scoring(self):
        """Test workflow complexity scoring."""
        # Simple workflow
        simple_ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Simple",
                "agents": [
                    {"name": "Agent", "steps": [{"name": "Step", "attributes": {}}]}
                ],
                "secrets": [],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(simple_ir, "langgraph")
        assert results["summary"]["complexity_score"] == "simple"

        # Complex workflow
        complex_ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Complex",
                "agents": [
                    {
                        "name": f"Agent{i}",
                        "steps": [
                            {
                                "name": f"Step{j}",
                                "attributes": {
                                    "artifact": f"out{j}.txt",
                                    "retry": 3,
                                    "timeout": 30,
                                },
                            }
                            for j in range(5)
                        ],
                    }
                    for i in range(5)
                ],
                "secrets": [],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(complex_ir, "langgraph")
        complexity = results["summary"]["complexity_score"]
        assert complexity in ["complex", "very complex"]

    def test_health_scoring(self):
        """Test workflow health scoring."""
        # Excellent health - no issues
        excellent_ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "Perfect Workflow",
                "agents": [
                    {
                        "name": "PerfectAgent",
                        "steps": [
                            {"name": "PerfectStep", "attributes": {"artifact": "output.txt"}}
                        ],
                    }
                ],
                "secrets": [],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(excellent_ir, "langgraph")
        assert results["summary"]["health"] in ["excellent", "good"]

        # Poor health - has errors
        poor_ir = {
            "ir_version": "0.2",
            "workflow": {
                "title": "",  # Missing title
                "agents": [
                    {
                        "name": "Agent",
                        "steps": [
                            {"name": "Step1", "attributes": {}},
                            {"name": "Step1", "attributes": {}},  # Duplicate
                        ],
                    }
                ],
                "secrets": [],
                "escape_blocks": [],
            },
        }

        results = audit_workflow(poor_ir, "langgraph")
        assert results["summary"]["health"] == "poor"
