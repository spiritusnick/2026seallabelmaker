"""
Order Processor Module

Processes Shopify orders and creates sticker data structures.
Implements business logic for:
- One sticker per line item
- Local delivery vs shipping determination
- Sticker data formatting
"""

from typing import List, Dict, Any
from dataclasses import dataclass


# Local delivery cities (from PRD)
LOCAL_DELIVERY_CITIES = [
    "Lombard",
    "Glen Ellyn",
    "Addison",
    "Wheaton",
    "Villa Park"
]


@dataclass
class StickerData:
    """Data structure for a single sticker."""
    order_name: str
    customer_name: str
    address_line1: str
    address_line2: str
    city: str
    state: str
    zip_code: str
    quantity: int
    product_name: str
    variant_info: str
    requires_shipping: bool  # True if needs "SHIP" label


class OrderProcessor:
    """Processes orders and generates sticker data."""

    def __init__(self, local_cities: List[str] = None):
        """
        Initialize processor.

        Args:
            local_cities: List of local delivery city names (optional)
        """
        self.local_cities = [city.lower() for city in (local_cities or LOCAL_DELIVERY_CITIES)]

    def is_local_delivery(self, city: str) -> bool:
        """
        Check if city qualifies for local delivery.

        Args:
            city: City name from shipping address

        Returns:
            True if local delivery, False if requires shipping
        """
        if not city:
            return False
        return city.lower().strip() in self.local_cities

    def create_stickers_from_orders(self, orders: List[Dict[str, Any]]) -> List[StickerData]:
        """
        Convert orders to sticker data structures.
        Creates ONE sticker per line item.

        Args:
            orders: List of order dictionaries from Shopify

        Returns:
            List of StickerData objects (one per line item)
        """
        stickers = []

        for order in orders:
            order_stickers = self._process_single_order(order)
            stickers.extend(order_stickers)

        return stickers

    def _process_single_order(self, order: Dict[str, Any]) -> List[StickerData]:
        """
        Process a single order and create stickers for each line item.

        Args:
            order: Order dictionary from Shopify

        Returns:
            List of StickerData objects for this order
        """
        stickers = []

        # Extract order-level info
        order_name = order.get('name', 'Unknown')

        # Customer info
        customer = order.get('customer', {})
        customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip()
        if not customer_name:
            customer_name = "Unknown Customer"

        # Shipping address
        shipping = order.get('shipping_address', {})
        if not shipping:
            print(f"  [WARNING] Order {order_name} has no shipping address, skipping")
            return stickers

        address_line1 = shipping.get('address1', '')
        address_line2 = shipping.get('address2', '')
        city = shipping.get('city', '')
        state = shipping.get('province_code', shipping.get('province', ''))
        zip_code = shipping.get('zip', '')

        # Determine if requires shipping label
        requires_shipping = not self.is_local_delivery(city)

        # Process each line item
        line_items = order.get('line_items', [])

        if not line_items:
            print(f"  [WARNING] Order {order_name} has no line items, skipping")
            return stickers

        for item in line_items:
            quantity = item.get('quantity', 1)
            product_name = item.get('name', 'Unknown Product')

            # Extract variant information
            variant_title = item.get('variant_title', '')

            # If variant_title is None or empty, check properties
            if not variant_title or variant_title == 'Default Title':
                # Some products might have variant info in properties
                properties = item.get('properties', [])
                variant_parts = [prop.get('value', '') for prop in properties if prop.get('value')]
                variant_info = ' / '.join(variant_parts) if variant_parts else ''
            else:
                variant_info = variant_title

            # Create sticker
            sticker = StickerData(
                order_name=order_name,
                customer_name=customer_name,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                zip_code=zip_code,
                quantity=quantity,
                product_name=product_name,
                variant_info=variant_info,
                requires_shipping=requires_shipping
            )

            stickers.append(sticker)

        return stickers

    def display_sticker_summary(self, stickers: List[StickerData]):
        """
        Display summary of sticker data (for testing/debugging).

        Args:
            stickers: List of StickerData objects
        """
        print(f"\n{'='*60}")
        print(f"STICKER DATA SUMMARY ({len(stickers)} stickers)")
        print(f"{'='*60}")

        local_count = sum(1 for s in stickers if not s.requires_shipping)
        shipping_count = sum(1 for s in stickers if s.requires_shipping)

        print(f"\nLocal Delivery: {local_count}")
        print(f"Requires Shipping: {shipping_count}")

        for i, sticker in enumerate(stickers, 1):
            ship_label = "**SHIP**" if sticker.requires_shipping else "LOCAL"

            print(f"\n{i}. [{ship_label}] Order {sticker.order_name}")
            print(f"   {sticker.customer_name}")
            print(f"   {sticker.address_line1}")
            if sticker.address_line2:
                print(f"   {sticker.address_line2}")
            print(f"   {sticker.city}, {sticker.state} {sticker.zip_code}")
            print(f"   {sticker.quantity}x {sticker.product_name}")
            if sticker.variant_info:
                print(f"      {sticker.variant_info}")


def main():
    """Standalone test using sample order data."""
    print("="*60)
    print("ORDER PROCESSOR - STANDALONE TEST")
    print("="*60)

    # Sample test data (simulating Shopify orders)
    sample_orders = [
        {
            'name': 'SCC2031',
            'customer': {'first_name': 'Randi', 'last_name': 'Abts'},
            'shipping_address': {
                'address1': '123 Main St',
                'address2': 'Apt 4B',
                'city': 'Lombard',
                'province': 'IL',
                'zip': '60148'
            },
            'line_items': [
                {
                    'quantity': 2,
                    'name': 'Spiritus Coffee Subscription',
                    'variant_title': 'Medium Roast / Ground for Drip'
                }
            ]
        },
        {
            'name': 'SCC2030',
            'customer': {'first_name': 'Perry', 'last_name': 'Johnson'},
            'shipping_address': {
                'address1': '456 Oak Ave',
                'address2': '',
                'city': 'Philadelphia',
                'province': 'PA',
                'zip': '19103'
            },
            'line_items': [
                {
                    'quantity': 1,
                    'name': 'Ethiopian Single Origin',
                    'variant_title': 'Whole Bean'
                },
                {
                    'quantity': 1,
                    'name': 'Colombian Blend',
                    'variant_title': 'Ground for Espresso'
                }
            ]
        }
    ]

    # Process orders
    processor = OrderProcessor()
    stickers = processor.create_stickers_from_orders(sample_orders)

    # Display results
    processor.display_sticker_summary(stickers)

    print(f"\n{'='*60}")
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
