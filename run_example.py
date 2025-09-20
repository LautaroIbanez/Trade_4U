#!/usr/bin/env python3
"""
Example script showing how to run the BTC 1TPD backtester.
"""

import subprocess
import sys

def run_backtest_example():
    """Run a complete backtest example."""
    print("🚀 BTC 1 Trade Per Day Backtester - Example Run")
    print("=" * 60)
    
    # Example 1: Basic backtest
    print("\n📊 Running basic backtest (June-September 2024)...")
    cmd = [
        sys.executable, 
        "btc_1tpd_backtest_final.py",
        "--since", "2024-06-01",
        "--until", "2024-09-19",
        "--risk_usdt", "20"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print("STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print(f"Return code: {result.returncode}")
    except Exception as e:
        print(f"Error running backtest: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Example completed!")
    print("Check 'trades_final.csv' for detailed results.")

if __name__ == "__main__":
    run_backtest_example()

