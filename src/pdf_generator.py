"""
PDF Generator Module

Generates printable PDFs using Avery 5160 template format.
Formats stickers with customer info, address, and product details.
"""

from datetime import datetime
from typing import List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from order_processor import StickerData


# Grind types to look for in variant info
GRIND_TYPES = [
    "Whole Bean",
    "Ground for Auto Drip",
    "Ground Auto Drip",
    "Auto Drip",
    "Ground for Drip",
    "French Press",
    "Ground for French Press",
    "Ground for Espresso",
    "Espresso",
]


def extract_grind_type(variant_info: str, product_name: str) -> Optional[str]:
    """
    Extract grind type from variant info or product name.

    Args:
        variant_info: The variant info string (e.g., "Rotating All Coffees / Whole Bean")
        product_name: The product name (may contain grind type)

    Returns:
        The grind type if found, None otherwise
    """
    # Check variant_info first (case-insensitive)
    text_to_check = f"{variant_info} {product_name}".lower()

    for grind in GRIND_TYPES:
        if grind.lower() in text_to_check:
            # Return normalized grind type
            if "whole bean" in grind.lower():
                return "Whole Bean"
            elif "french press" in grind.lower():
                return "French Press"
            elif "auto drip" in grind.lower() or "for drip" in grind.lower():
                return "Ground Auto Drip"
            elif "espresso" in grind.lower():
                return "Ground Espresso"
            return grind

    return None


# Avery 5160 Specifications (from PRD)
AVERY_5160 = {
    'page_width': 8.5 * inch,
    'page_height': 11 * inch,
    'label_width': 2.625 * inch,
    'label_height': 1.0 * inch,
    'columns': 3,
    'rows': 10,
    'top_margin': 0.5 * inch,
    'left_margin': 0.1875 * inch,
    'column_gap': 0.125 * inch,
    'row_gap': 0.0 * inch,
}


