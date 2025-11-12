# Claude Code Testing Container

This Docker container allows you to test ADC agents with Claude Code in an isolated environment.

## Quick Start

```bash
# 1. Build and start container
cd docker-claude-test
chmod +x start-container.sh
./start-container.sh

# 2. SSH into container
ssh -p 2222 testuser@localhost
# Password: testuser

# 3. Inside container - Install Claude Code
# Follow Claude Code installation instructions for Linux
# Then authenticate with your account

# 4. Test agents
# Open Claude Code and check if agents load without errors
```

## What's Installed

- ✅ ADC v0.9.1 (via pipx)
- ✅ 1 Claude Code command: `/adc`
- ✅ 10 Claude Code agents (all with unique names)
- ✅ SSH server (port 2222)

## Agent Names (All Unique)

```
adc-app-simulator
adc-code-generator
adc-code-generator-v2
adc-compliance-auditor
adc-contract-refiner
adc-contract-writer
adc-pr-orchestrator
adc-system-evaluator
adc-workflow-orchestrator
adc-workflow-orchestrator-old
```

## Testing Checklist

- [ ] SSH into container
- [ ] Install Claude Code
- [ ] Authenticate
- [ ] Check for "Duplicate tools registered" error
- [ ] Verify all 10 agents appear
- [ ] Test using an agent (e.g., @adc-code-generator)

## Useful Commands

```bash
# Check agent names
docker exec -u testuser adc-claude-test grep '^name:' ~/.claude/agents/adc-*.md

# List installed agents
docker exec -u testuser adc-claude-test ls -la ~/.claude/agents/

# Check ADC health
docker exec -u testuser adc-claude-test bash -c 'export PATH="/home/testuser/.local/bin:$PATH" && adc health'

# Stop container
docker stop adc-claude-test
docker rm adc-claude-test

# Restart container
./start-container.sh
```

## Troubleshooting

### Can't connect via SSH
```bash
# Check if container is running
docker ps | grep adc-claude-test

# Check SSH logs
docker logs adc-claude-test
```

### ADC not found
```bash
# Check PATH
docker exec -u testuser adc-claude-test bash -c 'echo $PATH'

# Reinstall
docker exec -u testuser adc-claude-test bash -c '
    export PATH="/home/testuser/.local/bin:$PATH"
    pipx install /dist/*.whl[all]
    adc-setup
'
```

## Clean Up

```bash
# Stop and remove container
docker stop adc-claude-test
docker rm adc-claude-test

# Remove image
docker rmi adc-claude-test
```
