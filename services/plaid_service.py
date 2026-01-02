import hashlib
import logging
import os

import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest

from models.delta import TransactionsDelta
from models.transaction import Transaction

logger = logging.getLogger(__name__)


def create_plaid_client() -> plaid_api.PlaidApi:
    """Create and configure a Plaid API client."""
    configuration = plaid.Configuration(
        host=plaid.Environment.Production,
        api_key={
            "clientId": os.getenv("PLAID_CLIENT_ID"),
            "secret": os.getenv("PLAID_SECRET"),
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def hash_token(token: str) -> str:
    """Hash access token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def fetch_plaid_delta(
    client: plaid_api.PlaidApi,
    access_token: str,
    cursor: str,
    delta: TransactionsDelta,
) -> list[str]:
    """
    Fetch transaction delta from Plaid for a single access token.
    
    Mutates the provided TransactionsDelta with added, modified, deleted
    transactions and updates the cursor in meta.
    
    Args:
        client: Plaid API client
        access_token: Plaid access token
        cursor: Current cursor for this token (empty string for initial sync)
        delta: TransactionsDelta to populate (mutated in place)
        
    Returns:
        List of account names associated with this token
    """
    token_hash = hash_token(access_token)
    all_accounts: dict[str, str] = {}
    
    # Track counts for this token only
    added_count = 0
    modified_count = 0
    deleted_count = 0
    
    current_cursor = cursor
    
    while True:
        request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=current_cursor,
        ) if current_cursor else TransactionsSyncRequest(access_token=access_token)
        
        response = client.transactions_sync(request)
        
        # Build account lookup
        for account in response["accounts"]:
            all_accounts[account["account_id"]] = (
                account.get("official_name") or account["name"]
            )
        
        # Process added transactions
        for txn in response["added"]:
            account_name = all_accounts.get(txn["account_id"], "Unknown")
            transaction = Transaction.from_plaid(txn, account_name)
            delta.added[transaction.transaction_id] = transaction
            added_count += 1
        
        # Process modified transactions
        for txn in response["modified"]:
            account_name = all_accounts.get(txn["account_id"], "Unknown")
            transaction = Transaction.from_plaid(txn, account_name)
            delta.modified.append(transaction)
            modified_count += 1
        
        # Process removed transactions
        for txn in response["removed"]:
            delta.deleted.add(txn["transaction_id"])
            deleted_count += 1
        
        current_cursor = response["next_cursor"]
        
        if not response["has_more"]:
            break
    
    # Update meta with final cursor
    delta.meta[token_hash] = current_cursor
    
    account_names = list(all_accounts.values())
    logger.info(
        "Fetched delta for %s: %d added, %d modified, %d deleted",
        ", ".join(account_names) if account_names else "unknown accounts",
        added_count,
        modified_count,
        deleted_count,
    )
    
    return account_names
