# Universal Library Loader - Implementation Checklist

## Contract Overview

**Contract IDs:**
- `universal-library-loader-adc-001` (Phase 1: Core Implementation)
- `universal-library-loader-adc-002` (Phase 2: Native Bindings - Future)

**Total Design Blocks:**
- Phase 1 Contract: 25 blocks (3 Rationale, 2 Implementation, 2 Constraint, 2 DataModel, 7 Feature, 1 Tool, 1 Algorithm, 1 Integration, 4 TestScenario, 2 Parity)
- Phase 2 Contract: 12 blocks (2 Rationale, 3 Implementation, 2 Feature, 1 Constraint, 2 TestScenario, 2 Parity)

**Lines of Specification:**
- Phase 1: 1,881 lines
- Phase 2: 936 lines
- Total: 2,817 lines of implementable specification

---

## Phase 1: Core Implementation (5 Weeks)

### Week 1: Core Infrastructure
**Goal:** Foundational data models and Python bridge

- [ ] `src/adc/library_loader/metadata.py`
  - [ ] `LanguageType` enum (7 language types)
  - [ ] `BridgeType` enum (6 bridge types)
  - [ ] `LibraryMetadata` dataclass
  - [ ] Tests: `tests/test_library_metadata.py`

- [ ] `src/adc/library_loader/verification.py`
  - [ ] `SignatureMismatch` dataclass
  - [ ] `VerificationResult` dataclass with `compliance_score` property
  - [ ] Tests: `tests/test_verification_result.py`

- [ ] `src/adc/library_loader/detection.py`
  - [ ] `LANGUAGE_INDICATORS` dict (6 languages × 3-5 indicators each)
  - [ ] `detect_language()` function
  - [ ] Error handling for unknown languages
  - [ ] Tests: `tests/test_language_detection.py`

- [ ] `src/adc/library_loader/bridges/python_bridge.py`
  - [ ] `PythonBridge` class with `load()`, `get_signature()`, `verify_signature()`
  - [ ] Module name detection from setup.py/pyproject.toml
  - [ ] Proxy object creation with all public functions
  - [ ] Tests: `tests/bridges/test_python_bridge.py`

- [ ] `src/adc/library_loader/marker_verifier.py`
  - [ ] `MarkerVerifier` class
  - [ ] `find_markers()` using ripgrep (rg)
  - [ ] `verify_coverage()` for required block IDs
  - [ ] Fallback to grep if rg unavailable
  - [ ] Tests: `tests/test_marker_verifier.py`

**Success Criteria:**
- All unit tests passing
- Python library loading works end-to-end
- Marker verification finds ADC-IMPLEMENTS in test fixtures
- Coverage >90%

---

### Week 2: Node.js Support
**Goal:** JSON-RPC bridge for Node.js libraries

- [ ] `src/adc/library_loader/bridges/node_bridge.py`
  - [ ] `NodeBridge` class with subprocess management
  - [ ] `_create_rpc_server()` generates temporary JSON-RPC server script
  - [ ] `_call_function()` sends JSON-RPC requests via stdin/stdout
  - [ ] Proxy object creation with dynamic method binding
  - [ ] Subprocess cleanup in `__del__`
  - [ ] Tests: `tests/bridges/test_node_bridge.py`

- [ ] `tests/fixtures/nodejs-api/`
  - [ ] Sample Node.js project with package.json
  - [ ] Simple API functions (createTask, listTasks)
  - [ ] TypeScript type definitions if possible
  - [ ] ADC-IMPLEMENTS markers in source

**Success Criteria:**
- Node.js subprocess starts successfully (<500ms)
- JSON-RPC communication works bidirectionally
- Functions callable from Python
- TypeScript types introspectable (if .d.ts available)
- All tests passing

---

### Week 3: CLI Fallback
**Goal:** Generic CLI execution for compiled languages

- [ ] `src/adc/library_loader/bridges/cli_fallback.py`
  - [ ] `CliFallbackBridge` class
  - [ ] `_detect_cli_executable()` searches bin/, build/, target/release/, dist/
  - [ ] `verify_commands_exist()` checks CLI commands via --help
  - [ ] Proxy object for CLI command execution
  - [ ] Clear error messages for missing executable
  - [ ] Documentation of verification limitations
  - [ ] Tests: `tests/bridges/test_cli_fallback.py`

- [ ] `tests/fixtures/rust-cli/`
  - [ ] Sample Rust CLI project with Cargo.toml
  - [ ] CLI commands: create, list, complete, delete
  - [ ] Build instructions in README
  - [ ] ADC-IMPLEMENTS markers in Rust source

**Success Criteria:**
- CLI executable found in standard locations
- All commands verified via --help parsing
- Proxy executes commands successfully
- Limitations clearly documented
- All tests passing

---

### Week 4: Integration
**Goal:** Contract parsing and full verification workflow

