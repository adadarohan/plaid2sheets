import logging

import gspread

from models.delta import TransactionsDelta
from models.transaction import Transaction

logger = logging.getLogger(__name__)


def load_rules(spreadsheet: gspread.Spreadsheet) -> dict[str, tuple[str, str]]:
    """
    Load category override rules from rules worksheet.
    
    Returns:
        Dict mapping lowercase merchant_name -> (override_category, override_detailed_category)
        Returns empty dict if rules worksheet doesn't exist
    """
    rules: dict[str, tuple[str, str]] = {}
    try:
        rules_worksheet = spreadsheet.worksheet("rules")
        records = rules_worksheet.get_all_values()
        
        # Skip header row
        for row in records[1:]:
            if len(row) >= 3 and row[0]:
                merchant_name_lower = row[0].strip().lower()
                override_category = row[1].strip()
                override_detailed_category = row[2].strip()
                
                if merchant_name_lower and override_category:
                    rules[merchant_name_lower] = (override_category, override_detailed_category)
        
        logger.info("Loaded %d rule(s) from rules sheet", len(rules))
    except gspread.WorksheetNotFound:
        logger.info("No rules worksheet found - skipping category overrides")
    except Exception as e:
        logger.warning("Failed to load rules: %s", e)
    
    return rules


def apply_category_rules(
    delta: TransactionsDelta, rules: dict[str, tuple[str, str]]
) -> None:
    """
    Apply category override rules to transactions.
    
    Updates transactions in-place if their merchant name matches a rule.
    Sets category_source to "Rules Sheet" for overridden categories.
    
    Args:
        delta: The transactions delta to apply rules to (mutated in place)
        rules: Dict mapping lowercase merchant_name -> (category, detailed_category)
    """
    if not rules:
        logger.info("No rules to apply")
        return
    
    total_overridden = 0
    
    # Apply rules to added transactions
    for txn in delta.added.values():
        merchant_lower = txn.merchant_name.lower()
        if merchant_lower in rules:
            override_category, override_detailed = rules[merchant_lower]
            txn.category_primary = override_category
            txn.category_detailed = override_detailed
            txn.category_source = "Rules Sheet"
            total_overridden += 1
            logger.debug(
                "Applied rule to transaction %s: %s -> %s",
                txn.transaction_id,
                txn.merchant_name,
                override_category,
            )
    
    # Apply rules to modified transactions
    for txn in delta.modified:
        merchant_lower = txn.merchant_name.lower()
        if merchant_lower in rules:
            override_category, override_detailed = rules[merchant_lower]
            txn.category_primary = override_category
            txn.category_detailed = override_detailed
            txn.category_source = "Rules Sheet"
            total_overridden += 1
            logger.debug(
                "Applied rule to modified transaction %s: %s -> %s",
                txn.transaction_id,
                txn.merchant_name,
                override_category,
            )
    
    logger.info("Applied category rules to %d transaction(s)", total_overridden)


def local_reconcile(delta: TransactionsDelta) -> TransactionsDelta:
    """
    Reconcile delta against local added transactions (in place).
    
    Attempts to resolve modified and deleted transactions against
    the locally added transactions before pushing to sheets.
    
    - If a deleted transaction exists in added, remove it locally
    - If a modified transaction exists in added, update it locally
    - Otherwise, keep in deleted/modified for sheets
    
    Args:
        delta: The aggregated delta from all Plaid tokens (mutated in place)
        
    Returns:
        The same TransactionsDelta, ready to be pushed to Google Sheets
    """
    # Handle deleted transactions
    resolved_deletes: set[str] = set()
    for txn_id in delta.deleted:
        if txn_id in delta.added:
            # Transaction was added and deleted in same sync - remove locally
            del delta.added[txn_id]
            resolved_deletes.add(txn_id)
            logger.debug("Deleted transaction %s resolved locally", txn_id)
    delta.deleted -= resolved_deletes
    
    # Handle modified transactions
    unresolved_modified: list = []
    for txn in delta.modified:
        if txn.transaction_id in delta.added:
            # Transaction was added and modified in same sync - update locally
            delta.added[txn.transaction_id] = txn
            logger.debug("Modified transaction %s resolved locally", txn.transaction_id)
        else:
            # Transaction exists in sheets - keep for modification
            unresolved_modified.append(txn)
    delta.modified = unresolved_modified
    
    logger.info(
        "Local reconciliation complete: %d to add, %d to modify, %d to delete in sheets",
        len(delta.added),
        len(delta.modified),
        len(delta.deleted),
    )
    
    return delta
