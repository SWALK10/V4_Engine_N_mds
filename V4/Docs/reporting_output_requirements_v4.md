# CPS V4 Reporting Output Requirements & Testing Documentation

**Location:** `docs/CPS_v4/reporting_output_requirements_v4.md`

---

## 1. Key Report Output Requirements

_Adapted from: [docs/Keep/report_standard_verification.md]_  
**Summary:** All V4 reports must include the following, with strict adherence to structure and completeness:

### 1.1 Performance Table Report (XLSX)

- **Filename:** `EMA_V3_1_performance_tables_YYYYMMDD_HHMMSS.xlsx`
- **Signal History Tab:**
  - Date Format: `YYYY-MM-DD`, no timestamps
  - Columns: Tickers + Cash
  - Allocation: Sum to 100% per row
  - Formatting: 0.00%
- **Allocation History Tab:**
  - Structure: Matches Signal History
  - Allocations: Actual capital with 1-day lag
  - Completeness: Each row sums to 100%, no gaps
  - Formatting: 0.00%
- **Trade Log Tab:**
  - Columns: `trade_num`, `symbol`, `quantity`, `execution_date`, `execution_price`, `commission+slippage`, `amount`, `pnl`
  - Sorting: By `execution_date` and `trade_num`
  - Completeness: All executed trades included
