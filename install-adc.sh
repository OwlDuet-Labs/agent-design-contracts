#!/bin/bash
# ADC Complete Installation Script
# Installs ADC CLI, agents, and commands for system-wide use

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         ADC (Agent Design Contracts) Installer             ║${NC}"
echo -e "${BLUE}║                     Version 0.9.2                          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}[1/6]${NC} Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}✗ Python 3.9+ required, found $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check for pipx
echo -e "${YELLOW}[2/6]${NC} Checking for pipx..."
if ! command -v pipx &> /dev/null; then
    echo -e "${YELLOW}  pipx not found. Installing via homebrew...${NC}"
    if command -v brew &> /dev/null; then
        brew install pipx
        pipx ensurepath
    else
        echo -e "${RED}✗ Homebrew not found. Please install pipx manually:${NC}"
        echo -e "  python3 -m pip install --user pipx"
        echo -e "  python3 -m pipx ensurepath"
        exit 1
    fi
fi
echo -e "${GREEN}✓ pipx is available${NC}"

# Install ADC CLI via pipx
echo -e "${YELLOW}[3/6]${NC} Installing ADC CLI tool..."
if pipx list | grep -q "agentic-design-contracts"; then
    echo -e "${YELLOW}  ADC already installed. Reinstalling...${NC}"
    pipx uninstall agentic-design-contracts 2>/dev/null || true
fi
pipx install -e "$SCRIPT_DIR[all]"
echo -e "${GREEN}✓ ADC CLI installed system-wide${NC}"

# Install Claude Code commands
echo -e "${YELLOW}[4/6]${NC} Installing Claude Code commands..."
mkdir -p ~/.claude/commands
cp "$SCRIPT_DIR/.claude/commands/adc.md" ~/.claude/commands/
# Update the ADC framework path in the command file
sed -i.bak "s|/Users/mathiascaldas/Documents/work/OwlDuet/agent-design-contracts2|$SCRIPT_DIR|g" ~/.claude/commands/adc.md
rm ~/.claude/commands/adc.md.bak 2>/dev/null || true
echo -e "${GREEN}✓ /adc command installed${NC}"

# Install Claude Code agents
echo -e "${YELLOW}[5/6]${NC} Installing Claude Code agents..."
mkdir -p ~/.claude/agents
cp -r "$SCRIPT_DIR/.claude/agents/"* ~/.claude/agents/
echo -e "${GREEN}✓ ADC agents installed (7 agents)${NC}"

# Create helper scripts
echo -e "${YELLOW}[6/6]${NC} Creating helper scripts..."

# Create project setup script
cat > ~/adc-setup-project.sh << 'SETUP_SCRIPT'
#!/bin/bash
# Quick setup script for adding ADC to any project

PROJECT_DIR="${1:-.}"
ADC_SOURCE="__ADC_PATH__"

echo "🔧 Setting up ADC in: $PROJECT_DIR"

# Create symlink
if [ -L "$PROJECT_DIR/adc" ] || [ -e "$PROJECT_DIR/adc" ]; then
    echo "⚠️  adc/ already exists"
    read -p "   Replace it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$PROJECT_DIR/adc"
        ln -s "$ADC_SOURCE" "$PROJECT_DIR/adc"
        echo "✅ Symlink updated"
    fi
else
    ln -s "$ADC_SOURCE" "$PROJECT_DIR/adc"
    echo "✅ Symlink created"
fi

# Create contracts directory
mkdir -p "$PROJECT_DIR/contracts"
echo "✅ Contracts directory ready"

echo ""
echo "🎉 Setup complete!"
echo "   Use: /adc in Claude Code"
echo "   Use: @adc/roles/*.md to reference roles"
echo "   Use: adc <command> in terminal"
SETUP_SCRIPT

# Replace placeholder with actual path
sed "s|__ADC_PATH__|$SCRIPT_DIR|g" ~/adc-setup-project.sh > ~/adc-setup-project.sh.tmp
mv ~/adc-setup-project.sh.tmp ~/adc-setup-project.sh
chmod +x ~/adc-setup-project.sh

echo -e "${GREEN}✓ Helper scripts created${NC}"

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                  Installation Complete! 🎉                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ ADC CLI:${NC} Available system-wide as 'adc' command"
echo -e "${GREEN}✓ Claude Commands:${NC} /adc available in all projects"
echo -e "${GREEN}✓ Claude Agents:${NC} @adc-* agents available everywhere"
echo -e "${GREEN}✓ Helper Script:${NC} ~/adc-setup-project.sh"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Set up API keys in ~/.zshrc:"
echo "     export ANTHROPIC_API_KEY=\"your-key\""
echo "     export OPENAI_API_KEY=\"your-key\""
echo "     export GOOGLE_API_KEY=\"your-key\""
echo ""
echo "  2. Reload your shell:"
echo "     source ~/.zshrc"
echo ""
echo "  3. Test installation:"
echo "     adc health"
echo ""
echo "  4. Use in any project:"
echo "     cd ~/your-project"
echo "     ~/adc-setup-project.sh"
echo "     # Then use /adc in Claude Code"
echo ""
echo -e "${BLUE}Documentation:${NC} $SCRIPT_DIR/README.md"
echo -e "${BLUE}ADC Framework:${NC} $SCRIPT_DIR"
echo ""
