import os
import csv
import hashlib
from datetime import datetime, timezone
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
import gspread


def get_or_create_worksheet(spreadsheet, name):
    """Get worksheet by name, create if it doesn't exist."""
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=20)


def load_cursors_from_meta(meta_worksheet):
    """Load cursor mappings from _meta worksheet."""
    cursors = {}
    try:
        records = meta_worksheet.get_all_values()
        for row in records:
            if len(row) >= 2 and row[0] != 'last_run_time_utc':
                cursors[row[0]] = row[1]
    except Exception:
        pass
    return cursors


def save_meta(meta_worksheet, cursors):
    """Save metadata to _meta worksheet."""
    meta_worksheet.clear()
    rows = [['last_run_time_utc', datetime.now(timezone.utc).isoformat()]]
    for token_hash, cursor in cursors.items():
        rows.append([token_hash, cursor])
    meta_worksheet.update(range_name='A1', values=rows)


def hash_token(token):
    """Hash access token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def main():
    # Load environment variables
    load_dotenv()

    # Plaid configuration
    configuration = plaid.Configuration(
        host=plaid.Environment.Production,
        api_key={
            'clientId': os.getenv('PLAID_CLIENT_ID'),
            'secret': os.getenv('PLAID_SECRET'),
        }
    )
    api_client = plaid.ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)

    access_tokens = os.getenv('PLAID_ACCESS_TOKENS').split(',')

    # Setup Google Sheets
    gc = gspread.service_account(filename='google_sheets_credentials.json')
    sh = gc.open_by_key(os.getenv('GOOGLE_SHEETS_KEY'))
    
    transactions_worksheet = get_or_create_worksheet(sh, 'transactions')
    meta_worksheet = get_or_create_worksheet(sh, '_meta')
    
    # Load existing cursors
    cursors = load_cursors_from_meta(meta_worksheet)

    all_transactions = []
    all_accounts = {}
    
    for access_token in access_tokens:
        token_hash = hash_token(access_token)
        cursor = cursors.get(token_hash, '')
        
        while True:
            if cursor:
                request = TransactionsSyncRequest(
                    access_token=access_token,
                    cursor=cursor
                )
            else:
                request = TransactionsSyncRequest(
                    access_token=access_token
                )
            response = client.transactions_sync(request)
            
            # Build account lookup
            for account in response['accounts']:
                all_accounts[account['account_id']] = account.get('official_name') or account['name']
            
            # Process added transactions
            for txn in response['added']:
                account_name = all_accounts.get(txn['account_id'], 'Unknown')
                personal_finance = txn.get('personal_finance_category', {})
                merchant_name = txn.get('merchant_name') or txn.get('name') or ''
    
                all_transactions.append([
                    txn['transaction_id'],
                    account_name,
                    txn['amount'],
                    str(txn['date']),
                    merchant_name,
                    personal_finance.get('primary') or '',
                    personal_finance.get('detailed') or ''
                ])
            
            cursor = response['next_cursor']
            cursors[token_hash] = cursor
            
            if not response['has_more']:
                break

    print(f"Fetched {len(all_transactions)} transactions")

    # Upload to Google Sheets
    if all_transactions:
        transactions_worksheet.append_rows(all_transactions)
        print(f"Uploaded {len(all_transactions)} transactions to Google Sheets")
    
    # Save metadata
    save_meta(meta_worksheet, cursors)
    print("Updated _meta worksheet")


if __name__ == "__main__":
    main()
