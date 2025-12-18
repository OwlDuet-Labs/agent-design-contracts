"""Sequential ADC workflow implementation with nested loops and progress detection.

ADC-IMPLEMENTS: <sequential-workflow-agent-01>
ADC-IMPLEMENTS: <sequential-workflow-impl-01>
ADC-IMPLEMENTS: <sequential-workflow-algorithm-01>
"""

import json
import os
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import anthropic

from .state import WorkflowState, WorkflowResult


# Model selection: Use Haiku for simple agents, Sonnet for complex reasoning
# contract-writer uses Sonnet because contract creation requires strong reasoning
AGENT_MODELS_HAIKU = {
    "@adc-contract-writer": "haiku",  # Haiku for cost-effective contract creation
    "@adc-compliance-auditor": "haiku",
    "@adc-contract-refiner": "haiku",
    "@adc-pr-orchestrator": "haiku",
    "@adc-code-generator": "sonnet",  # Sonnet for complex code generation
    "@adc-system-evaluator": "sonnet",
}

# All Sonnet (for comparison)
AGENT_MODELS_SONNET = {
    "@adc-contract-writer": "sonnet",
    "@adc-compliance-auditor": "sonnet",
    "@adc-contract-refiner": "sonnet",
    "@adc-pr-orchestrator": "sonnet",
    "@adc-code-generator": "sonnet",
    "@adc-system-evaluator": "sonnet",
}

# Hybrid: Sonnet for contract-writer (better parity sections), Haiku for other simple agents
AGENT_MODELS_SONNET_CONTRACTS = {
    "@adc-contract-writer": "sonnet",  # Sonnet for high-quality contract parity sections
    "@adc-compliance-auditor": "haiku",
    "@adc-contract-refiner": "haiku",
    "@adc-pr-orchestrator": "haiku",
    "@adc-code-generator": "sonnet",  # Sonnet for complex code generation
    "@adc-system-evaluator": "sonnet",
}


# Tool definitions for agent workspace actions
WORKSPACE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the workspace. Returns the file content as a string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read (absolute or relative to workspace)"
                }
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the workspace. Creates the file if it doesn't exist, overwrites if it does. Creates parent directories if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write (absolute or relative to workspace)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["file_path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Edit an existing file by replacing old_string with new_string. The old_string must match exactly (including whitespace).",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit (absolute or relative to workspace)"
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact string to find in the file (must match exactly)"
                },
                "new_string": {
                    "type": "string",
                    "description": "String to replace old_string with"
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    },
    {
        "name": "run_bash",
        "description": "Execute a bash command in the workspace directory. Returns stdout, stderr, and exit code.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Bash command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds (default: 60)",
                    "default": 60
                }
            },
            "required": ["command"]
        }
    },
    {
        "name": "list_directory",
        "description": "List files and directories in a given path. Returns list of entries with type (file/directory) and name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Path to directory to list (absolute or relative to workspace, defaults to workspace root)",
                    "default": "."
                }
            }
        }
    }
]


@dataclass
class ProgressTracker:
    """Track compliance score progress to detect stagnation.

    ADC-IMPLEMENTS: <sequential-workflow-algorithm-01>
    """

    scores: list = field(default_factory=list)

    def add_score(self, score: float):
        """Add a compliance score to history."""
        self.scores.append(score)

    def is_stuck(self) -> bool:
        """Check if no progress in last 2 runs."""
        if len(self.scores) < 3:
            return False

        # Check last 3 scores for improvement
        last_three = self.scores[-3:]
        # If no improvement in last 2 runs (scores not increasing)
        if last_three[-1] <= last_three[-2] and last_three[-2] <= last_three[-3]:
            return True
        return False


