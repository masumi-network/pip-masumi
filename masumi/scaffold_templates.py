"""
Templates for generating Masumi agent projects with full project structure.
"""

import os
import time
from typing import Optional, List, Dict, Tuple
from pathlib import Path


# Framework templates
LANGCHAIN_TEMPLATE = '''from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Framework setup
llm = OpenAI(temperature=0.7)

# Example prompt template
prompt = PromptTemplate(
    input_variables=["text"],
    template="Process the following text: {text}"
)

chain = LLMChain(llm=llm, prompt=prompt)
'''

CREWAI_TEMPLATE = '''from crewai import Agent, Task, Crew

# Framework setup - define your agents and tasks here
# Example:
# agent = Agent(
#     role='Agent Role',
#     goal='Agent Goal',
#     backstory='Agent backstory'
# )
'''

AUTOGEN_TEMPLATE = '''from autogen import ConversableAgent

# Framework setup - define your agents here
# Example:
# agent = ConversableAgent(
#     name="agent",
#     system_message="You are a helpful assistant.",
#     llm_config={"config_list": [{"model": "gpt-4", "api_key": os.getenv("OPENAI_API_KEY")}]}
# )
'''


def _get_framework_template(framework: Optional[str]) -> Tuple[str, str, str]:
    """Get framework template, imports, and setup code separately."""
    if framework == "langchain":
        imports = "from langchain.llms import OpenAI\nfrom langchain.chains import LLMChain\nfrom langchain.prompts import PromptTemplate"
        setup = """# Framework setup
llm = OpenAI(temperature=0.7)

# Example prompt template
prompt = PromptTemplate(
    input_variables=["text"],
    template="Process the following text: {text}"
)

chain = LLMChain(llm=llm, prompt=prompt)"""
        return LANGCHAIN_TEMPLATE, imports, setup
    elif framework == "crewai":
        imports = "from crewai import Agent, Task, Crew"
        setup = """# Framework setup - define your agents and tasks here
# Example:
# agent = Agent(
#     role='Agent Role',
#     goal='Agent Goal',
#     backstory='Agent backstory'
# )"""
        return CREWAI_TEMPLATE, imports, setup
    elif framework == "autogen":
        imports = "from autogen import ConversableAgent"
        setup = """# Framework setup - define your agents here
# Example:
# agent = ConversableAgent(
#     name="agent",
#     system_message="You are a helpful assistant.",
#     llm_config={"config_list": [{"model": "gpt-4", "api_key": os.getenv("OPENAI_API_KEY")}]}
# )"""
        return AUTOGEN_TEMPLATE, imports, setup
    else:
        return "", "", ""


def _get_process_job_template(framework: Optional[str]) -> str:
    """Get process_job function template with framework integration."""
    framework_code = ""
    
    if framework == "langchain":
        framework_code = """    # Example: Use LangChain
    text = input_data.get("text", "")
    result = chain.run(text=text)
"""
    elif framework == "crewai":
        framework_code = """    # Example: Use CrewAI
    # task = Task(description=f"Process: {input_data}", agent=agent)
    # crew = Crew(agents=[agent], tasks=[task])
    # result = crew.kickoff()
    result = {"status": "processed", "data": input_data}
"""
    elif framework == "autogen":
        framework_code = """    # Example: Use AutoGen
    # result = agent.generate_reply(messages=[{"role": "user", "content": str(input_data)}])
    result = {"status": "processed", "data": input_data}
"""
    else:
        framework_code = """    # Process input
    text = input_data.get("text", "")
    result = f"Processed: {text}"
"""
    
    return f"""async def process_job(identifier_from_purchaser: str, input_data: dict):
    \"\"\"
    Process a job - implement your agentic behavior here
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing
    \"\"\"
{framework_code}
    return {{"result": result, "purchaser": identifier_from_purchaser}}
"""




def _get_requirements_txt(framework: Optional[str]) -> str:
    """Generate requirements.txt content."""
    requirements = [
        "masumi>=0.1.41",
        "python-dotenv>=0.19.0",
    ]
    
    # Framework dependencies
    if framework:
        requirements.append(f"{framework}>=0.1.0")
    
    return "\n".join(requirements) + "\n"


