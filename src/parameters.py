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
MODE_HOUSE_VS_HOUSE = "house_vs_house"


@dataclass
class BuyingParameters:
    purchase_price: float
    down_payment: float
    mortgage_length_years: int
    mortgage_interest_rate: float
    amortization_and_repairs_rate: float

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

    def __post_init__(self) -> None:
        if self.deposit < 0:
            raise ValueError("deposit must be non-negative")
        if self.current_rent < 0:
            raise ValueError("current_rent must be non-negative")


@dataclass
class LettingParameters:
    initial_rent: float

    def __post_init__(self) -> None:
        if self.initial_rent < 0:
            raise ValueError("initial_rent must be non-negative")


@dataclass
class Scenario:
    buying: BuyingParameters
    investment_return_pct: list[float]
    nominal_house_index: list[float]
    nominal_rent_index: list[float]
    renting: RentingParameters | None = None
    letting: LettingParameters | None = None
    buying_b: BuyingParameters | None = None
    letting_b: LettingParameters | None = None

    def __post_init__(self) -> None:
        two_house = self.buying_b is not None
        if two_house:
            if self.renting is not None:
                raise ValueError("two-house mode cannot include renting")
            if self.letting is None or self.letting_b is None:
                raise ValueError("two-house mode needs letting for both houses")
        else:
            if self.letting_b is not None:
                raise ValueError("letting_b requires buying_b")
            if (self.renting is None) == (self.letting is None):
                raise ValueError("exactly one of renting or letting is required")
        if not self.nominal_house_index or self.nominal_house_index[0] == 0:
            raise ValueError("nominal_house_index must start with a non-zero base")
        if not self.nominal_rent_index or self.nominal_rent_index[0] == 0:
            raise ValueError("nominal_rent_index must start with a non-zero base")
        if not self.investment_return_pct:
            raise ValueError("investment_return_pct must not be empty")

    @property
    def mode(self) -> str:
        if self.buying_b is not None:
            return MODE_HOUSE_VS_HOUSE
        if self.letting is not None:
            return MODE_LET_VS_INVEST
        return MODE_RENT_VS_BUY
