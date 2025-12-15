# Product Requirements Document (PRD)
## Automated Order Fulfillment Sticker System

**Version:** 1.0  
**Date:** October 22, 2025  
**Status:** Draft  
**Owner:** Spiritus Coffee Co.

---

## Executive Summary

This document outlines the requirements for an automated system that generates daily fulfillment stickers from Shopify orders. The system will eliminate manual order processing by automatically pulling unfulfilled orders each morning, formatting them into printable stickers that employees can quickly apply to bags for order fulfillment and delivery.

---

## Problem Statement

### Current State
- Manual order processing requires employees to review orders each morning
- Time-consuming to transcribe customer information and order details onto bags
- Risk of errors in transcription or missed orders
- Difficult to quickly distinguish between local delivery and shipping orders

### Desired State
- Automated daily generation of fulfillment stickers at 8:00 AM
- One sticker per line item with customer information and product details
- Clear visual distinction between local delivery and shipping orders
- Ready-to-print format compatible with existing Toshiba network printer

---

## Goals & Success Metrics

### Primary Goals
1. Reduce morning prep time by 75% (from ~30 minutes to ~7 minutes)
2. Eliminate manual transcription errors (target: 0 errors per week)
3. Enable any employee to quickly understand and fulfill orders
4. Streamline the pickup vs. shipping workflow

### Success Metrics
- **Efficiency:** Time from order review to fulfillment start < 10 minutes
- **Accuracy:** 100% of orders have correctly printed stickers
- **Reliability:** System runs successfully 99%+ of scheduled times
- **User Satisfaction:** Employees rate system 4.5/5 or higher for ease of use

---

## User Stories

### As a shop employee, I want to:
- Arrive each morning and have stickers already printed and ready to use
- Quickly identify which orders are local delivery vs. shipping
- See all product details clearly on one sticker per item
- Apply stickers to bags without referencing additional documentation
- Know immediately which address each order goes to

### As a business owner, I want to:
- Automatically pull new orders daily without manual intervention
- Only print stickers for orders that need fulfillment (unfulfilled, not yet marked for pickup)
- Avoid duplicate stickers if the system runs multiple times
- Have a reliable, low-maintenance system that integrates with our existing workflow

---

## Functional Requirements

### Core Functionality

#### FR1: Daily Automated Execution
- **FR1.1:** System runs automatically at 8:00 AM Central Time daily
- **FR1.2:** System logs execution time and status for monitoring
- **FR1.3:** On failure, system sends notification and retries once after 15 minutes
- **FR1.4:** Manual trigger option available through simple interface or command

#### FR2: Shopify Order Retrieval
- **FR2.1:** Connect to Shopify API using secure credentials
- **FR2.2:** Query all orders with `fulfillment_status = "unfulfilled"`
- **FR2.3:** Filter OUT orders tagged with "Ready For Pickup"
- **FR2.4:** Pull orders created/updated within last 7 days (configurable)
- **FR2.5:** Handle pagination for large order volumes (>250 orders)

#### FR3: Sticker Generation Logic
- **FR3.1:** Generate ONE sticker per line item (not per order)
- **FR3.2:** For orders with multiple line items, create separate stickers for each item
- **FR3.3:** Each sticker includes:
  - Customer name (Shipping Name)
  - Full shipping address (Street, Address1, Address2, City, Zip)
  - Line item quantity and product name
  - Variant details (e.g., "Whole Bean" vs "Ground for Drip")
- **FR3.4:** Format matches Avery 5160 template (3 columns x 10 rows = 30 labels per sheet)
- **FR3.5:** Use clear, readable font (Arial or Helvetica, 10-11pt)

#### FR4: Shipping Indicator
- **FR4.1:** System identifies order city from shipping address
- **FR4.2:** Local delivery cities: Lombard, Glen Ellyn, Addison, Wheaton, Villa Park
- **FR4.3:** Orders with cities NOT in the local list are marked "**SHIP**" in bold at top of sticker
- **FR4.4:** Orders with cities in the local list have no special marking (default)
- **FR4.5:** Shipping indicator uses bold, red text for visibility

#### FR5: Print Output
- **FR5.1:** Generate PDF formatted for Avery 5160 template
- **FR5.2:** PDF saved to designated network folder with naming convention: `fulfillment-stickers-YYYY-MM-DD.pdf`
- **FR5.3:** Optional: Auto-send to Toshiba network printer queue
- **FR5.4:** Maintain print history folder with last 30 days of generated PDFs