- **Header:** Cell A1 displays main parameters
- **Performance Tab:**
  - Structure: Parameters left, metrics right
  - Rows: One per parameter combination + benchmark
  - Formatting: Percentages (0.00%), Ratios (0.00), Currency ($#,##0.00)

### 1.2 Monthly & Annual Returns Graphic (PNG)

- **Filename:** `EMA_V3_1_monthly_returns_YYYYMMDD_HHMMSS.png`
- **Content:**
  - Heatmap: Monthly returns (years as rows, months as columns)
  - Annual Returns: Single column next to heatmap
  - Color Legend: Return scale (e.g., -5% to +8%)
- **Formatting:**
  - Title: "Monthly Returns"
  - Axis Labels: Year (rows), Month (columns: Jan–Dec)
  - Values: Percentages (0.00%), no missing months/years
  - Resolution: High DPI (≥300, ideally 600)
- **Audit:** Matches Allocation History and Trade Log

### 1.3 Combined Cumulative Returns & Drawdown Graphic (PNG)

- **Filename:** `EMA_V3_1_cumulative_returns_drawdown_YYYYMMDD_HHMMSS.png`
- **Content:**
  - Top Panel: Cumulative returns for strategy and benchmark
  - Bottom Panel: Drawdowns over the same period
- **Formatting:**
  - Title: "Cumulative Returns & Drawdown"
  - Axis Labels: Date (x), Percentage (y)
  - Legend: Strategy, Benchmark
  - Resolution: High DPI (≥300, ideally 600)

### 1.4 Parameter Flow Verification

- All key parameters must be traced from GUI → Registry → Adapter → Reports → Reports Display
- Example parameters: `st_lookback`, `mt_lookback`, `lt_lookback`, `execution_delay`, `top_n`, `create_excel`, `create_charts`, etc.

### 1.5 Signal History Verification

- Signal history must be:
  - Created and populated in backtest.py
  - Preserved through all adapters/modules
  - Used for report generation
  - Present in the final Excel tab

### 1.6 General Requirements

- **Completeness:** No missing dates, assets, or required fields

- **Format:** Data must be in tabular format, suitable for Excel import and programmatic verification

- **No Synthetic Data:** Only real data from the production backtest engine is valid for compliance and testing

- **Trade Log Tab**: All executed trades, with required columns

- **Performance Metrics Tab**: Standardized metrics (CAGR, volatility, Sharpe, etc.)

- **Completeness**: No missing dates, assets, or required fields

- **Format**: Data must be in tabular format, suitable for Excel import and programmatic verification

- **No Synthetic Data**: Only real data from the production backtest engine is valid for compliance and testing

---

## 2. V4 Production Modules & Functions (Reporting Pipeline)

**Critical modules and functions for report generation:**

- `v4/engine/backtest_v4.py`: Main backtest engine
  - `BacktestEngine.run_backtest`: Runs the backtest and produces output
  - `BacktestEngine._calculate_results`: Assembles all output fields (see below)
- `v4_reporting/v4_performance_report.py`: Main reporting module
  - `generate_performance_report`: Consumes backtest output and generates Excel reports
  - `generate_optimization_report`: For optimization reporting
- `v4_reporting/test_v4_performance_report.py`: Test harness (should only use real engine data)
- `v4/settings/settings_parameters_v4.ini`: Parameter definitions (used by all above)

---

## 3. Report Testing Process (V4)

**Inputs:**

- Real backtest results from `BacktestEngine.run_backtest`
- Configuration via INI files

**Process:**

1. Run the backtest engine with real data and production parameters.
2. Capture the output dictionary from `_calculate_results` (see structure below).
3. Pass this output to the reporting module (`v4_performance_report.py`).
4. Generate Excel reports and raw data files.
5. Verify:
   - All required tabs/files are present
   - Data is complete (no missing dates/assets)
   - Structure matches report standards
   - No synthetic data is used at any stage

**Outputs:**

- Excel report (with all required tabs)
- Raw data files: `signal_history.txt`, `allocation_history.txt`, `trade_log.csv`, etc.

---

## 4. Backtest Engine Output Structure Documentation

**The following fields are returned by `BacktestEngine._calculate_results` and are required for reporting:**

### `signal_history`

- **Type:** `pandas.DataFrame`
- **Index:** Dates (trading days)
- **Columns:** Asset tickers (e.g., AAPL, MSFT, ...)
- **Values:** Allocation signals (float, 0.0–1.0, sum to 1.0 per row)
- **Role:** Used for the Signal History tab in reports
- **Source:** Direct output from signal generator

### `weights_history` (a.k.a. Allocation History)

- **Type:** `pandas.DataFrame`
- **Index:** Dates (trading days)
- **Columns:** Asset tickers
- **Values:** Actual executed allocations (float, 0.0–1.0, sum to 1.0 per row)
- **Role:** Used for the Allocation History tab in reports
- **Source:** Derived from signal history, adjusted for execution delay and trade dates
- **Note:** Forward-filled between trades to show continuous allocation

### `trade_log`

- **Type:** `pandas.DataFrame`
- **Columns:** At minimum: `date`, `ticker`, `action`, `quantity`, `price`, `total`, `execution_date`, `pnl`, etc.
- **Role:** Used for the Trade Log tab in reports
- **Source:** Generated by the execution engine

### Total Portfolio Equity Daily

### By day, tickers in columns and grand total on last column   Shows total $ value of holdings by date (can add in an additional cash column if need to tie to total actual (not theory) portfolio value by day

### `performance` (metrics)

- **Type:** `dict`
- **Keys:** `cagr`, `volatility`, `sharpe`, `max_drawdown`, `turnover`, `win_rate`
- **Role:** Used for performance summary tab

### Example Output Dictionary (abbreviated)

```python
{
    'initial_capital': ...,
    'final_value': ...,
    'total_return': ...,
    'strategy_returns': ...,
    'benchmark_returns': ...,
    'weights_history': <DataFrame>,
    'position_history': <DataFrame>,
    'signal_history': <DataFrame>,
    'trade_log': <DataFrame>,
    'performance': {...},
    'monthly_returns': ...,
    'yearly_returns': ...
}
```

---

## 5. Compliance Checklist

- [ ] All report tabs/files present (signal, allocation, trade log, performance)
- [ ] Data is real (from engine), not synthetic
- [ ] Data structures match above documentation
- [ ] All fields/columns present and complete
- [ ] Output format is tabular and Excel-compatible
- [ ] Testing process uses only production modules and real data

---

**For further reference:**

- [report_standard_verification.md](../Keep/report_standard_verification.md)
- [v4_performance_report.py](../../v4_reporting/v4_performance_report.py)
- [backtest_v4.py](../../v4/engine/backtest_v4.py)
- [settings_parameters_v4.ini](../../v4/settings/settings_parameters_v4.ini)
