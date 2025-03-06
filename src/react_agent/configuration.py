"""Define the configurable parameters for the agent."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field, fields
from typing import Annotated, Optional
import logging
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config

from react_agent import prompts

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> dict:
    """Load configuration from config.json file."""
    # First load environment variables
    env_path = Path('.env')
    if not env_path.exists():
        env_path = Path('../.env')
    if not env_path.exists():
        env_path = Path('../../.env')

    if env_path.exists():
        logger.info(f"Loading environment from {env_path.absolute()}")
        load_dotenv(env_path)
    else:
        logger.warning("No .env file found!")

    # Then load config file
    config_dir = Path(__file__).parent
    config_path = config_dir / 'config.json'
    template_path = config_dir / 'config.template.json'

    # Try loading config.json first, fall back to template
    if config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        config_file = config_path
    else:
        logger.info(f"No config.json found, using template from {template_path}")
        if not template_path.exists():
            logger.error("No config template found!")
            return {}
        config_file = template_path

    try:
        with open(config_file) as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

# Load configuration
CONFIG = load_config()

@dataclass(kw_only=True)
class Configuration:
    """The configuration for the Amazon shopping assistant agent."""

    name: str = field(
        default=CONFIG.get('name', 'Amazon Shopping Assistant'),
        metadata={
            "description": "Name of this configuration"
        },
    )

    system_prompt: str = field(
        default=CONFIG.get('system_prompt', prompts.SYSTEM_PROMPT),
        metadata={
            "description": "The system prompt to use for the agent's interactions."
        },
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=CONFIG.get('model', "anthropic/claude-3-5-sonnet-20240620"),
        metadata={
            "description": "The name of the language model to use."
        },
    )

    # Results configuration
    max_search_results: int = field(
        default=CONFIG.get('max_search_results', 5),
        metadata={
            "description": "Maximum number of search results to return."
        },
    )

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Log configuration
        logger.info(f"Using configuration: {self.name}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Max search results: {self.max_search_results}")

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        if config is None:
            logger.info("Creating new Configuration from config.json")
            return cls()

        config = ensure_config(config)
        configurable = config.get("configurable", {})

        if configurable is None or not isinstance(configurable, dict):
            logger.info("Creating new Configuration from config.json (no valid configurable)")
            return cls()

        # Create instance with config.json values first
        instance = cls()

        # Update fields from configurable
        for field in fields(cls):
            if field.name in configurable:
                setattr(instance, field.name, configurable[field.name])

        return instance
