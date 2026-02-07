# ADC Contracts

This directory contains Agent Design Contract (ADC) specifications for the adc-labs project.

## Contract Files

### Active Contracts

1. **adc-tool-adc-001.qmd** - ADC CLI Tool specification
   - Core CLI interface for ADC methodology
   - Agent invocation and configuration management

2. **adc-cli-best-practices-adc-002.qmd** - ADC CLI Best Practices
   - Auditor-verifiable CLI design patterns
   - Structured output and validation requirements

3. **adc-cli-testing-adc-003.qmd** - ADC CLI Testing Practices
   - Test strategy and quality assurance

4. **adc-sequential-workflow-001.qmd** - Sequential Agent Workflow (NEW)
   - Eliminates orchestrator overhead through context summarization
   - Nested loop architecture (inner: implementation, outer: refinement)
   - 53.6% token reduction (15.1M to 7M tokens)
   - 53.9% cost reduction ($10.02 to $4.62 per task)
   - Status: PROPOSED (ready for implementation)

### Supporting Documentation

- **adc-sequential-workflow-IMPLEMENTATION.md** - Implementation guide for sequential workflow
- **adc-sequential-workflow-COMPARISON.md** - Orchestrator vs Sequential pattern analysis
- **adc-sequential-workflow-VALIDATION.md** - Schema compliance validation report

## File Naming Convention

Contracts follow this pattern:
- `adc-{module}-adc-{number}.qmd` (e.g., `adc-cli-adc-001.qmd`)
- `{module}-{component}-{number}.qmd` (e.g., `adc-sequential-workflow-001.qmd`)

Supporting docs:
- `{contract-name}-{TYPE}.md` (e.g., `adc-sequential-workflow-IMPLEMENTATION.md`)

## Directory Organization

Maintain no more than 8 contracts per directory:
- Current count: 4 contracts + 3 docs = 7 files
- Use subdirectories when exceeding 8 contracts
- Use auto-incrementing numbers (001, 002, 003, etc.)

## Contract Structure

Each contract file must:
1. Start with YAML front matter (contract_id, title, author, status, version, dates)
2. Include design blocks following ADC Schema v1.0 format
3. Use proper block types: [Rationale], [Implementation], [Agent], [DataModel], [Algorithm], [Tool], [Feature], [Constraint], [TestScenario], [Diagram]
4. Include Parity sections for all implementable blocks
5. Follow functional design principles (no Optional types, sensible defaults)

## ADC Workflow

1. **Create**: Write new contracts using `@adc-contract-writer`
2. **Refine**: Improve contracts using `@adc-refiner`
3. **Implement**: Generate code using `@adc-code-generator`
4. **Audit**: Check compliance using `@adc-auditor`
5. **Evaluate**: Test system using `@adc-system-evaluator`
6. **Release**: Create PRs using `@adc-pr-orchestrator`

## Sequential Workflow Quick Start

The new sequential workflow pattern offers significant improvements:

```bash
# Implement the sequential workflow
cd /Volumes/X10/owl/adc/adc-labs

# Generate code from contract
adc generate --contracts contracts/adc-sequential-workflow-001.qmd

# Run implementation
python -m src.adc.workflows.sequential_workflow \
    --task "Implement user authentication" \
    --workspace ./workspace

# Run evaluation with sequential workflow
python runners/run_comprehensive_evaluation.py \
    --sequential-workflow \
    --max-outer-iterations 5 \
    --max-inner-iterations 10 \
    --track-tokens
```

## Key Metrics

### Sequential Workflow Performance

| Metric | Baseline (Orchestrator) | Sequential | Improvement |
|--------|------------------------|-----------|-------------|
| Avg Tokens | 15.1M | 7M | 53.6% |
| Avg Cost | $10.02 | $4.62 | 53.9% |
| Success Rate | 91.5% | 91.5%+ | Same/better |
| Execution Time | 4.3-4.5 min | 4.0-4.2 min | 5-10% faster |

### Token Budget by Path

- Optimal (1st try): 3.2M tokens ($2.11) - 79% savings
- Typical (2nd try): 6.2M tokens ($4.09) - 59% savings
- Difficult (3rd try): 9.2M tokens ($6.07) - 39% savings
- Max iterations: 11M tokens ($7.26) - 27% savings

## Schema Reference

All contracts follow ADC Schema v1.0 specification.
Schema documentation: `/Users/tad/labs/agent-design-contracts/adc-schema.qmd`

## Contributing

When creating new contracts:
1. Follow the ADC schema strictly
2. Use functional design principles (no Optional types)
3. Include complete Parity sections
4. Provide comprehensive test scenarios
5. Validate against schema before committing
6. Keep directory under 8 files (create subdirectories as needed)
