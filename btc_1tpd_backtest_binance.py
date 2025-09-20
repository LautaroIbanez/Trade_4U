#!/usr/bin/env python3
"""
BTC 1 Trade Per Day Backtester - Main CLI Script
Implements a comprehensive backtesting system for BTC/USDT futures trading strategy.
"""

import argparse
import sys
import os
from datetime import datetime, timezone
import pandas as pd

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import fetch_historical_data, resample_data
from strategy import TradingStrategy
from backtester import Backtester


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BTC 1 Trade Per Day Backtester",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python btc_1tpd_backtest_binance.py --since "2024-06-01" --until "2024-09-19" --signal_tf 15 --risk_usdt 20
  python btc_1tpd_backtest_binance.py --since "2024-01-01" --risk_usdt 50 --daily_target 100 --force_one_trade
        """
    )
    
    # Data parameters
    parser.add_argument("--symbol", default="BTC/USDT:USDT", help="Trading symbol (default: BTC/USDT:USDT)")
    parser.add_argument("--since", required=True, help="Start date in ISO format (e.g., 2024-06-01)")
    parser.add_argument("--until", help="End date in ISO format (e.g., 2024-09-19)")
    parser.add_argument("--signal_tf", type=int, choices=[5, 15], default=15, help="Signal timeframe in minutes (default: 15)")
    
    # Risk management
    parser.add_argument("--risk_usdt", type=float, default=20.0, help="Risk amount in USDT (default: 20)")
    parser.add_argument("--daily_target", type=float, default=50.0, help="Daily profit target in USDT (default: 50)")
    parser.add_argument("--daily_max_loss", type=float, default=-30.0, help="Daily max loss in USDT (default: -30)")
    
    # Strategy parameters
    parser.add_argument("--force_one_trade", action="store_true", help="Force one trade per day using fallback")
    parser.add_argument("--fallback_mode", choices=["ORB", "EMA15_pullback", "BestOfBoth"], default="BestOfBoth", help="Fallback strategy mode")
    parser.add_argument("--adx_min", type=float, default=20.0, help="Minimum ADX value for confirmation (default: 20)")
    parser.add_argument("--min_rr_ok", type=float, default=1.8, help="Minimum R/R ratio for fallback trades (default: 1.8)")
    
    # Technical parameters
    parser.add_argument("--atr_mult_orb", type=float, default=1.2, help="ATR multiplier for ORB stop loss (default: 1.2)")
    parser.add_argument("--atr_mult_fallback", type=float, default=1.5, help="ATR multiplier for fallback stop loss (default: 1.5)")
    parser.add_argument("--tp_multiplier", type=float, default=2.0, help="Take profit multiplier (default: 2.0)")
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    print("🚀 BTC 1 Trade Per Day Backtester")
    print("=" * 50)
    print(f"Symbol: {args.symbol}")
    print(f"Period: {args.since} to {args.until or 'now'}")
    print(f"Signal TF: {args.signal_tf}m")
    print(f"Risk: {args.risk_usdt} USDT")
    print(f"Daily Target: {args.daily_target} USDT")
    print(f"Daily Max Loss: {args.daily_max_loss} USDT")
    print(f"Force One Trade: {args.force_one_trade}")
    print(f"Fallback Mode: {args.fallback_mode}")
    print("=" * 50)
    
    try:
        # Fetch historical data
        print("\n📊 Fetching historical data...")
        htf_data = fetch_historical_data(args.symbol, args.since, args.until, "1h")
        ltf_data = fetch_historical_data(args.symbol, args.since, args.until, f"{args.signal_tf}m")
        
        if htf_data.empty or ltf_data.empty:
            print("❌ Error: No data retrieved. Check your date range and symbol.")
            return
        
        print(f"✅ High TF data: {len(htf_data)} candles")
        print(f"✅ Low TF data: {len(ltf_data)} candles")
        
        # Initialize strategy
        strategy_config = {
            "signal_tf": args.signal_tf,
            "risk_usdt": args.risk_usdt,
            "daily_target": args.daily_target,
            "daily_max_loss": args.daily_max_loss,
            "force_one_trade": args.force_one_trade,
            "fallback_mode": args.fallback_mode,
            "adx_min": args.adx_min,
            "min_rr_ok": args.min_rr_ok,
            "atr_mult_orb": args.atr_mult_orb,
            "atr_mult_fallback": args.atr_mult_fallback,
            "tp_multiplier": args.tp_multiplier
        }
        
        strategy = TradingStrategy(strategy_config)
        
        # Initialize backtester
        backtester = Backtester(strategy, htf_data, ltf_data)
        
        # Run backtest
        print("\n🔄 Running backtest...")
        results = backtester.run_backtest()
        
        # Save results
        output_file = "trades.csv"
        results.to_csv(output_file, index=False)
        print(f"✅ Results saved to {output_file}")
        
        # Display summary
        backtester.display_summary()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

