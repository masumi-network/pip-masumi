"""Test script to verify LangChain and CrewAI scaffolds work."""

import shutil
from pathlib import Path
import pytest
from masumi.scaffold_templates import _scaffold_langchain, _scaffold_crewai


def test_langchain_scaffold():
    """Test that LangChain scaffold generates all required files."""
    langchain_path = Path("test-scaffolds/test-langchain")
    if langchain_path.exists():
        shutil.rmtree(langchain_path)
    langchain_path.mkdir(parents=True, exist_ok=True)

    try:
        _scaffold_langchain("test-langchain", langchain_path, interactive=False)
        
        # Check files
        required_files = [
            "main.py",
            "agent.py",
            "tools/__init__.py",
            "tools/custom_tools.py",
            "config/prompts.py",
            "requirements.txt",
            ".env.example",
            "README.md",
            ".gitignore"
        ]
        
        missing = []
        for file in required_files:
            if not (langchain_path / file).exists():
                missing.append(file)
        
        assert not missing, f"Missing files: {missing}"
        
    finally:
        # Cleanup
        if langchain_path.exists():
            shutil.rmtree(langchain_path)


def test_crewai_scaffold():
    """Test that CrewAI scaffold generates all required files."""
    crewai_path = Path("test-scaffolds/test-crewai")
    if crewai_path.exists():
        shutil.rmtree(crewai_path)
    crewai_path.mkdir(parents=True, exist_ok=True)

    try:
        _scaffold_crewai("test-crewai", crewai_path, interactive=False)
        
        # Check files
        required_files = [
            "main.py",
            "crew.py",
            "config/agents.yaml",
            "config/tasks.yaml",
            "tools/__init__.py",
            "tools/custom_tools.py",
            "knowledge/.gitkeep",
            "requirements.txt",
            ".env.example",
            "README.md",
            ".gitignore"
        ]
        
        missing = []
        for file in required_files:
            if not (crewai_path / file).exists():
                missing.append(file)
        
        assert not missing, f"Missing files: {missing}"
        
    finally:
        # Cleanup
        if crewai_path.exists():
            shutil.rmtree(crewai_path)
