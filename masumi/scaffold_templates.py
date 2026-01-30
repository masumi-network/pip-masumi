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
- [Masumi CLI Help](https://github.com/masumi-network/pip-masumi)

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
    """Generate agent.py template for LangChain scaffold with tool calling pattern."""
    return f'''#!/usr/bin/env python3
"""
{project_name} - LangChain Agent Logic
Generated by masumi init

This file contains your LangChain agent setup with tool calling and process_job function.
The process_job function integrates LangChain with Masumi's endpoint abstraction.

Implement your agentic behavior in the process_job function below.
"""

import os
import logging
import asyncio
from typing import Dict, Any
from langchain_core.exceptions import LangChainException
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tools.custom_tools import get_tools
from config.prompts import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _initialize_llm():
    """Initialize LLM - supports OpenAI, Groq, and Anthropic."""
    # Check for provider API keys (priority: OpenAI > Groq > Anthropic)
    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("TEMPERATURE", "0.7"))
        )
    elif os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq
        return ChatGroq(
            model_name=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=float(os.getenv("TEMPERATURE", "0.8"))
        )
    elif os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            temperature=float(os.getenv("TEMPERATURE", "0.7"))
        )
    else:
        raise ValueError(
            "No LLM API key found. Set OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY"
        )


def _initialize_agent():
    """Initialize LLM with tools bound for tool calling."""
    llm = _initialize_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
    return prompt | llm_with_tools, tools


# Initialize agent
try:
    agent_chain, agent_tools = _initialize_agent()
except Exception as e:
    logger.error(f"Agent initialization failed: {{e}}")
    agent_chain = None
    agent_tools = []


async def process_job(identifier_from_purchaser: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a job using LangChain Agent with tool calling - integrates with Masumi endpoints.
    
    Implement your agentic behavior here. This template provides a tool calling agent pattern
    that you can customize for your specific use case.
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA
    
    Returns:
        Result of processing (must be JSON-serializable)
    """
    # Validate agent is initialized
    if agent_chain is None:
        error_msg = "Agent chain not initialized. Check logs for initialization errors."
        logger.error(error_msg)
        return {{
            "status": "error",
            "error": error_msg,
            "identifier": identifier_from_purchaser
        }}
    
    if agent_chain is None:
        return {{
            "status": "error",
            "error": "Agent chain not initialized. Check logs for initialization errors.",
            "identifier": identifier_from_purchaser
        }}
    
    try:
        # Extract input from Masumi format
        # TODO: Customize this based on your INPUT_SCHEMA in main.py
        text = input_data.get("text", "")
        if not text:
            raise ValueError("text field is required in input_data")
        
        # Initialize messages and tool map
        messages = [HumanMessage(content=text)]
        tool_map = {{tool.name: tool for tool in agent_tools}}
        max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
        
        # Tool calling loop
        for iteration in range(max_iterations):
            # Invoke chain
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda msgs=messages: agent_chain.invoke({{"messages": msgs}})
            )
            messages.append(response)
            
            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    # Extract tool info
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {{}})
                        tool_id = tool_call.get("id", "")
                    else:
                        tool_name = getattr(tool_call, 'name', '')
                        tool_args = getattr(tool_call, 'args', {{}})
                        tool_id = getattr(tool_call, 'id', '')
                    
                    # Execute tool
                    if tool_name in tool_map:
                        try:
                            result = tool_map[tool_name].invoke(tool_args)
                            messages.append(ToolMessage(content=str(result), tool_call_id=tool_id or ""))
                        except Exception as e:
                            messages.append(ToolMessage(content=f"Error: {{str(e)}}", tool_call_id=tool_id or ""))
                    else:
                        messages.append(ToolMessage(content=f"Unknown tool: {{tool_name}}", tool_call_id=tool_id or ""))
            else:
                # No more tool calls, done
                break
        
        # Extract final response
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and msg.content.strip():
                output_text = msg.content
                break
        else:
            output_text = str(messages[-1]) if messages else "No response generated"
        
        return {{
            "status": "completed",
            "result": output_text,
            "identifier": identifier_from_purchaser
        }}
        
    except Exception as e:
        logger.error(f"Error processing job: {{e}}", exc_info=True)
        return {{
            "status": "error",
            "error": str(e),
            "identifier": identifier_from_purchaser
        }}
'''


def _get_langchain_tools_template() -> str:
    """Generate custom_tools.py template for LangChain scaffold."""
    return '''"""
Custom LangChain tools for your agent.

Add your custom tools here using the @tool decorator.
Tools allow your agent to interact with external systems, APIs, or perform calculations.
"""

from langchain_core.tools import tool


@tool
def example_tool(query: str) -> str:
    """
    Example custom tool - replace with your own tools.
    
    Args:
        query: Input query string
    
    Returns:
        Processed result
    
    Example: Add tools for web search, API calls, database queries, etc.
    """
    # Implement your tool logic here
    return f"Processed: {query}"


def get_tools():
    """
    Get list of custom tools for the agent.
    
    Returns:
        List of tool objects
    
    Examples:
        # Add web search tool:
        # from langchain_community.tools import DuckDuckGoSearchRun
        # search_tool = DuckDuckGoSearchRun()
        # return [search_tool, example_tool]
        
        # Add multiple tools:
        # from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
        # from langchain_community.utilities import WikipediaAPIWrapper
        # search = DuckDuckGoSearchRun()
        # wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        # return [search, wiki, example_tool]
        
        # Add custom API tool:
        # @tool
        # def fetch_weather(location: str) -> str:
        #     \"\"\"Get weather for a location.\"\"\"
        #     # Your API call here
        #     return weather_data
        # return [fetch_weather, example_tool]
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
You process user requests and return helpful responses.
Use tools when needed to gather information or perform actions.

Guidelines:
- Be clear and concise in your responses
- Use tools when you need current information, calculations, or external data
- Explain your reasoning when using tools
- Provide accurate and helpful answers"""

# Optional: Customize user prompt template if needed
# This template is used when formatting user messages
USER_PROMPT_TEMPLATE = """{input}"""
'''


def _get_langchain_requirements() -> str:
    """Generate requirements.txt for LangChain scaffold with complete dependencies."""
    requirements = [
        "# Core dependencies",
        "masumi",
        "python-dotenv",
        "",
        "# LangChain core",
        "langchain>=1.0.0,<2.0.0",
        "langchain-core>=1.0.0",
        "",
        "# LLM Providers (choose one or more)",
        "# OpenAI (default)",
        "langchain-openai>=0.1.0",
        "",
        "# Groq (fast, free-tier alternative)",
        "# langchain-groq>=1.0.0",
        "",
        "# Anthropic",
        "# langchain-anthropic>=0.1.0",
        "",
        "# Tools and utilities",
        "langchain-community>=0.0.20",
        "",
        "# Optional: DuckDuckGo search",
        "# ddgs>=0.1.0  # Uncomment if you want to use DuckDuckGo search",
        "",
        "# Optional: Other search providers",
        "# tavily-python>=0.3.0  # For Tavily search (uncomment to use)",
        "",
        "# Optional: Testing",
        "# pytest>=7.0.0",
        "# pytest-asyncio>=0.18.0",
    ]
    return "\n".join(requirements) + "\n"


def _get_langchain_env_template() -> str:
    """Generate .env.example for LangChain scaffold with multiple provider support."""
    base_env = _get_env_template(None, [])
    langchain_env = [
        "",
        "# ============================================",
        "# LLM CONFIGURATION: LangChain",
        "# ============================================",
        "# Choose ONE provider by setting its API key:",
        "# Priority: OpenAI > Groq > Anthropic",
        "",
        "# OpenAI (default) - Get key from: https://platform.openai.com/api-keys",
        "OPENAI_API_KEY=your_openai_api_key_here",
        "#OPENAI_MODEL=gpt-3.5-turbo  # Optional: specify model",
        "",
        "# Groq (fast, free-tier alternative) - Get key from: https://console.groq.com/keys",
        "#GROQ_API_KEY=your_groq_api_key_here",
        "#GROQ_MODEL=llama-3.3-70b-versatile  # Optional: specify model",
        "",
        "# Anthropic - Get key from: https://console.anthropic.com/",
        "#ANTHROPIC_API_KEY=your_anthropic_api_key_here",
        "#ANTHROPIC_MODEL=claude-3-sonnet-20240229  # Optional: specify model",
        "",
        "# ============================================",
        "# AGENT CONFIGURATION",
        "# ============================================",
        "# Temperature (0.0-1.0): Controls randomness (default: 0.7 for OpenAI/Anthropic, 0.8 for Groq)",
        "#TEMPERATURE=0.7",
        "",
        "# Max iterations for tool calling loop (default: 5)",
        "#MAX_ITERATIONS=5",
        "",
        "# Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)",
        "#LOG_LEVEL=INFO",
        "",
        "# ============================================",
        "# OPTIONAL: LangSmith Tracing (for debugging)",
        "# ============================================",
        "#LANGCHAIN_TRACING_V2=false",
        "#LANGCHAIN_API_KEY=your_langsmith_api_key",
        "",
    ]
    return base_env + "\n".join(langchain_env)


def _get_langchain_readme_template(project_name: str) -> str:
    """Generate README.md for LangChain scaffold with comprehensive documentation."""
    return f"""# {project_name}

A Masumi agent project with LangChain integration and tool calling, generated with `masumi init`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - Set ONE LLM API key: OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY
   # - For API mode: AGENT_IDENTIFIER, PAYMENT_API_KEY, SELLER_VKEY (Masumi)
   ```

3. **Implement your agent logic:**
   - Edit `agent.py` to implement your `process_job()` function
   - Add custom tools in `tools/custom_tools.py`
   - Customize prompts in `config/prompts.py`

4. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   
   # Standalone mode - test locally without API server
   masumi run main.py --standalone --input '{{"text": "Hello"}}'
   ```

## Configuration

### Required Environment Variables

**For Standalone Testing (LLM only):**
- **ONE** of the following LLM API keys:
  - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
  - `GROQ_API_KEY` - Get from https://console.groq.com/keys (free tier available)
  - `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

**For API Mode (Production):**
- All Masumi variables:
  - `AGENT_IDENTIFIER`: Your agent ID (get after registering on Masumi network)
  - `PAYMENT_API_KEY`: Your payment API key
  - `SELLER_VKEY`: Your seller wallet verification key
- **ONE** LLM API key (as above)

### Optional Environment Variables

**LLM Configuration:**
- `OPENAI_MODEL`: Model name (default: gpt-3.5-turbo)
- `GROQ_MODEL`: Model name (default: llama-3.3-70b-versatile)
- `ANTHROPIC_MODEL`: Model name (default: claude-3-sonnet-20240229)
- `TEMPERATURE`: 0.0-1.0 (default: 0.7 for OpenAI/Anthropic, 0.8 for Groq)

**Agent Configuration:**
- `MAX_ITERATIONS`: Max tool calling iterations (default: 5)

**Masumi Configuration:**
- `PAYMENT_SERVICE_URL`: Payment service URL (must end with /api/v1)
- `NETWORK`: 'Preprod' or 'Mainnet' (default: 'Preprod')
- `PORT`: Port to bind to (default: 8080)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Project Structure

```
.
├── main.py              # Entry point - Masumi.run() integration
├── agent.py             # LangChain tool calling agent + process_job
├── tools/               # Custom LangChain tools
│   ├── __init__.py
│   └── custom_tools.py  # Custom tool definitions
├── config/              # Configuration
│   └── prompts.py       # System prompts
├── requirements.txt     # Dependencies (masumi + langchain)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## LangChain Integration

### Tool Calling Pattern

This scaffold uses the **tool calling agent pattern** (recommended):
- LLM decides when to use tools based on the request
- Manual loop for tool execution with full control
- Full visibility into tool calls and responses
- Works across all providers (OpenAI, Groq, Anthropic)
- Supports multi-step tool calling (agent can use tools multiple times)

**How it works:**
1. User sends input → `process_job()` receives it
2. Agent analyzes the request and decides: respond directly OR use tools
3. If tools needed: executes tool(s), gets results, processes response
4. Agent can iterate: use tools again if needed (up to `MAX_ITERATIONS`)
5. Returns final result with all tool call results incorporated

**Benefits:**
- Transparent: See exactly what tools are called and when
- Flexible: Easy to add custom tools or modify behavior
- Reliable: Handles errors gracefully with retry logic
- Efficient: Only calls tools when necessary

### Customizing the Agent

1. **Modify `agent.py`:**
   - Change the `process_job()` function logic to match your use case
   - Adjust tool calling loop behavior (e.g., change `MAX_ITERATIONS`)
   - Add custom validation or preprocessing of input data
   - Customize the return format to include metadata or structured data
   - Add custom error handling for your specific domain

2. **Add custom tools in `tools/custom_tools.py`:**
   ```python
   from langchain_core.tools import tool
   
   @tool
   def my_custom_tool(input: str) -> str:
       \"\"\"Tool description for the LLM - be specific about what it does.\"\"\"
       # Your tool logic here
       # Can call APIs, databases, perform calculations, etc.
       return result
   
   # Add to get_tools() function
   def get_tools():
       return [my_custom_tool]
   ```
   
   **Tool Tips:**
   - Write clear docstrings - the LLM uses these to decide when to call tools
   - Tools should be idempotent when possible
   - Handle errors gracefully and return informative error messages
   - Use type hints for better tool schema generation

3. **Update prompts in `config/prompts.py`:**
   - Customize `SYSTEM_PROMPT` to change agent behavior and personality
   - Modify how the agent uses tools (when to use, how to interpret results)
   - Add domain-specific instructions or constraints
   - Guide the agent's response format and style

### Using Different LLM Providers

The scaffold automatically detects which provider to use based on environment variables (priority: OpenAI > Groq > Anthropic).

**To use Groq (fast, free-tier):**
```bash
# Install Groq package
pip install langchain-groq

# Set in .env
GROQ_API_KEY=your_groq_api_key_here
# Optionally: GROQ_MODEL=llama-3.3-70b-versatile
```

**To use Anthropic:**
```bash
# Install Anthropic package
pip install langchain-anthropic

# Set in .env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Optionally: ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**To use OpenAI (default):**
```bash
# Already installed
# Set in .env
OPENAI_API_KEY=your_openai_api_key_here
# Optionally: OPENAI_MODEL=gpt-3.5-turbo
```

## Masumi Integration

The `process_job()` function in `agent.py` integrates LangChain with Masumi's endpoint abstraction:

- **Input:** `{{"text": "Your input here"}}` (matches INPUT_SCHEMA)
- **Process:** LangChain agent with tool calling
- **Output:** `{{"status": "completed", "result": "Your result here"}}`

This allows your LangChain agent to work seamlessly with Masumi's payment and API infrastructure.

## Development

### Running Locally (Standalone Mode)

Perfect for testing without Masumi setup:

```bash
# Test the agent
masumi run main.py --standalone --input '{{"text": "Your input here"}}'
```

### Running in API Mode (Production)

Requires Masumi credentials:

```bash
# Run the server
masumi run
# Server starts on http://0.0.0.0:8080
```

### Debugging

Enable debug logging:
```bash
# In .env file
LOG_LEVEL=DEBUG
```

This shows:
- Tool calls and results
- Agent decisions
- Full request/response flow

## Troubleshooting

### "No LLM API key found"
- Set ONE of: `OPENAI_API_KEY`, `GROQ_API_KEY`, or `ANTHROPIC_API_KEY` in `.env`

### "Agent chain not initialized"
- Check logs for initialization errors
- Verify API key is correct
- Ensure provider package is installed (`langchain-openai`, `langchain-groq`, etc.)

### Tool calling errors (Groq)
- Groq sometimes has tool format issues - retry logic handles this automatically
- If persistent, try a different model or provider

### Payment service errors
- Verify `PAYMENT_SERVICE_URL` ends with `/api/v1`
- Ensure URL matches your payment service instance (not generic default)
- Check that `PAYMENT_API_KEY` matches the service URL

### Port already in use
```bash
# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use different port
PORT=8081 masumi run
```

## Provider Comparison

| Provider | Speed | Cost | Best For |
|----------|-------|------|----------|
| **Groq** | ⚡ Very Fast | 🆓 Free tier | Fast responses, testing |
| **OpenAI** | ⚡ Fast | 💰 Paid | Production, reliability |
| **Anthropic** | ⚡ Fast | 💰 Paid | Quality, safety |

**Recommendation:** Start with Groq for testing (free), switch to OpenAI/Anthropic for production.

## Next Steps

1. 🔧 **Implement `process_job()`:** Edit `agent.py` to add your agent logic
   - Update input extraction to match your `INPUT_SCHEMA`
   - Customize the tool calling loop if needed
   - Adjust return format for your use case

2. 🛠️ **Add tools:** Create custom tools in `tools/custom_tools.py`
   - Use `@tool` decorator for simple functions
   - Import tools from `langchain_community` for common use cases
   - Update `get_tools()` to return your tools

3. 📝 **Customize prompts:** Update `config/prompts.py` for your use case
   - Modify `SYSTEM_PROMPT` to guide agent behavior
   - Add domain-specific instructions

4. 🧪 **Test locally:** Use standalone mode to test your agent
   ```bash
   masumi run main.py --standalone --input '{{"text": "Your input here"}}'
   ```

5. 🚀 **Deploy:** Set up Masumi credentials and deploy
   - Register on Masumi network
   - Set environment variables
   - Run in API mode: `masumi run`

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [LangChain Documentation](https://python.langchain.com)
- [LangChain Tool Calling Guide](https://python.langchain.com/docs/modules/tools/)
- [Masumi CLI Help](https://github.com/masumi-network/pip-masumi)

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
from crewai import Agent, Task, Crew, Process, LLM

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _create_llm() -> LLM:
    """Create LLM from env (Groq, OpenAI, or Anthropic). Fails with clear error if no key set."""
    if os.getenv("GROQ_API_KEY"):
        return LLM(model="groq/llama-3.1-8b-instant")
    if os.getenv("OPENAI_API_KEY"):
        return LLM(model="gpt-4")
    if os.getenv("ANTHROPIC_API_KEY"):
        return LLM(model="claude-3-opus-20240229")
    raise ValueError(
        "No LLM API key found. Set GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY"
    )


def load_agents_from_yaml(config_path: Path, llm: LLM) -> list:
    """
    Load agent definitions from YAML file.
    
    Args:
        config_path: Path to agents.yaml file
        llm: LLM instance for all agents
    
    Returns:
        List of Agent objects
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Handle empty files or files with only comments (yaml.safe_load returns None)
    if config is None:
        config = {{}}
    
    agents = []
    for agent_config in config.get('agents', []):
        agent = Agent(
            role=agent_config.get('role', ''),
            goal=agent_config.get('goal', ''),
            backstory=agent_config.get('backstory', ''),
            llm=llm,
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
    
    # Handle empty files or files with only comments (yaml.safe_load returns None)
    if config is None:
        config = {{}}
    
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
    
    llm = _create_llm()
    agents = load_agents_from_yaml(agents_path, llm)
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
        Masumi-compatible dict: success {{"status": "completed", "result": "...", "identifier": "..."}}
        or error {{"status": "error", "error": "...", "identifier": "..."}}
    """
    logger.info(f"Processing job for purchaser: {{identifier_from_purchaser}}")
    logger.info(f"Input data: {{input_data}}")
    
    topic = input_data.get("topic", "")
    if not topic:
        # Required input missing; return error dict (Masumi expects dict, not raise)
        return {{
            "status": "error",
            "error": "Topic field is required",
            "identifier": identifier_from_purchaser
        }}
    
    try:
        crew = create_crew()
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
        # Masumi-compatible result dict (JSON-serializable)
        return {{
            "status": "completed",
            "result": output_text,
            "identifier": identifier_from_purchaser
        }}
    except Exception as e:
        logger.error(f"Error in CrewAI processing: {{e}}")
        return {{
            "status": "error",
            "error": str(e),
            "identifier": identifier_from_purchaser
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
        "langgraph>=0.3.1",
        "litellm",
        "pyyaml>=6.0",
        "",
        "# Optional LLM providers (install as needed):",
        "# groq          # For Groq models",
        "# openai        # For OpenAI (often included with crewai)",
        "# anthropic     # For Anthropic models",
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
        "# Choose ONE provider (set the corresponding API key):",
        "",
        "# Option 1: Groq (recommended - fast, cost-effective)",
        "GROQ_API_KEY=",
        "",
        "# Option 2: OpenAI",
        "#OPENAI_API_KEY=your_openai_api_key_here",
        "",
        "# Option 3: Anthropic",
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

**Python:** 3.10–3.13 recommended (CrewAI/LangGraph compatibility).

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Requirements include `langgraph` and `litellm` (needed for CrewAI).

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values:
   # - Set ONE LLM API key: OPENAI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY
   # - For API mode: AGENT_IDENTIFIER, PAYMENT_API_KEY, SELLER_VKEY 
   ```

3. **Implement your crew logic:**
   - Edit `config/agents.yaml` to define your agents (role, goal, backstory)
   - Edit `config/tasks.yaml` to define your tasks (description, expected_output)
   - Customize `crew.py` if needed (process type, tools, knowledge base)
   - Add custom tools in `tools/custom_tools.py` if needed

4. **Run the agent:**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   
   # Standalone mode - test locally without API server
   masumi run main.py --standalone --input '{{"topic": "...your topic..."}}'
   ```

## Configuration

### Required Environment Variables

**For Standalone Testing (LLM only):**
- **ONE** of the following LLM API keys:
  - `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
  - `GROQ_API_KEY` - Get from https://console.groq.com/keys (free tier available)
  - `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/

**For API Mode:**
- All Masumi variables:
  - `AGENT_IDENTIFIER`: Your agent ID (get after registering on Masumi network)
  - `PAYMENT_API_KEY`: Your payment API key
  - `SELLER_VKEY`: Your seller wallet verification key
- **ONE** LLM API key (as above)

### Optional Environment Variables

**LLM Configuration:**
- `OPENAI_MODEL`: Model name (default: gpt-3.5-turbo)
- `GROQ_MODEL`: Model name (default: llama-3.3-70b-versatile)
- `ANTHROPIC_MODEL`: Model name (default: claude-3-sonnet-20240229)
- `TEMPERATURE`: 0.0-1.0 (default: 0.7 for OpenAI/Anthropic, 0.8 for Groq)

### Optional Environment Variables

**Masumi Configuration:**
- `PAYMENT_SERVICE_URL`: Payment service URL (must end with /api/v1)
- `NETWORK`: 'Preprod' or 'Mainnet' (default: 'Preprod')
- `PORT`: Port to bind to (default: 8080)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)

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
├── requirements.txt     # Dependencies (masumi, crewai, langgraph, litellm)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## CrewAI Integration

### How CrewAI Works

CrewAI uses a **multi-agent crew pattern**:
- **Agents** are specialized workers with roles, goals, and backstories
- **Tasks** are assigned to specific agents and executed sequentially
- **Crew** orchestrates the workflow, managing agent collaboration
- Agents can use **tools** to perform actions (search, API calls, etc.)
- Tasks can reference outputs from previous tasks

**How it works:**
1. User sends input → `process_job()` receives it
2. Input data is extracted and used to format task descriptions (using placeholders like `{{topic}}`)
3. Crew kicks off with `crew.kickoff()`
4. Agents execute tasks sequentially, each agent working on assigned tasks
5. Each agent can use tools to gather information or perform actions
6. Task outputs are passed to subsequent tasks
7. Final result is returned with all agent outputs incorporated

**Benefits:**
- **Specialized agents:** Each agent has a clear role and expertise
- **Sequential workflow:** Tasks execute in order, building on previous work
- **Tool integration:** Agents can use tools for real-world actions
- **YAML configuration:** Easy to modify agents and tasks without code changes
- **Scalable:** Add more agents and tasks as your needs grow

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
- `description`: What the task should do (can use `{{topic}}` or other placeholders)
- `expected_output`: What the task should produce
- `agent`: Which agent should handle this task (must match role in agents.yaml)

Tasks execute sequentially, so later tasks can use outputs from earlier tasks.

### Customizing the Crew

Modify `crew.py` to:
- Change the process type (sequential, hierarchical, etc.)
- Add custom tools to agents
- Configure different LLM providers
- Add knowledge base integration for RAG
- Customize agent behavior and tool assignments

**Process Types:**
- `Process.sequential`: Tasks execute one after another (default)
- `Process.hierarchical`: Manager agent coordinates other agents
- Custom processes: Define your own workflow logic

### Adding Custom Tools

1. Create tools in `tools/custom_tools.py`:
   ```python
   from crewai_tools import tool
   
   @tool("My Custom Tool")
   def my_tool(input: str) -> str:
       \"\"\"Tool description for the agent - be specific about what it does.\"\"\"
       # Your tool logic here
       # Can call APIs, databases, perform calculations, etc.
       return result
   ```

2. Import and add to agents in `crew.py`:
   ```python
   from tools.custom_tools import my_tool
   
   agent = Agent(
       role="...",
       tools=[my_tool]  # Add tools here
   )
   ```
   
   **Tool Tips:**
   - Write clear docstrings - agents use these to decide when to use tools
   - Tools should be idempotent when possible
   - Handle errors gracefully and return informative error messages
   - Use type hints for better tool schema generation
   - Import tools from `crewai_tools` for common use cases (web search, file operations, etc.)

### Using Different LLM Providers

The scaffold automatically detects which provider to use based on environment variables (priority: OpenAI > Groq > Anthropic).

**To use Groq (fast, free-tier):**
```bash
# Install Groq package (if not already included)
pip install groq

# Set in .env
GROQ_API_KEY=your_groq_api_key_here
# Optionally: GROQ_MODEL=llama-3.3-70b-versatile
```

**To use Anthropic:**
```bash
# Install Anthropic package (if not already included)
pip install anthropic

# Set in .env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# Optionally: ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**To use OpenAI (default):**
```bash
# Already installed
# Set in .env
OPENAI_API_KEY=your_openai_api_key_here
# Optionally: OPENAI_MODEL=gpt-3.5-turbo
```

CrewAI will automatically use the available provider through LiteLLM.

## Masumi Integration

The `process_job()` function in `crew.py` integrates CrewAI with Masumi's endpoint abstraction:

- **Input:** `{{"topic": "Your topic here"}}` (matches INPUT_SCHEMA)
- **Process:** CrewAI crew executes tasks sequentially with assigned agents
- **Output:** `{{"status": "completed", "result": "Your result here"}}`

**How it works:**
1. `process_job()` receives Masumi input format
2. Extracts input data and formats task descriptions with placeholders
3. Crew kicks off with `crew.kickoff()`
4. Agents execute tasks in sequence
5. Final result is returned in Masumi-compatible format

This allows your CrewAI crew to work seamlessly with Masumi's payment and API infrastructure.

## Development

### Running Locally (Standalone Mode)

Perfect for testing without Masumi setup:

```bash
# Test the crew
masumi run main.py --standalone --input '{{"topic": "...your topic..."}}'
```

This runs the crew directly without starting the API server, useful for:
- Testing agent behavior
- Debugging task execution
- Validating YAML configurations
- Iterating on prompts and tools

### Running in API Mode (Production)

Requires Masumi credentials:

```bash
# Run the server
masumi run
# Server starts on http://0.0.0.0:8080
```


## Troubleshooting

### "No LLM API key found"
- Set ONE of: `OPENAI_API_KEY`, `GROQ_API_KEY`, or `ANTHROPIC_API_KEY` in `.env`

### "Agent 'X' not found for task"
- Check that agent role names in `tasks.yaml` exactly match role names in `agents.yaml`
- Verify YAML syntax is correct (indentation, quotes, etc.)

### "YAML parsing error"
- Check YAML syntax in `config/agents.yaml` and `config/tasks.yaml`
- Ensure proper indentation (2 spaces, not tabs)
- Verify all required fields are present (role, goal, backstory for agents; description, expected_output, agent for tasks)

### Crew execution errors
- Check logs for specific agent or task failures
- Verify LLM API key is correct and has sufficient credits
- Ensure input data format matches expected schema
- Check that task placeholders (like `{{topic}}`) match input data keys

### Payment service errors
- Verify `PAYMENT_SERVICE_URL` ends with `/api/v1`
- Ensure URL matches your payment service instance (not generic default)
- Check that `PAYMENT_API_KEY` matches the service URL

### Port already in use
```bash
# Find and kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use different port
PORT=8081 masumi run
```

### CrewAI/LangGraph compatibility issues
- Ensure Python version is 3.10-3.13 (CrewAI requirement)
- Update dependencies: `pip install --upgrade crewai langgraph litellm`
- Check CrewAI documentation for breaking changes in your version

## Provider Comparison

| Provider | Speed | Cost | Best For |
|----------|-------|------|----------|
| **Groq** | ⚡ Very Fast | 🆓 Free tier | Fast responses, testing |
| **OpenAI** | ⚡ Fast | 💰 Paid | Production, reliability |
| **Anthropic** | ⚡ Fast | 💰 Paid | Quality, safety |

**Recommendation:** Start with Groq for testing (free), switch to OpenAI/Anthropic for production.

## Next Steps

1. 🔧 **Configure agents:** Edit `config/agents.yaml` to define your specialized agents
   - Add roles that match your use case
   - Write clear goals and detailed backstories
   - Set `allow_delegation` appropriately

2. 📋 **Define tasks:** Edit `config/tasks.yaml` to create your workflow
   - Use placeholders like `{{topic}}` for dynamic content
   - Assign tasks to appropriate agents
   - Order tasks logically (later tasks can use earlier outputs)

3. 🛠️ **Add tools:** Create custom tools in `tools/custom_tools.py` if needed
   - Use `@tool` decorator from `crewai_tools`
   - Import tools from `crewai_tools` for common use cases
   - Add tools to agents in `crew.py`

4. ⚙️ **Customize crew:** Modify `crew.py` for advanced configurations
   - Change process type (sequential, hierarchical, etc.)
   - Add knowledge base integration for RAG
   - Configure custom LLM settings

5. 🧪 **Test locally:** Use standalone mode to test your crew
   ```bash
   masumi run main.py --standalone --input '{{"topic": "...your topic..."}}'
   ```

6. 🚀 **Deploy:** Set up Masumi credentials and deploy
   - Register on Masumi network
   - Set environment variables
   - Run in API mode: `masumi run`

## Documentation

- [Masumi Documentation](https://docs.masumi.network)
- [CrewAI Documentation](https://docs.crewai.com)
- [CrewAI Agents Guide](https://docs.crewai.com/concepts/agents)
- [CrewAI Tasks Guide](https://docs.crewai.com/concepts/tasks)
- [CrewAI Tools Guide](https://docs.crewai.com/concepts/tools)
- [Masumi CLI Help](https://github.com/masumi-network/pip-masumi)

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
                (config_dir / "__init__.py").write_text("")
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
        (config_dir / "__init__.py").write_text("")
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
        "# Load .env from project directory (works even when cwd differs)",
        "from pathlib import Path",
        "from dotenv import load_dotenv",
        "load_dotenv(Path(__file__).resolve().parent / \".env\")",
        "",
        "from masumi import run",
        "from crew import process_job",
        "",
        "# Input schema (MIP-003); returned by /input_schema endpoint",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "topic",',
        '            "type": "text",',
        '            "name": "Topic",',
        '            "description": "Topic to research and summarize (e.g. \'Artificial Intelligence\', \'Cardano\')"',
        '        }',
        '    ]',
        '}',
        "",
        "# MIP-003 /demo: example input and output for discovery",
        "def demo_handler() -> dict:",
        "    return {",
        '        "input": {"topic": "Artificial Intelligence"},',
        '        "output": {"result": "Example summary output..."}',
        "    }",
        "",
        "if __name__ == \"__main__\":",
        "    run(",
        "        start_job_handler=process_job,",
        "        input_schema_handler=INPUT_SCHEMA,",
        "        demo_handler=demo_handler,",
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
    
    # Set output directory - use provided value or default to project_name
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
