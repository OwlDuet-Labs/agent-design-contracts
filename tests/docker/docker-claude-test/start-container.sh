#!/bin/bash
# Start Docker container for Claude Code testing

set -e

echo "🐳 Starting Claude Code test container..."
echo ""

# Build the image
echo "🏗️  Building Docker image..."
docker build -t adc-claude-test .

echo "✅ Image built"
echo ""

# Check if wheel file exists
WHEEL_FILE=$(ls ../dist/*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL_FILE" ]; then
    echo "❌ No wheel file found in ../dist/"
    echo "Run: cd .. && ./build-package-improved.sh"
    exit 1
fi

WHEEL_NAME=$(basename "$WHEEL_FILE")
echo "📦 Found wheel: $WHEEL_NAME"
echo ""

# Start container
echo "🚀 Starting container..."
CONTAINER_ID=$(docker run -d \
    -p 2222:22 \
    -v "$(cd .. && pwd)/dist:/dist:ro" \
    --name adc-claude-test \
    adc-claude-test)

echo "✅ Container started: $CONTAINER_ID"
echo ""

# Wait for SSH to be ready
echo "⏳ Waiting for SSH to be ready..."
sleep 3

# Install ADC in the container
echo "📥 Installing ADC in container..."
docker exec -u testuser adc-claude-test bash -c "
    python3 -m pipx install /dist/$WHEEL_NAME[all] 2>&1 | tail -3
    export PATH=\"/home/testuser/.local/bin:\$PATH\"
    adc-setup 2>&1 | grep -E '(✓|✅|Setup complete)'
"

echo ""
echo "✅ ADC installed successfully!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Container is ready for Claude Code testing!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Connection details:"
echo "   Host: localhost"
echo "   Port: 2222"
echo "   User: testuser"
echo "   Pass: testuser"
echo ""
echo "🔧 SSH command:"
echo "   ssh -p 2222 testuser@localhost"
echo ""
echo "📁 ADC files installed at:"
echo "   ~/.claude/commands/adc.md"
echo "   ~/.claude/agents/adc-*.md (10 agents)"
echo ""
echo "🧪 To test:"
echo "   1. SSH into container: ssh -p 2222 testuser@localhost"
echo "   2. Install Claude Code in the container"
echo "   3. Authenticate with your account"
echo "   4. Check if agents load without duplicate errors"
echo ""
echo "🛑 To stop container:"
echo "   docker stop adc-claude-test"
echo "   docker rm adc-claude-test"
echo ""
echo "🔍 To check agent names:"
echo "   docker exec -u testuser adc-claude-test grep '^name:' ~/.claude/agents/adc-*.md"
echo ""
