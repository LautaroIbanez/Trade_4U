# BTC 1 Trade Per Day Backtester

A comprehensive Python backtesting system for BTC/USDT futures trading strategy that implements a 1 trade per day approach using Opening Range Breakout (ORB) with fallback mechanisms.

## Strategy Overview

The strategy combines macro trend analysis with intraday breakout patterns:

### Macro Bias (1H Timeframe)
- **Long Bias**: Close > EMA200 AND EMA50 > EMA200
- **Short Bias**: Close < EMA200 AND EMA50 < EMA200
- **Neutral**: No trades when bias is neutral

### Entry Strategy
- **Primary**: Opening Range Breakout (ORB) from 11:00-12:00 UTC
- **Entry Window**: 11:00-13:00 UTC only
- **Confirmations Required**:
  - Price above/below intraday VWAP (for long/short)
  - ADX(14) >= 20 (trend strength)
  - Current volume > SMA volume(20)

### Fallback Strategy
When ORB fails and `force_one_trade=True`:
- **EMA15 Pullback**: Wait for pullback to EMA15 with engulfing pattern
- **Volume Confirmation**: Current volume > SMA volume(20)
- **R/R Check**: Minimum 1.8:1 risk/reward ratio

### Risk Management
- **Position Sizing**: Fixed USDT amount or % of equity
- **Stop Loss**: ATR(14) × multiplier (1.2 for ORB, 1.5 for fallback)
- **Take Profit**: 2R (Risk/Reward = 1:2)
- **Break-even**: Move SL to entry at +1R
- **Daily Limits**: 
  - Target: +50 USDT (configurable)
  - Max Loss: -30 USDT (configurable)
- **Session End**: Force close at 17:00 UTC

## Installation

1. Clone or download the project files
2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note:** The project now includes comprehensive plotting capabilities. If you want to generate visual reports, make sure matplotlib and seaborn are installed:
```bash
pip install matplotlib seaborn
```

## Usage

### Basic Example (Recommended)
```bash
python btc_1tpd_backtest_final.py --since "2024-06-01" --until "2024-09-19"
```

### Advanced Example
```bash
python btc_1tpd_backtest_final.py \
  --since "2024-06-01" \
  --until "2024-09-19" \
  --risk_usdt 20 \
  --daily_target 50 \
  --daily_max_loss -30 \
  --adx_min 15
```

### Original Complex Strategy
```bash
python btc_1tpd_backtest_binance.py \
  --since "2024-06-01" \
  --until "2024-09-19" \
  --signal_tf 15 \
  --risk_usdt 20 \
  --daily_target 50 \
  --daily_max_loss -30 \
  --force_one_trade \
  --fallback_mode BestOfBoth
```

### Command Line Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--symbol` | BTC/USDT:USDT | Trading symbol |
| `--since` | Required | Start date (ISO format) |
| `--until` | Current time | End date (ISO format) |
| `--signal_tf` | 15 | Signal timeframe (5 or 15 minutes) |
| `--risk_usdt` | 20.0 | Risk amount per trade |
| `--daily_target` | 50.0 | Daily profit target |
| `--daily_max_loss` | -30.0 | Daily max loss limit |
| `--force_one_trade` | False | Force one trade per day |
| `--fallback_mode` | BestOfBoth | Fallback strategy (ORB/EMA15_pullback/BestOfBoth) |
| `--adx_min` | 20.0 | Minimum ADX value |
| `--min_rr_ok` | 1.8 | Minimum R/R for fallback |
| `--atr_mult_orb` | 1.2 | ATR multiplier for ORB SL |
| `--atr_mult_fallback` | 1.5 | ATR multiplier for fallback SL |
| `--tp_multiplier` | 2.0 | Take profit multiplier |

## Output

### Console Summary
```
==================================================
📊 BACKTEST SUMMARY
==================================================
Total Trades: 87
Win Rate: 65.5% (57/87)
Profit Factor: 3.17
Expectancy: +14.94 USDT
Avg Win: +33.33 USDT
Avg Loss: -20.00 USDT
Max Consecutive Losses: 3
Green Days: 66% (57/87)
Total PnL: +1300.00 USDT
==================================================

First 5 trades:
      day_key  side  entry_price    exit_price   pnl_usdt  r_multiple
0  2024-06-01  long      67747.1  67892.742857  33.333333    1.666667
1  2024-06-03  long      69449.7  69764.214286  33.333333    1.666667
2  2024-06-04  long      69095.6  69390.542857  33.333333    1.666667
3  2024-06-06  long      71407.6  71644.314286  33.333333    1.666667
4  2024-06-07  long      71924.2  71769.014286 -20.000000   -1.000000
```

### CSV Output (trades_final.csv)
| Column | Description |
|--------|-------------|
| day_key | Trading date (YYYY-MM-DD) |
| entry_time | Entry timestamp |
| side | Trade direction (long/short) |
| entry_price | Entry price |
| sl | Stop loss price |
| tp | Take profit price |
| exit_time | Exit timestamp |
| exit_price | Exit price |
| exit_reason | Exit reason (take_profit/stop_loss/session_end/break_even) |
| pnl_usdt | Profit/Loss in USDT |
| r_multiple | Risk multiple achieved |
| used_fallback | Whether fallback strategy was used |

