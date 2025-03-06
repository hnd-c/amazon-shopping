import asyncio
import sys
from typing import Dict, Any, List, Optional

from .main import search_amazon, AmazonConnection

# Define test cases as a dictionary for easy selection and modification
TEST_CASES = {
    "bluetooth_speaker": {
        "name": "Bluetooth Speaker Search",
        "query": "bluetooth speaker",
        "price_min": "30",
        "price_max": "100",
        "prime_only": True,
        "brand": "JBL",
        "min_rating": 4,
        "condition": "new",
        "sort_by": "review-rank",
    },

    "wireless_earbuds": {
        "name": "Premium Wireless Earbuds",
        "query": "wireless earbuds",
        "price_min": "50",
        "price_max": "150",
        "prime_only": True,
        "free_shipping": True,
        "brand": ["Apple", "Samsung", "Sony"],
        "min_rating": 4,
        "condition": "new",
        "features": ["noise cancelling", "waterproof"],
        "sort_by": "review-rank",
        "max_display": 5,
    },

    "kitchen_towels": {
        "name": "Budget Kitchen Towels",
        "query": "kitchen towels",
        "price_max": "15",
        "prime_only": True,
        "max_delivery_days": 2,
        "discount_only": True,
        "min_rating": 3,
        "department": "Home & Kitchen",
        "sort_by": "price-asc",
        "max_display": 4,
    },

    "leather_wallet": {
        "name": "Luxury Leather Wallets",
        "query": "leather wallet",
        "price_min": "100",
        "brand": ["Coach", "Michael Kors", "Gucci"],
        "condition": "new",
        "material": "genuine leather",
        "color": "black",
        "customer_reviews": "positive",
        "sort_by": "price-desc",
        "max_display": 3,
    },

    "laptop_deals": {
        "name": "Laptop Deals",
        "query": "laptop",
        "price_min": "500",
        "price_max": "1200",
        "deals": True,
        "price_drops": True,
        "min_rating": 4,
        "features": ["SSD", "16GB RAM"],
        "availability": "in_stock",
        "sort_by": "review-rank",
        "max_display": 5,
    },

    "organic_tea": {
        "name": "Specialty Organic Tea",
        "query": "organic tea",
        "seller": "Teavana",
        "prime_only": True,
        "min_rating": 4,
        "department": "Grocery",
        "features": ["loose leaf", "organic certified"],
        "sort_by": "newest",
        "max_display": 4,
    },

    "womens_gifts": {
        "name": "Women's Gift Ideas",
        "query": "birthday gift for women",
        "price_min": "25",
        "price_max": "75",
        "prime_only": True,
        "free_shipping": True,
        "min_rating": 4,
        "condition": "new",
        "department": "Beauty & Personal Care",
        "sort_by": "review-rank",
        "max_display": 6,
    }
}

# Add these new test cases to the TEST_CASES dictionary

