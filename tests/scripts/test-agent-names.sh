#!/bin/bash
# Test for unique agent names (no duplicates)

set -e

echo "🧪 Testing agent names for duplicates..."
echo ""

WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
WHEEL_NAME=$(basename "$WHEEL_FILE")

# Create Dockerfile
cat > Dockerfile.agent-test <<'EOF'
FROM python:3.11-slim
RUN pip install pipx
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser
ENV PATH="/home/testuser/.local/bin:$PATH"
CMD ["/bin/bash"]
EOF

echo "🏗️  Building test image..."
docker build -f Dockerfile.agent-test -t adc-agent-test . -q

echo "✅ Image built"
echo ""
echo "🧪 Testing agent name uniqueness..."
echo ""

# Run test
docker run --rm -v "$(pwd)/dist:/dist" adc-agent-test bash -c "
set -e

echo '=== Installing ADC ==='
pipx install '/dist/$WHEEL_NAME[all]' > /dev/null 2>&1
echo '✅ Installed'
echo ''

echo '=== Running adc-setup ==='
adc-setup > /dev/null 2>&1
echo '✅ Setup complete'
echo ''

echo '=== Checking agent names ==='
echo ''
echo 'Agent files installed:'
ls ~/.claude/agents/adc-*.md | wc -l | xargs echo '  Total files:'
echo ''

echo 'Agent names in frontmatter:'
grep '^name:' ~/.claude/agents/adc-*.md | sort
echo ''

echo 'Checking for duplicates...'
DUPLICATES=\$(grep '^name:' ~/.claude/agents/adc-*.md | cut -d: -f2 | sort | uniq -d)

if [ -z \"\$DUPLICATES\" ]; then
    echo '✅ No duplicate agent names found!'
    echo ''
    echo 'All agent names are unique:'
    grep '^name:' ~/.claude/agents/adc-*.md | cut -d: -f2 | sort | sed 's/^/  ✓ /'
    exit 0
else
    echo '❌ DUPLICATE AGENT NAMES FOUND:'
    echo \"\$DUPLICATES\" | sed 's/^/  ⚠️  /'
    exit 1
fi
"

TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f Dockerfile.agent-test
docker rmi adc-agent-test -f > /dev/null 2>&1

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ ✅ ✅  AGENT NAME TEST PASSED! ✅ ✅ ✅"
    echo ""
    echo "No duplicate agent names - ready for deployment!"
    exit 0
else
    echo ""
    echo "❌ ❌ ❌  AGENT NAME TEST FAILED! ❌ ❌ ❌"
    exit 1
fi
