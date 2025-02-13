"""Chemical compliance query tools."""

from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.configuration import Configuration
from react_agent.tools.database.compliance import ChemicalComplianceDB

logger = logging.getLogger(__name__)

async def get_chemical_compliance(
    chemical_id: int,
    state_code: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get compliance information for a chemical.

    Args:
        chemical_id: ID of the chemical
        state_code: Optional state code to filter by
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalComplianceDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_compliance_by_chemical(chemical_id, state_code)

async def get_restricted_chemicals(
    state_code: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get list of restricted chemicals.

    Args:
        state_code: Optional state code to filter by
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalComplianceDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_restricted_chemicals(state_code)

async def get_state_requirements(
    state_code: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get all compliance requirements for a state.

    Args:
        state_code: State code to get requirements for
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalComplianceDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_state_requirements(state_code)

async def get_chemicals_requiring_permits(
    state_code: Optional[str] = None,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Get chemicals that require permits.

    Args:
        state_code: Optional state code to filter by
    """
    configuration = Configuration.from_runnable_config(config)
    db = ChemicalComplianceDB(configuration.supabase_url, configuration.supabase_key)
    return await db.get_chemicals_requiring_permits(state_code)

# List of available compliance tools
COMPLIANCE_TOOLS = [
    get_chemical_compliance,
    get_restricted_chemicals,
    get_state_requirements,
    get_chemicals_requiring_permits
]