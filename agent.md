# Agent context — rent vs buy

This file is for future coding agents. Follow the user's methodology; do not invent extra cashflows or economic effects.

## What this project is

A Streamlit tool that compares **buying** vs **renting** a home in **HUF**. Horizon is origination (month 0) through the last mortgage payment. The model is static and month-by-month.

Do not change the wealth equations unless the user asks. Keep transfer duty and the 10% down-payment floor as fixed rules unless they change them.

## Layout

User-facing (keep at repo root):

- `README.md` — how to run + model description
- `start.bat` — Windows launcher (creates `.venv` on first run, starts Streamlit)
- `start.sh` — same for Git Bash / Unix
- `requirements.txt`

Implementation (do not scatter new Python at the repo root):

- `src/app.py` — Streamlit UI
- `src/parameters.py` — dataclasses and constants
- `src/mortgage.py` — fully amortizing fixed-rate mortgage
- `src/model.py` — `WealthModel` / `WealthPoint`

Run with: `.venv\Scripts\python.exe -m streamlit run src\app.py`

GitHub: `https://github.com/tiszayadam/rent-vs-buy` (private). Working branch has been `cursor/static-wealth-model`.

## Parameters

Rates in code are **annual decimals** (`0.03` = 3%). The UI shows percents and divides by 100.

**Buying** (`BuyingParameters`): `purchase_price`, `down_payment`, `mortgage_length_years`, `mortgage_interest_rate`, `amortization_and_repairs_rate`, `appreciation_rate`.

Derived: `loan_amount = purchase_price - down_payment`, `transfer_duty = purchase_price * TRANSFER_DUTY_RATE`.

**Renting** (`RentingParameters`): `deposit`, `current_rent` (monthly HUF), `yearly_rent_increase`.

**Shared:** `Scenario.investment_return` — one leftover-cash return for both paths, HUF-denominated.

**Fixed constants** in `parameters.py`:

- `TRANSFER_DUTY_RATE = 0.04` (not user-editable). In the UI this is labelled as Hungarian *vagyonszerzési illeték*.
- `MIN_DOWN_PAYMENT_RATE = 0.10`

## Model rules (do not drift)

- Month 0: buyer pays down payment + transfer duty; renter pays deposit. No mortgage payment and no rent yet.
- Months 1…N: buyer pays the constant fully amortizing instalment (principal + interest, monthly rate = annual / 12). Renter pays `current_rent * (1 + yearly_rent_increase) ** ((month - 1) // 12)`.
- Leftover: compare outflows each stage; the cheaper path invests the difference. Grow existing investment balances first (`(1 + r)**(1/12) - 1`), then add that month's leftover.
- House value: `purchase_price * (1 + appreciation - amortization_and_repairs) ** (month / 12)`. Amortization/repairs are a value haircut, not a cash cost.
- Remaining principal after `month` payments; ~0 at the end.
- Buying wealth = investment + house − remaining principal.
- Renting wealth = deposit (face value, not invested) + investment.

API: `WealthModel(scenario).at(month)` or `.timeline()`.

## UI conventions

- Parameters live on the **main page** (three columns: Buying, Renting, Investment), not a sidebar.
- HUF **inputs** use Streamlit `st.number_input` so +/- sit inside the field (native spinbuttons). Native HTML number fields cannot show `70 000 000` grouping; captions, metrics, and the chart axis use space-separated thousands via `format_grouped`.
- Default steps: purchase/down ±1 000 000; deposit/rent ±10 000; percents ±0.1; years ±1.
- Defaults: purchase 70 000 000, down 15 000 000, mortgage 25 years at 3%, amort/repairs 1%, appreciation 3%, deposit 500 000, rent 250 000, rent increase 3%, investment return 8%.
- Chart: wealth vs years for Buying and Renting; Plotly `separators=". "` and grouped HUF ticks.

## What not to do

- Do not add interest-only mortgages, extra cash outflows (tax, insurance as cash), inflation, FX, or different investment returns per path unless the user specifies them.
- Do not put implementation Python back in the repo root.
- Do not treat `model_description.md` as current — that file was merged into `README.md` and removed.
