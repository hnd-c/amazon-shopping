"""Base test class for query tests."""

import os
import pytest
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

@pytest.fixture
def config() -> RunnableConfig:
    """Get test configuration."""
    load_dotenv()
    return RunnableConfig(
        configurable={
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_ANON_KEY')
        }
    )