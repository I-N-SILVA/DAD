"""
Configuration Manager

Loads and manages system configuration from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class APIConfig:
    """API keys configuration."""
    anthropic_api_key: str
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None


@dataclass
class RAGConfig:
    """RAG system configuration."""
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    top_k_results: int
    similarity_threshold: float
    vectorstore_path: str


@dataclass
class ClaudeConfig:
    """Claude API configuration."""
    model: str
    max_tokens: int
    temperature: float
    system_prompt: str


@dataclass
class ContentConfig:
    """Content generation configuration."""
    niches: list
    target_audience: str
    tweet_characteristics: Dict[str, Any]
    writing_style: Dict[str, Any]


class ConfigManager:
    """
    Manages application configuration.

    Loads configuration from YAML file and provides typed access
    to configuration sections.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to config YAML file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

        if not self.config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            logger.info("Please copy config/config.example.yaml to config/config.yaml")
            # Try example config
            example_path = Path("config/config.example.yaml")
            if example_path.exists():
                self.config_path = example_path
                logger.info(f"Using example config: {example_path}")
            else:
                raise FileNotFoundError(f"Config file not found: {config_path}")

        self.load_config()

    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

            logger.info(f"Configuration loaded from {self.config_path}")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def reload(self):
        """Reload configuration from file."""
        self.load_config()
        logger.info("Configuration reloaded")

    @property
    def api_keys(self) -> APIConfig:
        """Get API keys configuration."""
        keys = self.config.get('api_keys', {})
        return APIConfig(
            anthropic_api_key=keys.get('anthropic_api_key', ''),
            twitter_api_key=keys.get('twitter_api_key'),
            twitter_api_secret=keys.get('twitter_api_secret'),
            twitter_access_token=keys.get('twitter_access_token'),
            twitter_access_secret=keys.get('twitter_access_secret'),
            twitter_bearer_token=keys.get('twitter_bearer_token')
        )

    @property
    def rag(self) -> RAGConfig:
        """Get RAG configuration."""
        rag = self.config.get('rag', {})
        return RAGConfig(
            embedding_model=rag.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2'),
            chunk_size=rag.get('chunk_size', 512),
            chunk_overlap=rag.get('chunk_overlap', 50),
            top_k_results=rag.get('top_k_results', 5),
            similarity_threshold=rag.get('similarity_threshold', 0.7),
            vectorstore_path=rag.get('vectorstore_path', './data/vectorstore/chroma')
        )

    @property
    def claude(self) -> ClaudeConfig:
        """Get Claude configuration."""
        claude = self.config.get('claude', {})
        return ClaudeConfig(
            model=claude.get('model', 'claude-sonnet-4-5-20250929'),
            max_tokens=claude.get('max_tokens', 1024),
            temperature=claude.get('temperature', 0.7),
            system_prompt=claude.get('system_prompt', '')
        )

    @property
    def content(self) -> ContentConfig:
        """Get content configuration."""
        content = self.config.get('content', {})
        return ContentConfig(
            niches=content.get('niches', []),
            target_audience=content.get('target_audience', ''),
            tweet_characteristics=content.get('tweet_characteristics', {}),
            writing_style=content.get('writing_style', {})
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key (supports dot notation, e.g., 'rag.chunk_size')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None):
        """
        Save configuration to file.

        Args:
            path: Optional path to save to (defaults to original path)
        """
        save_path = Path(path) if path else self.config_path

        try:
            with open(save_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

            logger.info(f"Configuration saved to {save_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def __repr__(self) -> str:
        return f"ConfigManager(path={self.config_path})"


# Global configuration instance
_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config


def reload_config():
    """Reload global configuration."""
    global _config
    if _config:
        _config.reload()
    else:
        _config = ConfigManager()


if __name__ == "__main__":
    # Test configuration manager
    config = ConfigManager("config/config.example.yaml")

    print(f"Embedding model: {config.rag.embedding_model}")
    print(f"Claude model: {config.claude.model}")
    print(f"Content niches: {config.content.niches}")

    # Test dot notation
    chunk_size = config.get('rag.chunk_size')
    print(f"Chunk size: {chunk_size}")

    # Test set and get
    config.set('test.value', 123)
    print(f"Test value: {config.get('test.value')}")
