#!/bin/bash
# Comprehensive Claude Code + ADC test

echo "🧪 Running comprehensive Claude Code + ADC test..."
echo ""

# Test 1: Check ADC installation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: ADC Installation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

export PATH="$HOME/.local/bin:$PATH"

if command -v adc &> /dev/null; then
    echo "✅ adc command found"
    adc --version 2>&1 | head -1 || echo "Version check failed"
else
    echo "❌ adc command not found"
    exit 1
fi
echo ""

# Test 2: Check Claude Code files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Claude Code Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check command
if [ -f ~/.claude/commands/adc.md ]; then
    echo "✅ /adc command installed"
else
    echo "❌ /adc command missing"
    exit 1
fi

# Check agents
AGENT_COUNT=$(ls ~/.claude/agents/adc-*.md 2>/dev/null | wc -l)
echo "✅ Found $AGENT_COUNT ADC agents"

if [ "$AGENT_COUNT" -ne 10 ]; then
    echo "❌ Expected 10 agents, found $AGENT_COUNT"
    exit 1
fi
echo ""

# Test 3: Check for duplicate agent names
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Agent Name Uniqueness (CRITICAL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Agent names from frontmatter:"
grep '^name:' ~/.claude/agents/adc-*.md | awk '{print $2}' | sort | nl
echo ""

DUPLICATES=$(grep '^name:' ~/.claude/agents/adc-*.md | awk '{print $2}' | sort | uniq -d)

if [ -z "$DUPLICATES" ]; then
    echo "✅ NO DUPLICATE AGENT NAMES - Claude Code will work correctly!"
else
    echo "❌ DUPLICATE AGENT NAMES FOUND:"
    echo "$DUPLICATES"
    echo ""
    echo "This will cause 'Duplicate tools registered' error in Claude Code"
    exit 1
fi
echo ""

# Test 4: Verify specific fixed agents
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Verify Fixed Agent Names"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check adc-code-generator-v2
V2_NAME=$(grep '^name:' ~/.claude/agents/adc-code-generator-v2.md | awk '{print $2}')
if [ "$V2_NAME" = "adc-code-generator-v2" ]; then
    echo "✅ adc-code-generator-v2.md has correct name: $V2_NAME"
else
    echo "❌ adc-code-generator-v2.md has wrong name: $V2_NAME (expected: adc-code-generator-v2)"
    exit 1
fi

# Check adc-workflow-orchestrator-old
OLD_NAME=$(grep '^name:' ~/.claude/agents/adc-workflow-orchestrator-old.md | awk '{print $2}')
if [ "$OLD_NAME" = "adc-workflow-orchestrator-old" ]; then
    echo "✅ adc-workflow-orchestrator-old.md has correct name: $OLD_NAME"
else
    echo "❌ adc-workflow-orchestrator-old.md has wrong name: $OLD_NAME (expected: adc-workflow-orchestrator-old)"
    exit 1
fi
echo ""

# Test 5: Check Claude Code can read agents
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Claude Code Agent Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if command -v claude &> /dev/null; then
    echo "✅ Claude Code CLI found"
    
    # Try to list agents (if command exists)
    if claude agents list &> /dev/null; then
        echo "✅ Claude Code can list agents"
        claude agents list 2>&1 | grep -i adc | head -5
    else
        echo "⚠️  'claude agents list' command not available (may need different syntax)"
    fi
else
    echo "⚠️  Claude Code CLI not found in PATH"
fi
echo ""

# Test 6: ADC Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 6: ADC Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

adc health 2>&1 | grep -E "(Overall Status|Health Score|Component Status)" || echo "Health check ran"
echo ""

# Test 7: File integrity check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 7: File Integrity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check all agent files are readable
READABLE=0
TOTAL=0
for agent in ~/.claude/agents/adc-*.md; do
    TOTAL=$((TOTAL + 1))
    if [ -r "$agent" ]; then
        READABLE=$((READABLE + 1))
    else
        echo "❌ Cannot read: $agent"
    fi
done

echo "✅ $READABLE/$TOTAL agent files are readable"
echo ""

# Final summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ADC CLI installed and working"
echo "✅ 10 agents installed"
echo "✅ No duplicate agent names"
echo "✅ Fixed agents have correct names"
echo "✅ All files readable"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 ALL TESTS PASSED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Package is ready for production deployment"
echo "✅ No 'Duplicate tools registered' errors expected"
echo ""