- [ ] `src/adc/library_loader/contract_extractor.py`
  - [ ] `ExpectedInterface` dataclass
  - [ ] `FunctionSignature` dataclass
  - [ ] `ContractInterfaceExtractor` class
  - [ ] `_extract_functions()` parses APIEndpoint/Feature blocks
  - [ ] `_extract_block_ids()` finds all <block-id> markers
  - [ ] `_extract_contract_id()` from YAML front matter
  - [ ] Tests: `tests/test_contract_extractor.py`

- [ ] `src/adc/library_loader/verifier.py`
  - [ ] `verify_compliance()` implements full algorithm from <ull-algo-01>
  - [ ] Function existence checks
  - [ ] Signature verification (if supported)
  - [ ] Marker verification (always)
  - [ ] Compliance score calculation
  - [ ] Tests: `tests/test_verifier.py`

- [ ] `src/adc/library_loader/__init__.py`
  - [ ] `load_library()` main entry point
  - [ ] `_select_bridge()` chooses appropriate bridge
  - [ ] Auto-detection with manual override
  - [ ] Metadata creation and error handling
  - [ ] Tests: `tests/test_load_library.py`

**Success Criteria:**
- Contract parsing extracts all required interface elements
- Full verification workflow completes successfully
- All bridges integrated via load_library()
- Error messages clear and actionable
- All tests passing

---

### Week 5: Validation & Production Readiness
**Goal:** Performance testing, token measurement, documentation

- [ ] `tests/integration/test_python_verification.py`
  - [ ] End-to-end test on sample Python project
  - [ ] Verify all functions found and signatures match
  - [ ] Measure token usage (<2,000 tokens)
  - [ ] Measure performance (<500ms)

- [ ] `tests/integration/test_nodejs_verification.py`
  - [ ] End-to-end test on sample Node.js project
  - [ ] Verify subprocess communication
  - [ ] Measure token usage (<2,000 tokens)
  - [ ] Measure performance (<1,000ms including subprocess startup)

- [ ] `tests/integration/test_rust_cli_verification.py`
  - [ ] End-to-end test on sample Rust CLI project
  - [ ] Verify CLI fallback limitations documented
  - [ ] Measure token usage (<1,200 tokens)
  - [ ] Measure performance (<500ms)

- [ ] `tests/performance/test_token_measurement.py`
  - [ ] Test 5 diverse projects (Python, Node.js, Rust, Go, mixed)
  - [ ] Compare library loading vs file reading
  - [ ] Aggregate savings (target: 96%+ average)
  - [ ] Generate benchmark report

- [ ] Documentation
  - [ ] `docs/token-efficiency-benchmarks.md` with measured results
  - [ ] `docs/verification-capabilities.md` per-language matrix
  - [ ] API reference for load_library()
  - [ ] Error handling guide
  - [ ] Examples for each language

**Success Criteria:**
- All integration tests passing
- Token savings ≥96% on average
- All verifications complete in <3 seconds
- Documentation complete and clear
- Ready for auditor integration

---

## Auditor Integration

**Goal:** Replace file reading with library loading in compliance auditor

- [ ] Update `src/adc/agents/compliance_auditor.py`
  - [ ] Import library_loader
  - [ ] Replace file reading with `load_library()`
  - [ ] Use `verify_compliance()` from verifier
  - [ ] Maintain same compliance scoring logic
  - [ ] Generate same format reports

- [ ] Integration tests
  - [ ] Run auditor on sample projects before/after
  - [ ] Verify compliance scores match
  - [ ] Measure token reduction
  - [ ] Confirm no functionality regression

**Success Criteria:**
- Auditor token usage reduced by 96%
- All compliance checks still work
- No false negatives
- Reports maintain same format

---

## Phase 2: Native Bindings (Future - 12 Weeks)

**Only implement if Phase 1 succeeds AND demand exists for compiled language verification**

### Week 6-7: Rust PyO3 Support
- [ ] `src/adc/library_loader/bridges/rust_bridge.py`
- [ ] Example Rust project with PyO3 bindings
- [ ] Documentation: `docs/rust-binding-setup.md`
- [ ] Tests: Full signature verification for Rust

### Week 8-9: Go ctypes Support
- [ ] `src/adc/library_loader/bridges/go_bridge.py`
- [ ] Example Go project with C-shared build
- [ ] Documentation: `docs/go-binding-setup.md`
- [ ] Tests: Full signature verification for Go

### Week 10-11: Java Jep Support
- [ ] `src/adc/library_loader/bridges/java_bridge.py`
- [ ] Example Java project with Jep integration
- [ ] Documentation: `docs/java-binding-setup.md`
- [ ] Tests: Full signature verification for Java

### Week 12: Auto-Binding Detection
- [ ] Update `_select_bridge()` to prefer bindings over CLI
- [ ] `_has_pyo3_bindings()`, `_has_go_shared_library()`, `_has_jar_file()`
- [ ] Build integration helpers
- [ ] Migration documentation

---

## File Structure Summary

