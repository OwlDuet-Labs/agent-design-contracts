# ADC GitHub Distribution Guide

## 🎯 Overview

This guide covers distributing ADC through GitHub releases (no PyPI needed).

**Distribution Method:** GitHub Releases with wheel files

**Benefits:**
- ✅ No PyPI account needed
- ✅ Version control through Git tags
- ✅ Easy rollback to previous versions
- ✅ Private or public distribution
- ✅ Direct download links

---

## 📦 Building for GitHub Release

### Step 1: Prepare Package Data

```bash
# Copy data files to package (one time setup)
mkdir -p src/adc/{roles,schema,claude/commands,claude/agents}
cp -r roles/*.md src/adc/roles/
cp adc-schema.qmd src/adc/schema/
cp .claude/commands/adc.md src/adc/claude/commands/
cp .claude/agents/adc-*.md src/adc/claude/agents/
```

### Step 2: Build Package

```bash
# Use the improved build script
./build-package-improved.sh
```

This will:
- ✅ Prepare all data files
- ✅ Build wheel and source distribution
- ✅ Verify package contents
- ✅ Show installation commands

---

## 🚀 Creating a GitHub Release

### Method 1: Using GitHub CLI (Recommended)

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # Change version to 0.9.0

# 2. Commit changes
git add .
git commit -m "Release v0.9.0"
git push

# 3. Create tag
git tag v0.9.0
git push origin v0.9.0

# 4. Create release with wheel file
gh release create v0.9.0 \
  dist/agentic_design_contracts-0.9.0-py3-none-any.whl \
  --title "ADC v0.9.0" \
  --notes "See CHANGELOG.md for details"
```

### Method 2: Using GitHub Web Interface

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Choose a tag: `v0.9.0` (create new tag)
4. Release title: `ADC v0.9.0`
5. Drag and drop: `dist/agentic_design_contracts-0.9.0-py3-none-any.whl`
6. Add release notes from CHANGELOG.md
7. Click "Publish release"

---

## 📥 User Installation

### From GitHub Release (Recommended)

```bash
# 1. Download wheel from GitHub
wget https://github.com/OwlDuet-Labs/agent-design-contracts/releases/download/v0.9.0/agentic_design_contracts-0.9.0-py3-none-any.whl

# 2. Install with pipx
pipx install agentic_design_contracts-0.9.0-py3-none-any.whl[all]

# 3. Run setup
adc-setup

# 4. Test
adc health
```

### From Git Repository (Development)

```bash
# Install directly from GitHub
pipx install "git+https://github.com/OwlDuet-Labs/agent-design-contracts.git[all]"

# Run setup
adc-setup
```

### With Symlinks (Development Mode)

```bash
# Clone repository
git clone https://github.com/OwlDuet-Labs/agent-design-contracts.git
cd agent-design-contracts

# Install in editable mode
pipx install -e ".[all]"

# Setup with symlinks (changes to package reflect immediately)
adc-setup --symlink
```

---

## 🔄 Update Workflow

### For Package Maintainers

```bash
# 1. Make changes to code/agents/roles
vim src/adc_cli/...
vim .claude/agents/...

# 2. Update version
vim pyproject.toml  # Bump version

# 3. Update changelog
vim CHANGELOG.md

# 4. Prepare and build
./build-package-improved.sh

# 5. Test in Docker
./test-in-docker.sh

# 6. Commit and tag
git add .
git commit -m "Release v0.10.0"
git tag v0.10.0
git push origin main v0.10.0

