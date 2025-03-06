"""Amazon search tool for the React Agent."""

from typing import Any, Dict, List, Optional, Union
from typing_extensions import Annotated
from langchain_core.tools import InjectedToolArg
from langchain_core.runnables import RunnableConfig
import logging

from react_agent.amazon_connection.main import AmazonConnection, search_amazon

logger = logging.getLogger(__name__)

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
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Search for products on Amazon with comprehensive filtering options.

    Args:
        query: The search query for products
        price_min: Minimum price (e.g. "10.99")
        price_max: Maximum price (e.g. "99.99")
        prime_only: Only show Prime eligible items
        free_shipping: Only show items with free shipping
        max_delivery_days: Maximum delivery days (e.g. 2 for two-day shipping)
        availability: Availability status (e.g. "in_stock")
        brand: Brand name or comma-separated list of brands
        seller: Specific seller name
        min_rating: Minimum star rating (1-5)
        customer_reviews: Filter by review type ("positive" or "critical")
        discount_only: Only show discounted items
        deals: Only show deals
        condition: Product condition ("new", "used", "renewed", "refurbished")
        department: Department/category name
        category: Simplified category name (e.g. "electronics", "home", "beauty")
        color: Product color
        size: Product size
        material: Product material
        features: Comma-separated list of product features to filter by
        sort_by: Sort method ("featured", "price-asc", "price-desc", "review-rank", "newest")
        max_results: Maximum number of results to return

    Returns:
        List of product information including title, price, rating, and URL
    """
    logger.info(f"Searching Amazon for: {query}")

    # Process brand parameter if it's a comma-separated string
    brand_param = None
    if brand:
        if "," in brand:
            brand_param = [b.strip() for b in brand.split(",")]
        else:
            brand_param = brand

    # Process features if it's a comma-separated string
    features_param = None
    if features:
        features_param = [f.strip() for f in features.split(",")]

    # Build filters dictionary
    filters = {}

    # Add all non-None parameters to filters
    locals_copy = locals().copy()
    for param, value in locals_copy.items():
        if param not in ['query', 'filters', 'max_results', 'config', 'brand', 'features',
                         'brand_param', 'features_param', 'locals_copy']:
            if value is not None and not (isinstance(value, bool) and value is False):
                filters[param] = value

    # Add processed parameters
    if brand_param:
        filters["brand"] = brand_param
    if features_param:
        filters["features"] = features_param

    try:
        # Run the search in headless mode
        products = await search_amazon(query, filters)

        # Format the results
        formatted_results = []
        for product in products[:max_results]:
            formatted_product = {
                "title": product.get("title", "Unknown"),
                "price": product.get("price", "N/A"),
                "url": product.get("url", ""),
                "asin": product.get("asin", ""),
                "prime_eligible": product.get("prime_eligible", False)
            }

            # Add rating if available
            if "rating" in product:
                formatted_product["rating"] = product["rating"]

            # Add review count if available
            if "review_count" in product:
                formatted_product["review_count"] = product["review_count"]

            formatted_results.append(formatted_product)

        logger.info(f"Found {len(formatted_results)} products for query: {query}")
        return formatted_results

    except Exception as e:
        logger.error(f"Error searching Amazon: {str(e)}")
        return [{"error": f"Failed to search Amazon: {str(e)}"}]

async def find_deals(
    category: str,
    *,
    price_max: Optional[str] = None,
    prime_only: bool = True,
    min_rating: Optional[int] = 4,
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find current deals and discounts on Amazon in a specific category.

    Args:
        category: Product category (e.g. "electronics", "home", "kitchen")
        price_max: Maximum price (e.g. "99.99")
        prime_only: Only show Prime eligible items
        min_rating: Minimum star rating (1-5)
        max_results: Maximum number of results to return

    Returns:
        List of deal products with price, rating, and discount information
    """
    logger.info(f"Finding deals in category: {category}")

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

    try:
        # Run the search in headless mode
        products = await search_amazon(category, filters)

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

    except Exception as e:
        logger.error(f"Error finding deals: {str(e)}")
        return [{"error": f"Failed to find deals: {str(e)}"}]

