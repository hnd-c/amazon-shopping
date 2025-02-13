"""Chemical shipping database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDB

logger = logging.getLogger(__name__)

class ShippingEstimatesDB(BaseDB):
    """Shipping estimates database operations."""

    TABLE_NAME = 'ShippingEstimates'

    VALID_COLUMNS = {
        'id', 'OriginLocation', 'DestinationState', 'EstimatedDays',
        'ShippingMethod', 'BaseRate', 'LastUpdated'
    }

    DEFAULT_COLUMNS = [
        'OriginLocation', 'DestinationState', 'EstimatedDays',
        'ShippingMethod', 'BaseRate'
    ]

    def _test_connection(self):
        """Test database connection."""
        test = self.client.table(self.TABLE_NAME).select('count').execute()
        logger.info(f"Connected successfully. Found {len(test.data)} records")

    async def get_shipping_estimate(
        self,
        origin: str,
        destination: str,
        method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get shipping estimates for a route."""
        filters = {
            'OriginLocation': origin,
            'DestinationState': destination
        }
        if method:
            filters['ShippingMethod'] = method

        query = self._build_query(self.TABLE_NAME, self.DEFAULT_COLUMNS, filters=filters)
        return await self.execute_query(query)

    async def get_shipping_methods(
        self,
        origin: Optional[str] = None,
        destination: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available shipping methods."""
        filters = {}
        if origin:
            filters['OriginLocation'] = origin
        if destination:
            filters['DestinationState'] = destination

        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS,
            filters=filters
        )
        query = query.order('BaseRate', desc=False)
        return await self.execute_query(query)

    async def get_fastest_routes(
        self,
        destination: str,
        max_days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get fastest shipping routes to a destination."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS,
            filters={'DestinationState': destination}
        )

        if max_days:
            query = query.lte('EstimatedDays', max_days)

        query = query.order('EstimatedDays', desc=False)
        return await self.execute_query(query)