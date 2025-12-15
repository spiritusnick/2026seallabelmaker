"""
Shopify API Connector Module

This module handles connection to Shopify API and retrieval of unfulfilled orders.
It can be run standalone to test the Shopify connection.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv
import shopify


class ShopifyConnector:
    """Handles Shopify API connection and order retrieval."""

    def __init__(self):
        """Initialize Shopify connection using environment variables."""
        # Load env.env from parent directory
        env_path = os.path.join(os.path.dirname(__file__), '..', 'env.env')
        load_dotenv(env_path)

        self.store_url = os.getenv('SHOPIFY_STORE_URL')
        self.api_key = os.getenv('SHOPIFY_API_KEY')
        self.api_secret = os.getenv('SHOPIFY_API_SECRET')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

        # Validate credentials
        if not all([self.store_url, self.access_token]):
            raise ValueError("Missing required Shopify credentials in env.env")

        # Extract shop name from URL
        self.shop_name = self.store_url.replace('https://', '').replace('http://', '')

        # Initialize Shopify session
        self._init_session()

    def _init_session(self):
        """Initialize Shopify API session."""
        api_version = '2024-10'  # Using API version from PRD
        shop_url = f"https://{self.shop_name}"

        session = shopify.Session(shop_url, api_version, self.access_token)
        shopify.ShopifyResource.activate_session(session)
        print(f"[OK] Connected to Shopify store: {self.shop_name}")

    def get_unfulfilled_orders(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Retrieve unfulfilled orders from Shopify.

        Args:
            days_back: Number of days to look back for orders (default: 7)

        Returns:
            List of order dictionaries
        """
        # Calculate date range
        start_date = datetime.now() - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d')

        print(f"\nFetching unfulfilled orders since {start_date_str}...")

        # Retrieve orders using Shopify API
        # Parameters: fulfillment_status=unfulfilled, created_at_min
        orders = shopify.Order.find(
            fulfillment_status='unfulfilled',
            created_at_min=start_date_str,
            status='any',  # Include all order statuses
            limit=250  # Maximum per request
        )

        print(f"[OK] Retrieved {len(orders)} unfulfilled orders")

        # Convert to dictionary format for easier processing
        order_list = []
        for order in orders:
            order_dict = order.to_dict()
            order_list.append(order_dict)

        return order_list

    def filter_orders(self, orders: List[Dict[str, Any]], exclude_tag: str = "Ready For Pickup") -> List[Dict[str, Any]]:
        """
        Filter orders to exclude those with specific tag.

        Args:
            orders: List of order dictionaries
            exclude_tag: Tag to exclude (default: "Ready For Pickup")

        Returns:
            Filtered list of orders
        """
        filtered = []
        excluded_count = 0

        for order in orders:
            tags = order.get('tags', '')
            # Tags are stored as comma-separated string
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]

            if exclude_tag not in tag_list:
                filtered.append(order)
            else:
                excluded_count += 1

        print(f"[OK] Filtered out {excluded_count} orders with '{exclude_tag}' tag")
        print(f"[OK] {len(filtered)} orders remaining for processing")

        return filtered

    def display_order_summary(self, orders: List[Dict[str, Any]]):
        """
        Display a summary of retrieved orders (for testing/debugging).

        Args:
            orders: List of order dictionaries
        """
        print(f"\n{'='*60}")
        print(f"ORDER SUMMARY ({len(orders)} orders)")
        print(f"{'='*60}")

        for i, order in enumerate(orders, 1):
            order_name = order.get('name', 'N/A')
            customer = order.get('customer', {})
            customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()

            shipping_address = order.get('shipping_address', {})
            city = shipping_address.get('city', 'N/A')

            line_items = order.get('line_items', [])
            item_count = sum(item.get('quantity', 0) for item in line_items)

            print(f"\n{i}. Order {order_name}")
            print(f"   Customer: {customer_name}")
            print(f"   City: {city}")
            print(f"   Line Items: {len(line_items)} ({item_count} total items)")
            print(f"   Tags: {order.get('tags', 'None')}")

    def close(self):
        """Close Shopify session."""
        shopify.ShopifyResource.clear_session()
        print("\n[OK] Shopify session closed")


def main():
    """Standalone test function to verify Shopify connection."""
    print("="*60)
    print("SHOPIFY CONNECTOR - STANDALONE TEST")
    print("="*60)

    try:
        # Initialize connector
        connector = ShopifyConnector()

        # Get unfulfilled orders
        orders = connector.get_unfulfilled_orders(days_back=7)

        # Filter out "Ready For Pickup" orders
        filtered_orders = connector.filter_orders(orders)

        # Display summary
        connector.display_order_summary(filtered_orders)

        # Close connection
        connector.close()

        print(f"\n{'='*60}")
        print("[OK] TEST COMPLETED SUCCESSFULLY")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
