# Universal Library Loader - Architecture Summary

## Problem Statement

The ADC auditor currently reads all source files to verify interface compliance, consuming **42,600 tokens per audit** (128,000 tokens total across 3 audit cycles). This costs **$18.42 per 48-task benchmark**.

We need a way to verify that implementations match contract specifications WITHOUT reading all the source code.

## Solution: Universal Library Loader

A unified Python interface for loading and introspecting libraries written in ANY language.

### Token Economics

| Approach | Tokens per Audit | 3 Audits | 48-Task Benchmark | Cost |
|----------|------------------|----------|-------------------|------|
| **Current (Reading Files)** | 42,600 | 128,000 | 6.14M | $18.42 |
| **Library Loader (Python/Node.js)** | 1,600 | 4,800 | 230K | $0.69 |
| **CLI Fallback (Rust/Go)** | 1,000 | 3,000 | 144K | $0.43 |
| **Savings** | **96-98%** | **96-98%** | **96-98%** | **$17.73-$17.99** |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ load_library(workspace_path)                                │
│   Unified API for all languages                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
                  Language Detection
                  (setup.py, package.json, Cargo.toml, etc.)
                         │
         ┌───────────────┼───────────────┬──────────────┐
         ▼               ▼               ▼              ▼
   PythonBridge    NodeBridge    CliFallbackBridge  (Phase 2)
   ─────────────  ─────────────  ─────────────────  ──────────
   - importlib    - subprocess   - CLI execution    - PyO3 (Rust)
   - inspect      - JSON-RPC     - --help parsing   - ctypes (Go)
   - Full verify  - Full verify  - LIMITED verify   - Jep (Java)
                                                     - Full verify
```

## Phase 1: Immediate Implementation

### What's Implemented

**1. Python Direct Loading (PythonBridge)**
- Use `importlib` to dynamically import Python modules
- Use `inspect.signature()` to verify function signatures
- Full type annotation verification
- Docstring extraction
- **Verification Level: FULL**
- **Token Usage: ~1,600 per audit**

**2. Node.js Subprocess Bridge (NodeBridge)**
- Spawn Node.js process with JSON-RPC server
- Call functions via JSON-RPC protocol
- Introspect TypeScript type definitions if available
- **Verification Level: FULL**
- **Token Usage: ~1,600 per audit**

**3. CLI Fallback (CliFallbackBridge)**
- For Go, Rust, Java, C++ (without bindings)
- Execute CLI with `--help` to verify commands exist
- Parse output to check basic functionality
- **Verification Level: LIMITED (no signature verification)**
- **Token Usage: ~1,000 per audit**

**4. ADC Marker Verification (MarkerVerifier)**
- Use `rg` (ripgrep) to find ADC-IMPLEMENTS markers
- Required for ALL languages
- Links code to contract blocks
- **Token Usage: ~500 per audit**

### What Can Be Verified

| Language | Phase 1 Bridge | Functions Exist | Signatures | Types | Docstrings | Markers |
|----------|----------------|-----------------|------------|-------|------------|---------|
| Python | PythonBridge | ✅ | ✅ | ✅ | ✅ | ✅ |
| Node.js | NodeBridge | ✅ | ✅ | ✅ | ❌ | ✅ |
| Rust | CliFallback | ✅ | ❌ | ❌ | ❌ | ✅ |
| Go | CliFallback | ✅ | ❌ | ❌ | ❌ | ✅ |
| Java | CliFallback | ✅ | ❌ | ❌ | ❌ | ✅ |
| C++ | CliFallback | ✅ | ❌ | ❌ | ❌ | ✅ |

### User-Facing API

```python
from adc.library_loader import load_library

# Universal interface - works for ANY language
lib, metadata = load_library(workspace_path="./workspace")

# Check verification capabilities
print(f"Language: {metadata.detected_language}")
print(f"Bridge: {metadata.bridge_type}")
print(f"Signature verification: {metadata.supports_signature_verification}")

# Use library (same API regardless of language!)
result = lib.create_task(title="foo", description="bar")
tasks = lib.list_tasks()

# Introspect (if supported)
if metadata.supports_signature_verification:
    import inspect
    sig = inspect.signature(lib.create_task)
    print(f"Signature: {sig}")
