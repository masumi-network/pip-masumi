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
    
    return result
"""




def _get_requirements_txt() -> str:
    """Generate requirements.txt content for plain Python scaffold."""
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
        "# Get credentials from: admin interface",
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
    """Generate README.md content for plain Python scaffold."""
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


# ============================================================================
# LangChain Template Functions
# ============================================================================

def _get_langchain_agent_template(project_name: str) -> str:
    """Generate agent.py template for LangChain scaffold."""
    return f'''#!/usr/bin/env python3
"""
{project_name} - LangChain Agent Logic
Generated by masumi init

This file contains your LangChain agent setup and process_job function.
The process_job function integrates LangChain with Masumi's endpoint abstraction.
"""

import os
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from tools.custom_tools import get_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = ChatOpenAI(
    model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Create prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant integrated with Masumi."),
    ("human", "{{input}}")
])

# Create chain
chain = LLMChain(llm=llm, prompt=prompt)


async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Process a job using LangChain - integrates with Masumi endpoints.
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing (must be JSON-serializable)
    """
    logger.info(f"Processing job for purchaser: {{identifier_from_purchaser}}")
    logger.info(f"Input data: {{input_data}}")
    
    # Extract input from Masumi format
    text = input_data.get("text", "")
    
    # Invoke LangChain chain
    try:
        result = await chain.ainvoke({{"input": text}})
        output_text = result.get("text", str(result))
        
        logger.info(f"LangChain processing complete. Result: {{output_text[:100]}}...")
        
        # Return result compatible with Masumi serialization
        return {{
            "status": "completed",
            "result": output_text,
            "identifier": identifier_from_purchaser
        }}
    except Exception as e:
        logger.error(f"Error in LangChain processing: {{e}}")
        return {{
            "status": "error",
            "error": str(e)
        }}
'''


def _get_langchain_tools_template() -> str:
    """Generate custom_tools.py template for LangChain scaffold."""
    return '''"""
Custom LangChain tools for your agent.

Add your custom tools here using the @tool decorator.
"""

from langchain.tools import tool


@tool
def example_tool(query: str) -> str:
    """
    Example custom tool - replace with your own tools.
    
    Args:
        query: Input query string
    
    Returns:
        Processed result
    """
    # Implement your tool logic here
    return f"Processed: {query}"


def get_tools():
    """
    Get list of custom tools for the agent.
    
    Returns:
        List of tool objects
    """
    return [example_tool]
'''


def _get_langchain_prompts_template() -> str:
    """Generate prompts.py template for LangChain scaffold."""
    return '''"""
System prompts and prompt templates for your LangChain agent.

Customize these prompts to match your agent's behavior.
"""

SYSTEM_PROMPT = """You are a helpful AI assistant integrated with Masumi.
You process user requests and return helpful responses."""

