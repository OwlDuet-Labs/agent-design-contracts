"""
Get role file path from installed ADC package.
Useful for agents that need to reference role definitions.
"""
import sys
from pathlib import Path


def get_role_path(role_name: str) -> Path:
    """
    Get the path to a role file from the installed ADC package.
    
    Args:
        role_name: Name of the role (e.g., 'code_generator', 'auditor')
    
    Returns:
        Path to the role file
    
    Raises:
        FileNotFoundError: If the role file doesn't exist
    """
    try:
        # Try using importlib.resources (Python 3.9+)
        from importlib import resources
        
        # Get the adc package resources
        adc_package = resources.files('adc')
        role_file = adc_package / 'roles' / f'{role_name}.md'
        
        # Check if it exists
        if hasattr(role_file, 'exists') and role_file.exists():
            return Path(str(role_file))
        else:
            # Fallback: try to read it to verify it exists
            try:
                role_file.read_text()
                return Path(str(role_file))
            except:
                pass
    except (ImportError, Exception):
        pass
    
    # Fallback: check if we're in the source directory
    current_dir = Path.cwd()
    
    # Try ./roles/
    local_role = current_dir / 'roles' / f'{role_name}.md'
    if local_role.exists():
        return local_role
    
    # Try ./adc/roles/
    symlink_role = current_dir / 'adc' / 'roles' / f'{role_name}.md'
    if symlink_role.exists():
        return symlink_role
    
    # Try ../roles/ (if we're in a subdirectory)
    parent_role = current_dir.parent / 'roles' / f'{role_name}.md'
    if parent_role.exists():
        return parent_role
    
    raise FileNotFoundError(
        f"Role '{role_name}' not found. "
        f"Tried: package data, ./roles/, ./adc/roles/, ../roles/"
    )


def list_available_roles() -> list[str]:
    """
    List all available role files.
    
    Returns:
        List of role names (without .md extension)
    """
    roles = []
    
    try:
        from importlib import resources
        adc_package = resources.files('adc')
        roles_dir = adc_package / 'roles'
        
        if hasattr(roles_dir, 'iterdir'):
            for role_file in roles_dir.iterdir():
                if role_file.name.endswith('.md'):
                    roles.append(role_file.name[:-3])  # Remove .md
    except:
        # Fallback: check local directories
        for search_dir in [Path.cwd() / 'roles', Path.cwd() / 'adc' / 'roles']:
            if search_dir.exists():
                for role_file in search_dir.glob('*.md'):
                    role_name = role_file.stem
                    if role_name not in roles:
                        roles.append(role_name)
    
    return sorted(roles)


def get_role_command(args):
    """
    Handle the 'adc get-role' command.
    
    Args:
        args: Parsed command-line arguments
    """
    if args.list:
        # List all available roles
        roles = list_available_roles()
        if roles:
            print("Available roles:")
            for role in roles:
                print(f"  - {role}")
        else:
            print("No roles found.", file=sys.stderr)
            sys.exit(1)
        return
    
    if not args.role_name:
        print("Error: role name required. Use --list to see available roles.", file=sys.stderr)
        sys.exit(1)
    
    try:
        role_path = get_role_path(args.role_name)
        
        if args.content:
            # Print the content of the role file
            print(role_path.read_text())
        else:
            # Print just the path
            print(role_path)
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nUse 'adc get-role --list' to see available roles.", file=sys.stderr)
        sys.exit(1)


def add_get_role_parser(subparsers):
    """Add get-role command parser."""
    parser = subparsers.add_parser(
        'get-role',
        help='Get path to role definition file',
        description='Get the file path or content of an ADC role definition'
    )
    
    parser.add_argument(
        'role_name',
        nargs='?',
        help='Name of the role (e.g., code_generator, auditor, refiner)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available roles'
    )
    
    parser.add_argument(
        '--content', '-c',
        action='store_true',
        help='Print role file content instead of path'
    )
    
    parser.set_defaults(func=get_role_command)