#### FR6: Order Processing Feedback Loop
- **FR6.1:** After sticker generation, optionally tag orders in Shopify with "Sticker Printed - [Date]"
- **FR6.2:** This tag enables tracking and prevents confusion if system runs multiple times
- **FR6.3:** Tag should be configurable (can be disabled if not desired)

---

## Technical Requirements

### System Architecture

#### Component 1: Scheduler
- **Platform:** Cloud-based scheduler (AWS EventBridge, Google Cloud Scheduler, or cron job)
- **Frequency:** Daily at 8:00 AM Central Time
- **Reliability:** Automated monitoring and retry logic

#### Component 2: Shopify Integration Module
- **API:** Shopify REST Admin API or GraphQL API
- **Authentication:** Private app credentials or OAuth
- **Rate Limiting:** Respect Shopify API rate limits (2 requests/second for standard plans)
- **Data Retrieved:**
  - Order ID, Name (e.g., "SCC1982")
  - Customer name
  - Shipping address (all fields)
  - Line items with quantities and product details
  - Tags
  - Fulfillment status

#### Component 3: Sticker Generation Engine
- **Input:** JSON array of order data from Shopify
- **Processing:**
  - Parse orders into individual line items
  - Apply shipping logic (check city against local delivery list)
  - Format text for sticker layout
- **Output:** PDF file formatted for Avery 5160

#### Component 4: PDF Generation Library
- **Technology Options:**
  - Python: ReportLab, PyPDF2, or weasyprint
  - Node.js: PDFKit or Puppeteer
  - Ruby: Prawn
- **Template:** Avery 5160 dimensions (1" x 2-5/8", 30 labels per page)
- **Margin Handling:** Precise alignment to ensure labels print correctly

#### Component 5: File Management & Printing
- **Storage:** Network drive or cloud storage (accessible by printer)
- **Printing Options:**
  - Option A: Auto-send to printer via network printing protocol
  - Option B: Save to watched folder that printer monitors
  - Option C: Save to shared folder for manual printing
- **Archival:** Keep PDFs for 30 days with automatic cleanup

### Data Model

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

### Infrastructure Requirements

#### Hosting
- **Recommended:** Cloud platform (AWS Lambda, Google Cloud Functions, or dedicated VPS)
- **Alternative:** On-premises server if security requirements mandate
- **Uptime:** 99.5% minimum

#### Credentials Storage
- **Shopify API Key:** Stored in environment variables or secrets manager
- **Printer Credentials:** Stored securely (if direct printing)
- **Encryption:** All credentials encrypted at rest

#### Monitoring & Logging
- **Execution Logs:** Every run logged with timestamp, orders processed, errors
- **Alerts:** Email/SMS notification on failure
- **Dashboard:** Optional web dashboard showing recent runs and status

---

## User Interface / Output Specifications

### Sticker Layout (Avery 5160)

```
┌─────────────────────────────────────┐
│ **SHIP**                   [if not local]
│                                     │
│ Kate Shovan                         │
│ 227 W North Ave                     │
│ Lombard, IL 60148                   │
│                                     │
│ 1x Spiritus Coffee Subscription    │
│    Rotating Lighter Roasts          │
│    Ground for Drip                  │
└─────────────────────────────────────┘
```

### Sticker Formatting Rules
1. **Shipping Indicator:** Bold, red, 14pt font, top-left if applicable
2. **Customer Name:** Bold, 11pt font
3. **Address:** Regular, 10pt font, address lines stacked
4. **Product Info:** Regular, 9pt font, indented for variant details
5. **Quantity:** Format as "2x" or "1x" before product name
6. **Line Spacing:** 1.2x for readability

### PDF Output
- **Filename Format:** `fulfillment-stickers-2025-10-22.pdf`
- **Page Size:** Letter (8.5" x 11")
- **Orientation:** Portrait
- **Margins:** Match Avery 5160 template exactly
  - Top: 0.5"
  - Bottom: 0.5"
  - Left: 0.1875"
  - Right: 0.1875"
- **Label Dimensions:** 1" H x 2.625" W
- **Labels per page:** 30 (3 columns x 10 rows)

---

## Integration Specifications

### Shopify API Integration

#### Required API Scopes
- `read_orders`: Access order information
- `write_orders`: Add tags to orders (if using feedback loop)
- `read_products`: Access product variant details

