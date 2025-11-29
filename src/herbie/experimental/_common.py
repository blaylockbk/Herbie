"""Common utilities for experimental modules: console and logger setup."""

import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console()
rich_handler = RichHandler(
    console=console,
    rich_tracebacks=True,
    show_level=True,
    show_time=True,
    markup=True,
)
logging.basicConfig(
    level=logging.INFO,
    handlers=[rich_handler],
    datefmt="[%H:%M:%S]",
    format="%(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
