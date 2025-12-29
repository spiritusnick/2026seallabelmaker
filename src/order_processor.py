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
    sticker_number: int = 1  # Which sticker for this address (1, 2, 3...)
    total_for_address: int = 1  # Total stickers for this address


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
        Creates ONE sticker per unit (quantity 2 = 2 stickers).

        Args:
            orders: List of order dictionaries from Shopify

        Returns:
            List of StickerData objects (one per unit)
        """
        stickers = []

        for order in orders:
            order_stickers = self._process_single_order(order)
            stickers.extend(order_stickers)

        # Calculate sticker numbers per address (e.g., 1/4, 2/4, 3/4, 4/4)
        self._calculate_sticker_numbers(stickers)

        return stickers

    def _calculate_sticker_numbers(self, stickers: List[StickerData]):
        """
        Calculate sticker numbers for each address.
        Groups stickers by address and assigns 1/N, 2/N, etc.

        Args:
            stickers: List of StickerData objects to update in place
        """
        # Group stickers by address key (name + address)
        address_groups: Dict[str, List[StickerData]] = {}

        for sticker in stickers:
            # Create a key based on customer name and address
            key = f"{sticker.customer_name}|{sticker.address_line1}|{sticker.city}"
            if key not in address_groups:
                address_groups[key] = []
            address_groups[key].append(sticker)

        # Assign sticker numbers within each group
        for key, group in address_groups.items():
            total = len(group)
            for i, sticker in enumerate(group, 1):
                sticker.sticker_number = i
                sticker.total_for_address = total

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

            # Extract variant information from variant_title
            variant_title = item.get('variant_title', '')

            # Also check properties (subscription orders often have grind info here)
            properties = item.get('properties', [])
            property_parts = []
            for prop in properties:
                prop_name = prop.get('name', '')
                prop_value = prop.get('value', '')
                # Skip internal/hidden properties (often start with _)
                if prop_value and not prop_name.startswith('_'):
                    property_parts.append(prop_value)

            # Combine variant_title and properties for complete info
            variant_parts = []
            if variant_title and variant_title != 'Default Title':
                variant_parts.append(variant_title)
            if property_parts:
                variant_parts.extend(property_parts)

            variant_info = ' / '.join(variant_parts) if variant_parts else ''

            # Create one sticker per unit (quantity 2 = 2 stickers)
            for _ in range(quantity):
                sticker = StickerData(
                    order_name=order_name,
                    customer_name=customer_name,
                    address_line1=address_line1,
                    address_line2=address_line2,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    quantity=1,  # Each sticker represents 1 unit
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
