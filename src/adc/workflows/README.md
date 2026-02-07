# ADC Sequential Workflow

Sequential agent workflow implementation that eliminates orchestrator overhead through context summarization and direct agent invocation.

## Contract

Implements: `/Volumes/X10/owl/adc/adc-labs/contracts/adc-sequential-workflow-001.qmd`

## Architecture

The sequential workflow replaces the centralized orchestrator with a two-level loop architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                     SEQUENTIAL WORKFLOW                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Contract Writer  │
                    │   (Initial)      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Create Summary   │
                    │  100K → 10K      │
                    └────────┬─────────┘
                             │
                             ▼
            ╔════════════════════════════════════╗
            ║        OUTER LOOP (max 5)          ║
            ╚════════════════════════════════════╝
                             │
                    ┌────────┴─────────┐
                    │                  │
                    ▼                  ▼
            ┌──────────────┐   ┌──────────────┐
            │   Auditor    │   │   Refiner    │
            │  (Initial)   │   │  (If tests   │
            └──────┬───────┘   │   failed)    │
                   │           └──────▲───────┘
                   ▼                  │
    ╔══════════════════════════════╗ │
    ║  INNER LOOP (max 10)         ║ │
    ║  Until compliance >= 0.8     ║ │
    ╚══════════════════════════════╝ │
                   │                  │
         ┌─────────┴──────────┐       │
         ▼                    ▼       │
    ┌─────────┐      ┌──────────────┐│
    │ Auditor │◄────►│     Code     ││
    │         │      │  Generator   ││
    └─────────┘      └──────────────┘│
         │                            │
         │ compliance >= 0.8          │
         ▼                            │
    ┌──────────────┐                 │
    │  Evaluator   │                 │
    └──────┬───────┘                 │
           │                         │
     ┌─────┴─────┐                   │
     ▼           ▼                   │
  ┌────┐    ┌────────┐               │
  │Pass│    │  Fail  │───────────────┘
  └─┬──┘    └────────┘
    │
    ▼
┌───────────────┐
│PR Orchestrator│
└───────────────┘
    │
    ▼
 SUCCESS
```

## Key Innovations

### 1. Context Summarization

Agents receive summarized context (10-20K tokens) instead of full context (100-300K tokens):

- **Contracts Summary**: 100K → 10K tokens (90% reduction)
- **Violations Summary**: 20K → 5K tokens (75% reduction)
- **Evaluator Context**: 300K → 20K tokens (93% reduction)

### 2. Sequential Invocation

Agents execute directly without a coordinating orchestrator:

- No parent context accumulation
- Direct Claude CLI invocation per agent
- State persisted only through WorkflowState object

### 3. Progress Detection

Workflow stops after 2 stagnant runs (no compliance improvement):

- Tracks compliance scores across iterations
- Prevents infinite loops
- Fails fast when stuck

## Token Efficiency

Expected token consumption:

```
Initial setup:
- Contract writer: 200K tokens
- Summary creation: 10K tokens

Per outer iteration:
- Auditor (initial): 200K tokens
- Inner loop (avg 3 iterations): 3 × 500K = 1.5M tokens
- System evaluator: 800K tokens
- Refiner (if needed): 500K tokens
Total per outer iteration: ~3M tokens

Expected workflow:
- Successful on iteration 1: ~3.2M tokens ($2.11)
- Successful on iteration 2: ~6.2M tokens ($4.09)
- Successful on iteration 3: ~9.2M tokens ($6.07)
- Average (2.3 iterations): ~7M tokens ($4.62)

Baseline comparison:
- Current orchestrator: 15.1M tokens ($10.02)
- Sequential workflow: 7M tokens ($4.62)
- Savings: 53.6% tokens, 53.9% cost
```

## Usage

### Programmatic API

```python
from pathlib import Path
from adc.workflows import SequentialWorkflow

# Create workspace
workspace = Path("./my-project")
workspace.mkdir(exist_ok=True)

# Run workflow
workflow = SequentialWorkflow(workspace)
result = workflow.run("Create a REST API with authentication")

# Check results
print(f"Status: {result.status}")
print(f"Total Cost: ${result.total_cost:.2f}")
print(f"Token Savings: {result.token_efficiency_vs_baseline():.1f}%")
```

### Via Evaluation Runner

```bash
# Single task test
python3 runners/run_comprehensive_evaluation.py \
  --tasks 1 \
  --methods adc-sequential

