import logging
import os
from datetime import datetime, timezone

import gspread

from models.delta import TransactionsDelta

logger = logging.getLogger(__name__)


def get_sheets_client() -> gspread.Client:
    """Create a Google Sheets client using service account credentials."""
    return gspread.service_account(filename="google_sheets_credentials.json")


def get_or_create_worksheet(
    spreadsheet: gspread.Spreadsheet, name: str
) -> gspread.Worksheet:
    """Get worksheet by name, create if it doesn't exist."""
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=1000, cols=20)


def load_meta(meta_worksheet: gspread.Worksheet) -> dict[str, str]:
    """
    Load cursor mappings from _meta worksheet.
    
    Returns:
        Dict mapping token_hash -> cursor
    """
    cursors: dict[str, str] = {}
    try:
        records = meta_worksheet.get_all_values()
        for row in records:
            if len(row) >= 2 and row[0] != "last_run_time_utc":
                cursors[row[0]] = row[1]
    except Exception as e:
        logger.warning("Failed to load meta: %s", e)
    
    logger.info("Loaded %d cursor(s) from meta", len(cursors))
    return cursors


def push_sheets_delta(
    transactions_worksheet: gspread.Worksheet,
    meta_worksheet: gspread.Worksheet,
    sheets_delta: TransactionsDelta,
) -> None:
    """
    Push the sheets delta to Google Sheets.
    
    Handles:
    - Deleting removed transactions
    - Updating modified transactions
    - Appending new transactions
    - Saving updated cursor metadata
    
    Args:
        transactions_worksheet: The transactions worksheet
        meta_worksheet: The _meta worksheet
        sheets_delta: The delta to push
    """
    # Handle deleted transactions
    for txn_id in sheets_delta.deleted:
        try:
            cell = transactions_worksheet.find(txn_id)
            if cell:
                transactions_worksheet.delete_rows(cell.row)
                logger.info("Deleted transaction %s from row %d", txn_id, cell.row)
        except gspread.exceptions.CellNotFound:
            logger.warning("Transaction %s not found in sheets for deletion", txn_id)
    
    # Handle modified transactions
    for txn in sheets_delta.modified:
        try:
            cell = transactions_worksheet.find(txn.transaction_id)
            if cell:
                cell_range = f"A{cell.row}:G{cell.row}"
                transactions_worksheet.update(range_name=cell_range, values=[txn.to_row()])
                logger.info("Updated transaction %s at row %d", txn.transaction_id, cell.row)
        except gspread.exceptions.CellNotFound:
            # Add as new if not found
            sheets_delta.added[txn.transaction_id] = txn
            logger.info(
                "Transaction %s not found for modification, adding as new",
                txn.transaction_id,
            )
    
    # Handle new transactions
    if sheets_delta.added:
        rows = [txn.to_row() for txn in sheets_delta.added.values()]
        transactions_worksheet.append_rows(rows)
        logger.info("Appended %d new transactions", len(rows))
    
    # Save metadata
    _save_meta(meta_worksheet, sheets_delta.meta)


def _save_meta(meta_worksheet: gspread.Worksheet, cursors: dict[str, str]) -> None:
    """Save metadata to _meta worksheet."""
    meta_worksheet.clear()
    rows: list[list[str]] = [["last_run_time_utc", datetime.now(timezone.utc).isoformat()]]
    for token_hash, cursor in cursors.items():
        rows.append([token_hash, cursor])
    meta_worksheet.update(range_name="A1", values=rows)
    logger.info("Updated _meta worksheet with %d cursor(s)", len(cursors))