USER_PROMPT_TEMPLATE = """{input}"""
'''


def _get_langchain_requirements() -> str:
    """Generate requirements.txt for LangChain scaffold."""
    requirements = [
        "masumi",
        "python-dotenv",
        "langchain>=1.0.0,<2.0.0",
        "langchain-openai>=0.1.0",
    ]
    return "\n".join(requirements) + "\n"


def _get_langchain_env_template() -> str:
    """Generate .env.example for LangChain scaffold."""
    base_env = _get_env_template(None, [])
    langchain_env = [
        "",
        "# ============================================",
        "# LLM CONFIGURATION: LangChain",
        "# ============================================",
        "# OpenAI API Key (required for LangChain)",
        "OPENAI_API_KEY=your_openai_api_key_here",
        "",
        "# Optional: Specify model (default: gpt-3.5-turbo)",
        "#OPENAI_MODEL=gpt-3.5-turbo",
        "",
        "# Optional: LangSmith tracing (for debugging)",
        "#LANGCHAIN_TRACING_V2=false",
        "#LANGCHAIN_API_KEY=your_langsmith_api_key",
        "",
    ]
    return base_env + "\n".join(langchain_env)


def _get_langchain_readme_template(project_name: str) -> str:
    """Generate README.md for LangChain scaffold."""
    return f"""# {project_name}

A Masumi agent project with LangChain integration, generated with `masumi init`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or install with masumi extras:
   pip install masumi[langchain]
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - AGENT_IDENTIFIER, PAYMENT_API_KEY, SELLER_VKEY (Masumi)
   # - OPENAI_API_KEY (LangChain LLM)
   ```

3. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   
   # Standalone mode - executes job directly
   masumi run main.py --standalone --input '{{"text": "Hello World"}}'
   ```

## Configuration

### Required Environment Variables

**Masumi:**
- `AGENT_IDENTIFIER`: Your agent ID (get it after registering on Masumi network)
- `PAYMENT_API_KEY`: Your payment API key
- `SELLER_VKEY`: Your seller wallet verification key

**LangChain:**
- `OPENAI_API_KEY`: Your OpenAI API key (required for LangChain LLM)

### Optional Environment Variables

- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `PAYMENT_SERVICE_URL`: Payment service URL (defaults to production)
- `NETWORK`: Network to use - 'Preprod' or 'Mainnet' (defaults to 'Preprod')
- `PORT`: Port to bind to (defaults to 8080)

## Project Structure

```
.
├── main.py              # Entry point - Masumi.run() integration
├── agent.py             # LangChain chain setup + process_job wrapper
├── tools/               # Custom LangChain tools
│   ├── __init__.py
│   └── custom_tools.py  # Example tool definitions
├── config/              # Configuration
│   └── prompts.py       # System prompts
├── requirements.txt     # Dependencies (masumi + langchain)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## LangChain Integration

### Customizing the Agent

1. **Modify the chain in `agent.py`:**
   - Change the prompt template
   - Add tools to the chain
   - Configure different LLM providers

2. **Add custom tools in `tools/custom_tools.py`:**
   ```python
   from langchain.tools import tool
   
   @tool
   def my_custom_tool(input: str) -> str:
       # Your tool logic
       return result
   ```

3. **Update prompts in `config/prompts.py`:**
   - Customize system prompts
   - Modify prompt templates

### Using Different LLM Providers

To use providers other than OpenAI:

1. Install the provider package:
   ```bash
   pip install langchain-anthropic  # For Anthropic
   pip install langchain-google-genai  # For Google
   ```

2. Update `agent.py` imports and initialization:
   ```python
   from langchain_anthropic import ChatAnthropic
   
   llm = ChatAnthropic(
       model="claude-3-sonnet-20240229",
       anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
   )
   ```

3. Add API key to `.env`:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

## Masumi Integration

The `process_job()` function in `agent.py` integrates LangChain with Masumi's endpoint abstraction:

- Accepts `identifier_from_purchaser: str, input_data: dict` (Masumi format)
- Extracts input from `input_data`
- Invokes LangChain chain/agent
- Returns JSON-serializable result

This allows your LangChain agent to work seamlessly with Masumi's payment and API infrastructure.

## Development

### Running Locally

1. Set up your `.env` file with test values
2. Run in standalone mode for testing:
   ```bash
   masumi run main.py --standalone --input '{{"text": "Hello World"}}'
   ```

### Deploying

1. Register your agent on the Masumi network
2. Get your `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, and `SELLER_VKEY`
3. Set environment variables in your deployment environment
4. Run the agent in API mode:
   ```bash
   masumi run
   ```

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [LangChain Documentation](https://python.langchain.com)
- [Masumi CLI Help](https://github.com/masumi-network/masumi)

## License

MIT
"""


# ============================================================================
# CrewAI Template Functions
# ============================================================================

def _get_crewai_crew_template(project_name: str) -> str:
    """Generate crew.py template for CrewAI scaffold."""
    return f'''#!/usr/bin/env python3
"""
{project_name} - CrewAI Crew Setup
Generated by masumi init

This file contains your CrewAI crew setup and process_job function.
The process_job function integrates CrewAI with Masumi's endpoint abstraction.
"""

