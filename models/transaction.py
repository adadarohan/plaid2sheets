from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    """Represents a financial transaction from Plaid."""
    
    transaction_id: str
    account_name: str
    amount: float
    date: date
    merchant_name: str
    category_primary: str
    category_detailed: str

    def to_row(self) -> list[str | float]:
        """Convert transaction to a row for Google Sheets."""
        return [
            self.transaction_id,
            self.account_name,
            self.amount,
            str(self.date),
            self.merchant_name,
            self.category_primary,
            self.category_detailed,
        ]

    @classmethod
    def from_plaid(cls, txn: dict, account_name: str) -> "Transaction":
        """Create a Transaction from Plaid API response data."""
        personal_finance = txn.get("personal_finance_category", {})
        merchant_name = txn.get("merchant_name") or txn.get("name") or ""
        
        return cls(
            transaction_id=txn["transaction_id"],
            account_name=account_name,
            amount=txn["amount"],
            date=txn["date"],
            merchant_name=merchant_name,
            category_primary=personal_finance.get("primary") or "",
            category_detailed=personal_finance.get("detailed") or "",
        )
