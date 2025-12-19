# Code Generator Control Flow: Before and After Fix

## BEFORE FIX (Buggy Flow)

```
┌─────────────────────────────────────────┐
│ Parse files_to_fix from audit           │
│ Result: [] (empty)                      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │ files_to_fix? │
          └───────┬───────┘
                  │
        ┌─────────┴─────────┐
        │ NO (empty)        │ YES (has files)
        ▼                   ▼
┌───────────────┐   ┌───────────────────┐
│ Check for     │   │ Self-Loop:        │
│ stub files    │   │ Process each file │
└───────┬───────┘   │ with fresh budget │
        │           └───────────────────┘
        ▼
  ┌─────────┐
  │ Stubs?  │
  └────┬────┘
       │
   ┌───┴────┐
   │ YES    │ NO
   ▼        ▼
┌──────┐  ┌──────────┐
│ Set  │  │ Fallback │
│files │  │ Global   │
│_to_  │  │ Approach │
│fix=[│  └──────────┘
│stubs]│
└──┬───┘
   │
   ▼
┌────────────────────────────┐
│ ❌ BUG: Do nothing!        │
│ files_to_fix is populated  │
│ but never processed!       │
└────────────────────────────┘
```

**Result:** Stubs detected but ignored. Loop repeats with 0% compliance.

---

## AFTER FIX (Correct Flow)

```
┌─────────────────────────────────────────┐
│ Parse files_to_fix from audit           │
│ Result: [] (empty)                      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
          ┌───────────────┐
          │ files_to_fix? │
          └───────┬───────┘
                  │
        ┌─────────┴─────────┐
        │ NO (empty)        │
        ▼                   │
┌───────────────┐          │
│ Check for     │          │
│ stub files    │          │
└───────┬───────┘          │
        │                  │
        ▼                  │
  ┌─────────┐             │
  │ Stubs?  │             │
  └────┬────┘             │
       │                  │
   ┌───┴────┐            │
   │ YES    │            │
   ▼        │            │
┌──────┐   │            │
│ Set  │   │            │
│files │   │            │
│_to_  │   │            │
│fix=[│   │            │
│stubs]│   │            │
└──┬───┘   │            │
   │        │            │
   │ ✅ Fall through!   │
   │        │            │
   └────────┴────────────┘
            │
            ▼
    ┌───────────────┐
    │ files_to_fix? │  ← NEW CHECK (after stub detection)
    └───────┬───────┘
            │
     ┌──────┴──────┐
     │ YES         │ NO
     ▼             ▼
┌─────────────┐  ┌──────────┐
│ Self-Loop:  │  │ Fallback │
│ Process     │  │ Global   │
│ each file   │  │ Approach │
│ with fresh  │  └──────────┘
│ budget      │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ For each file:      │
│ 1. Read stub        │
│ 2. Call code gen    │
│ 3. Write real code  │
│ ✅ SUCCESS!         │
└─────────────────────┘
```

**Result:** Stubs detected and processed. Code is written. Compliance increases.

---

## Key Difference

### Before:
```python
if not files_to_fix:
    if stub_files:
        files_to_fix = [stubs]
    else:
        fallback()
else:  # ← Never reached when stubs detected!
    process_files()
```

### After:
```python
if not files_to_fix:
    if stub_files:
        files_to_fix = [stubs]

if files_to_fix:  # ← New check after stub detection
    process_files()
else:
    fallback()
```

## Code Execution Path

### Before Fix (Stubs Present):
1. `files_to_fix = []` (empty from audit)
2. Enter `if not files_to_fix:` (TRUE)
3. Find stubs, set `files_to_fix = [stub1, stub2]`
4. Exit `if` block
5. **Skip** `else:` block (because we entered the `if`)
6. Continue to `state.inner_iteration += 1`
7. Loop back to auditor (no code written)

### After Fix (Stubs Present):
1. `files_to_fix = []` (empty from audit)
2. Enter `if not files_to_fix:` (TRUE)
3. Find stubs, set `files_to_fix = [stub1, stub2]`
4. Exit `if` block
5. **Enter** `if files_to_fix:` (TRUE - now populated!)
6. Process each stub file with code generator
7. Continue to `state.inner_iteration += 1`
8. Loop back to auditor (code written, compliance improves)

## Test Evidence

### Before Fix:
```
[Stubs] Found 2 stub files to complete...
Implementation exists: False
Compliance: 0.0%
```

### After Fix:
```
[Stubs] Found 2 stub files to complete...
[Self-Loop] Processing 2 files separately...
  [Generating] src/models.py (1 issues)...
  [Generating] src/database.py (1 issues)...
[Success] Processed 2/2 files
Implementation exists: True
Compliance: 45.0%
```
