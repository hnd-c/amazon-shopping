"""Amazon Connection Module - Handles all interactions with Amazon's website. Uses Playwright for browser automation to search, filter, and extract product information."""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Union, Any

from playwright.async_api import Response
from urllib.parse import urlencode, quote_plus

# Import from browser_management instead of defining locally
from .browser_management import Browser, browser_pool, rate_limiter, USER_AGENTS
from .utils import with_retry, create_error_response, SELECTORS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AmazonConnection(Browser):
    """Main class for handling Amazon website interactions."""

    BASE_URL = "https://www.amazon.com"

    def __init__(self, headless: bool = True, slow_mo: int = 50, proxy: Optional[str] = None, proxies: Optional[List[str]] = None):
        """Initialize the Amazon connection."""
        super().__init__(headless, slow_mo, proxy, proxies)

    # ===== SEARCH METHODS =====

    async def search_products(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon with enhanced stealth measures.
        """
        logger.info(f"Searching for: {query}")

        # Construct search URL
        search_url = self.build_search_url(query)

        # Use stealth navigation instead of regular navigation
        success = await self.stealth_visit(search_url)

        if not success:
            logger.warning("Failed to navigate to search page stealthily")
            return []

        # Wait for search results to load
        await self._wait_for_element("div.s-result-list")

        # Add a delay to ensure all content is loaded
        await asyncio.sleep(random.uniform(2, 4))

        # Extract product information
        products = await self._extract_search_results(max_results)

        logger.info(f"Found {len(products)} products for query: {query}")
        return products

    async def apply_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply filters to the current search results.

        Args:
            filters: Dictionary of filters to apply
                Supported filters:
                - price_min: Minimum price
                - price_max: Maximum price
                - prime_only: Only show Prime eligible items (boolean)
                - brand: Brand name or list of brands
                - min_rating: Minimum star rating (1-5)
                - sort_by: Sort method (e.g., "price-asc", "price-desc", "review-rank")
                - free_shipping: Only show items with free shipping (boolean)
                - discount_only: Only show discounted items (boolean)
                - max_delivery_days: Maximum delivery days
                - condition: Product condition (new, used, refurbished, renewed)
                - department: Department/category
                - seller: Specific seller
                - availability: Availability status (in_stock, include_out_of_stock)
                - color: Product color
                - size: Product size
                - material: Product material
                - features: Product features
                - customer_reviews: Customer review filter (positive, critical)
                - price_drops: Show only items with recent price drops (boolean)
                - deals: Show only deals (boolean)

        Returns:
            List of filtered product dictionaries
        """
        logger.info(f"Applying filters: {filters}")

        # Get current URL
        current_url = self.page.url

        # Build filter URL
        if "?" in current_url:
            base_url = current_url.split("?")[0]
            query = current_url.split("?")[1].split("&")[0]
            filter_url = f"{base_url}?{query}"
        else:
            filter_url = current_url

        # Add filter parameters
        filter_params = []

        # Price range filter
        if 'price_min' in filters and 'price_max' in filters:
            min_price = int(float(filters['price_min']) * 100)
            max_price = int(float(filters['price_max']) * 100)
            filter_params.append(f"p_36:{min_price}-{max_price}")
        elif 'price_min' in filters:
            min_price = int(float(filters['price_min']) * 100)
            filter_params.append(f"p_36:{min_price}-")
        elif 'price_max' in filters:
            max_price = int(float(filters['price_max']) * 100)
            filter_params.append(f"p_36:-{max_price}")

        # Prime filter
        if 'prime_only' in filters and filters['prime_only']:
            filter_params.append("p_85:2470955011")

        # Brand filter
        if 'brand' in filters:
            if isinstance(filters['brand'], list):
                # Multiple brands
                brand_param = "p_89:"
                for i, brand in enumerate(filters['brand']):
                    if i > 0:
                        brand_param += "|"
                    brand_param += brand.replace(" ", "+")
                filter_params.append(brand_param)
            else:
                # Single brand
                brand = filters['brand'].replace(" ", "+")
                filter_params.append(f"p_89:{brand}")

        # Customer rating filter
        if 'min_rating' in filters:
            rating = int(float(filters['min_rating']))
            rating_map = {
                1: "p_72:1248882011",
                2: "p_72:1248883011",
                3: "p_72:1248884011",
                4: "p_72:1248885011"
            }
            if rating in rating_map:
                filter_params.append(rating_map[rating])

        # Free shipping filter
        if 'free_shipping' in filters and filters['free_shipping']:
            filter_params.append("p_76:1")

        # Discount filter
        if 'discount_only' in filters and filters['discount_only']:
            filter_params.append("p_n_deal_type:23566065011")

        # Condition filter
        if 'condition' in filters:
            condition = filters['condition'].lower()
            condition_map = {
                "new": "p_n_condition-type:6461716011",
                "used": "p_n_condition-type:6461718011",
                "refurbished": "p_n_condition-type:6461717011",
                "renewed": "p_n_condition-type:16349437011"
            }
            if condition in condition_map:
                filter_params.append(condition_map[condition])

        # Availability filter
        if 'availability' in filters:
            availability = filters['availability'].lower()
            if availability == "in_stock":
                filter_params.append("p_n_availability:2661601011")
            elif availability == "include_out_of_stock":
                # This is the default, so we don't need to add a parameter
                pass

        # Department/category filter
        if 'department' in filters:
            department = filters['department'].replace(" ", "+")
            filter_params.append(f"n:{department}")

        # Seller filter
        if 'seller' in filters:
            seller = filters['seller'].replace(" ", "+")
            filter_params.append(f"p_6:{seller}")

        # Color filter
        if 'color' in filters:
            color = filters['color'].replace(" ", "+")
            filter_params.append(f"p_n_feature_twenty_browse-bin:{color}")

        # Size filter
        if 'size' in filters:
            size = filters['size'].replace(" ", "+")
            filter_params.append(f"p_n_size_browse-bin:{size}")

        # Material filter
        if 'material' in filters:
            material = filters['material'].replace(" ", "+")
            filter_params.append(f"p_n_material_browse:{material}")

        # Features filter
        if 'features' in filters and isinstance(filters['features'], list):
            for feature in filters['features']:
                feature_param = feature.replace(" ", "+")
                filter_params.append(f"p_n_feature_browse-bin:{feature_param}")

        # Customer reviews filter
        if 'customer_reviews' in filters:
            review_type = filters['customer_reviews'].lower()
            if review_type == "positive":
                filter_params.append("p_72:1248885011")  # 4+ stars
            elif review_type == "critical":
                filter_params.append("p_72:1248882011")  # 1+ stars (includes critical)

        # Price drops filter
        if 'price_drops' in filters and filters['price_drops']:
            filter_params.append("p_n_deal_type:23566064011")

        # Deals filter
        if 'deals' in filters and filters['deals']:
            filter_params.append("p_n_deal_type:23566065011")

        # Maximum delivery days filter
        if 'max_delivery_days' in filters:
            days = int(filters['max_delivery_days'])
            if days <= 2:
                filter_params.append("p_n_shipping_option-bin:3242350011")  # 2-day shipping
            elif days <= 4:
                filter_params.append("p_n_shipping_option-bin:3242351011")  # 3-4 day shipping

        # Add sorting parameter
        if 'sort_by' in filters:
            sort_value = filters['sort_by']
            sort_mapping = {
                "price-asc": "price-asc-rank",
                "price-desc": "price-desc-rank",
                "review-rank": "review-rank",
                "newest": "date-desc-rank",
                "featured": "relevancerank"
            }
            if sort_value in sort_mapping:
                filter_url += f"&s={sort_mapping[sort_value]}"

        # Add filter parameters to URL
        if filter_params:
            filter_url = f"{filter_url}&rh={','.join(filter_params)}"

        # Debug log
        logger.info(f"Filter URL: {filter_url}")

        # Use stealth navigation for the filter URL
        success = await self.stealth_visit(filter_url)

        if not success:
            logger.warning("Failed to navigate to filtered results page stealthily")
            return []

        # Wait for results to load
        await asyncio.sleep(random.uniform(2, 4))

        # Extract filtered results
        return await self._extract_search_results(20)

    def build_search_url(self, query, filters=None):
        """Build Amazon search URL with filters."""
        base_url = f"https://www.amazon.com/s?k={quote_plus(query)}"

        if not filters:
            return base_url

        filter_params = []

        # Price range filter
        if 'price_min' in filters and 'price_max' in filters:
            min_price = int(float(filters['price_min']) * 100)
            max_price = int(float(filters['price_max']) * 100)
            filter_params.append(f"p_36:{min_price}-{max_price}")

        # Prime filter
        if 'prime_only' in filters and filters['prime_only']:
            filter_params.append("p_85:2470955011")
        elif 'exclude_prime' in filters and filters['exclude_prime']:
            filter_params.append("p_85:-2470955011")

        # Customer rating filter
        if 'min_rating' in filters:
            rating = int(float(filters['min_rating']))
            filter_params.append(f"p_72:1248882011-{rating}00")

        if filter_params:
            return f"{base_url}&rh={','.join(filter_params)}"
        return base_url

    # ===== PRODUCT DETAIL METHODS =====

    async def get_product_details(self, product_url: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific product.

        Args:
            product_url: URL of the product page

        Returns:
            Dictionary with detailed product information
        """
        logger.info(f"Getting details for product: {product_url}")

        # Use stealth navigation instead of regular navigation
        success = await self.stealth_visit(product_url)

        if not success:
            logger.warning("Failed to navigate to product page stealthily")
            return {}

        # Wait for product page to load
        await self._wait_for_element("#productTitle")

        # Check for CAPTCHA first
        if await self.check_for_captcha():
            logger.warning("CAPTCHA detected when trying to get product details")
            return {}

        # Extract product details
        product_details = {}

        # Title
        title_element = await self.page.query_selector("#productTitle")
        if title_element:
            product_details["title"] = (await title_element.text_content()).strip()

        # Price with fallbacks
        for selector in ["#priceblock_ourprice", "#priceblock_dealprice", ".a-price .a-offscreen"]:
            price_element = await self.page.query_selector(selector)
            if price_element:
                product_details["price"] = await price_element.text_content()
                break

        # Rating with fallbacks
        rating_element = await self.page.query_selector("span[data-hook='rating-out-of-text']")
        if rating_element:
            product_details["rating"] = await rating_element.text_content()
        else:
            rating_element = await self.page.query_selector("#acrPopover")
            if rating_element:
                rating_text = await rating_element.get_attribute("title")
                if rating_text:
                    product_details["rating"] = rating_text.split(" out of")[0]

        # Review count
        review_count_element = await self.page.query_selector("#acrCustomerReviewText")
        if review_count_element:
            review_text = await review_count_element.text_content()
            if "ratings" in review_text or "reviews" in review_text:
                count_text = review_text.split(" ")[0].replace(",", "")
                product_details["review_count"] = count_text

        # Check for Prime eligibility
        prime_element = await self.page.query_selector("#isPrimeBadge, .a-icon-prime")
        product_details["prime_eligible"] = prime_element is not None

        # Availability
        availability_element = await self.page.query_selector("#availability")
        if availability_element:
            product_details["availability"] = (await availability_element.text_content()).strip()

        # Get product description
        description_element = await self.page.query_selector("#productDescription p")
        if description_element:
            product_details["description"] = (await description_element.text_content()).strip()
        else:
            product_details["description"] = await self._get_text("#productDescription")

        # Get product features
        features = []
        feature_elements = await self.page.query_selector_all("#feature-bullets li:not(.aok-hidden) span.a-list-item")
        if feature_elements:
            for element in feature_elements:
                feature_text = await element.text_content()
                features.append(feature_text.strip())
        else:
            feature_bullets = await self.page.query_selector_all("#feature-bullets li")
            for bullet in feature_bullets:
                feature_text = await bullet.text_content()
                features.append(feature_text.strip())
        product_details["features"] = features

        # Get product specifications
        product_details["specifications"] = await self._extract_product_specifications()

        # Get product images
        images = []
        image_elements = await self.page.query_selector_all("#altImages img")
        for img in image_elements:
            src = await img.get_attribute("src")
            if src and "sprite" not in src:
                # Convert thumbnail URL to full-size image URL
                full_size_src = src.replace("._SS40_", "._SL1500_")
                images.append(full_size_src)

        # If no images found, try to get the main image
        if not images:
            main_img = await self.page.query_selector("#landingImage")
            if main_img:
                src = await main_img.get_attribute("src")
                if src:
                    images.append(src)

        product_details["images"] = images

        # Extract Prime delivery information
        try:
            delivery_element = await self.page.query_selector("div[data-hook='delivery-block']")
            if delivery_element:
                delivery_text = await delivery_element.text_content()
                product_details["delivery_info"] = delivery_text
                product_details["prime_delivery"] = "Prime" in delivery_text
        except Exception as e:
            logger.debug(f"Error extracting delivery info: {e}")
            product_details["delivery_info"] = None
            product_details["prime_delivery"] = False

        logger.info(f"Extracted details for product: {product_details.get('title', 'Unknown')}")
        return product_details

    # ===== REVIEW METHODS =====

    async def get_product_reviews(self, product_url: str, max_reviews: int = 10) -> List[Dict[str, Any]]:
        """Get reviews for a product directly from the product page."""
        logger.info(f"Getting reviews for product: {product_url}")

        try:
            # Use stealth navigation instead of regular navigation
            success = await self.stealth_visit(product_url)

            if not success:
                logger.warning("Failed to navigate to product page stealthily for reviews")
                return []

            # Wait for product page to load
            await self._wait_for_element("#productTitle")

            # Check for CAPTCHA
            if await self.check_for_captcha():
                logger.warning("CAPTCHA detected when trying to get reviews")
                return []

            # Scroll down to reviews section to ensure it loads
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)

            # Extract reviews from the product page
            reviews = []

            # First try to get reviews from the product page
            review_elements = await self.page.query_selector_all("#customerReviews .review")

            # If no reviews found, try alternative selectors
            if not review_elements:
                review_elements = await self.page.query_selector_all("[data-hook='review']")

            # If still no reviews, try clicking "See all reviews" button if it exists
            if not review_elements:
                see_all_button = await self.page.query_selector("a[data-hook='see-all-reviews-link-foot']")
                if see_all_button:
                    try:
                        # Click with a try/except as this might trigger anti-bot measures
                        await see_all_button.click()
                        await asyncio.sleep(3)
                        review_elements = await self.page.query_selector_all("[data-hook='review']")
                    except Exception as e:
                        logger.warning(f"Error clicking 'See all reviews': {e}")

            # Process found reviews
            for i, review_element in enumerate(review_elements):
                if i >= max_reviews:
                    break

                review = {}

                # Extract review data with multiple selector fallbacks
                # Rating
                rating_element = await review_element.query_selector("i[data-hook='review-star-rating'], .a-icon-star")
                if rating_element:
                    rating_text = await rating_element.text_content() or await rating_element.get_attribute("title") or ""
                    if "out of 5 stars" in rating_text:
                        review["rating"] = rating_text.split(" out of")[0]
                    elif "stars" in rating_text:
                        review["rating"] = rating_text.split(" stars")[0].strip()

                # Title
                title_element = await review_element.query_selector("a[data-hook='review-title'], span[data-hook='review-title']")
                if title_element:
                    review["title"] = await title_element.text_content()

                # Date
                date_element = await review_element.query_selector("span[data-hook='review-date']")
                if date_element:
                    review["date"] = await date_element.text_content()

                # Verified purchase
                verified_element = await review_element.query_selector("span[data-hook='avp-badge']")
                review["verified_purchase"] = verified_element is not None

                # Content
                content_element = await review_element.query_selector("span[data-hook='review-body'] span:not(script)")
                if content_element:
                    review["content"] = await content_element.text_content()

                # Helpful votes
                helpful_element = await review_element.query_selector("span[data-hook='helpful-vote-statement']")
                if helpful_element:
                    helpful_text = await helpful_element.text_content()
                    if "found this helpful" in helpful_text:
                        votes = helpful_text.split(" ")[0]
                        review["helpful_votes"] = votes

                reviews.append(review)

            # If we couldn't get reviews, extract at least the overall rating
            if not reviews:
                overall_rating = await self.page.query_selector("#acrPopover")
                if overall_rating:
                    rating_text = await overall_rating.get_attribute("title") or ""
                    if rating_text:
                        reviews.append({
                            "rating": rating_text.split(" out of")[0],
                            "title": "Overall Rating",
                            "content": f"This product has an overall rating of {rating_text}",
                            "verified_purchase": False
                        })

            logger.info(f"Found {len(reviews)} reviews for product")
            return reviews

        except Exception as e:
            logger.error(f"Error getting reviews: {str(e)}")
            return []

    async def get_review_statistics(self, product_url: str) -> Dict[str, Any]:
        """
        Get review statistics for a product.

        Args:
            product_url: The product URL

        Returns:
            Dictionary with review statistics
        """
        logger.info(f"Getting review statistics for product: {product_url}")

        # Extract ASIN from URL if needed
        asin = None
        if "/dp/" in product_url:
            asin = product_url.split("/dp/")[1].split("/")[0].split("?")[0]

        # Navigate to reviews page
        reviews_url = f"https://www.amazon.com/product-reviews/{asin}/" if asin else f"{product_url.split('?')[0]}/reviews"

        # Use stealth navigation
        success = await self.stealth_visit(reviews_url)

        if not success:
            logger.warning("Failed to navigate to reviews page stealthily")
            return {}

        # Wait for reviews to load
        await self._wait_for_element("#cm_cr-review_list")

        stats = {}

        # Overall rating
        rating_element = await self.page.query_selector("span[data-hook='rating-out-of-text']")
        if rating_element:
            rating_text = await rating_element.text_content()
            if "out of 5" in rating_text:
                stats["overall_rating"] = rating_text.split(" out of")[0]

        # Total reviews
        total_element = await self.page.query_selector("div[data-hook='cr-filter-info-review-rating-count']")
        if total_element:
            total_text = await total_element.text_content()
            if "total ratings" in total_text:
                total = total_text.split("total ratings")[0].strip().split(" ")[-1].replace(",", "")
                stats["total_reviews"] = total

        # Rating breakdown
        breakdown = {}
        for stars in range(5, 0, -1):
            star_element = await self.page.query_selector(f"a[data-hook='cr-filter-info-link'][title='{stars} star']")
            if star_element:
                percentage_element = await star_element.query_selector("span.a-size-base")
                if percentage_element:
                    percentage = await percentage_element.text_content()
                    breakdown[f"{stars}_star"] = percentage

        stats["rating_breakdown"] = breakdown

        logger.info(f"Extracted review statistics for product")
        return stats

    # ===== DATA EXTRACTION HELPERS =====

    async def _extract_search_results(self, max_results: int) -> List[Dict[str, Any]]:
        """Extract product information from search results."""
        products = []

        # Check if we're on a CAPTCHA page
        for captcha_selector in SELECTORS["captcha_selectors"]:
            captcha_element = await self.page.query_selector(captcha_selector)
            if captcha_element:
                logger.warning(f"CAPTCHA detected with selector: {captcha_selector}")
                return products

        # Wait for search results to load
        await self._wait_for_element(SELECTORS["search_results_container"], timeout=5000)

        # Get all product cards
        product_cards = await self.page.query_selector_all(SELECTORS["product_card"])

        logger.info(f"Found {len(product_cards)} product cards")

        # Process each product card
        for i, card in enumerate(product_cards):
            if i >= max_results:
                break

            try:
                # Extract product information
                product = await self.extract_product_data(card)

                # Add to products list if we have at least title and URL
                if product.get("title") and product.get("url"):
                    products.append(product)

            except Exception as e:
                logger.warning(f"Error extracting product {i}: {str(e)}")

        return products

    async def extract_product_data(self, card):
        """Extract product data with fallback selectors."""
        product = {}

        # Title extraction with fallbacks
        title_element = await card.query_selector(SELECTORS["product_title"])
        if title_element:
            product["title"] = await title_element.text_content()

        # ASIN and URL extraction
        asin = await card.get_attribute("data-asin")
        if asin:
            product["asin"] = asin
            product["url"] = f"https://www.amazon.com/dp/{asin}"
        else:
            # Fallback to link extraction
            link_element = await card.query_selector("h2 a.a-link-normal")
            if link_element:
                href = await link_element.get_attribute("href")
                if href:
                    product["url"] = f"https://www.amazon.com{href}" if not href.startswith('http') else href
                    # Try to extract ASIN from URL
                    if "/dp/" in href:
                        asin = href.split("/dp/")[1].split("/")[0].split("?")[0]
                        product["asin"] = asin

        # Price extraction
        price_element = await card.query_selector(SELECTORS["product_price"])
        if price_element:
            product["price"] = await price_element.text_content()

        # Prime eligibility
        prime_element = await card.query_selector(SELECTORS["prime_badge"])
        product["prime_eligible"] = prime_element is not None

        # Rating extraction
        rating_element = await card.query_selector(SELECTORS["product_rating"])
        if rating_element:
            rating_text = await rating_element.text_content()
            if "out of 5 stars" in rating_text:
                product["rating"] = rating_text.split(" out of")[0]

        # Review count
        review_element = await card.query_selector("span.a-size-base.s-underline-text")
        if review_element:
            review_text = await review_element.text_content()
            product["review_count"] = review_text.replace(",", "")

        return product

    async def _extract_product_specifications(self) -> Dict[str, str]:
        """Extract product specifications from the product page."""
        specs = {}

        # Try to get specifications from product details section
        try:
            # Check for technical details table
            tech_rows = await self.page.query_selector_all("#productDetails_techSpec_section_1 tr")
            for row in tech_rows:
                try:
                    key_element = await row.query_selector("th")
                    value_element = await row.query_selector("td")

                    if key_element and value_element:
                        key = await key_element.text_content()
                        value = await value_element.text_content()
                        specs[key.strip()] = value.strip()
                except Exception:
                    continue

            # Check for additional details table
            detail_rows = await self.page.query_selector_all("#productDetails_detailBullets_sections1 tr")
            for row in detail_rows:
                try:
                    key_element = await row.query_selector("th")
                    value_element = await row.query_selector("td")

                    if key_element and value_element:
                        key = await key_element.text_content()
                        value = await value_element.text_content()
                        specs[key.strip()] = value.strip()
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error extracting product specifications: {str(e)}")

        return specs

    async def _extract_product_images(self, max_images: int = 5) -> List[str]:
        """Extract product images from the product page."""
        images = []

        try:
            # Try to get images from the image gallery
            img_elements = await self.page.query_selector_all("#altImages img")
            for img in img_elements:
                if len(images) >= max_images:
                    break

                try:
                    src = await img.get_attribute("src")
                    if src and "sprite" not in src and src not in images:
                        # Convert thumbnail URL to full-size image URL
                        full_size_src = src.replace("._SS40_", "._SL1500_")
                        images.append(full_size_src)
                except Exception:
                    continue

            # If no images found, try to get the main image
            if not images:
                main_img = await self.page.query_selector("#landingImage")
                if main_img:
                    src = await main_img.get_attribute("src")
                    if src:
                        images.append(src)

        except Exception as e:
            logger.warning(f"Error extracting product images: {str(e)}")

        return images

    # ===== CAPTCHA & ERROR HANDLING =====

    async def check_for_captcha(self):
        """Check if we've hit a CAPTCHA and handle it."""
        # First check for 503 Service Unavailable
        if "503" in self.page.url or await self.page.query_selector("title:has-text('503 Service Unavailable')"):
            logger.warning("503 Service Unavailable detected - Amazon is blocking requests")
            timestamp = int(time.time())
            screenshot_path = f"amazon_block_{timestamp}.png"
            await self.page.screenshot(path=screenshot_path)
            logger.warning(f"Amazon block screenshot saved to {screenshot_path}")
            return True

        captcha_selectors = [
            "form[action='/errors/validateCaptcha']",
            "input[name='amzn-captcha-submit']",
            "img[src*='captcha']",
            "div.a-box-inner > h4:contains('Enter the characters you see below')",
            "form[action*='validateCaptcha']",
            "input[id='captchacharacters']",
            "div.a-row > b:contains('Type the characters you see in this image')",
            "div.a-box-inner:contains('Sorry, we just need to make sure you're not a robot')",
            "body:has-text('To discuss automated access to Amazon data please contact')",
            "body:has-text('We\'re sorry, we\'re having trouble processing your request')"
        ]

        for selector in captcha_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    logger.warning(f"CAPTCHA detected with selector: {selector}")

                    # Take a screenshot of the CAPTCHA for debugging
                    timestamp = int(time.time())
                    screenshot_path = f"captcha_{timestamp}.png"
                    await self.page.screenshot(path=screenshot_path)
                    logger.warning(f"CAPTCHA screenshot saved to {screenshot_path}")

                    # Implement CAPTCHA solving here if needed
                    # For now, we'll just return True to indicate CAPTCHA was detected
                    return True
            except Exception as e:
                logger.debug(f"Error checking CAPTCHA selector {selector}: {e}")

        # Also check for login walls that might appear instead of CAPTCHAs
        login_selectors = [
            "form[name='signIn']",
            "input[name='email']",
            "div.a-box-inner:contains('Sign in')",
            "h1:contains('Sign-In')",
            "div.a-box-inner > h1:contains('Sign in')"
        ]

        for selector in login_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    logger.warning(f"Login wall detected with selector: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Error checking login selector {selector}: {e}")

        return False

    async def stealth_visit(self, url, max_retries=3):
        """
        Visit a URL with enhanced stealth measures to avoid detection.
        """
        logger.info(f"Stealth visiting: {url}")

        for attempt in range(max_retries):
            try:
                # Add random delay before navigation
                await asyncio.sleep(random.uniform(2, 5))

                # Simulate human-like behavior before navigation
                await self._add_pre_navigation_behavior()

                # Navigate with a more realistic timeout
                response = await self.page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                # Check for 503 or CAPTCHA
                if response and response.status == 503:
                    logger.warning(f"503 detected on stealth visit attempt {attempt+1}")

                    # Take screenshot for debugging
                    timestamp = int(time.time())
                    screenshot_path = f"amazon_block_{timestamp}.png"
                    await self.page.screenshot(path=screenshot_path)

                    # Try to rotate proxy if available
                    if self.proxies and len(self.proxies) > 0:
                        logger.info("Rotating proxy due to 503 error")
                        await self.rotate_proxy()

                    # Add increasing delay between retries
                    if attempt < max_retries - 1:
                        delay = 5 * (2 ** attempt) * (0.5 + random.random())
                        logger.info(f"Waiting {delay:.2f}s before retry")
                        await asyncio.sleep(delay)
                        continue
                    return False

                # Check for CAPTCHA after navigation
                if await self.check_for_captcha():
                    logger.warning(f"CAPTCHA detected on stealth visit attempt {attempt+1}")

                    # Try to rotate proxy if available
                    if self.proxies and len(self.proxies) > 0:
                        logger.info("Rotating proxy due to CAPTCHA")
                        await self.rotate_proxy()

                    if attempt < max_retries - 1:
                        delay = 5 * (2 ** attempt) * (0.5 + random.random())
                        await asyncio.sleep(delay)
                        continue
                    return False

                # Add post-navigation human-like behavior
                await self._add_post_navigation_behavior()

                return True

            except Exception as e:
                logger.warning(f"Error during stealth visit attempt {attempt+1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                    continue
                return False

        return False

    async def _add_pre_navigation_behavior(self):
        """Add human-like behavior before navigation to avoid detection."""
        try:
            # Random mouse movements
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Sometimes click on a random spot
            if random.random() < 0.3:
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.page.mouse.click(x, y)

            # Sometimes resize window
            if random.random() < 0.2:
                width = random.randint(1000, 1200)
                height = random.randint(800, 900)
                await self.page.set_viewport_size({"width": width, "height": height})
        except Exception as e:
            logger.debug(f"Error in pre-navigation behavior: {e}")

    async def _add_post_navigation_behavior(self):
        """Add human-like behavior after navigation to avoid detection."""
        try:
            # Wait a random time after page load
            await asyncio.sleep(random.uniform(1, 3))

            # Random scrolling
            for _ in range(random.randint(2, 5)):
                scroll_y = random.randint(100, 500)
                await self.page.evaluate(f"window.scrollBy(0, {scroll_y})")
                await asyncio.sleep(random.uniform(0.5, 1.5))

            # Sometimes scroll back up
            if random.random() < 0.5:
                await self.page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(random.uniform(0.5, 1))

            # Random mouse movements
            for _ in range(random.randint(3, 7)):
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.page.mouse.move(x, y)
                await asyncio.sleep(random.uniform(0.2, 0.5))
        except Exception as e:
            logger.debug(f"Error in post-navigation behavior: {e}")
