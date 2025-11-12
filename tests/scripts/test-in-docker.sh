#!/bin/bash
# Test ADC package in isolated Docker container

set -e

echo "🐳 Testing ADC package in Docker..."
echo ""

# Check if wheel file exists
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
if [ ! -f "$WHEEL_FILE" ]; then
    echo "❌ ERROR: No wheel file found in dist/"
    echo "Run ./build-package-improved.sh first"
    exit 1
fi

echo "📦 Found wheel: $WHEEL_FILE"
echo ""

# Create Dockerfile
cat > Dockerfile.test <<'EOF'
FROM python:3.11-slim

# Install pipx
RUN pip install --quiet pipx

# Create test user
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser

# Set up PATH for pipx
ENV PATH="/home/testuser/.local/bin:$PATH"

CMD ["/bin/bash"]
EOF

echo "🏗️  Building test Docker image..."
docker build -f Dockerfile.test -t adc-test . -q

echo "✅ Docker image built"
echo ""
echo "🧪 Running installation tests..."
echo ""

# Get wheel filename
WHEEL_NAME=$(basename "$WHEEL_FILE")

# Run tests in container
docker run --rm -v "$(pwd)/dist:/dist" adc-test bash -c "
set -e

echo '=== Test 1: Install package ==='
pipx install '/dist/$WHEEL_NAME[all]'
echo '✅ Package installed'
echo ''

echo "=== Test 2: Check CLI commands ==="
adc --version || adc --help | head -5
echo "✅ adc command works"
echo ""

echo "=== Test 3: Run adc-setup ==="
adc-setup
echo "✅ adc-setup completed"
echo ""

echo "=== Test 4: Verify Claude Code files ==="
echo "Commands:"
ls -la ~/.claude/commands/ 2>/dev/null || echo "  No commands directory"
echo ""
echo "Agents:"
ls -la ~/.claude/agents/ 2>/dev/null || echo "  No agents directory"
echo ""

if [ -f ~/.claude/commands/adc.md ]; then
    echo "✅ /adc command installed"
else
    echo "❌ /adc command NOT found"
    exit 1
fi

AGENT_COUNT=$(ls ~/.claude/agents/adc-*.md 2>/dev/null | wc -l | tr -d " ")
echo "Found $AGENT_COUNT agents"
if [ "$AGENT_COUNT" -ge 7 ]; then
    echo "✅ All agents installed"
else
    echo "❌ Expected 7 agents, found $AGENT_COUNT"
    exit 1
fi
echo ""

echo "=== Test 5: Check adc health ==="
adc health
echo "✅ adc health works"
echo ""

echo "=== Test 6: List installed agents ==="
ls ~/.claude/agents/adc-*.md | xargs -n1 basename
echo ""

echo '=== Test 7: Verify package data ==='
python3 << 'PYEOF'
import importlib.resources as resources
import adc

# Check roles
try:
    roles_path = resources.files(adc) / "roles"
    roles = list(roles_path.iterdir())
    print(f"Roles: {len(roles)} files")
    if len(roles) < 5:
        print("❌ Expected at least 5 roles")
        exit(1)
except Exception as e:
    print(f"❌ Error accessing roles: {e}")
    exit(1)

# Check schema
try:
    schema_path = resources.files(adc) / "schema"
    schemas = list(schema_path.iterdir())
    print(f"Schema: {len(schemas)} files")
    if len(schemas) < 1:
        print("❌ Expected at least 1 schema file")
        exit(1)
except Exception as e:
    print(f"❌ Error accessing schema: {e}")
    exit(1)

# Check claude files
try:
    claude_path = resources.files(adc) / "claude"
    agents_path = claude_path / "agents"
    agents = list(agents_path.iterdir())
    print(f"Agents: {len(agents)} files")
    if len(agents) < 7:
        print("❌ Expected at least 7 agent files")
        exit(1)
except Exception as e:
    print(f"❌ Error accessing claude files: {e}")
    exit(1)

print("✅ All package data accessible")
PYEOF
echo ''

echo '=== All Tests Passed! ==='
"

TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f Dockerfile.test
docker rmi adc-test -f > /dev/null 2>&1

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ ✅ ✅  ALL TESTS PASSED! ✅ ✅ ✅"
    echo ""
    echo "Package is ready for distribution!"
    echo ""
    echo "Next steps:"
    echo "1. Test on Test PyPI:"
    echo "   python3 -m twine upload --repository testpypi dist/*"
    echo ""
    echo "2. If Test PyPI works, publish to real PyPI:"
    echo "   python3 -m twine upload dist/*"
    exit 0
else
    echo ""
    echo "❌ ❌ ❌  TESTS FAILED! ❌ ❌ ❌"
    echo ""
    echo "Fix the issues before distributing."
    exit 1
fi
