import logging
import os

from dotenv import load_dotenv

from models.delta import TransactionsDelta
from services.plaid_service import create_plaid_client, fetch_plaid_delta, hash_token
from services.reconciliation import local_reconcile
from services.sheets_service import (
    get_sheets_client,
    get_or_create_worksheet,
    load_meta,
    push_sheets_delta,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Main orchestration flow:
    1. Get meta info (cursors) from Google Sheets
    2. For each access token, fetch Plaid delta
    3. Local reconciliation against added transactions
    4. Push sheets delta to Google Sheets
    """
    load_dotenv()

    # Get meta info (cursors) from Google Sheets
    logger.info("Loading meta info from Google Sheets")
    gc = get_sheets_client()
    sh = gc.open_by_key(os.getenv("GOOGLE_SHEETS_KEY"))
    
    transactions_worksheet = get_or_create_worksheet(sh, "transactions")
    meta_worksheet = get_or_create_worksheet(sh, "_meta")
    
    cursors = load_meta(meta_worksheet)
    access_tokens = os.getenv("PLAID_ACCESS_TOKENS", "").split(",")
    
    # For each access token, fetch Plaid delta
    logger.info("Fetching Plaid deltas for %d token(s)", len(access_tokens))
    plaid_client = create_plaid_client()
    plaid_delta = TransactionsDelta()
    
    for access_token in access_tokens:
        token_hash = hash_token(access_token)
        cursor = cursors.get(token_hash, "")
        fetch_plaid_delta(plaid_client, access_token, cursor, plaid_delta)
    
    logger.info(
        "Plaid delta complete: %d added, %d modified, %d deleted",
        len(plaid_delta.added),
        len(plaid_delta.modified),
        len(plaid_delta.deleted),
    )
    
    # Local reconciliation
    logger.info("Running local reconciliation")
    sheets_delta = local_reconcile(plaid_delta)
    
    # Push sheets delta
    logger.info("Pushing sheets delta")
    push_sheets_delta(transactions_worksheet, meta_worksheet, sheets_delta)
    
    logger.info("Sync complete")


if __name__ == "__main__":
    main()
