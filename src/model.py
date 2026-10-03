"""Static month-by-month wealth evolution until the mortgage is repaid."""

from __future__ import annotations

from dataclasses import dataclass

from indices.series import house_value_from_index, rent_from_index
from mortgage import Mortgage
from parameters import (
    MODE_HOUSE_VS_HOUSE,
    MODE_LET_VS_INVEST,
    BuyingParameters,
    LettingParameters,
    Scenario,
)


def _monthly_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 12) - 1


def _instalment(mortgage: Mortgage, month: int) -> float:
    if month <= 0 or month > mortgage.n_payments:
        return 0.0
    return mortgage.monthly_payment()


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
    house_value_b: float = 0.0
    remaining_principal_b: float = 0.0


class WealthModel:
    """Wealth for both paths from origination (month 0) through the last mortgage payment.

    In rent-vs-buy mode, ``buying_*`` is owner-occupier and ``renting_*`` is the tenant.
    In let-vs-invest mode, ``buying_*`` is the landlord and ``renting_*`` is the
    cash-only investment account (no deposit, cashflows are zero).
    In house-vs-house mode, ``buying_*`` is house A and ``renting_*`` is house B;
    both are buy-to-let investments.
    """

    def __init__(self, scenario: Scenario) -> None:
        self.scenario = scenario
        self.mortgage = Mortgage(
            principal=scenario.buying.loan_amount,
            annual_interest_rate=scenario.buying.mortgage_interest_rate,
            length_years=scenario.buying.mortgage_length_years,
        )
        self.mortgage_b: Mortgage | None = None
        if scenario.buying_b is not None:
            self.mortgage_b = Mortgage(
                principal=scenario.buying_b.loan_amount,
                annual_interest_rate=scenario.buying_b.mortgage_interest_rate,
                length_years=scenario.buying_b.mortgage_length_years,
            )
            self.horizon_months = max(self.mortgage.n_payments, self.mortgage_b.n_payments)
        else:
            self.horizon_months = self.mortgage.n_payments
        self._timeline = self._simulate()

    def at(self, month: int) -> WealthPoint:
        if month < 0 or month > self.horizon_months:
            raise ValueError(f"month must be between 0 and {self.horizon_months}")
        return self._timeline[month]

    def timeline(self) -> list[WealthPoint]:
        return list(self._timeline)

    def _indexed_rent(self, initial: float, month: int) -> float:
        return rent_from_index(initial, self.scenario.nominal_rent_index, month)

    def _rent(self, month: int) -> float:
        if self.scenario.mode == MODE_LET_VS_INVEST:
            letting = self.scenario.letting
            assert letting is not None
            initial = letting.initial_rent
        else:
            renting = self.scenario.renting
            assert renting is not None
            initial = renting.current_rent
        return self._indexed_rent(initial, month)

    def _buy_to_let_cashflow(
        self,
        buying: BuyingParameters,
        mortgage: Mortgage,
        letting: LettingParameters,
        month: int,
    ) -> float:
        if month == 0:
            return buying.down_payment + buying.transfer_duty
        return _instalment(mortgage, month) - self._indexed_rent(letting.initial_rent, month)

    def _cashflows(self, month: int) -> tuple[float, float]:
        buying = self.scenario.buying
        if self.scenario.mode == MODE_HOUSE_VS_HOUSE:
            buying_b = self.scenario.buying_b
            letting = self.scenario.letting
            letting_b = self.scenario.letting_b
            assert buying_b is not None and letting is not None and letting_b is not None
            assert self.mortgage_b is not None
            return (
                self._buy_to_let_cashflow(buying, self.mortgage, letting, month),
                self._buy_to_let_cashflow(buying_b, self.mortgage_b, letting_b, month),
            )
        if self.scenario.mode == MODE_LET_VS_INVEST:
            letting = self.scenario.letting
            assert letting is not None
            return self._buy_to_let_cashflow(buying, self.mortgage, letting, month), 0.0

        renting = self.scenario.renting
        assert renting is not None
        if month == 0:
            return buying.down_payment + buying.transfer_duty, renting.deposit
        return _instalment(self.mortgage, month), self._rent(month)

    def _simulate(self) -> list[WealthPoint]:
        buying = self.scenario.buying
        buying_b = self.scenario.buying_b
        investment_m = _monthly_rate(self.scenario.investment_return)
        renting = self.scenario.renting
        deposit = 0.0 if renting is None else renting.deposit

        buy_investment = 0.0
        rent_investment = 0.0
        points: list[WealthPoint] = []

        for month in range(self.horizon_months + 1):
            if month > 0:
                buy_investment *= 1 + investment_m
                rent_investment *= 1 + investment_m

            buy_cf, rent_cf = self._cashflows(month)

            leftover = buy_cf - rent_cf
            if leftover > 0:
                rent_investment += leftover
            elif leftover < 0:
                buy_investment += -leftover

            house_value = house_value_from_index(
                buying.purchase_price,
                self.scenario.nominal_house_index,
                month,
                buying.amortization_and_repairs_rate,
            )
            remaining = self.mortgage.remaining_principal(month)
            buying_wealth = buy_investment + house_value - remaining

            house_value_b = 0.0
            remaining_b = 0.0
            if buying_b is not None and self.mortgage_b is not None:
                house_value_b = house_value_from_index(
                    buying_b.purchase_price,
                    self.scenario.nominal_house_index,
                    month,
                    buying_b.amortization_and_repairs_rate,
                )
                remaining_b = self.mortgage_b.remaining_principal(month)
                renting_wealth = rent_investment + house_value_b - remaining_b
            else:
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
                    house_value_b=house_value_b,
                    remaining_principal_b=remaining_b,
                )
            )

        return points
