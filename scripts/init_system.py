"""
System Initialization Script

Sets up the X Content RAG system:
- Creates necessary directories
- Initializes databases
- Sets up vector store
- Validates configuration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
import yaml


def create_directories():
    """Create necessary directory structure."""
    logger.info("Creating directory structure...")

    directories = [
        "data/knowledge_base",
        "data/databases",
        "data/databases/backups",
        "data/logs",
        "data/vectorstore/chroma",
        "screenshots",
        "config"
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"  ✓ {directory}")

    logger.info("Directory structure created")


def validate_config():
    """Validate configuration file exists and is valid."""
    logger.info("Validating configuration...")

    config_path = Path("config/config.yaml")
    example_path = Path("config/config.example.yaml")

    if not config_path.exists():
        if example_path.exists():
            logger.warning("config.yaml not found. Please copy config.example.yaml to config.yaml")
            logger.info("Run: cp config/config.example.yaml config/config.yaml")
            # Create a basic config from example
            logger.info("Creating basic config.yaml from example...")
            import shutil
            shutil.copy(example_path, config_path)
            logger.info("  ✓ Created config.yaml (please edit with your API keys)")
        else:
            logger.error("No config files found!")
            return False
    else:
        # Validate YAML syntax
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Check for required keys
            required_keys = ['api_keys', 'rag', 'claude']
            for key in required_keys:
                if key not in config:
                    logger.warning(f"Missing config section: {key}")

            # Check API key
            if not config.get('api_keys', {}).get('anthropic_api_key'):
                logger.warning("⚠️  Anthropic API key not configured!")
                logger.info("   Edit config/config.yaml and add your API key")

            logger.info("  ✓ Configuration valid")

        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return False

    return True


def initialize_vector_store():
    """Initialize ChromaDB vector store."""
    logger.info("Initializing vector store...")

    try:
        from rag.vectorstore.chroma_store import ChromaStore
        from backend.core.config import get_config

        config = get_config()

        # Create vector store
        store = ChromaStore(
            persist_directory=config.rag.vectorstore_path,
            collection_name="content"
        )

        count = store.count()
        logger.info(f"  ✓ Vector store initialized ({count} documents)")

        return True

    except Exception as e:
        logger.error(f"Error initializing vector store: {e}")
        return False


def setup_logging():
    """Configure logging."""
    logger.info("Setting up logging...")

    from loguru import logger as log_instance

    # Remove default handler
    log_instance.remove()

    # Add console handler
    log_instance.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="INFO"
    )

    # Add file handler
    log_instance.add(
        "data/logs/system_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} | {message}"
    )

    logger.info("  ✓ Logging configured")


def check_dependencies():
    """Check if required packages are installed."""
    logger.info("Checking dependencies...")

    required_packages = [
        'anthropic',
        'chromadb',
        'sentence_transformers',
        'fastapi',
        'tweepy',
        'playwright',
        'apscheduler',
        'streamlit',
        'beautifulsoup4'
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"  ✓ {package}")
        except ImportError:
            logger.warning(f"  ✗ {package} not installed")
            missing.append(package)

    if missing:
        logger.warning(f"\nMissing packages: {', '.join(missing)}")
        logger.info("Install with: pip install -r requirements.txt")
        return False

    logger.info("All dependencies installed")
    return True


def main():
    """Run system initialization."""
    logger.info("=" * 80)
    logger.info("X CONTENT RAG SYSTEM - INITIALIZATION")
    logger.info("=" * 80)

    # Check dependencies
    if not check_dependencies():
        logger.error("\n⚠️  Please install missing dependencies first")
        logger.info("Run: pip install -r requirements.txt")
        return False

    # Create directories
    create_directories()

    # Setup logging
    setup_logging()

    # Validate config
    if not validate_config():
        logger.error("\n⚠️  Configuration validation failed")
        return False

    # Initialize vector store
    if not initialize_vector_store():
        logger.error("\n⚠️  Vector store initialization failed")
        return False

    logger.info("\n" + "=" * 80)
    logger.info("✅ SYSTEM INITIALIZATION COMPLETE")
    logger.info("=" * 80)

    logger.info("\nNext steps:")
    logger.info("1. Edit config/config.yaml with your API keys")
    logger.info("2. (Optional) Import your Twitter archive: python scripts/import_twitter_archive.py")
    logger.info("3. Start the backend: python -m backend.main")
    logger.info("4. Launch dashboard: streamlit run dashboard/app.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
