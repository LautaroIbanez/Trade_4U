"""
Utility Functions Module
Contains helper functions for data fetching, resampling, and session management.
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import pytz
import time


def fetch_historical_data(symbol, since, until=None, timeframe='1h', exchange_name='binance'):
    """
    Fetch historical data from Binance.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC/USDT:USDT')
        since: Start date in ISO format or datetime
        until: End date in ISO format or datetime (optional)
        timeframe: Data timeframe ('1h', '15m', '5m', etc.)
        exchange_name: Exchange name (default: 'binance')
    
    Returns:
        pandas.DataFrame: OHLCV data with UTC timezone
    """
    try:
        # Initialize exchange
        exchange = getattr(ccxt, exchange_name)({
            'apiKey': '',  # No API key needed for public data
            'secret': '',
            'sandbox': False,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        
        # Parse dates
        if isinstance(since, str):
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
        else:
            since_dt = since
            
        if until:
            if isinstance(until, str):
                until_dt = datetime.fromisoformat(until.replace('Z', '+00:00'))
            else:
                until_dt = until
        else:
            until_dt = datetime.now(timezone.utc)
        
        # Ensure timezone awareness
        if since_dt.tzinfo is None:
            since_dt = since_dt.replace(tzinfo=timezone.utc)
        if until_dt.tzinfo is None:
            until_dt = until_dt.replace(tzinfo=timezone.utc)
        
        # Convert to milliseconds
        since_ms = int(since_dt.timestamp() * 1000)
        until_ms = int(until_dt.timestamp() * 1000)
        
        print(f"Fetching {symbol} data from {since_dt} to {until_dt} ({timeframe})...")
        
        # Fetch data in chunks to avoid rate limits
        all_data = []
        current_since = since_ms
        chunk_size = 1000  # Number of candles per request
        
        while current_since < until_ms:
            try:
                # Calculate chunk end time
                chunk_until = min(current_since + (chunk_size * _get_timeframe_ms(timeframe)), until_ms)
                
                # Fetch chunk
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, current_since, chunk_size)
                
                if not ohlcv:
                    break
                
                all_data.extend(ohlcv)
                
                # Update current_since to last timestamp + 1
                current_since = ohlcv[-1][0] + 1
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error fetching chunk: {e}")
                break
        
        if not all_data:
            print(f"No data retrieved for {symbol}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)
        
        # Ensure UTC timezone
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')
        
        # Remove duplicates and sort
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index()
        
        # Filter by date range
        df = df[(df.index >= since_dt) & (df.index <= until_dt)]
        
        print(f"Retrieved {len(df)} candles for {symbol}")
        return df
        
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


def _get_timeframe_ms(timeframe):
    """Convert timeframe string to milliseconds."""
    timeframe_map = {
        '1m': 60 * 1000,
        '3m': 3 * 60 * 1000,
        '5m': 5 * 60 * 1000,
        '15m': 15 * 60 * 1000,
        '30m': 30 * 60 * 1000,
        '1h': 60 * 60 * 1000,
        '2h': 2 * 60 * 60 * 1000,
        '4h': 4 * 60 * 60 * 1000,
        '6h': 6 * 60 * 60 * 1000,
        '8h': 8 * 60 * 60 * 1000,
        '12h': 12 * 60 * 60 * 1000,
        '1d': 24 * 60 * 60 * 1000,
    }
    
    return timeframe_map.get(timeframe, 60 * 60 * 1000)  # Default to 1 hour


def resample_data(df, timeframe, agg_method='ohlc'):
    """
    Resample data to different timeframe.
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Target timeframe string
        agg_method: Aggregation method ('ohlc' or 'last')
    
    Returns:
        pandas.DataFrame: Resampled data
    """
    try:
        if df.empty:
            return df
        
        # Define aggregation rules
        if agg_method == 'ohlc':
            agg_rules = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
        else:  # last
            agg_rules = {
                'open': 'last',
                'high': 'last',
                'low': 'last',
                'close': 'last',
                'volume': 'last'
            }
        
        # Resample
        resampled = df.resample(timeframe).agg(agg_rules)
        
        # Remove rows with NaN values
        resampled = resampled.dropna()
        
        return resampled
        
    except Exception as e:
        print(f"Error resampling data: {e}")
        return df


def get_trading_sessions():
    """Get trading session times in UTC."""
    return {
        'orb_start': 11,    # 11:00 UTC
        'orb_end': 12,      # 12:00 UTC
        'entry_start': 11,  # 11:00 UTC
        'entry_end': 13,    # 13:00 UTC
        'session_end': 17   # 17:00 UTC
    }


def is_market_open(dt_utc):
    """Check if market is open at given UTC time."""
    hour = dt_utc.hour
    return 0 <= hour < 24  # Crypto markets are 24/7


def get_previous_close(data, current_time):
    """Get previous close price at given time."""
    try:
        previous_data = data[data.index < current_time]
        if not previous_data.empty:
            return previous_data['close'].iloc[-1]
        return None
    except:
        return None


def validate_data_integrity(df, required_columns=['open', 'high', 'low', 'close', 'volume']):
    """Validate data integrity and check for missing values."""
    if df.empty:
        return False, "Data is empty"
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing columns: {missing_columns}"
    
    # Check for NaN values
    nan_counts = df[required_columns].isnull().sum()
    if nan_counts.any():
        return False, f"NaN values found: {nan_counts.to_dict()}"
    
    # Check for negative prices
    price_columns = ['open', 'high', 'low', 'close']
    negative_prices = (df[price_columns] <= 0).any()
    if negative_prices.any():
        return False, "Negative or zero prices found"
    
    # Check for negative volume
    if (df['volume'] < 0).any():
        return False, "Negative volume found"
    
    # Check OHLC logic
    invalid_ohlc = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | (df['low'] > df['open']) | (df['low'] > df['close'])
    if invalid_ohlc.any():
        return False, "Invalid OHLC relationships found"
    
    return True, "Data validation passed"


def calculate_returns(prices):
    """Calculate simple returns from price series."""
    return prices.pct_change().dropna()


def calculate_log_returns(prices):
    """Calculate logarithmic returns from price series."""
    return np.log(prices / prices.shift(1)).dropna()


def get_volatility(returns, window=20):
    """Calculate rolling volatility."""
    return returns.rolling(window=window).std() * np.sqrt(252)  # Annualized


def format_currency(amount, currency='USDT', decimals=2):
    """Format currency amount for display."""
    return f"{amount:,.{decimals}f} {currency}"


def format_percentage(value, decimals=1):
    """Format percentage value for display."""
    return f"{value:.{decimals}f}%"


def get_timeframe_description(timeframe):
    """Get human-readable description of timeframe."""
    descriptions = {
        '1m': '1 minute',
        '3m': '3 minutes',
        '5m': '5 minutes',
        '15m': '15 minutes',
        '30m': '30 minutes',
        '1h': '1 hour',
        '2h': '2 hours',
        '4h': '4 hours',
        '6h': '6 hours',
        '8h': '8 hours',
        '12h': '12 hours',
        '1d': '1 day',
    }
    return descriptions.get(timeframe, timeframe)


def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is zero."""
    return numerator / denominator if denominator != 0 else default


def clamp(value, min_value, max_value):
    """Clamp value between min and max."""
    return max(min_value, min(value, max_value))


def round_to_precision(value, precision):
    """Round value to specified decimal precision."""
    return round(value, precision)


def get_current_utc_time():
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def is_weekend(dt):
    """Check if given datetime is weekend."""
    return dt.weekday() >= 5  # Saturday = 5, Sunday = 6


def get_next_trading_day(dt):
    """Get next trading day (skip weekends for traditional markets)."""
    next_day = dt + timedelta(days=1)
    while is_weekend(next_day):
        next_day += timedelta(days=1)
    return next_day
