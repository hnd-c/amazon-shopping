"""Test compliance query functions."""

import pytest
from react_agent.tools.queries.compliance import (
    get_chemical_compliance,
    get_restricted_chemicals,
    get_state_requirements,
    get_chemicals_requiring_permits
)
from react_agent.tools.queries.catalog import search_by_criteria

@pytest.mark.asyncio
async def test_get_chemical_compliance(config):
    """Test compliance query."""
    # First get a valid chemical ID for Titanium dioxide
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find Titanium dioxide to get its ID"
    chemical_id = results[0]['ChemicalId']

    # Test compliance for specific state
    results = await get_chemical_compliance(
        chemical_id=chemical_id,
        state_code="CA",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'IsRestricted' in results[0]
        assert 'StateCode' in results[0]
        assert results[0]['ChemicalId'] == chemical_id

@pytest.mark.asyncio
async def test_get_restricted_chemicals(config):
    """Test restricted chemicals query."""
    results = await get_restricted_chemicals(
        state_code="CA",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'IsRestricted' in results[0]
        assert results[0]['IsRestricted'] is True
        assert results[0]['StateCode'] == "CA"

@pytest.mark.asyncio
async def test_get_state_requirements(config):
    """Test state requirements query."""
    results = await get_state_requirements(
        state_code="CA",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'StateCode' in results[0]
        assert 'RequiredPermits' in results[0]
        assert results[0]['StateCode'] == "CA"

@pytest.mark.asyncio
async def test_get_chemicals_requiring_permits(config):
    """Test permit requirements query."""
    results = await get_chemicals_requiring_permits(
        state_code="CA",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'RequiredPermits' in results[0]