#### API Endpoints

**Get Unfulfilled Orders:**
```
GET /admin/api/2024-10/orders.json?fulfillment_status=unfulfilled&created_at_min=YYYY-MM-DD&limit=250
```

**Get Order Details:**
```
GET /admin/api/2024-10/orders/{order_id}.json
```

**Update Order Tags (Optional):**
```
PUT /admin/api/2024-10/orders/{order_id}.json
Body: { "order": { "tags": "existing-tags, Sticker Printed - 2025-10-22" } }
```

#### Error Handling
- **Rate Limit Hit:** Wait and retry with exponential backoff
- **API Timeout:** Retry up to 3 times before failing
- **Invalid Response:** Log error and continue with other orders
- **Network Error:** Retry after 30 seconds

### Printer Integration

#### Network Printer Setup
- **Printer:** Toshiba network printer
- **Connection Method:** 
  - Option 1: Direct network printing via IP address
  - Option 2: Windows/Mac network shared printer
  - Option 3: Print to PDF in network folder (manual print)

#### Print Job Configuration
- **Paper Size:** Letter (8.5" x 11")
- **Paper Type:** Avery 5160 label sheets
- **Print Quality:** Normal (300 DPI minimum)
- **Color:** Color (for red shipping indicator)
- **Duplex:** Off (single-sided)

---

## Security & Compliance

### Data Security
- **API Credentials:** Stored in secure environment variables or secrets manager (AWS Secrets Manager, HashiCorp Vault)
- **Data in Transit:** All API calls use HTTPS/TLS 1.2+
- **Data at Rest:** PDFs stored on secure network drive with access controls
- **Retention:** PDFs deleted after 30 days automatically

### Access Control
- **System Access:** Limited to IT administrator and business owner
- **Printer Access:** All employees (read-only for PDFs)
- **API Access:** Service account with minimal required permissions

### Privacy
- **Customer Data:** Customer addresses only used for order fulfillment
- **Data Minimization:** Only retrieve necessary order fields
- **Compliance:** Ensure alignment with any PCI DSS requirements (if handling payment data)

---

## Testing & Validation

### Unit Testing
- [ ] Shopify API connection and authentication
- [ ] Order filtering logic (unfulfilled, exclude "Ready For Pickup" tag)
- [ ] Sticker generation for single line item
- [ ] Sticker generation for multiple line items
- [ ] Shipping indicator logic (local vs. non-local cities)
- [ ] PDF formatting and Avery 5160 alignment

### Integration Testing
- [ ] End-to-end flow: API → Processing → PDF generation
- [ ] Scheduler triggers at correct time
- [ ] Error handling and retry logic
- [ ] Network printer communication
- [ ] File storage and naming conventions

### User Acceptance Testing (UAT)
- [ ] Print test page and verify alignment on Avery 5160 labels
- [ ] Employee reviews stickers for readability and completeness
- [ ] Test with various order types (subscription, one-time, multiple items)
- [ ] Verify shipping indicators appear correctly
- [ ] Confirm local delivery orders have no shipping indicator

### Edge Cases
- [ ] Order with very long product name (truncation handling)
- [ ] Order with multiple address lines (Address2 populated)
- [ ] Order with no line items (should skip)
- [ ] Order with 5+ line items (generates 5+ stickers)
- [ ] City name with variations (e.g., "Villa Park" vs "Villa park")
- [ ] No orders available (empty result set)

---

## Timeline & Milestones

### Phase 1: Development & Testing (Weeks 1-2)
- **Week 1:**
  - Set up Shopify API connection
  - Implement order retrieval and filtering logic
  - Create sticker generation engine
  - Develop PDF output module
- **Week 2:**
  - Integrate all components
  - Implement scheduler
  - Unit testing
  - Integration testing

### Phase 2: UAT & Refinement (Week 3)
- Print test stickers on actual Avery 5160 labels
- Employee training and feedback
- Adjust formatting based on feedback
- Final bug fixes

### Phase 3: Deployment (Week 4)
- Deploy to production environment
- Configure scheduler for 8:00 AM daily run
- Set up monitoring and alerts
- Create documentation and runbook

### Phase 4: Monitoring & Optimization (Ongoing)
- Monitor daily execution logs
- Gather employee feedback
- Optimize performance as needed
- Implement future enhancements

---

## Future Enhancements (Post-MVP)

