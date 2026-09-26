"""Fully amortizing fixed-rate mortgage with equal monthly instalments."""

from __future__ import annotations


class Mortgage:
    def __init__(self, principal: float, annual_interest_rate: float, length_years: int) -> None:
        if principal < 0:
            raise ValueError("principal must be non-negative")
        if length_years < 0:
            raise ValueError("length_years must be non-negative")
        self.principal = float(principal)
        self.annual_interest_rate = float(annual_interest_rate)
        self.length_years = int(length_years)
        self.n_payments = self.length_years * 12
        self.monthly_rate = self.annual_interest_rate / 12

    def monthly_payment(self) -> float:
        """Fixed monthly instalment (principal + interest)."""
        if self.n_payments == 0 or self.principal == 0:
            return 0.0
        r = self.monthly_rate
        if r == 0:
            return self.principal / self.n_payments
        factor = (1 + r) ** self.n_payments
        return self.principal * r * factor / (factor - 1)

    def remaining_principal(self, payments_made: int) -> float:
        if payments_made <= 0:
            return self.principal
        if payments_made >= self.n_payments:
            return 0.0
        r = self.monthly_rate
        if r == 0:
            remaining = self.principal * (1 - payments_made / self.n_payments)
            return max(0.0, remaining)
        payment = self.monthly_payment()
        balance = self.principal * (1 + r) ** payments_made - payment * ((1 + r) ** payments_made - 1) / r
        return max(0.0, balance)
