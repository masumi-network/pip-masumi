"""
Interactive CLI utilities for Masumi init with animations and visual feedback.
"""

import sys
import time
from typing import List, Optional, Dict, Any

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
    HAS_INQUIRER = True
except ImportError:
    HAS_INQUIRER = False


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Masumi brand color #DA2F5A
    MASUMI = '\033[38;2;218;47;90m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'


def print_color(text: str, color: str = Colors.RESET, end: str = '\n'):
    """Print colored text."""
    print(f"{color}{text}{Colors.RESET}", end=end, flush=True)


def clear_line():
    """Clear the current line."""
    print('\r' + ' ' * 80 + '\r', end='', flush=True)


def show_banner():
    """Display the Masumi scaffold banner with brand color #DA2F5A."""
    # Each line between ║ symbols must be exactly 66 characters
    banner = f"""{Colors.MASUMI}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║       ███╗   ███╗ █████╗ ███████╗██╗   ██╗███╗   ███╗██╗         ║
║       ████╗ ████║██╔══██╗██╔════╝██║   ██║████╗ ████║██║         ║
║       ██╔████╔██║███████║███████╗██║   ██║██╔████╔██║██║         ║
║       ██║╚██╔╝██║██╔══██║╚════██║██║   ██║██║╚██╔╝██║██║         ║
║       ██║ ╚═╝ ██║██║  ██║███████║╚██████╔╝██║ ╚═╝ ██║██║         ║
║       ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝         ║
║                                                                  ║
║                    {Colors.GREEN}Agent Project Scaffolder{Colors.MASUMI}{Colors.BOLD}                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
    print(banner)


def animate_loading(text: str, duration: float = 0.5):
    """Show a loading animation."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    frame_idx = 0

    while time.time() < end_time:
        frame = frames[frame_idx % len(frames)]
        print(f'\r{Colors.MASUMI}{frame}{Colors.RESET} {text}', end='', flush=True)
        frame_idx += 1
        time.sleep(0.1)

    clear_line()


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.MASUMI}ℹ{Colors.RESET} {text}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def select_option(
    prompt: str,
    options: List[Dict[str, Any]],
    default: Optional[int] = None
) -> Optional[str]:
    """
    Display a selection menu and get user choice.

    Args:
        prompt: The prompt text
        options: List of option dicts with 'key', 'label', 'description', 'value'
        default: Default option index (0-based)

    Returns:
        The selected value or None
    """
    if HAS_INQUIRER:
        # Use InquirerPy for better UX
        choices = []
        default_value = None

        for i, option in enumerate(options):
            label = option.get('label', '')
            desc = option.get('description', '')
            value = option.get('value')

            # Format: label - description
            display = f"{label} - {desc}" if desc else label
            choices.append(Choice(value=value, name=display))

            if i == default:
                default_value = value

        try:
            result = inquirer.select(
                message=prompt,
                choices=choices,
                default=default_value,
                pointer="❯",
                qmark="❯",  # Custom prompt marker
            ).execute()
            return result
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}")
            sys.exit(0)
    else:
        # Fallback to basic implementation
        print(f"\n{Colors.BOLD}{Colors.MASUMI}{prompt}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")

        for i, option in enumerate(options):
            marker = f"{Colors.GREEN}●{Colors.RESET}" if i == default else "○"
            key = option.get('key', str(i + 1))
            label = option.get('label', '')
            desc = option.get('description', '')

            if desc:
                print(f"  {marker} {Colors.BOLD}[{key}]{Colors.RESET} {label}")
                print(f"     {Colors.DIM}{desc}{Colors.RESET}")
            else:
                print(f"  {marker} {Colors.BOLD}[{key}]{Colors.RESET} {label}")

        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")

        default_key = options[default]['key'] if default is not None else None
        default_text = f" (default: {default_key})" if default_key else ""

        while True:
            try:
                choice = input(f"\n{Colors.MASUMI}Select an option{default_text}: {Colors.RESET}").strip()

                if not choice and default is not None:
                    return options[default]['value']

                # Try to match by key
                for option in options:
                    if option.get('key', '').lower() == choice.lower():
                        return option['value']

                # Try to match by index
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return options[idx]['value']
                except ValueError:
                    pass

                print_error(f"Invalid choice. Please select from the options above.")
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}\n")
                sys.exit(0)

