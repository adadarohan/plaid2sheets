# plaid2sheets
A script to fetch transactions from Plaid and upload them to a Google Sheets spreadsheet for $0.30 / account / month. Run as a github action or locally.

## Setup
This project takes about 15 minutes to set up from scratch. However, it can take a few days for Plaid to approve your developer account for production access.

1. Create a [plaid developer account](https://my.plaid.com/sign-up), request production access and get your client ID and secret. Then, activate the `transactions` product.
I was able to get approved for production access by answering all security / compliance questions with the fact that this is only for personal use.

2. Get the access tokens for each item (credit card, bank acount) you want to get transactions for. You can do this through the [plaid postman collection](https://github.com/plaid/plaid-postman?tab=readme-ov-file#making-api-calls-with-real-data-in-production) (recomended) or the [plaid quickstart app](https://plaid.com/docs/quickstart/).

> [!WARNING]
> Do not lose or reveal your access tokens. Plaid bills you per access token (including duplicates). If you want to stop using your access tokens, you must remove them from the Plaid console, otherwise you will continued to be billed regardless of usage.

3. Create a [Google Sheets](sheets.google.com) spreadsheet where you would like the script to populate transactions. Create a worksheet with the name `transactions` and first row -

| transaction_id | account_name | amount | date | merchant_name | category | category_detailed |
|----------------|--------------|--------|------|---------------|----------|-------------------|

4. Fetch your Google Sheets API credentials by following steps 1 through 6 on the [gspread docs](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account). Then, share the spreadsheet you created in step 3 with the service account email found in the JSON file you downloaded in step 6.

5. Fork this repository, and add the following to the Github Actions Secrets (Settings -> Secrets and variables -> Actions):
- `PLAID_CLIENT_ID` - Your Plaid client ID from step 1
- `PLAID_SECRET` - Your Plaid secret (production) from step 1
- `PLAID_ACCESS_TOKENS` - Comma separated list of access tokens from step 2
- `GOOGLE_SHEETS_KEY` - The key from the URL of the spreadsheet you created in step 3 (e.g. `1_e6Otb9KqxgkfhOvGsY46dpWNJqZQ_i8Kyxk3-Sa3RA`) 
- `GOOGLE_SHEETS_CREDENTIALS` - The contents of the JSON file you downloaded in step 6 of the previous step.
Alternatively, you can create a `.env` and `google_sheets_credentials.json` file in the root of the project and run it locally.

6. On the Github website, go to Actions -> Money Sync -> Run workflow -> Run workflow to run the sync for the first time. Subsequent runs will be automatic based on the schedule defined in `.github/workflows/run-money-sync.yaml` (defaults to weekly updates).

## Common Issues
### Plaid Access Token "Something went wrong" only for certain accounts
If you see this error when trying to fetch transactions, it likely means that your Plaid account has not completed the OAuth flow for that particular institution. See [plaid oath page](https://dashboard.plaid.com/activity/status/oauth-institutions) for more details.

## Design Decisions and Notes
### Transaction Catergories
Plaid provides both a high level category (e.g. "Food and Drink") and a more detailed category (e.g. "Restaurants"). Both are included in the spreadsheet for flexibility. You can find the categories in the [plaid docs](https://plaid.com/docs/api/products/transactions/#transactions-sync-response-added-personal-finance-category-version).

### _meta Worksheet
Plaid requires us to keep track of the previous cursor when fetching transactions incrementally. This script uses a `_meta` worksheet in the same spreadsheet to store the cursor for each access token (hashed), along with the last run time. This worksheet is created automatically if it does not exist.

### Transaction IDs
Transaction IDs are kept in the spreadsheet for future support of the `removed` and `modified` arrays returned by the Plaid transactions sync endpoint. Currently, only new transactions are appended to the spreadsheet.