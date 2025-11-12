#!/bin/bash
# Test for duplicate tools registration issue

set -e

echo "🧪 Testing for duplicate tools registration issue..."
echo ""

# Check if wheel exists
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
if [ ! -f "$WHEEL_FILE" ]; then
    echo "❌ No wheel file found. Building..."
    ./build-package-improved.sh
    WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
fi

WHEEL_NAME=$(basename "$WHEEL_FILE")
echo "📦 Using wheel: $WHEEL_NAME"
echo ""

# Create Dockerfile
cat > Dockerfile.duplicate-test <<'EOF'
FROM python:3.11-slim

RUN pip install pipx
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser
ENV PATH="/home/testuser/.local/bin:$PATH"

CMD ["/bin/bash"]
EOF

echo "🏗️  Building test image..."
docker build -f Dockerfile.duplicate-test -t adc-duplicate-test . -q

echo "✅ Image built"
echo ""
echo "🧪 Running installation and command tests..."
echo ""

# Run comprehensive test
docker run --rm -v "$(pwd)/dist:/dist" adc-duplicate-test bash -c "
set -e

echo '=== Installing ADC ==='
pipx install '/dist/$WHEEL_NAME[all]' 2>&1 | tail -5
echo ''

echo '=== Testing adc --help ==='
adc --help 2>&1 | head -10
echo ''

echo '=== Testing adc health ==='
adc health 2>&1
echo ''

echo '=== Testing adc get-role --list ==='
adc get-role --list 2>&1
echo ''

echo '=== Testing adc validate --help ==='
adc validate --help 2>&1 | head -5
echo ''

echo '=== All commands tested successfully ==='
"

TEST_RESULT=$?

# Cleanup
echo ""
echo "🧹 Cleaning up..."
rm -f Dockerfile.duplicate-test
docker rmi adc-duplicate-test -f > /dev/null 2>&1

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo "✅ No duplicate tools registration issue found!"
    exit 0
else
    echo ""
    echo "❌ Test failed - issue detected"
    exit 1
fi
