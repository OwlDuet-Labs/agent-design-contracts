# Agent Design Contract (ADC) Schema v1.0

## 1. Overview

An Agent Design Contract (ADC) is a machine-readable design document, written in Markdown, that specifies the architecture and intent of an AI-driven system. An ADC contract serves as the single source of truth for development, enabling automated code generation, auditing, and drift detection by specialized agents used for development.

The rationale for ADC is to:
1. Define a lightweight specification for designs for agentic systems that's easily read and implemented by humans and AI agents.
2. Support agent-based development using any agent, tool, or IDE.
3. Critically, create a single source of truth that supports cross-team collaboration and communication.

An ADC file consists of two parts:
1.  **YAML Front Matter:** Contains structured metadata about the contract.
2.  **Design Blocks:** A series of typed, addressable sections that describe each component of the system.

---

## 2. File Structure

### YAML Front Matter

Every ADC file MUST begin with a YAML front matter block.

```yaml
---
contract_id: module_name-unique-identifier-adc-001
title: "Human-Readable Title of the Contract"
author: "Author Name"
status: "proposed" # proposed | active | deprecated | superseded
version: 1.2
created_date: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"
---
```

### Design Blocks

The body of the contract is composed of "Design Blocks." Each block represents an atomic component of the design and follows a strict format:

**Format:** `### [Type: Name] <ID>`

* **`[Type]`**: The official ADC block type (e.g., `[Agent]`, `[DataModel]`).
* **`Name`**: A human-readable name for the block.
* **`<ID>`**: A stable, globally unique identifier (e.g., `<adc-pipe-agent-01>`). This ID is critical for linking and auditing.

---

## 3. ADC Block Types

The following are the official block types supported by the ADC schema.

### High-Level & Scoping Types

* **`[Rationale: ...]`**: Explains the "why" behind the contract or a major design decision. It provides context for human readers and AI agents.
* **`[Implementation: ...]`**: Provides high-level guidance, notes, or constraints for how the entire contract should be implemented, often specifying libraries or architectural patterns.

### Agentic & Logic Types

* **`[Agent: ...]`**: The core agentic component. Defines an autonomous agent with a specific `Persona` and a `Thinking Process` (algorithm) that dictates its behavior.
* **`[Algorithm: ...]`**: Describes a specific, self-contained piece of logic, a calculation, or a business rule, often using mathematical notation (LaTeX) or structured pseudocode.
* **`[prompt<Name>: ...]`**: Defines a typed, reusable prompt for an LLM. The `<Name>` allows it to be referenced directly from code. The body specifies the prompt's inputs, template, and expected output format.

### Data & Structure Types

* **`[DataModel: ...]`**: Defines a data structure, schema, or class. Supports inheritance notation (e.g., `[DataModel: MyModel(BaseModel)]`) to show relationships. This block is typically translated into a Pydantic model.
* **`[DataTransform: ...]`**: Describes a function or process that converts data from one `DataModel` to another. Specifies inputs, outputs, and the transformation logic.
* **`[Translation: ...]`**: Defines a morphism between two specific `DataModel` types with explicit input/output contracts and bidirectional mapping logic. Requires both source and target data models to be defined elsewhere in the contract.

### System & Requirement Types

* **`[Tool: ...]`**: Describes a tool or service that is used by an agent and provides an interface to the agent.
* **`[Feature: ...]`**: Describes a user-facing capability or a significant system feature, including its configuration and benefits.
* **`[Constraint: ...]`**: Defines a non-functional requirement, boundary condition, or performance gate (e.g., "Response time must be <100ms").
* **`[APIEndpoint: ...]`**: The contract for a service API endpoint, defining the path, method, request/response objects, and error codes.
* **`[TestScenario: ...]`**: Describes a key user story, edge case, or scenario that must be covered by tests.

### Visual & Reference Types

* **`[Diagram: ...]`**: A visual representation of the system architecture or a process flow. MUST use Mermaid.js syntax. Nodes in the diagram should use ADC IDs to be verifiable.
* **`[Reference: ...]`**: A pointer to definitions located in another ADC file, used to link contracts together without duplicating content.

---

## 4. Core Sections within Blocks

### The `Parity` Section