### Visual Reports (PNG Files)
The backtester automatically generates comprehensive visual reports including:

- **Equity Curve** (`trading_report_equity_curve.png`): Shows cumulative PnL over time
- **PnL Distribution** (`trading_report_pnl_distribution.png`): Histogram of individual trade PnL
- **Monthly Performance** (`trading_report_monthly_performance.png`): Monthly PnL breakdown
- **Win/Loss Analysis** (`trading_report_win_loss_analysis.png`): Win/loss pie chart and R-multiple distribution
- **Drawdown Analysis** (`trading_report_drawdown.png`): Drawdown over time
- **Trade Timeline** (`trading_report_trade_timeline.png`): Individual trades plotted over time

#### Generate Plots from Existing Data
```bash
# Generate plots from any trades CSV
python generate_plots.py trades_final.csv

# Save plots to specific directory
python generate_plots.py trades_final.csv --output-dir plots/

# Display plots without saving
python generate_plots.py trades_final.csv --no-save
```

## Project Structure

```

## Web Dashboard (Dash)

The project includes an interactive web dashboard built with Dash.

### Install extra dependencies
```bash
pip install -r requirements.txt
```

### Prepare data
- Ensure `trades_final.csv` exists in the project root (`btc_1tpd_backtester/`).
- You can generate/update it by running the backtester examples above.

### Run the web app (development)
```bash
python -m webapp.app
```
This starts a local server on `http://127.0.0.1:8050`.

### What you get
- Recomendación de hoy: Uses `signals/today_signal.py:get_today_trade_recommendation` to compute the ORB signal for the current UTC day (status, side, entry time/price, SL/TP, ORB levels, notes).
- Interactive charts: Equity curve, PnL distribution, drawdown, and trade timeline with hover/zoom/range.
- Controls: Symbol input and a refresh button. Errors are shown if `trades_final.csv` is missing.

### CLI helper for today recommendation
```bash
python -m signals.today_signal --symbol BTC/USDT:USDT
```

### Configuration notes
- Default symbol: `BTC/USDT:USDT`
- ORB window: 11:00–12:00 UTC; Entry window: 11:00–13:00 UTC.
- Macro bias from 1h EMA50/EMA200 via `indicators.get_macro_bias`.
- For real intraday live signals you would need live data refresh and credentials; this project fetches public OHLCV from Binance via CCXT.
btc_1tpd_backtester/
│── btc_1tpd_backtest_binance.py   # Original complex strategy
│── btc_1tpd_backtest_final.py     # Recommended working version
│── indicators.py                   # Technical indicators (EMA, ATR, ADX, VWAP)
│── strategy.py                     # Trading strategy logic
│── backtester.py                   # Backtesting engine and metrics
│── utils.py                        # Utility functions (data fetching, helpers)
│── plot_results.py                 # Comprehensive plotting functions
│── generate_plots.py               # Standalone plot generator
│── requirements.txt                # Python dependencies
│── README.md                       # This documentation
│── trades_final.csv                # Output file (generated)
│── trading_report_*.png            # Visual reports (generated)
```

## Key Features

- ✅ **No Repaint**: All calculations use closed candles only
- ✅ **Modular Design**: Clean separation of concerns
- ✅ **Comprehensive Metrics**: Win rate, profit factor, expectancy, etc.
- ✅ **Risk Management**: Fixed risk per trade with daily limits
- ✅ **Multiple Timeframes**: HTF for bias, LTF for entries
- ✅ **Fallback Mechanisms**: EMA15 pullback when ORB fails
- ✅ **Session Management**: Proper UTC time handling
- ✅ **Data Validation**: Integrity checks for OHLCV data
- ✅ **Visual Reports**: Automatic generation of comprehensive charts
- ✅ **Interactive Plots**: Equity curves, drawdowns, performance analysis

## Technical Indicators

- **EMA**: Exponential Moving Average (50, 200 for bias)
- **ATR**: Average True Range for stop loss calculation
- **ADX**: Average Directional Index for trend strength
- **VWAP**: Volume Weighted Average Price for confirmation
- **ORB**: Opening Range Breakout levels (11:00-12:00 UTC)

## Time Zones

All times are in UTC:
- **ORB Window**: 11:00-12:00 UTC
- **Entry Window**: 11:00-13:00 UTC  
- **Session End**: 17:00 UTC

## Dependencies

- `ccxt`: Cryptocurrency exchange API
- `pandas`: Data manipulation and analysis
- `numpy`: Numerical computations
- `pytz`: Timezone handling

## Notes

- The strategy is designed for BTC/USDT futures on Binance
- All data is fetched from Binance public API (no API keys required)
- Backtest results are for educational purposes only
- Past performance does not guarantee future results
- Consider transaction costs and slippage in live trading

## License

This project is for educational and research purposes. Use at your own risk.
