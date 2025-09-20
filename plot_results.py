"""
Plotting Module for BTC 1TPD Backtester Results
Creates comprehensive visualizations of trading results.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from datetime import datetime
import seaborn as sns

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


def plot_equity_curve(trades_df, title="Equity Curve"):
    """Plot the equity curve showing cumulative PnL over time."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    # Calculate cumulative PnL
    trades_df = trades_df.copy()
    trades_df['cumulative_pnl'] = trades_df['pnl_usdt'].cumsum()
    
    # Convert entry_time to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(trades_df['entry_time']):
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    
    plt.figure(figsize=(12, 6))
    plt.plot(trades_df['entry_time'], trades_df['cumulative_pnl'], 
             linewidth=2, marker='o', markersize=4)
    
    # Add horizontal line at zero
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    
    # Formatting
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative PnL (USDT)', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45)
    
    # Add final PnL as text
    final_pnl = trades_df['cumulative_pnl'].iloc[-1]
    plt.text(0.02, 0.98, f'Total PnL: {final_pnl:+.2f} USDT', 
             transform=plt.gca().transAxes, fontsize=12, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
             verticalalignment='top')
    
    plt.tight_layout()
    return plt.gcf()


def plot_pnl_distribution(trades_df, title="PnL Distribution"):
    """Plot the distribution of individual trade PnL."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    plt.figure(figsize=(10, 6))
    
    # Create histogram
    plt.hist(trades_df['pnl_usdt'], bins=20, alpha=0.7, edgecolor='black')
    
    # Add vertical lines for mean and median
    mean_pnl = trades_df['pnl_usdt'].mean()
    median_pnl = trades_df['pnl_usdt'].median()
    
    plt.axvline(mean_pnl, color='red', linestyle='--', linewidth=2, 
                label=f'Mean: {mean_pnl:+.2f} USDT')
    plt.axvline(median_pnl, color='green', linestyle='--', linewidth=2, 
                label=f'Median: {median_pnl:+.2f} USDT')
    plt.axvline(0, color='gray', linestyle='-', alpha=0.5, label='Break-even')
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('PnL per Trade (USDT)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return plt.gcf()


def plot_monthly_performance(trades_df, title="Monthly Performance"):
    """Plot monthly PnL breakdown."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    trades_df = trades_df.copy()
    
    # Convert entry_time to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(trades_df['entry_time']):
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    
    # Group by month
    trades_df['month'] = trades_df['entry_time'].dt.to_period('M')
    monthly_pnl = trades_df.groupby('month')['pnl_usdt'].sum()
    
    plt.figure(figsize=(12, 6))
    
    # Create bar plot
    colors = ['green' if x > 0 else 'red' for x in monthly_pnl.values]
    bars = plt.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, monthly_pnl.values)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (1 if value > 0 else -3),
                f'{value:+.0f}', ha='center', va='bottom' if value > 0 else 'top')
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Month', fontsize=12)
    plt.ylabel('PnL (USDT)', fontsize=12)
    plt.xticks(range(len(monthly_pnl)), [str(month) for month in monthly_pnl.index], rotation=45)
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return plt.gcf()


