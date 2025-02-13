"""Chemical inventory database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDB

logger = logging.getLogger(__name__)

class ChemicalInventoryDB(BaseDB):
    """Chemical inventory database operations."""

    TABLE_NAME = 'ChemicalInventory'

    VALID_COLUMNS = {
        'id', 'ChemicalId', 'AvailableQuantity', 'Unit',
        'WarehouseLocation', 'LastUpdated'
    }

    DEFAULT_COLUMNS = [
        'ChemicalId', 'AvailableQuantity', 'Unit',
        'WarehouseLocation'
    ]

    def _test_connection(self):
        """Test database connection."""
        test = self.client.table(self.TABLE_NAME).select('count').execute()
        logger.info(f"Connected successfully. Found {len(test.data)} records")

    async def get_chemical_inventory(
        self,
        chemical_id: int,
        warehouse: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get inventory levels for a chemical."""
        filters = {'ChemicalId': chemical_id}
        if warehouse:
            filters['WarehouseLocation'] = warehouse

        query = self._build_query(self.TABLE_NAME, self.DEFAULT_COLUMNS, filters=filters)
        return await self.execute_query(query)

    async def get_warehouse_inventory(
        self,
        warehouse: str,
        min_quantity: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Get inventory in a specific warehouse."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS,
            filters={'WarehouseLocation': warehouse}
        )

        if min_quantity is not None:
            query = query.gte('AvailableQuantity', min_quantity)

        return await self.execute_query(query)

    async def get_low_stock_items(
        self,
        threshold: float,
        warehouse: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get items with stock below threshold."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS
        )
        query = query.lte('AvailableQuantity', threshold)

        if warehouse:
            query = query.eq('WarehouseLocation', warehouse)

        return await self.execute_query(query)