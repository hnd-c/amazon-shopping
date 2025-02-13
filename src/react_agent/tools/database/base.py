"""Base database functionality."""

from typing import Any, Dict, List, Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

class BaseDB:
    """Base database class with common functionality."""

    def __init__(self, url: str, key: str):
        """Initialize Supabase client."""
        if not url or not key:
            raise ValueError("Supabase URL and key are required")

        try:
            self.client = create_client(url, key)
            self._test_connection()
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def _test_connection(self):
        """Test database connection."""
        raise NotImplementedError("Subclasses must implement _test_connection")

    def _build_query(
        self,
        table: str,
        columns: List[str],
        search_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Build a base query with common functionality."""
        query = self.client.table(table).select(','.join(columns))

        if filters:
            for key, value in filters.items():
                if isinstance(value, dict):  # For range operations
                    for op, val in value.items():
                        if op == 'gte':
                            query = query.gte(key, val)
                        elif op == 'lte':
                            query = query.lte(key, val)
                        elif op == 'neq':
                            query = query.neq(key, val)
                else:
                    query = query.eq(key, value)

        return query

    async def execute_query(self, query: Any) -> List[Dict[str, Any]]:
        """Execute a query and handle errors."""
        try:
            result = query.execute()
            logger.info(f"Query returned {len(result.data)} results")
            return result.data
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            return []
