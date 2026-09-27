"""Static month-by-month wealth evolution until the mortgage is repaid."""

from __future__ import annotations

from dataclasses import dataclass

from mortgage import Mortgage
from parameters import Scenario


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


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
    """Wealth for both paths from origination (month 0) through the last mortgage payment."""

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

    def _simulate(self) -> list[WealthPoint]:
        buying = self.scenario.buying
        renting = self.scenario.renting
        mortgage_payment = self.mortgage.monthly_payment()
        investment_m = _monthly_rate(self.scenario.investment_return)
        net_house_annual = buying.appreciation_rate - buying.amortization_and_repairs_rate

        buy_investment = 0.0
        rent_investment = 0.0
        points: list[WealthPoint] = []

        for month in range(self.horizon_months + 1):
            if month > 0:
                buy_investment *= 1 + investment_m
                rent_investment *= 1 + investment_m

            if month == 0:
                buy_cf = buying.down_payment + buying.transfer_duty
                rent_cf = renting.deposit
            else:
                buy_cf = mortgage_payment
                years_elapsed = (month - 1) // 12
                rent_cf = renting.current_rent * (1 + renting.yearly_rent_increase) ** years_elapsed

            leftover = buy_cf - rent_cf
            if leftover > 0:
                rent_investment += leftover
            elif leftover < 0:
                buy_investment += -leftover

            house_value = buying.purchase_price * (1 + net_house_annual) ** (month / 12)
            remaining = self.mortgage.remaining_principal(month)
            buying_wealth = buy_investment + house_value - remaining
            renting_wealth = renting.deposit + rent_investment

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
