# Spiritus Coffee - Automated Fulfillment Sticker System

Automated system that generates daily fulfillment stickers from Shopify orders. Pulls unfulfilled orders and creates printable stickers (Avery 5160 format) for quick order fulfillment.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `env.env` file with your Shopify and email credentials:

```bash
# Shopify API Configuration
SHOPIFY_STORE_URL=https://your-store.myshopify.com
SHOPIFY_API_KEY=your_api_key
SHOPIFY_API_SECRET=your_api_secret
SHOPIFY_ACCESS_TOKEN=your_access_token
SHOPIFY_SHARED_SECRET=your_shared_secret

# Email Configuration (for automated email delivery)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_TO=recipient1@example.com,recipient2@example.com
EMAIL_SUBJECT=Daily Fulfillment Stickers - {date}
```

**Note for Gmail users:** Use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

### 3. Run the System

```bash
python src/main.py
```

This will:
- Connect to Shopify
- Retrieve unfulfilled orders (last 7 days)
- Filter out orders tagged "Ready For Pickup"
- Generate PDF with Avery 5160 labels
- Save to `output/fulfillment-stickers-YYYY-MM-DD.pdf`
- **Automatically email PDF to recipients** (if configured)

## What It Does

### Business Logic

- **One sticker per line item** (orders with multiple items get multiple stickers)
- **Local delivery cities:** Lombard, Glen Ellyn, Addison, Wheaton, Villa Park
- **Shipping indicator:** Orders outside local delivery area get red "**SHIP**" label
- **Automatic filtering:** Excludes orders tagged "Ready For Pickup"

### Each Sticker Contains

- Customer name
- Full shipping address
- Product name and quantity (e.g., "2x Ethiopian Blend")
- Variant details (e.g., "Whole Bean" or "Ground for Drip")

## Project Structure

```
seallabelprinter/
├── .github/
│   └── workflows/
│       └── daily-fulfillment-email.yml  # GitHub Actions workflow
├── src/
│   ├── main.py                 # Main orchestration script
│   ├── shopify_connector.py    # Shopify API integration
│   ├── order_processor.py      # Order processing & business logic
│   ├── pdf_generator.py        # PDF generation (Avery 5160)
│   └── email_sender.py         # Email delivery via SMTP
├── output/                     # Generated PDFs
├── env.env                     # Environment variables (not in git!)
├── requirements.txt            # Python dependencies
├── CLAUDE.md                   # Project instructions for Claude Code
├── PRD.md                      # Product requirements document
└── README.md                   # This file
```

## Testing Individual Modules

Each module can run standalone:

```bash
# Test Shopify connection
python src/shopify_connector.py

# Test order processing logic
python src/order_processor.py

# Test PDF generation
python src/pdf_generator.py

# Test email configuration (does not send actual email)
python src/email_sender.py
```

## Printing Instructions

1. Load **Avery 5160 label sheets** into your Toshiba printer
2. Open the generated PDF from `output/` directory
3. Print at **100% scale** (no scaling/fitting)
4. Use **color printing** (for red shipping indicators)
5. Apply stickers to order bags

## Local Delivery Cities

The following cities qualify for local delivery (no shipping label):
- Lombard
- Glen Ellyn
- Addison
- Wheaton
- Villa Park

All other cities will show a red **"SHIP"** indicator.

## Customization

### Change Number of Days to Look Back

Edit `src/main.py`:

```python
DAYS_BACK = 14  # Look back 14 days instead of 7
```

### Modify Local Delivery Cities

Edit `src/order_processor.py`:

```python
LOCAL_DELIVERY_CITIES = [
    "Lombard",
    "Glen Ellyn",
    "Addison",
    "Wheaton",
    "Villa Park",
    "Your New City"  # Add your city here
]
```

## Automated Daily Email via GitHub Actions

This repository includes a GitHub Actions workflow that automatically:
1. Runs daily at **7:00 AM Central Time**
2. Generates fulfillment stickers from Shopify orders
3. Emails the PDF to configured recipients
4. Archives PDFs for 30 days as workflow artifacts

### Setting Up GitHub Actions

#### 1. Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following secrets:

**Shopify Credentials:**
- `SHOPIFY_STORE_URL` - Your Shopify store URL (e.g., `https://your-store.myshopify.com`)
- `SHOPIFY_API_KEY` - Your Shopify API key
- `SHOPIFY_API_SECRET` - Your Shopify API secret
- `SHOPIFY_ACCESS_TOKEN` - Your Shopify access token
- `SHOPIFY_SHARED_SECRET` - Your Shopify shared secret

**Email Configuration:**
- `SMTP_SERVER` - SMTP server address (e.g., `smtp.gmail.com`)
- `SMTP_PORT` - SMTP port (e.g., `587`)
- `EMAIL_FROM` - Sender email address
- `EMAIL_PASSWORD` - Email password or app password
- `EMAIL_TO` - Recipient email addresses, comma-separated (e.g., `user1@example.com,user2@example.com`)
- `EMAIL_SUBJECT` - Email subject template (optional, default: `Daily Fulfillment Stickers - {date}`)

#### 2. Workflow Configuration

The workflow is located at `.github/workflows/daily-fulfillment-email.yml`

**Schedule:** Daily at 7:00 AM Central Time (12:00 UTC)

**Manual Trigger:** You can also run the workflow manually:
- Go to **Actions** tab in GitHub
- Select **Daily Fulfillment Sticker Email**
- Click **Run workflow**

#### 3. View Results

After each run:
- Check the **Actions** tab for workflow status
- Download generated PDFs from workflow artifacts (kept for 30 days)
- Recipients will receive the PDF via email automatically

### Alternative Scheduling Options

For local automation without GitHub Actions:

- **macOS/Linux:** cron job
- **Windows:** Task Scheduler
- **Cloud:** AWS Lambda + EventBridge, Google Cloud Scheduler

Example cron (7 AM daily):
```
0 7 * * * cd /path/to/seallabelprinter && python src/main.py
```

## Troubleshooting

### "Missing required Shopify credentials"
- Check that `env.env` file exists and contains all required variables
- Verify credentials are correct in Shopify admin

### No orders retrieved
- Check date range (default: last 7 days)
- Verify orders are marked as "unfulfilled" in Shopify
- Check that orders aren't tagged "Ready For Pickup"

### PDF alignment issues
- Ensure printing at 100% scale (no "fit to page")
- Use genuine Avery 5160 labels
- Check printer settings for correct paper size (Letter/8.5x11)

## Requirements

- Python 3.11+
- Shopify store with API access
- Avery 5160 label sheets
- Color printer (for shipping indicators)

## Security

⚠️ **IMPORTANT:** Never commit `env.env` to version control. It contains sensitive API credentials.

## Support

See `PRD.md` for complete product requirements and specifications.
