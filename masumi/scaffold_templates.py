"""
Scaffold templates for generating Masumi agent projects with full project structure.
"""

import os
import time
from typing import Optional, List, Dict, Tuple
from pathlib import Path


# Database templates
SQLITE_TEMPLATE = '''import sqlite3

# Database setup
DB_PATH = os.getenv("DB_PATH", "agent.db")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    return conn
'''

POSTGRESQL_TEMPLATE = '''import psycopg2
from psycopg2 import pool

# Database setup
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "masumi_agent"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

# Connection pool
db_pool = None

def get_db():
    """Get database connection from pool"""
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
    return db_pool.getconn()

def return_db(conn):
    """Return connection to pool"""
    db_pool.putconn(conn)
'''

MONGODB_TEMPLATE = '''from pymongo import MongoClient

# Database setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "masumi_agent")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    """Get database instance"""
    return db
'''

REDIS_TEMPLATE = '''import redis

# Redis setup
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def get_redis():
    """Get Redis client"""
    return redis_client
'''


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


# Additional library templates
OPENAI_TEMPLATE = '''import openai

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")
'''

ANTHROPIC_TEMPLATE = '''from anthropic import Anthropic

# Anthropic setup
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
'''

REQUESTS_TEMPLATE = '''import requests

# Requests library available for HTTP calls
# Example: response = requests.get("https://api.example.com/data")
'''

PANDAS_TEMPLATE = '''import pandas as pd

# Pandas available for data manipulation
# Example: df = pd.DataFrame(data)
'''

NUMPY_TEMPLATE = '''import numpy as np

# NumPy available for numerical operations
# Example: array = np.array([1, 2, 3])
'''


def _get_database_template(database: Optional[str]) -> Tuple[str, str, str]:
    """Get database template, imports, and setup code separately."""
    if database == "sqlite":
        imports = "import sqlite3"
        setup = """# Database setup
DB_PATH = os.getenv("DB_PATH", "agent.db")

def get_db():
    \"\"\"Get database connection\"\"\"
    conn = sqlite3.connect(DB_PATH)
    return conn"""
        return SQLITE_TEMPLATE, imports, setup
    elif database == "postgresql":
        imports = "import psycopg2\nfrom psycopg2 import pool"
        setup = """# Database setup
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "masumi_agent"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "")
}

# Connection pool
db_pool = None

def get_db():
    \"\"\"Get database connection from pool\"\"\"
    global db_pool
    if db_pool is None:
        db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_CONFIG)
    return db_pool.getconn()

def return_db(conn):
    \"\"\"Return connection to pool\"\"\"
    db_pool.putconn(conn)"""
        return POSTGRESQL_TEMPLATE, imports, setup
    elif database == "mongodb":
        imports = "from pymongo import MongoClient"
        setup = """# Database setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("DB_NAME", "masumi_agent")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db():
    \"\"\"Get database instance\"\"\"
    return db"""
        return MONGODB_TEMPLATE, imports, setup
    elif database == "redis":
        imports = "import redis"
        setup = """# Redis setup
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def get_redis():
    \"\"\"Get Redis client\"\"\"
    return redis_client"""
        return REDIS_TEMPLATE, imports, setup
    else:
        return "", "", ""


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


def _get_additional_library_template(library: str) -> Tuple[str, str, str]:
    """Get additional library template, imports, and setup code separately."""
    if library == "openai":
        imports = "import openai"
        setup = """# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")"""
        return OPENAI_TEMPLATE, imports, setup
    elif library == "anthropic":
        imports = "from anthropic import Anthropic"
        setup = """# Anthropic setup
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))"""
        return ANTHROPIC_TEMPLATE, imports, setup
    elif library == "requests":
        imports = "import requests"
        setup = """# Requests library available for HTTP calls
# Example: response = requests.get("https://api.example.com/data")"""
        return REQUESTS_TEMPLATE, imports, setup
    elif library == "pandas":
        imports = "import pandas as pd"
        setup = """# Pandas available for data manipulation
# Example: df = pd.DataFrame(data)"""
        return PANDAS_TEMPLATE, imports, setup
    elif library == "numpy":
        imports = "import numpy as np"
        setup = """# NumPy available for numerical operations
# Example: array = np.array([1, 2, 3])"""
        return NUMPY_TEMPLATE, imports, setup
    else:
        return "", "", ""