Every implementable Design Block (e.g., `Agent`, `DataModel`, `Feature`) MUST contain a `Parity` section. This creates the explicit, traceable link between design, code, and documentation.

```markdown
**Parity:**
- **Implementation Scope:** `src/pipelines/orchestrator/`
- **Configuration Scope:** `configs/pipelines/`
- **Tests:**
  - `tests/test_pipeline_orchestrator.py`
  - `tests/test_pipeline_e2e.py`
```

### Translation Block Requirements

The `[Translation: ...]` block MUST include:

1. **Source Model Reference**: `**Input:** DataModelName` - references an existing `[DataModel]` block
2. **Target Model Reference**: `**Output:** DataModelName` - references an existing `[DataModel]` block  
3. **Forward Mapping**: Function signature and logic for source → target transformation
4. **Reverse Mapping**: Function signature and logic for target → source transformation (when applicable)
5. **Validation Rules**: Constraints and error handling for invalid transformations
6. **Parity Section**: Implementation scope as with other ADC blocks

**Example:**
```markdown
### [Translation: EventToMetric] <event-metric-translation-01>

**Input:** BehaviorEvent
**Output:** BusinessMetrics

**Forward Mapping:**
```python
def transform_event_to_metrics(event: BehaviorEvent) -> List[BusinessMetrics]:
    # transformation logic
```

**Reverse Mapping:** Not applicable (lossy transformation)

**Validation Rules:**
- Source event must have valid user_id
- Timestamp must be within last 24 hours
- Properties must not exceed 1KB serialized size

**Parity:**
- **Implementation Scope:** `src/core/translations/event_metric.py`
```

### The `ADC-IMPLEMENTS` Marker

To complete the loop from design to code, the `code_generator` agent MUST add a marker in the source code immediately before the class or function that implements a design block. The `auditor` agent uses this marker to verify compliance.

**Format:** `ADC-IMPLEMENTS: <ID>`

**Example (in Python):**

```python
# ADC-IMPLEMENTS: <adc-pipe-agent-01>
class TuningPipelineOrchestrator:
    def run(self):
        # ... implementation of the agent's thinking process
```

---

## 5. File Organization Guidelines

### Project Directory Structure

ADC projects MUST follow this standardized directory structure to ensure consistency across workflows and proper separation of concerns:

```
project-root/
├── contracts/              # Contract specifications only (.md files)
│   ├── ADC_001_SYSTEM_ARCHITECTURE.md
│   ├── ADC_002_DATA_PIPELINE.md
│   └── ADC_003_API_DESIGN.md
│
├── adc_files/             # All ADC workflow artifacts
│   ├── refinement/        # Contract refinement outputs (ephemeral, gitignored)
│   │   ├── ADC_001_REFINEMENT_REPORT.md
│   │   ├── ADC_001_REFINEMENT_SUMMARY.md
│   │   └── ADC_001_REFINEMENT_CHECKLIST.md
│   │
│   ├── compliance/        # Compliance audit reports (committed)
│   │   ├── ADC_001_COMPLIANCE_AUDIT.md
│   │   └── ADC_001_COMPLIANCE_SUMMARY.md
│   │
│   ├── evaluation/        # Evaluation and test results (committed)
│   │   ├── ADC_001_EVALUATION_REPORT.md
│   │   └── ADC_001_TEST_RESULTS.md
│   │
│   ├── implementation/    # Implementation summaries (committed)
│   │   ├── ADC_001_IMPLEMENTATION_SUMMARY.md
│   │   └── ADC_001_DEPLOYMENT_CHECKLIST.md
│   │
│   └── releases/          # PR descriptions and release docs (committed)
│       ├── ADC_001_PR_DESCRIPTION.md
│       └── ADC_001_RELEASE_NOTES.md
│
├── claude_tmp/            # Temporary working files (gitignored)
│   ├── scratch/           # Scratch work and notes
│   ├── debug/             # Debug outputs and logs
│   └── temp_outputs/      # Intermediate processing outputs
│
└── src/                   # Implementation code
    └── ...
```

### File Placement Rules