```
src/adc/library_loader/
  __init__.py                      # load_library() entry point
  metadata.py                       # LibraryMetadata, enums
  verification.py                   # VerificationResult
  detection.py                      # Language detection
  contract_extractor.py             # Parse ADC contracts
  verifier.py                       # Full verification workflow
  marker_verifier.py                # ADC-IMPLEMENTS grep

  bridges/
    __init__.py
    python_bridge.py                # Phase 1
    node_bridge.py                  # Phase 1
    cli_fallback.py                 # Phase 1
    go_bridge.py                    # Phase 2
    rust_bridge.py                  # Phase 2
    java_bridge.py                  # Phase 2

tests/
  test_library_metadata.py
  test_verification_result.py
  test_language_detection.py
  test_contract_extractor.py
  test_verifier.py
  test_marker_verifier.py
  test_load_library.py

  bridges/
    test_python_bridge.py
    test_node_bridge.py
    test_cli_fallback.py
    test_go_bridge.py               # Phase 2
    test_rust_bridge.py             # Phase 2
    test_java_bridge.py             # Phase 2

  integration/
    test_python_verification.py
    test_nodejs_verification.py
    test_rust_cli_verification.py
    test_rust_pyo3_verification.py  # Phase 2
    test_go_ctypes_verification.py  # Phase 2
    test_java_jep_verification.py   # Phase 2

  performance/
    test_token_measurement.py

  fixtures/
    python-todo/
    nodejs-api/
    rust-cli/
    rust-pyo3-tasks/                # Phase 2
    go-ctypes-tasks/                # Phase 2
    java-jep-tasks/                 # Phase 2

docs/
  token-efficiency-benchmarks.md
  verification-capabilities.md
  phase2-binding-guide.md           # Phase 2
  go-binding-setup.md               # Phase 2
  rust-binding-setup.md             # Phase 2
  java-binding-setup.md             # Phase 2
```

---

## Success Metrics - Final Validation

### Token Efficiency (Must Achieve)
- [ ] Python verification: <2,000 tokens (vs 42,600 current)
- [ ] Node.js verification: <2,000 tokens (vs 45,000+ current)
- [ ] Rust/Go CLI: <1,200 tokens (vs 40,000+ current)
- [ ] **Overall: 96%+ token reduction**
- [ ] 48-task benchmark: $18.42 → $0.69 (97% cost savings)

### Performance (Must Achieve)
- [ ] Library load time: <500ms (Python/Node.js)
- [ ] CLI detection: <200ms
- [ ] Marker verification: <2 seconds (1000 files)
- [ ] Total verification: <3 seconds

### Functional (Must Achieve)
- [ ] Zero false negatives (compliant projects pass)
- [ ] Clear error messages for non-compliance
- [ ] All languages supported
- [ ] Auditor integration seamless

### Quality (Should Achieve)
- [ ] 90%+ test coverage
- [ ] All error paths tested
- [ ] Documentation complete
- [ ] Examples for each language

---

## Risk Mitigation Checklist

- [ ] **Node.js subprocess overhead:** Cache subprocess, reuse connections
- [ ] **CLI fallback limitations:** Document clearly, provide Phase 2 path
- [ ] **Language detection failures:** Support manual override, clear errors
- [ ] **Token savings lower than expected:** Measure continuously, optimize prompts
- [ ] **Binding setup complexity (Phase 2):** Provide examples, auto-build helpers

---

## Definition of Done

**Phase 1 is COMPLETE when:**
1. All Phase 1 checklist items complete
2. All tests passing with >90% coverage
3. Token usage benchmarks show 96%+ savings
4. Performance targets met (<3 seconds)
5. Auditor integration works end-to-end
6. Documentation complete
7. Code reviewed and approved
8. Deployed to production
9. Monitoring shows expected token savings

**Phase 2 is TRIGGERED when:**
1. Phase 1 deployed successfully
2. Token savings validated in production
3. Demand exists for compiled language verification (>10 projects)
4. Team capacity available (12 weeks)

---

## Quick Start for Implementers

1. **Read the contracts:**
   - `001-overview.qmd` - Full Phase 1 specification
   - `002-phase2-bindings.qmd` - Future Phase 2 details
   - `ARCHITECTURE_SUMMARY.md` - High-level overview

2. **Start with Week 1:**
   - Implement data models (metadata.py, verification.py)
   - Build Python bridge (simplest, no subprocess)
   - Get marker verification working
   - Validate with unit tests

3. **Follow weekly milestones:**
   - Each week builds on previous work
   - Integration tests validate end-to-end
   - Token measurements confirm savings

4. **Use test fixtures:**
   - Create sample projects for each language
   - Include ADC-IMPLEMENTS markers
   - Document build/run instructions

5. **Measure continuously:**
   - Token usage per verification
   - Performance timings
   - Compliance score accuracy
   - Error message clarity

Good luck! This contract provides a complete, implementable specification for 96% token savings.
