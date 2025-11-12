#!/usr/bin/env python3
"""Simulate Claude Code agent loading to detect duplicates."""
import yaml
from pathlib import Path
from collections import defaultdict

agents_dir = Path.home() / '.claude' / 'agents'
agent_files = list(agents_dir.glob('*.md'))

print(f'🔍 Found {len(agent_files)} agent files\n')

agent_names = defaultdict(list)

for agent_file in agent_files:
    with open(agent_file) as f:
        content = f.read()
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                if frontmatter and 'name' in frontmatter:
                    name = frontmatter['name']
                    agent_names[name].append(agent_file.name)
                    print(f'  ✓ {agent_file.name:<40} → name: {name}')
            except Exception as e:
                print(f'  ⚠️  {agent_file.name} → Error: {e}')

print()

# Check for duplicates
duplicates = {name: files for name, files in agent_names.items() if len(files) > 1}

if duplicates:
    print('❌ DUPLICATE AGENT NAMES DETECTED!\n')
    print('Claude Code would show:\n')
    print('  Duplicate Agent Names Found:\n')
    for i, (name, files) in enumerate(duplicates.items(), 1):
        print(f'  {i}. {name} appears in:')
        for file in files:
            print(f'    - ~/.claude/agents/{file}')
    print()
    exit(1)
else:
    print('✅ NO DUPLICATE AGENT NAMES!\n')
    print('All agent names are unique:')
    for name in sorted(agent_names.keys()):
        print(f'  ✓ {name}')
    print()
    print('Claude Code will load these agents without errors! 🎉')
