#!/usr/bin/env python3
"""
Generate plots from existing trading results.
This script can be used to create visualizations from any trades CSV file.
"""

import argparse
import sys
import os
import pandas as pd

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from plot_results import create_comprehensive_report


def main():
    """Generate plots from trading results."""
    parser = argparse.ArgumentParser(
        description="Generate trading performance plots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_plots.py trades_final.csv
  python generate_plots.py trades.csv --output-dir plots/
  python generate_plots.py trades_final.csv --no-save
        """
    )
    
    parser.add_argument("csv_file", help="CSV file with trading results")
    parser.add_argument("--output-dir", default=".", help="Output directory for plots (default: current directory)")
    parser.add_argument("--no-save", action="store_true", help="Don't save plots to files, only display")
    parser.add_argument("--title", help="Custom title for the report")
    
    args = parser.parse_args()
    
    try:
        # Load trades data
        print(f"📊 Loading trades from {args.csv_file}...")
        trades_df = pd.read_csv(args.csv_file)
        
        if trades_df.empty:
            print("❌ No trades data found in the CSV file")
            return
        
        print(f"✅ Loaded {len(trades_df)} trades")
        
        # Display basic info
        total_pnl = trades_df['pnl_usdt'].sum()
        win_rate = (len(trades_df[trades_df['pnl_usdt'] > 0]) / len(trades_df)) * 100
        
        print(f"📈 Total PnL: {total_pnl:+.2f} USDT")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        
        # Create comprehensive report
        title = args.title or f"Trading Report - {args.csv_file}"
        print(f"\n🎨 Creating visual report: {title}")
        
        # Change to output directory if specified
        original_dir = os.getcwd()
        if args.output_dir != ".":
            os.makedirs(args.output_dir, exist_ok=True)
            os.chdir(args.output_dir)
        
        try:
            create_comprehensive_report(trades_df, save_plots=not args.no_save)
            print("✅ Visual report completed!")
            
            if not args.no_save:
                print(f"📁 Plots saved in: {os.getcwd()}")
                
        finally:
            # Return to original directory
            os.chdir(original_dir)
        
    except FileNotFoundError:
        print(f"❌ File not found: {args.csv_file}")
        print("   Make sure the CSV file exists and the path is correct.")
    except pd.errors.EmptyDataError:
        print("❌ The CSV file is empty")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()

