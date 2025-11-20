# Changelog

All notable changes to the Agentic Design Contracts (ADC) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.9.2] - 2025-11-12

### 🔧 Schema Installation, Update Command & File Organization

This release fixes a critical issue where ADC agents couldn't access the schema file after installation, adds a convenient update command, and establishes standardized file organization guidelines.

### Added

#### 📚 Schema Installation
- **Schema file installation** - `adc-schema.qmd` now installed to `~/.claude/schema/`
- **Symlink support** - Schema supports both copy and symlink modes
- **Agent accessibility** - All agents can now reference `~/.claude/schema/adc-schema.qmd`

#### 📁 File Organization Guidelines
- **Standardized directory structure** - Added comprehensive file organization section to ADC schema
- **Workspace constraints** - Enforced rules to keep all files within project workspace
- **Directory definitions** - Clear separation between contracts, workflow artifacts, and temporary files
- **Git ignore patterns** - Defined which directories should be committed vs ignored
- **File naming conventions** - Standardized naming patterns for all ADC artifacts

#### 🔄 Update Command
- **`adc-update` command** - Convenient command to refresh all Claude Code files
- **Post-upgrade workflow** - Easy updates after package upgrades
- **Alias for setup** - `adc-update` internally calls `adc-setup`

#### 🚀 Init Command
- **`adc init` command** - Initialize ADC project structure automatically
- **Directory scaffolding** - Creates standardized directory structure
- **Template .gitignore** - Installs .gitignore with ADC patterns
- **README generation** - Creates helpful README in contracts directory
- **Force mode** - `--force` flag to overwrite existing directories

### Changed

#### 🔗 Agent References
- **Updated all agent files** - Changed schema paths from relative to absolute
  - `adc-contract-writer.md` - Now references `~/.claude/schema/adc-schema.qmd`
  - `adc-contract-refiner.md` - Now references `~/.claude/schema/adc-schema.qmd`
  - `adc-code-generator.md` - Now references `~/.claude/schema/adc-schema.qmd`
  - `adc-code-generator-v2.md` - Now references `~/.claude/schema/adc-schema.qmd`
  - `adc-compliance-auditor.md` - Now references `~/.claude/schema/adc-schema.qmd`
  - `adc-workflow-orchestrator.md` - Now references `~/.claude/schema/adc-schema.qmd`
- **Updated command file** - `.claude/commands/adc.md` now references correct schema path

#### 📖 Documentation
- **INSTALL.md** - Added schema installation to setup description
- **INSTALL.md** - Documented `adc-update` command usage
- **INSTALL.md** - Updated uninstall instructions to include schema file

### Fixed
- **Schema accessibility** - Agents can now properly access the ADC schema after installation
- **Broken references** - Fixed relative path references that didn't work after installation
- **Role file references** - Updated agents to use `adc get-role` command instead of file paths
- **Package cleanup** - Removed deprecated agent files (v2, old versions)

## [0.9.1] - 2025-11-01

### 🎉 Major Release - Production-Ready Distribution

This release focuses on making ADC easily distributable and deployable across different environments, with comprehensive packaging, testing, and deployment infrastructure. **Critical bug fix:** Resolved duplicate agent names that caused "Duplicate tools registered" errors in Claude Code.

### Added

#### 📦 Package Distribution
- **Wheel-based distribution** - Complete Python wheel packaging with all data files
- **GitHub Releases support** - Distribution via GitHub releases (no PyPI required)
- **Automated build script** (`build-package-improved.sh`) with verification
- **Docker testing** (`test-simple.sh`) for isolated package validation
- **EC2 deployment** (`deploy-to-ec2.sh`) for cloud deployment

#### 🔧 Setup & Installation
- **`adc-setup` command** - Automated Claude Code integration setup
- **Symlink support** (`adc-setup --symlink`) for development mode
- **PATH configuration** - Automatic pipx path setup
- **Multi-environment support** - Ubuntu, Amazon Linux, macOS compatibility

#### 📚 Documentation
- **EC2-DEPLOYMENT.md** - Comprehensive EC2 deployment guide (6 methods)
- **EC2-QUICK-START.md** - Quick reference for EC2 deployment
- **EC2-POST-INSTALL.md** - Post-installation configuration guide
- **GITHUB-DISTRIBUTION.md** - GitHub releases workflow
- **TEST-RESULTS.md** - Package testing documentation
- **PRODUCTION-REVIEW.md** - Production readiness checklist

