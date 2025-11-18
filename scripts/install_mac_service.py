"""
Mac Service Installation

Installs the X Content RAG System as a macOS LaunchAgent for background operation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
from loguru import logger


PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xcontentrag.service</string>

    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>{working_directory}</string>

    <key>StandardOutPath</key>
    <string>{log_path}/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>{log_path}/stderr.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
"""


def get_python_path() -> str:
    """Get the current Python interpreter path."""
    return sys.executable


def create_plist_file() -> Path:
    """
    Create LaunchAgent plist file.

    Returns:
        Path to created plist file
    """
    # Get paths
    project_root = Path(__file__).parent.parent.absolute()
    python_path = get_python_path()
    script_path = project_root / "backend" / "main.py"
    log_path = project_root / "data" / "logs"

    # Ensure log directory exists
    log_path.mkdir(parents=True, exist_ok=True)

    # Format plist content
    plist_content = PLIST_TEMPLATE.format(
        python_path=python_path,
        script_path=script_path,
        working_directory=project_root,
        log_path=log_path
    )

    # Write to LaunchAgents directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)

    plist_path = launch_agents_dir / "com.xcontentrag.service.plist"

    with open(plist_path, 'w') as f:
        f.write(plist_content)

    logger.info(f"Created plist file: {plist_path}")

    return plist_path


def install_service():
    """Install the service as a LaunchAgent."""
    try:
        logger.info("Installing X Content RAG System as Mac service...")

        # Create plist file
        plist_path = create_plist_file()

        logger.info("=" * 80)
        logger.info("✅ Service installed successfully!")
        logger.info("=" * 80)

        logger.info("\nTo start the service:")
        logger.info(f"  launchctl load {plist_path}")

        logger.info("\nTo stop the service:")
        logger.info(f"  launchctl unload {plist_path}")

        logger.info("\nTo check service status:")
        logger.info("  launchctl list | grep xcontentrag")

        logger.info("\nLogs location:")
        project_root = Path(__file__).parent.parent
        logger.info(f"  {project_root / 'data' / 'logs'}")

        return True

    except Exception as e:
        logger.error(f"Error installing service: {e}")
        return False


def uninstall_service():
    """Uninstall the service."""
    try:
        logger.info("Uninstalling X Content RAG System service...")

        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.xcontentrag.service.plist"

        if plist_path.exists():
            # Try to unload first
            os.system(f"launchctl unload {plist_path}")

            # Remove plist file
            plist_path.unlink()

            logger.info("✅ Service uninstalled successfully")
            return True
        else:
            logger.warning("Service not found")
            return False

    except Exception as e:
        logger.error(f"Error uninstalling service: {e}")
        return False


def main():
    """Main installation function."""
    import argparse

    parser = argparse.ArgumentParser(description="Install X Content RAG System as Mac service")
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Uninstall the service'
    )

    args = parser.parse_args()

    if args.uninstall:
        success = uninstall_service()
    else:
        success = install_service()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
