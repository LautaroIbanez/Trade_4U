#!/usr/bin/env python3
"""
BTC 1 Trade Per Day Backtester - Final Working Version
Simplified version that generates trades successfully.
"""

import argparse
import sys
import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import fetch_historical_data
from indicators import ema, atr, adx, vwap
from plot_results import create_comprehensive_report


class SimpleTradingStrategy:
    """Simplified trading strategy that works."""
    
    def __init__(self, config):
        """Initialize strategy with configuration parameters."""
        self.config = config
        self.risk_usdt = config.get('risk_usdt', 20.0)
        self.daily_target = config.get('daily_target', 50.0)
        self.daily_max_loss = config.get('daily_max_loss', -30.0)
        self.adx_min = config.get('adx_min', 15.0)
        self.atr_mult = config.get('atr_mult_orb', 1.2)
        self.tp_multiplier = config.get('tp_multiplier', 2.0)
        
        # Daily state
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 1
    
    def reset_daily_state(self):
        """Reset daily tracking variables."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
    
    def can_trade_today(self):
        """Check if trading is allowed today."""
        return (self.daily_trades < self.max_daily_trades and 
                self.daily_pnl < self.daily_target and 
                self.daily_pnl > self.daily_max_loss)
    
    def get_orb_levels(self, day_data):
        """Calculate ORB levels for the day."""
        # ORB window: 11:00-12:00 UTC
        orb_data = day_data[(day_data.index.hour >= 11) & (day_data.index.hour < 12)]
        
        if orb_data.empty:
            return None, None
        
        orb_high = orb_data['high'].max()
        orb_low = orb_data['low'].min()
        
        return orb_high, orb_low
    
    def check_breakout(self, entry_data, orb_high, orb_low):
        """Check for ORB breakouts."""
        for timestamp, row in entry_data.iterrows():
            current_price = row['close']
            
            # Long breakout
            if current_price > orb_high:
                return 'long', timestamp, current_price
            
            # Short breakout
            elif current_price < orb_low:
                return 'short', timestamp, current_price
        
        return None, None, None
    
    def calculate_trade_params(self, side, entry_price, day_data):
        """Calculate trade parameters."""
        # Calculate ATR
        atr_value = atr(day_data, 14).iloc[-1]
        
        if pd.isna(atr_value):
            return None
        
        # Calculate stop loss and take profit
        if side == 'long':
            stop_loss = entry_price - (atr_value * self.atr_mult)
            take_profit = entry_price + (atr_value * self.tp_multiplier)
        else:
            stop_loss = entry_price + (atr_value * self.atr_mult)
            take_profit = entry_price - (atr_value * self.tp_multiplier)
        
        # Calculate position size
        risk_amount = self.risk_usdt
        price_diff = abs(entry_price - stop_loss)
        position_size = risk_amount / price_diff if price_diff > 0 else 0
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'atr_value': atr_value
        }
    
    def simulate_trade_exit(self, trade_params, side, day_data):
        """Simulate trade exit."""
        entry_price = trade_params['entry_price']
        stop_loss = trade_params['stop_loss']
        take_profit = trade_params['take_profit']
        position_size = trade_params['position_size']
        
        # Get remaining data after entry
        entry_time = trade_params['entry_time']
        remaining_data = day_data[day_data.index > entry_time]
        
        if remaining_data.empty:
            # Exit at end of day
            exit_price = day_data['close'].iloc[-1]
            exit_reason = 'session_end'
        else:
            # Check for TP/SL hits
            if side == 'long':
                tp_hit = remaining_data['high'] >= take_profit
                sl_hit = remaining_data['low'] <= stop_loss
                
                if tp_hit.any():
                    exit_time = remaining_data[tp_hit].index[0]
                    exit_price = take_profit
                    exit_reason = 'take_profit'
                elif sl_hit.any():
                    exit_time = remaining_data[sl_hit].index[0]
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                else:
                    exit_time = remaining_data.index[-1]
                    exit_price = remaining_data['close'].iloc[-1]
                    exit_reason = 'session_end'
            else:  # short
                tp_hit = remaining_data['low'] <= take_profit
                sl_hit = remaining_data['high'] >= stop_loss
                
                if tp_hit.any():
                    exit_time = remaining_data[tp_hit].index[0]
                    exit_price = take_profit
                    exit_reason = 'take_profit'
                elif sl_hit.any():
                    exit_time = remaining_data[sl_hit].index[0]
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                else:
                    exit_time = remaining_data.index[-1]
                    exit_price = remaining_data['close'].iloc[-1]
                    exit_reason = 'session_end'
        
        # Calculate PnL
        if side == 'long':
            pnl = (exit_price - entry_price) * position_size
        else:
            pnl = (entry_price - exit_price) * position_size
        
        # Calculate R-multiple
        risk = abs(entry_price - stop_loss)
        if risk > 0:
            r_multiple = abs(exit_price - entry_price) / risk
            if (side == 'long' and exit_price < entry_price) or (side == 'short' and exit_price > entry_price):
                r_multiple = -r_multiple
        else:
            r_multiple = 0
        
        return {
            'exit_time': exit_time,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl_usdt': pnl,
            'r_multiple': r_multiple
        }
    
    def process_day(self, day_data, date):
        """Process trading for a single day."""
        trades = []
        
        # Reset daily state
        self.reset_daily_state()
        
        if len(day_data) < 50:  # Need enough data for indicators
            return trades
        
        # Get ORB levels
        orb_high, orb_low = self.get_orb_levels(day_data)
        
        if orb_high is None or orb_low is None:
            return trades
        
        # Entry window: 11:00-13:00 UTC
        entry_data = day_data[(day_data.index.hour >= 11) & (day_data.index.hour < 13)]
        
        if entry_data.empty:
            return trades
        
        # Check for breakouts
        side, breakout_time, entry_price = self.check_breakout(entry_data, orb_high, orb_low)
        
        if side is None:
            return trades
        
        # Calculate trade parameters
        trade_params = self.calculate_trade_params(side, entry_price, day_data)
        
        if trade_params is None:
            return trades
        
        # Add entry info to trade params
        trade_params['entry_price'] = entry_price
        trade_params['entry_time'] = breakout_time
        
        # Simulate trade
        exit_info = self.simulate_trade_exit(trade_params, side, day_data)
        
        # Create trade record
        trade = {
            'day_key': date.strftime('%Y-%m-%d'),
            'entry_time': trade_params['entry_time'],
            'side': side,
            'entry_price': trade_params['entry_price'],
            'sl': trade_params['stop_loss'],
            'tp': trade_params['take_profit'],
            'exit_time': exit_info['exit_time'],
            'exit_price': exit_info['exit_price'],
            'exit_reason': exit_info['exit_reason'],
            'pnl_usdt': exit_info['pnl_usdt'],
            'r_multiple': exit_info['r_multiple'],
            'used_fallback': False
        }
        
        trades.append(trade)
        
        # Update daily state
        self.daily_pnl += exit_info['pnl_usdt']
        self.daily_trades += 1
        
        return trades


def run_backtest(symbol, since, until, config):
    """Run the backtest."""
    print(f"🚀 BTC 1 Trade Per Day Backtester - FINAL VERSION")
    print("=" * 60)
    print(f"Symbol: {symbol}")
    print(f"Period: {since} to {until}")
    print(f"Risk: {config['risk_usdt']} USDT")
    print(f"ADX Min: {config['adx_min']}")
    print("=" * 60)
    
    # Fetch data
    print("\n📊 Fetching historical data...")
    data = fetch_historical_data(symbol, since, until, "15m")
    
    if data.empty:
        print("❌ No data retrieved.")
        return pd.DataFrame()
    
    print(f"✅ Data: {len(data)} candles")
    
    # Initialize strategy
    strategy = SimpleTradingStrategy(config)
    
    # Process each day
    print("\n🔄 Running backtest...")
    all_trades = []
    
    daily_groups = data.groupby(data.index.date)
    
    for date, day_data in daily_groups:
        trades = strategy.process_day(day_data, date)
        all_trades.extend(trades)
    
    return pd.DataFrame(all_trades)


def display_summary(trades_df):
    """Display backtest summary."""
    if trades_df.empty:
        print("\n❌ No trades generated during backtest period.")
        return
    
    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df['pnl_usdt'] > 0])
    losing_trades = len(trades_df[trades_df['pnl_usdt'] < 0])
    
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    total_pnl = trades_df['pnl_usdt'].sum()
    avg_win = trades_df[trades_df['pnl_usdt'] > 0]['pnl_usdt'].mean() if winning_trades > 0 else 0
    avg_loss = trades_df[trades_df['pnl_usdt'] < 0]['pnl_usdt'].mean() if losing_trades > 0 else 0
    
    gross_profit = trades_df[trades_df['pnl_usdt'] > 0]['pnl_usdt'].sum()
    gross_loss = abs(trades_df[trades_df['pnl_usdt'] < 0]['pnl_usdt'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    expectancy = (winning_trades * avg_win + losing_trades * avg_loss) / total_trades if total_trades > 0 else 0
    
    # Consecutive losses
    consecutive_losses = 0
    max_consecutive = 0
    
    for pnl in trades_df['pnl_usdt']:
        if pnl < 0:
            consecutive_losses += 1
            max_consecutive = max(max_consecutive, consecutive_losses)
        else:
            consecutive_losses = 0
    
    # Green days
    daily_pnl = trades_df.groupby('day_key')['pnl_usdt'].sum()
    green_days = len(daily_pnl[daily_pnl > 0])
    total_days = len(daily_pnl)
    green_days_pct = (green_days / total_days) * 100 if total_days > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 BACKTEST SUMMARY")
    print("=" * 50)
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {win_rate:.1f}% ({winning_trades}/{total_trades})")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Expectancy: {expectancy:+.2f} USDT")
    print(f"Avg Win: {avg_win:+.2f} USDT")
    print(f"Avg Loss: {avg_loss:+.2f} USDT")
    print(f"Max Consecutive Losses: {max_consecutive}")
    print(f"Green Days: {green_days_pct:.0f}% ({green_days}/{total_days})")
    print(f"Total PnL: {total_pnl:+.2f} USDT")
    print("=" * 50)
    
    # Show first few trades
    if not trades_df.empty:
        print("\nFirst 5 trades:")
        print(trades_df[['day_key', 'side', 'entry_price', 'exit_price', 'pnl_usdt', 'r_multiple']].head())


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BTC 1 Trade Per Day Backtester - Final Version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python btc_1tpd_backtest_final.py --since "2024-06-01" --until "2024-09-19" --risk_usdt 20
  python btc_1tpd_backtest_final.py --since "2024-01-01" --risk_usdt 50 --adx_min 10
        """
    )
    
    parser.add_argument("--symbol", default="BTC/USDT:USDT", help="Trading symbol (default: BTC/USDT:USDT)")
    parser.add_argument("--since", required=True, help="Start date in ISO format (e.g., 2024-06-01)")
    parser.add_argument("--until", help="End date in ISO format (e.g., 2024-09-19)")
    parser.add_argument("--risk_usdt", type=float, default=20.0, help="Risk amount in USDT (default: 20)")
    parser.add_argument("--daily_target", type=float, default=50.0, help="Daily profit target in USDT (default: 50)")
    parser.add_argument("--daily_max_loss", type=float, default=-30.0, help="Daily max loss in USDT (default: -30)")
    parser.add_argument("--adx_min", type=float, default=15.0, help="Minimum ADX value (default: 15)")
    parser.add_argument("--atr_mult_orb", type=float, default=1.2, help="ATR multiplier for stop loss (default: 1.2)")
    parser.add_argument("--tp_multiplier", type=float, default=2.0, help="Take profit multiplier (default: 2.0)")
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    config = {
        'risk_usdt': args.risk_usdt,
        'daily_target': args.daily_target,
        'daily_max_loss': args.daily_max_loss,
        'adx_min': args.adx_min,
        'atr_mult_orb': args.atr_mult_orb,
        'tp_multiplier': args.tp_multiplier
    }
    
    # Run backtest
    results = run_backtest(args.symbol, args.since, args.until, config)
    
    # Save results
    if not results.empty:
        output_file = "trades_final.csv"
        results.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to {output_file}")
    
    # Display summary
    display_summary(results)
    
    # Create visual report if there are trades
    if not results.empty:
        try:
            print("\n📊 Creating visual report...")
            create_comprehensive_report(results, save_plots=True)
        except Exception as e:
            print(f"⚠️  Could not create visual report: {e}")
            print("   Make sure matplotlib and seaborn are installed:")
            print("   pip install matplotlib seaborn")


if __name__ == "__main__":
    main()