async def compare_products(
    product_urls: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Compare multiple Amazon products side by side.

    Args:
        product_urls: Comma-separated list of Amazon product URLs to compare

    Returns:
        Comparison of products with key features, prices, and ratings
    """
    logger.info(f"Comparing products")

    # Split URLs
    urls = [url.strip() for url in product_urls.split(",")]
    if len(urls) < 2:
        return {"error": "Please provide at least two product URLs to compare"}

    if len(urls) > 5:
        urls = urls[:5]  # Limit to 5 products for comparison

    try:
        products = []
        async with AmazonConnection(headless=True) as amazon:
            for url in urls:
                details = await amazon.get_product_details(url)
                if details:
                    products.append({
                        "title": details.get("title", "Unknown"),
                        "price": details.get("price", "N/A"),
                        "rating": details.get("rating", "N/A"),
                        "prime_eligible": details.get("prime_eligible", False),
                        "features": details.get("features", [])[:3],  # Top 3 features
                        "url": url
                    })

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

    except Exception as e:
        logger.error(f"Error comparing products: {str(e)}")
        return {"error": f"Failed to compare products: {str(e)}"}

async def find_bestsellers(
    category: str,
    *,
    prime_only: bool = False,
    max_results: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> List[Dict[str, Any]]:
    """Find bestselling products in a specific category on Amazon.

    Args:
        category: Product category (e.g. "electronics", "books", "toys")
        prime_only: Only show Prime eligible items
        max_results: Maximum number of results to return

    Returns:
        List of bestselling products in the specified category
    """
    logger.info(f"Finding bestsellers in category: {category}")

    # Build filters for bestseller search
    filters = {
        "category": category,
        "prime_only": prime_only,
        "sort_by": "review-rank",
        "min_rating": 4
    }

    try:
        # Run the search in headless mode
        products = await search_amazon(f"best {category}", filters)

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

    except Exception as e:
        logger.error(f"Error finding bestsellers: {str(e)}")
        return [{"error": f"Failed to find bestsellers: {str(e)}"}]

async def get_product_details(
    product_url: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get detailed information about a specific Amazon product.

    Args:
        product_url: The URL of the Amazon product

    Returns:
        Detailed product information including features, specifications, and reviews
    """
    logger.info(f"Getting details for product: {product_url}")

    try:
        async with AmazonConnection(headless=True) as amazon:
            details = await amazon.get_product_details(product_url)
            reviews = await amazon.get_product_reviews(product_url)

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

    except Exception as e:
        logger.error(f"Error getting product details: {str(e)}")
        return {"error": f"Failed to get product details: {str(e)}"}

async def get_product_reviews(
    product_url: str,
    *,
    review_type: Optional[str] = None,
    max_reviews: int = 5,
    config: Annotated[RunnableConfig, InjectedToolArg]
) -> Dict[str, Any]:
    """Get customer reviews for a specific Amazon product.

    Args:
        product_url: The URL of the Amazon product
        review_type: Type of reviews to get ("positive", "critical", or None for all)
        max_reviews: Maximum number of reviews to return

    Returns:
        Product reviews with ratings, titles, and content
    """
    logger.info(f"Getting reviews for product: {product_url}")

    try:
        async with AmazonConnection(headless=True) as amazon:
            details = await amazon.get_product_details(product_url)
            all_reviews = await amazon.get_product_reviews(product_url)

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

    except Exception as e:
        logger.error(f"Error getting product reviews: {str(e)}")
        return {"error": f"Failed to get product reviews: {str(e)}"}

# List of available Amazon tools
AMAZON_TOOLS = [
    search_amazon_products,
    find_deals,
    compare_products,
    find_bestsellers,
    get_product_details,
    get_product_reviews
]
