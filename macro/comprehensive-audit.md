# Comprehensive ADC Audit Macro

## Purpose
This macro automates the comprehensive audit of all projects containing Agent Design Contracts (ADC), evaluating implementation completeness, mock detection, design drift, and architectural quality. It generates individual audit reports per project and a summary report highlighting gaps and improvement opportunities.

## Configuration
The macro reads configuration from `~/.adcconfig.yaml` to determine output directories and audit settings. Default configuration:

```yaml
root_dir: /Users/owl/repos/org-level-reports
summary
  reports_subdir: summaries
audit:
  reports_subdir: audits
```

## Command Implementation

```bash
# As @auditor.md, search through all directories and find projects that contain a contracts dir. 
# Audit each contract against the sources and update the status field. 
# For each project create an <project>-audit.md file in the configured summary/audits directory.
# Some projects have the same name bc they're the same repo, so then use <project>-<parentdir> as the project name.
```

## Macro Steps

### 1. Configuration Loading Phase
```python
# ADC-IMPLEMENTS: comprehensive-audit-config
import yaml
import os
from pathlib import Path

def load_audit_config():
    """Load audit configuration from ~/.adcconfig.yaml"""
    config_path = Path.home() / '.adcconfig.yaml'
    
    if not config_path.exists():
        # Create default config if missing
        default_config = {
            'root_dir': str('./adc-reports'),
            'summary': {
                'reports_subdir': 'summaries',
                'date_format': '%Y-%m-%d',
            }
            'audit': {
                'reports_subdir': 'audits',
                'date_format': '%Y-%m-%d',
                'auto_update_status': False
            }
        }
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        return default_config
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```

### 2. Discovery Phase
```python
# ADC-IMPLEMENTS: comprehensive-audit-discovery
def discover_contract_projects(config):
    """Find all projects containing contracts directories"""
    projects = []
    exclude_patterns = config.get('discovery', {}).get('exclude_patterns', ['*/.*'])
    
    # Search pattern: **/contracts/
    # Expected locations based on research.md mapping:
    # - Application & Services: app/, agent-design-contracts/
    # - Sound Engine: soundengine/, reverb/
    # - LLM Development: llm/
    # - Sound Engine Expansion: (future projects)
    
    # Apply exclusion patterns from config
    return projects

def update_project_list(projects, config):
    """Create/update project-list.csv with discovered projects"""
    # ADC-IMPLEMENTS: comprehensive-audit-project-list
    import csv
    from pathlib import Path

    project_list_path = Path(config['root_dir'])
    
    # Create CSV with headers if it doesn't exist
    if not project_list_path.exists():
        with open(project_list_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['project_name', 'github_uri', 'path'])
    
    # Read existing entries to avoid duplicates
    existing_projects = set()
    if project_list_path.exists():
        with open(project_list_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_projects.add(row['path'])
    
    # Add new projects
    new_entries = []
    for project in projects:
        if project['path'] not in existing_projects:
            # Generate GitHub URI based on path
            github_uri = generate_github_uri(project['path'])
            new_entries.append({
                'project_name': project['name'],
                'github_uri': github_uri,
                'path': project['path']
            })
    
    # Append new entries
    if new_entries:
        with open(project_list_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['project_name', 'github_uri', 'path'])
            writer.writerows(new_entries)
    
    return project_list_path

def generate_github_uri(project_path):
    """Generate GitHub URI from project path"""
    # Default to placeholder - user should update with actual URIs
    return f"https://github.com/user/repo#{project_path.replace('/', '-')}"
```

### 3. Audit Execution Phase
```python
# ADC-IMPLEMENTS: comprehensive-audit-execution
def audit_project(project_path, contracts_dir, config):
    """Execute comprehensive audit for a single project"""
    # Read auditor.md requirements
    # For each contract in contracts/:
    #   1. Check ADC-IMPLEMENTS markers
    #   2. Detect mocked implementations using config severity levels
    #   3. Analyze design drift
    #   4. Identify technical roadblocks
    #   5. Generate meta-policy recommendations
    return audit_report
```