def _get_env_template(database: Optional[str], framework: Optional[str], additional_libs: List[str]) -> str:
    """Generate .env file template matching the root .env.example format."""
    env_lines = [
        "# Masumi Agent Configuration",
        "# Copy this file to .env: cp .env.example .env",
        "# Get credentials from: https://admin.masumi.network",
        "",
        "# ============================================",
        "# REQUIRED (for API mode)",
        "# ============================================",
        "AGENT_IDENTIFIER=your-agent-id-here",
        "SELLER_VKEY=your-seller-vkey-here",
        "PAYMENT_API_KEY=your-payment-api-key-here",
        "",
        "# ============================================",
        "# OPTIONAL",
        "# ============================================",
        "# Network: Preprod (testnet) or Mainnet (production)",
        "NETWORK=Preprod",
        "",
        "# Payment service URL",
        "PAYMENT_SERVICE_URL=https://payment.masumi.network/api/v1",
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
    
    # Framework/API keys
    if framework == "langchain":
        env_lines.extend([
            "# ============================================",
            "# API KEYS: OpenAI",
            "# ============================================",
            "OPENAI_API_KEY=your_openai_api_key_here",
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


def _get_readme_template(project_name: str, framework: Optional[str]) -> str:
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
   masumi run main.py
   
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
    
    if framework:
        readme += f"""
### Framework

This project uses **{framework.capitalize()}** for agent orchestration.
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
   masumi run main.py
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
    framework: Optional[str] = None,
    interactive: bool = True
) -> None:
    """
    Generate a new Masumi agent project with full structure.
    
    Args:
        project_name: Name of the project (default: "masumi-agent")
        output_dir: Output directory (default: project_name)
        framework: Framework choice ("langchain", "crewai", "autogen", or None)
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
        
        # Get output directory
        if output_dir is None:
            output_dir = get_input("Output directory", default=project_name)
        
        # Select framework
        if framework is None:
            framework = select_option(
                "🔧 Select a framework",
                [
                    {
                        "key": "1",
                        "label": "None",
                        "description": "Plain Python (default)",
                        "value": None
                    },
                    {
                        "key": "2",
                        "label": "LangChain",
                        "description": "LLM orchestration and chaining",
                        "value": "langchain"
                    },
                    {
                        "key": "3",
                        "label": "CrewAI",
                        "description": "Multi-agent framework for collaborative AI",
                        "value": "crewai"
                    },
                    {
                        "key": "4",
                        "label": "AutoGen",
                        "description": "Conversational AI agents framework",
                        "value": "autogen"
                    }
                ],
                default=0
            )
        
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
    _, fw_imports, fw_setup = _get_framework_template(framework)
    process_job_code = _get_process_job_template(framework)
    
    # Build imports section (collect all unique imports)
    imports_set = set()
    imports_set.add("import os")
    imports_set.add("from masumi import run, Config")
    imports_set.add("import logging")
    
    # Add framework imports
    if fw_imports:
        for imp in fw_imports.split('\n'):
            if imp.strip():
                imports_set.add(imp.strip())
    
    # Convert to sorted list (standard library first, then third-party)
    imports_list = sorted(imports_set, key=lambda x: (not x.startswith('import '), x))
    
    # Build header comment
    header_parts = [f"{project_name} - Masumi Agent", "Generated by masumi init"]
    if framework:
        header_parts.append(f"Framework: {framework.capitalize()}")
    
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
    ]
    
    # Add framework setup
    if fw_setup:
        agent_template_parts.extend([
            fw_setup,
            "",
        ])
    
    # Add process_job function
    agent_template_parts.extend([
        "# Define agent logic",
        process_job_code,
        ""
    ])
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
                (project_path / "requirements.txt").write_text(_get_requirements_txt(framework))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 4:
                (project_path / ".env.example").write_text(_get_env_template(None, framework, []))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 5:
                (project_path / "README.md").write_text(_get_readme_template(project_name, framework))
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
        (project_path / "requirements.txt").write_text(_get_requirements_txt(framework))
        (project_path / ".env.example").write_text(_get_env_template(None, framework, []))
        (project_path / "README.md").write_text(_get_readme_template(project_name, framework))
        (project_path / ".gitignore").write_text(_get_gitignore_template())

    # Show completion message
    if interactive:
        from .interactive_cli import show_completion_message
        show_completion_message(project_name, output_dir)
    else:
        print(f"\n✅ Generated Masumi agent project: {output_dir}")
        print("\nProject structure:")
        print(f"  {output_dir}/")
        print(f"    ├── main.py          # Entry point - run this to start the agent")
        print(f"    ├── agent.py         # Agent logic - implement your agentic behavior here")
        print(f"    ├── requirements.txt")
        print(f"    ├── .env.example")
        print(f"    ├── .gitignore")
        print(f"    └── README.md")
        print("\nNext steps:")
        print(f"  1-3. Quick setup (copy & paste):")
        print(f"     cd {output_dir} && pip install -r requirements.txt && cp .env.example .env")
        print("     # Edit .env with your actual values")
        print("  4. Run your agent:")
        print("     masumi run main.py")
        print("     # Or for standalone testing:")
        print("     masumi run main.py --standalone")
        print()
