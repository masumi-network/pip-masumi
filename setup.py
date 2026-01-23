from setuptools import setup, find_packages
import os

# Read README.md if it exists
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="masumi",
    version="2.0.0",
    packages=find_packages(),
    package_dir={'masumi': 'masumi'},
    install_requires=[
        "aiohttp>=3.8.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.18.0",
        "canonicaljson>=1.6.3",
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.23.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "InquirerPy>=0.3.4",
        "pip-system-certs>=4.0.0",
    ],
    extras_require={
        "langchain": [
            "langchain>=1.0.0,<2.0.0",
            "langchain-openai>=0.1.0",
        ],
        "crewai": [
            "crewai>=1.0.0,<2.0.0",
            "pyyaml>=6.0",
        ],
        "ai": [
            "langchain>=1.0.0,<2.0.0",
            "langchain-openai>=0.1.0",
            "crewai>=1.0.0,<2.0.0",
            "pyyaml>=6.0",
        ],
    },
    author="Patrick Tobler",
    author_email="patrick@nmkr.io",
    description="Masumi Payment Module for Cardano blockchain integration with optional AI framework support (LangChain, CrewAI)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/masumi-network/masumi",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10,<3.14",
    entry_points={
        "console_scripts": [
            "masumi=masumi.cli:main",
        ],
    },
) 
