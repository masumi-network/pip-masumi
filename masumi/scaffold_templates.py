"""
Templates for generating Masumi agent projects with full project structure.
"""

import os
import time
from typing import Optional, List, Dict
from pathlib import Path


def _get_process_job_template() -> str:
    """Get process_job function template."""
    return """async def process_job(identifier_from_purchaser: str, input_data: dict):
    \"\"\"
    Process a job - implement your agentic behavior here
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing
    \"\"\"
    # Process input
    text = input_data.get("text", "")
    result = f"Processed: {text}"
    
    return {"result": result, "purchaser": identifier_from_purchaser}
"""




def _get_requirements_txt() -> str:
    """Generate requirements.txt content."""
    requirements = [
        "masumi",
        "python-dotenv",
    ]
    
    return "\n".join(requirements) + "\n"


def _get_env_template(database: Optional[str], additional_libs: List[str]) -> str:
    """Generate .env file template matching the root .env.example format."""
    env_lines = [
        "# Masumi Agent Configuration",
        "# Copy this file to .env: cp .env.example .env",
        "# Get credentials from: https://admin.masumi.network",
        "",
        "# ============================================",
        "# REQUIRED (for API mode)",
        "# ============================================",
        "AGENT_IDENTIFIER=",
        "SELLER_VKEY=",
        "PAYMENT_API_KEY=",
        "",
        "# ============================================",
        "# OPTIONAL",
        "# ============================================",
        "# Network: Preprod (testnet) or Mainnet (production)",
        "NETWORK=Preprod",
        "",
        "# Payment service URL add /api/v1 at the end",
        "PAYMENT_SERVICE_URL=",
        "",
        "# Server configuration",
        "#HOST=0.0.0.0",
        "#PORT=8080",
        "",
        "# Testing - skip blockchain payments",
        "#MOCK_PAYMENTS=false",
        "",
    ]
    
    # Database environment variables
    if database == "sqlite":
        env_lines.extend([
            "# ============================================",
            "# DATABASE: SQLite",
            "# ============================================",
            "DB_PATH=agent.db",
            "",
        ])
    elif database == "postgresql":
        env_lines.extend([
            "# ============================================",
            "# DATABASE: PostgreSQL",
            "# ============================================",
            "DB_HOST=localhost",
            "DB_PORT=5432",
            "DB_NAME=masumi_agent",
            "DB_USER=postgres",
            "DB_PASSWORD=your_password_here",
            "",
        ])
    elif database == "mongodb":
        env_lines.extend([
            "# ============================================",
            "# DATABASE: MongoDB",
            "# ============================================",
            "MONGO_URI=mongodb://localhost:27017/",
            "DB_NAME=masumi_agent",
            "",
        ])
    elif database == "redis":
        env_lines.extend([
            "# ============================================",
            "# DATABASE: Redis",
            "# ============================================",
            "REDIS_HOST=localhost",
            "REDIS_PORT=6379",
            "REDIS_DB=0",
            "",
        ])
    
    if "anthropic" in additional_libs:
        env_lines.extend([
            "# ============================================",
            "# API KEYS: Anthropic",
            "# ============================================",
            "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
            "",
        ])
    
    return "\n".join(env_lines)


def _get_readme_template(project_name: str) -> str:
    """Generate README.md content."""
    readme = f"""# {project_name}

A Masumi agent project generated with `masumi init`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   # If no file is provided, defaults to main.py
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   
   # Standalone mode - executes job directly
   masumi run main.py --standalone
   ```

## Configuration

### Required Environment Variables

- `AGENT_IDENTIFIER`: Your agent ID (get it after registering on Masumi network)
- `PAYMENT_API_KEY`: Your payment API key
- `SELLER_VKEY`: Your seller wallet verification key

### Optional Environment Variables

- `PAYMENT_SERVICE_URL`: Payment service URL (defaults to production)
- `NETWORK`: Network to use - 'Preprod' or 'Mainnet' (defaults to 'Preprod')
- `PORT`: Port to bind to (defaults to 8080)
"""
    
    readme += """
## Project Structure

```
.
├── main.py           # Entry point - run this to start the agent
├── agent.py          # Agent logic - implement your agentic behavior here
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create from .env.example)
├── .env.example      # Environment variables template
└── README.md         # This file
```

## Development

### Running Locally

1. Set up your `.env` file with test values
2. Run in standalone mode for testing:
   ```bash
   masumi run main.py --standalone --input '{"text": "Hello World"}'
   ```

### Deploying

1. Register your agent on the Masumi network
2. Get your `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, and `SELLER_VKEY`
3. Set environment variables in your deployment environment
4. Run the agent in API mode:
   ```bash
   masumi run                    # Runs main.py by default
   masumi run main.py           # Or specify explicitly
   ```

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [Masumi CLI Help](https://github.com/masumi-network/masumi)

## License

MIT
"""
    return readme


def _get_gitignore_template() -> str:
    """Generate .gitignore content."""
    return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
