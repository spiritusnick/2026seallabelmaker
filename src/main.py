"""
Main Orchestration Script

Coordinates all modules to generate fulfillment stickers:
1. Connect to Shopify
2. Retrieve unfulfilled orders
3. Filter orders (exclude "Ready For Pickup")
4. Process into sticker data
5. Generate PDF with Avery 5160 format
"""

import os
import sys
from datetime import datetime
from shopify_connector import ShopifyConnector
from order_processor import OrderProcessor
from pdf_generator import PDFGenerator
from email_sender import EmailSender


def run_sticker_generation(days_back: int = 10, output_dir: str = "output", auto_email: bool = True):
    """
    Main workflow to generate fulfillment stickers.

    Args:
        days_back: Number of days to look back for orders
        output_dir: Directory to save PDF output
        auto_email: If True, automatically send PDF via email

    Returns:
        Path to generated PDF file
    """
    print("="*70)
    print("SPIRITUS COFFEE - AUTOMATED FULFILLMENT STICKER GENERATION")
    print("="*70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Step 1: Connect to Shopify and retrieve orders
        print("[1/5] Connecting to Shopify...")
        connector = ShopifyConnector()

        print("[2/5] Retrieving unfulfilled orders...")
        orders = connector.get_unfulfilled_orders(days_back=days_back)

        if not orders:
            print("\n[WARNING] No unfulfilled orders found.")
            print("   No stickers to generate.\n")
            connector.close()
            return None

        # Step 2: Filter orders
        print("[3/5] Filtering orders...")
        filtered_orders = connector.filter_orders(orders, exclude_tag="Ready For Pickup")

        if not filtered_orders:
            print("\n[WARNING] All orders filtered out (tagged 'Ready For Pickup').")
            print("   No stickers to generate.\n")
            connector.close()
            return None

        # Step 3: Process orders into sticker data
        print("[4/5] Processing orders into sticker data...")
        processor = OrderProcessor()
        stickers = processor.create_stickers_from_orders(filtered_orders)

        if not stickers:
            print("\n[WARNING] No stickers generated from orders.")
            print("   Check that orders have valid line items and addresses.\n")
            connector.close()
            return None

        print(f"[OK] Generated {len(stickers)} stickers from {len(filtered_orders)} orders")

        # Display breakdown
        local_count = sum(1 for s in stickers if not s.requires_shipping)
        shipping_count = sum(1 for s in stickers if s.requires_shipping)
        print(f"  - Local delivery: {local_count}")
        print(f"  - Requires shipping: {shipping_count}")

        # Step 4: Generate PDF
        print("[5/5] Generating PDF...")
        generator = PDFGenerator(output_dir=output_dir)
        pdf_path = generator.generate_pdf(stickers)

        # Close Shopify connection
        connector.close()

        # Success summary
        print(f"\n{'='*70}")
        print("[OK] STICKER GENERATION COMPLETED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"\nPDF file: {pdf_path}")
        print(f"Total stickers: {len(stickers)}")
        print(f"Orders processed: {len(filtered_orders)}")

        # Auto-email if requested
        if auto_email:
            print(f"\n{'='*70}")
            print("[EMAIL] Sending PDF via email...")
            try:
                email_sender = EmailSender()
                additional_info = f"Local delivery: {local_count} | Requires shipping: {shipping_count}"
                email_success = email_sender.send_pdf(pdf_path, order_count=len(stickers), additional_info=additional_info)

                if email_success:
                    print(f"[OK] Email sent successfully!")
                else:
                    print(f"[WARNING] Email failed to send. Check email configuration in env.env")
            except Exception as e:
                print(f"[WARNING] Email error: {e}")
            print(f"{'='*70}")

        print(f"\nNext steps:")
        print(f"  1. Open the PDF: {pdf_path}")
        print(f"  2. Load Avery 5160 labels into printer")
        print(f"  3. Print the PDF")
        print(f"  4. Apply stickers to order bags\n")

        return pdf_path

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for the script."""
    # ==========================================
    # CONFIGURATION - Customize these settings
    # ==========================================
    DAYS_BACK = 10          # Look back 10 days for orders
    OUTPUT_DIR = "output"   # Directory to save PDFs
    AUTO_EMAIL = True       # Set to True to automatically send PDF via email

    # ==========================================

    run_sticker_generation(days_back=DAYS_BACK, output_dir=OUTPUT_DIR, auto_email=AUTO_EMAIL)


if __name__ == "__main__":
    main()