#### Contracts Directory (`contracts/`)
- **Purpose**: Single source of truth for all contract specifications
- **File Format**: `.md` (Markdown, Quarto-compatible)
- **Naming Convention**: `ADC_{NUMBER}_{NAME}.md`
- **Version Control**: Always committed to git
- **Parity Example**:
  ```yaml
  parity:
    file_path: "contracts/ADC_001_SYSTEM_ARCHITECTURE.md"
  ```

#### Refinement Directory (`adc_files/refinement/`)
- **Purpose**: Intermediate refinement artifacts from contract analysis
- **File Types**: Reports, summaries, checklists
- **Version Control**: Gitignored (ephemeral)
- **Lifecycle**: Created during refinement, can be deleted after contract update
- **Agent**: `@adc-contract-refiner`

#### Compliance Directory (`adc_files/compliance/`)
- **Purpose**: Audit reports tracking implementation compliance
- **File Types**: Audit reports, compliance summaries
- **Version Control**: Committed to git
- **Lifecycle**: Permanent record of compliance status
- **Agent**: `@adc-compliance-auditor`

#### Evaluation Directory (`adc_files/evaluation/`)
- **Purpose**: Empirical evaluation results and test data
- **File Types**: Evaluation reports, test results, performance metrics
- **Version Control**: Committed to git
- **Lifecycle**: Historical record of system performance
- **Agent**: `@adc-system-evaluator`

#### Implementation Directory (`adc_files/implementation/`)
- **Purpose**: Implementation summaries and deployment documentation
- **File Types**: Implementation notes, deployment checklists
- **Version Control**: Committed to git
- **Lifecycle**: Documentation of implementation decisions
- **Agent**: `@adc-code-generator`

#### Releases Directory (`adc_files/releases/`)
- **Purpose**: PR descriptions and release documentation
- **File Types**: PR descriptions, release notes, changelogs
- **Version Control**: Committed to git
- **Lifecycle**: Permanent release history
- **Agent**: `@adc-pr-orchestrator`

#### Temporary Directory (`claude_tmp/`)
- **Purpose**: All temporary and scratch files
- **File Types**: Any temporary outputs, debug logs, intermediate data
- **Version Control**: Gitignored
- **Lifecycle**: Can be deleted at any time
- **Critical Rule**: NEVER use `/tmp` or directories outside the workspace

### Workspace Constraints

**CRITICAL: All file operations MUST stay within the project workspace unless explicitly requested by the user.**

**Prohibited Actions:**
- ❌ Creating files in `/tmp` or system temporary directories
- ❌ Writing files outside the project root
- ❌ Using absolute paths that leave the workspace

**Required Actions:**
- ✅ Use `claude_tmp/` for all temporary files
- ✅ Use relative paths within the project
- ✅ Follow the standardized directory structure

### Git Ignore Patterns

Projects MUST include these patterns in `.gitignore`:

```gitignore
# ADC Temporary Files
claude_tmp/
adc_files/refinement/

# ADC Configuration
.adcconfig.json
*.adc-backup
contracts/*.tmp
contracts/*.bak
```

### File Naming Conventions

All ADC-related files MUST follow these naming patterns:

- **Contracts**: `ADC_{NUMBER}_{NAME}.md`
  - Example: `ADC_001_SYSTEM_ARCHITECTURE.md`
  
- **Refinement**: `ADC_{NUMBER}_REFINEMENT_{TYPE}.md`
  - Example: `ADC_001_REFINEMENT_REPORT.md`
  
- **Compliance**: `ADC_{NUMBER}_COMPLIANCE_{TYPE}.md`
  - Example: `ADC_001_COMPLIANCE_AUDIT.md`
  
- **Evaluation**: `ADC_{NUMBER}_EVALUATION_{TYPE}.md`
  - Example: `ADC_001_EVALUATION_REPORT.md`
  
- **Implementation**: `ADC_{NUMBER}_IMPLEMENTATION_{TYPE}.md`
  - Example: `ADC_001_IMPLEMENTATION_SUMMARY.md`
  
- **Releases**: `ADC_{NUMBER}_{TYPE}.md`
  - Example: `ADC_001_PR_DESCRIPTION.md`

### Validation

Use `adc validate-structure` to check if your project follows the ADC file organization guidelines
