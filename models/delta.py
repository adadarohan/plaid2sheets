from dataclasses import dataclass, field
from models.transaction import Transaction


@dataclass
class TransactionsDelta:
    """
    Delta representing transaction changes.
    
    Used for both Plaid sync results and sheets reconciliation output.
    Contains added, modified, and deleted transactions along with cursor metadata.
    """
    
    added: dict[str, Transaction] = field(default_factory=dict)  # transaction_id -> Transaction
    modified: list[Transaction] = field(default_factory=list)
    deleted: set[str] = field(default_factory=set)  # transaction_ids
    meta: dict[str, str] = field(default_factory=dict)  # token_hash -> cursor