def _get_process_job_template(database: Optional[str], framework: Optional[str], additional_libs: List[str]) -> str:
    """Get process_job function template with database/framework integration."""
    db_code = ""
    framework_code = ""
    
    if database == "sqlite":
        db_code = """    # Example: Save to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (purchaser_id, input_data) VALUES (?, ?)",
        (identifier_from_purchaser, str(input_data))
    )
    conn.commit()
    conn.close()
"""
    elif database == "postgresql":
        db_code = """    # Example: Save to database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO jobs (purchaser_id, input_data) VALUES (%s, %s)",
        (identifier_from_purchaser, str(input_data))
    )
    conn.commit()
    return_db(conn)
"""
    elif database == "mongodb":
        db_code = """    # Example: Save to database
    db = get_db()
    db.jobs.insert_one({
        "purchaser_id": identifier_from_purchaser,
        "input_data": input_data
    })
"""
    elif database == "redis":
        db_code = """    # Example: Cache in Redis
    redis_client = get_redis()
    redis_client.set(f"job:{identifier_from_purchaser}", str(input_data))
"""
    
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
    Process a job - integrate with database and framework here
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing
    \"\"\"
{db_code}{framework_code}
    return {{"result": result, "purchaser": identifier_from_purchaser}}
"""


def _get_init_code(database: Optional[str]) -> str:
    """Get initialization code for database tables."""
    if database == "sqlite":
        return """    # Initialize database tables if needed
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchaser_id TEXT,
            input_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
    conn.close()
"""
    elif database == "postgresql":
        return """    # Initialize database tables if needed
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            purchaser_id TEXT,
            input_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    \"\"\")
    conn.commit()
    return_db(conn)
"""
    elif database == "mongodb":
        return """    # Database collections are created automatically in MongoDB
    # No initialization needed
"""
    elif database == "redis":
        return """    # Redis doesn't require table initialization
    # No initialization needed
"""
    return ""


def _get_requirements_txt(database: Optional[str], framework: Optional[str], additional_libs: List[str]) -> str:
    """Generate requirements.txt content."""
    requirements = [
        "masumi>=0.1.41",
        "python-dotenv>=0.19.0",
    ]
    
    # Database dependencies
    db_packages = {
        "sqlite": None,  # Built-in
        "postgresql": "psycopg2-binary>=2.9.0",
        "mongodb": "pymongo>=4.0.0",
        "redis": "redis>=4.0.0"
    }
    if database and database in db_packages and db_packages[database]:
        requirements.append(db_packages[database])
    
    # Framework dependencies
    if framework:
        requirements.append(f"{framework}>=0.1.0")
    
    # Additional library dependencies
    lib_packages = {
        "openai": "openai>=1.0.0",
        "anthropic": "anthropic>=0.7.0",
        "requests": "requests>=2.28.0",
        "pandas": "pandas>=2.0.0",
        "numpy": "numpy>=1.24.0"
    }
    for lib in additional_libs:
        if lib in lib_packages:
            requirements.append(lib_packages[lib])
    
    return "\n".join(requirements) + "\n"


def _get_env_template(database: Optional[str], framework: Optional[str], additional_libs: List[str]) -> str:
    """Generate .env file template."""
    env_lines = [
        "# Masumi Configuration",
        "# Get these values after registering your agent on the Masumi network",
        "AGENT_IDENTIFIER=your_agent_identifier_here",
        "PAYMENT_API_KEY=your_payment_api_key_here",
        "SELLER_VKEY=your_seller_vkey_here",
        "",
        "# Optional Masumi Settings",
        "PAYMENT_SERVICE_URL=https://payment.masumi.network/api/v1",
        "NETWORK=Preprod  # Options: Preprod or Mainnet",
        "",
    ]
    
    # Database environment variables
    if database == "sqlite":
        env_lines.extend([
            "# SQLite Configuration",
            "DB_PATH=agent.db",
            "",
        ])
    elif database == "postgresql":
        env_lines.extend([
            "# PostgreSQL Configuration",
            "DB_HOST=localhost",
            "DB_PORT=5432",
            "DB_NAME=masumi_agent",
            "DB_USER=postgres",
            "DB_PASSWORD=your_password_here",
            "",
        ])
    elif database == "mongodb":
        env_lines.extend([
            "# MongoDB Configuration",
            "MONGO_URI=mongodb://localhost:27017/",
            "DB_NAME=masumi_agent",
            "",
        ])
    elif database == "redis":
        env_lines.extend([
            "# Redis Configuration",
            "REDIS_HOST=localhost",
            "REDIS_PORT=6379",
            "REDIS_DB=0",
            "",
        ])
    
    # Framework/API keys
    if framework == "langchain" or "openai" in additional_libs:
        env_lines.extend([
            "# OpenAI Configuration (if using OpenAI)",
            "OPENAI_API_KEY=your_openai_api_key_here",
            "",
        ])
    
    if "anthropic" in additional_libs:
        env_lines.extend([
            "# Anthropic Configuration",
            "ANTHROPIC_API_KEY=your_anthropic_api_key_here",
            "",
        ])
    
    return "\n".join(env_lines)


def _get_readme_template(project_name: str, database: Optional[str], framework: Optional[str], additional_libs: List[str]) -> str:
    """Generate README.md content."""
    readme = f"""# {project_name}

