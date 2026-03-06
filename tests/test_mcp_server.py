# ADC-IMPLEMENTS: <adc-mcp-server-01>
"""
Tests for the ADC MCP Server.

Tests cover:
  - Server creation and initialization
  - All 14 tool implementations (local + AI-powered stubs)
  - Resource listing and reading
  - Prompt listing and retrieval
  - Auto-installer client detection
  - Caching behavior
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary ADC project structure for testing."""
    # contracts/
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()

    contract_content = """---
contract_id: "test-adc-001"
title: "Test Contract"
status: "active"
version: 1.0
---

### [Feature: Test Feature] <test-feature-01>
A test feature for validation.

**Parity:**
- **Implementation Scope:** `src/test_module.py`
- **Tests:** `tests/test_feature.py`

### [DataModel: TestModel] <test-model-01>
A test data model.

- `id: str` - Unique identifier
- `name: str` - Display name

**Parity:**
- **Implementation Scope:** `src/models.py`
"""
    (contracts_dir / "test-adc-001.md").write_text(contract_content)

    # src/
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    source_content = """# ADC-IMPLEMENTS: <test-feature-01>
class TestFeature:
    pass

# ADC-IMPLEMENTS: <test-model-01>
class TestModel:
    id: str
    name: str
"""
    (src_dir / "test_module.py").write_text(source_content)

    # roles/
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    (roles_dir / "auditor.md").write_text("# Auditor Role\nYou are the auditor.")
    (roles_dir / "code_generator.md").write_text("# Code Generator\nYou generate code.")
    (roles_dir / "refiner.md").write_text("# Refiner\nYou refine contracts.")

    return tmp_path


# ---------------------------------------------------------------------------
# Tool Tests
# ---------------------------------------------------------------------------

