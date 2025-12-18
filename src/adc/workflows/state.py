"""State management for sequential ADC workflow.

ADC-IMPLEMENTS: <sequential-workflow-datamodel-01>
ADC-IMPLEMENTS: <sequential-workflow-datamodel-02>
ADC-IMPLEMENTS: <sequential-workflow-datamodel-03>
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class PhaseRecord:
    """Records the execution of a single workflow phase (agent invocation).

    ADC-IMPLEMENTS: <sequential-workflow-datamodel-02>
    """

    agent: str  # Agent name (e.g., "auditor", "code_generator")
    timestamp: datetime  # When phase executed
    tokens_used: int  # Tokens consumed in this phase (input + output, excluding cache reads)
    result_summary: str  # Compact summary of phase result
    iteration_context: Dict[str, int] = field(default_factory=dict)  # Iteration numbers
    input_tokens: int = 0  # Input tokens (excluding cache reads)
    output_tokens: int = 0  # Output tokens
    cache_creation_tokens: int = 0  # Tokens written to cache (billed at 1.25x)
    cache_read_tokens: int = 0  # Tokens read from cache (billed at 0.1x)


@dataclass
class WorkflowState:
    """Maintains the state of the sequential workflow execution across nested loops.

    ADC-IMPLEMENTS: <sequential-workflow-datamodel-01>
    """

    task_description: str  # Original task description (required)
    workspace: str  # Path to workspace directory (required)
    outer_iteration: int = 0  # Current refinement loop iteration
    inner_iteration: int = 0  # Current implementation loop iteration
    max_outer: int = 5  # Maximum refinement iterations
    max_inner: int = 10  # Maximum implementation iterations per refinement
    contracts_summary: str = ""  # Summarized contract context
    compliance_score: float = 0.0  # Latest audit compliance score
    last_violations: List[str] = field(default_factory=list)  # Latest audit violations
    evaluator_satisfied: bool = False  # Whether system evaluator is satisfied
    evaluator_feedback: str = ""  # Latest evaluator feedback
    inner_loop_active: bool = False  # Whether currently in inner loop
    phase_history: List[PhaseRecord] = field(default_factory=list)  # History of phase transitions

    def calculate_total_tokens(self) -> int:
        """Sum tokens used across all phases (excluding cache reads)."""
        return sum(phase.tokens_used for phase in self.phase_history)

    def calculate_total_cost(self) -> float:
        """Calculate total cost using proper cache pricing.

        Pricing for Claude Sonnet 4.5:
        - Input: $3.00/1M tokens
        - Output: $15.00/1M tokens
        - Cache write: $3.75/1M tokens (1.25x input)
        - Cache read: $0.30/1M tokens (0.1x input)

        Pricing for Claude Haiku 3.5:
        - Input: $0.25/1M tokens
        - Output: $1.25/1M tokens
        - Cache write: $0.30/1M tokens (1.2x input)
        - Cache read: $0.03/1M tokens (0.12x input)

        For simplicity, we use Sonnet pricing as most agents use Sonnet.
        """
        total_cost = 0.0

        for phase in self.phase_history:
            # Input tokens (regular)
            total_cost += (phase.input_tokens / 1_000_000) * 3.00
            # Output tokens
            total_cost += (phase.output_tokens / 1_000_000) * 15.00
            # Cache creation tokens (1.25x input price)
            total_cost += (phase.cache_creation_tokens / 1_000_000) * 3.75
            # Cache read tokens (0.1x input price)
            total_cost += (phase.cache_read_tokens / 1_000_000) * 0.30

        return total_cost

    def record_phase(
        self,
        agent: str,
        tokens_used: int,
        result_summary: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_creation_tokens: int = 0,
        cache_read_tokens: int = 0
    ):
        """Record a phase transition with detailed token metrics.

        Args:
            agent: Agent name (e.g., "auditor", "code_generator")
            tokens_used: Total tokens consumed (input + output, excluding cache reads)
            result_summary: Compact summary of phase result
            input_tokens: Input tokens (excluding cache reads)
            output_tokens: Output tokens
            cache_creation_tokens: Tokens written to cache (billed at 1.25x)
            cache_read_tokens: Tokens read from cache (billed at 0.1x)
        """
        self.phase_history.append(PhaseRecord(
            agent=agent,
            timestamp=datetime.now(),
            tokens_used=tokens_used,
            result_summary=result_summary,
            iteration_context={
                "outer": self.outer_iteration,
                "inner": self.inner_iteration if self.inner_loop_active else None
            },
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_tokens=cache_creation_tokens,
            cache_read_tokens=cache_read_tokens
        ))

    @classmethod
    def from_task(cls, task_description: str, workspace: str) -> 'WorkflowState':
        """Factory method to initialize state from task."""
        return cls(
            task_description=task_description,
            workspace=workspace
        )


@dataclass
class WorkflowResult:
    """Result of workflow execution with final state and outcome.

    ADC-IMPLEMENTS: <sequential-workflow-datamodel-03>
    """

    status: str  # "success", "failed"
    final_state: WorkflowState  # Final workflow state
    total_tokens: int  # Total tokens consumed
    total_cost: float  # Total cost in dollars
    reason: str = "completed"  # Reason for outcome
    pr_url: str = ""  # Pull request URL if successful
    execution_time_seconds: float = 0.0  # Total execution time

    def is_success(self) -> bool:
        """Check if workflow succeeded."""
        return self.status == "success"

    def token_efficiency_vs_baseline(self, baseline_tokens: int = 15_100_000) -> float:
        """Calculate token efficiency improvement percentage."""
        return ((baseline_tokens - self.total_tokens) / baseline_tokens) * 100

    def cost_savings_vs_baseline(self, baseline_cost: float = 10.02) -> float:
        """Calculate cost savings percentage."""
        return ((baseline_cost - self.total_cost) / baseline_cost) * 100
