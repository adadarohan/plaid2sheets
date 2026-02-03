<div align="center">

# plaid2sheets

**Automated personal finance tracking made simple**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

*Sync your bank transactions to Google Sheets automatically for just **$0.30 per account per month***

[Features](#features) • [Quick Start](#quick-start) • [Setup](#setup) • [Troubleshooting](#troubleshooting)

</div>

---

## Overview

`plaid2sheets` is a lightweight automation tool that syncs your financial transactions from Plaid directly to Google Sheets. Perfect for personal finance tracking without expensive subscription services.

### Features

- **Multi-Account Support** — Connect unlimited bank accounts and credit cards
- **Incremental Sync** — Uses Plaid's sync API to avoid duplicates
- **Rich Categories** — Includes both high-level and detailed transaction categories
- **Zero Infrastructure** — Run locally or use GitHub Actions (free tier included)
- **Cost Effective** — Only pay Plaid's API fees ($0.30/account/month)
- **Privacy First** — Your data stays between Plaid and your Google Sheet


## Setup

> **Setup time:** ~15 minutes  
> **Note:** Plaid production access approval may take 2-5 business days

### Step 1: Create a Plaid Developer Account

1. Sign up at [Plaid Dashboard](https://my.plaid.com/sign-up)
2. Request **production access**
3. Enable the **Transactions** product
4. Save your **Client ID** and **Secret**

<details>
<summary>Tips for production approval</summary>

For personal-use projects, approval is typically straightforward. In your application:
- Clearly state this is for **personal use only**
- Mention that **no third parties** will access the data
- Explain you're building a personal finance tracker

</details>

### Step 2: Generate Access Tokens

Create a Plaid access token for each bank account or credit card you want to sync.

**Recommended methods:**

| Method | Link | Best For |
|--------|------|----------|
| Plaid Postman | [plaid/plaid-postman](https://github.com/plaid/plaid-postman) | Quick API testing |
| Plaid Quickstart | [Quickstart Guide](https://plaid.com/docs/quickstart/) | Full UI experience |

> **IMPORTANT: Access Token Security**
> 
> - Never commit tokens to version control
> - Each token costs $0.30/month — including duplicates!
> - Deleting tokens from code ≠ stopping billing
> - **Always delete unused tokens** from the [Plaid Dashboard](https://dashboard.plaid.com)

### Step 3: Create Your Google Sheet

1. Create a new [Google Sheets](https://sheets.google.com) spreadsheet
2. Add a worksheet named `transactions`
3. Add this exact header row:

```
Transaction ID | Account Name | Amount | Date | Merchant Name | Category | Detailed Category
```

### Step 4: Set Up Google Sheets API Access

1. Follow **steps 1-6** in the [gspread service account guide](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account)
2. Download the service account credentials JSON
3. Copy the **service account email** from the JSON
4. Share your spreadsheet with that email (grant **Editor** access)

### Step 5: Configure Secrets

#### For GitHub Actions (Recommended)

Fork this repository and add these secrets in **Settings → Secrets and variables → Actions**:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `PLAID_CLIENT_ID` | Your Plaid client ID | `5f8a...` |
| `PLAID_SECRET` | Your Plaid production secret | `abc123...` |
| `PLAID_ACCESS_TOKENS` | Comma-separated access tokens | `access-prod-abc,access-prod-xyz` |
| `GOOGLE_SHEETS_KEY` | Spreadsheet ID from URL | `1_e6Otb9K...Sa3RA` |
| `GOOGLE_SHEETS_CREDENTIALS` | Full service account JSON contents | `{"type": "service_account"...}` |

#### For Local Execution

Create these files in the project root:

**`.env`** (see `.env.example` for template)
```env
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ACCESS_TOKENS=token1,token2
GOOGLE_SHEETS_KEY=your_spreadsheet_id
```

**`google_sheets_credentials.json`**
```json
{
  "type": "service_account",
  "project_id": "...",
  ...
}
```

### Step 6: Run the Sync

#### GitHub Actions
1. Go to **Actions → Money Sync → Run workflow**
2. Click **Run workflow** to test
3. Verify transactions appear in your sheet
4. Subsequent runs happen automatically (weekly by default, configured in `.github/workflows/run-money-sync.yaml`)

#### Local Execution
```bash
python main.py
```

---

## Troubleshooting

### "Something went wrong" error for specific banks

**Symptoms:** Transaction sync fails only for certain financial institutions

**Solution:** The OAuth flow for that institution may be incomplete. Check Plaid's OAuth status:
- [OAuth Institutions Status](https://dashboard.plaid.com/activity/status/oauth-institutions)

### Duplicate transactions appearing

**Cause:** The sync cursor was reset or lost

**Solution:** Check the `_meta` worksheet in your Google Sheet. Each access token (hashed) should have a cursor value.

### Missing transactions

**Possible causes:**
1. First sync only fetches recent transactions (typically 30 days)
2. Check Plaid's [transaction history](https://plaid.com/docs/api/products/transactions/#transactions-sync) limits
3. Verify the account is properly linked in Plaid Dashboard

---

## Architecture & Design

### Transaction Categories

Plaid provides both:
- A high-level category (e.g. `Food and Drink`)
- A detailed category (e.g. `Restaurants`)

Both are stored to allow downstream filtering or custom logic.  
Category definitions come from [Plaid’s Transactions API](https://plaid.com/docs/api/products/transactions/#transactions-sync-response-added-personal-finance-category).

### `_meta` worksheet

Plaid requires a cursor to fetch transactions incrementally.

This project stores:
- The cursor (per hashed access token)
- The last sync timestamp

These are kept in a `_meta` worksheet in the same spreadsheet.  
The worksheet is created automatically if it does not exist.


### Reconciliation Philosophy

Transaction reconciliation is intentionally **decoupled** from syncing. This enables:

- Custom categorization rules
- Manual transaction overrides  
- Business-specific logic
- Integration with other tools

---

## Sheet Format

Your `transactions` worksheet will be populated with:

| Column | Description | Example |
|--------|-------------|---------|
| Transaction ID | Unique Plaid identifier | `AbCdEf123` |
| Account Name | Institution name | `Chase Freedom` |
| Amount | Transaction amount (negative = expense) | `-42.50` |
| Date | Transaction date | `2026-02-01` |
| Merchant Name | Store or service | `Whole Foods Market` |
| Category | High-level category | `Food and Drink` |
| Detailed Category | Specific category | `Groceries` |

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Open an issue first to discuss proposed changes
2. Update documentation as needed
3. Add tests if applicable

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Disclaimer

This project is not affiliated with Plaid Inc. Use at your own risk. Always review your financial data for accuracy and keep your credentials secure.

---

<div align="center">

**Built with ❤️ for personal finance nerds**

[Report Bug](https://github.com/adadarohan/plaid2sheets/issues) · [Request Feature](https://github.com/adadarohan/plaid2sheets/issues)

</div>