```

## Phase 2: Native Bindings (Future)

### Goal
Enable FULL verification for compiled languages by requiring Python bindings.

### Binding Technologies

**Rust → PyO3**
```rust
use pyo3::prelude::*;

#[pyfunction]
fn create_task(title: String, description: String) -> PyResult<Task> {
    // Rust implementation
}

#[pymodule]
fn mytasks(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(create_task, m)?)?;
    Ok(())
}
```

Build: `maturin build --release`

**Go → ctypes (C-shared)**
```go
import "C"

//export CreateTask
func CreateTask(titlePtr *C.char, descPtr *C.char) *C.char {
    // Go implementation
}
```

Build: `go build -buildmode=c-shared -o libtasks.so`

**Java → Jep (Java Embedded Python)**
```python
import jep

with jep.Jep(classpath=["mytasks.jar"]) as j:
    result = j.invoke("com.example.TaskManager.createTask", "foo", "bar")
```

Build: `mvn package`

### Phase 2 Benefits
- Full signature verification for ALL languages
- Same token efficiency as Python (~1,600 tokens)
- No CLI limitations
- Complete type safety

### Phase 2 Trade-offs
- Requires developers to learn binding tools
- Additional build complexity
- Maintenance overhead for bindings

## Auditor Integration

### Before (Reading Files)
```python
def verify_compliance(contract_path, workspace_path):
    # Read all Python files
    files = glob(f"{workspace_path}/**/*.py")
    file_contents = [read_file(f) for f in files]  # 40,000+ tokens!

    # Parse and verify...
    return compliance_report
```

**Token Usage: 42,600 per audit**

### After (Library Loader)
```python
from adc.library_loader import load_library
from adc.library_loader.verifier import verify_compliance

def verify_compliance(contract_path, workspace_path):
    # Extract expected interface from contract (200 tokens)
    expected = extract_interface(contract_path)

    # Load library (0 tokens - runs locally)
    lib, metadata = load_library(workspace_path)

    # Verify compliance (1,400 tokens)
    result = verify_compliance(expected, lib, metadata, workspace_path)

    return result
