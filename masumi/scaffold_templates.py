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

This is a working Q&A assistant example that you can test immediately and then modify
to build your own agent.
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

# Configure structured logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)


def _initialize_llm():
    """
    Initialize and validate LLM configuration.
    Supports OpenAI, Groq, and Anthropic providers based on environment variables.
    """
    # Check for provider API keys (priority: OpenAI > Groq > Anthropic)
    openai_key = os.getenv("OPENAI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_key:
        from langchain_openai import ChatOpenAI
        model_name = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        logger.info(f"Initializing OpenAI LLM: model={{model_name}}, temperature={{temperature}}")
        return ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            openai_api_key=openai_key
        )
    elif groq_key:
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        temperature = float(os.getenv("TEMPERATURE", "0.8"))
        logger.info(f"Initializing Groq LLM: model={{model_name}}, temperature={{temperature}}")
        return ChatGroq(
            model_name=model_name,
            temperature=temperature,
            groq_api_key=groq_key
        )
    elif anthropic_key:
        from langchain_anthropic import ChatAnthropic
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        temperature = float(os.getenv("TEMPERATURE", "0.7"))
        logger.info(f"Initializing Anthropic LLM: model={{model_name}}, temperature={{temperature}}")
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=anthropic_key
        )
    else:
        raise ValueError(
            "No LLM API key found. Please set one of the following environment variables:\\n"
            "  - OPENAI_API_KEY (for OpenAI)\\n"
            "  - GROQ_API_KEY (for Groq)\\n"
            "  - ANTHROPIC_API_KEY (for Anthropic)\\n"
            "Get API keys from:\\n"
            "  - OpenAI: https://platform.openai.com/api-keys\\n"
            "  - Groq: https://console.groq.com/keys\\n"
            "  - Anthropic: https://console.anthropic.com/"
        )


def _initialize_agent():
    """Initialize LLM with tools bound for tool calling."""
    try:
        llm = _initialize_llm()
        tools = get_tools()
        
        logger.info(f"Loaded {{len(tools)}} tools: {{[tool.name for tool in tools]}}")
        
        # Bind tools to the model for tool calling
        llm_with_tools = llm.bind_tools(tools)
        
        # Create prompt template with system message
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create chain
        chain = prompt | llm_with_tools
        
        logger.info("Agent initialized successfully")
        return chain, tools
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {{e}}", exc_info=True)
        raise


# Initialize agent
try:
    agent_chain, agent_tools = _initialize_agent()
except Exception as e:
    logger.error(f"Agent initialization failed: {{e}}")
    agent_chain = None
    agent_tools = []


def _validate_input_data(input_data: Dict[str, Any]) -> str:
    """
    Validate and extract input data.
    
    Args:
        input_data: Input data dictionary
    
    Returns:
        Question string
    """
    if not isinstance(input_data, dict):
        raise ValueError("input_data must be a dictionary")
    
    question = input_data.get("question", "").strip()
    if not question:
        raise ValueError("question field is required in input_data")
    
    return question