import os
import yaml
import logging
from pathlib import Path
from crewai import Agent, Task, Crew, Process

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_agents_from_yaml(config_path: Path) -> list:
    """
    Load agent definitions from YAML file.
    
    Args:
        config_path: Path to agents.yaml file
    
    Returns:
        List of Agent objects
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    agents = []
    for agent_config in config.get('agents', []):
        agent = Agent(
            role=agent_config.get('role', ''),
            goal=agent_config.get('goal', ''),
            backstory=agent_config.get('backstory', ''),
            verbose=True,
            allow_delegation=agent_config.get('allow_delegation', False)
        )
        agents.append(agent)
    
    return agents


def load_tasks_from_yaml(config_path: Path, agents: list) -> list:
    """
    Load task definitions from YAML file.
    
    Args:
        config_path: Path to tasks.yaml file
        agents: List of Agent objects to assign tasks to
    
    Returns:
        List of Task objects
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Create agent lookup by role
    agent_lookup = {{agent.role: agent for agent in agents}}
    
    tasks = []
    for task_config in config.get('tasks', []):
        agent_role = task_config.get('agent', '')
        assigned_agent = agent_lookup.get(agent_role)
        
        if not assigned_agent:
            logger.warning(f"Agent '{{agent_role}}' not found for task: {{task_config.get('description', '')}}")
            continue
        
        task = Task(
            description=task_config.get('description', ''),
            expected_output=task_config.get('expected_output', ''),
            agent=assigned_agent
        )
        tasks.append(task)
    
    return tasks


def create_crew() -> Crew:
    """
    Create and configure the CrewAI crew.
    
    Returns:
        Configured Crew object
    """
    config_dir = Path(__file__).parent / 'config'
    agents_path = config_dir / 'agents.yaml'
    tasks_path = config_dir / 'tasks.yaml'
    
    # Load agents and tasks from YAML
    agents = load_agents_from_yaml(agents_path)
    tasks = load_tasks_from_yaml(tasks_path, agents)
    
    # Create crew with sequential process
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    return crew


async def process_job(identifier_from_purchaser: str, input_data: dict):
    """
    Process a job using CrewAI - integrates with Masumi endpoints.
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing (must be JSON-serializable)
    """
    logger.info(f"Processing job for purchaser: {{identifier_from_purchaser}}")
    logger.info(f"Input data: {{input_data}}")
    
    # Extract input from Masumi format
    topic = input_data.get("topic", "")
    
    # Create crew
    crew = create_crew()
    
    # Format task descriptions with input data
    # Note: You may need to update tasks.yaml to use {{topic}} placeholder
    # For now, we'll pass topic as context
    try:
        # Invoke crew with input (kickoff is synchronous, run in executor)
        import asyncio
        result = await asyncio.to_thread(crew.kickoff, inputs={{'topic': topic}})
        
        # Extract result text
        if hasattr(result, 'raw'):
            output_text = result.raw
        elif isinstance(result, str):
            output_text = result
        else:
            output_text = str(result)
        
        logger.info(f"CrewAI processing complete. Result: {{output_text[:100]}}...")
        
        # Return result compatible with Masumi serialization
        return {{
            "status": "completed",
            "result": output_text,
            "identifier": identifier_from_purchaser
        }}
    except Exception as e:
        logger.error(f"Error in CrewAI processing: {{e}}")
        return {{
            "status": "error",
            "error": str(e)
        }}
'''


def _get_crewai_agents_yaml_template() -> str:
    """Generate agents.yaml template for CrewAI scaffold."""
    return '''# CrewAI Agent Definitions
# Each agent has a role, goal, and backstory

agents:
  - role: "Research Analyst"
    goal: "Research and analyze topics thoroughly"
    backstory: |
      You are an expert research analyst with years of experience
      in gathering and analyzing information. You excel at finding
      relevant details and presenting them clearly.
    allow_delegation: false

  - role: "Content Writer"
    goal: "Write clear and engaging content based on research"
    backstory: |
      You are a skilled content writer who transforms research
      into well-structured, engaging content. You have a talent
      for making complex topics accessible.
    allow_delegation: false

# Add more agents as needed
# Use {topic} or other placeholders for dynamic content
'''


def _get_crewai_tasks_yaml_template() -> str:
    """Generate tasks.yaml template for CrewAI scaffold."""
    return '''# CrewAI Task Definitions
