"""Supabase database operations module."""

from typing import Any, Dict, List, Optional, Union
from supabase import create_client, Client
import logging

# Set up logging
logger = logging.getLogger(__name__)

class SupabaseDB:
    """Handles Supabase database read operations."""

    VALID_COLUMNS = {
        'id', 'CDPHId', 'ProductName', 'CSFId', 'CSF', 'CompanyId',
        'CompanyName', 'BrandName', 'PrimaryCategoryId', 'PrimaryCategory',
        'SubCategoryId', 'SubCategory', 'CasId', 'CasNumber', 'ChemicalId',
        'ChemicalName', 'InitialDateReported', 'MostRecentDateReported',
        'DiscontinuedDate', 'ChemicalCreatedAt', 'ChemicalUpdatedAt',
        'ChemicalDateRemoved', 'ChemicalCount'
    }

    def __init__(self, url: str, key: str):
        """Initialize Supabase client.

        Args:
            url: Supabase project URL
            key: Supabase anonymous key

        Raises:
            ValueError: If URL or key is empty
        """
        logger.info(f"Initializing SupabaseDB with URL: {url[:20]}...")

        if not url or url.isspace():
            raise ValueError("Supabase URL is required")
        if not key or key.isspace():
            raise ValueError("Supabase key is required")

        try:
            self.client = create_client(url, key)
            # Test connection
            test = self.client.table('ChemicalCatalog').select('count').execute()
            logger.info(f"Connected successfully. Found {len(test.data)} records")
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise

    async def query_chemicals(
        self,
        search_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query chemicals from the database."""
        try:
            # Start with base query
            query = self.client.table('ChemicalCatalog')

            # Select columns
            if columns:
                query = query.select(','.join(columns))
            else:
                query = query.select('ProductName,CompanyName,BrandName,ChemicalName,CasNumber,PrimaryCategory')

            # Handle search term across multiple fields
            if search_term:
                # For CAS number, use exact match
                if search_term.replace('-', '').isdigit():
                    query = query.eq('CasNumber', search_term)
                else:
                    # For text search, use ILIKE
                    query = query.or_(
                        f"ProductName.ilike.%{search_term}%,"
                        f"BrandName.ilike.%{search_term}%,"
                        f"ChemicalName.ilike.%{search_term}%,"
                        f"CompanyName.ilike.%{search_term}%"
                    )

            # Apply any additional filters
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            # Execute query
            result = query.execute()
            logger.info(f"Query returned {len(result.data)} results")
            return result.data

        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return []

    async def get_chemical_catalog(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch chemical catalog entries with optional filters."""
        query = self.client.table('ChemicalCatalog').select('*')

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.execute()
        return result.data

    async def add_chemical(self, chemical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new chemical to the catalog."""
        result = self.client.table('ChemicalCatalog').insert(chemical_data).execute()
        return result.data[0]

    async def update_chemical(self, id: str, chemical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing chemical in the catalog."""
        result = self.client.table('ChemicalCatalog').update(chemical_data).eq('id', id).execute()
        return result.data[0]

    async def delete_chemical(self, id: str) -> Dict[str, Any]:
        """Delete a chemical from the catalog."""
        result = self.client.table('ChemicalCatalog').delete().eq('id', id).execute()
        return result.data[0]

    async def get_products_by_date_range(
        self,
        start_date: str,
        end_date: str,
        date_column: str = 'InitialDateReported'
    ) -> List[Dict[str, Any]]:
        """Query products reported within a date range."""
        try:
            query = self.client.table('ChemicalCatalog').select(
                'ProductName,CompanyName,BrandName,ChemicalName,InitialDateReported,MostRecentDateReported'
            ).gte(date_column, start_date).lte(date_column, end_date)

            result = query.execute()
            logger.info(f"Found {len(result.data)} products between {start_date} and {end_date}")
            return result.data
        except Exception as e:
            logger.error(f"Date range query failed: {str(e)}")
            return []

    async def get_products_by_subcategory(
        self,
        subcategory: str
    ) -> List[Dict[str, Any]]:
        """Query products by subcategory."""
        try:
            query = self.client.table('ChemicalCatalog').select(
                'ProductName,CompanyName,BrandName,ChemicalName,SubCategory'
            ).ilike('SubCategory', f'%{subcategory}%')

            result = query.execute()
            logger.info(f"Found {len(result.data)} products in subcategory: {subcategory}")
            return result.data
        except Exception as e:
            logger.error(f"Subcategory query failed: {str(e)}")
            return []

    async def get_discontinued_products(
        self,
        before_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query discontinued products."""
        try:
            # Start with base query
            query = self.client.table('ChemicalCatalog').select(
                'ProductName,CompanyName,BrandName,ChemicalName,DiscontinuedDate'
            ).neq('DiscontinuedDate', None)  # Changed from not_() to neq()

            if before_date:
                query = query.lte('DiscontinuedDate', before_date)

            result = query.execute()
            logger.info(f"Found {len(result.data)} discontinued products")
            return result.data
        except Exception as e:
            logger.error(f"Discontinued products query failed: {str(e)}")
            return []

    async def get_product_statistics(self) -> Dict[str, Any]:
        """Get statistical information about the products."""
        try:
            # Use raw SQL for statistics via RPC
            stats = self.client.rpc('get_product_stats').execute()
            return stats.data
        except Exception as e:
            logger.error(f"Statistics query failed: {str(e)}")
            return {}

    async def search_multi_criteria(
        self,
        company: Optional[str] = None,
        category: Optional[str] = None,
        chemical: Optional[str] = None,
        brand: Optional[str] = None,
        date_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search products with multiple optional criteria."""
        try:
            query = self.client.table('ChemicalCatalog').select(
                'ProductName,CompanyName,BrandName,ChemicalName,PrimaryCategory,InitialDateReported'
            )

            if company:
                query = query.ilike('CompanyName', f'%{company}%')
            if category:
                query = query.ilike('PrimaryCategory', f'%{category}%')
            if chemical:
                query = query.ilike('ChemicalName', f'%{chemical}%')
            if brand:
                query = query.ilike('BrandName', f'%{brand}%')
            if date_after:
                query = query.gte('InitialDateReported', date_after)

            result = query.execute()
            logger.info(f"Multi-criteria search returned {len(result.data)} results")
            return result.data
        except Exception as e:
            logger.error(f"Multi-criteria search failed: {str(e)}")
            return []