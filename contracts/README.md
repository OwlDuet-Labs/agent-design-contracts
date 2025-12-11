# ADC Contracts

This directory contains Agent Design Contract (ADC) specifications.

## File Naming Convention

Contracts should follow this naming pattern:
- `ADC_{NUMBER}_{NAME}.qmd`
- Example: `ADC_001_SYSTEM_ARCHITECTURE.qmd`

## Structure

Each contract file should:
1. Start with YAML front matter containing metadata
2. Include design blocks following the ADC schema
3. Reference the schema at `~/.claude/schema/adc-schema.qmd`

## Workflow

1. **Create**: Write new contracts using `@adc-contract-writer`
2. **Refine**: Improve contracts using `@adc-contract-refiner`
3. **Implement**: Generate code using `@adc-code-generator`
4. **Audit**: Check compliance using `@adc-compliance-auditor`
5. **Evaluate**: Test system using `@adc-system-evaluator`
6. **Release**: Create PRs using `@adc-pr-orchestrator`

See the ADC schema for complete documentation.
