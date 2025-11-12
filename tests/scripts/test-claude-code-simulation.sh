#!/bin/bash
# Simulate Claude Code agent loading to detect duplicate names

set -e

echo "🧪 Simulating Claude Code agent loading..."
echo ""

WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
WHEEL_NAME=$(basename "$WHEEL_FILE")

# Create Dockerfile
cat > Dockerfile.claude-test <<'EOF'
FROM python:3.11-slim
RUN pip install pipx pyyaml
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser
ENV PATH="/home/testuser/.local/bin:$PATH"
CMD ["/bin/bash"]
EOF

echo "🏗️  Building test image..."
docker build -f Dockerfile.claude-test -t adc-claude-test . -q

echo "✅ Image built"
echo ""
echo "🧪 Simulating Claude Code agent registration..."
echo ""

# Run test that simulates Claude Code's agent loading
docker run --rm -v "$(pwd)/dist:/dist" adc-claude-test bash -c '
set -e

echo "=== Installing ADC ==="
pipx install "/dist/'"$WHEEL_NAME"'[all]" > /dev/null 2>&1
echo "✅ Installed"
echo ""

echo "=== Running adc-setup ==="
adc-setup > /dev/null 2>&1
echo "✅ Setup complete"
echo ""

echo "=== Simulating Claude Code Agent Loading ==="
echo ""

# Create Python script to simulate Claude Code agent loading
cat > test_agent_loading.py << "PYEOF"
import os
import yaml
from pathlib import Path
from collections import defaultdict

def load_agent_frontmatter(file_path):
    """Load YAML frontmatter from agent file."""
    with open(file_path, "r") as f:
        content = f.read()
    
    # Extract frontmatter between --- markers
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                return yaml.safe_load(parts[1])
            except:
                return None
    return None

def check_duplicate_agents():
    """Simulate Claude Code checking for duplicate agent names."""
    agents_dir = Path.home() / ".claude" / "agents"
    
    if not agents_dir.exists():
        print("❌ Agents directory not found")
        return False
    
    # Load all agent files
    agent_files = list(agents_dir.glob("*.md"))
    print(f"Found {len(agent_files)} agent files")
    print()
    
    # Track agent names and their files
    agent_names = defaultdict(list)
    
    for agent_file in agent_files:
        frontmatter = load_agent_frontmatter(agent_file)
        if frontmatter and "name" in frontmatter:
            name = frontmatter["name"]
            agent_names[name].append(agent_file.name)
            print(f"  ✓ {agent_file.name} → name: {name}")
    
    print()
    
    # Check for duplicates
    duplicates = {name: files for name, files in agent_names.items() if len(files) > 1}
    
    if duplicates:
        print("❌ DUPLICATE AGENT NAMES DETECTED!")
        print()
        print("Claude Code would show this error:")
        print()
        print("  Duplicate Agent Names Found:")
        print()
        for i, (name, files) in enumerate(duplicates.items(), 1):
            print(f"  {i}. {name} appears in:")
            for file in files:
                print(f"    - ~/.claude/agents/{file}")
        print()
        return False
    else:
        print("✅ NO DUPLICATE AGENT NAMES!")
        print()
        print("All agent names are unique:")
        for name in sorted(agent_names.keys()):
            print(f"  ✓ {name}")
        print()
        return True

if __name__ == "__main__":
    success = check_duplicate_agents()
    exit(0 if success else 1)
PYEOF

# Run the simulation
python3 test_agent_loading.py
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ Claude Code simulation PASSED"
    echo "   Agents would load without errors"
else
    echo ""
    echo "❌ Claude Code simulation FAILED"
    echo "   Would show duplicate tools registered error"
fi

exit $TEST_RESULT
'

TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f Dockerfile.claude-test
docker rmi adc-claude-test -f > /dev/null 2>&1

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ ✅ ✅  CLAUDE CODE SIMULATION PASSED! ✅ ✅ ✅"
    echo ""
    echo "Agents will load in Claude Code without duplicate errors!"
    exit 0
else
    echo ""
    echo "❌ ❌ ❌  CLAUDE CODE SIMULATION FAILED! ❌ ❌ ❌"
    echo ""
    echo "Claude Code would show duplicate tools registered error"
    exit 1
fi