def _handle_provider_error(error: Exception, provider: str) -> Dict[str, str]:
    """
    Handle provider-specific errors with helpful messages.
    
    Args:
        error: The exception that occurred
        provider: Provider name (openai, groq, anthropic)
    
    Returns:
        Dictionary with error_type and error message
    """
    error_str = str(error)
    
    if provider == "groq":
        if "tool_use_failed" in error_str or "failed_generation" in error_str.lower():
            return {{
                "error_type": "tool_call_error",
                "error": (
                    "Groq API tool calling error. The model attempted to use a tool but the format was incorrect. "
                    "This may be a temporary issue. Try again or adjust your query."
                )
            }}
        elif "model_decommissioned" in error_str or "decommissioned" in error_str.lower():
            return {{
                "error_type": "model_decommissioned",
                "error": (
                    "The selected Groq model has been decommissioned. "
                    "Please update GROQ_MODEL environment variable to a current model. "
                    "Visit https://console.groq.com/docs/models for available models."
                )
            }}
        elif "429" in error_str or "RateLimitError" in str(type(error).__name__):
            if "insufficient_quota" in error_str or "quota" in error_str.lower():
                return {{
                    "error_type": "quota_exceeded",
                    "error": (
                        "Groq API quota exceeded. Please check your account limits. "
                        "Visit https://console.groq.com/ to manage your account."
                    )
                }}
            else:
                return {{
                    "error_type": "rate_limit",
                    "error": (
                        "Groq API rate limit exceeded. The request will be retried automatically. "
                        "If this persists, please wait a moment and try again."
                    )
                }}
    
    elif provider == "openai":
        if "insufficient_quota" in error_str or "quota" in error_str.lower():
            return {{
                "error_type": "quota_exceeded",
                "error": (
                    "OpenAI API quota exceeded. Please check your billing at platform.openai.com"
                )
            }}
        elif "rate_limit" in error_str.lower():
            return {{
                "error_type": "rate_limit",
                "error": (
                    "OpenAI API rate limit exceeded. Wait a moment and retry."
                )
            }}
    
    elif provider == "anthropic":
        if "429" in error_str:
            return {{
                "error_type": "rate_limit",
                "error": (
                    "Anthropic API rate limit exceeded. Wait a moment and retry."
                )
            }}
    
    return {{
        "error_type": "error",
        "error": f"Unexpected error: {{error_str}}"
    }}


