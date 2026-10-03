"""Static month-by-month wealth evolution until the mortgage is repaid."""

from __future__ import annotations

from dataclasses import dataclass

from mortgage import Mortgage
from parameters import MODE_LET_VS_INVEST, Scenario


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def _stepped_monthly_rent(initial: float, yearly_increase: float, month: int) -> float:
    years_elapsed = (month - 1) // 12
    return initial * (1 + yearly_increase) ** years_elapsed


@dataclass(frozen=True)
class WealthPoint:
    month: int
    buying_cashflow: float
    renting_cashflow: float
    buying_investment: float
    renting_investment: float
    house_value: float
    remaining_principal: float
    buying_wealth: float
    renting_wealth: float


class WealthModel:
    """Wealth for both paths from origination (month 0) through the last mortgage payment.

    In rent-vs-buy mode, ``buying_*`` is owner-occupier and ``renting_*`` is the tenant.
    In let-vs-invest mode, ``buying_*`` is the landlord and ``renting_*`` is the
    cash-only investment account (no deposit, cashflows are zero).
    """

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.mortgage = Mortgage(
            principal=scenario.buying.loan_amount,
            annual_interest_rate=scenario.buying.mortgage_interest_rate,
            length_years=scenario.buying.mortgage_length_years,
        )
        self.horizon_months = self.mortgage.n_payments
        self._timeline = self._simulate()

    def at(self, month: int) -> WealthPoint:
        if month < 0 or month > self.horizon_months:
            raise ValueError(f"month must be between 0 and {self.horizon_months}")
        return self._timeline[month]

    def timeline(self) -> list[WealthPoint]:
        return list(self._timeline)

    def _cashflows(self, month: int, mortgage_payment: float) -> tuple[float, float]:
        buying = self.scenario.buying
        if self.scenario.mode == MODE_LET_VS_INVEST:
            letting = self.scenario.letting
            assert letting is not None
            if month == 0:
                return buying.down_payment + buying.transfer_duty, 0.0
            rent_in = _stepped_monthly_rent(
                letting.initial_rent, letting.yearly_rent_increase, month
            )
            return mortgage_payment - rent_in, 0.0

        renting = self.scenario.renting
        assert renting is not None
        if month == 0:
            return buying.down_payment + buying.transfer_duty, renting.deposit
        rent_out = _stepped_monthly_rent(
            renting.current_rent, renting.yearly_rent_increase, month
        )
        return mortgage_payment, rent_out

    def _simulate(self) -> list[WealthPoint]:
        buying = self.scenario.buying
        mortgage_payment = self.mortgage.monthly_payment()
        investment_m = _monthly_rate(self.scenario.investment_return)
        net_house_annual = buying.appreciation_rate - buying.amortization_and_repairs_rate
        renting = self.scenario.renting
        deposit = 0.0 if renting is None else renting.deposit

        buy_investment = 0.0
        rent_investment = 0.0
        points: list[WealthPoint] = []

        for month in range(self.horizon_months + 1):
            if month > 0:
                buy_investment *= 1 + investment_m
                rent_investment *= 1 + investment_m

            buy_cf, rent_cf = self._cashflows(month, mortgage_payment)

            leftover = buy_cf - rent_cf
            if leftover > 0:
                rent_investment += leftover
            elif leftover < 0:
                buy_investment += -leftover

            house_value = buying.purchase_price * (1 + net_house_annual) ** (month / 12)
            remaining = self.mortgage.remaining_principal(month)
            buying_wealth = buy_investment + house_value - remaining
            renting_wealth = deposit + rent_investment

            points.append(
                WealthPoint(
                    month=month,
                    buying_cashflow=buy_cf,
                    renting_cashflow=rent_cf,
                    buying_investment=buy_investment,
                    renting_investment=rent_investment,
                    house_value=house_value,
                    remaining_principal=remaining,
                    buying_wealth=buying_wealth,
                    renting_wealth=renting_wealth,
                )
            )

        return points