class SequentialWorkflow:
    """Sequential ADC workflow controller that eliminates orchestrator overhead.

    This workflow implements a two-level loop architecture:
    - Inner Loop: Auditor ↔ Code Generator (implementation refinement until compliance >= 0.8)
    - Outer Loop: Evaluator → Refiner → Auditor (contract refinement until tests pass)

    Key innovations:
    1. Context Summarization: Agents receive 10-20K token summaries instead of 100-300K full context
    2. Sequential Invocation: Agents execute directly without coordinator accumulation
    3. Progress Detection: Stops workflow after 2 stagnant runs (no compliance improvement)

    ADC-IMPLEMENTS: <sequential-workflow-agent-01>
    """

    def __init__(self, workspace: Path, claude_executable: str = "claude", use_haiku: bool = False, agent_models: Optional[Dict[str, str]] = None):
        """Initialize sequential workflow.

        Args:
            workspace: Path to workspace directory
            claude_executable: Path to Claude CLI executable (DEPRECATED - using API now)
            use_haiku: Use Haiku for simple agents (default: False, all Sonnet)
            agent_models: Custom agent model configuration (overrides use_haiku if provided)
        """
        self.workspace = workspace
        self.use_haiku = use_haiku
        if agent_models is not None:
            self.agent_models = agent_models
        else:
            self.agent_models = AGENT_MODELS_HAIKU if use_haiku else AGENT_MODELS_SONNET
        self.contracts_summary: Optional[str] = None
        self.progress = ProgressTracker()
        self.state_file = workspace / ".adc-workflow-state.json"

        # Initialize Anthropic API client (persistent session)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = anthropic.Anthropic(api_key=api_key)

        # Cache role file contents (loaded once, reused for all agents)
        self.role_files: Dict[str, str] = {}
        self._load_role_files()

    def _load_role_files(self):
        """Load role file contents from adc-labs framework directory.

        Role files are read from the framework installation rather than copied
        into workspaces. This keeps role definitions centralized and prevents
        workspace pollution.

        The role files directory is located relative to this module:
        adc-labs/src/adc/roles/

        Populates self.role_files with mapping: role_name -> role_content
        """
        # Find roles directory relative to this module
        # This file is in: adc-labs/src/adc/workflows/sequential_workflow.py
        # Roles are in: adc-labs/src/adc/roles/
        module_dir = Path(__file__).parent.parent  # adc-labs/src/adc/
        roles_dir = module_dir / "roles"

        if not roles_dir.exists():
            print(f"  [Warning] Roles directory not found: {roles_dir}")
            return

        # Map agent names to role file names
        role_mapping = {
            "@adc-contract-writer": "contract_writer.md",
            "@adc-compliance-auditor": "auditor.md",
            "@adc-contract-refiner": "refiner.md",
            "@adc-code-generator": "code_generator.md",
            "@adc-system-evaluator": "system_evaluator.md",
            "@adc-pr-orchestrator": "pr_orchestrator.md",
        }

        for agent_name, role_file in role_mapping.items():
            role_path = roles_dir / role_file
            if role_path.exists():
                try:
                    self.role_files[agent_name] = role_path.read_text()
                except Exception as e:
                    print(f"  [Warning] Failed to load {role_file}: {e}")
            else:
                print(f"  [Warning] Role file not found: {role_path}")

    def load_contracts_summary(self) -> str:
        """Load contracts once, create summary (saves 90K tokens per agent).

        ADC-IMPLEMENTS: <sequential-workflow-algorithm-02>

        Returns:
            Summarized contract content (10K tokens instead of 100K)
        """
        contracts_dir = self.workspace / "contracts"
        if not contracts_dir.exists():
            return ""

        # Read all contracts (support both .qmd and .adc extensions)
        contracts = []
        for contract_file in list(contracts_dir.glob("**/*.qmd")) + list(contracts_dir.glob("**/*.adc")):
            with open(contract_file) as f:
                content = f.read()
                contracts.append({
                    "file": str(contract_file.name),
                    "content": content
                })

        # Create summary (simplified version - in production use context_summarizer.py)
        summary_lines = [
            f"# Contracts Summary ({len(contracts)} contracts)",
            "",
            f"Workspace: {self.workspace}",
            "",
        ]

        for contract in contracts:
            # Extract just the YAML frontmatter and first few sections
            lines = contract["content"].split("\n")
            # Take first 50 lines as a simple summary
            summary_lines.append(f"## {contract['file']}")
            summary_lines.extend(lines[:50])
            summary_lines.append("")

        self.contracts_summary = "\n".join(summary_lines)
        return self.contracts_summary

    def _get_model_id(self, model_name: str) -> str:
        """Map model nickname to full model ID.

        Args:
            model_name: "haiku" or "sonnet"

        Returns:
            Full model ID for Anthropic API
        """
        model_map = {
            "haiku": "claude-3-5-haiku-20241022",
            "sonnet": "claude-sonnet-4-5-20250929",
        }
        return model_map.get(model_name, "claude-sonnet-4-5-20250929")

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to workspace.

        Args:
            path: Absolute or relative path

        Returns:
            Absolute Path object
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.workspace / p).resolve()

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a workspace tool and return result.

        Args:
            tool_name: Name of tool to execute
            tool_input: Tool parameters

        Returns:
            JSON string with tool result
        """
        try:
            if tool_name == "read_file":
                file_path = self._resolve_path(tool_input["file_path"])
                if not file_path.exists():
                    return json.dumps({"error": f"File not found: {file_path}"})
                content = file_path.read_text()
                return json.dumps({"content": content})

            elif tool_name == "write_file":
                file_path = self._resolve_path(tool_input["file_path"])
                content = tool_input["content"]
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)
                return json.dumps({"success": True, "path": str(file_path)})

            elif tool_name == "edit_file":
                file_path = self._resolve_path(tool_input["file_path"])
                if not file_path.exists():
                    return json.dumps({"error": f"File not found: {file_path}"})

                content = file_path.read_text()
                old_string = tool_input["old_string"]
                new_string = tool_input["new_string"]

                if old_string not in content:
                    return json.dumps({"error": f"String not found in file: {old_string[:100]}..."})

                new_content = content.replace(old_string, new_string, 1)
                file_path.write_text(new_content)
                return json.dumps({"success": True, "path": str(file_path)})

            elif tool_name == "run_bash":
                command = tool_input["command"]
                timeout = tool_input.get("timeout", 60)

                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(self.workspace),
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                return json.dumps({
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                })

            elif tool_name == "list_directory":
                directory = tool_input.get("directory", ".")
                dir_path = self._resolve_path(directory)

                if not dir_path.exists():
                    return json.dumps({"error": f"Directory not found: {dir_path}"})

                entries = []
                for item in dir_path.iterdir():
                    entries.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file"
                    })

                return json.dumps({"entries": entries})

            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})

        except subprocess.TimeoutExpired:
            return json.dumps({"error": "Command timed out"})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from response, handling markdown code blocks and mixed content.

        This method implements a multi-strategy JSON extraction approach:
        1. Try direct json.loads() (fastest path for clean JSON)
        2. Extract from markdown code blocks (```json ... ```)
        3. Find raw JSON object in text ({ ... })

        Args:
            response: Raw response string that may contain JSON

        Returns:
            Parsed JSON dict if found, None if extraction failed
        """
        import re

        # Strategy 1: Try direct parsing (clean JSON)
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        # Pattern: ```json ... ``` or ```\n{...}\n```
        json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(json_block_pattern, response)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # Strategy 3: Find raw JSON object (look for outermost { ... })
        # This handles cases where JSON appears after text
        # Use a more robust approach: find first { and last }
        first_brace = response.find('{')
        last_brace = response.rfind('}')

        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                json_str = response[first_brace:last_brace + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # No valid JSON found
        return None

    def _parse_json_list(self, response: str) -> Optional[List[str]]:
        """Parse JSON array from agent response.

        Handles markdown code blocks and mixed content.

        Args:
            response: Agent response that may contain JSON array

        Returns:
            List of strings if found, None if extraction failed
        """
        import re

        # Strategy 1: Try direct parsing as array
        try:
            data = json.loads(response.strip())
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        json_block_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
        matches = re.findall(json_block_pattern, response)

        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                continue

        # Strategy 3: Find raw JSON array (look for [ ... ])
        first_bracket = response.find('[')
        last_bracket = response.rfind(']')

        if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
            try:
                json_str = response[first_bracket:last_bracket + 1]
                data = json.loads(json_str)
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        # Strategy 4: Try extracting from dict with "items" key
        data = self._extract_json_from_response(response)
        if isinstance(data, dict) and "items" in data:
            items = data["items"]
            if isinstance(items, list):
                return items

        # No valid JSON array found
        return None

    def _list_workspace_files(self) -> str:
        """List all files in workspace for context building.

        Returns:
            Formatted string with file tree structure
        """
        files = []
        for path in self.workspace.rglob("*"):
            if path.is_file() and not path.name.startswith("."):
                rel_path = path.relative_to(self.workspace)
                files.append(str(rel_path))

        files.sort()
        if not files:
            return "  (no files yet)"
        return "\n".join(f"  - {f}" for f in files)

    def _create_stub_from_parity(self, contract_path: Path) -> List[str]:
        """Create stub files from contract parity section.

        ADC-036: Contract-writer creates stub files that code generator completes.

        Args:
            contract_path: Path to .qmd contract file

        Returns:
            List of created stub file paths
        """
        import re

        created_files = []

        # Read contract content
        try:
            content = contract_path.read_text()
        except Exception as e:
            print(f"    [Warning] Failed to read {contract_path}: {e}")
            return created_files

        # Find parity sections: look for "## Parity" or "### Parity"
        # Split content by headings and filter for parity sections
        # This is more reliable than complex regex
        sections = re.split(r'\n(#{1,3}\s+.*?)\n', content)

        parity_matches = []
        for i in range(1, len(sections), 2):
            heading = sections[i]
            section_content = sections[i+1] if i+1 < len(sections) else ""

            # Check if this is a parity section
            if re.search(r'Parity', heading, re.IGNORECASE):
                # Combine heading and content
                full_section = heading + "\n" + section_content
                parity_matches.append(full_section)

        if not parity_matches:
            return created_files

        for parity_section in parity_matches:
            # Extract file path: look for "**File:** `path/to/file.py`"
            file_match = re.search(r'\*\*File:\*\*\s+`([^`]+)`', parity_section)
            if not file_match:
                continue

            file_path = file_match.group(1)
            target_path = self.workspace / file_path

            # Skip if file already exists
            if target_path.exists():
                continue

            # Extract ADC-IMPLEMENTS markers
            implements_pattern = r'`(ADC-IMPLEMENTS:\s+[^`]+)`'
            implements = re.findall(implements_pattern, parity_section)

            if not implements:
                continue

            # Create stub file
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate stub content
            stub_lines = [
                f"# {implements[0]}",
                f'"""Stub implementation for {file_path}',
                "",
                "This file was auto-generated from contract parity sections.",
                "Complete the implementations below.",
                '"""',
                "",
            ]

            # Add more implements markers if present
            for impl in implements[1:]:
                stub_lines.append(f"# {impl}")
                stub_lines.append("# TODO: Implement this component")
                stub_lines.append("")

            try:
                target_path.write_text("\n".join(stub_lines))
                created_files.append(file_path)
                print(f"    [Stub] Created {file_path}")
            except Exception as e:
                print(f"    [Warning] Failed to create stub {file_path}: {e}")

        return created_files

    def _parse_file_list_from_audit(self, audit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract files needing implementation from audit data.

        Args:
            audit_data: Parsed JSON from auditor response

        Returns:
            List of dicts with 'path' and 'issues' keys
        """
        import re

        files_map = {}  # path -> list of issues

        implementation_issues = audit_data.get("implementation_issues", [])

        for issue in implementation_issues:
            # Extract file path from issue string
            # Format: "Missing X in src/main.py:15"
            # or: "Function signature in src/models.py:20 does not match"
            match = re.search(r'(?:in|at)\s+(\S+\.py)', issue)
            if match:
                file_path = match.group(1)
                if file_path not in files_map:
                    files_map[file_path] = []
                files_map[file_path].append(issue)

        # Convert to list of dicts
        files_list = [
            {"path": path, "issues": issues}
            for path, issues in files_map.items()
        ]

        return files_list

    def invoke_agent(
        self,
        agent_role: str,
        prompt: str,
        workspace: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Invoke agent with minimal context using Anthropic API with tool use and prompt caching.

        This method implements a tool execution loop:
        1. Send prompt to agent with available tools
        2. If agent uses tools, execute them in workspace
        3. Send tool results back to agent
        4. Repeat until agent returns final text response

        Args:
            agent_role: Name of the role (e.g., "@adc-compliance-auditor")
            prompt: Prompt to send to agent
            workspace: Workspace directory (defaults to self.workspace)

        Returns:
            Dict with agent response and metadata including cache metrics
        """
        if workspace is None:
            workspace = self.workspace

        # Get model for this agent (defaults to sonnet if not specified)
        model_name = self.agent_models.get(agent_role, "sonnet")
        model_id = self._get_model_id(model_name)

        # Build system prompt with role definition and cache control
        system_blocks = []

        # Add role file content if available (from framework directory)
        if agent_role in self.role_files:
            system_blocks.append({
                "type": "text",
                "text": self.role_files[agent_role],
                "cache_control": {"type": "ephemeral"}  # Cache role definitions
            })
        else:
            # Fallback: generic agent description
            system_blocks.append({
                "type": "text",
                "text": f"You are {agent_role}, an expert AI agent in the ADC (Agent Design Contracts) workflow.",
            })

        # Add contracts summary with cache control if available
        if self.contracts_summary:
            system_blocks.append({
                "type": "text",
                "text": f"## Contracts Context\n\n{self.contracts_summary}",
                "cache_control": {"type": "ephemeral"}  # Enable caching!
            })

        # Add workspace context
        system_blocks.append({
            "type": "text",
            "text": f"## Workspace\n\nWorking directory: {workspace}\n\nUse the provided tools to read files, write files, edit files, run commands, and list directories. All file paths can be relative to the workspace or absolute.",
        })

        # Initialize conversation history
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Track cumulative token usage
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_creation_tokens = 0
        total_cache_read_tokens = 0

        start_time = time.time()
        max_iterations = 30  # Allow more tools for complex single-file operations (ADC-035)
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1

                # Call API with tools
                # Set max_tokens based on model capabilities
                # Haiku: 8192 max, Sonnet: 16000 max
                max_output_tokens = 8000 if "haiku" in model_id.lower() else 16000

                response = self.client.messages.create(
                    model=model_id,
                    max_tokens=max_output_tokens,
                    system=system_blocks,
                    tools=WORKSPACE_TOOLS,
                    messages=messages
                )

                # Track token usage
                usage = response.usage
                total_input_tokens += usage.input_tokens
                total_output_tokens += usage.output_tokens
                total_cache_creation_tokens += getattr(usage, "cache_creation_input_tokens", 0)
                total_cache_read_tokens += getattr(usage, "cache_read_input_tokens", 0)

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Agent finished - extract final text response
                    response_text = ""
                    for block in response.content:
                        if block.type == "text":
                            response_text += block.text

                    duration = time.time() - start_time
                    return {
                        "success": True,
                        "response": response_text,
                        "tokens_used": total_input_tokens + total_output_tokens,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "cache_creation_tokens": total_cache_creation_tokens,
                        "cache_read_tokens": total_cache_read_tokens,
                        "duration": duration,
                        "error": None
                    }

                elif response.stop_reason == "tool_use":
                    # Agent wants to use tools - execute them
                    tool_results = []

                    # Add assistant message to conversation
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })

                    # Execute each tool use
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            tool_use_id = block.id

                            print(f"      [Tool] {tool_name}({', '.join(f'{k}={v[:50] if isinstance(v, str) else v}...' if isinstance(v, str) and len(v) > 50 else f'{k}={v}' for k, v in tool_input.items())})")

                            # Execute tool
                            result = self._execute_tool(tool_name, tool_input)

                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result
                            })

                    # Send tool results back to agent
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })

                else:
                    # Unexpected stop reason
                    duration = time.time() - start_time
                    return {
                        "success": False,
                        "response": "",
                        "tokens_used": total_input_tokens + total_output_tokens,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "cache_creation_tokens": total_cache_creation_tokens,
                        "cache_read_tokens": total_cache_read_tokens,
                        "duration": duration,
                        "error": f"Unexpected stop reason: {response.stop_reason}"
                    }

            # Max iterations reached
            duration = time.time() - start_time
            return {
                "success": False,
                "response": "",
                "tokens_used": total_input_tokens + total_output_tokens,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_creation_tokens": total_cache_creation_tokens,
                "cache_read_tokens": total_cache_read_tokens,
                "duration": duration,
                "error": f"Max tool use iterations ({max_iterations}) reached"
            }

        except anthropic.APITimeoutError:
            return {
                "success": False,
                "response": "",
                "tokens_used": total_input_tokens + total_output_tokens,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_creation_tokens": total_cache_creation_tokens,
                "cache_read_tokens": total_cache_read_tokens,
                "duration": time.time() - start_time,
                "error": "API request timed out"
            }
        except anthropic.APIError as e:
            return {
                "success": False,
                "response": "",
                "tokens_used": total_input_tokens + total_output_tokens,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_creation_tokens": total_cache_creation_tokens,
                "cache_read_tokens": total_cache_read_tokens,
                "duration": time.time() - start_time,
                "error": f"API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "tokens_used": total_input_tokens + total_output_tokens,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "cache_creation_tokens": total_cache_creation_tokens,
                "cache_read_tokens": total_cache_read_tokens,
                "duration": time.time() - start_time,
                "error": str(e)
            }

    def inner_loop(self, state: WorkflowState) -> float:
        """Auditor ↔ Code Generator loop until compliance >= 0.8.

        ADC-IMPLEMENTS: <sequential-workflow-algorithm-01>

        Args:
            state: Current workflow state

        Returns:
            Final compliance score
        """
        state.inner_loop_active = True

        while True:
            # Invoke Auditor
            print(f"  [Auditor] Running compliance audit (iteration {state.inner_iteration})...")
            audit_prompt = f"""Audit the implementation against contracts in workspace: {self.workspace}

CRITICAL OUTPUT REQUIREMENT:
Your response MUST be ONLY valid JSON. No explanatory text, preamble, or markdown formatting.
Do NOT wrap in markdown code blocks. Do NOT add comments or explanations before/after JSON.
Return ONLY the raw JSON object as specified below.

If you cannot complete the audit due to errors, return:
{{"compliance_score": 0.0, "error": "explanation of what went wrong"}}

Contracts Summary:
{self.contracts_summary}

## MULTI-PHASE COMPLIANCE AUDIT

You must perform this audit in THREE distinct phases and report results separately:

### PHASE 1: Implementation Discovery (40% weight)
1. Use list_directory tool to explore workspace structure
2. Look for implementation files in these locations:
   - src/ directory (most common)
   - Root workspace directory (*.py files)
   - build/ directory (if exists)
3. Check if expected files from contract Parity sections exist
4. Score:
   - All expected files exist: 40 points
   - Some files exist: 20 points
   - No files exist: 0 points

### PHASE 2: Marker Verification (40% weight)
1. Use read_file tool to check each Python file for ADC-IMPLEMENTS markers
2. ADC-IMPLEMENTS markers should appear as comments like:
   - # ADC-IMPLEMENTS: <contract-id>
   - # ADC-IMPLEMENTS: contract_name.adc
   - # @contract_name: some_contract
3. Count total classes/functions vs. those with markers
4. Score:
   - 90-100% of items have markers: 40 points
   - 70-89% have markers: 30 points
   - 50-69% have markers: 20 points
   - <50% have markers: 10 points

### PHASE 3: Implementation Quality (20% weight)
1. Check if implementation structure matches contract specifications
2. Identify actual implementation issues (wrong logic, missing functions)
3. **CRITICAL**: Distinguish between:
   - **Environment Issues**: Import errors, missing dependencies, path issues
   - **Implementation Issues**: Wrong logic, missing required methods, incorrect structure
4. Score:
   - No implementation issues: 20 points
   - Minor issues: 15 points
   - Major issues: 5 points
   - Critical issues: 0 points

## IMPORTANT: Environment vs. Implementation Issues

**Environment Issues (DON'T penalize compliance):**
- ModuleNotFoundError for correctly named modules
- Import path errors where the module file exists
- Missing external dependencies (can be fixed with pip install)
- Database connection errors (environment configuration)

**Implementation Issues (DO penalize compliance):**
- Missing required functions/classes specified in contract
- Incorrect function signatures
- Wrong logic that doesn't match contract specifications
- Missing ADC-IMPLEMENTS markers on existing code

## JSON Response Format

Return compliance score (0.0-1.0) and detailed breakdown in JSON format:
{{
  "compliance_score": 0.85,
  "phase_scores": {{
    "implementation_discovery": 40,
    "marker_verification": 35,
    "implementation_quality": 15
  }},
  "files_checked": ["src/main.py", "src/models.py"],
  "implementation_exists": true,
  "markers_present": 12,
  "markers_missing": 3,
  "total_items": 15,
  "environment_issues": [
    "ModuleNotFoundError: No module named 'task_api' in tests/test_api.py - this is likely a PYTHONPATH issue, not an implementation issue"
  ],
  "implementation_issues": [
    "Missing ADC-IMPLEMENTS marker in src/main.py:15 (function create_app)",
    "Function signature in src/models.py:20 does not match contract specification"
  ],
  "compliant_items": 12,
  "total_items": 15
}}

**If you find NO Python files in the workspace:**
Set compliance_score to 0.0 and phase_scores to all zeros.

**Calculate final compliance_score:**
compliance_score = (phase_scores.implementation_discovery + phase_scores.marker_verification + phase_scores.implementation_quality) / 100.0
"""

            audit_result = self.invoke_agent(
                "@adc-compliance-auditor",
                audit_prompt
            )

            if not audit_result["success"]:
                print(f"    ERROR: Auditor failed: {audit_result['error']}")
                return state.compliance_score

            # Parse audit result with JSON extraction fallback
            audit_data = self._extract_json_from_response(audit_result["response"])

            if audit_data is not None:
                # Successfully extracted JSON
                compliance = audit_data.get("compliance_score", 0.0)

                # Extract phase scores for debugging
                phase_scores = audit_data.get("phase_scores", {})
                implementation_exists = audit_data.get("implementation_exists", False)
                markers_present = audit_data.get("markers_present", 0)
                markers_missing = audit_data.get("markers_missing", 0)

                # Separate environment issues from implementation issues
                environment_issues = audit_data.get("environment_issues", [])
                implementation_issues = audit_data.get("implementation_issues", [])

                # Legacy support for "violations" field (backward compatibility)
                violations = audit_data.get("violations", implementation_issues)
                if not implementation_issues and violations:
                    implementation_issues = violations

                files_checked = audit_data.get("files_checked", [])
                compliant_items = audit_data.get("compliant_items", 0)
                total_items = audit_data.get("total_items", 0)

                # Log detailed audit results
                print(f"    Implementation exists: {implementation_exists}")
                print(f"    Files checked: {len(files_checked)}")
                if files_checked:
                    print(f"      {', '.join(files_checked[:5])}{' ...' if len(files_checked) > 5 else ''}")
                print(f"    Markers: {markers_present}/{total_items} present, {markers_missing} missing")
                print(f"    Phase scores: Discovery={phase_scores.get('implementation_discovery', 'N/A')}, Markers={phase_scores.get('marker_verification', 'N/A')}, Quality={phase_scores.get('implementation_quality', 'N/A')}")
                print(f"    Environment issues: {len(environment_issues)}")
                print(f"    Implementation issues: {len(implementation_issues)}")

            else:
                # JSON extraction failed - provide detailed diagnostics
                print(f"    [Error] Failed to extract JSON from auditor response")
                print(f"    Response length: {len(audit_result['response'])} characters")
                print(f"    Response preview (first 300 chars):")
                print(f"    {audit_result['response'][:300]}")
                if len(audit_result['response']) > 300:
                    print(f"    Response preview (last 100 chars):")
                    print(f"    ...{audit_result['response'][-100:]}")

                # Check for common failure patterns
                response_lower = audit_result['response'].lower()
                if 'json' in response_lower and '```' in audit_result['response']:
                    print(f"    [Hint] Response contains markdown code blocks - extraction should have worked")
                    print(f"    [Hint] This might be a malformed JSON structure inside the code block")
                elif '{' not in audit_result['response']:
                    print(f"    [Hint] Response contains no JSON objects - auditor may have returned error message")
                else:
                    print(f"    [Hint] Response contains braces but JSON is malformed")

                # Keep previous score, mark as extraction failure
                compliance = state.compliance_score
                violations = []
                implementation_issues = []
                environment_issues = []
                files_checked = []
                implementation_exists = False
                markers_present = 0
                markers_missing = 0
                phase_scores = {}

            state.compliance_score = compliance
            state.last_violations = implementation_issues  # Only track implementation issues
            state.record_phase(
                "auditor",
                audit_result["tokens_used"],
                f"Compliance: {compliance:.1%}",
                input_tokens=audit_result.get("input_tokens", 0),
                output_tokens=audit_result.get("output_tokens", 0),
                cache_creation_tokens=audit_result.get("cache_creation_tokens", 0),
                cache_read_tokens=audit_result.get("cache_read_tokens", 0)
            )

            self.progress.add_score(compliance)
            print(f"    Compliance: {compliance:.1%}")

            # Show environment issues (informational, not compliance-blocking)
            if environment_issues:
                print(f"    Environment issues ({len(environment_issues)}) [informational]:")
                for issue in environment_issues[:3]:
                    print(f"      - {issue}")
                if len(environment_issues) > 3:
                    print(f"      ... and {len(environment_issues) - 3} more")

            # Show implementation issues (these need to be fixed)
            if implementation_issues:
                print(f"    Implementation issues ({len(implementation_issues)}) [must fix]:")
                for issue in implementation_issues[:3]:
                    print(f"      - {issue}")
                if len(implementation_issues) > 3:
                    print(f"      ... and {len(implementation_issues) - 3} more")

            # Save detailed audit report for debugging
            audit_report_path = self.workspace / f".audit_report_{state.outer_iteration}_{state.inner_iteration}.json"
            try:
                with open(audit_report_path, "w") as f:
                    json.dump({
                        "iteration": {"outer": state.outer_iteration, "inner": state.inner_iteration},
                        "compliance_score": compliance,
                        "phase_scores": phase_scores,
                        "implementation_exists": implementation_exists,
                        "markers_present": markers_present,
                        "markers_missing": markers_missing,
                        "files_checked": files_checked,
                        "environment_issues": environment_issues,
                        "implementation_issues": implementation_issues,
                        "violations": violations,  # Legacy field for backward compatibility
                        "compliant_items": compliant_items,
                        "total_items": total_items,
                        "raw_response": audit_result["response"]
                    }, f, indent=2)
            except Exception as e:
                print(f"    [Warning] Failed to save audit report: {e}")

            # Check for stagnation
            if self.progress.is_stuck():
                print("    STOP: No progress detected in 2 consecutive runs")
                state.inner_loop_active = False
                return compliance

            # Exit if compliant
            if compliance >= 0.8:
                print(f"    SUCCESS: Compliance threshold met ({compliance:.1%})")
                state.inner_loop_active = False
                return compliance

            # Check max iterations
            if state.inner_iteration >= state.max_inner:
                print(f"    STOP: Max inner iterations ({state.max_inner}) reached")
                state.inner_loop_active = False
                return compliance

            # Generate code to fix implementation issues (not environment issues)
            print(f"  [Code Generator] Fixing implementation issues...")

            # ADC-035: Self-inner-loop pattern for code generation
            # Parse file list from audit data
            files_to_fix = self._parse_file_list_from_audit(audit_data)

            # Include environment issues as context (don't fix them, just be aware)
            env_context = ""
            if environment_issues:
                env_context = f"""

NOTE: The following environment issues were detected but DO NOT need code changes:
{chr(10).join(f"- {issue}" for issue in environment_issues[:3])}

These are PYTHONPATH, import path, or dependency issues that will be resolved separately.
Focus ONLY on fixing the implementation issues listed above.
"""

            # ADC-036: If no files from audit, check if stub files exist from contract-writer
            print(f"    [DEBUG] files_to_fix before stub check: {len(files_to_fix) if files_to_fix else 0} items")
            if not files_to_fix:
                # Find .py files, excluding framework/infrastructure directories (NOT tests - those need code!)
                excluded_dirs = {"contracts", ".venv", "__pycache__", ".git", ".adc"}
                stub_files = [
                    f for f in self.workspace.rglob("*.py")
                    if f.is_file()
                    and not f.name.startswith(".")
                    and not any(part in excluded_dirs for part in f.relative_to(self.workspace).parts)
                ]
                print(f"    [DEBUG] Found {len(stub_files)} .py files in workspace (after excluding {excluded_dirs})")

                if stub_files:
                    print(f"    [Stubs] Found {len(stub_files)} stub files to complete...")
                    # Convert to files_to_fix format
                    files_to_fix = [
                        {"path": str(f.relative_to(self.workspace)), "issues": ["Complete stub implementation"]}
                        for f in stub_files
                    ]
                    print(f"    [DEBUG] files_to_fix after conversion: {len(files_to_fix)} items, truthy={bool(files_to_fix)}")
                    # Fall through to self-loop processing below

            # Process files with self-loop pattern (either from audit or stubs)
            print(f"    [DEBUG] Checking if files_to_fix for self-loop: {len(files_to_fix) if files_to_fix else 0} items, truthy={bool(files_to_fix)}")
            if files_to_fix:
                # Self-loop: Generate each file separately with fresh tool budget
                print(f"    [Self-Loop] Processing {len(files_to_fix)} files separately...")

                files_processed = 0
                for file_info in files_to_fix:
                    file_path = file_info["path"]
                    file_issues = file_info["issues"]

                    print(f"      [Generating] {file_path} ({len(file_issues)} issues)...")

                    # Get current workspace context
                    workspace_context = self._list_workspace_files()

                    # Check if this is a stub file completion
                    is_stub = file_issues == ["Complete stub implementation"]

                    file_prompt = f"""{"Complete stub file" if is_stub else "Generate/fix"} ONLY {file_path}.

Contracts Summary:
{self.contracts_summary}

Existing workspace files:
{workspace_context}

Requirements for THIS FILE ONLY:
{chr(10).join(f"- {issue}" for issue in file_issues)}
{env_context}

IMPORTANT CONSTRAINTS:
- Focus ONLY on {file_path}
{"- The file already exists as a stub with ADC-IMPLEMENTS markers - complete the implementations" if is_stub else "- Add ADC-IMPLEMENTS markers before each class/function"}
- Follow contract specifications exactly
- Maintain existing functionality in this file
- DO NOT modify other files (they will be processed separately)
- DO NOT try to fix import errors or environment issues
"""

                    codegen_result = self.invoke_agent(
                        "@adc-code-generator",
                        file_prompt
                    )

                    if not codegen_result["success"]:
                        print(f"        [Error] Failed to generate {file_path}: {codegen_result['error']}")
                        # Continue with other files instead of failing completely
                        continue

                    files_processed += 1
                    state.record_phase(
                        "code_generator",
                        codegen_result["tokens_used"],
                        f"Generated {file_path}",
                        input_tokens=codegen_result.get("input_tokens", 0),
                        output_tokens=codegen_result.get("output_tokens", 0),
                        cache_creation_tokens=codegen_result.get("cache_creation_tokens", 0),
                        cache_read_tokens=codegen_result.get("cache_read_tokens", 0)
                    )

                print(f"    [Success] Processed {files_processed}/{len(files_to_fix)} files")

                # If no files were processed successfully, stop
                if files_processed == 0:
                    print(f"    ERROR: Failed to process any files")
                    state.inner_loop_active = False
                    return compliance

            else:
                # Fallback: global fix if no specific files or stubs identified
                print("    [Fallback] No specific files or stubs identified, using global approach...")
                issues_summary = "\n".join(f"- {issue}" for issue in implementation_issues[:10])

                codegen_prompt = f"""Fix contract compliance implementation issues.

Contracts Summary:
{self.contracts_summary}

Implementation issues to fix:
{issues_summary}
{env_context}

Requirements:
- Add ADC-IMPLEMENTS markers before each class/function
- Follow contract specifications exactly
- Maintain existing functionality
- DO NOT try to fix import errors or environment issues (those will be resolved separately)
"""

                codegen_result = self.invoke_agent(
                    "@adc-code-generator",
                    codegen_prompt
                )

                if not codegen_result["success"]:
                    print(f"    ERROR: Code generator failed: {codegen_result['error']}")
                    state.inner_loop_active = False
                    return compliance

                state.record_phase(
                    "code_generator",
                    codegen_result["tokens_used"],
                    f"Fixed {len(implementation_issues)} implementation issues",
                    input_tokens=codegen_result.get("input_tokens", 0),
                    output_tokens=codegen_result.get("output_tokens", 0),
                    cache_creation_tokens=codegen_result.get("cache_creation_tokens", 0),
                    cache_read_tokens=codegen_result.get("cache_read_tokens", 0)
                )

            state.inner_iteration += 1
            # Loop back to auditor

    def outer_loop(self, state: WorkflowState) -> WorkflowResult:
        """Main workflow loop with contract refinement.

        ADC-IMPLEMENTS: <sequential-workflow-algorithm-01>

        Args:
            state: Workflow state

        Returns:
            WorkflowResult with final state and outcome
        """
        # Initial contract creation if needed
        contracts_dir = self.workspace / "contracts"
        # Check for both .qmd and .adc contract files
        existing_contracts = list(contracts_dir.glob("**/*.qmd")) + list(contracts_dir.glob("**/*.adc")) if contracts_dir.exists() else []
        if not contracts_dir.exists() or not existing_contracts:
            print("[Contract Writer] Creating initial contracts...")

            # ADC-035: Self-inner-loop pattern for contract creation
            # Phase 1: Planning - get list of contracts needed
            planning_prompt = f"""Analyze this task and output ONLY a JSON array of contract names needed.

Task: {state.task_description}

Output ONLY a JSON array like: ["main", "database", "testing"]

Requirements:
- Create 1-3 focused contract names (no file extensions)
- DO NOT create documentation contracts (README, INDEX, SUMMARY, MANIFEST, VERIFICATION)
- Contract names should be descriptive but concise (e.g., "main", "api", "database", "testing")

Output ONLY the JSON array. No explanations, no markdown, just the array.
"""

            print("  [Planning] Determining contracts needed...")
            planning_result = self.invoke_agent("@adc-contract-writer", planning_prompt)

            contracts_needed = None
            if planning_result["success"]:
                contracts_needed = self._parse_json_list(planning_result["response"])

            # Fallback if planning fails
            if not contracts_needed:
                print("  [Warning] Planning phase failed, using default contract list: ['main']")
                contracts_needed = ["main"]
            else:
                print(f"  [Planning] Contracts to create: {contracts_needed}")

            state.record_phase(
                "contract_writer_planning",
                planning_result.get("tokens_used", 0),
                f"Planned {len(contracts_needed)} contracts",
                input_tokens=planning_result.get("input_tokens", 0),
                output_tokens=planning_result.get("output_tokens", 0),
                cache_creation_tokens=planning_result.get("cache_creation_tokens", 0),
                cache_read_tokens=planning_result.get("cache_read_tokens", 0)
            )

            # Phase 2: Execution - create each contract in separate invocation
            contracts_created = 0
            for contract_name in contracts_needed:
                print(f"  [Writing] Creating contract: {contract_name}.qmd...")

                # Get current workspace context
                workspace_context = self._list_workspace_files()

                writer_prompt = f"""Write ONLY the '{contract_name}.qmd' contract for this task.

Task: {state.task_description}

Existing workspace files:
{workspace_context}

Other contracts that exist/will be created: {contracts_needed}

IMPORTANT CONSTRAINTS:
- Focus ONLY on writing {contract_name}.qmd
- DO NOT write other contracts (they will be created separately)
- Keep contract concise (200-500 lines)
- Follow ADC schema with YAML frontmatter
- Save to contracts/{contract_name}.qmd

CRITICAL REQUIREMENT - Parity Section:
You MUST include a Parity section specifying which files will implement this contract.

Example format:
```markdown
## Parity

This contract is implemented by the following files:

**File:** `src/models.py`
- Task data models
- `ADC-IMPLEMENTS: {contract_name}.data_model`

**File:** `src/api.py`
- API implementation
- `ADC-IMPLEMENTS: {contract_name}.api_routes`

**File:** `tests/test_{contract_name}.py`
- Test suite
- `ADC-IMPLEMENTS: {contract_name}.testing`
```

File Path Requirements:
- Use backticks: **File:** `src/filename.py`
- Paths relative to workspace root
- Include file extensions
- One **File:** entry per implementation file
- List ADC-IMPLEMENTS markers for each file

Without a proper Parity section, stub file creation will fail and code generators won't know which files to create.

Include all required sections for THIS contract only.
"""

                # Retry logic for contract writer (handles API timeouts)
                max_retries = 3
                retry_delay = 5  # seconds
                writer_result = None

                for attempt in range(max_retries):
                    if attempt > 0:
                        print(f"    [Retry {attempt}/{max_retries}] Retrying after {retry_delay}s delay...")
                        time.sleep(retry_delay)

                    writer_result = self.invoke_agent(
                        "@adc-contract-writer",
                        writer_prompt
                    )

                    if writer_result["success"]:
                        break

                    error_msg = writer_result.get("error", "unknown")
                    print(f"    [Warning] Attempt {attempt + 1} failed: {error_msg}")

                    # If it's not a timeout, don't retry
                    if "timeout" not in error_msg.lower():
                        break

                if not writer_result["success"]:
                    print(f"    [Error] Failed to create {contract_name}.qmd: {writer_result.get('error', 'unknown')}")
                    # Continue with other contracts instead of failing completely
                    continue

                contracts_created += 1
                state.record_phase(
                    "contract_writer",
                    writer_result["tokens_used"],
                    f"Created {contract_name}.qmd",
                    input_tokens=writer_result.get("input_tokens", 0),
                    output_tokens=writer_result.get("output_tokens", 0),
                    cache_creation_tokens=writer_result.get("cache_creation_tokens", 0),
                    cache_read_tokens=writer_result.get("cache_read_tokens", 0)
                )

            # Check if at least one contract was created
            if contracts_created == 0:
                return WorkflowResult(
                    status="failed",
                    reason="contract_writer_failed",
                    final_state=state,
                    total_tokens=state.calculate_total_tokens(),
                    total_cost=state.calculate_total_cost()
                )

            print(f"  [Success] Created {contracts_created}/{len(contracts_needed)} contracts")

            # ADC-036: Create stub files from parity sections
            print("  [Stubs] Generating stub files from parity sections...")
            all_stubs = []
            for contract_name in contracts_needed:
                contract_path = contracts_dir / f"{contract_name}.qmd"
                if contract_path.exists():
                    stubs = self._create_stub_from_parity(contract_path)
                    all_stubs.extend(stubs)

            if all_stubs:
                print(f"  [Stubs] Created {len(all_stubs)} stub files: {', '.join(all_stubs)}")
            else:
                print("  [Stubs] No stub files created (parity sections may not specify files)")

        # Load contracts summary once
        print("[Setup] Loading contracts summary...")
        self.load_contracts_summary()

        # OUTER LOOP: Refinement Loop
        while state.outer_iteration < state.max_outer:
            print(f"\n=== OUTER LOOP ITERATION {state.outer_iteration + 1}/{state.max_outer} ===")

            # Reset inner loop progress
            self.progress = ProgressTracker()
            state.inner_iteration = 0

            # INNER LOOP: Auditor ↔ Code Generator
            print("\n--- INNER LOOP: Implementation Refinement ---")
            compliance = self.inner_loop(state)

            # Check if we should stop
            if compliance < 0.8:
                return WorkflowResult(
                    status="failed",
                    reason="max_inner_iterations_reached",
                    final_state=state,
                    total_tokens=state.calculate_total_tokens(),
                    total_cost=state.calculate_total_cost()
                )

            # System Evaluator
            print("\n[Evaluator] Running system tests...")
            evaluator_prompt = f"""Evaluate the implementation against contracts.

Contracts Summary:
{self.contracts_summary}

Workspace: {self.workspace}

Requirements:
1. Run all tests (pytest)
2. Check performance constraints
3. Verify feature completeness

Return result in JSON format:
{{
  "satisfied": true/false,
  "failures": ["test failure 1", ...],
  "feedback": "Summary of issues"
}}
"""

            evaluator_result = self.invoke_agent(
                "@adc-system-evaluator",
                evaluator_prompt
            )

            if not evaluator_result["success"]:
                return WorkflowResult(
                    status="failed",
                    reason="evaluator_failed",
                    final_state=state,
                    total_tokens=state.calculate_total_tokens(),
                    total_cost=state.calculate_total_cost()
                )

            # Parse evaluator result
            try:
                eval_data = json.loads(evaluator_result["response"])
                satisfied = eval_data.get("satisfied", False)
                feedback = eval_data.get("feedback", "")
            except (json.JSONDecodeError, AttributeError):
                satisfied = False
                feedback = evaluator_result["response"]

            state.evaluator_satisfied = satisfied
            state.evaluator_feedback = feedback
            state.record_phase(
                "evaluator",
                evaluator_result["tokens_used"],
                f"Satisfied: {satisfied}",
                input_tokens=evaluator_result.get("input_tokens", 0),
                output_tokens=evaluator_result.get("output_tokens", 0),
                cache_creation_tokens=evaluator_result.get("cache_creation_tokens", 0),
                cache_read_tokens=evaluator_result.get("cache_read_tokens", 0)
            )

            # Decision Point: Are tests passing?
            if satisfied:
                # SUCCESS PATH: Create PR
                print("\n[PR Orchestrator] Creating pull request...")
                pr_result = self.invoke_agent(
                    "@adc-pr-orchestrator",
                    "Create pull request for this implementation."
                )

                state.record_phase(
                    "pr_orchestrator",
                    pr_result.get("tokens_used", 0),
                    "PR created",
                    input_tokens=pr_result.get("input_tokens", 0),
                    output_tokens=pr_result.get("output_tokens", 0),
                    cache_creation_tokens=pr_result.get("cache_creation_tokens", 0),
                    cache_read_tokens=pr_result.get("cache_read_tokens", 0)
                )

                return WorkflowResult(
                    status="success",
                    reason="tests_passed",
                    pr_url=pr_result.get("response", ""),
                    final_state=state,
                    total_tokens=state.calculate_total_tokens(),
                    total_cost=state.calculate_total_cost()
                )

            # FAILURE PATH: Refine contracts and retry
            print("\n[Refiner] Tests failed - refining contracts...")
            refiner_prompt = f"""Refine contracts based on test failures.

Evaluation Feedback:
{feedback}

Update contracts to fix root cause issues.
"""

            refiner_result = self.invoke_agent(
                "@adc-contract-refiner",
                refiner_prompt
            )

            if not refiner_result["success"]:
                return WorkflowResult(
                    status="failed",
                    reason="refiner_failed",
                    final_state=state,
                    total_tokens=state.calculate_total_tokens(),
                    total_cost=state.calculate_total_cost()
                )

            state.record_phase(
                "refiner",
                refiner_result["tokens_used"],
                "Contracts refined",
                input_tokens=refiner_result.get("input_tokens", 0),
                output_tokens=refiner_result.get("output_tokens", 0),
                cache_creation_tokens=refiner_result.get("cache_creation_tokens", 0),
                cache_read_tokens=refiner_result.get("cache_read_tokens", 0)
            )

            # Reload contracts summary
            self.load_contracts_summary()

            state.outer_iteration += 1
            # Loop back to inner loop

        # Max outer iterations reached
        return WorkflowResult(
            status="failed",
            reason="max_outer_iterations_reached",
            final_state=state,
            total_tokens=state.calculate_total_tokens(),
            total_cost=state.calculate_total_cost()
        )

    def run(self, task_description: str) -> WorkflowResult:
        """Execute the sequential ADC workflow.

        Args:
            task_description: Task description

        Returns:
            WorkflowResult with final state and outcome
        """
        start_time = time.time()

        # Initialize state
        state = WorkflowState.from_task(task_description, str(self.workspace))

        print(f"\n{'='*70}")
        print(f"SEQUENTIAL ADC WORKFLOW")
        print(f"{'='*70}")
        print(f"Task: {task_description}")
        print(f"Workspace: {self.workspace}")
        print(f"{'='*70}\n")

        # Execute outer loop
        result = self.outer_loop(state)

        # Add execution time
        result.execution_time_seconds = time.time() - start_time

        # Print summary
        print(f"\n{'='*70}")
        print(f"WORKFLOW COMPLETE")
        print(f"{'='*70}")
        print(f"Status: {result.status}")
        print(f"Reason: {result.reason}")
        print(f"Total Tokens: {result.total_tokens:,}")
        print(f"Total Cost: ${result.total_cost:.2f}")
        print(f"Execution Time: {result.execution_time_seconds:.1f}s")
        print(f"Token Efficiency: {result.token_efficiency_vs_baseline():.1f}% savings vs baseline")
        print(f"Cost Savings: {result.cost_savings_vs_baseline():.1f}% vs baseline")
        print(f"{'='*70}\n")

        return result