async def process_job(identifier_from_purchaser: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a job using LangChain Agent with tool calling - integrates with Masumi endpoints.
    
    This is a working Q&A assistant example that:
    - Answers questions directly if knowledge is sufficient
    - Uses web search tool when current information is needed
    - Returns helpful, accurate answers
    
    Args:
        identifier_from_purchaser: Identifier from the purchaser
        input_data: Input data matching INPUT_SCHEMA (should contain "question" field)
    
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
    
    logger.info(f"Processing Q&A job for purchaser: {{identifier_from_purchaser}}")
    logger.debug(f"Input data: {{input_data}}")
    
    # Detect provider for error handling (must be before try block)
    provider = "openai" if os.getenv("OPENAI_API_KEY") else ("groq" if os.getenv("GROQ_API_KEY") else "anthropic")
    
    try:
        # Validate and extract input
        question = _validate_input_data(input_data)
        logger.info(f"Question: {{question}}")
        
        # Create tool lookup
        tool_map = {{tool.name: tool for tool in agent_tools}}
        
        # Initialize messages
        messages = [HumanMessage(content=question)]
        max_iterations = int(os.getenv("MAX_ITERATIONS", "5"))
        tool_calls_count = 0
        
        # Run agent loop with tool calling
        for iteration in range(max_iterations):
            try:
                # Invoke chain
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda msgs=messages: agent_chain.invoke({{"messages": msgs}})
                )
            except Exception as invoke_error:
                # Handle provider-specific tool calling errors
                error_str = str(invoke_error)
                
                if "tool_use_failed" in error_str or "failed_generation" in error_str.lower():
                    logger.warning(f"Tool calling error on iteration {{iteration + 1}}: {{error_str[:200]}}")
                    
                    # Retry on first iteration
                    if iteration == 0:
                        logger.info("Retrying with same query...")
                        await asyncio.sleep(0.5)  # Brief delay before retry
                        continue
                    else:
                        logger.error(f"Tool calling failed after retry: {{invoke_error}}")
                        raise
                else:
                    # Re-raise other errors
                    raise
            
            # If we got here, the invoke was successful
            messages.append(response)
            
            # Check if model wants to call tools
            tool_calls = None
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = response.tool_calls
            
            if tool_calls:
                logger.debug(f"Iteration {{iteration + 1}}: Model requested {{len(tool_calls)}} tool calls")
                
                # Execute tool calls
                for tool_call in tool_calls:
                    # Increment counter for each individual tool call to ensure unique IDs
                    tool_calls_count += 1
                    
                    # Handle different tool call formats
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {{}})
                        tool_id = tool_call.get("id", "")
                    elif hasattr(tool_call, 'name'):
                        tool_name = getattr(tool_call, 'name', '')
                        tool_args = getattr(tool_call, 'args', {{}})
                        tool_id = getattr(tool_call, 'id', '')
                    else:
                        logger.warning(f"Unexpected tool call format: {{tool_call}}")
                        continue
                    
                    logger.debug(f"Executing tool: {{tool_name}} with args: {{tool_args}}")
                    
                    if tool_name in tool_map:
                        try:
                            tool_result = tool_map[tool_name].invoke(tool_args)
                            messages.append(
                                ToolMessage(
                                    content=str(tool_result),
                                    tool_call_id=tool_id if tool_id else f"call_{{tool_calls_count}}"
                                )
                            )
                            logger.debug(f"Tool {{tool_name}} executed successfully")
                        except Exception as tool_error:
                            logger.error(f"Error executing tool {{tool_name}}: {{tool_error}}", exc_info=True)
                            messages.append(
                                ToolMessage(
                                    content=f"Error: {{str(tool_error)}}",
                                    tool_call_id=tool_id if tool_id else f"call_{{tool_calls_count}}"
                                )
                            )
                    else:
                        logger.warning(f"Unknown tool: {{tool_name}}. Available tools: {{list(tool_map.keys())}}")
                        messages.append(
                            ToolMessage(
                                content=f"Unknown tool: {{tool_name}}. Available tools: {{', '.join(tool_map.keys())}}",
                                tool_call_id=tool_id if tool_id else f"call_{{tool_calls_count}}"
                            )
                        )
            else:
                # No more tool calls, we're done
                logger.debug(f"Iteration {{iteration + 1}}: No tool calls, finalizing response")
                break
        
        # Extract final response
        if messages:
            # Find the last AIMessage that isn't a tool call request
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    # Check if this message has content (not just tool calls)
                    if msg.content and msg.content.strip():
                        output_text = msg.content
                        break
                    elif not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                        # No tool calls, use content even if empty
                        output_text = msg.content or "No content in response"
                        break
            else:
                # Fallback: use last message as string
                output_text = str(messages[-1])
        else:
            output_text = "No response generated"
            logger.warning("No response generated")
        
        logger.info(f"Q&A processing complete. Result length: {{len(output_text)}} chars")
        logger.debug(f"Full result: {{output_text}}")
        
        # Return result compatible with Masumi serialization
        return {{
            "status": "completed",
            "result": output_text,
            "identifier": identifier_from_purchaser,
            "question": question,
            "tool_calls": tool_calls_count
        }}
        
    except ValueError as e:
        error_msg = f"Invalid input data: {{str(e)}}"
        logger.error(error_msg)
        return {{
            "status": "error",
            "error": error_msg,
            "identifier": identifier_from_purchaser
        }}
    except LangChainException as e:
        error_msg = f"LangChain error: {{str(e)}}"
        logger.error(error_msg, exc_info=True)
        return {{
            "status": "error",
            "error": error_msg,
            "identifier": identifier_from_purchaser
        }}
    except Exception as e:
        # Handle provider-specific errors
        error_info = _handle_provider_error(e, provider)
        logger.error(f"{{error_info['error_type']}}: {{error_info['error']}}", exc_info=True)
        return {{
            "status": "error",
            "error": error_info["error"],
            "error_type": error_info["error_type"],
            "identifier": identifier_from_purchaser
        }}
'''


def _get_langchain_tools_template() -> str:
    """Generate custom_tools.py template for LangChain scaffold with working examples."""
    return '''"""
Custom LangChain tools for your agent.

This file includes a working DuckDuckGo search tool that you can use immediately.
Add your own custom tools here using the @tool decorator.
"""

