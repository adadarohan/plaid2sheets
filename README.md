# plaid2sheets

`plaid2sheets` fetches transactions from Plaid and syncs them to a Google Sheets spreadsheet for  **$0.30 per account per month**.  
It can be run locally or on a schedule using GitHub Actions.

## Overview

- Pulls transactions from one or more Plaid items (credit cards, bank accounts)
- Writes normalized transaction data to a Google Sheet
- Uses Plaid’s incremental sync API to avoid duplicates
- Requires no paid infrastructure beyond Plaid itself

## Setup

Initial setup takes about **15 minutes**, but **Plaid production access approval may take a few days**.

### 1. Create a Plaid developer account

- Sign up at https://my.plaid.com/sign-up
- Request **production access**
- Enable the **Transactions** product
- Note your **Client ID** and **Secret**

For personal-use projects, production access approval is typically straightforward if you clearly state that no third parties will access the data.

### 2. Generate access tokens

Create a Plaid access token for each account (bank, credit card) you want to sync.

Recommended methods:
- Plaid Postman collection (recommended):  
  https://github.com/plaid/plaid-postman
- Plaid Quickstart app:  
  https://plaid.com/docs/quickstart/

> **Warning**  
> Do not lose or expose access tokens.  
> Plaid bills per access token (including duplicates). Removing tokens from your code is **not sufficient**—you must delete unused tokens from the Plaid dashboard to stop billing.

### 3. Create the Google Sheet

Create a Google Sheets spreadsheet and add a worksheet named **`transactions`** with the following header row:

| Transaction ID | Account Name | Amount | Date | Merchant Name | Category | Detailed Category |
|----------------|--------------|--------|------|---------------|----------|-------------------|

### 4. Set up Google Sheets API access

Follow **steps 1–6** in the gspread service account guide:  
https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account

After downloading the credentials JSON:
- Copy the **service account email**
- Share your spreadsheet (from step 3) with that email, with **Editor** access


### 5. Configure secrets

Fork this repository and add the following **GitHub Actions secrets**  
(Settings → Secrets and variables → Actions):

- `PLAID_CLIENT_ID`  
  Plaid client ID
- `PLAID_SECRET`  
  Plaid production secret
- `PLAID_ACCESS_TOKENS`  
  Comma-separated list of access tokens
- `GOOGLE_SHEETS_KEY`  
  Spreadsheet ID from the Google Sheets URL  
  (e.g. `1_e6Otb9KqxgkfhOvGsY46dpWNJqZQ_i8Kyxk3-Sa3RA`)
- `GOOGLE_SHEETS_CREDENTIALS`  
  Full contents of the service account JSON file

**Local execution:**  
Instead of GitHub secrets, you may create:
- a `.env` file (see `.env.example` for format)
- a `google_sheets_credentials.json` file in the project root with the service account JSON

### 6. Run the workflow

- Go to **Actions → Money Sync → Run workflow**
- Run it once manually to verify setup
- Subsequent runs follow the schedule defined in  
  `.github/workflows/run-money-sync.yaml` (weekly by default)

## Common Issues

### Plaid access token fails for specific institutions

If transaction sync fails with a generic “Something went wrong” error for only some accounts, the OAuth flow for that institution may be incomplete.

Check Plaid’s OAuth status page:  
https://dashboard.plaid.com/activity/status/oauth-institutions


## Design Decisions and Notes

### Transaction categories

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


### Local reconciliation

Transaction reconciliation is intentionally kept separate from syncing.  
This allows future extensions such as:
- Custom categorization
- Manual overrides
- Business-specific logic