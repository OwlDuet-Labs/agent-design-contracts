# Sequential Workflow Implementation Guide

## Contract: adc-sequential-workflow-001.qmd

### Overview

This contract specifies a sequential agent workflow that eliminates orchestrator overhead through:

1. **Context Summarization**: Reduce token usage by 85-90% per agent invocation
2. **Sequential Execution**: Direct agent-to-agent invocation without centralized orchestrator
3. **Nested Loop Control**: Two-level architecture for implementation and contract refinement

### Expected Impact

- **Token Reduction**: 47-53% (from 15.1M to 6-8M tokens per task)
- **Cost Reduction**: 50%+ (from $10.02 to $4-5 per task)
- **Success Rate**: 91.5%+ (maintained from baseline)

---

## Contract Structure

### Design Blocks (16 total)

1. **[Rationale]** - Why eliminate orchestrator overhead
2. **[Implementation]** - High-level architecture guidance
3. **[Agent]** - SequentialWorkflowController (main workflow orchestrator)
4. **[DataModel] × 3** - WorkflowState, PhaseRecord, WorkflowResult
5. **[Algorithm] × 2** - Nested loop control, context summarization
6. **[Tool]** - ContextSummarizer utility
7. **[Feature] × 2** - Sequential invocation, token tracking
8. **[Constraint]** - Token budget limits
9. **[TestScenario] × 3** - Inner loop, outer loop, token compliance
10. **[Diagram]** - Mermaid flowchart of workflow

---

## Implementation Files

### Required Files

```
src/adc/workflows/
├── sequential_workflow.py      # SequentialWorkflowController
├── state.py                    # WorkflowState, PhaseRecord, WorkflowResult
├── loop_control.py             # Nested loop algorithms
├── context_summarizer.py       # ContextSummarizer tool
├── agent_invoker.py            # AgentInvoker for sequential calls
└── token_tracker.py            # TokenBudgetTracker

config/workflows/
└── sequential.yaml             # Workflow configuration

tests/workflows/
├── test_sequential_workflow.py             # Main workflow tests
├── test_loop_control.py                    # Loop algorithm tests
├── test_context_summarization.py           # Summarization tests
├── test_agent_invocation.py                # Agent invocation tests
├── test_token_tracking.py                  # Token budget tests
├── test_constraints.py                     # Constraint validation
├── test_inner_loop_convergence.py          # Inner loop test scenario
├── test_outer_loop_refinement.py           # Outer loop test scenario
└── test_token_budget_compliance.py         # Token compliance test scenario
```

### Integration Files

```
runners/
└── run_comprehensive_evaluation.py    # Add --sequential-workflow flag
```

---

## Key Algorithms

### 1. Nested Loop Control

**Inner Loop (Implementation):**
```
Purpose: Fix code violations until compliance >= 0.8
Agents: Auditor ↔ Code Generator
Max iterations: 10
Token cost: ~500K per iteration
Exit: compliance >= 0.8 OR max_inner reached
```

**Outer Loop (Refinement):**
```
Purpose: Fix contract issues when tests fail
Agents: Evaluator → Refiner → Auditor → [Inner Loop]
Max iterations: 5
Token cost: ~3M per iteration
Exit: evaluator.satisfied OR max_outer reached
```

### 2. Context Summarization

**Contracts Summary:**
- Input: 100K tokens (full contracts)
- Output: 10K tokens (summary)
- Savings: 90%
- Used by: Auditor, Code Generator, Evaluator

**Violations Summary:**
- Input: 20K tokens (audit report)
- Output: 5K tokens (prioritized violations)
- Savings: 75%
- Used by: Code Generator in inner loop

**Evaluator Feedback:**
- Input: 30K tokens (evaluation result)
- Output: 15K tokens (test failures + recommendations)
- Savings: 50%
- Used by: Refiner

---

## Token Budget Analysis

### Expected Token Consumption

| Workflow Path | Outer Iter | Inner Iter | Total Tokens | Cost | Savings |
|---------------|-----------|-----------|--------------|------|---------|
| Optimal (1st try) | 1 | 3 | 3.2M | $2.11 | 78.8% |
| Typical (2nd try) | 2 | 5 total | 6.2M | $4.09 | 58.9% |
| Difficult (3rd try) | 3 | 12 total | 9.2M | $6.07 | 39.1% |
| Max iterations | 5 | varies | ~11M | $7.26 | 27.2% |
| **Average** | **2.3** | **7 total** | **~7M** | **$4.62** | **53.9%** |

**Baseline Comparison:**
- Current orchestrator: 15.1M tokens @ $10.02
- Sequential workflow: 7M tokens @ $4.62
- **Savings: 8.1M tokens (53.6%) and $5.40 (53.9%)**

### Per-Phase Token Breakdown