def plot_win_loss_analysis(trades_df, title="Win/Loss Analysis"):
    """Plot win/loss analysis with R-multiple distribution."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Win/Loss pie chart
    wins = len(trades_df[trades_df['pnl_usdt'] > 0])
    losses = len(trades_df[trades_df['pnl_usdt'] < 0])
    breaks = len(trades_df[trades_df['pnl_usdt'] == 0])
    
    labels = ['Wins', 'Losses']
    sizes = [wins, losses]
    colors = ['lightgreen', 'lightcoral']
    
    if breaks > 0:
        labels.append('Break-even')
        sizes.append(breaks)
        colors.append('lightgray')
    
    ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
    ax1.set_title('Win/Loss Distribution', fontweight='bold')
    
    # R-multiple distribution
    r_multiples = trades_df['r_multiple'].dropna()
    if not r_multiples.empty:
        ax2.hist(r_multiples, bins=20, alpha=0.7, edgecolor='black')
        ax2.axvline(0, color='gray', linestyle='-', alpha=0.5, label='Break-even')
        ax2.axvline(r_multiples.mean(), color='red', linestyle='--', 
                   label=f'Mean: {r_multiples.mean():.2f}R')
        ax2.set_xlabel('R-Multiple')
        ax2.set_ylabel('Frequency')
        ax2.set_title('R-Multiple Distribution', fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=16, fontweight='bold')
    plt.tight_layout()
    return plt.gcf()


def plot_drawdown(trades_df, title="Drawdown Analysis"):
    """Plot drawdown analysis."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    trades_df = trades_df.copy()
    
    # Calculate cumulative PnL
    trades_df['cumulative_pnl'] = trades_df['pnl_usdt'].cumsum()
    
    # Calculate running maximum
    trades_df['running_max'] = trades_df['cumulative_pnl'].expanding().max()
    
    # Calculate drawdown
    trades_df['drawdown'] = trades_df['cumulative_pnl'] - trades_df['running_max']
    
    plt.figure(figsize=(12, 6))
    
    # Plot drawdown
    plt.fill_between(range(len(trades_df)), trades_df['drawdown'], 0, 
                     color='red', alpha=0.3, label='Drawdown')
    plt.plot(range(len(trades_df)), trades_df['drawdown'], color='red', linewidth=1)
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Trade Number', fontsize=12)
    plt.ylabel('Drawdown (USDT)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add max drawdown info
    max_dd = trades_df['drawdown'].min()
    plt.text(0.02, 0.98, f'Max Drawdown: {max_dd:.2f} USDT', 
             transform=plt.gca().transAxes, fontsize=12,
             bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
             verticalalignment='top')
    
    plt.tight_layout()
    return plt.gcf()


def plot_trade_timeline(trades_df, title="Trade Timeline"):
    """Plot individual trades on a timeline."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    trades_df = trades_df.copy()
    
    # Convert entry_time to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(trades_df['entry_time']):
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    
    plt.figure(figsize=(14, 8))
    
    # Separate wins and losses
    wins = trades_df[trades_df['pnl_usdt'] > 0]
    losses = trades_df[trades_df['pnl_usdt'] < 0]
    
    # Plot wins
    if not wins.empty:
        plt.scatter(wins['entry_time'], wins['pnl_usdt'], 
                   color='green', s=60, alpha=0.7, label='Winning Trades')
    
    # Plot losses
    if not losses.empty:
        plt.scatter(losses['entry_time'], losses['pnl_usdt'], 
                   color='red', s=60, alpha=0.7, label='Losing Trades')
    
    # Add horizontal line at zero
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    
    # Formatting
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('PnL per Trade (USDT)', fontsize=12)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Format x-axis dates
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator(interval=3))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    return plt.gcf()


def plot_trades_on_price(trades_df, title="Trades on Price Chart"):
    """Plot trades overlaid on BTC price chart."""
    if trades_df.empty:
        print("No trades to plot")
        return
    
    # Import here to avoid circular imports
    from utils import fetch_historical_data
    
    trades_df = trades_df.copy()
    
    # Convert entry_time to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(trades_df['entry_time']):
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'])
    
    # Get the date range from trades
    start_date = trades_df['entry_time'].min().date()
    end_date = trades_df['entry_time'].max().date()
    
    print(f"Fetching price data from {start_date} to {end_date}...")
    
    try:
        # Fetch BTC price data for the period
        price_data = fetch_historical_data("BTC/USDT:USDT", 
                                         str(start_date), 
                                         str(end_date), 
                                         "1h")
        
        if price_data.empty:
            print("No price data available")
            return None
            
        # Create the plot
        fig, ax = plt.subplots(figsize=(16, 10))
        
        # Plot price line
        ax.plot(price_data.index, price_data['close'], 
                linewidth=1, color='black', alpha=0.7, label='BTC Price')
        
        # Plot trades
        for _, trade in trades_df.iterrows():
            entry_time = trade['entry_time']
            entry_price = trade['entry_price']
            exit_time = trade['exit_time']
            exit_price = trade['exit_price']
            side = trade['side']
            pnl = trade['pnl_usdt']
            
            # Convert exit_time to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(pd.Series([exit_time])):
                exit_time = pd.to_datetime(exit_time)
            
            # Determine color based on PnL
            if pnl > 0:
                color = 'green'
                marker = '^' if side == 'long' else 'v'
                alpha = 0.8
            else:
                color = 'red'
                marker = 'v' if side == 'long' else '^'
                alpha = 0.8
            
            # Plot entry point
            ax.scatter(entry_time, entry_price, 
                      color=color, marker=marker, s=100, alpha=alpha, 
                      edgecolors='black', linewidth=1, zorder=5)
            
            # Plot exit point
            ax.scatter(exit_time, exit_price, 
                      color=color, marker='x', s=80, alpha=alpha, 
                      edgecolors='black', linewidth=2, zorder=5)
            
            # Draw line from entry to exit
            ax.plot([entry_time, exit_time], [entry_price, exit_price], 
                   color=color, alpha=0.6, linewidth=2, linestyle='--')
            
            # Add trade info as text (for first few trades to avoid clutter)
            if len(trades_df) <= 20:  # Only show text for small number of trades
                mid_time = entry_time + (exit_time - entry_time) / 2
                mid_price = (entry_price + exit_price) / 2
                
                # Add trade number and PnL
                ax.annotate(f'T{len(trades_df[trades_df["entry_time"] <= entry_time])}\n{pnl:+.0f}',
                           xy=(mid_time, mid_price),
                           xytext=(0, 10), textcoords='offset points',
                           ha='center', va='bottom',
                           fontsize=8, alpha=0.8,
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        
        # Formatting
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('BTC Price (USDT)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(price_data)//20)))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add legend
        legend_elements = [
            plt.Line2D([0], [0], color='black', linewidth=1, label='BTC Price'),
            plt.scatter([], [], color='green', marker='^', s=100, label='Long Entry'),
            plt.scatter([], [], color='green', marker='v', s=100, label='Short Entry'),
            plt.scatter([], [], color='red', marker='v', s=100, label='Long Loss'),
            plt.scatter([], [], color='red', marker='^', s=100, label='Short Loss'),
            plt.scatter([], [], color='gray', marker='x', s=80, label='Exit Points')
        ]
        ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
        
        # Add summary statistics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl_usdt'] > 0])
        win_rate = (winning_trades / total_trades) * 100
        total_pnl = trades_df['pnl_usdt'].sum()
        
        stats_text = f'Trades: {total_trades} | Win Rate: {win_rate:.1f}% | Total PnL: {total_pnl:+.0f} USDT'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=12,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
                verticalalignment='top')
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        print(f"Error creating price chart: {e}")
        return None


def create_comprehensive_report(trades_df, save_plots=True):
    """Create a comprehensive visual report of trading results."""
    if trades_df.empty:
        print("No trades to create report for")
        return
    
    print("📊 Creating comprehensive trading report...")
    
    # Create all plots
    plots = {
        'equity_curve': plot_equity_curve(trades_df),
        'pnl_distribution': plot_pnl_distribution(trades_df),
        'monthly_performance': plot_monthly_performance(trades_df),
        'win_loss_analysis': plot_win_loss_analysis(trades_df),
        'drawdown': plot_drawdown(trades_df),
        'trade_timeline': plot_trade_timeline(trades_df),
        'price_chart': plot_trades_on_price(trades_df)
    }
    
    if save_plots:
        print("💾 Saving plots...")
        for name, fig in plots.items():
            filename = f"trading_report_{name}.png"
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"   ✅ Saved: {filename}")
    
    # Show all plots
    plt.show()
    
    print("✅ Comprehensive report created!")
    return plots


def main():
    """Example usage of the plotting functions."""
    try:
        # Load trades data
        trades_df = pd.read_csv('trades_final.csv')
        
        if trades_df.empty:
            print("❌ No trades data found in trades_final.csv")
            return
        
        print(f"📈 Loaded {len(trades_df)} trades")
        
        # Create comprehensive report
        create_comprehensive_report(trades_df, save_plots=True)
        
    except FileNotFoundError:
        print("❌ trades_final.csv not found. Please run the backtester first.")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
