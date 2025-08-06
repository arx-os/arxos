"""
Money Value Object

Represents monetary values in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP
import locale


@dataclass(frozen=True)
class Money:
    """
    Money value object representing monetary amounts.

    Attributes:
        amount: Amount as a Decimal
        currency: Currency code (e.g., 'USD', 'EUR')
    """

    amount: Decimal
    currency: str

    def __post_init__(self):
        """Validate money after initialization."""
        self._validate_amount()
        self._validate_currency()

    def _validate_amount(self):
        """Validate amount value."""
        if not isinstance(self.amount, Decimal):
            raise ValueError("Amount must be a Decimal")
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def _validate_currency(self):
        """Validate currency code."""
        if not self.currency or not self.currency.strip():
            raise ValueError("Currency cannot be empty")
        if len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter code")
        if not self.currency.isalpha():
            raise ValueError("Currency must contain only letters")

    @classmethod
    def from_string(cls, amount_str: str, currency: str) -> "Money":
        """
        Create Money from string amount.

        Args:
            amount_str: Amount as string
            currency: Currency code

        Returns:
            New Money object
        """
        try:
            amount = Decimal(amount_str)
            return cls(amount, currency)
        except (ValueError, TypeError):
            raise ValueError("Invalid amount string")

    @classmethod
    def from_float(cls, amount: float, currency: str) -> "Money":
        """
        Create Money from float amount.

        Args:
            amount: Amount as float
            currency: Currency code

        Returns:
            New Money object
        """
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def zero(cls, currency: str) -> "Money":
        """
        Create zero amount Money.

        Args:
            currency: Currency code

        Returns:
            New Money object with zero amount
        """
        return cls(Decimal("0"), currency)

    def __add__(self, other: "Money") -> "Money":
        """Add two Money objects."""
        if not isinstance(other, Money):
            raise ValueError("Can only add Money objects")
        if self.currency != other.currency:
            raise ValueError("Cannot add Money with different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money objects."""
        if not isinstance(other, Money):
            raise ValueError("Can only subtract Money objects")
        if self.currency != other.currency:
            raise ValueError("Cannot subtract Money with different currencies")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(result, self.currency)

    def __mul__(self, factor: float) -> "Money":
        """Multiply Money by a factor."""
        if not isinstance(factor, (int, float, Decimal)):
            raise ValueError("Factor must be a number")
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __truediv__(self, divisor: float) -> "Money":
        """Divide Money by a divisor."""
        if not isinstance(divisor, (int, float, Decimal)):
            raise ValueError("Divisor must be a number")
        if divisor <= 0:
            raise ValueError("Divisor must be positive")
        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __lt__(self, other: "Money") -> bool:
        """Compare Money objects."""
        if not isinstance(other, Money):
            raise ValueError("Can only compare with Money objects")
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money with different currencies")
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Compare Money objects."""
        if not isinstance(other, Money):
            raise ValueError("Can only compare with Money objects")
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money with different currencies")
        return self.amount <= other.amount

    def __eq__(self, other: "Money") -> bool:
        """Compare Money objects."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self) -> int:
        """Hash for Money object."""
        return hash((self.amount, self.currency))

    @property
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    @property
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

    def round_to_currency(self) -> "Money":
        """Round amount to currency precision."""
        # Most currencies use 2 decimal places
        rounded_amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Money(rounded_amount, self.currency)

    def format(self, locale_code: Optional[str] = None) -> str:
        """
        Format money for display.

        Args:
            locale_code: Locale code for formatting

        Returns:
            Formatted money string
        """
        if locale_code:
            try:
                locale.setlocale(locale.LC_ALL, locale_code)
            except locale.Error:
                pass

        try:
            return locale.currency(float(self.amount), symbol=True, grouping=True)
        except (ValueError, TypeError):
            return f"{self.currency} {self.amount:.2f}"

    def __str__(self) -> str:
        """String representation of money."""
        return f"{self.currency} {self.amount:.2f}"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Money(amount={self.amount}, currency='{self.currency}')"
