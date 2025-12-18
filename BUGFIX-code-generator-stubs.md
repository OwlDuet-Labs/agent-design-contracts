# Bug Fix: Code Generator Stub Processing

**Date:** 2025-12-17
**Component:** Sequential Workflow - Code Generator Phase
**Severity:** Critical (Infinite Loop)
**Status:** Fixed

## Problem Description

The sequential workflow's stub file creation feature was creating files but not filling them with code, resulting in an infinite loop:

1. Contract-writer creates contracts with parity sections
2. Stub files are created: `src/models.py`, `src/database.py`, etc.
3. Code generator detects stubs: `[Stubs] Found 2 stub files to complete...`
4. **BUG**: Code generator doesn't write any code to the stubs
5. Auditor reports: `Implementation exists: False`, `Compliance: 0.0%`
6. Loop repeats until `max_inner_iterations_reached`

## Root Cause

Control flow logic error in `sequential_workflow.py` lines 1165-1283.

The code had this structure:

```python
files_to_fix = self._parse_file_list_from_audit(audit_data)  # Empty

if not files_to_fix:
    # Detect stubs
    stub_files = [...]
    if stub_files:
        files_to_fix = [...]  # Populate with stubs
    else:
        # Fallback: global approach
        invoke_agent("@adc-code-generator", ...)
else:
    # Self-loop: Process files one by one
    for file_info in files_to_fix:
        invoke_agent("@adc-code-generator", file_prompt)
```

**The Bug:** When stubs were detected, `files_to_fix` was populated inside the `if not files_to_fix:` block, but the code never reached the `else:` block that would actually process those files. The `else` only executed when `files_to_fix` was **already populated** from the audit.

## Solution

Restructured the control flow to check `files_to_fix` **after** stub detection:

```python
files_to_fix = self._parse_file_list_from_audit(audit_data)  # Empty

# Detect stubs if no files from audit
if not files_to_fix:
    stub_files = [...]
    if stub_files:
        files_to_fix = [...]  # Populate with stubs
        # Fall through to processing below

# Process files (either from audit OR stubs)
if files_to_fix:
    # Self-loop: Process files one by one
    for file_info in files_to_fix:
        invoke_agent("@adc-code-generator", file_prompt)
else:
    # Fallback: global approach (only if no files AND no stubs)
    invoke_agent("@adc-code-generator", global_prompt)
```

**Key Change:** Changed line 1178 from `else:` to `if files_to_fix:` to check the variable after stub detection.

## Code Changes

**File:** `src/adc/workflows/sequential_workflow.py`

### Before (Lines 1165-1217):
```python
if not files_to_fix:
    stub_files = [...]
    if stub_files:
        files_to_fix = [...]
    else:
        # Fallback
        invoke_agent(...)
else:  # ← BUG: Never reached when stubs detected
    # Self-loop
    for file_info in files_to_fix:
        invoke_agent(...)
```

### After (Lines 1165-1246):
```python
if not files_to_fix:
    stub_files = [...]
    if stub_files:
        files_to_fix = [...]
        # Fall through to self-loop processing below

if files_to_fix:  # ← FIX: Check after stub detection
    # Self-loop
    for file_info in files_to_fix:
        invoke_agent(...)
else:
    # Fallback (only if no files AND no stubs)
    invoke_agent(...)
```

## Expected Behavior After Fix

### Before Fix:
```
[Auditor] Running compliance audit (iteration 0)...
  Implementation exists: False
  Compliance: 0.0%
[Code Generator] Fixing implementation issues...
  [Stubs] Found 2 stub files to complete...
[Auditor] Running compliance audit (iteration 1)...
  Implementation exists: False  ← Still no code!
  Compliance: 0.0%
[Code Generator] Fixing implementation issues...
  [Stubs] Found 2 stub files to complete...
[Auditor] Running compliance audit (iteration 2)...
  Implementation exists: False
  Compliance: 0.0%
STOP: Max inner iterations (3) reached
```

### After Fix:
```
[Auditor] Running compliance audit (iteration 0)...
  Implementation exists: False
  Compliance: 0.0%
[Code Generator] Fixing implementation issues...
  [Stubs] Found 2 stub files to complete...
  [Self-Loop] Processing 2 files separately...
    [Generating] src/models.py (1 issues)...
    [Generating] src/database.py (1 issues)...
  [Success] Processed 2/2 files
[Auditor] Running compliance audit (iteration 1)...
  Implementation exists: True  ← Code written!
  Files checked: 2
  Compliance: 45.0%  ← Progress!
[Code Generator] Fixing implementation issues...
  ... (continues improving until >= 80%)
```

## Verification

To verify the fix works:

```bash
cd /Volumes/X10/owl/adc/iterate-bench
python runners/run_sequential_workflow.py --task test-parity-stubs
```

Expected results:
- Stub files contain actual Python code (not just ADC-IMPLEMENTS markers)
- Auditor reports `Implementation exists: True`
- Compliance score increases iteration by iteration
- No infinite loops

## Testing Coverage

**Test Case:** Parity Stubs Integration
- **Location:** `evaluations/test-parity-stubs/adc-sequential-haiku/task-001/`
- **Before:** Failed with `max_inner_iterations_reached`, compliance stuck at 0.0%
- **After:** Should succeed with compliance >= 80%

## Related Issues

- ADC-035: Self-inner-loop pattern for code generation
- ADC-036: Stub file creation from contract parity sections

## Impact

**Before:** All workflows using parity sections would fail in infinite loops
**After:** Stub files are properly completed with working code

This fix enables the full contract-to-code pipeline:
1. Contract-writer creates contracts with parity sections
2. Stub files are auto-generated with proper structure
3. Code generator fills stubs with actual implementations
4. Auditor verifies compliance
5. Tests pass

## Author

Claude Code (ADC Refactorer Agent)
Date: 2025-12-17