# Tasks are executed sequentially by assigned agents

tasks:
  - description: |
      Research the topic: {topic}
      Provide a comprehensive analysis with key points and insights.
    expected_output: |
      A detailed research report covering:
      - Key points about the topic
      - Important insights
      - Relevant information
    agent: "Research Analyst"

  - description: |
      Based on the research provided, write a clear and engaging
      summary about: {topic}
    expected_output: |
      A well-written summary that:
      - Is clear and accessible
      - Highlights key points
      - Is engaging to read
    agent: "Content Writer"

# Add more tasks as needed
# Use {topic} or other placeholders for dynamic content
# Tasks execute in order, so later tasks can reference earlier outputs
'''


def _get_crewai_requirements() -> str:
    """Generate requirements.txt for CrewAI scaffold."""
    requirements = [
        "masumi",
        "python-dotenv",
        "crewai>=1.0.0,<2.0.0",
        "pyyaml>=6.0",
    ]
    return "\n".join(requirements) + "\n"


def _get_crewai_env_template() -> str:
    """Generate .env.example for CrewAI scaffold."""
    base_env = _get_env_template(None, [])
    crewai_env = [
        "",
        "# ============================================",
        "# LLM CONFIGURATION: CrewAI",
        "# ============================================",
        "# OpenAI API Key (default LLM for CrewAI)",
        "OPENAI_API_KEY=your_openai_api_key_here",
        "",
        "# Optional: Anthropic API Key",
        "#ANTHROPIC_API_KEY=your_anthropic_api_key_here",
        "",
        "# Optional: Search API Key (for search tools)",
        "#SERPER_API_KEY=your_serper_api_key_here",
        "",
    ]
    return base_env + "\n".join(crewai_env)


def _get_crewai_readme_template(project_name: str) -> str:
    """Generate README.md for CrewAI scaffold."""
    return f"""# {project_name}

A Masumi agent project with CrewAI integration, generated with `masumi init`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or install with masumi extras:
   pip install masumi[crewai]
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - AGENT_IDENTIFIER, PAYMENT_API_KEY, SELLER_VKEY (Masumi)
   # - OPENAI_API_KEY (CrewAI LLM)
   ```

3. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   
   # Standalone mode - executes job directly
   masumi run main.py --standalone --input '{{"topic": "Artificial Intelligence"}}'
   ```

## Configuration

### Required Environment Variables

**Masumi:**
- `AGENT_IDENTIFIER`: Your agent ID (get it after registering on Masumi network)
- `PAYMENT_API_KEY`: Your payment API key
- `SELLER_VKEY`: Your seller wallet verification key

**CrewAI:**
- `OPENAI_API_KEY`: Your OpenAI API key (required for CrewAI LLM)

### Optional Environment Variables

- `ANTHROPIC_API_KEY`: For using Anthropic models
- `SERPER_API_KEY`: For search tools
- `PAYMENT_SERVICE_URL`: Payment service URL (defaults to production)
- `NETWORK`: Network to use - 'Preprod' or 'Mainnet' (defaults to 'Preprod')
- `PORT`: Port to bind to (defaults to 8080)

## Project Structure

```
.
├── main.py              # Entry point - Masumi.run() integration
├── crew.py              # CrewAI Crew setup + process_job wrapper
├── config/              # YAML configuration files
│   ├── agents.yaml     # Agent definitions (role, goal, backstory)
│   └── tasks.yaml       # Task definitions (description, expected_output)
├── tools/               # Custom tools (optional)
│   ├── __init__.py
│   └── custom_tools.py
├── knowledge/           # Knowledge base files (optional, for RAG)
│   └── .gitkeep
├── requirements.txt     # Dependencies (masumi + crewai)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## CrewAI Integration

### Configuring Agents

Edit `config/agents.yaml` to define your agents:

```yaml
agents:
  - role: "Research Analyst"
    goal: "Research topics thoroughly"
    backstory: "You are an expert researcher..."
    allow_delegation: false
```

Each agent needs:
- `role`: The agent's role/title
- `goal`: What the agent aims to achieve
- `backstory`: Context about the agent's background
- `allow_delegation`: Whether agent can delegate tasks

### Configuring Tasks

Edit `config/tasks.yaml` to define your tasks:

```yaml
tasks:
  - description: "Research the topic: {{topic}}"
    expected_output: "A detailed research report"
    agent: "Research Analyst"
```

Each task needs:
- `description`: What the task should do (can use {{topic}} placeholders)
- `expected_output`: What the task should produce
- `agent`: Which agent should handle this task

Tasks execute sequentially, so later tasks can use outputs from earlier tasks.

### Customizing the Crew

Modify `crew.py` to:
- Change the process type (sequential, hierarchical, etc.)
- Add custom tools
- Configure different LLM providers
- Add knowledge base integration

### Adding Custom Tools

1. Create tools in `tools/custom_tools.py`:
   ```python
   from crewai_tools import tool
   
   @tool("My Custom Tool")
   def my_tool(input: str) -> str:
       # Your tool logic
       return result
   ```

2. Import and add to agents in `crew.py`:
   ```python
   from tools.custom_tools import my_tool
   
   agent = Agent(
       role="...",
       tools=[my_tool]
   )
   ```

### Using Different LLM Providers

To use providers other than OpenAI:

1. Install the provider package:
   ```bash
   pip install anthropic  # For Anthropic
   ```

2. Set environment variable:
   ```
   ANTHROPIC_API_KEY=your_key_here
   ```

3. CrewAI will automatically use the available provider.

## Masumi Integration

The `process_job()` function in `crew.py` integrates CrewAI with Masumi's endpoint abstraction:

- Accepts `identifier_from_purchaser: str, input_data: dict` (Masumi format)
- Extracts input from `input_data`
- Formats tasks with input data (using placeholders like {{topic}})
- Invokes `crew.kickoff()`
- Returns JSON-serializable result

This allows your CrewAI crew to work seamlessly with Masumi's payment and API infrastructure.

## Development

### Running Locally

1. Set up your `.env` file with test values
2. Run in standalone mode for testing:
   ```bash
   masumi run main.py --standalone --input '{{"topic": "AI"}}'
   ```

### Deploying

1. Register your agent on the Masumi network
2. Get your `AGENT_IDENTIFIER`, `PAYMENT_API_KEY`, and `SELLER_VKEY`
3. Set environment variables in your deployment environment
4. Run the agent in API mode:
   ```bash
   masumi run
   ```

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [CrewAI Documentation](https://docs.crewai.com)
- [Masumi CLI Help](https://github.com/masumi-network/masumi)

## License

MIT
"""


# ============================================================================
# Scaffold Functions
# ============================================================================

def _scaffold_simple_python(
    project_name: str,
    project_path: Path,
    interactive: bool
) -> None:
    """Generate plain Python scaffold (default)."""
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
        "from masumi import run",
        "from agent import process_job",
        "",
        "# Define input schema",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "text",',
        '            "type": "string",',
        '            "name": "Text Input"',
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
        from .interactive_cli import animate_loading, print_success
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
                print_success(success_msg)
            elif i == 1:
                (project_path / "agent.py").write_text(agent_template)
                print_success(success_msg)
            elif i == 2:
                (project_path / "main.py").write_text(main_template)
                print_success(success_msg)
            elif i == 3:
                (project_path / "requirements.txt").write_text(_get_requirements_txt())
                print_success(success_msg)
            elif i == 4:
                (project_path / ".env.example").write_text(_get_env_template(None, []))
                print_success(success_msg)
            elif i == 5:
                (project_path / "README.md").write_text(_get_readme_template(project_name))
                print_success(success_msg)
            elif i == 6:
                (project_path / ".gitignore").write_text(_get_gitignore_template())
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


def _scaffold_langchain(
    project_name: str,
    project_path: Path,
    interactive: bool
) -> None:
    """Generate LangChain scaffold."""
    # Create directories
    tools_dir = project_path / "tools"
    config_dir = project_path / "config"
    tools_dir.mkdir(exist_ok=True)
    config_dir.mkdir(exist_ok=True)
    
    # Build main.py template (entry point - same pattern as simple)
    main_template_parts = [
        "#!/usr/bin/env python3",
        '"""',
        f"{project_name} - Main Entry Point",
        "Generated by masumi init",
        "",
        "This is the entry point for your Masumi agent with LangChain.",
        "Run this file to start the agent server.",
        '"""',
        "# Load environment variables from .env file",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "",
        "from masumi import run",
        "from agent import process_job",
        "",
        "# Define input schema",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "text",',
        '            "type": "string",',
        '            "name": "Text Input"',
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
        from .interactive_cli import animate_loading, print_success
        steps = [
            ("Creating project structure", "Project directory created"),
            ("Generating agent.py", "LangChain agent file generated"),
            ("Generating main.py", "Entry point file generated"),
            ("Creating tools directory", "Tools directory created"),
            ("Creating config directory", "Config directory created"),
            ("Creating requirements.txt", "Dependencies file created"),
            ("Setting up .env.example", "Environment template created"),
            ("Writing README.md", "Documentation created"),
            ("Adding .gitignore", "Git ignore file added")
        ]
        for i, (step_name, success_msg) in enumerate(steps):
            animate_loading(f"{step_name}...", duration=0.2)
            if i == 0:
                print_success(success_msg)
            elif i == 1:
                (project_path / "agent.py").write_text(_get_langchain_agent_template(project_name))
                print_success(success_msg)
            elif i == 2:
                (project_path / "main.py").write_text(main_template)
                print_success(success_msg)
            elif i == 3:
                (tools_dir / "__init__.py").write_text("")
                (tools_dir / "custom_tools.py").write_text(_get_langchain_tools_template())
                print_success(success_msg)
            elif i == 4:
                (config_dir / "prompts.py").write_text(_get_langchain_prompts_template())
                print_success(success_msg)
            elif i == 5:
                (project_path / "requirements.txt").write_text(_get_langchain_requirements())
                print_success(success_msg)
            elif i == 6:
                (project_path / ".env.example").write_text(_get_langchain_env_template())
                print_success(success_msg)
            elif i == 7:
                (project_path / "README.md").write_text(_get_langchain_readme_template(project_name))
                print_success(success_msg)
            elif i == 8:
                (project_path / ".gitignore").write_text(_get_gitignore_template())
                print_success(success_msg)
            time.sleep(0.05)
    else:
        # Non-interactive mode - just write files
        (project_path / "agent.py").write_text(_get_langchain_agent_template(project_name))
        (project_path / "main.py").write_text(main_template)
        (tools_dir / "__init__.py").write_text("")
        (tools_dir / "custom_tools.py").write_text(_get_langchain_tools_template())
        (config_dir / "prompts.py").write_text(_get_langchain_prompts_template())
        (project_path / "requirements.txt").write_text(_get_langchain_requirements())
        (project_path / ".env.example").write_text(_get_langchain_env_template())
        (project_path / "README.md").write_text(_get_langchain_readme_template(project_name))
        (project_path / ".gitignore").write_text(_get_gitignore_template())


def _scaffold_crewai(
    project_name: str,
    project_path: Path,
    interactive: bool
) -> None:
    """Generate CrewAI scaffold."""
    # Create directories
    config_dir = project_path / "config"
    tools_dir = project_path / "tools"
    knowledge_dir = project_path / "knowledge"
    config_dir.mkdir(exist_ok=True)
    tools_dir.mkdir(exist_ok=True)
    knowledge_dir.mkdir(exist_ok=True)
    
    # Build main.py template (entry point - same pattern as simple)
    main_template_parts = [
        "#!/usr/bin/env python3",
        '"""',
        f"{project_name} - Main Entry Point",
        "Generated by masumi init",
        "",
        "This is the entry point for your Masumi agent with CrewAI.",
        "Run this file to start the agent server.",
        '"""',
        "# Load environment variables from .env file",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "",
        "from masumi import run",
        "from crew import process_job",
        "",
        "# Define input schema",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "topic",',
        '            "type": "string",',
        '            "name": "Topic"',
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
        from .interactive_cli import animate_loading, print_success
        steps = [
            ("Creating project structure", "Project directory created"),
            ("Generating crew.py", "CrewAI crew file generated"),
            ("Generating main.py", "Entry point file generated"),
            ("Creating config directory", "Config directory created"),
            ("Creating tools directory", "Tools directory created"),
            ("Creating knowledge directory", "Knowledge directory created"),
            ("Creating requirements.txt", "Dependencies file created"),
            ("Setting up .env.example", "Environment template created"),
            ("Writing README.md", "Documentation created"),
            ("Adding .gitignore", "Git ignore file added")
        ]
        for i, (step_name, success_msg) in enumerate(steps):
            animate_loading(f"{step_name}...", duration=0.2)
            if i == 0:
                print_success(success_msg)
            elif i == 1:
                (project_path / "crew.py").write_text(_get_crewai_crew_template(project_name))
                print_success(success_msg)
            elif i == 2:
                (project_path / "main.py").write_text(main_template)
                print_success(success_msg)
            elif i == 3:
                (config_dir / "agents.yaml").write_text(_get_crewai_agents_yaml_template())
                (config_dir / "tasks.yaml").write_text(_get_crewai_tasks_yaml_template())
                print_success(success_msg)
            elif i == 4:
                (tools_dir / "__init__.py").write_text("")
                (tools_dir / "custom_tools.py").write_text("# Add your CrewAI custom tools here\n")
                print_success(success_msg)
            elif i == 5:
                (knowledge_dir / ".gitkeep").write_text("")
                print_success(success_msg)
            elif i == 6:
                (project_path / "requirements.txt").write_text(_get_crewai_requirements())
                print_success(success_msg)
            elif i == 7:
                (project_path / ".env.example").write_text(_get_crewai_env_template())
                print_success(success_msg)
            elif i == 8:
                (project_path / "README.md").write_text(_get_crewai_readme_template(project_name))
                print_success(success_msg)
            elif i == 9:
                (project_path / ".gitignore").write_text(_get_gitignore_template())
                print_success(success_msg)
            time.sleep(0.05)
    else:
        # Non-interactive mode - just write files
        (project_path / "crew.py").write_text(_get_crewai_crew_template(project_name))
        (project_path / "main.py").write_text(main_template)
        (config_dir / "agents.yaml").write_text(_get_crewai_agents_yaml_template())
        (config_dir / "tasks.yaml").write_text(_get_crewai_tasks_yaml_template())
        (tools_dir / "__init__.py").write_text("")
        (tools_dir / "custom_tools.py").write_text("# Add your CrewAI custom tools here\n")
        (knowledge_dir / ".gitkeep").write_text("")
        (project_path / "requirements.txt").write_text(_get_crewai_requirements())
        (project_path / ".env.example").write_text(_get_crewai_env_template())
        (project_path / "README.md").write_text(_get_crewai_readme_template(project_name))
        (project_path / ".gitignore").write_text(_get_gitignore_template())


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
    
    framework = "plain"  # Default framework
    
    # Set default project name first
    if project_name is None:
        project_name = "masumi-agent"
    
    if interactive:
        # Import interactive CLI utilities
        from .interactive_cli import (
            show_banner, select_option, get_input,
            show_progress, show_completion_message, print_info, print_warning
        )
        
        # Show banner
        show_banner()
        
        # Get project name (with default)
        project_name = get_input("Project name", default=project_name)

        print()  # Add spacing
        
        # Framework selection
        framework = select_option(
            "Select framework",
            [
                {"value": "plain", "label": "Plain Python", "description": "Default Python scaffold (no AI framework)"},
                {"value": "langchain", "label": "LangChain", "description": "LangChain-based agent scaffold"},
                {"value": "crewai", "label": "CrewAI", "description": "CrewAI-based agent scaffold"}
            ],
            default=0  # Plain Python is default
        )
        
        print()  # Add spacing after selection
    
    # Output directory always matches project name
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
    
    # Route to appropriate scaffold function
    if framework == "langchain":
        _scaffold_langchain(project_name, project_path, interactive)
    elif framework == "crewai":
        _scaffold_crewai(project_name, project_path, interactive)
    else:  # plain or default
        _scaffold_simple_python(project_name, project_path, interactive)

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
