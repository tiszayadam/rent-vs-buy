# Model description

This is a static, month-by-month comparison of two housing paths — **buying** and **renting** — from origination (month 0) through the last mortgage payment.

The two paths are assumed to face the same choice of housing spend at each stage. Whoever spends less invests the difference. Both investment accounts grow at the same annual return, compounded monthly.

## Horizon and timing

- Horizon is the mortgage length in months.
- Month 0 is the upfront cash outlay only (no mortgage instalment and no rent yet).
- Months 1 through \(N\) are the monthly cashflows. After \(N\) payments the loan principal is zero.

## Buying cashflows

- **Upfront:** down payment plus transfer duty. Transfer duty is a fixed 4% of purchase price. Down payment must be at least 10% of purchase price.
- **Loan:** purchase price minus down payment.
- **Each month:** a constant instalment on a fully amortizing mortgage (equal monthly payments, fixed annual rate, monthly rate = annual rate / 12). The instalment covers principal and interest, not interest only.

House value at month \(m\) is

\[
\text{purchase price} \times (1 + \text{appreciation} - \text{amortization and repairs})^{m/12}.
\]

Amortization and repairs reduce house *value*; they are not a separate cash outflow.

## Renting cashflows

- **Upfront:** the rental deposit, held at face value (it does not earn the investment return).
- **Each month:** current monthly rent, increased once per year by the yearly rent increase (months 1–12 at the starting rent, then stepped up each following year).

## Leftover cash

At every stage, outgoing cashflows are compared:

- if buying costs more, the renter invests the difference;
- if renting costs more, the buyer invests the difference.

Existing investment balances then grow one month at a time at

\[
(1 + \text{investment return})^{1/12} - 1
\]

before that month’s leftover (if any) is added.

## Wealth

- **Buying:** investment account + house value − remaining mortgage principal.
- **Renting:** deposit + investment account.

The Streamlit UI plots these two wealth series over the mortgage.
