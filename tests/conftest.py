"""Test configuration and shared fixtures."""

import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

@pytest.fixture
def config() -> dict:
    """Get test configuration."""
    load_dotenv()

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        pytest.fail("Missing Supabase credentials. Check your .env file")

    return {
        'configurable': {
            'supabase_url': url,
            'supabase_key': key
        }
    }

@pytest_asyncio.fixture(autouse=True)
async def verify_db_connection(config):
    """Verify database connection before running tests."""
    from react_agent.tools.database.catalog import ChemicalCatalogDB

    db = ChemicalCatalogDB(
        config['configurable']['supabase_url'],
        config['configurable']['supabase_key']
    )

    try:
        results = await db.query_chemicals()
        if not results:
            pytest.skip("Database is empty. Load test data before running tests.")
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {str(e)}")