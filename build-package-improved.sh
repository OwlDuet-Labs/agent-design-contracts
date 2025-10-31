#!/bin/bash
# Build ADC distributable package with data file preparation and verification

set -e

echo "🔨 Building ADC distributable package..."
echo ""

# Step 1: Prepare package data directories
echo "📋 Preparing package data directories..."
mkdir -p src/adc/roles
mkdir -p src/adc/schema
mkdir -p src/adc/claude/commands
mkdir -p src/adc/claude/agents

# Step 2: Copy data files
echo "📦 Copying data files to package..."

# Copy roles
if [ -d "roles" ]; then
    cp -r roles/*.md src/adc/roles/ 2>/dev/null && echo "  ✅ Copied roles" || echo "  ⚠️  No roles to copy"
else
    echo "  ⚠️  roles/ directory not found"
fi

# Copy schema
if [ -f "adc-schema.qmd" ]; then
    cp adc-schema.qmd src/adc/schema/ && echo "  ✅ Copied schema" || echo "  ⚠️  Failed to copy schema"
else
    echo "  ⚠️  adc-schema.qmd not found"
fi

# Copy Claude command
if [ -f ".claude/commands/adc.md" ]; then
    cp .claude/commands/adc.md src/adc/claude/commands/ && echo "  ✅ Copied /adc command" || echo "  ⚠️  Failed to copy command"
else
    echo "  ⚠️  .claude/commands/adc.md not found"
fi

# Copy Claude agents
if [ -d ".claude/agents" ]; then
    cp .claude/agents/adc-*.md src/adc/claude/agents/ 2>/dev/null && echo "  ✅ Copied agents" || echo "  ⚠️  No agents to copy"
else
    echo "  ⚠️  .claude/agents/ directory not found"
fi

echo ""
echo "📊 Package data summary:"
echo "  Roles: $(ls src/adc/roles/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Schema: $(ls src/adc/schema/*.qmd 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Commands: $(ls src/adc/claude/commands/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Agents: $(ls src/adc/claude/agents/*.md 2>/dev/null | wc -l | tr -d ' ') files"
echo ""

# Step 3: Check if build tools are installed
if ! python3 -c "import build" 2>/dev/null; then
    echo "📦 Installing build tools..."
    pip3 install --upgrade build twine
fi

# Step 4: Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ src/*.egg-info

# Step 5: Build the package
echo "🏗️  Building wheel and source distribution..."
python3 -m build

# Step 6: Verify package contents
echo ""
echo "🔍 Verifying package contents..."
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)

if [ -f "$WHEEL_FILE" ]; then
    echo "Checking wheel: $WHEEL_FILE"
    echo ""
    
    # Check for roles
    ROLES_COUNT=$(unzip -l "$WHEEL_FILE" | grep -c "adc/roles/.*\.md" || echo "0")
    echo "  Roles: $ROLES_COUNT files"
    
    # Check for schema
    SCHEMA_COUNT=$(unzip -l "$WHEEL_FILE" | grep -c "adc/schema/.*\.qmd" || echo "0")
    echo "  Schema: $SCHEMA_COUNT files"
    
    # Check for claude files
    CLAUDE_COUNT=$(unzip -l "$WHEEL_FILE" | grep -c "adc/claude/" || echo "0")
    echo "  Claude files: $CLAUDE_COUNT files"
    
    echo ""
    
    # Validation
    if [ "$ROLES_COUNT" -lt 5 ]; then
        echo "  ⚠️  WARNING: Expected at least 5 role files, found $ROLES_COUNT"
    fi
    
    if [ "$SCHEMA_COUNT" -lt 1 ]; then
        echo "  ⚠️  WARNING: Expected schema file, found $SCHEMA_COUNT"
    fi
    
    if [ "$CLAUDE_COUNT" -lt 8 ]; then
        echo "  ⚠️  WARNING: Expected at least 8 Claude files (1 command + 7 agents), found $CLAUDE_COUNT"
    fi
    
    if [ "$ROLES_COUNT" -ge 5 ] && [ "$SCHEMA_COUNT" -ge 1 ] && [ "$CLAUDE_COUNT" -ge 8 ]; then
        echo "  ✅ Package verification PASSED"
    else
        echo "  ❌ Package verification FAILED - some files missing!"
        echo ""
        echo "  Run this to see what's in the wheel:"
        echo "  unzip -l $WHEEL_FILE | grep adc/"
        exit 1
    fi
else
    echo "  ❌ ERROR: Wheel file not found!"
    exit 1
fi

echo ""
echo "✅ Build complete and verified!"
echo ""
echo "📦 Generated files:"
ls -lh dist/
echo ""

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)

echo "🎯 Next steps:"
echo ""
echo "1. Test locally in Docker (RECOMMENDED):"
echo "   docker run -it --rm -v \$(pwd)/dist:/dist python:3.11-slim bash"
echo "   # Inside container:"
echo "   pip install pipx && pipx ensurepath"
echo "   export PATH=\"/root/.local/bin:\$PATH\""
echo "   pipx install /dist/agentic_design_contracts-${VERSION}-py3-none-any.whl[all]"
echo "   adc-setup && adc health"
echo ""
echo "2. Test on Test PyPI (RECOMMENDED before real PyPI):"
echo "   python3 -m twine upload --repository testpypi dist/*"
echo "   # Then test install:"
echo "   pipx install --index-url https://test.pypi.org/simple/ agentic-design-contracts[all]"
echo ""
echo "3. Publish to PyPI (only after testing):"
echo "   python3 -m twine upload dist/*"
echo ""
echo "4. Share wheel file directly:"
echo "   cp dist/agentic_design_contracts-${VERSION}-py3-none-any.whl ~/Desktop/"
echo ""
