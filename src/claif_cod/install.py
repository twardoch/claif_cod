# this_file: claif_cod/src/claif_cod/install.py

import shutil
from pathlib import Path

from loguru import logger

# Import common install functionality
try:
    from claif.common.utils import prompt_tool_configuration
    from claif.install import (
        bundle_all_tools,
        ensure_bun_installed,
        get_install_location,
        install_npm_package_globally,
        uninstall_tool,
    )
except ImportError:
    # Fallback if claif package not available
    logger.warning("claif package not found, using local implementations")
    from claif_cod.install_fallback import (
        bundle_all_tools,
        ensure_bun_installed,
        get_install_location,
        install_npm_package_globally,
        uninstall_tool,
    )

    def prompt_tool_configuration(tool_name: str, config_commands: list[str]) -> None:
        """Fallback implementation for tool configuration prompt."""
        if config_commands:
            for _cmd in config_commands:
                pass


def install_codex() -> dict:
    """Install Codex CLI with bundled approach."""
    if not ensure_bun_installed():
        return {
            "installed": [],
            "failed": ["codex"],
            "message": "bun installation failed",
        }

    install_dir = get_install_location()

    # Install npm package globally first
    logger.info("Installing @openai/codex...")
    if not install_npm_package_globally("@openai/codex"):
        return {
            "installed": [],
            "failed": ["codex"],
            "message": "@openai/codex installation failed",
        }

    # Bundle all tools (this creates the dist directory with all tools)
    logger.info("Bundling CLI tools...")
    dist_dir = bundle_all_tools()
    if not dist_dir:
        return {
            "installed": [],
            "failed": ["codex"],
            "message": "bundling failed",
        }

    # Install Codex from bundled dist
    logger.info("Installing codex...")
    codex_source = dist_dir / "codex" / "codex"
    codex_target = install_dir / "codex"

    try:
        if codex_source.exists():
            # Copy the bundled executable
            shutil.copy2(codex_source, codex_target)
            codex_target.chmod(0o755)

            logger.success("🎉 Codex installed successfully!")
            logger.info("You can now use 'codex' command from anywhere")

            # Prompt for configuration
            config_commands = [
                "export OPENAI_API_KEY=your_api_key_here",
                "codex --help",
            ]
            prompt_tool_configuration("Codex", config_commands)

            return {"installed": ["codex"], "failed": []}
        else:
            msg = f"Bundled codex executable not found at {codex_source}"
            logger.error(msg)
            return {
                "installed": [],
                "failed": ["codex"],
                "message": "bundled executable not found",
            }

    except Exception as e:
        logger.error(f"Failed to install Codex: {e}")
        return {
            "installed": [],
            "failed": ["codex"],
            "message": f"installation failed: {e}",
        }


def uninstall_codex() -> dict:
    """Uninstall Codex CLI."""
    logger.info("Uninstalling codex...")

    if uninstall_tool("codex"):
        logger.success("✓ Codex uninstalled successfully")
        return {"uninstalled": ["codex"], "failed": []}
    return {"uninstalled": [], "failed": ["codex"], "message": "codex uninstallation failed"}


def is_codex_installed() -> bool:
    """Check if Codex is installed."""
    install_dir = get_install_location()
    codex_executable = install_dir / "codex"
    codex_dir = install_dir / "codex"

    return (codex_executable.exists() and codex_executable.is_file()) or (codex_dir.exists() and codex_dir.is_dir())


def get_codex_status() -> dict:
    """Get Codex installation status."""
    if is_codex_installed():
        install_dir = get_install_location()
        codex_path = install_dir / "codex"
        return {"installed": True, "path": str(codex_path), "type": "bundled (claif-owned)"}
    return {"installed": False, "path": None, "type": None}
