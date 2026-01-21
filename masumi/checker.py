"""
Masumi Environment Checker
Validates configuration, dependencies, and connectivity.
"""

import os
import sys
import asyncio
import importlib.util
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CheckResult:
    """Result of a validation check."""
    passed: bool
    message: str
    fix_hint: str = ""
    level: str = "error"  # error, warning, info


def is_hex_string(value: str) -> bool:
    """Check if a string is a valid hexadecimal string."""
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def validate_agent_identifier(value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate AGENT_IDENTIFIER format.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, "AGENT_IDENTIFIER cannot be empty. Note: The agent identifier is assigned automatically and can be found in the admin interface after agent registration."
    
    value = value.strip()
    
    # Check exact length (must be 120 characters)
    if len(value) != 120:
        return False, f"AGENT_IDENTIFIER must be exactly 120 characters (got {len(value)}). Note: The agent identifier is assigned automatically and can be found in the admin interface after agent registration."
    
    # Must be a valid hex string (only 0-9, a-f, A-F)
    if not is_hex_string(value):
        return False, "AGENT_IDENTIFIER must be a valid hex string (only 0-9, a-f, A-F allowed). Note: The agent identifier is assigned automatically and can be found in the admin interface after agent registration."
    
    return True, None


def validate_payment_api_key(value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate PAYMENT_API_KEY format.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, "PAYMENT_API_KEY cannot be empty. Note: You can find or create it in your admin interface."
    
    value = value.strip()
    
    # Check minimum length (API keys are typically at least 16 characters)
    if len(value) < 16:
        return False, "PAYMENT_API_KEY is too short (minimum 16 characters). Note: You can find or create it in your admin interface."
    
    # Check maximum reasonable length
    if len(value) > 512:
        return False, "PAYMENT_API_KEY is too long (maximum 512 characters). Note: You can find or create it in your admin interface."
    
    # API keys can be:
    # - Hex strings (if it's all hex, validate as hex)
    # - Base64-like strings (alphanumeric with +, /, =)
    # - Prefixed strings like "sk_live_..." (alphanumeric with underscores)
    # So we'll be lenient but check for obviously invalid characters
    if not re.match(r'^[a-zA-Z0-9_+/=-]+$', value):
        return False, "PAYMENT_API_KEY contains invalid characters. Note: You can find or create it in your admin interface."
    
    return True, None


def validate_seller_vkey(value: str) -> Tuple[bool, Optional[str]]:
    """
    Validate SELLER_VKEY format (hex string).
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value or not value.strip():
        return False, "SELLER_VKEY cannot be empty. Note: You can find it in your admin panel wallet or payment sources section."
    
    value = value.strip()
    
    # Must be a valid hex string (only 0-9, a-f, A-F)
    # Length can vary, but must be hex only
    if not is_hex_string(value):
        return False, "SELLER_VKEY must be a valid hex string (only 0-9, a-f, A-F allowed). Note: You can find it in your admin panel wallet or payment sources section."
    
    return True, None


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

        # Required variables with validation
        required_vars = ["AGENT_IDENTIFIER", "PAYMENT_API_KEY", "SELLER_VKEY"]
        missing = []

        for var_name in required_vars:
            value = os.getenv(var_name)
            if value:
                # Validate format based on variable type
                is_valid = True
                error_msg = None
                
                if var_name == "AGENT_IDENTIFIER":
                    is_valid, error_msg = validate_agent_identifier(value)
                elif var_name == "PAYMENT_API_KEY":
                    is_valid, error_msg = validate_payment_api_key(value)
                elif var_name == "SELLER_VKEY":
                    is_valid, error_msg = validate_seller_vkey(value)
                
                if is_valid:
                    # Mask sensitive values
                    display_value = f"{value[:4]}...{value[-4:]}" if len(value) > 10 else "***"
                    results.append(CheckResult(
                        passed=True,
                        message=f"{var_name} set ({display_value})",
                        level="info"
                    ))
                else:
                    # Validation failed
                    results.append(CheckResult(
                        passed=False,
                        message=f"{var_name} format invalid: {error_msg}",
                        fix_hint=f"Check that {var_name} is correctly formatted. Get it from the Masumi admin interface.",
                        level="error"
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


    async def run_all_checks(self, verbose: bool = False) -> bool:
        """Run all checks and return True if all critical checks pass."""
        self.verbose = verbose

        print("\n" + "=" * 50)
        print("🔍 Masumi Environment Check")
        print("=" * 50 + "\n")



        # Virtual environment
        result = self.check_virtual_environment()
        self.add_result(result)

        # Masumi installation
        result = self.check_masumi_installation()
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
            print("🎉 Ready! Run: masumi run (defaults to main.py)")
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