```

**Token Usage: 1,600 per audit (96% reduction)**

## Implementation Roadmap

### Phase 1A: Core Infrastructure (Week 1)
- [ ] LibraryMetadata, VerificationResult models
- [ ] Language detection logic
- [ ] PythonBridge implementation
- [ ] MarkerVerifier implementation
- [ ] Unit tests

### Phase 1B: Node.js Support (Week 2)
- [ ] NodeBridge with JSON-RPC
- [ ] Subprocess management
- [ ] Integration tests

### Phase 1C: CLI Fallback (Week 3)
- [ ] CliFallbackBridge for Rust/Go/Java
- [ ] CLI detection and execution
- [ ] Limitation documentation
- [ ] Integration tests

### Phase 1D: Integration (Week 4)
- [ ] ContractInterfaceExtractor (parse ADC contracts)
- [ ] Full verification workflow
- [ ] Auditor integration
- [ ] End-to-end tests

### Phase 1E: Validation (Week 5)
- [ ] Token usage benchmarks
- [ ] Performance testing (all <3 seconds)
- [ ] Documentation
- [ ] Production readiness

### Phase 2 (Future - Based on Phase 1 Success)
- [ ] Rust PyO3 bindings (Week 6-7)
- [ ] Go ctypes bindings (Week 8-9)
- [ ] Java Jep bindings (Week 10-11)
- [ ] Auto-binding detection (Week 12)

## Success Metrics

### Token Efficiency (Primary Goal)
- **Target: 96%+ reduction in auditor token usage**
- Current: 42,600 tokens per audit
- Phase 1: 1,600-2,100 tokens per audit
- Measured: Run 48-task benchmark, compare before/after

### Performance (Secondary Goal)
- **Target: All verifications complete in <3 seconds**
- Python library loading: <100ms
- Node.js subprocess startup: <500ms
- CLI fallback execution: <200ms
- Marker grep (1000 files): <2 seconds

### Functional Requirements
- **Zero false negatives** (compliant projects must pass)
- **Clear error messages** for non-compliance
- **All languages supported** (even if limited verification)
- **Seamless auditor integration**

### Quality Requirements
- 90%+ test coverage
- All error paths tested
- Complete documentation
- Examples for each language

## Key Design Decisions

### 1. Progressive Enhancement Over Perfection
**Decision:** Ship Phase 1 with CLI fallback for compiled languages, even though it provides LIMITED verification.

**Rationale:**
- 98% token savings vs file reading (even better than full verification!)
- Gets value to users immediately
- CLI fallback always available as safety net
- Phase 2 bindings can enhance gradually

### 2. Fail-Fast Philosophy
**Decision:** Raise clear errors when verification fails, never silently substitute defaults.

**Rationale:**
- Prevents mask failures with fallback values
- Forces developers to fix actual issues
- Clear error messages guide to solutions
- Aligns with ADC functional design principles

### 3. No Optional Types
**Decision:** Use concrete types everywhere, fail if data unavailable.

**Rationale:**
- Aligns with ADC "no Optional types" principle
- Forces explicit handling of all cases
- Prevents None-checking defensive programming
- Makes API contracts clearer

### 4. Language Auto-Detection
**Decision:** Automatically detect language from workspace structure, allow manual override.

**Rationale:**
- Zero configuration for standard projects
- Handles polyglot projects gracefully
- Override available when needed
- Reduces user friction

### 5. Unified Python Interface
**Decision:** All languages expose same Python API regardless of implementation.

**Rationale:**
- Auditor doesn't need language-specific logic
- Easy to add new language bridges
- Enables language migration without auditor changes
- Consistent developer experience

## Risks and Mitigations

### Risk: Subprocess Overhead for Node.js
**Mitigation:** Cache Node.js subprocess for multiple verifications, reuse connection.

### Risk: Binding Setup Complexity (Phase 2)
**Mitigation:** Provide clear documentation, example projects, auto-build helpers.

### Risk: CLI Fallback Too Limited
**Mitigation:** Clearly document limitations, provide migration path to bindings, maintain marker verification.

### Risk: Language Detection Failures
**Mitigation:** Support manual language specification, provide clear errors with checked locations.

### Risk: Token Savings Lower Than Expected
**Mitigation:** Measure continuously, optimize verification prompts, cache common results.

## Contract Files

- **001-overview.qmd**: Main contract with Phase 1 implementation details
  - All design blocks, data models, algorithms
  - Python, Node.js, CLI fallback bridges
  - Auditor integration
  - Test scenarios and success criteria

- **002-phase2-bindings.qmd**: Future Phase 2 contract
  - Native bindings for Go, Rust, Java, C++
  - PyO3, ctypes, Jep implementation details
  - Build integration helpers
  - Migration path from CLI fallback

- **ARCHITECTURE_SUMMARY.md**: This file
  - High-level architecture overview
  - Token economics and ROI
  - Implementation roadmap
  - Design decisions and rationale

## References

### Related ADC Contracts
- `adc-cost-optimization-001.qmd`: Token overhead reduction strategies
- `refactor-evaluator-token-optimization-adc-041.qmd`: Similar token optimization approach

### External Documentation
- Python `importlib`: https://docs.python.org/3/library/importlib.html
- Python `inspect`: https://docs.python.org/3/library/inspect.html
- PyO3 (Rust): https://pyo3.rs/
- Jep (Java): https://github.com/ninia/jep
- ctypes (Python): https://docs.python.org/3/library/ctypes.html

## Questions for Implementation

1. **Marker Format:** Should we standardize on `# ADC-IMPLEMENTS: <block-id>` for all languages, or allow language-specific comment styles?
   - Recommendation: Allow language-specific (`//`, `#`, `/**/`) but enforce format consistency

2. **Caching:** Should we cache loaded libraries across multiple verifications to save startup time?
   - Recommendation: Yes for Node.js subprocess, optional for Python (depends on import side effects)

3. **Error Granularity:** How detailed should error messages be for signature mismatches?
   - Recommendation: Show expected vs found signature, list specific parameter differences

4. **Phase 2 Trigger:** What success metrics determine when to implement Phase 2 bindings?
   - Recommendation: If >10 projects need compiled language verification AND token savings hold in production

5. **Multi-Language Projects:** How to handle Bazel projects with multiple languages?
   - Recommendation: Load each language component separately, aggregate verification results
