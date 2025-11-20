#!/bin/bash
# Simple Docker test for ADC package

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
WHEEL_NAME=$(basename "$WHEEL_FILE")
echo ""

# Create simple Dockerfile
cat > Dockerfile.test <<'EOF'
FROM python:3.11-slim
RUN pip install --quiet pipx
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser
ENV PATH="/home/testuser/.local/bin:$PATH"
CMD ["/bin/bash"]
EOF

echo "🏗️  Building test Docker image..."
docker build -f Dockerfile.test -t adc-test . -q

echo "✅ Docker image built"
echo ""
echo "🧪 Running tests..."
echo ""

# Run tests
docker run --rm -v "$(pwd)/dist:/dist" adc-test bash -c "
set -e

echo '=== Test 1: Install package ==='
pipx install '/dist/$WHEEL_NAME[all]'
echo '✅ Package installed'
echo ''

echo '=== Test 2: Check CLI ==='
adc --help | head -3
echo '✅ adc command works'
echo ''

echo '=== Test 3: Run adc-setup ==='
adc-setup
echo '✅ adc-setup completed'
echo ''

echo '=== Test 4: Verify files ==='
echo 'Commands:'
ls ~/.claude/commands/ 2>/dev/null || echo '  No commands'
echo ''
echo 'Agents:'
ls ~/.claude/agents/adc-*.md 2>/dev/null | wc -l | xargs echo '  Found' 
echo ''

if [ -f ~/.claude/commands/adc.md ]; then
    echo '✅ /adc command installed'
else
    echo '❌ /adc command NOT found'
    exit 1
fi

AGENT_COUNT=\$(ls ~/.claude/agents/adc-*.md 2>/dev/null | wc -l | tr -d ' ')
if [ \"\$AGENT_COUNT\" -ge 7 ]; then
    echo \"✅ Found \$AGENT_COUNT agents\"
else
    echo \"❌ Expected 7+ agents, found \$AGENT_COUNT\"
    exit 1
fi
echo ''

echo '=== Test 5: Check adc health ==='
adc health
echo '✅ adc health works'
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
    exit 0
else
    echo ""
    echo "❌ ❌ ❌  TESTS FAILED! ❌ ❌ ❌"
    exit 1
fi
