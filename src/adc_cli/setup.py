"""
ADC User Environment Setup
Installs Claude Code commands and agents to user's home directory
Supports both copying and symlinking
"""
import os
import sys
import shutil
from pathlib import Path
from importlib import resources


def setup_user_environment():
    """Set up ADC in user's Claude Code environment."""
    
    print("🔧 Setting up ADC user environment...")
    print()
    
    # Check for --symlink flag
    use_symlinks = '--symlink' in sys.argv or '-s' in sys.argv
    
    if use_symlinks:
        print("🔗 Using symlinks (files will stay in package, linked to ~/.claude/)")
    else:
        print("📋 Copying files to ~/.claude/")
    print()
    
    # Get user's home directory
    home = Path.home()
    claude_dir = home / ".claude"
    
    # Create directories
    commands_dir = claude_dir / "commands"
    agents_dir = claude_dir / "agents"
    schema_dir = claude_dir / "schema"
    
    commands_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)
    schema_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Get package paths
        print("📝 Installing Claude Code commands...")
        if hasattr(resources, 'files'):
            # Python 3.9+
            adc_package = resources.files('adc')
            commands_src = adc_package / 'claude' / 'commands'
            agents_src = adc_package / 'claude' / 'agents'
            
            # Get actual filesystem paths (needed for symlinks)
            # This works because resources.files returns a Path-like object
            commands_src_path = None
            agents_src_path = None
            schema_src_path = None
            
            # Try to get actual path for symlinking
            if use_symlinks:
                try:
                    # For installed packages, we need the actual filesystem path
                    import adc
                    package_path = Path(adc.__file__).parent
                    commands_src_path = package_path / 'claude' / 'commands'
                    agents_src_path = package_path / 'claude' / 'agents'
                    schema_src_path = package_path / 'schema'
                except Exception:
                    print("⚠️  Could not determine package path for symlinks, falling back to copy")
                    use_symlinks = False
            
            # Install command files
            for cmd_file in commands_src.iterdir():
                if cmd_file.suffix == '.md':
                    dest = commands_dir / cmd_file.name
                    
                    # Remove existing file/symlink
                    if dest.exists() or dest.is_symlink():
                        dest.unlink()
                    
                    if use_symlinks and commands_src_path:
                        # Create symlink
                        src = commands_src_path / cmd_file.name
                        dest.symlink_to(src)
                        print(f"   🔗 {cmd_file.name} (symlinked)")
                    else:
                        # Copy file
                        dest.write_text(cmd_file.read_text())
                        print(f"   ✓ {cmd_file.name}")
            
            # Install agent files
            print()
            print("🤖 Installing Claude Code agents...")
            for agent_file in agents_src.iterdir():
                if agent_file.suffix == '.md':
                    dest = agents_dir / agent_file.name
                    
                    # Remove existing file/symlink
                    if dest.exists() or dest.is_symlink():
                        dest.unlink()
                    
                    if use_symlinks and agents_src_path:
                        # Create symlink
                        src = agents_src_path / agent_file.name
                        dest.symlink_to(src)
                        print(f"   🔗 {agent_file.name} (symlinked)")
                    else:
                        # Copy file
                        dest.write_text(agent_file.read_text())
                        print(f"   ✓ {agent_file.name}")
            
            # Install schema files
            print()
            print("📚 Installing ADC schema...")
            schema_src = adc_package / 'schema' / 'adc-schema.qmd'
            schema_dest = schema_dir / 'adc-schema.qmd'
            
            # Remove existing file/symlink
            if schema_dest.exists() or schema_dest.is_symlink():
                schema_dest.unlink()
            
            if use_symlinks and schema_src_path:
                # Create symlink
                src = schema_src_path / 'adc-schema.qmd'
                schema_dest.symlink_to(src)
                print(f"   🔗 adc-schema.qmd (symlinked)")
            else:
                # Copy file
                schema_dest.write_text(schema_src.read_text())
                print(f"   ✓ adc-schema.qmd")
        
        print()
        print("✅ Setup complete!")
        print()
        print("📋 What was installed:")
        print(f"   • Commands: {commands_dir}")
        print(f"   • Agents: {agents_dir}")
        print(f"   • Schema: {schema_dir}")
        if use_symlinks:
            print()
            print("🔗 Files are symlinked - updates to package will reflect immediately")
        print()
        print("🎯 Next steps:")
        print("   1. Set up API keys in ~/.zshrc:")
        print("      export ANTHROPIC_API_KEY='your-key'")
        print("      export OPENAI_API_KEY='your-key'")
        print("      export GOOGLE_API_KEY='your-key'")
        print()
        print("   2. Reload your shell:")
        print("      source ~/.zshrc")
        print()
        print("   3. Test installation:")
        print("      adc health")
        print()
        print("   4. Use in Claude Code:")
        print("      /adc create contracts for [your feature]")
        print("      @adc-code-generator implement contracts")
        print()
        print("💡 Tip: Run 'adc-setup --symlink' to use symlinks instead of copying")
        print()
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        print()
        print("You can manually copy files from the package:")
        print(f"   Commands: {adc_package / 'claude' / 'commands'}")
        print(f"   Agents: {adc_package / 'claude' / 'agents'}")
        return 1
    
    return 0


def update_user_environment():
    """Update ADC files in user's Claude Code environment.
    
    This is an alias for setup_user_environment() that re-installs all files.
    Useful after upgrading the ADC package to get the latest versions.
    """
    print("🔄 Updating ADC user environment...")
    print()
    print("This will refresh all commands, agents, and schema files.")
    print()
    
    # Just call setup - it already handles overwriting existing files
    return setup_user_environment()


def get_package_info():
    """Get information about installed ADC package."""
    try:
        if hasattr(resources, 'files'):
            adc_package = resources.files('adc')
            roles_dir = adc_package / 'roles'
            schema_file = adc_package / 'schema' / 'adc-schema.qmd'
            
            print("📦 ADC Package Information")
            print()
            print(f"Roles directory: {roles_dir}")
            print(f"Schema file: {schema_file}")
            print()
            
            if roles_dir.exists():
                print("Available roles:")
                for role in roles_dir.iterdir():
                    if role.suffix == '.md':
                        print(f"   • {role.name}")
    except Exception as e:
        print(f"Error getting package info: {e}")


if __name__ == "__main__":
    import sys
    sys.exit(setup_user_environment())