### 4. Report Generation Phase
```python
# ADC-IMPLEMENTS: comprehensive-audit-reporting
def generate_audit_reports(audit_results, config):
    """Create individual and summary audit reports"""
    # Get configured paths
    root_dir = Path(config['root_dir'])
    summary_dir = root_dir / Path(config['summary']['reports_subdir'])
    audit_dir = root_dir / Path(config['audit']['reports_subdir'])
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate reports using configured templates
    date_format = config['audit']['date_format']
    today = datetime.now().strftime(date_format)
    
    # Individual reports: <root_dir>/audits/<project>-audit.md
    # Summary report: <root_dir>/summaries/AUDIT-SUMMARY-<date>.md
    
    if config['audit']['auto_update_status']:
        # Update contract status fields where applicable
        pass
```

## Missing Projects & Major Gaps

Based on the research.md mapping and audit results, here are the critical gaps:

### 🚨 Missing Projects (Per research.md)

1. **Musical LLM Development** (LLM Development category)
   - Status: Planned but no contracts found
   - Impact: Gap in music-specific language understanding
   - Recommendation: Create contracts for musical terminology, theory, and generation

2. **Backend Services** (Application & Services category)
   - Status: Partially addressed in app project
   - Impact: Missing server-side infrastructure contracts
   - Recommendation: Define contracts for API gateway, auth, and data services

3. **Calibration Systems** (Sound Engine Expansion category)
   - Status: Future project, no contracts
   - Impact: No room correction or system calibration
   - Recommendation: Create contracts for measurement, analysis, and correction

4. **Psychoacoustic Perception Models** (Sound Engine Expansion category)
   - Status: Research phase, no contracts
   - Impact: Missing perceptual optimization capabilities
   - Recommendation: Define contracts for loudness, masking, and spatial perception

### 📊 Major Gaps in Existing Projects

1. **agent-design-contracts** (37.5% compliance)
   - Critical: Workflow orchestration completely unimplemented
   - Impact: Can't achieve "revolutionary development acceleration"
   - Fix: Prioritize workflow system or defer contract

2. **reverb** (65% compliance, 27% mocked)
   - Critical: SpectralCodec and MaterialLearner mocked
   - Impact: Core 4D reverb value proposition unavailable
   - Fix: Implement neural vocoder and ML training

3. **app** (17% mocked)
   - Critical: Agent Service returns hardcoded responses
   - Impact: No actual AI assistance for users
   - Fix: Integrate OpenAI WebRTC API

## Structural Refactoring Recommendations

### 1. Reduce Repository Redundancy
```
Current State:
- soundengine/midside-plus/owlduet-plugins/
- soundengine/zmq/owlduet-plugins/
(Same project in two locations)

Proposed Structure:
soundengine/
  owlduet-plugins/
    variants/
      midside-plus/
      zmq/
    contracts/  # Unified contracts
    core/       # Shared code
```

### 2. Centralize Contract Management
```
Proposed Structure:
contracts-registry/
  adc-schema.qmd          # Central schema definition
  categories/
    application/          # App & Services contracts
    sound-engine/         # Audio processing contracts
    llm-development/      # ML/AI contracts
    expansion/            # Future capabilities
  mapping/
    projects.yaml         # Project-to-contract mapping
    dependencies.yaml     # Inter-contract dependencies
```

### 3. Extract Common Functionality
```
Key Functionality to Extract:

1. Mock Detection Framework
   - Standardized mock severity levels
   - Automated detection tools
   - Elimination tracking

2. Contract Validation Engine
   - ADC-IMPLEMENTS parser
   - Semantic compliance checker
   - Design drift analyzer

3. Audio Quality Assurance
   - Perceptual metrics library
   - A/B testing framework
   - Regression test suite

4. Security & Credentials
   - Unified credential management
   - API key rotation service
   - Audit logging
```

### 4. Implement Contract Inheritance
```yaml
# Base contracts for common patterns
base-contracts/
  audio-processor-base.qmd    # Common to all audio plugins
  ml-training-base.qmd        # Common to all ML components
  cli-application-base.qmd    # Common to all CLI tools
  transport-base.qmd          # Common to all IPC/network
```

