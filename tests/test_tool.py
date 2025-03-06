"""Test script for Amazon Connection Tool functions."""

import asyncio
import sys
import argparse
from typing import Dict, Any, List, Optional

from src.react_agent.amazon_connection.tool import (
    search_amazon_products,
    find_deals,
    compare_products,
    find_bestsellers,
    get_product_details,
    get_product_reviews
)

# Define test cases for different tool functions
TEST_CASES = {
    "search_basic": {
        "name": "Basic Product Search",
        "function": "search_amazon_products",
        "params": {
            "query": "bluetooth speaker",
            "max_results": 3
        }
    },

    "search_filtered": {
        "name": "Filtered Product Search",
        "function": "search_amazon_products",
        "params": {
            "query": "wireless earbuds",
            "price_min": "50",
            "price_max": "150",
            "prime_only": True,
            "brand": "Apple, Sony, Samsung",
            "min_rating": 4,
            "sort_by": "review-rank",
            "max_results": 3
        }
    },

    "deals": {
        "name": "Find Deals in Electronics",
        "function": "find_deals",
        "params": {
            "category": "electronics",
            "price_max": "100",
            "prime_only": True,
            "min_rating": 4,
            "max_results": 3
        }
    },

    "bestsellers": {
        "name": "Find Bestsellers in Books",
        "function": "find_bestsellers",
        "params": {
            "category": "books",
            "prime_only": True,
            "max_results": 3
        }
    },

    "product_details": {
        "name": "Get Product Details",
        "function": "get_product_details",
        "params": {
            "product_url": "https://www.amazon.com/dp/B07QDPRYYD"  # Example ASIN for Echo Dot
        }
    },

    "product_reviews": {
        "name": "Get Product Reviews",
        "function": "get_product_reviews",
        "params": {
            "product_url": "https://www.amazon.com/dp/B07QDPRYYD",  # Example ASIN for Echo Dot
            "review_type": "positive",
            "max_reviews": 3
        }
    },

    "compare_products": {
        "name": "Compare Multiple Products",
        "function": "compare_products",
        "params": {
            "product_urls": "https://www.amazon.com/dp/B07QDPRYYD, https://www.amazon.com/dp/B07XJ8C8F5"  # Echo Dot and Echo
        }
    }
}

# Add more specific test cases
TEST_CASES.update({
    "search_features": {
        "name": "Search with Feature Filtering",
        "function": "search_amazon_products",
        "params": {
            "query": "headphones",
            "features": "noise cancelling, wireless, bluetooth",
            "price_min": "50",
            "price_max": "200",
            "prime_only": True,
            "max_results": 3
        }
    },

    "search_department": {
        "name": "Search in Specific Department",
        "function": "search_amazon_products",
        "params": {
            "query": "coffee maker",
            "department": "Kitchen & Dining",
            "price_max": "100",
            "prime_only": True,
            "max_results": 3
        }
    },

    "search_condition": {
        "name": "Search by Product Condition",
        "function": "search_amazon_products",
        "params": {
            "query": "iphone",
            "condition": "renewed",
            "price_max": "400",
            "max_results": 3
        }
    },

    "deals_kitchen": {
        "name": "Find Kitchen Deals",
        "function": "find_deals",
        "params": {
            "category": "kitchen",
            "price_max": "50",
            "prime_only": True,
            "max_results": 3
        }
    }
})

async def run_test_case(case_id: str, config: Dict = None):
    """Run a specific test case by ID."""
    if case_id not in TEST_CASES:
        print(f"Error: Test case '{case_id}' not found.")
        print(f"Available test cases: {', '.join(TEST_CASES.keys())}")
        return

    case = TEST_CASES[case_id]

    # Create a default config if none provided
    if config is None:
        config = {}

    # Remove the 'name' key which is not a parameter
    print(f"\n\n=== RUNNING TEST CASE: {case['name']} ===")

    # Get the function to call
    function_name = case["function"]
    params = case["params"].copy()

    # Add config to params
    params["config"] = config

    # Call the appropriate function
    if function_name == "search_amazon_products":
        result = await search_amazon_products(**params)
    elif function_name == "find_deals":
        result = await find_deals(**params)
    elif function_name == "compare_products":
        result = await compare_products(**params)
    elif function_name == "find_bestsellers":
        result = await find_bestsellers(**params)
    elif function_name == "get_product_details":
        result = await get_product_details(**params)
    elif function_name == "get_product_reviews":
        result = await get_product_reviews(**params)
    else:
        print(f"Error: Unknown function '{function_name}'")
        return

    # Display results
    print(f"\nResults for {case['name']}:")

    if isinstance(result, list):
        print(f"Found {len(result)} items")
        for i, item in enumerate(result):
            print(f"\nItem {i+1}:")
            for key, value in item.items():
                if key == "features" and isinstance(value, list):
                    print(f"  {key}:")
                    for feature in value[:3]:  # Show first 3 features
                        print(f"    - {feature}")
                elif key == "reviews" and isinstance(value, list):
                    print(f"  {key}: {len(value)} reviews")
                    for j, review in enumerate(value[:2]):  # Show first 2 reviews
                        print(f"    Review {j+1}: {review.get('rating', 'N/A')} - {review.get('title', 'No title')}")
                else:
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  {key}: {value}")
    else:
        # For dictionary results
        for key, value in result.items():
            if key == "features" and isinstance(value, list):
                print(f"{key}:")
                for feature in value[:3]:  # Show first 3 features
                    print(f"  - {feature}")
            elif key == "reviews" and isinstance(value, list):
                print(f"{key}: {len(value)} reviews")
                for i, review in enumerate(value[:2]):  # Show first 2 reviews
                    print(f"  Review {i+1}: {review.get('rating', 'N/A')} - {review.get('title', 'No title')}")
            elif key == "products" and isinstance(value, list):
                print(f"{key}: {len(value)} products")
                for i, product in enumerate(value):
                    print(f"  Product {i+1}: {product.get('title', 'Unknown')}")
            else:
                # Truncate long values
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"{key}: {value}")

    return result