# Full comparison
python3 runners/run_comprehensive_evaluation.py \
  --tasks all \
  --methods adc-sequential,adc-integrated,baseline \
  --parallel 4
```

## Data Models

### WorkflowState

Maintains workflow execution state:

```python
@dataclass
class WorkflowState:
    task_description: str
    workspace: str
    outer_iteration: int = 0
    inner_iteration: int = 0
    max_outer: int = 5
    max_inner: int = 10
    contracts_summary: str = ""
    compliance_score: float = 0.0
    last_violations: List[str] = field(default_factory=list)
    evaluator_satisfied: bool = False
    evaluator_feedback: str = ""
    inner_loop_active: bool = False
    phase_history: List[PhaseRecord] = field(default_factory=list)
```

### WorkflowResult

Final workflow outcome:

```python
@dataclass
class WorkflowResult:
    status: str  # "success", "failed"
    final_state: WorkflowState
    total_tokens: int
    total_cost: float
    reason: str = "completed"
    pr_url: str = ""
    execution_time_seconds: float = 0.0
```

### PhaseRecord

Individual agent execution record:

```python
@dataclass
class PhaseRecord:
    agent: str
    timestamp: datetime
    tokens_used: int
    result_summary: str
    iteration_context: Dict[str, int] = field(default_factory=dict)
```

## Loop Control

### Inner Loop (Implementation Refinement)

**Purpose**: Implement contracts correctly
**Agents**: Auditor ↔ Code Generator
**Max Iterations**: 10
**Exit Condition**: `compliance >= 0.8` OR `iterations >= max_inner`
**Token Cost**: ~500K per iteration

```python
while compliance < 0.8 AND inner_iteration < max_inner:
    1. Invoke auditor (200K tokens)
    2. Check progress (stop if stuck)
    3. If not compliant:
       - Invoke code generator (300K tokens)
       - Increment iteration
```

### Outer Loop (Contract Refinement)

**Purpose**: Fix contract issues when implementation correct but tests fail
**Agents**: Evaluator → Refiner → Auditor → [Inner Loop]
**Max Iterations**: 5
**Exit Condition**: `evaluator.satisfied == true` OR `iterations >= max_outer`
**Token Cost**: ~3M per iteration

```python
for outer_iteration in range(max_outer):
    1. Execute inner loop (until compliance >= 0.8)
    2. Invoke evaluator (800K tokens)
    3. If satisfied:
       - Invoke PR orchestrator
       - Return SUCCESS
    4. Else:
       - Invoke refiner (500K tokens)
       - Reload contracts summary
       - Continue to next iteration
```

## Progress Detection

The workflow automatically detects stagnation and stops:

```python
class ProgressTracker:
    def is_stuck(self) -> bool:
        """Check if no progress in last 2 runs."""
        if len(self.scores) < 3:
            return False

        last_three = self.scores[-3:]
        # No improvement in last 2 runs
        if last_three[-1] <= last_three[-2] and last_three[-2] <= last_three[-3]:
            return True
        return False
```

## Testing

Run unit tests:

```bash
python3 runners/test_adc_sequential.py
```

Test with dev mode (no actual Claude execution):

```bash
python3 runners/run_comprehensive_evaluation.py \
  --tasks 1 \
  --methods adc-sequential \
  --dev
```

## Files

```
src/adc/workflows/
├── __init__.py              # Package exports
├── state.py                 # WorkflowState, PhaseRecord, WorkflowResult
├── sequential_workflow.py   # SequentialWorkflow, ProgressTracker
└── README.md               # This file
```

## Future Enhancements

1. **Context Summarizer Tool**: More sophisticated summarization beyond simple truncation
2. **MCP State Manager**: Persist state across interruptions
3. **Token Budget Alerts**: Warning when approaching budget limits
4. **Parallel Inner Loops**: Run multiple fix attempts in parallel
5. **Adaptive Iteration Limits**: Adjust max_inner/max_outer based on task complexity

## References

- Contract: `/Volumes/X10/owl/adc/adc-labs/contracts/adc-sequential-workflow-001.qmd`
- Evaluation Runner: `/Volumes/X10/owl/adc/iterate-bench/runners/run_comprehensive_evaluation.py`
- Unit Tests: `/Volumes/X10/owl/adc/iterate-bench/runners/test_adc_sequential.py`
