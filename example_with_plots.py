#!/usr/bin/env python3
"""
Example script demonstrating the BTC 1TPD backtester with visual reports.
"""

import subprocess
import sys
import os

def run_backtest_with_plots():
    """Run a complete backtest with visual reports."""
    print("🚀 BTC 1 Trade Per Day Backtester - Example with Plots")
    print("=" * 70)
    
    # Example: Run backtest for a specific period
    print("\n📊 Running backtest for August 2024...")
    cmd = [
        sys.executable, 
        "btc_1tpd_backtest_final.py",
        "--since", "2024-08-01",
        "--until", "2024-08-31",
        "--risk_usdt", "20",
        "--adx_min", "15"
    ]
    
    try:
        print("Command:", " ".join(cmd))
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ Backtest completed successfully!")
            print("\n📁 Generated files:")
            
            # Check for generated files
            files_to_check = [
                "trades_final.csv",
                "trading_report_equity_curve.png",
                "trading_report_pnl_distribution.png",
                "trading_report_monthly_performance.png",
                "trading_report_win_loss_analysis.png",
                "trading_report_drawdown.png",
                "trading_report_trade_timeline.png"
            ]
            
            for filename in files_to_check:
                if os.path.exists(filename):
                    size = os.path.getsize(filename)
                    print(f"   ✅ {filename} ({size:,} bytes)")
                else:
                    print(f"   ❌ {filename} (not found)")
            
            print("\n🎨 Visual reports generated!")
            print("   You can now analyze your trading performance with the generated charts.")
            
        else:
            print(f"\n❌ Backtest failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"\n❌ Error running backtest: {e}")
    
    print("\n" + "=" * 70)
    print("💡 Next steps:")
    print("   1. Check the generated PNG files for visual analysis")
    print("   2. Review trades_final.csv for detailed trade data")
    print("   3. Try different parameters to optimize the strategy")
    print("   4. Use generate_plots.py to create plots from other CSV files")

def demonstrate_plot_generation():
    """Demonstrate standalone plot generation."""
    print("\n🎨 Demonstrating standalone plot generation...")
    
    if not os.path.exists("trades_final.csv"):
        print("❌ No trades_final.csv found. Run the backtest first.")
        return
    
    # Generate plots with custom output directory
    cmd = [
        sys.executable,
        "generate_plots.py",
        "trades_final.csv",
        "--output-dir", "example_plots",
        "--title", "Example Trading Analysis"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print("✅ Standalone plot generation completed!")
        else:
            print(f"❌ Plot generation failed with return code: {result.returncode}")
    except Exception as e:
        print(f"❌ Error generating plots: {e}")

def main():
    """Main execution function."""
    print("Welcome to the BTC 1TPD Backtester with Visual Reports!")
    print("This example demonstrates the complete workflow including chart generation.")
    
    # Run backtest with plots
    run_backtest_with_plots()
    
    # Demonstrate standalone plot generation
    demonstrate_plot_generation()
    
    print("\n🎉 Example completed!")
    print("The backtester now provides comprehensive visual analysis of trading performance.")

if __name__ == "__main__":
    main()

