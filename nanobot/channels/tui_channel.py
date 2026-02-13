"""TUI (Text User Interface) channel implementation for Nanobot."""

import asyncio
import sys
from typing import Any, AsyncGenerator, Dict

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class TUIChannel:
    """
    Text User Interface channel for terminal-based interaction.

    Features:
    - Rich terminal UI with colors and formatting
    - Interactive command input
    - Real-time message display
    - Session management
    """

    name = "tui"

    def __init__(self, config: Any, bus: MessageBus):
        """
        Initialize TUI channel.

        Args:
            config: Configuration object with prompt, colors attributes
            bus: Message bus for communication
        """
        self.config = config
        self.bus = bus
        self.prompt = getattr(config, "prompt", "> ")
        self.use_colors = getattr(config, "colors", True)
        self._running = False
        self._input_task = None
        self._rich_console = None
        self._session_active = False

        try:
            from rich.console import Console
            from rich.panel import Panel
            self.Console = Console
            self.Panel = Panel
            self._rich_console = Console()
        except ImportError:
            logger.warning("Rich library not available, using plain terminal")

    async def start(self) -> None:
        """Start TUI channel and begin listening for input."""
        if self._running:
            return

        self._running = False
        self._session_active = True

        # Display welcome message
        self.show_welcome()

        # Start input loop
        self._input_task = asyncio.create_task(self._input_loop())

        logger.info("TUI channel started")

    async def stop(self) -> None:
        """Stop TUI channel."""
        self._running = False
        self._session_active = False

        # Stop input task
        if self._input_task:
            self._input_task.cancel()
            try:
                await self._input_task
            except asyncio.CancelledError:
                pass

        # Display goodbye message
        self._display_message("System", "TUI session ended")

        logger.info("TUI channel stopped")

    async def send(self, msg: OutboundMessage) -> None:
        """
        Display a message in TUI.

        Args:
            msg: Outbound message to display
        """
        content = msg.content
        sender = "System"

        self._display_message(sender, content)

    async def _input_loop(self) -> None:
        """Main input receiving loop."""
        self._session_active = True

        try:
            while self._running and self._session_active:
                try:
                    # Get user input (with timeout to allow cancellation)
                    user_input = await asyncio.wait_for(
                        self._get_input_async(),
                        timeout=0.5
                    )

                    if user_input is None:
                        continue

                    # Check for exit command
                    if user_input.lower() in ("exit", "quit", "q"):
                        self._session_active = False
                        break

                    # Create inbound message
                    inbound_msg = InboundMessage(
                        channel=self.name,
                        sender_id="user",
                        chat_id="tui",
                        content=user_input,
                        media=[],
                        metadata={}
                    )

                    # Publish to message bus
                    await self.bus.publish_inbound(inbound_msg)

                except asyncio.TimeoutError:
                    # Continue to check _running flag
                    continue
                except (EOFError, KeyboardInterrupt):
                    logger.info("TUI input interrupted")
                    break

        except Exception as e:
            if self._running:
                logger.error(f"Error in TUI input loop: {e}")

    async def _get_input_async(self) -> str | None:
        """Async input with timeout support."""
        loop = asyncio.get_event_loop()

        try:
            # Check if stdin has data available
            import select
            if select.select([sys.stdin], [], [], 0.0)[0]:
                line = await loop.run_in_executor(None, input, self.prompt)
                return line.strip()
            return None

        except (EOFError, KeyboardInterrupt):
            raise
        except Exception as e:
            logger.error(f"Error reading input: {e}")
            return None

    def _display_message(self, sender: str, content: str, msg_type: str = "text") -> None:
        """Display message with appropriate formatting."""
        if self._rich_console:
            self._display_rich_message(sender, content, msg_type)
        else:
            self._display_plain_message(sender, content, msg_type)

    def _display_rich_message(self, sender: str, content: str, msg_type: str) -> None:
        """Display message with rich formatting."""
        if self.use_colors:
            if sender == "System":
                self._rich_console.print(f"[dim cyan][{sender}][/dim cyan] {content}")
            elif sender == "Bot":
                self._rich_console.print(f"[bold green][{sender}][/bold green] {content}")
            else:
                self._rich_console.print(f"[bold blue][{sender}][/bold blue] {content}")
        else:
            self._rich_console.print(f"[{sender}] {content}")

    def _display_plain_message(self, sender: str, content: str, msg_type: str) -> None:
        """Display message in plain text."""
        print(f"[{sender}] {content}")

    def show_welcome(self) -> None:
        """Display welcome message."""
        welcome = """
╔════════════════════════════════════════╗
║     Welcome to Nanobot TUI            ║
║                                        ║
║  Commands:                             ║
║    help     - Show available commands  ║
║    exit     - Exit TUI                ║
║    status   - Show system status       ║
║                                        ║
╚════════════════════════════════════════╝
        """
        if self._rich_console:
            self._rich_console.print(welcome, style="bold blue")
        else:
            print(welcome)

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        import os
        os.system("cls" if os.name == "nt" else "clear")

    @property
    def is_running(self) -> bool:
        """Check if the channel is running."""
        return self._running
