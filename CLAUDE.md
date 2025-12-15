# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Automated Order Fulfillment Sticker System** for Spiritus Coffee Co.

This system automates the generation of daily fulfillment stickers from Shopify orders. It pulls unfulfilled orders each morning at 8:00 AM CT and generates printable stickers (Avery 5160 format) that employees can apply to bags for order fulfillment and delivery.

### Key Business Logic

1. **Order Filtering:**
   - Only retrieve orders with `fulfillment_status = "unfulfilled"`
   - Exclude orders tagged with "Ready For Pickup"
   - Pull orders created/updated within last 7 days (configurable)

2. **Sticker Generation:**
   - ONE sticker per line item (not per order)
   - Orders with multiple line items get separate stickers for each item
   - Format: Avery 5160 template (3 columns x 10 rows = 30 labels per sheet)

3. **Local Delivery vs Shipping Logic:**
   - **Local delivery cities:** Lombard, Glen Ellyn, Addison, Wheaton, Villa Park
   - Orders to cities NOT in this list are marked **"SHIP"** in bold red text at top of sticker
   - Local delivery orders have no special marking

4. **Sticker Content:**
   - Customer name (shipping name)
   - Full shipping address (Street, Address1, Address2, City, Zip)
   - Line item quantity and product name (format: "1x Product Name")
   - Variant details (e.g., "Whole Bean" vs "Ground for Drip")

## Environment Configuration

### Required Environment Variables (stored in `env.env`)

```bash
SHOPIFY_STORE_URL=https://spiritus-coffee-lombard.myshopify.com
SHOPIFY_API_KEY=<api_key>
SHOPIFY_API_SECRET=<api_secret>
SHOPIFY_ACCESS_TOKEN=<access_token>
SHOPIFY_SHARED_SECRET=<shared_secret>
```

**CRITICAL:** Never commit actual credentials to git. The `env.env` file should be in `.gitignore`.

## Shopify API Integration

### Required API Scopes
- `read_orders`: Access order information
- `write_orders`: Add tags to orders (optional feedback loop)
- `read_products`: Access product variant details

### Key API Endpoints

**Get Unfulfilled Orders:**
```
GET /admin/api/2024-10/orders.json?fulfillment_status=unfulfilled&created_at_min=YYYY-MM-DD&limit=250
```

**Update Order Tags (Optional):**
```
PUT /admin/api/2024-10/orders/{order_id}.json
Body: { "order": { "tags": "existing-tags, Sticker Printed - YYYY-MM-DD" } }
```

### Rate Limiting
- Shopify API limit: 2 requests/second for standard plans
- Implement retry logic with exponential backoff on rate limit hit
- Handle pagination for >250 orders

## PDF Generation Requirements

### Avery 5160 Template Specifications
- **Label Size:** 1" H x 2.625" W
- **Layout:** 3 columns x 10 rows (30 labels per sheet)
- **Page Size:** Letter (8.5" x 11")
- **Margins:**
  - Top/Bottom: 0.5"
  - Left/Right: 0.1875"
- **Label Spacing:**
  - Horizontal: 0.125" between columns
  - Vertical: 0" between rows

### Sticker Formatting
1. **Shipping Indicator:** Bold, red, 14pt font (top-left, only if NOT local delivery)
2. **Customer Name:** Bold, 11pt font
3. **Address:** Regular, 10pt font, stacked lines
4. **Product Info:** Regular, 9pt font, variant details indented
5. **Quantity:** Format as "1x" or "2x" before product name
6. **Line Spacing:** 1.2x for readability
7. **Font:** Arial or Helvetica

### File Output
- **Filename:** `fulfillment-stickers-YYYY-MM-DD.pdf`
- **Archive:** Keep PDFs for 30 days, then auto-delete

## Technology Stack Recommendations

### Option 1: Python (Recommended)
- **Language:** Python 3.11+
- **Scheduler:** AWS Lambda + EventBridge (or cron job)
- **Shopify Library:** `ShopifyAPI` or `pyactiveresource`
- **PDF Generation:** `ReportLab` (precise control) or `weasyprint` (HTML to PDF)
- **Dependencies:** Install via pip in virtual environment

### Option 2: Node.js
- **Language:** Node.js 18+
- **Scheduler:** Google Cloud Functions + Cloud Scheduler
- **Shopify Library:** `@shopify/shopify-api`
- **PDF Generation:** `PDFKit` or `puppeteer`

## Scheduler Configuration

- **Run Time:** 8:00 AM Central Time, daily
- **Retry Logic:** On failure, retry once after 15 minutes
- **Logging:** Log execution time, order count, errors
- **Alerts:** Email/SMS notification on failure
- **Manual Trigger:** Provide simple interface/command for manual runs

## Testing Checklist

### Critical Test Cases
- [ ] Single line item order
- [ ] Multiple line items order (generates multiple stickers)
- [ ] Local delivery city (no "SHIP" indicator)
- [ ] Non-local city (shows "SHIP" in red)
- [ ] Order with Address2 populated
- [ ] Very long product names (test truncation/wrapping)
- [ ] Empty result set (no orders)
- [ ] Order with "Ready For Pickup" tag (should be excluded)
- [ ] Print alignment on actual Avery 5160 labels

### City Name Handling
- Implement case-insensitive matching for city names
- Consider fuzzy matching for variations (e.g., "Villa Park" vs "VillaPark")

## Data Model Reference

```javascript
{
  "order_id": "6497728430319",
  "order_name": "SCC1981",
  "customer_name": "Kate Shovan",
  "shipping_address": {
    "street": "227 W North Ave",
    "address1": "227 W North Ave",
    "address2": "",
    "city": "Lombard",
    "zip": "60148",
    "province": "IL"
  },
  "line_items": [
    {
      "quantity": 1,
      "name": "Spiritus Coffee Subscription - Rotating Roasters Choice",
      "variant": "Rotating Lighter Roasts / Ground for Drip"
    }
  ],
  "tags": ["Ready For Pickup", "subscription order"],
  "is_local_delivery": true,
  "requires_shipping_label": false
}
```

## Error Handling

### Shopify API
- **Rate Limit Hit:** Wait and retry with exponential backoff
- **API Timeout:** Retry up to 3 times before failing
- **Invalid Response:** Log error, continue with other orders
- **Network Error:** Retry after 30 seconds

### PDF Generation
- **Invalid Address Data:** Log error, skip sticker generation for that item
- **PDF Write Failure:** Alert admin, retain order data for manual processing

## Security Notes

- Store all Shopify credentials in environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Use HTTPS/TLS 1.2+ for all API calls
- Store PDFs on secure network drive with access controls
- Auto-delete PDFs after 30 days for data minimization

## Project Files

- `PRD.md` - Complete product requirements document (reference for all functional and technical requirements)
- `env.env` - Environment variables (Shopify credentials) - **DO NOT COMMIT**