from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun


# DuckDuckGo search tool - ready to use!
# This tool allows your agent to search the web for current information
search_tool = DuckDuckGoSearchRun()


@tool
def calculate(expression: str) -> str:
    """
    Perform basic mathematical calculations.
    
    Useful for answering math questions or performing calculations.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 5")
    
    Returns:
        Result of the calculation as a string
    
    Note: This example uses eval() for simplicity. In production, consider using
    a safer math evaluation library like 'simpleeval' or 'numexpr'.
    """
    try:
        # WARNING: eval() is used here for simplicity in the example.
        # In production, use a safer math evaluation library.
        # Example: from simpleeval import simple_eval; result = simple_eval(expression)
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


def get_tools():
    """
    Get list of custom tools for the agent.
    
    Returns:
        List of tool objects
    """
    # DuckDuckGo search is included by default
    # Add or remove tools as needed for your use case
    return [search_tool, calculate]
'''


def _get_langchain_prompts_template() -> str:
    """Generate prompts.py template for LangChain scaffold."""
    return '''"""
System prompts and prompt templates for your LangChain agent.

Customize these prompts to match your agent's behavior.
"""

SYSTEM_PROMPT = """You are a helpful Q&A assistant integrated with Masumi.

Your purpose is to answer questions accurately and helpfully. When answering questions:
1. Use your knowledge to answer directly if you're confident about the answer
2. Use the search tool if you need current information, recent events, or want to verify facts
3. Present information clearly and concisely
4. If you use search results, synthesize them into a coherent answer
5. Always aim to be helpful, accurate, and educational

Guidelines:
- Answer questions clearly and directly
- Use search when you need up-to-date information
- Cite sources when using search results
- If you're unsure, use search to find accurate information
- Be concise but thorough

Remember: You have access to web search tools - use them when you need current or verified information!"""

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
        "# LLM Providers (all included - agent code dynamically selects based on env vars)",
        "# OpenAI (default)",
        "langchain-openai>=0.1.0",
        "",
        "# Groq (fast, free-tier alternative)",
        "langchain-groq>=1.0.0",
        "",
        "# Anthropic",
        "langchain-anthropic>=0.1.0",
        "",
        "# Tools and utilities",
        "langchain-community>=0.0.20",
        "",
        "# DuckDuckGo search (included by default)",
        "ddgs>=0.1.0",
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

**This scaffold includes a working Q&A assistant example** that you can test immediately and then modify to build your own agent.

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

3. **Test the working example:**
   ```bash
   # Standalone mode - test locally without API server
   masumi run main.py --standalone --input '{{"question": "What is Python?"}}'
   ```

4. **Run in API mode (production):**
   ```bash
   # API mode (default) - runs as FastAPI server
   masumi run                    # Runs main.py
   masumi run main.py           # Or specify explicitly
   ```

## Working Example

This scaffold includes a **working Q&A assistant** that:
- Answers questions directly when possible
- Uses web search (DuckDuckGo) when current information is needed
- Demonstrates tool calling patterns
- Works with OpenAI, Groq, or Anthropic providers

**Test it:**
```bash
masumi run main.py --standalone --input '{{"question": "What is Python?"}}'
```

Then modify `agent.py` to build your own agent!

## Architecture

```mermaid
graph TD
    A[User Request] --> B[Masumi API]
    B --> C[process_job function]
    C --> D[LangChain Agent]
    D --> E{{Tool Needed?}}
    E -->|Yes| F[Execute Tool]
    F --> G[DuckDuckGo Search]
    F --> H[Calculate Tool]
    G --> D
    H --> D
    E -->|No| I[LLM Response]
    I --> J[Return Result]
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
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)

**Masumi Configuration:**
- `PAYMENT_SERVICE_URL`: Payment service URL (must end with /api/v1)
- `NETWORK`: 'Preprod' or 'Mainnet' (default: 'Preprod')
- `PORT`: Port to bind to (default: 8080)

## Project Structure

```
.
├── main.py              # Entry point - Masumi.run() integration
├── agent.py             # LangChain tool calling agent + process_job
├── tools/               # Custom LangChain tools
│   ├── __init__.py
│   └── custom_tools.py  # DuckDuckGo search + calculate tools
├── config/              # Configuration
│   └── prompts.py       # System prompts for Q&A assistant
├── requirements.txt     # Dependencies (masumi + langchain)
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## LangChain Integration

