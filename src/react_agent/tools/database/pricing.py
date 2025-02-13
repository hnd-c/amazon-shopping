"""Chemical pricing database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDB

logger = logging.getLogger(__name__)

class ChemicalPricingDB(BaseDB):
    """Chemical pricing database operations."""

    TABLE_NAME = 'ChemicalPricing'

    VALID_COLUMNS = {
        'id', 'ChemicalId', 'UnitSize', 'Price',
        'Currency', 'EffectiveDate', 'CreatedAt'
    }

    DEFAULT_COLUMNS = [
        'ChemicalId', 'UnitSize', 'Price',
        'Currency', 'EffectiveDate'
    ]

    def _test_connection(self):
        """Test database connection."""
        test = self.client.table(self.TABLE_NAME).select('count').execute()
        logger.info(f"Connected successfully. Found {len(test.data)} records")

    async def query_prices(
        self,
        chemical_id: Optional[int] = None,
        effective_date: Optional[str] = None,
        currency: Optional[str] = None,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query chemical prices with flexible criteria."""
        cols = columns or self.DEFAULT_COLUMNS

        filters = {}
        if chemical_id:
            filters['ChemicalId'] = chemical_id
        if currency:
            filters['Currency'] = currency
        if effective_date:
            filters['EffectiveDate'] = {'lte': effective_date}

        query = self._build_query(self.TABLE_NAME, cols, filters=filters)
        return await self.execute_query(query)

    async def get_latest_prices(
        self,
        chemical_id: int
    ) -> List[Dict[str, Any]]:
        """Get the latest prices for a chemical."""
        query = self.client.table(self.TABLE_NAME)\
            .select('*')\
            .eq('ChemicalId', chemical_id)\
            .order('EffectiveDate', desc=True)\
            .limit(1)
        return await self.execute_query(query)

    async def get_price_history(
        self,
        chemical_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get price history for a chemical within a date range."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS,
            filters={'ChemicalId': chemical_id}
        )

        if start_date:
            query = query.gte('EffectiveDate', start_date)
        if end_date:
            query = query.lte('EffectiveDate', end_date)

        query = query.order('EffectiveDate', desc=True)
        return await self.execute_query(query)