#### 🤖 Claude Code Integration
- **10 specialized agents** installed via `adc-setup`:
  - `adc-code-generator` - Transform contracts to code
  - `adc-code-generator-v2` - Enhanced code generation
  - `adc-compliance-auditor` - Contract compliance checking
  - `adc-contract-writer` - Contract creation assistant
  - `adc-contract-refiner` - Contract improvement
  - `adc-app-simulator` - Application simulation
  - `adc-system-evaluator` - System evaluation
  - `adc-pr-orchestrator` - PR and release management
  - `adc-workflow-orchestrator` - Workflow coordination
  - `adc-workflow-orchestrator-old` - Legacy workflow support
- **`/adc` command** - Quick contract operations in Claude Code
- **Automatic installation** to `~/.claude/` directory

#### 🔐 Security & Configuration
- **AWS Secrets Manager integration** examples
- **AWS Systems Manager Parameter Store** examples
- **IAM role configurations** for EC2
- **Environment variable management** best practices
- **Security group configurations**

### Changed

#### 🏗️ Package Structure
- **Data files relocated** to `src/adc/` for proper packaging
- **Fixed import issues** in `adc/__init__.py`
- **Renamed `commands/` to `command_modules/`** to avoid module shadowing
- **Added `__init__.py`** to command_modules package
- **Improved package metadata** in `pyproject.toml`

#### 🧪 Testing Infrastructure
- **Automated Docker tests** - Full installation verification in isolated environment
- **Claude Code integration tests** - Real-world testing with authenticated Claude Code
- **Agent name uniqueness validation** - Prevents duplicate tool registration errors
- **Package content verification** - Ensures all data files included
- **Health check validation** - Verifies CLI functionality
- **Multi-step test suite** - Installation, setup, and runtime tests
- **17/17 tests passed** - 100% success rate in production environment

#### 📝 Build Process
- **Automated data file preparation** - Copies roles, schema, agents to package
- **Build verification** - Checks wheel contents before distribution
- **Clear error messages** - Helpful feedback on build failures
- **Version consistency** - Automatic version detection from pyproject.toml

### Fixed

- **Duplicate agent names** - Fixed Claude Code "duplicate tools registered" error
  - `adc-code-generator-v2.md` now has unique name `adc-code-generator-v2`
  - `adc-workflow-orchestrator-old.md` now has unique name `adc-workflow-orchestrator-old`
- **Module import errors** - Fixed circular imports and missing modules
- **PATH issues** - Added pipx ensurepath to installation
- **Package data access** - Proper use of importlib.resources
- **Symlink creation** - Robust symlink handling with fallback to copy
- **File permissions** - Proper executable permissions on scripts

### Deployment

#### 🚀 Distribution Methods
1. **Direct SCP Upload** - Simple wheel file transfer to servers
2. **S3 + EC2** - Centralized wheel storage with automated installation
3. **User Data Scripts** - Auto-install on EC2 launch
4. **Private PyPI Server** - Self-hosted package repository
5. **Docker Containers** - Containerized ADC deployment
6. **GitHub Releases** - Public/private distribution via GitHub

#### 🎯 Deployment Features
- **One-command deployment** - `./deploy-to-ec2.sh`
- **Automated installation** - No manual steps required
- **Health verification** - Post-install validation
- **Rollback support** - Easy version switching
- **Multi-server deployment** - Team-wide distribution

### Testing

#### ✅ Verified Components
- Package builds successfully with all data files
- CLI commands work (`adc`, `adc-setup`)
- Claude Code files install correctly (1 command + 10 agents)
- Health check runs successfully
- Symlink mode works for development
- EC2 deployment completes successfully
- Docker tests pass in isolated environment

#### 📊 Test Coverage
- Build process verification
- Installation validation
- CLI functionality
- Setup script execution
- File installation
- Health check operation
- Multi-environment compatibility

### Documentation

#### 📖 New Guides
- **Complete EC2 deployment** with 6 different methods
- **GitHub releases workflow** for distribution
- **Post-installation configuration** steps
- **Troubleshooting guides** for common issues
- **Security best practices** for production
- **Quick reference cards** for common tasks

