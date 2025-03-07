"""Amazon search tool for the React Agent."""

import asyncio
from typing import Any, Dict, List, Optional, Union
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging
from functools import wraps

from .main import AmazonConnection, browser_pool
from .utils import ProductInfo, ErrorResponse, create_error_response, with_retry, SELECTORS, RateLimiter, BrowserContextManager

logger = logging.getLogger(__name__)

# Create a global rate limiter instance
rate_limiter = RateLimiter()

# Define the amazon_tool decorator BEFORE using it
def amazon_tool(func):
    """Decorator for Amazon tool functions to handle common patterns."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract config from kwargs
        config = kwargs.get("config", {})

        # Use the browser context manager with the global rate_limiter
        async with BrowserContextManager(config, rate_limiter) as browser:
            # Add browser to kwargs for the function to use
            kwargs["browser"] = browser
            return await func(*args, **kwargs)

    return wrapper

# Apply the retry decorator to all tool functions
@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def search_amazon_products(
    query: str,
    *,
    # Price filters
    price_min: Optional[str] = None,
    price_max: Optional[str] = None,
    # Shipping and availability filters
    prime_only: bool = False,
    free_shipping: bool = False,
    max_delivery_days: Optional[int] = None,
    availability: Optional[str] = None,
    # Brand and seller filters
    brand: Optional[str] = None,
    seller: Optional[str] = None,
    # Rating and review filters
    min_rating: Optional[int] = None,
    customer_reviews: Optional[str] = None,
    # Deal filters
    discount_only: bool = False,
    deals: bool = False,
    # Product attribute filters
    condition: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    material: Optional[str] = None,
    features: Optional[str] = None,
    # Sorting and display
    sort_by: Optional[str] = "review-rank",
    max_results: int = 5,
    browser: Optional[Any] = None,  # Added by decorator
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[List[ProductInfo], ErrorResponse]:
    """Search for products on Amazon with comprehensive filtering options."""
    try:
        # Build filters dictionary
        filters = {}
        locals_copy = locals().copy()
        for param, value in locals_copy.items():
            if param not in ['query', 'filters', 'max_results', 'config', 'browser', 'locals_copy']:
                if value is not None and not (isinstance(value, bool) and value is False):
                    filters[param] = value

        # Process special parameters
        if brand and isinstance(brand, str) and "," in brand:
            filters["brand"] = [b.strip() for b in brand.split(",")]

        if features and isinstance(features, str) and "," in features:
            filters["features"] = [f.strip() for f in features.split(",")]

        # Execute search
        logger.info(f"Searching Amazon for: {query}")
        products = await browser.search_products(query)

        if filters:
            logger.info(f"Applying filters: {filters}")
            products = await browser.apply_filters(filters)

        # Format results
        formatted_results = []
        for product in products[:max_results]:
            formatted_product = {
                "title": product.get("title", "Unknown"),
                "price": product.get("price", "N/A"),
                "url": product.get("url", ""),
                "asin": product.get("asin", ""),
                "prime_eligible": product.get("prime_eligible", False)
            }

            # Add optional fields if available
            for field in ["rating", "review_count", "availability", "delivery_info"]:
                if field in product:
                    formatted_product[field] = product[field]

            formatted_results.append(formatted_product)

        logger.info(f"Found {len(formatted_results)} products for query: {query}")
        return formatted_results

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def find_deals(
    category: str,
    *,
    price_max: Optional[str] = None,
    prime_only: bool = True,
    min_rating: Optional[int] = 4,
    max_results: int = 5,
    browser: Optional[Any] = None,  # Added browser parameter
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Find current deals and discounts on Amazon in a specific category."""
    try:
        # Build filters for deals search
        filters = {
            "deals": True,
            "discount_only": True,
            "category": category,
            "prime_only": prime_only,
            "sort_by": "price-asc"
        }

        if price_max:
            filters["price_max"] = price_max
        if min_rating:
            filters["min_rating"] = min_rating

        # Execute search
        logger.info(f"Searching Amazon deals for: {category}")
        products = await browser.search_products(category)

        if filters:
            logger.info(f"Applying filters: {filters}")
            products = await browser.apply_filters(filters)

        # Format the results
        formatted_results = []
        for product in products[:max_results]:
            formatted_product = {
                "title": product.get("title", "Unknown"),
                "price": product.get("price", "N/A"),
                "url": product.get("url", ""),
                "prime_eligible": product.get("prime_eligible", False),
                "deal_type": "Discount/Deal"
            }

            # Add rating if available
            if "rating" in product:
                formatted_product["rating"] = product["rating"]

            formatted_results.append(formatted_product)

        logger.info(f"Found {len(formatted_results)} deals in category: {category}")
        return formatted_results

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def compare_products(
    product_urls: str,
    *,
    browser: Optional[Any] = None,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[Dict[str, Any], ErrorResponse]:
    """Compare multiple Amazon products side by side."""
    try:
        logger.info(f"Comparing products")

        # Split URLs
        urls = [url.strip() for url in product_urls.split(",")]
        if len(urls) < 2:
            return create_error_response("Please provide at least two product URLs to compare")

        if len(urls) > 5:
            urls = urls[:5]  # Limit to 5 products for comparison

        # Fetch product details concurrently
        async def fetch_product(url):
            # Remove redundant rate limiter wait - the decorator already handles this
            return await browser.get_product_details(url)

        # Use gather to run requests in parallel
        product_details = await asyncio.gather(
            *[fetch_product(url) for url in urls],
            return_exceptions=True
        )

        products = []
        for i, details in enumerate(product_details):
            if isinstance(details, Exception):
                logger.warning(f"Error fetching product {i+1}: {str(details)}")
                continue

            if details:
                products.append({
                    "title": details.get("title", "Unknown"),
                    "price": details.get("price", "N/A"),
                    "rating": details.get("rating", "N/A"),
                    "prime_eligible": details.get("prime_eligible", False),
                    "features": details.get("features", [])[:3],  # Top 3 features
                    "url": urls[i]
                })

        if not products:
            return create_error_response("Could not retrieve any product details to compare")

        # Create comparison result
        comparison = {
            "products": products,
            "comparison_summary": {
                "price_range": f"{min([p.get('price', '$0') for p in products])} - {max([p.get('price', '$0') for p in products])}",
                "highest_rated": max(products, key=lambda x: float(x.get("rating", "0").split()[0]) if x.get("rating") else 0).get("title"),
                "total_compared": len(products)
            }
        }

        return comparison

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def find_bestsellers(
    category: str,
    *,
    prime_only: bool = False,
    max_results: int = 5,
    browser: Optional[Any] = None,  # Add browser parameter
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[List[Dict[str, Any]], ErrorResponse]:
    """Find bestselling products in a specific category on Amazon."""
    try:
        logger.info(f"Finding bestsellers in category: {category}")

        # Build filters for bestseller search
        filters = {
            "category": category,
            "prime_only": prime_only,
            "sort_by": "review-rank",
            "min_rating": 4
        }

        # Execute search
        logger.info(f"Searching Amazon bestsellers for: {category}")
        products = await browser.search_products(f"best {category}")

        if filters:
            logger.info(f"Applying filters: {filters}")
            products = await browser.apply_filters(filters)

        # Format the results
        formatted_results = []
        for product in products[:max_results]:
            formatted_product = {
                "title": product.get("title", "Unknown"),
                "price": product.get("price", "N/A"),
                "url": product.get("url", ""),
                "rating": product.get("rating", "N/A"),
                "prime_eligible": product.get("prime_eligible", False),
                "bestseller_rank": f"#{len(formatted_results)+1} in {category}"
            }

            formatted_results.append(formatted_product)

        logger.info(f"Found {len(formatted_results)} bestsellers in category: {category}")
        return formatted_results

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def get_product_details(
    product_url: str,
    *,
    browser: Optional[Any] = None,  # Add browser parameter
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[Dict[str, Any], ErrorResponse]:
    """Get detailed information about a specific Amazon product."""
    try:
        logger.info(f"Getting details for product: {product_url}")

        logger.info(f"Fetching product details")
        details = await browser.get_product_details(product_url)

        # Wait for rate limiter before getting reviews
        await rate_limiter.wait()
        reviews = await browser.get_product_reviews(product_url)

        # Format the response
        result = {
            "title": details.get("title", "Unknown"),
            "price": details.get("price", "N/A"),
            "rating": details.get("rating", "N/A"),
            "prime_eligible": details.get("prime_eligible", False),
            "availability": details.get("availability", "Unknown")
        }

        # Add delivery info if available
        if "delivery_info" in details:
            result["delivery_info"] = details["delivery_info"]

        # Add description if available
        if "description" in details and details["description"]:
            result["description"] = details["description"]

        # Add features if available
        if "features" in details and details["features"]:
            result["features"] = details["features"][:5]  # Limit to top 5 features

        # Add specifications if available
        if "specifications" in details and details["specifications"]:
            result["specifications"] = details["specifications"]

        # Add reviews if available
        if reviews:
            result["reviews"] = []
            for review in reviews[:3]:  # Limit to top 3 reviews
                result["reviews"].append({
                    "rating": review.get("rating", "N/A"),
                    "title": review.get("title", ""),
                    "date": review.get("date", ""),
                    "verified_purchase": review.get("verified_purchase", False),
                    "content": review.get("content", "")[:200]  # Limit content length
                })

        return result

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

@with_retry(max_retries=3, retry_delay=2)
@amazon_tool
async def get_product_reviews(
    product_url: str,
    *,
    review_type: Optional[str] = None,
    max_reviews: int = 5,
    browser: Optional[Any] = None,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Union[Dict[str, Any], ErrorResponse]:
    """Get customer reviews for a specific Amazon product."""
    try:
        logger.info(f"Getting reviews for product: {product_url}")

        logger.info(f"Fetching product details")
        details = await browser.get_product_details(product_url)

        # Remove redundant rate limiter wait - the decorator already handles this
        all_reviews = await browser.get_product_reviews(product_url)

        # Filter reviews if review_type is specified
        filtered_reviews = all_reviews
        if review_type and all_reviews:
            if review_type.lower() == "positive":
                filtered_reviews = [r for r in all_reviews if r.get("rating", "").startswith(("4", "5"))]
            elif review_type.lower() == "critical":
                filtered_reviews = [r for r in all_reviews if r.get("rating", "").startswith(("1", "2", "3"))]

        # Format the response
        result = {
            "product_title": details.get("title", "Unknown"),
            "overall_rating": details.get("rating", "N/A"),
            "total_reviews": len(all_reviews),
            "reviews": []
        }

        # Add reviews
        for review in filtered_reviews[:max_reviews]:
            result["reviews"].append({
                "rating": review.get("rating", "N/A"),
                "title": review.get("title", ""),
                "date": review.get("date", ""),
                "verified_purchase": review.get("verified_purchase", False),
                "content": review.get("content", ""),
                "helpful_votes": review.get("helpful_votes", "0")
            })

        return result

    finally:
        # Only close the browser if we're not in a chain of Amazon tool calls
        if not config.get("keep_browser_open"):
            await browser_pool.close_browser_if_created(config)

# List of available Amazon tools
AMAZON_TOOLS = [
    search_amazon_products,
    find_deals,
    compare_products,
    find_bestsellers,
    get_product_details,
    get_product_reviews
]