async def run_all_test_cases():
    """Run all defined test cases."""
    print("\n\n=== RUNNING ALL TEST CASES ===")
    for case_id in TEST_CASES:
        await run_test_case(case_id)

async def run_custom_search(query, **kwargs):
    """Run a custom search with provided parameters."""
    print(f"\n\n=== CUSTOM SEARCH: {query} ===")

    # Create config
    config = {}

    # Add all parameters to the search
    params = {"query": query, "config": config}
    params.update(kwargs)

    # Run the search
    result = await search_amazon_products(**params)

    # Display results
    print(f"\nSearch results for '{query}':")
    print(f"Found {len(result)} items")

    for i, item in enumerate(result):
        print(f"\nItem {i+1}:")
        for key, value in item.items():
            # Truncate long values
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"  {key}: {value}")

    return result

def print_help():
    """Print help information about available test cases."""
    print("\nAmazon Connection Tool Tester")
    print("----------------------------")
    print("Usage:")
    print("  python -m src.react_agent.amazon_connection.test_tool [options]")
    print("\nOptions:")
    print("  --help                 Show this help message")
    print("  --list                 List all available test cases")
    print("  --test <case_id>       Run a specific test case")
    print("  --all                  Run all test cases")
    print("  --search <query>       Run a custom search with optional parameters")
    print("\nAdditional search parameters (with --search):")
    print("  --price_min <value>    Minimum price")
    print("  --price_max <value>    Maximum price")
    print("  --prime_only           Only show Prime eligible items")
    print("  --brand <brands>       Comma-separated list of brands")
    print("  --min_rating <1-5>     Minimum star rating")
    print("  --department <dept>    Department/category name")
    print("  --features <features>  Comma-separated list of features")
    print("  --sort_by <method>     Sort method (price-asc, price-desc, review-rank)")
    print("  --max_results <num>    Maximum number of results to return")
    print("\nAvailable test cases:")
    for case_id, case in TEST_CASES.items():
        print(f"  {case_id}: {case['name']}")

async def main():
    """Run Amazon Connection Tool tests."""
    parser = argparse.ArgumentParser(description="Test Amazon Connection Tool functions")
    parser.add_argument("--list", action="store_true", help="List all available test cases")
    parser.add_argument("--test", type=str, help="Run a specific test case")
    parser.add_argument("--all", action="store_true", help="Run all test cases")
    parser.add_argument("--search", type=str, help="Run a custom search with optional parameters")

    # Additional search parameters
    parser.add_argument("--price_min", type=str, help="Minimum price")
    parser.add_argument("--price_max", type=str, help="Maximum price")
    parser.add_argument("--prime_only", action="store_true", help="Only show Prime eligible items")
    parser.add_argument("--brand", type=str, help="Comma-separated list of brands")
    parser.add_argument("--min_rating", type=int, help="Minimum star rating (1-5)")
    parser.add_argument("--department", type=str, help="Department/category name")
    parser.add_argument("--features", type=str, help="Comma-separated list of features")
    parser.add_argument("--sort_by", type=str, help="Sort method (price-asc, price-desc, review-rank)")
    parser.add_argument("--max_results", type=int, default=5, help="Maximum number of results to return")

    # Parse arguments
    args = parser.parse_args()

    if len(sys.argv) == 1:
        print_help()
        return

    if args.list:
        print("Available test cases:")
        for case_id, case in TEST_CASES.items():
            print(f"  {case_id}: {case['name']}")
        return

    if args.test:
        await run_test_case(args.test)
        return

    if args.all:
        await run_all_test_cases()
        return

    if args.search:
        # Collect all search parameters
        search_params = {}
        if args.price_min:
            search_params["price_min"] = args.price_min
        if args.price_max:
            search_params["price_max"] = args.price_max
        if args.prime_only:
            search_params["prime_only"] = True
        if args.brand:
            search_params["brand"] = args.brand
        if args.min_rating:
            search_params["min_rating"] = args.min_rating
        if args.department:
            search_params["department"] = args.department
        if args.features:
            search_params["features"] = args.features
        if args.sort_by:
            search_params["sort_by"] = args.sort_by
        if args.max_results:
            search_params["max_results"] = args.max_results

        await run_custom_search(args.search, **search_params)
        return

    # Default behavior: run the basic search test
    await run_test_case("search_basic")

if __name__ == "__main__":
    asyncio.run(main())