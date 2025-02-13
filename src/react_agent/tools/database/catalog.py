"""Chemical catalog database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDB

logger = logging.getLogger(__name__)

class ChemicalCatalogDB(BaseDB):
    """Chemical catalog database operations."""

    TABLE_NAME = 'ChemicalCatalog'

    VALID_COLUMNS = {
        'id', 'CDPHId', 'ProductName', 'CSFId', 'CSF', 'CompanyId',
        'CompanyName', 'BrandName', 'PrimaryCategoryId', 'PrimaryCategory',
        'SubCategoryId', 'SubCategory', 'CasId', 'CasNumber', 'ChemicalId',
        'ChemicalName', 'InitialDateReported', 'MostRecentDateReported',
        'DiscontinuedDate', 'ChemicalCreatedAt', 'ChemicalUpdatedAt',
        'ChemicalDateRemoved', 'ChemicalCount'
    }

    DEFAULT_COLUMNS = [
        'ProductName', 'CompanyName', 'BrandName', 'ChemicalName',
        'CasNumber', 'PrimaryCategory'
    ]

    def _test_connection(self):
        """Test database connection."""
        test = self.client.table(self.TABLE_NAME).select('count').execute()
        logger.info(f"Connected successfully. Found {len(test.data)} records")

    async def query_chemicals(
        self,
        search_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query chemicals with flexible search criteria."""
        cols = columns or self.DEFAULT_COLUMNS
        query = self._build_query(self.TABLE_NAME, cols, search_term, filters)

        if search_term:
            if search_term.replace('-', '').isdigit():
                query = query.eq('CasNumber', search_term)
            else:
                query = query.or_(
                    f"ProductName.ilike.%{search_term}%,"
                    f"BrandName.ilike.%{search_term}%,"
                    f"ChemicalName.ilike.%{search_term}%,"
                    f"CompanyName.ilike.%{search_term}%"
                )

        return await self.execute_query(query)

    async def get_products_by_subcategory(
        self,
        subcategory: str
    ) -> List[Dict[str, Any]]:
        """Query products by subcategory."""
        columns = ['ProductName', 'CompanyName', 'BrandName', 'ChemicalName', 'SubCategory']
        query = self._build_query(self.TABLE_NAME, columns)
        query = query.ilike('SubCategory', f'%{subcategory}%')
        return await self.execute_query(query)

    async def get_discontinued_products(
        self,
        before_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query discontinued products."""
        columns = ['ProductName', 'CompanyName', 'BrandName', 'ChemicalName', 'DiscontinuedDate']
        filters = {'DiscontinuedDate': {'neq': None}}

        if before_date:
            filters['DiscontinuedDate'] = {'lte': before_date}

        query = self._build_query(self.TABLE_NAME, columns, filters=filters)
        return await self.execute_query(query)

    async def get_product_statistics(self) -> Dict[str, Any]:
        """Get statistical information about the products."""
        try:
            stats = self.client.rpc('get_product_stats').execute()
            return stats.data
        except Exception as e:
            logger.error(f"Statistics query failed: {str(e)}")
            return {}
