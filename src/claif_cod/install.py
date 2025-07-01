# this_file: claif_cod/src/claif_cod/install.py

from loguru import logger

# Import common install functionality
try:
    from claif.install import (
        ensure_bun_installed,
        get_install_location,
        install_npm_package_globally,
        bundle_all_tools,
        install_portable_tool,
        uninstall_tool,
    )
except ImportError:
    logger.error("claif package not found. Please install claif package first.")
    exit(1)


def install_codex() -> dict:
    """Install Codex CLI with bundled approach."""
    if not ensure_bun_installed():
        return {"installed": [], "failed": ["codex"], "message": "bun installation failed"}

    install_dir = get_install_location()

    # Install npm package globally first
    logger.info("Installing @openai/codex...")
    if not install_npm_package_globally("@openai/codex"):
        return {"installed": [], "failed": ["codex"], "message": "@openai/codex installation failed"}

    # Bundle all tools (this creates the dist directory with all tools)
    logger.info("Bundling CLI tools...")
    dist_dir = bundle_all_tools()
    if not dist_dir:
        return {"installed": [], "failed": ["codex"], "message": "bundling failed"}

    # Install Codex specifically
    logger.info("Installing codex...")
    if install_portable_tool("codex", install_dir, dist_dir):
        logger.success("🎉 Codex installed successfully!")
        logger.info("You can now use 'codex' command from anywhere")
        return {"installed": ["codex"], "failed": []}
    else:
        return {"installed": [], "failed": ["codex"], "message": "codex installation failed"}


def uninstall_codex() -> dict:
    """Uninstall Codex CLI."""
    logger.info("Uninstalling codex...")

    if uninstall_tool("codex"):
        logger.success("✓ Codex uninstalled successfully")
        return {"uninstalled": ["codex"], "failed": []}
    else:
        return {"uninstalled": [], "failed": ["codex"], "message": "codex uninstallation failed"}


def is_codex_installed() -> bool:
    """Check if Codex is installed."""
    install_dir = get_install_location()
    codex_executable = install_dir / "codex"

    return codex_executable.exists() and codex_executable.is_file()


def get_codex_status() -> dict:
    """Get Codex installation status."""
    if is_codex_installed():
        install_dir = get_install_location()
        codex_path = install_dir / "codex"
        return {"installed": True, "path": str(codex_path), "type": "bundled (claif-owned)"}
    else:
        return {"installed": False, "path": None, "type": None}