### Tool Calling Pattern

This scaffold uses the **tool calling agent pattern** (recommended):
- LLM decides when to use tools
- Manual loop for tool execution
- Full control and visibility
- Works across all providers

**How it works:**
1. User sends question → `process_job()` receives it
2. Agent decides: answer directly OR use search tool
3. If tool needed: executes tool, gets results, synthesizes answer
4. Returns final answer

### Customizing the Agent

1. **Modify `agent.py`:**
   - Change the `process_job()` function logic
   - Adjust tool calling loop behavior
   - Add custom validation or processing

2. **Add custom tools in `tools/custom_tools.py`:**
   ```python
   from langchain_core.tools import tool
   
   @tool
   def my_custom_tool(input: str) -> str:
       \"\"\"Tool description for the LLM.\"\"\"
       # Your tool logic
       return result
   
   # Add to get_tools() function
   def get_tools():
       return [search_tool, calculate, my_custom_tool]
   ```

3. **Update prompts in `config/prompts.py`:**
   - Customize `SYSTEM_PROMPT` to change agent behavior
   - Modify how the agent uses tools

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

- **Input:** `{{"question": "What is Python?"}}` (matches INPUT_SCHEMA)
- **Process:** LangChain agent with tool calling
- **Output:** `{{"status": "completed", "result": "Python is..."}}`

This allows your LangChain agent to work seamlessly with Masumi's payment and API infrastructure.

## Development

### Running Locally (Standalone Mode)

Perfect for testing without Masumi setup:

```bash
# Set only LLM API key in .env
OPENAI_API_KEY=your_key_here

# Test the agent
masumi run main.py --standalone --input '{{"question": "What is Python?"}}'
```

### Running in API Mode (Production)

Requires Masumi credentials:

```bash
# Set all required env vars in .env
AGENT_IDENTIFIER=your_agent_id
PAYMENT_API_KEY=your_payment_key
SELLER_VKEY=your_seller_key
OPENAI_API_KEY=your_openai_key

# Run the server
masumi run
# Server starts on http://0.0.0.0:8080
```

### Debugging

Enable debug logging:
```bash
# In .env
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

1. ✅ **Test the example:** `masumi run main.py --standalone --input '{{"question": "..."}}'`
2. 🔧 **Modify `agent.py`:** Change `process_job()` to build your own agent
3. 🛠️ **Add tools:** Create custom tools in `tools/custom_tools.py`
4. 📝 **Customize prompts:** Update `config/prompts.py` for your use case
5. 🚀 **Deploy:** Set up Masumi credentials and deploy

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
    
    # Handle empty files or files with only comments (yaml.safe_load returns None)
    if config is None:
        config = {{}}
    
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
        "",
        "This includes a working Q&A assistant example that you can test immediately:",
        "  masumi run main.py --standalone --input '{{\"question\": \"What is Python?\"}}'",
        "",
        "Then modify agent.py to build your own agent!",
        '"""',
        "# Load environment variables from .env file",
        "from dotenv import load_dotenv",
        "load_dotenv()",
        "",
        "from masumi import run",
        "from agent import process_job",
        "",
        "# Define input schema",
        "# This matches the working Q&A example in agent.py",
        'INPUT_SCHEMA = {',
        '    "input_data": [',
        '        {',
        '            "id": "question",',
        '            "type": "string",',
        '            "name": "Question"',
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