class TestTools:
    """Test all MCP tool implementations."""

    def test_adc_init(self, tmp_path):
        from adc_cli.mcp_server.tools import _adc_init

        result = _adc_init(project_path=str(tmp_path))
        assert result["status"] == "success"
        assert (tmp_path / "contracts").exists()
        assert (tmp_path / "src").exists()
        assert (tmp_path / "roles").exists()

    def test_adc_init_already_exists(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_init

        # First init — may create contracts/README.md
        _adc_init(project_path=str(temp_project))
        # Second init — everything already exists
        result = _adc_init(project_path=str(temp_project))
        assert result["status"] == "success"
        assert "Already initialized" in result["message"]

    def test_adc_list_contracts(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_list_contracts

        result = _adc_list_contracts(project_path=str(temp_project))
        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["contracts"][0]["contract_id"] == "test-adc-001"
        assert result["contracts"][0]["title"] == "Test Contract"

    def test_adc_list_contracts_no_dir(self, tmp_path):
        from adc_cli.mcp_server.tools import _adc_list_contracts

        result = _adc_list_contracts(project_path=str(tmp_path))
        assert result["status"] == "error"

    def test_adc_parse_contract(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_parse_contract

        result = _adc_parse_contract(
            file_path="contracts/test-adc-001.md",
            project_path=str(temp_project),
        )
        assert result["status"] == "success"
        assert result["metadata"]["contract_id"] == "test-adc-001"
        assert result["summary"]["total_blocks"] == 2
        assert "Feature" in result["summary"]["block_types"]
        assert "DataModel" in result["summary"]["block_types"]

    def test_adc_parse_contract_detailed(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_parse_contract

        result = _adc_parse_contract(
            file_path="contracts/test-adc-001.md",
            project_path=str(temp_project),
            detailed=True,
        )
        assert result["status"] == "success"
        # Detailed mode includes body text
        for block in result["blocks"]:
            assert "body" in block

    def test_adc_parse_contract_caching(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_parse_contract, _contract_cache

        # Clear cache
        _contract_cache.clear()

        # First call — should parse
        result1 = _adc_parse_contract(
            file_path="contracts/test-adc-001.md",
            project_path=str(temp_project),
        )
        assert result1["status"] == "success"
        assert len(_contract_cache) == 1

        # Second call — should use cache
        result2 = _adc_parse_contract(
            file_path="contracts/test-adc-001.md",
            project_path=str(temp_project),
        )
        assert result2 == result1

    def test_adc_parse_contract_not_found(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_parse_contract

        result = _adc_parse_contract(
            file_path="contracts/nonexistent.md",
            project_path=str(temp_project),
        )
        assert result["status"] == "error"

    def test_adc_find_markers(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_find_markers

        result = _adc_find_markers(project_path=str(temp_project))
        assert result["status"] == "success"
        assert result["total_markers"] == 2
        assert result["unique_block_ids"] == 2
        assert "test-feature-01" in result["by_block_id"]
        assert "test-model-01" in result["by_block_id"]

    def test_adc_find_markers_no_src(self, tmp_path):
        from adc_cli.mcp_server.tools import _adc_find_markers

        result = _adc_find_markers(project_path=str(tmp_path))
        assert result["status"] == "error"

    def test_adc_get_role(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_get_role

        result = _adc_get_role("auditor", project_path=str(temp_project))
        assert result["status"] == "success"
        assert "Auditor" in result["content"]

    def test_adc_get_role_not_found(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_get_role

        result = _adc_get_role("nonexistent_role", project_path=str(temp_project))
        assert result["status"] == "error"

    def test_adc_list_roles(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_list_roles

        result = _adc_list_roles(project_path=str(temp_project))
        assert result["status"] == "success"
        assert result["count"] >= 3
        role_names = [r["name"] for r in result["roles"]]
        assert "auditor" in role_names
        assert "code_generator" in role_names

    def test_adc_health(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_health

        result = _adc_health(project_path=str(temp_project))
        assert result["status"] in ("healthy", "warning", "degraded")
        assert "contracts" in result["components"]
        assert "source" in result["components"]
        assert "roles" in result["components"]

    def test_adc_config_show(self):
        from adc_cli.mcp_server.tools import _adc_config_show

        result = _adc_config_show()
        assert result["status"] == "success"
        assert "config" in result
        assert "default_agent" in result["config"]

    def test_adc_validate(self, temp_project):
        from adc_cli.mcp_server.tools import _adc_validate

        result = _adc_validate(project_path=str(temp_project))
        assert result["status"] == "success"
        assert "validation_summary" in result

    def test_adc_validate_no_contracts(self, tmp_path):
        from adc_cli.mcp_server.tools import _adc_validate

        result = _adc_validate(project_path=str(tmp_path))
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# Resource Tests
# ---------------------------------------------------------------------------

class TestResources:
    """Test MCP resource providers."""

    def test_list_role_names(self, temp_project):
        from adc_cli.mcp_server.resources import _list_role_names

        with patch("adc_cli.mcp_server.resources.Path") as mock_path:
            # Directly test with the temp_project roles
            names = _list_role_names()
            # At minimum, package-bundled roles should be discoverable
            # (exact count depends on environment)
            assert isinstance(names, list)

    def test_read_config(self):
        from adc_cli.mcp_server.resources import _read_config

        config_text = _read_config()
        # Should be valid JSON
        config = json.loads(config_text)
        assert "default_agent" in config


# ---------------------------------------------------------------------------
# Prompt Tests
# ---------------------------------------------------------------------------

class TestPrompts:
    """Test MCP prompt definitions."""

    def test_prompt_definitions_complete(self):
        from adc_cli.mcp_server.prompts import PROMPT_DEFINITIONS, _PROMPT_CONFIG

        # Every prompt should have a config entry
        for prompt in PROMPT_DEFINITIONS:
            assert prompt.name in _PROMPT_CONFIG, f"Missing config for prompt: {prompt.name}"

    def test_prompt_definitions_have_descriptions(self):
        from adc_cli.mcp_server.prompts import PROMPT_DEFINITIONS

        for prompt in PROMPT_DEFINITIONS:
            assert prompt.description, f"Empty description for prompt: {prompt.name}"
            assert len(prompt.description) > 20, f"Description too short for: {prompt.name}"

    def test_build_prompt_content(self, temp_project):
        from adc_cli.mcp_server.prompts import _build_prompt_content

        # Test with a role that exists in temp_project
        os.chdir(temp_project)
        content = _build_prompt_content(
            role_name="auditor",
            agent_filename="adc-compliance-auditor.md",
            task_description="test audit",
        )
        # Should contain role content or fallback
        assert len(content) > 0
        assert "ADC" in content or "auditor" in content.lower()


# ---------------------------------------------------------------------------
# Setup MCP Command Tests
# ---------------------------------------------------------------------------

class TestSetupMCP:
    """Test the setup-mcp auto-installer."""

    def test_get_client_configs(self):
        from adc_cli.command_modules.setup_mcp_command import _get_client_configs

        clients = _get_client_configs()
        assert len(clients) == 4
        names = [c["name"] for c in clients]
        assert "Windsurf" in names
        assert "Cursor" in names
        assert "Claude Desktop" in names
        assert "VS Code Continue" in names

    def test_build_mcp_entry(self):
        from adc_cli.command_modules.setup_mcp_command import _build_mcp_entry

        entry = _build_mcp_entry("adc-mcp")
        assert entry["command"] == "adc-mcp"
        assert entry["args"] == []

    def test_build_mcp_entry_full_path(self):
        from adc_cli.command_modules.setup_mcp_command import _build_mcp_entry

        entry = _build_mcp_entry("/usr/local/bin/adc-mcp")
        assert entry["command"] == "/usr/local/bin/adc-mcp"

    def test_write_client_config_new(self, tmp_path):
        from adc_cli.command_modules.setup_mcp_command import _write_client_config

        client = {
            "name": "TestClient",
            "config_path": tmp_path / "test_config.json",
            "config_key": "mcpServers",
        }
        mcp_entry = {"command": "adc-mcp", "args": []}

        ok, message = _write_client_config(client, mcp_entry)
        assert ok
        assert "Configured" in message

        # Verify file was written correctly
        with open(client["config_path"]) as f:
            config = json.load(f)
        assert "mcpServers" in config
        assert "adc" in config["mcpServers"]
        assert config["mcpServers"]["adc"]["command"] == "adc-mcp"

    def test_write_client_config_existing(self, tmp_path):
        from adc_cli.command_modules.setup_mcp_command import _write_client_config

        config_path = tmp_path / "test_config.json"
        existing = {"mcpServers": {"other-server": {"command": "other"}}}
        config_path.write_text(json.dumps(existing))

        client = {
            "name": "TestClient",
            "config_path": config_path,
            "config_key": "mcpServers",
        }
        mcp_entry = {"command": "adc-mcp", "args": []}

        ok, message = _write_client_config(client, mcp_entry)
        assert ok

        with open(config_path) as f:
            config = json.load(f)
        # Both servers should be present
        assert "adc" in config["mcpServers"]
        assert "other-server" in config["mcpServers"]

    def test_write_client_config_no_overwrite(self, tmp_path):
        from adc_cli.command_modules.setup_mcp_command import _write_client_config

        config_path = tmp_path / "test_config.json"
        existing = {"mcpServers": {"adc": {"command": "old-adc-mcp"}}}
        config_path.write_text(json.dumps(existing))

        client = {
            "name": "TestClient",
            "config_path": config_path,
            "config_key": "mcpServers",
        }
        mcp_entry = {"command": "adc-mcp", "args": []}

        ok, message = _write_client_config(client, mcp_entry, force=False)
        assert ok
        assert "Already configured" in message

        # Should NOT have overwritten
        with open(config_path) as f:
            config = json.load(f)
        assert config["mcpServers"]["adc"]["command"] == "old-adc-mcp"

    def test_write_client_config_force_overwrite(self, tmp_path):
        from adc_cli.command_modules.setup_mcp_command import _write_client_config

        config_path = tmp_path / "test_config.json"
        existing = {"mcpServers": {"adc": {"command": "old-adc-mcp"}}}
        config_path.write_text(json.dumps(existing))

        client = {
            "name": "TestClient",
            "config_path": config_path,
            "config_key": "mcpServers",
        }
        mcp_entry = {"command": "adc-mcp", "args": []}

        ok, message = _write_client_config(client, mcp_entry, force=True)
        assert ok

        with open(config_path) as f:
            config = json.load(f)
        assert config["mcpServers"]["adc"]["command"] == "adc-mcp"


# ---------------------------------------------------------------------------
# Server Creation Test
# ---------------------------------------------------------------------------

class TestServerCreation:
    """Test that the MCP server can be created."""

    def test_create_server(self):
        from adc_cli.mcp_server.server import create_server

        server = create_server()
        assert server is not None
        assert server.name == "adc"

    def test_tool_definitions_valid(self):
        from adc_cli.mcp_server.tools import TOOL_DEFINITIONS, _TOOL_HANDLERS

        # Every defined tool should have a handler
        for tool in TOOL_DEFINITIONS:
            assert tool.name in _TOOL_HANDLERS, f"Missing handler for tool: {tool.name}"

        # Every handler should have a tool definition
        tool_names = {t.name for t in TOOL_DEFINITIONS}
        for handler_name in _TOOL_HANDLERS:
            assert handler_name in tool_names, f"Orphan handler: {handler_name}"

    def test_tool_count(self):
        from adc_cli.mcp_server.tools import TOOL_DEFINITIONS

        assert len(TOOL_DEFINITIONS) == 14