### 5. Create Meta-ADC Tools
```
adc-tools/
  adc-lint              # Validate contract format
  adc-check             # Check implementation compliance
  adc-gen               # Generate code from contracts
  adc-mock-detect       # Find and tag mocked code
  adc-report            # Generate audit reports
```

## Integration with Research.md Categories

### Align Audits with Product Capabilities
1. **Tag contracts** with research.md categories
2. **Track coverage** per category (not just per project)
3. **Identify gaps** at category level
4. **Prioritize** based on strategic priorities

### Example Category-Based Audit
```yaml
Application & Services:
  Projects: [app, agent-design-contracts]
  Contract Coverage: 60%
  Critical Gaps: 
    - Backend services undefined
    - Agent Service mocked
  Next Actions:
    - Define backend architecture contracts
    - Implement real AI integration

Sound Engine:
  Projects: [owlduet-plugins, reverb]
  Contract Coverage: 82.5%
  Critical Gaps:
    - 4D reverb components mocked
    - Missing calibration systems
  Next Actions:
    - Implement neural vocoders
    - Create calibration contracts
```

## Execution Workflow

1. **Load Configuration**
   ```bash
   # Read config from ~/.adcconfig.yaml
   CONFIG=$(yq eval '.' ~/.adcconfig.yaml)
   SUMMARY_DIR=$(yq eval '.root_dir' ~/.adcconfig.yaml)
   AUDIT_DIR="${SUMMARY_DIR}/$(yq eval '.audit.reports_subdir' ~/.adcconfig.yaml)"
   ```

2. **Run Discovery**
   ```bash
   find . -type d -name "contracts" -not -path "*/\.*" | sort
   ```

3. **Update Project List**
   ```bash
   # Update or-research-contracts/project-list.csv
   python -c "
   projects = discover_contract_projects(config)
   project_list_path = update_project_list(projects, config)
   print(f'Updated project list: {project_list_path}')
   "
   ```

4. **Execute Audits**
   ```bash
   # Ensure audit directory exists
   mkdir -p "$AUDIT_DIR"
   
   for project in $projects; do
     adc audit --project $project --output "$AUDIT_DIR"
   done
   ```

4. **Generate Summary**
   ```bash
   adc summarize --input "$AUDIT_DIR" --categories "$SUMMARY_DIR/../mapping/research.md"
   ```

5. **Update Status** (if auto_update_status is true)
   ```bash
   if [ "$(yq eval '.audit.auto_update_status' ~/.adcconfig.yaml)" = "true" ]; then
     adc update-status --audit-results "$AUDIT_DIR"
   fi
   ```

## Example Usage

```bash
# Run comprehensive audit with default config
adc macro comprehensive-audit

# Run with custom config file
ADC_CONFIG=/path/to/custom/config.yaml adc macro comprehensive-audit

# Run and force status updates
adc macro comprehensive-audit --update-status

# Output will be in: ./adc-reports
```

## Benefits of This Approach

1. **Systematic Coverage** - No project missed
2. **Consistent Standards** - Same audit criteria everywhere  
3. **Gap Visibility** - Clear view of missing capabilities
4. **Actionable Output** - Specific recommendations per project
5. **Strategic Alignment** - Maps to research.md categories
6. **Automation Ready** - Can be fully automated with tools

## Configuration Benefits

The `~/.adcconfig.yaml` configuration provides:

1. **Centralized Output** - All audits go to a single, configurable location
2. **Flexible Organization** - Easy to change output directories without modifying code
3. **Consistent Paths** - All ADC tools use the same configuration
4. **Environment Portability** - Different configs for different environments
5. **Integration Ready** - Other tools can read the same config file

Example configurations for different scenarios:

```yaml
# Development environment
root_dir: ~/dev/adc-audits
audit:
  reports_subdir: dev-audits
  auto_update_status: true

# CI/CD environment  
root_dir: /var/ci/adc-reports
audit:
  reports_subdir: ci-audits
  auto_update_status: false

# Shared team environment
root_dir: /shared/team/adc-reports
audit:
  reports_subdir: team-audits
  auto_update_status: false
```

This macro provides a repeatable, comprehensive audit process that aligns with the organizational structure defined in research.md while identifying critical gaps and improvement opportunities across the entire codebase.
