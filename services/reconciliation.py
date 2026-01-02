import logging

from models.delta import TransactionsDelta

logger = logging.getLogger(__name__)


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
