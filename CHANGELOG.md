# Changelog

All notable changes to the Agentic Design Contracts (ADC) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.9.0] - 2025-08-27

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

[0.9.0]: https://github.com/OwlDuet-Labs/agent-design-contracts/releases/tag/v0.9.0
