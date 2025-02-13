"""Test catalog query functions."""

import pytest
from react_agent.tools.queries.catalog import (
    search_chemicals,
    search_by_criteria,
    search_by_date_range,
    get_discontinued_products,
    get_products_by_subcategory,
    get_statistics,
    get_chemical_details
)

@pytest.mark.asyncio
async def test_search_chemicals(config):
    """Test chemical search."""
    # Test with a known chemical name that exists in database
    results = await search_chemicals("Titanium dioxide", config=config)
    assert isinstance(results, list)
    assert len(results) > 0, "Should find at least one result for Titanium dioxide"
    assert any('titanium dioxide' in result['ChemicalName'].lower()
              for result in results)

    # Test with CAS number
    results = await search_chemicals("13463-67-7", config=config)  # CAS for Titanium dioxide
    assert len(results) > 0, "Should find results for Titanium dioxide CAS"

    # Test with non-existent chemical
    results = await search_chemicals("NonExistentChemical12345", config=config)
    assert len(results) == 0, "Should return empty list for non-existent chemical"

@pytest.mark.asyncio
async def test_search_by_criteria(config):
    """Test criteria search."""
    # Test with known CAS number
    results = await search_by_criteria(
        cas_number="13463-67-7",  # CAS number for Titanium dioxide
        config=config
    )
    assert len(results) > 0, "Should find results for Titanium dioxide CAS number"
    assert results[0]['CasNumber'] == "13463-67-7"

    # Test with chemical name
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find results for Titanium dioxide"
    assert any('titanium dioxide' in result['ChemicalName'].lower()
              for result in results)

    # Store a ChemicalId for later tests
    chemical_id = results[0]['ChemicalId']

    # Test with multiple criteria
    results = await search_by_criteria(
        cas_number="13463-67-7",
        chemical_name="Titanium dioxide",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert results[0]['CasNumber'] == "13463-67-7"
        assert 'titanium dioxide' in results[0]['ChemicalName'].lower()

@pytest.mark.asyncio
async def test_search_by_date_range(config):
    """Test date range search."""
    results = await search_by_date_range(
        start_date="2020-01-01",
        end_date="2023-12-31",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'InitialDateReported' in results[0]

@pytest.mark.asyncio
async def test_get_discontinued_products(config):
    """Test discontinued products query."""
    results = await get_discontinued_products(
        before_date="2023-12-31",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'DiscontinuedDate' in results[0]

@pytest.mark.asyncio
async def test_get_products_by_subcategory(config):
    """Test subcategory query."""
    results = await get_products_by_subcategory(
        subcategory="Test Category",
        config=config
    )
    assert isinstance(results, list)
    if results:
        assert 'SubCategory' in results[0]

@pytest.mark.asyncio
async def test_get_statistics(config):
    """Test statistics query."""
    results = await get_statistics(config=config)
    assert isinstance(results, dict)

@pytest.mark.asyncio
async def test_get_chemical_details(config):
    """Test chemical details query."""
    # First get a valid chemical ID
    results = await search_by_criteria(
        chemical_name="Titanium dioxide",
        config=config
    )
    assert len(results) > 0, "Should find Titanium dioxide to get its ID"
    chemical_id = results[0]['ChemicalId']

    # Now test get_chemical_details
    details = await get_chemical_details(
        chemical_id=chemical_id,
        config=config
    )
    assert isinstance(details, list)
    assert len(details) > 0, "Should find details for the chemical"
    assert details[0]['ChemicalId'] == chemical_id
    assert 'titanium dioxide' in details[0]['ChemicalName'].lower()