### Priority 1 (Next 3 Months)
1. **Mobile App:** View generated stickers on tablet for quick reference
2. **Barcode Integration:** Add QR code to stickers for scanning during fulfillment
3. **Fulfillment Confirmation:** Scan sticker to mark order as fulfilled in Shopify

### Priority 2 (6 Months)
4. **Batch Management:** Group stickers by delivery route or fulfillment priority
5. **Custom Sorting:** Allow employees to choose sort order (alphabetical, by city, by product)
6. **SMS Notifications:** Text message to owner if unusual number of orders (too many/few)

### Priority 3 (12 Months)
7. **Thermal Printer Support:** Add option to print on thermal label printer (4"x6" format)
8. **Multi-Location:** Support multiple fulfillment locations if business expands
9. **Inventory Integration:** Show low-stock warnings for items on stickers

---

## Assumptions & Dependencies

### Assumptions
1. Shopify API access remains available and reliable
2. Network printer is accessible during business hours
3. Avery 5160 label sheets are consistently stocked
4. Internet connection is stable for API calls
5. Orders are entered into Shopify in a timely manner (before 8:00 AM)

### Dependencies
1. **Shopify API:** System relies on Shopify API uptime and performance
2. **Network Printer:** Requires functional network printer
3. **Hosting Provider:** Cloud hosting service (AWS, Google Cloud, etc.) must be operational
4. **Label Supply:** Business must maintain inventory of Avery 5160 sheets

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Shopify API downtime | High | Low | Implement retry logic; manual fallback process |
| Incorrect label alignment | Medium | Medium | Thorough testing with actual labels; template adjustment tool |
| Scheduler failure | High | Low | Monitoring alerts; manual trigger option |
| Network printer offline | Medium | Medium | Save PDFs to folder; print manually if needed |
| City name variations | Low | Medium | Fuzzy matching or city normalization logic |

---

## Success Criteria & Definition of Done

### MVP Must-Haves
- [x] System runs automatically at 8:00 AM daily
- [x] Retrieves all unfulfilled orders without "Ready For Pickup" tag
- [x] Generates one sticker per line item
- [x] Displays shipping indicator for non-local orders
- [x] Outputs PDF in Avery 5160 format
- [x] PDF prints correctly on Toshiba network printer
- [x] Employees can fulfill orders using stickers alone

### Definition of Done
- All functional requirements implemented
- All tests passing (unit, integration, UAT)
- Documentation complete (user guide, technical docs, runbook)
- System deployed to production
- Employees trained on new process
- Monitoring and alerts configured
- Two weeks of successful daily execution

---

## Appendix

### A. Avery 5160 Template Specifications
- **Product:** Avery 5160 Easy Peel Address Labels
- **Label Size:** 1" x 2-5/8"
- **Labels Per Sheet:** 30
- **Layout:** 3 columns x 10 rows
- **Label Spacing:** 
  - Horizontal: 0.125" between columns
  - Vertical: 0" between rows
- **Sheet Dimensions:** 8.5" x 11"

### B. Local Delivery Cities
- Lombard
- Glen Ellyn
- Addison
- Wheaton
- Villa Park

### C. Sample Order Data
See attached: `sample_orders_export.csv`

### D. Sample Sticker Template
See attached: `sample_address_template.pdf`

### E. Technical Stack Recommendations

**Option 1: Python-Based**
- **Language:** Python 3.11+
- **Scheduler:** AWS Lambda + EventBridge
- **Shopify Library:** `ShopifyAPI` or `pyactiveresource`
- **PDF Generation:** `ReportLab` or `weasyprint`
- **Hosting:** AWS Lambda (serverless)

**Option 2: Node.js-Based**
- **Language:** Node.js 18+
- **Scheduler:** Google Cloud Functions + Cloud Scheduler
- **Shopify Library:** `@shopify/shopify-api`
- **PDF Generation:** `PDFKit` or `puppeteer`
- **Hosting:** Google Cloud Functions

**Option 3: Low-Code**
- **Platform:** Zapier or Make.com (Integromat)
- **Limitation:** May require custom code for PDF generation
- **Pros:** Faster initial setup, visual workflow
- **Cons:** Less flexible for complex formatting

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | [Owner Name] | | |
| Technical Lead | [Tech Lead] | | |
| Operations Manager | [Ops Manager] | | |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-22 | Claude | Initial PRD creation |

---

**End of Document**