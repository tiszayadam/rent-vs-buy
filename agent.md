# Agent context — rent vs buy

This file is for future coding agents. Follow the user's methodology; do not invent extra cashflows or economic effects.

## What this project is

A Streamlit tool in **HUF** with two modes: **buying vs renting** a home to live in, and **buy-to-let vs a cash investment account**. Horizon is origination (month 0) through the last mortgage payment. The model is static and month-by-month.

Do not change the wealth equations unless the user asks. Keep transfer duty and the 10% down-payment floor as fixed rules unless they change them.

## Layout

User-facing (keep at repo root):

- `README.md` — how to run
- `start.bat` — Windows launcher (creates `.venv` on first run, starts Streamlit; puts Git on PATH so the Deploy button can see GitHub)
- `start.sh` — same for Git Bash / Unix
- `streamlit_app.py` — root entrypoint for Streamlit Community Cloud / in-app Deploy (loads `src/app.py`)
- `requirements.txt`

Implementation (do not scatter new Python at the repo root except `streamlit_app.py`):

- `src/indices/` — expected inflation / real rent / real house index graphs (independent of the wealth model for now)
- `src/app.py` — Streamlit UI
- `src/parameters.py` — dataclasses and constants
- `src/mortgage.py` — fully amortizing fixed-rate mortgage
- `src/model.py` — `WealthModel` / `WealthPoint`

Run with: `.venv\Scripts\python.exe -m streamlit run streamlit_app.py`

GitHub: `https://github.com/tiszayadam/rent-vs-buy` (public). Prefer branch `main` for Community Cloud. `cursor/static-wealth-model` was the original working branch.

## Parameters

Rates in code are **annual decimals** (`0.03` = 3%). The UI shows percents and divides by 100.

**Buying** (`BuyingParameters`): `purchase_price`, `down_payment`, `mortgage_length_years`, `mortgage_interest_rate`, `amortization_and_repairs_rate`.

Derived: `loan_amount = purchase_price - down_payment`, `transfer_duty = purchase_price * TRANSFER_DUTY_RATE`.

**Renting** (`RentingParameters`, rent-vs-buy only): `deposit`, `current_rent` (monthly HUF).

**Letting** (`LettingParameters`, let-vs-invest only): `initial_rent` (monthly HUF received). No tenant deposit.

**Shared:** `Scenario.investment_return` — one leftover-cash return for both paths, HUF-denominated. Exactly one of `renting` or `letting` is set. `nominal_house_index` and `nominal_rent_index` are yearly series from the Expected indices tab (`nominal = real × inflation deflator / 100`).

**Fixed constants** in `parameters.py`:

- `TRANSFER_DUTY_RATE = 0.04` (not user-editable). In the UI this is labelled as Hungarian *vagyonszerzési illeték*.
- `MIN_DOWN_PAYMENT_RATE = 0.10`

## Model rules (do not drift)

Positive cashflow = net outflow. Rent received on the let path reduces (or reverses) the landlord’s monthly outflow.

- Month 0: house path pays down payment + transfer duty. Rent-vs-buy: renter pays deposit. Let-vs-invest: the cash account pays nothing. No mortgage payment and no rent yet.
- Months 1…N: house path pays the constant fully amortizing instalment (principal + interest, monthly rate = annual / 12). Rent-vs-buy: renter pays `current_rent * R_y / R_0` with `y = (month - 1) // 12`. Let-vs-invest: landlord *receives* `initial_rent * R_y / R_0`, so net house-path cashflow is instalment minus rent; cash account cashflow is 0. `R` is the yearly nominal rent index (last value held if the mortgage runs past the series).
- Leftover: compare net outflows each stage; the cheaper path (smaller outflow / larger inflow) invests the difference. Grow existing investment balances first (`(1 + r)**(1/12) - 1`), then add that month's leftover.
- House value: `purchase_price * (H_m / H_0) * (1 - amortization_and_repairs) ** (month / 12)`. `H_m` is the nominal house index linearly interpolated between yearly points. Amortization/repairs are a value haircut, not a cash cost.
- Remaining principal after `month` payments; ~0 at the end.
- House-path wealth = investment + house − remaining principal.
- Rent-vs-buy other wealth = deposit (face value, not invested) + investment.
- Let-vs-invest other wealth = investment only.

API: `WealthModel(scenario).at(month)` or `.timeline()`.

## UI conventions

- Mode radio at the top of **Wealth comparison**: Rent vs buy / Buy-to-let vs invest.
- Tabs: Wealth comparison | Expected indices. Index graphs live in `src/indices/`. Streamlit cannot drag Plotly points; click a year then use the vertical slider beside the chart. Rent and house plots show real (editable) and nominal (`real * cumulative inflation deflator / 100`, deflator 100 in 2027). The wealth model uses those nominal series (index widgets run before the wealth tab so slider edits apply on the same rerun).
- Parameters live on the **main page** (three columns: Buying, Renting or Letting, Investment), not a sidebar.
- HUF **inputs** use Streamlit `st.number_input` so +/- sit inside the field (native spinbuttons). Native HTML number fields cannot show `70 000 000` grouping; captions, metrics, and the chart axis use space-separated thousands via `format_grouped`.
- Default steps: purchase/down ±1 000 000; deposit/rent ±10 000; percents ±0.1; years ±1.
- Defaults: purchase 70 000 000, down 15 000 000, mortgage 25 years at 3%, amort/repairs 1%, deposit 500 000, rent 250 000, investment return 8%, inflation 3%/year, real rent/house indices 100.
- Chart: wealth vs years; Plotly `separators=". "` and grouped HUF ticks. Series names follow the mode (Buying/Renting or Buy-to-let/Investment account).

## What not to do

- Do not add interest-only mortgages, extra cash outflows (tax, insurance as cash), FX, or different investment returns per path unless the user specifies them. Nominal inflation and real rent/house paths are user-editable on Expected indices; do not invent other price processes.
- Do not put implementation Python back in the repo root.
- Do not treat `model_description.md` as current — that file was merged into `README.md` and removed.