#### 🎓 Examples
- One-liner installations
- Automated deployment scripts
- Docker test commands
- S3 integration examples
- IAM policy templates
- CloudWatch integration

### Infrastructure

#### 🔧 Scripts
- `build-package-improved.sh` - Enhanced build with verification
- `deploy-to-ec2.sh` - Automated EC2 deployment
- `test-simple.sh` - Docker-based testing
- `test-in-docker.sh` - Comprehensive test suite

#### 📦 Package Contents
- 7 role definition files
- 1 schema file (adc-schema.qmd)
- 1 Claude Code command
- 10 Claude Code agents
- All CLI tools and dependencies

### Performance

- **Fast installation** - Optimized package size
- **Minimal dependencies** - Only required packages
- **Efficient setup** - Quick Claude Code integration
- **Cached builds** - Faster subsequent builds

### Developer Experience

#### 🛠️ Development Mode
- **Symlink support** - Edit agents, see changes immediately
- **No reinstall needed** - Changes reflect in Claude Code instantly
- **Git-friendly** - Easy to track agent modifications
- **Fast iteration** - Quick testing of agent changes

#### 📝 Improved Workflows
- Clear build output with verification
- Helpful error messages
- Step-by-step deployment guides
- Automated testing before release
- Version management through Git tags

### Migration Notes

#### From Previous Versions
1. Rebuild package: `./build-package-improved.sh`
2. Test in Docker: `./test-simple.sh`
3. Deploy: `./deploy-to-ec2.sh` or distribute wheel
4. Run `adc-setup` on target systems
5. Configure API keys

#### Breaking Changes
- None - Fully backward compatible with 0.8.x

### Known Issues
- Health check may show warnings without contracts directory (expected)
- Symlink mode requires package installed in editable mode
- Windows symlink support requires administrator privileges

### Upcoming in 1.0.0
- [ ] PyPI distribution (optional)
- [ ] Windows installer
- [ ] Homebrew formula
- [ ] Auto-update mechanism
- [ ] Enhanced monitoring
- [ ] Performance metrics

---

## [0.8.0] - 2025-08-27 (Previous Release)

### Added
- Initial private release
- Core ADC CLI tool implementation
- Support for multiple AI providers (Anthropic, OpenAI, Google Gemini)
- Contract generation, auditing, and refinement commands
- Configuration management system
- VS Code integration support
- Contract linting functionality
- Comprehensive role definitions for AI agents

### Features
- **Code Generation**: Transform ADC contracts into production code
- **Contract Auditing**: Verify code compliance with design contracts
- **Contract Refinement**: Improve contract quality and completeness
- **Multi-provider Support**: Flexible AI provider selection
- **Custom Prompts**: Override default agent behaviors
- **Configuration Management**: Persistent settings and preferences

### Components
- `adc config` - Manage configuration settings
- `adc setup-vscode` - Configure VS Code integration
- `adc {generate|audit|refine}` - cli commands for git integration

## [0.8.0] - 2025-07-25

### Added
- Initial ADC schema definition (v1.0)
- Core contract block types
- Agent role specifications
- Basic CLI structure

### Changed
- Migrated from prototype to structured package
- Established contract ID conventions

## [0.7.0] - 2025-06-15

### Added
- Prototype implementation
- Basic contract parsing
- Initial AI provider integrations

### Experimental
- Testing ADC methodology with real projects
- Gathering feedback on contract structure

## Notes

### Version History
- **0.9.x** - Private beta release
- **0.8.x** - Alpha development
- **0.7.x** - Prototype phase

### Upcoming Features (1.0.0)
- [ ] Contract versioning and migration tools
- [ ] Enhanced VS Code extension
- [ ] CI/CD pipeline integration
- [ ] Additional AI provider support
- [ ] Contract validation improvements
- [ ] Performance optimizations

### Support
For issues or questions, please visit:
- [GitHub Issues](https://github.com/OwlDuet-Labs/agent-design-contracts/issues)
- [Documentation](https://github.com/OwlDuet-Labs/agent-design-contracts/docs)

---

[0.9.1]: https://github.com/OwlDuet-Labs/agent-design-contracts/releases/tag/v0.9.1
