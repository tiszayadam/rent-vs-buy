"""User-specified parameters for the wealth comparisons.

Rates are annual decimals (0.04 means 4%). Monetary amounts are HUF.
current_rent and initial_rent are monthly.
"""

from __future__ import annotations

from dataclasses import dataclass


TRANSFER_DUTY_RATE = 0.04
MIN_DOWN_PAYMENT_RATE = 0.10

MODE_RENT_VS_BUY = "rent_vs_buy"
MODE_LET_VS_INVEST = "let_vs_invest"


@dataclass
class BuyingParameters:
    purchase_price: float
    down_payment: float
    mortgage_length_years: int
    mortgage_interest_rate: float
    amortization_and_repairs_rate: float
    appreciation_rate: float

    def __post_init__(self) -> None:
        if self.purchase_price < 0:
            raise ValueError("purchase_price must be non-negative")
        if self.down_payment < 0:
            raise ValueError("down_payment must be non-negative")
        if self.down_payment > self.purchase_price:
            raise ValueError("down_payment cannot exceed purchase_price")
        if self.down_payment < MIN_DOWN_PAYMENT_RATE * self.purchase_price:
            raise ValueError("down_payment must be at least 10% of purchase_price")
        if self.mortgage_length_years < 0:
            raise ValueError("mortgage_length_years must be non-negative")

    @property
    def transfer_duty_rate(self) -> float:
        return TRANSFER_DUTY_RATE

    @property
    def transfer_duty(self) -> float:
        return self.purchase_price * TRANSFER_DUTY_RATE

    @property
    def loan_amount(self) -> float:
        return self.purchase_price - self.down_payment


@dataclass
class RentingParameters:
    deposit: float
    current_rent: float
    yearly_rent_increase: float

    def __post_init__(self) -> None:
        if self.deposit < 0:
            raise ValueError("deposit must be non-negative")
        if self.current_rent < 0:
            raise ValueError("current_rent must be non-negative")


@dataclass
class LettingParameters:
    initial_rent: float
    yearly_rent_increase: float

    def __post_init__(self) -> None:
        if self.initial_rent < 0:
            raise ValueError("initial_rent must be non-negative")


@dataclass
class Scenario:
    buying: BuyingParameters
    investment_return: float
    renting: RentingParameters | None = None
    letting: LettingParameters | None = None

    def __post_init__(self) -> None:
        if (self.renting is None) == (self.letting is None):
            raise ValueError("exactly one of renting or letting is required")

    @property
    def mode(self) -> str:
        return MODE_LET_VS_INVEST if self.letting is not None else MODE_RENT_VS_BUY