# 7. Create GitHub release
gh release create v0.10.0 dist/*.whl \
  --title "ADC v0.10.0" \
  --notes-file CHANGELOG.md
```

### For Users

```bash
# Download new version
wget https://github.com/OwlDuet-Labs/agent-design-contracts/releases/download/v0.10.0/agentic_design_contracts-0.10.0-py3-none-any.whl

# Upgrade
pipx upgrade agentic-design-contracts --pip-args="agentic_design_contracts-0.10.0-py3-none-any.whl[all]"

# Or reinstall
pipx uninstall agentic-design-contracts
pipx install agentic_design_contracts-0.10.0-py3-none-any.whl[all]

# Re-run setup
adc-setup
```

---

## 🧪 Testing Before Release

### Test 1: Docker Test (Isolated)

```bash
# Build package
./build-package-improved.sh

# Test in Docker
./test-in-docker.sh
```

### Test 2: Local Test (Your Machine)

```bash
# Backup your current setup
cp -r ~/.claude ~/.claude.backup

# Install from wheel
pipx install --force dist/*.whl[all]

# Test setup
adc-setup
adc health

# Restore if needed
rm -rf ~/.claude
mv ~/.claude.backup ~/.claude
```

### Test 3: Git Install Test

```bash
# Test direct git installation
pipx install --force "git+file://$(pwd)[all]"
adc-setup
adc health
```

---

## 📋 Release Checklist

### Before Building

- [ ] Version updated in `pyproject.toml`
- [ ] `CHANGELOG.md` updated with changes
- [ ] All data files in `src/adc/`
- [ ] All agents updated in `.claude/agents/`
- [ ] All roles updated in `roles/`
- [ ] Tests passing

### Building

- [ ] Run `./build-package-improved.sh`
- [ ] Verify package contents (script does this)
- [ ] Wheel file created successfully

### Testing

- [ ] Docker test passes (`./test-in-docker.sh`)
- [ ] CLI commands work
- [ ] `adc-setup` works
- [ ] Agents installed correctly
- [ ] Symlink mode works

### Releasing

- [ ] Code committed to git
- [ ] Git tag created (`v0.9.0`)
- [ ] Tag pushed to GitHub
- [ ] GitHub release created
- [ ] Wheel file attached to release
- [ ] Release notes added

### Post-Release

- [ ] Test installation from GitHub release
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)

---

## 🔗 Installation URLs

### Latest Release

```bash
# Get latest release URL
LATEST_URL=$(gh release view --json assets --jq '.assets[0].url')

# Install latest
pipx install "$LATEST_URL[all]"
```

### Specific Version

```bash
# v0.9.0
pipx install https://github.com/OwlDuet-Labs/agent-design-contracts/releases/download/v0.9.0/agentic_design_contracts-0.9.0-py3-none-any.whl[all]
```

### Development Version

```bash
# From main branch
pipx install "git+https://github.com/OwlDuet-Labs/agent-design-contracts.git[all]"

# From specific branch
pipx install "git+https://github.com/OwlDuet-Labs/agent-design-contracts.git@feature-branch[all]"
```

---

## 💡 Symlink Mode Benefits

### For Development

```bash
# Install in editable mode
pipx install -e ".[all]"

# Setup with symlinks
adc-setup --symlink
```

**Benefits:**
- ✅ Edit agents in package → Changes reflect immediately in Claude Code
- ✅ No need to re-run `adc-setup` after changes
- ✅ Perfect for testing agent modifications
- ✅ Easy to track changes in git

**Use Case:**
```bash
# Edit an agent
vim src/adc/claude/agents/adc-code-generator.md

# Changes are immediately available in Claude Code!
# No need to run adc-setup again
```

---

## 🎯 Quick Commands

### Build and Test

```bash
# Full workflow
./build-package-improved.sh && ./test-in-docker.sh
```

### Create Release

```bash
# Quick release
VERSION="0.9.0"
git tag "v$VERSION"
git push origin "v$VERSION"
gh release create "v$VERSION" dist/*.whl --generate-notes
```

### Install from GitHub

```bash
# One-liner install
wget -q https://github.com/OwlDuet-Labs/agent-design-contracts/releases/latest/download/agentic_design_contracts-0.9.0-py3-none-any.whl && \
pipx install agentic_design_contracts-0.9.0-py3-none-any.whl[all] && \
adc-setup
```

---

## 🆘 Troubleshooting

### "Wheel file not found"

```bash
# Make sure you built the package
./build-package-improved.sh

# Check dist/ directory
ls -la dist/
```

### "Package data missing"

```bash
# Verify data files are in src/adc/
ls -R src/adc/

# If missing, copy them:
cp -r roles/*.md src/adc/roles/
cp adc-schema.qmd src/adc/schema/
cp .claude/commands/adc.md src/adc/claude/commands/
cp .claude/agents/adc-*.md src/adc/claude/agents/
```

### "Symlinks not working"

```bash
# Check if files are actually symlinks
ls -la ~/.claude/agents/

# If not, re-run with --symlink
adc-setup --symlink
```

---

## ✅ Summary

**Distribution Method:** GitHub Releases

**Build Command:** `./build-package-improved.sh`

**Test Command:** `./test-in-docker.sh`

**Release Command:** `gh release create v0.9.0 dist/*.whl`

**Install Command:** `pipx install <wheel-url>[all]`

**Setup Command:** `adc-setup` or `adc-setup --symlink`

**No PyPI needed!** 🎉