| Phase | Agent | Context Size | Tokens Used |
|-------|-------|--------------|-------------|
| 1. Initial Setup | Contract Writer | Task description | 200K |
| 2. Audit | Auditor | Summary 10K | 200K |
| 3. Generate Code | Code Generator | Summary 10K + Violations 5K | 300K |
| 4. Re-audit | Auditor | Summary 10K | 200K |
| 5. Evaluate | System Evaluator | Summary 10K | 800K |
| 6. Refine (if needed) | Refiner | Full contracts 100K + Feedback 15K | 500K |
| 7. Create PR | PR Orchestrator | Workspace path | 100K |

---

## Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Implement `WorkflowState` data model
- [ ] Implement `PhaseRecord` data model
- [ ] Implement `WorkflowResult` data model
- [ ] Implement `ContextSummarizer` tool
- [ ] Implement `TokenBudgetTracker`
- [ ] Add unit tests for data models

### Phase 2: Agent Invocation
- [ ] Implement `AgentInvoker` class
- [ ] Implement `invoke_contract_writer()`
- [ ] Implement `invoke_auditor()`
- [ ] Implement `invoke_code_generator()`
- [ ] Implement `invoke_system_evaluator()`
- [ ] Implement `invoke_refiner()`
- [ ] Implement `invoke_pr_orchestrator()`
- [ ] Add unit tests for agent invocation

### Phase 3: Loop Control
- [ ] Implement inner loop algorithm
- [ ] Implement outer loop algorithm
- [ ] Implement loop exit conditions
- [ ] Implement iteration counter management
- [ ] Add unit tests for loop control

### Phase 4: Workflow Controller
- [ ] Implement `SequentialWorkflowController` agent
- [ ] Implement `execute_workflow()` method
- [ ] Integrate context summarization
- [ ] Integrate token tracking
- [ ] Add integration tests

### Phase 5: Test Scenarios
- [ ] Implement inner loop convergence test
- [ ] Implement outer loop refinement test
- [ ] Implement token budget compliance test
- [ ] Add edge case tests (max iterations, oscillation, etc.)

### Phase 6: Integration
- [ ] Add `--sequential-workflow` flag to evaluation runner
- [ ] Create workflow configuration file
- [ ] Add comprehensive evaluation tests
- [ ] Document usage and examples

### Phase 7: Validation
- [ ] Run against existing benchmark tasks
- [ ] Verify token reduction (target: 47-53%)
- [ ] Verify cost reduction (target: 50%+)
- [ ] Verify success rate maintained (target: 91.5%+)
- [ ] Compare against baseline orchestrator

---

## Usage Example

```python
from adc.workflows import SequentialWorkflowController

# Initialize controller
controller = SequentialWorkflowController(
    max_outer_iterations=5,
    max_inner_iterations=10,
    compliance_threshold=0.8
)

# Execute workflow
result = controller.execute_workflow(
    task_description="Implement user authentication system",
    workspace="/path/to/workspace"
)

# Check results
if result.is_success():
    print(f"Success! PR created: {result.pr_url}")
    print(f"Tokens used: {result.total_tokens:,}")
    print(f"Cost: ${result.total_cost:.2f}")
    print(f"Savings vs baseline: {result.token_efficiency_vs_baseline():.1f}%")
else:
    print(f"Failed: {result.reason}")
    print(f"Final state: outer={result.final_state.outer_iteration}, inner={result.final_state.inner_iteration}")
```

---

## Integration with Evaluation Runner

```bash
# Run evaluation with sequential workflow
python runners/run_comprehensive_evaluation.py \
    --sequential-workflow \
    --max-outer-iterations 5 \
    --max-inner-iterations 10 \
    --compliance-threshold 0.8 \
    --track-tokens
```

---

## Success Criteria

### Token Efficiency
- [ ] Average workflow: 6-8M tokens (vs 15.1M baseline)
- [ ] Token reduction: 47-53%
- [ ] No workflow exceeds 12M tokens

### Cost Efficiency
- [ ] Average cost: $4-6 per task (vs $10.02 baseline)
- [ ] Cost reduction: 40-60%
- [ ] Target cost: $4.62 per task

### Quality Maintenance
- [ ] Success rate: >= 91.5% (same as baseline)
- [ ] Code quality: Same or better than baseline
- [ ] Contract compliance: Same or better than baseline
- [ ] No functionality regressions

### Performance
- [ ] Context summarization: < 2 seconds
- [ ] Agent invocation overhead: < 5 seconds
- [ ] Total workflow time: Within 10% of baseline

---

## Next Steps

1. Review contract for completeness and accuracy
2. Implement core data models and infrastructure
3. Implement context summarization algorithm
4. Implement nested loop control
5. Integrate with evaluation runner
6. Run benchmark tests and validate metrics
7. Document results and compare to baseline

---

## Contract Metadata

- **Contract ID**: adc-sequential-workflow-001
- **Status**: proposed
- **Version**: 1.0
- **Created**: 2025-12-16
- **Location**: `/Volumes/X10/owl/adc/adc-labs/contracts/adc-sequential-workflow-001.qmd`
- **Lines**: 1048
- **Design Blocks**: 16