"""


def scaffold(
    project_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    interactive: bool = True
) -> None:
    """
    Generate a new Masumi agent project with full structure.
    
    Args:
        project_name: Name of the project (default: "masumi-agent")
        output_dir: Output directory (default: project_name)
        interactive: If True, prompt user for choices
    """
    
    if interactive:
        # Import interactive CLI utilities
        from .interactive_cli import (
            show_banner, select_option, get_input,
            show_progress, show_completion_message, print_info, print_warning
        )
        
        # Show banner
        show_banner()
        
        # Get project name
        if project_name is None:
            project_name = get_input("Project name", default="masumi-agent")

        # Set output directory to project name automatically
        if output_dir is None:
            output_dir = project_name
        
        print()  # Add spacing
    
    # Set defaults
    if project_name is None:
        project_name = "masumi-agent"
    if output_dir is None:
        output_dir = project_name
    
    # Create project directory
    project_path = Path(output_dir)
    if project_path.exists():
        if interactive:
            from .interactive_cli import get_input, print_warning, print_error
            print_warning(f"Directory '{output_dir}' already exists.")
            response = get_input("Overwrite? (y/N)", default="N").lower()
            if response != 'y':
                print_error("Cancelled.")
                return
        # Remove existing directory
        import shutil
        shutil.rmtree(project_path)
    
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Generate templates
    process_job_code = _get_process_job_template()
    
    # Build imports section
    imports_list = [
        "import os",
        "from masumi import run, Config",
        "import logging",
    ]
    
    # Build agent.py template (agent logic)
    agent_template_parts = [
        "#!/usr/bin/env python3",
        '"""',
        f"{project_name} - Agent Logic",
        "Generated by masumi init",
        "",
        "This file contains your agent's business logic.",
        "Implement your agentic behavior in the process_job function.",
        '"""',
        "\n".join(imports_list),
        "",
        "# Configure logging",
        "logging.basicConfig(",
        "    level=logging.INFO,",
        "    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'",
        ")",
        "logger = logging.getLogger(__name__)",
        "",
        "# Define agent logic",
        process_job_code,
        ""
    ]
    agent_template = "\n".join(agent_template_parts)
    
    # Build main.py template (entry point)
    main_template_parts = [
        "#!/usr/bin/env python3",
        '"""',
        f"{project_name} - Main Entry Point",
        "Generated by masumi init",
        "",
        "This is the entry point for your Masumi agent.",
        "Run this file to start the agent server.",
        '"""',
        "# Load environment variables from .env file",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "",
        "import os",
        "from masumi import run",
        "from agent import process_job",
        "",
        "# Define input schema",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "text",',
        '            "type": "string",',
        '            "name": "Text Input",',
        '            "data": {',
        '                "description": "Text to process"',
        '            },',
        '            "validations": [',
        '                {"validation": "required", "value": "true"}',
        '            ]',
        '        }',
        '    ]',
        '}',
        "",
        "# Main entry point",
        "if __name__ == \"__main__\":",
        "    # Config and identifiers loaded from environment variables",
        "    # Default mode is API - use --standalone flag to run standalone",
        "    run(",
        "        start_job_handler=process_job,",
        "        input_schema_handler=INPUT_SCHEMA",
        "        # config, agent_identifier, network loaded from env vars automatically",
        "    )",
        ""
    ]
    main_template = "\n".join(main_template_parts)
    
    # Write all files with progress indication
    if interactive:
        from .interactive_cli import show_progress, animate_loading
        steps = [
            ("Creating project structure", "Project directory created"),
            ("Generating agent.py", "Agent logic file generated"),
            ("Generating main.py", "Entry point file generated"),
            ("Creating requirements.txt", "Dependencies file created"),
            ("Setting up .env.example", "Environment template created"),
            ("Writing README.md", "Documentation created"),
            ("Adding .gitignore", "Git ignore file added")
        ]
        for i, (step_name, success_msg) in enumerate(steps):
            animate_loading(f"{step_name}...", duration=0.2)
            if i == 0:
                # Directory already created, just show success
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 1:
                (project_path / "agent.py").write_text(agent_template)
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 2:
                (project_path / "main.py").write_text(main_template)
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 3:
                (project_path / "requirements.txt").write_text(_get_requirements_txt())
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 4:
                (project_path / ".env.example").write_text(_get_env_template(None, []))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 5:
                (project_path / "README.md").write_text(_get_readme_template(project_name))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 6:
                (project_path / ".gitignore").write_text(_get_gitignore_template())
                from .interactive_cli import print_success
                print_success(success_msg)
            time.sleep(0.05)
    else:
        # Non-interactive mode - just write files
        (project_path / "agent.py").write_text(agent_template)
        (project_path / "main.py").write_text(main_template)
        (project_path / "requirements.txt").write_text(_get_requirements_txt())
        (project_path / ".env.example").write_text(_get_env_template(None, []))
        (project_path / "README.md").write_text(_get_readme_template(project_name))
        (project_path / ".gitignore").write_text(_get_gitignore_template())

    # Show completion message
    if interactive:
        from .interactive_cli import show_completion_message
        show_completion_message(project_name, output_dir)
    else:
        print(f"\n✅ Generated Masumi agent project: {output_dir}\n")
        print(f"Quick start:")
        print(f"cd {output_dir} && pip install -r requirements.txt && cp .env.example .env")
        print(f"\nStart Building")
        print()