TEST_CASES.update({
    "bluetooth_headphones": {
        "name": "Multi-Brand Electronics",
        "query": "bluetooth headphones",
        "price_min": "30",
        "price_max": "100",
        "prime_only": True,
        "brand": ["Sony", "JBL", "Anker"],
        "min_rating": 3,
        "sort_by": "price-asc",
        "max_display": 5,
    },

    "running_shoes": {
        "name": "Discount Shopping with Price Drops",
        "query": "running shoes",
        "price_min": "40",
        "price_max": "80",
        "discount_only": True,
        "price_drops": True,
        "prime_only": True,
        "min_rating": 4,
        "department": "Fashion",
        "sort_by": "price-asc",
        "max_display": 4,
    },

    "renewed_iphone": {
        "name": "Specific Product Condition",
        "query": "iphone",
        "price_min": "200",
        "price_max": "400",
        "condition": "renewed",
        "prime_only": True,
        "min_rating": 3,
        "sort_by": "price-asc",
        "max_display": 3,
    },

    "gift_basket": {
        "name": "Fast Shipping Priority",
        "query": "gift basket",
        "price_max": "50",
        "max_delivery_days": 2,
        "free_shipping": True,
        "prime_only": True,
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "cotton_sheets": {
        "name": "Material and Color Specific",
        "query": "cotton sheets",
        "price_min": "30",
        "price_max": "100",
        "material": "egyptian cotton",
        "color": "white",
        "prime_only": True,
        "min_rating": 4,
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "coffee_maker": {
        "name": "Department with Features",
        "query": "coffee maker",
        "price_min": "50",
        "price_max": "150",
        "department": "Kitchen & Dining",
        "features": ["programmable", "stainless steel"],
        "prime_only": True,
        "min_rating": 4,
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "face_moisturizer": {
        "name": "Customer Reviews Focus",
        "query": "face moisturizer",
        "price_min": "15",
        "price_max": "40",
        "customer_reviews": "positive",
        "department": "Beauty & Personal Care",
        "prime_only": True,
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "switch_games": {
        "name": "Availability with Deals",
        "query": "nintendo switch games",
        "price_max": "40",
        "availability": "in_stock",
        "deals": True,
        "prime_only": True,
        "sort_by": "price-asc",
        "max_display": 3,
    },

    "amazon_vitamins": {
        "name": "Specific Seller with Brand",
        "query": "vitamins",
        "seller": "Amazon",
        "brand": "Amazon Elements",
        "prime_only": True,
        "min_rating": 4,
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "water_bottle": {
        "name": "Maximum Filter Combination",
        "query": "water bottle",
        "price_min": "20",
        "price_max": "50",
        "prime_only": True,
        "free_shipping": True,
        "brand": "Hydro Flask",
        "min_rating": 4,
        "condition": "new",
        "material": "stainless steel",
        "color": "black",
        "features": ["insulated", "leak proof"],
        "department": "Sports & Outdoors",
        "sort_by": "review-rank",
        "max_display": 3,
    },

    "mens_tshirt": {
        "name": "Size Filter with Department",
        "query": "men's t-shirt",
        "price_max": "25",
        "size": "large",
        "department": "Clothing, Shoes & Jewelry",
        "prime_only": True,
        "discount_only": True,
        "sort_by": "price-asc",
        "max_display": 3,
    },

    "toys_deals": {
        "name": "Deals with Department",
        "query": "toys",
        "price_max": "30",
        "deals": True,
        "department": "Toys & Games",
        "prime_only": True,
        "min_rating": 4,
        "sort_by": "price-asc",
        "max_display": 3,
    }
})

# Add these constants at the top of the file for better category filtering

# Define more specific category mappings
CATEGORY_MAPPINGS = {
    # Electronics categories
    "electronics": "Electronics",
    "computers": "Computers & Accessories",
    "cell_phones": "Cell Phones & Accessories",
    "camera": "Camera & Photo",
    "audio": "Headphones & Speakers",
    "tv_video": "TV & Video",

    # Home categories
    "home": "Home & Kitchen",
    "kitchen": "Kitchen & Dining",
    "furniture": "Furniture",
    "bedding": "Bedding",
    "bath": "Bath",
    "appliances": "Appliances",

    # Clothing categories
    "clothing": "Clothing, Shoes & Jewelry",
    "mens_clothing": "Men's Clothing",
    "womens_clothing": "Women's Clothing",
    "kids_clothing": "Kids' Clothing",
    "shoes": "Shoes",
    "jewelry": "Jewelry",

    # Beauty categories
    "beauty": "Beauty & Personal Care",
    "skincare": "Skin Care",
    "haircare": "Hair Care",
    "makeup": "Makeup",
    "fragrance": "Fragrance",

    # Other popular categories
    "books": "Books",
    "toys": "Toys & Games",
    "sports": "Sports & Outdoors",
    "grocery": "Grocery & Gourmet Food",
    "health": "Health & Household",
    "pet_supplies": "Pet Supplies",
    "automotive": "Automotive",
    "office": "Office Products",
    "baby": "Baby",
    "tools": "Tools & Home Improvement",
}

async def amazon_search(
    query: str = "soap",
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
    price_drops: bool = False,
    deals: bool = False,
    # Product attribute filters
    condition: Optional[str] = None,
    department: Optional[str] = None,
    category: Optional[str] = None,  # New parameter for more specific categories
    color: Optional[str] = None,
    size: Optional[str] = None,
    material: Optional[str] = None,
    features: Optional[List[str]] = None,
    # Sorting
    sort_by: Optional[str] = None,
    # Display options
    max_display: int = 3,
    get_details: bool = True,
    headless: bool = False
):
    """Comprehensive Amazon search function with all available filters and improved error handling."""
    # Build filters dictionary from provided parameters
    filters = {}

    # Add all non-None parameters to filters
    locals_copy = locals().copy()
    for param, value in locals_copy.items():
        if param not in ['query', 'filters', 'max_display', 'get_details', 'headless', 'category'] and value is not None:
            if isinstance(value, bool) and value is False:
                continue
            filters[param] = value

    # Handle category mapping
    if category and category in CATEGORY_MAPPINGS:
        filters['department'] = CATEGORY_MAPPINGS[category]
    elif category:
        print(f"Warning: Unknown category '{category}'. Using as-is.")
        filters['department'] = category

    # Validate filters
    invalid_filters = []

    # Validate rating
    if min_rating is not None and (min_rating < 1 or min_rating > 5):
        invalid_filters.append(f"min_rating must be between 1 and 5, got {min_rating}")

    # Validate customer_reviews
    if customer_reviews is not None and customer_reviews.lower() not in ['positive', 'critical']:
        invalid_filters.append(f"customer_reviews must be 'positive' or 'critical', got {customer_reviews}")

    # Validate condition
    valid_conditions = ['new', 'used', 'renewed', 'refurbished']
    if condition is not None and condition.lower() not in valid_conditions:
        invalid_filters.append(f"condition must be one of {valid_conditions}, got {condition}")

    # Validate availability
    valid_availability = ['in_stock']
    if availability is not None and availability.lower() not in valid_availability:
        invalid_filters.append(f"availability must be one of {valid_availability}, got {availability}")

    # Validate sort_by
    valid_sort = ['featured', 'price-asc', 'price-desc', 'review-rank', 'newest']
    if sort_by is not None and sort_by.lower() not in valid_sort:
        invalid_filters.append(f"sort_by must be one of {valid_sort}, got {sort_by}")

    # If there are invalid filters, print warnings but continue
    if invalid_filters:
        print("Warning: Some filters have invalid values:")
        for invalid in invalid_filters:
            print(f"  - {invalid}")
        print("The search will continue with valid filters only.")

    # Print search information
    print(f"\n=== Searching for '{query}' ===")
    if filters:
        filter_str = ", ".join([f"{k}: {v}" for k, v in filters.items()])
        print(f"Applying filters: {filter_str}")
    else:
        print("No filters applied")

    # Perform the search
    try:
        products = await search_amazon(query, filters)

        # Check if any filters failed to apply
        if products and len(products) > 0 and 'filters_failed' in products[0] and products[0]['filters_failed']:
            print("\nWarning: Some filters could not be applied:")
            for k, v in products[0]['filters_failed'].items():
                print(f"  - {k}: {v}")

        # Display results
        print(f"\nFound {len(products)} products")
        for i, product in enumerate(products[:max_display]):
            print(f"\nProduct {i+1}:")
            print(f"Title: {product.get('title')}")
            print(f"Price: {product.get('price')}")
            print(f"URL: {product.get('url')}")

        details = None
        reviews = None

        # Get details for the first product if requested
        if get_details and products:
            product_url = products[0].get('url')
            print(f"\n=== Getting Details for Product ===")
            print(f"URL: {product_url}")

            try:
                async with AmazonConnection(headless=headless) as amazon:
                    details = await amazon.get_product_details(product_url)
                    reviews = await amazon.get_product_reviews(product_url)

                # Display product details
                print("\nProduct Details:")
                print(f"Title: {details.get('title')}")
                print(f"Price: {details.get('price')}")

                if 'features' in details and details['features']:
                    print("\nFeatures:")
                    for i, feature in enumerate(details['features'][:5]):
                        print(f"  {i+1}. {feature}")

                # Display reviews
                if reviews:
                    print("\nProduct Reviews:")
                    for i, review in enumerate(reviews[:3]):
                        print(f"\nReview {i+1}:")
                        print(f"Rating: {review.get('rating')}")
                        print(f"Title: {review.get('title')}")
                        content = review.get('content', '')
                        print(f"Content: {content[:100]}..." if len(content) > 100 else f"Content: {content}")
            except Exception as e:
                print(f"\nError getting product details: {e}")
                print("This may be due to Amazon's anti-scraping measures or the product page structure.")
    except Exception as e:
        print(f"\nError performing search: {e}")
        print("This may be due to Amazon's anti-scraping measures or network issues.")
        return [], None, None

    return products, details, reviews

async def run_test_case(case_id: str):
    """Run a specific test case by ID."""
    if case_id not in TEST_CASES:
        print(f"Error: Test case '{case_id}' not found.")
        print(f"Available test cases: {', '.join(TEST_CASES.keys())}")
        return

    case = TEST_CASES[case_id].copy()

    # Remove the 'name' key which is not a parameter of amazon_search
    if 'name' in case:
        name = case.pop('name')
        print(f"\n\n=== RUNNING TEST CASE: {name} ===")
    else:
        print(f"\n\n=== RUNNING TEST CASE: {case_id} ===")

    await amazon_search(**case)

async def run_all_test_cases():
    """Run all defined test cases."""
    print("\n\n=== RUNNING ALL TEST CASES ===")
    for case_id in TEST_CASES:
        await run_test_case(case_id)

async def run_additional_tests():
    """Run additional test cases to examine filter coverage."""
    print("\n\n=== ADDITIONAL FILTER TEST CASES ===\n")

    # Run all the new test cases
    for case_id in [
        "bluetooth_headphones",
        "running_shoes",
        "renewed_iphone",
        "gift_basket",
        "cotton_sheets",
        "coffee_maker",
        "face_moisturizer",
        "switch_games",
        "amazon_vitamins",
        "water_bottle",
        "mens_tshirt",
        "toys_deals"
    ]:
        await run_test_case(case_id)

# Add a function to display available categories
def print_category_help():
    """Print help information about available categories."""
    print("\nAvailable Categories:")
    print("--------------------")

    categories = {
        "Electronics": ["electronics", "computers", "cell_phones", "camera", "audio", "tv_video"],
        "Home": ["home", "kitchen", "furniture", "bedding", "bath", "appliances"],
        "Clothing": ["clothing", "mens_clothing", "womens_clothing", "kids_clothing", "shoes", "jewelry"],
        "Beauty": ["beauty", "skincare", "haircare", "makeup", "fragrance"],
        "Other": ["books", "toys", "sports", "grocery", "health", "pet_supplies", "automotive", "office", "baby", "tools"]
    }

    for category_group, category_list in categories.items():
        print(f"\n{category_group}:")
        for category in category_list:
            print(f"  - {category}: {CATEGORY_MAPPINGS[category]}")

async def main():
    """Run Amazon Connection demos."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Amazon Connection Test Runner")
            print("----------------------------")
            print("Usage:")
            print("  python -m src.react_agent.amazon_connection [options]")
            print("\nOptions:")
            print("  --help                 Show this help message")
            print("  --list                 List all available test cases")
            print("  --test <case_id>       Run a specific test case")
            print("  --all                  Run all test cases")
            print("  --additional           Run additional test cases")
            print("  --categories           Show available category mappings")
            print("\nAvailable test cases:")
            for case_id, case in TEST_CASES.items():
                print(f"  {case_id}: {case['name']}")
            return

        elif sys.argv[1] == "--categories":
            print_category_help()
            return

        elif sys.argv[1] == "--list":
            print("Available test cases:")
            for case_id, case in TEST_CASES.items():
                print(f"  {case_id}: {case['name']}")
            return

        elif sys.argv[1] == "--test" and len(sys.argv) > 2:
            await run_test_case(sys.argv[2])
            return

        elif sys.argv[1] == "--all":
            await run_all_test_cases()
            return

        elif sys.argv[1] == "--additional":
            await run_additional_tests()
            return

    # By default, run the bluetooth speaker test case
    await run_test_case("bluetooth_speaker")

if __name__ == "__main__":
    asyncio.run(main())