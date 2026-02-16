#!/usr/bin/env python3
"""
Test script to demonstrate the contract linting functionality
"""

import os
import sys
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from adc_cli.contract_lint import ContractLinter


def create_test_file():
    """Create a test file with common formatting issues"""
    content = """# Test Contract ADC-001

## Purpose
This is a test contract with various formatting issues.

**Capabilities**
* Process audio at 16kHz sample rate
  - Handle stereo to mono conversion
    * Apply proper averaging
  - Detect wake words with high accuracy

**Requirements**
- Model must support ONNX Runtime 1.19+
- Audio processing must be real-time
* Use consistent bullet points

## Implementation

### Mermaid Diagram

```mermaid
graph TD
    A[Audio Input (with parens)] --> B[Processing & Analysis]
    B -- Process Audio --> C[Wake Word Detection]
    C --> D[Action Handler]
```

### Code Example

```python
def process_audio(audio_data):
    # This code should not be modified
    return audio_data * 0.5
```

| Feature | Status |
|---------|--------|
| Audio Capture | Complete |
| Wake Word | In Progress |
| Action Handler | Planned |

## Testing
1. Unit tests for each component
2.Integration tests for full pipeline
3.    Performance benchmarks

**Note**
This contract demonstrates various formatting issues that the linter should fix.
"""
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='-adc-test.md', delete=False) as f:
        f.write(content)
        return f.name


def main():
    """Run the linting test"""
    print("Contract Linting Test")
    print("=" * 50)
    
    # Create test file
    test_file = create_test_file()
    print(f"Created test file: {test_file}\n")
    
    # Read original content
    with open(test_file, 'r') as f:
        original = f.read()
    
    print("Original content preview:")
    print("-" * 30)
    print(original[:300] + "...\n")
    
    # Configure and run linter
    config = {
        'auto_fix': True,
        'backup_originals': True,
        'verbose': True
    }
    
    linter = ContractLinter(config)
    results = linter.lint_contract_file(test_file)
    
    # Display results
    print("\nLinting Results:")
    print("-" * 30)
    print(f"Fixes applied: {', '.join(results['fixes_applied'])}")
    
    if results['warnings']:
        print(f"\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    # Show fixed content preview
    if results['file_updated']:
        with open(test_file, 'r') as f:
            fixed = f.read()
        
        print("\nFixed content preview:")
        print("-" * 30)
        print(fixed[:300] + "...\n")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    if os.path.exists(test_file + '.backup'):
        os.remove(test_file + '.backup')
    
    print("✨ Test complete!")


if __name__ == '__main__':
    main()