A Masumi agent project generated with `masumi scaffold`.

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
"""
    
    if database:
        readme += f"""
### Database Configuration

This project uses **{database.capitalize()}** for data storage.
See `.env` file for database connection settings.
"""
    
    if framework:
        readme += f"""
### Framework

This project uses **{framework.capitalize()}** for agent orchestration.
"""
    
    if additional_libs:
        readme += f"""
### Additional Libraries

This project includes:
{chr(10).join(f"- {lib.capitalize()}" for lib in additional_libs)}
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
    database: Optional[str] = None,
    framework: Optional[str] = None,
    additional_libs: Optional[List[str]] = None,
    interactive: bool = True
) -> None:
    """
    Generate a scaffolded Masumi agent project with full structure.
    
    Args:
        project_name: Name of the project (default: "masumi-agent")
        output_dir: Output directory (default: project_name)
        database: Database choice ("sqlite", "postgresql", "mongodb", "redis", or None)
        framework: Framework choice ("langchain", "crewai", "autogen", or None)
        additional_libs: List of additional libraries ("openai", "anthropic", "requests", "pandas", "numpy")
        interactive: If True, prompt user for choices
    """
    if additional_libs is None:
        additional_libs = []
    
    if interactive:
        # Import interactive CLI utilities
        from .interactive_cli import (
            show_banner, select_option, multi_select, get_input,
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
        
        # Select database
        if database is None:
            database = select_option(
                "📦 Select a database",
                [
                    {
                        "key": "1",
                        "label": "None",
                        "description": "No database (default)",
                        "value": None
                    },
                    {
                        "key": "2",
                        "label": "SQLite",
                        "description": "File-based, no setup needed - perfect for development",
                        "value": "sqlite"
                    },
                    {
                        "key": "3",
                        "label": "PostgreSQL",
                        "description": "Production-ready relational database",
                        "value": "postgresql"
                    },
                    {
                        "key": "4",
                        "label": "MongoDB",
                        "description": "NoSQL document database",
                        "value": "mongodb"
                    },
                    {
                        "key": "5",
                        "label": "Redis",
                        "description": "In-memory data store for caching and sessions",
                        "value": "redis"
                    }
                ],
                default=0
            )
        
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
        
        # Select additional libraries
        if not additional_libs:
            additional_libs = multi_select(
                "📚 Select additional libraries (optional)",
                [
                    {
                        "key": "1",
                        "label": "OpenAI",
                        "description": "OpenAI API client for GPT models",
                        "value": "openai"
                    },
                    {
                        "key": "2",
                        "label": "Anthropic",
                        "description": "Anthropic API client for Claude models",
                        "value": "anthropic"
                    },
                    {
                        "key": "3",
                        "label": "Requests",
                        "description": "HTTP library for API calls",
                        "value": "requests"
                    },
                    {
                        "key": "4",
                        "label": "Pandas",
                        "description": "Data manipulation and analysis",
                        "value": "pandas"
                    },
                    {
                        "key": "5",
                        "label": "NumPy",
                        "description": "Numerical computing library",
                        "value": "numpy"
                    }
                ],
                default=[]
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
    _, db_imports, db_setup = _get_database_template(database)
    _, fw_imports, fw_setup = _get_framework_template(framework)
    process_job_code = _get_process_job_template(database, framework, additional_libs)
    init_code = _get_init_code(database)
    
    # Build imports section (collect all unique imports)
    imports_set = set()
    imports_set.add("import os")
    imports_set.add("from masumi import run, Config")
    imports_set.add("import logging")
    
    # Add database imports
    if db_imports:
        for imp in db_imports.split('\n'):
            if imp.strip():
                imports_set.add(imp.strip())
    
    # Add framework imports
    if fw_imports:
        for imp in fw_imports.split('\n'):
            if imp.strip():
                imports_set.add(imp.strip())
    
    # Add additional library imports
    for lib in additional_libs:
        _, lib_imports, _ = _get_additional_library_template(lib)
        if lib_imports:
            for line in lib_imports.split('\n'):
                line = line.strip()
                if line:
                    imports_set.add(line)
    
    # Convert to sorted list (standard library first, then third-party)
    imports_list = sorted(imports_set, key=lambda x: (not x.startswith('import '), x))
    
    # Build header comment
    header_parts = [f"{project_name} - Masumi Agent", "Generated by masumi scaffold"]
    if database:
        header_parts.append(f"Database: {database.capitalize()}")
    if framework:
        header_parts.append(f"Framework: {framework.capitalize()}")
    if additional_libs:
        header_parts.append(f"Libraries: {', '.join(additional_libs)}")
    
    # Build agent.py template (agent logic)
    agent_template_parts = [
        "#!/usr/bin/env python3",
        '"""',
        f"{project_name} - Agent Logic",
        "Generated by masumi scaffold",
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
    
    # Add database setup
    if db_setup:
        agent_template_parts.extend([
            db_setup,
            "",
        ])
    
    # Add framework setup
    if fw_setup:
        agent_template_parts.extend([
            fw_setup,
            "",
        ])
    
    # Add additional library setups
    for lib in additional_libs:
        _, _, lib_setup = _get_additional_library_template(lib)
        if lib_setup:
            agent_template_parts.extend([
                lib_setup,
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
        "Generated by masumi scaffold",
        "",
        "This is the entry point for your Masumi agent.",
        "Run this file to start the agent server.",
        '"""',
        "import os",
        "from masumi import run",
        "from agent import process_job",
    ]
    
    # Add database imports if needed for initialization
    if init_code:
        if database == "sqlite":
            main_template_parts.append("from agent import get_db")
        elif database == "postgresql":
            main_template_parts.append("from agent import get_db, return_db")
        elif database == "mongodb":
            main_template_parts.append("from agent import get_db")
        elif database == "redis":
            main_template_parts.append("from agent import get_redis")
    
    main_template_parts.extend([
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
    ])
    
    # Add initialization code if needed
    if init_code:
        # Add init code with proper indentation
        # The init_code already has proper indentation, we just need to add it
        init_lines = init_code.rstrip().split('\n')
        for line in init_lines:
            if line.strip():
                # The init_code already has 4 spaces, so we keep it as is
                main_template_parts.append(line)
            else:
                main_template_parts.append("")
    
    main_template_parts.extend([
        "    # Config and identifiers loaded from environment variables",
        "    # Default mode is API - use --standalone flag to run standalone",
        "    run(",
        "        start_job_handler=process_job,",
        "        input_schema_handler=INPUT_SCHEMA",
        "        # config, agent_identifier, network loaded from env vars automatically",
        "    )",
        ""
    ])
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
                (project_path / "requirements.txt").write_text(_get_requirements_txt(database, framework, additional_libs))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 4:
                (project_path / ".env.example").write_text(_get_env_template(database, framework, additional_libs))
                from .interactive_cli import print_success
                print_success(success_msg)
            elif i == 5:
                (project_path / "README.md").write_text(_get_readme_template(project_name, database, framework, additional_libs))
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
        (project_path / "requirements.txt").write_text(_get_requirements_txt(database, framework, additional_libs))
        (project_path / ".env.example").write_text(_get_env_template(database, framework, additional_libs))
        (project_path / "README.md").write_text(_get_readme_template(project_name, database, framework, additional_libs))
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