class PDFGenerator:
    """Generates PDF files with Avery 5160 label format."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize PDF generator.

        Args:
            output_dir: Directory to save PDFs
        """
        self.output_dir = output_dir
        self.spec = AVERY_5160

    def generate_pdf(self, stickers: List[StickerData], filename: str = None) -> str:
        """
        Generate PDF from sticker data.

        Args:
            stickers: List of StickerData objects
            filename: Optional filename (defaults to fulfillment-stickers-YYYY-MM-DD.pdf)

        Returns:
            Path to generated PDF file
        """
        if not filename:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"fulfillment-stickers-{date_str}.pdf"

        filepath = f"{self.output_dir}/{filename}"

        # Create canvas
        c = canvas.Canvas(filepath, pagesize=letter)

        # Draw stickers
        self._draw_stickers(c, stickers)

        # Save PDF
        c.save()

        print(f"[OK] PDF generated: {filepath}")
        print(f"  Total stickers: {len(stickers)}")
        print(f"  Pages: {(len(stickers) - 1) // 30 + 1}")

        return filepath

    def _draw_stickers(self, c: canvas.Canvas, stickers: List[StickerData]):
        """
        Draw all stickers on PDF canvas.

        Args:
            c: ReportLab canvas
            stickers: List of StickerData objects
        """
        labels_per_page = self.spec['columns'] * self.spec['rows']

        for idx, sticker in enumerate(stickers):
            # Calculate position
            page_num = idx // labels_per_page
            position_on_page = idx % labels_per_page

            # Start new page if needed
            if idx > 0 and position_on_page == 0:
                c.showPage()

            # Calculate row and column
            row = position_on_page // self.spec['columns']
            col = position_on_page % self.spec['columns']

            # Calculate x, y coordinates (bottom-left of label)
            x = (self.spec['left_margin'] +
                 col * (self.spec['label_width'] + self.spec['column_gap']))

            # Apply offset for third column (4mm = ~0.157 inches) to align with labels
            if col == 2:
                x += 0.157 * inch

            # Y coordinate: start from top of page, go down
            y = (self.spec['page_height'] -
                 self.spec['top_margin'] -
                 row * (self.spec['label_height'] + self.spec['row_gap']) -
                 self.spec['label_height'])

            # Draw single sticker
            self._draw_single_sticker(c, sticker, x, y)

    def _draw_single_sticker(self, c: canvas.Canvas, sticker: StickerData, x: float, y: float):
        """
        Draw a single sticker at specified position.
        Format matches sample template: simpler, tighter layout.

        Args:
            c: ReportLab canvas
            sticker: StickerData object
            x: X coordinate (left edge)
            y: Y coordinate (bottom edge)
        """
        # Starting position for text (from top of label, closer to edge)
        text_y = y + self.spec['label_height'] - 0.08 * inch  # Start near top
        line_height = 0.12 * inch  # Tighter spacing to match sample
        left_margin = 0.05 * inch

        # Set default font
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor('#000000'))  # Black

        # Draw "SHIP" indicator if needed (red, bold)
        if sticker.requires_shipping:
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(HexColor('#CC0000'))  # Red
            c.drawString(x + left_margin, text_y, "**SHIP**")
            c.setFillColor(HexColor('#000000'))  # Back to black
            text_y -= line_height

        # Customer name with sticker count (e.g., "1/4" on right side)
        c.setFont("Helvetica", 10)
        c.drawString(x + left_margin, text_y, sticker.customer_name)

        # Draw sticker count on right side (e.g., "1/4")
        count_text = f"{sticker.sticker_number}/{sticker.total_for_address}"
        count_width = c.stringWidth(count_text, "Helvetica-Bold", 10)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + self.spec['label_width'] - count_width - 0.05 * inch, text_y, count_text)
        c.setFont("Helvetica", 10)

        text_y -= line_height

        # Address - single line format like sample (street + city)
        # Format: "220 W Ash St. Lombard"
        address_text = f"{sticker.address_line1} {sticker.city}"
        c.drawString(x + left_margin, text_y, address_text)
        text_y -= line_height

        # Product line with quantity and name
        # Format: "1- Spiritus Coffee Subscription"
        product_line = f"{sticker.quantity}- {sticker.product_name}"

        # Truncate if too long
        if len(product_line) > 40:
            product_line = product_line[:37] + "..."

        c.drawString(x + left_margin, text_y, product_line)
        text_y -= line_height * 0.95

        # Extract and display grind type (Whole Bean, Ground Auto Drip, French Press)
        grind_type = extract_grind_type(sticker.variant_info or "", sticker.product_name)
        if grind_type:
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x + left_margin, text_y, grind_type)
            c.setFont("Helvetica", 10)

        # Optional: Draw border for debugging (comment out for production)
        # c.rect(x, y, self.spec['label_width'], self.spec['label_height'])


def main():
    """Standalone test with sample sticker data."""
    print("="*60)
    print("PDF GENERATOR - STANDALONE TEST")
    print("="*60)

    # Create sample sticker data
    sample_stickers = [
        StickerData(
            order_name="SCC2031",
            customer_name="Randi Abts",
            address_line1="123 Main St",
            address_line2="Apt 4B",
            city="Lombard",
            state="IL",
            zip_code="60148",
            quantity=2,
            product_name="Spiritus Coffee Subscription - Rotating Roasters",
            variant_info="Medium Roast / Ground for Drip",
            requires_shipping=False
        ),
        StickerData(
            order_name="SCC2030",
            customer_name="Perry Johnson",
            address_line1="456 Oak Ave",
            address_line2="",
            city="Philadelphia",
            state="PA",
            zip_code="19103",
            quantity=1,
            product_name="Ethiopian Single Origin",
            variant_info="Whole Bean",
            requires_shipping=True
        ),
        StickerData(
            order_name="SCC2030",
            customer_name="Perry Johnson",
            address_line1="456 Oak Ave",
            address_line2="",
            city="Philadelphia",
            state="PA",
            zip_code="19103",
            quantity=1,
            product_name="Colombian Blend",
            variant_info="Ground for Espresso",
            requires_shipping=True
        ),
    ]

    # Generate PDF
    import os
    os.makedirs("output", exist_ok=True)

    generator = PDFGenerator()
    pdf_path = generator.generate_pdf(sample_stickers, filename="test-stickers.pdf")

    print(f"\n{'='*60}")
    print("[OK] TEST COMPLETED SUCCESSFULLY")
    print(f"  Open the PDF: {pdf_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