def multi_select(
    prompt: str,
    options: List[Dict[str, Any]],
    default: Optional[List[str]] = None
) -> List[str]:
    """
    Display a multi-selection menu and get user choices.

    Args:
        prompt: The prompt text
        options: List of option dicts with 'key', 'label', 'description', 'value'
        default: Default selected values

    Returns:
        List of selected values
    """
    if default is None:
        default = []

    if HAS_INQUIRER:
        # Use InquirerPy for better UX
        choices = []
        default_values = []

        for option in options:
            label = option.get('label', '')
            desc = option.get('description', '')
            value = option.get('value')

            # Format: label - description
            display = f"{label} - {desc}" if desc else label
            choices.append(Choice(value=value, name=display))

            if value in default:
                default_values.append(value)

        try:
            result = inquirer.checkbox(
                message=prompt,
                choices=choices,
                default=default_values,
                pointer="❯",
                qmark="❯",  # Custom prompt marker
                instruction="(Use arrow keys to move, space to select, enter to confirm)",
            ).execute()
            return result if result else []
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}")
            sys.exit(0)
    else:
        # Fallback to basic implementation
        print(f"\n{Colors.BOLD}{Colors.MASUMI}{prompt}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")
        print(f"{Colors.DIM}  (Enter comma-separated numbers, or press Enter to skip){Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")

        for i, option in enumerate(options):
            is_selected = option['value'] in default
            marker = f"{Colors.GREEN}✓{Colors.RESET}" if is_selected else " "
            key = str(i + 1)
            label = option.get('label', '')
            desc = option.get('description', '')

            if desc:
                print(f"  {marker} {Colors.BOLD}[{key}]{Colors.RESET} {label}")
                print(f"     {Colors.DIM}{desc}{Colors.RESET}")
            else:
                print(f"  {marker} {Colors.BOLD}[{key}]{Colors.RESET} {label}")

        print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")

        while True:
            try:
                choice = input(f"\n{Colors.MASUMI}Select options (comma-separated): {Colors.RESET}").strip()

                if not choice:
                    return default

                selected = []
                for num_str in choice.split(','):
                    num_str = num_str.strip()
                    try:
                        idx = int(num_str) - 1
                        if 0 <= idx < len(options):
                            selected.append(options[idx]['value'])
                    except ValueError:
                        pass

                if selected:
                    return selected
                else:
                    print_error("Invalid selection. Please enter valid numbers.")
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}\n")
                sys.exit(0)


def get_input(prompt: str, default: Optional[str] = None, validator: Optional[callable] = None) -> str:
    """Get user input with optional default and validation."""
    if HAS_INQUIRER:
        # Use InquirerPy for better UX
        def inquirer_validator(text):
            if not text and default:
                return True
            if not text:
                raise ValueError("This field is required.")
            if validator:
                validator(text)
            return True

        try:
            result = inquirer.text(
                message=prompt,
                default=default or "",
                validate=inquirer_validator if validator else None,
                qmark="❯",  # Custom prompt marker
            ).execute()
            return result if result else (default or "")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}")
            sys.exit(0)
    else:
        # Fallback to basic implementation
        default_text = f" (default: {default})" if default else ""

        while True:
            try:
                value = input(f"{Colors.MASUMI}{prompt}{default_text}: {Colors.RESET}").strip()

                if not value and default:
                    return default

                if not value:
                    print_error("This field is required.")
                    continue

                if validator:
                    try:
                        validator(value)
                    except ValueError as e:
                        print_error(str(e))
                        continue

                return value
            except KeyboardInterrupt:
                print(f"\n\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}\n")
                sys.exit(0)


def show_progress(steps: List[tuple], delay: float = 0.3):
    """
    Show progress through multiple steps.

    Args:
        steps: List of (step_name, success_message) tuples
        delay: Delay between steps
    """
    for step_name, success_msg in steps:
        animate_loading(f"{step_name}...", duration=delay)
        print_success(success_msg)
        time.sleep(0.1)


def show_completion_message(project_name: str, output_dir: str):
    """Show a nice completion message."""
    print(f"\n{Colors.GREEN}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║                      Project Created Successfully                ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")

    print(f"{Colors.BOLD}Project:{Colors.RESET} {Colors.MASUMI}{project_name}{Colors.RESET}")
    print(f"{Colors.BOLD}Location:{Colors.RESET} {Colors.MASUMI}{output_dir}{Colors.RESET}\n")

    print(f"{Colors.BOLD}Quick Setup:{Colors.RESET}")
    print(f"{Colors.CYAN}cd {output_dir} && pip install -r requirements.txt && cp .env.example .env{Colors.RESET}\n")

    print(f"{Colors.GREEN}{Colors.BOLD}Start Building{Colors.RESET}\n")

