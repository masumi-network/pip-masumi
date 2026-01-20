"""
Masumi Environment Checker
Validates configuration, dependencies, and connectivity.
"""

import os
import sys
import asyncio
import importlib.util
from typing import List
from dataclasses import dataclass


@dataclass
class CheckResult:
    """Result of a validation check."""
    passed: bool
    message: str
    fix_hint: str = ""
    level: str = "error"  # error, warning, info


class MasumiChecker:
    """Comprehensive environment validation for Masumi agents."""

    def __init__(self):
        self.results: List[CheckResult] = []
        self.errors = 0
        self.warnings = 0
        self.verbose = False

    def add_result(self, result: CheckResult):
        """Add a check result."""
        self.results.append(result)
        if not result.passed:
            if result.level == "error":
                self.errors += 1
            elif result.level == "warning":
                self.warnings += 1

    def check_python_version(self) -> List[CheckResult]:
        """Check if Python version is >= 3.8 and compatible with frameworks."""
        version_info = sys.version_info
        version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
        results = []

        # Check minimum version
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
            results.append(CheckResult(
                passed=False,
                message=f"Python {version_str} (too old)",
                fix_hint="Masumi requires Python 3.8+",
                level="error"
            ))
            return results

        # Check framework compatibility (most AI frameworks need 3.10+)
        # CrewAI, AutoGen: 3.10-3.13
        # LangChain, LlamaIndex: 3.10+ (no upper limit)
        if version_info.major == 3 and version_info.minor >= 14:
            results.append(CheckResult(
                passed=False,
                message=f"Python {version_str} unsupported by most AI frameworks",
                fix_hint="CrewAI, AutoGen max out at 3.13. Use Python 3.10-3.13",
                level="warning"
            ))
        else:
            results.append(CheckResult(
                passed=True,
                message=f"Python {version_str}",
                level="info"
            ))

        return results

    def check_virtual_environment(self) -> CheckResult:
        """Check if running in a virtual environment."""
        # Check multiple methods for virtual environment detection
        in_venv = False
        venv_type = None
        
        # Method 1: Standard venv/virtualenv (Python 3.3+)
        if hasattr(sys, 'real_prefix'):
            in_venv = True
            venv_type = "virtualenv"
        # Method 2: venv module (Python 3.3+) - most reliable
        elif hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
            in_venv = True
            venv_type = "venv"
        # Method 3: Check for VIRTUAL_ENV environment variable
        elif os.environ.get('VIRTUAL_ENV'):
            in_venv = True
            venv_type = "virtualenv (VIRTUAL_ENV)"
        # Method 4: Check for CONDA_DEFAULT_ENV (Conda environments)
        elif os.environ.get('CONDA_DEFAULT_ENV'):
            in_venv = True
            venv_type = "conda"
        # Method 5: Check for Poetry virtualenv
        elif os.environ.get('POETRY_ACTIVE'):
            in_venv = True
            venv_type = "poetry"

        if not in_venv:
            # Check if we're in a venv directory but not activated
            cwd = os.getcwd()
            venv_path = None
            
            # Check if current directory or parent is a venv
            if os.path.basename(cwd) in ['venv', 'env', 'virtualenv', '.venv']:
                if os.path.exists(os.path.join(cwd, 'bin', 'activate')) or os.path.exists(os.path.join(cwd, 'Scripts', 'activate')):
                    venv_path = cwd
            elif os.path.exists(os.path.join(cwd, 'venv', 'bin', 'activate')) or os.path.exists(os.path.join(cwd, 'venv', 'Scripts', 'activate')):
                venv_path = os.path.join(cwd, 'venv')
            elif os.path.exists(os.path.join(cwd, '.venv', 'bin', 'activate')) or os.path.exists(os.path.join(cwd, '.venv', 'Scripts', 'activate')):
                venv_path = os.path.join(cwd, '.venv')
            
            # Check parent directory
            parent = os.path.dirname(cwd)
            if parent and os.path.basename(parent) in ['venv', 'env', 'virtualenv', '.venv']:
                if os.path.exists(os.path.join(parent, 'bin', 'activate')) or os.path.exists(os.path.join(parent, 'Scripts', 'activate')):
                    venv_path = parent
            
            if venv_path:
                # Detect OS for correct activation command
                if os.path.exists(os.path.join(venv_path, 'bin', 'activate')):
                    activate_cmd = f"source {venv_path}/bin/activate"
                else:
                    activate_cmd = f"{venv_path}\\Scripts\\activate"
                
                return CheckResult(
                    passed=False,
                    message="Virtual environment found but not activated",
                    fix_hint=f"Run: {activate_cmd}",
                    level="warning"
                )
            
            return CheckResult(
                passed=False,
                message="No virtual environment detected",
                fix_hint="python -m venv venv && source venv/bin/activate (or: python3 -m venv venv && source venv/bin/activate)",
                level="warning"
            )

        return CheckResult(
            passed=True,
            message=f"Virtual environment active ({venv_type})" if venv_type else "Virtual environment active",
            level="info"
        )

    def check_required_packages(self) -> CheckResult:
        """Check if required packages are installed."""
        required_packages = [
            "aiohttp", "canonicaljson", "fastapi", "uvicorn",
            "pydantic", "dotenv", "InquirerPy"
        ]

        missing = []
        for package in required_packages:
            import_name = "dotenv" if package == "dotenv" else package
            if importlib.util.find_spec(import_name) is None:
                missing.append(package)

        if missing:
            return CheckResult(
                passed=False,
                message=f"Missing packages: {', '.join(missing)}",
                fix_hint="pip install masumi",
                level="error"
            )

        return CheckResult(
            passed=True,
            message=f"All required packages installed ({len(required_packages)})",
            level="info"
        )

    def check_env_file(self) -> CheckResult:
        """Check if .env file exists."""
        if os.path.exists(".env"):
            return CheckResult(
                passed=True,
                message=".env file found",
                level="info"
            )

        fix_hint = "cp .env.example .env" if os.path.exists(".env.example") else "Create .env file with your credentials"

        return CheckResult(
            passed=False,
            message=".env not found",
            fix_hint=fix_hint,
            level="warning"
        )

    def check_environment_variables(self) -> List[CheckResult]:
        """Check required environment variables."""
        # Try to load .env file from current directory
        env_file_path = os.path.join(os.getcwd(), ".env")

        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_file_path, override=False)
        except ImportError:
            pass

        results = []

        # Required variables
        required_vars = ["AGENT_IDENTIFIER", "PAYMENT_API_KEY", "SELLER_VKEY"]
        missing = []

        for var_name in required_vars:
            value = os.getenv(var_name)
            if value:
                # Mask sensitive values
                display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 10 else "***"
                results.append(CheckResult(
                    passed=True,
                    message=f"{var_name} set",
                    level="info"
                ))
            else:
                missing.append(var_name)

        if missing:
            results.append(CheckResult(
                passed=False,
                message=f"Missing: {', '.join(missing)}",
                fix_hint="Set these variables in your .env file",
                level="error"
            ))

        # Optional variables (only show if set)
        optional_vars = ["NETWORK", "PAYMENT_SERVICE_URL"]
        for var_name in optional_vars:
            value = os.getenv(var_name)
            if value:
                results.append(CheckResult(
                    passed=True,
                    message=f"{var_name}: {value}",
                    level="info"
                ))

        return results

    async def check_payment_service(self) -> CheckResult:
        """Check connectivity to payment service."""
        try:
            import aiohttp
        except ImportError:
            return CheckResult(
                passed=False,
                message="aiohttp not installed",
                fix_hint="pip install aiohttp>=3.8.0",
                level="error"
            )

        payment_service_url = os.getenv(
            "PAYMENT_SERVICE_URL",
            "https://payment.masumi.network/api/v1"
        )

        base_url = payment_service_url.replace("/api/v1", "")
        health_url = f"{base_url}/health"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return CheckResult(
                            passed=True,
                            message="Payment service reachable",
                            level="info"
                        )
                    else:
                        return CheckResult(
                            passed=False,
                            message=f"Payment service error (status {response.status})",
                            fix_hint=f"Check {base_url}",
                            level="warning"
                        )
        except (asyncio.TimeoutError, Exception) as e:
            return CheckResult(
                passed=False,
                message="Payment service unreachable",
                level="warning"
            )

    def check_masumi_installation(self) -> CheckResult:
        """Check if Masumi package is properly installed."""
        try:
            import masumi
            version = getattr(masumi, "__version__", "unknown")
            return CheckResult(
                passed=True,
                message=f"Masumi {version}",
                level="info"
            )
        except ImportError:
            return CheckResult(
                passed=False,
                message="Masumi not installed",
                fix_hint="pip install masumi",
                level="error"
            )

    def check_framework_compatibility(self) -> List[CheckResult]:
        """Check if installed AI frameworks are compatible with Python version."""
        version_info = sys.version_info
        results = []

        # Framework compatibility data: (package_name, display_name, min_version, max_version)
        # Source: PyPI as of Jan 2025
        frameworks = [
            ("crewai", "CrewAI", 10, 13),        # >=3.10, <3.14
            ("langchain", "LangChain", 10, 99),  # >=3.10, <4.0
            ("autogen", "AutoGen", 10, 13),      # >=3.10, <3.14 (AG2)
            ("pyautogen", "AutoGen", 10, 13),    # Alternative package name
            ("llama_index", "LlamaIndex", 9, 99),# >=3.9, <4.0
        ]

        installed_frameworks = {}  # Display name -> (min, max)
        incompatible_frameworks = []

        for package_name, display_name, min_minor, max_minor in frameworks:
            try:
                spec = importlib.util.find_spec(package_name)
                if spec is not None:
                    # Avoid duplicates (autogen vs pyautogen)
                    if display_name not in installed_frameworks:
                        installed_frameworks[display_name] = (min_minor, max_minor)

                        # Check compatibility
                        current_minor = version_info.minor
                        if version_info.major == 3:
                            if current_minor < min_minor:
                                incompatible_frameworks.append(
                                    f"{display_name} (requires 3.{min_minor}+)"
                                )
                            elif current_minor > max_minor:
                                incompatible_frameworks.append(
                                    f"{display_name} (max 3.{max_minor})"
                                )
            except (ImportError, ValueError):
                pass

        if installed_frameworks:
            results.append(CheckResult(
                passed=True,
                message=f"Frameworks: {', '.join(installed_frameworks.keys())}",
                level="info"
            ))

            if incompatible_frameworks:
                results.append(CheckResult(
                    passed=False,
                    message=f"Incompatible: {', '.join(incompatible_frameworks)}",
                    fix_hint="Use Python 3.10-3.13 for best compatibility",
                    level="warning"
                ))

        return results

    async def run_all_checks(self, verbose: bool = False) -> bool:
        """Run all checks and return True if all critical checks pass."""
        self.verbose = verbose

        print("\n" + "=" * 50)
        print("🔍 Masumi Environment Check")
        print("=" * 50 + "\n")

        # Python version (returns list now)
        for result in self.check_python_version():
            self.add_result(result)

        # Virtual environment
        result = self.check_virtual_environment()
        self.add_result(result)

        # Masumi installation
        result = self.check_masumi_installation()
        self.add_result(result)

        # Framework compatibility check
        for result in self.check_framework_compatibility():
            self.add_result(result)

        # Required packages
        result = self.check_required_packages()
        self.add_result(result)

        # .env file
        result = self.check_env_file()
        self.add_result(result)

        # Environment variables
        for result in self.check_environment_variables():
            self.add_result(result)

        # Payment service connectivity
        result = await self.check_payment_service()
        self.add_result(result)

        # Display results
        self._display_results()

        # Return True if no critical errors
        return self.errors == 0

    def _display_results(self):
        """Display all check results in a formatted manner."""
        errors = [r for r in self.results if not r.passed and r.level == "error"]
        warnings = [r for r in self.results if not r.passed and r.level == "warning"]
        success = [r for r in self.results if r.passed]

        # In verbose mode, show all checks
        if self.verbose:
            if success:
                for result in success:
                    print(f"✅ {result.message}")

            if warnings:
                print()
                for result in warnings:
                    print(f"⚠️  {result.message}")
                    if result.fix_hint:
                        print(f"   → {result.fix_hint}")

            if errors:
                print()
                for result in errors:
                    print(f"❌ {result.message}")
                    if result.fix_hint:
                        print(f"   → {result.fix_hint}")
        else:
            # In normal mode, only show warnings and errors
            if warnings:
                for result in warnings:
                    print(f"⚠️  {result.message}")
                    if result.fix_hint:
                        print(f"   → {result.fix_hint}")

            if errors:
                if warnings:
                    print()
                for result in errors:
                    print(f"❌ {result.message}")
                    if result.fix_hint:
                        print(f"   → {result.fix_hint}")

            # If everything passed, show summary
            if not warnings and not errors:
                print("✅ All checks passed!")

        # Summary
        print("\n" + "=" * 50)
        if self.errors == 0 and self.warnings == 0:
            print("🎉 Ready! Run: masumi run agent.py")
        elif self.errors == 0:
            print(f"✅ Ready (with {self.warnings} warning(s))")
            if not self.verbose:
                print("   Run: masumi check --verbose for details")
        else:
            print(f"❌ {self.errors} error(s) found. Fix and run: masumi check")
        print("=" * 50 + "\n")


async def run_check(verbose: bool = False):
    """Run the environment check."""
    checker = MasumiChecker()
    success = await checker.run_all_checks(verbose=verbose)
    return 0 if success else 1
