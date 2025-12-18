# Refactorer Role Documentation

## Overview

The Refactorer role is a new first-class ADC agent that orchestrates refactoring work through temporary contracts. It solves the problem of integrating features from standalone implementations into modular codebases without creating duplicate code paths or version-specific modules.

## Key Concepts

### Contract Types

ADC now supports two contract types via the `type` field in YAML front matter:

#### Component Contracts (`type: component`)
- **Permanent** architectural contracts
- Define system components, features, modules
- Code implementations link to these via `ADC-IMPLEMENTS`
- Updated as system evolves
- Status: proposed → active → deprecated → superseded

#### Refactor Contracts (`type: refactor`)
- **Temporary** coordination contracts
- Orchestrate updates to component contracts
- Never referenced by code implementations
- Deleted when auditor confirms completion
- Status: active → completed (then deleted)

### Workflow

```
1. Analysis & Contract Creation
   - Identify component contracts to update
   - Locate standalone/duplicate implementations
   - Review test coverage
   - Create temporary refactor contract

2. Test Assessment
   - Evaluate existing tests
   - Implement missing tests FIRST
   - Document baseline results

3. Orchestrated Loop
   - REFINER: Update component contracts
   - AUDITOR: Check compliance (READY/BLOCKED)
   - CODE GENERATOR: Implement changes (if blocked)
   - EVALUATOR: Verify no regression
   - Repeat until complete

4. Completion & Cleanup
   - Auditor confirms completion
   - Delete refactor contract
   - Archive standalone implementations
```

## New Block Types

Refactor contracts use specialized block types:

- **`[Rationale]`** - Why refactoring is needed
- **`[TargetContracts]`** - Component contracts to update
- **`[RefactoringTasks]`** - Phased implementation plan
- **`[TestStrategy]`** - Test coverage requirements
- **`[SuccessCriteria]`** - Completion conditions

## Anti-Patterns Prevented

The refactorer enforces:

❌ **Never:**
- Create permanent refactor contracts
- Link code to refactor contracts
- Create version-specific modules (e.g., `adc027_trainer.py`)
- Refactor without test coverage
- Skip existing test validation

✅ **Always:**
- Create temporary refactor contracts in `contracts/refactoring/`
- Update existing component contracts
- Implement/verify tests BEFORE refactoring
- Link code to component contracts
- Delete refactor contracts on completion
- Ensure zero regression

## Example Use Case

**Problem:** Standalone script `train_with_temperature_splits.py` has proven features that need integration into modular codebase.

**Solution:**

1. **Create refactor contract:**
   ```yaml
   contract_id: refactor-adc027-integration-adc-033
   type: refactor
   target_contracts:
     - "local-router-model-pipeline-adc-022"
   completion_criteria:
     - "All target contracts updated"
     - "All tests passing (zero regression)"
     - "Standalone implementation removed"
   ```

2. **Assess tests:**
   - Existing: `tests/test_trainer.py` ✅
   - Missing: Loss configuration tests
   - Action: Implement missing tests first

3. **Orchestrated loop:**
   - REFINER: Update ADC-022 with loss configuration, generic trainer
   - AUDITOR: Check implementation status
   - CODE GENERATOR: Create `loss.py`, update `trainer.py` (link to ADC-022)
   - EVALUATOR: Run all tests, verify no regression

4. **Completion:**
   - AUDITOR: "Contract COMPLETE, recommend DELETE"
   - Archive `train_with_temperature_splits.py`
   - Delete refactor contract
   - All changes tracked in ADC-022

## YAML Front Matter Changes

```yaml
---
contract_id: module_name-unique-identifier-adc-001
title: "Contract Title"
author: "Author Name"
type: "component" # NEW: component | refactor
status: "proposed"
version: 1.2
created_date: "YYYY-MM-DD"
last_updated: "YYYY-MM-DD"
# Refactor contracts only:
target_contracts: [] # List of component contract IDs
completion_criteria: [] # Completion conditions
---
```

## Files Modified

In the ADC-v1 repository:

- **`roles/refactorer.md`** - New role definition
- **`adc-schema.qmd`** - Updated with contract types and new block types
- **`CHANGELOG.md`** - Documented changes
- **`docs/REFACTORER_ROLE.md`** - This documentation

## Installation

After running `adc init`, the refactorer role will be available along with:
- Updated schema with contract types
- Support for `contracts/refactoring/` directory
- Four new block types for refactor contracts

## Usage

The refactorer is invoked automatically during the ADC loop when:
- User requests feature integration from standalone code
- User requests code consolidation/deduplication
- User requests refactoring with `/adc` command

It orchestrates other agents (refiner, auditor, code generator, evaluator) until the auditor confirms completion and recommends deletion of the temporary refactor contract.

## Benefits

1. **Zero regression** - Test-first approach ensures existing functionality preserved
2. **No duplication** - Features integrated into existing modules, not parallel implementations
3. **Clean architecture** - Updates existing contracts instead of version-specific code
4. **Traceable** - All changes documented in component contracts
5. **Temporary coordination** - Refactor contracts deleted on completion
6. **Generic naming** - Enforces `trainer.py` with config instead of `adc027_trainer.py`

## Key Principle

**Refactor into existing modules, don't create duplicates. Use temporary contracts to coordinate, delete when done.**

---

**Version:** Unreleased (v0.9.3+)
**Created:** 2024-11-24
**Status:** Ready for installation via `adc init`
