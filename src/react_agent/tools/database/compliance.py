"""Chemical compliance database operations."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDB

logger = logging.getLogger(__name__)

class ChemicalComplianceDB(BaseDB):
    """Chemical compliance database operations."""

    TABLE_NAME = 'ChemicalCompliance'

    VALID_COLUMNS = {
        'id', 'ChemicalId', 'StateCode', 'IsRestricted',
        'RestrictionDetails', 'RequiredPermits', 'LastUpdated'
    }

    DEFAULT_COLUMNS = [
        'ChemicalId', 'StateCode', 'IsRestricted',
        'RestrictionDetails', 'RequiredPermits'
    ]

    def _test_connection(self):
        """Test database connection."""
        test = self.client.table(self.TABLE_NAME).select('count').execute()
        logger.info(f"Connected successfully. Found {len(test.data)} records")

    async def get_compliance_by_chemical(
        self,
        chemical_id: int,
        state_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get compliance information for a chemical."""
        filters = {'ChemicalId': chemical_id}
        if state_code:
            filters['StateCode'] = state_code

        query = self._build_query(self.TABLE_NAME, self.DEFAULT_COLUMNS, filters=filters)
        return await self.execute_query(query)

    async def get_restricted_chemicals(
        self,
        state_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of restricted chemicals."""
        filters = {'IsRestricted': True}
        if state_code:
            filters['StateCode'] = state_code

        query = self._build_query(self.TABLE_NAME, self.DEFAULT_COLUMNS, filters=filters)
        return await self.execute_query(query)

    async def get_state_requirements(
        self,
        state_code: str
    ) -> List[Dict[str, Any]]:
        """Get all compliance requirements for a state."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS,
            filters={'StateCode': state_code}
        )
        return await self.execute_query(query)

    async def get_chemicals_requiring_permits(
        self,
        state_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get chemicals that require permits."""
        query = self._build_query(
            self.TABLE_NAME,
            self.DEFAULT_COLUMNS
        )
        query = query.not_.is_('RequiredPermits', 'null')

        if state_code:
            query = query.eq('StateCode', state_code)

        return await self.execute_query(query)