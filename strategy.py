"""
Trading Strategy Module
Implements the 1 trade per day BTC strategy with ORB and fallback logic.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from indicators import (
    ema, atr, adx, vwap, opening_range_high, opening_range_low,
    opening_range_breakout, engulfing_pattern, volume_confirmation,
    calculate_r_multiple, get_macro_bias, is_trading_session,
    is_entry_window, is_orb_window
)


class TradingStrategy:
    """Main trading strategy class implementing 1 trade per day logic."""
    
    def __init__(self, config):
        """Initialize strategy with configuration parameters."""
        self.config = config
        self.signal_tf = config['signal_tf']
        self.risk_usdt = config['risk_usdt']
        self.daily_target = config['daily_target']
        self.daily_max_loss = config['daily_max_loss']
        self.force_one_trade = config['force_one_trade']
        self.fallback_mode = config['fallback_mode']
        self.adx_min = config['adx_min']
        self.min_rr_ok = config['min_rr_ok']
        self.atr_mult_orb = config['atr_mult_orb']
        self.atr_mult_fallback = config['atr_mult_fallback']
        self.tp_multiplier = config['tp_multiplier']
        
        # Session times (UTC)
        self.orb_start = 11  # 11:00 UTC
        self.orb_end = 12    # 12:00 UTC
        self.entry_start = 11  # 11:00 UTC
        self.entry_end = 13    # 13:00 UTC
        self.session_end = 17  # 17:00 UTC
        
        # Daily state
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.max_daily_trades = 1
        
    def reset_daily_state(self):
        """Reset daily tracking variables."""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        
    def is_daily_target_reached(self):
        """Check if daily profit target is reached."""
        return self.daily_pnl >= self.daily_target
        
    def is_daily_loss_limit_reached(self):
        """Check if daily loss limit is reached."""
        return self.daily_pnl <= self.daily_max_loss
        
    def can_trade_today(self):
        """Check if trading is allowed today."""
        return (self.daily_trades < self.max_daily_trades and 
                not self.is_daily_target_reached() and 
                not self.is_daily_loss_limit_reached())
        
    def calculate_position_size(self, entry_price, stop_loss):
        """Calculate position size based on risk management."""
        risk_amount = self.risk_usdt
        price_diff = abs(entry_price - stop_loss)
        
        if price_diff == 0:
            return 0
            
        position_size = risk_amount / price_diff
        return min(position_size, risk_amount / (entry_price * 0.01))  # Max 1% of equity per trade
    
    def get_stop_loss_price(self, entry_price, side, atr_value, is_orb=True):
        """Calculate stop loss price."""
        atr_mult = self.atr_mult_orb if is_orb else self.atr_mult_fallback
        
        if side == 'long':
            return entry_price - (atr_value * atr_mult)
        else:
            return entry_price + (atr_value * atr_mult)
    
    def get_take_profit_price(self, entry_price, stop_loss, side):
        """Calculate take profit price."""
        risk = abs(entry_price - stop_loss)
        reward = risk * self.tp_multiplier
        
        if side == 'long':
            return entry_price + reward
        else:
            return entry_price - reward
    
    def check_orb_conditions(self, ltf_data, htf_data, side):
        """Check Opening Range Breakout conditions."""
        try:
            # Get current time
            current_time = ltf_data.index[-1]
            
            # Check if we're in ORB calculation window
            if not is_orb_window(current_time):
                return False, None, None, None
            
            # Calculate ORB levels
            # Convert to datetime for replace operations
            if hasattr(current_time, 'to_pydatetime'):
                dt = current_time.to_pydatetime()
            else:
                dt = current_time
            
            orb_start_time = dt.replace(hour=self.orb_start, minute=0, second=0, microsecond=0)
            orb_end_time = dt.replace(hour=self.orb_end, minute=0, second=0, microsecond=0)
            
            orb_high = opening_range_high(ltf_data, orb_start_time, orb_end_time)
            orb_low = opening_range_low(ltf_data, orb_start_time, orb_end_time)
            
            if pd.isna(orb_high) or pd.isna(orb_low):
                return False, None, None, None
            
            # Check breakout
            if not opening_range_breakout(ltf_data, orb_high, orb_low, side):
                return False, orb_high, orb_low, None
            
            # Get current price
            entry_price = ltf_data['close'].iloc[-1]
            
            # Calculate indicators
            atr_value = atr(ltf_data, 14).iloc[-1]
            adx_value = adx(ltf_data, 14).iloc[-1]
            vwap_value = vwap(ltf_data).iloc[-1]
            
            # Check confirmations (relaxed)
            volume_ok = volume_confirmation(ltf_data, 20)
            adx_ok = adx_value >= self.adx_min
            
            if side == 'long':
                vwap_ok = entry_price > vwap_value
            else:
                vwap_ok = entry_price < vwap_value
            
            # Relaxed conditions: Only require volume and ADX, VWAP is nice-to-have
            if volume_ok and adx_ok:
                stop_loss = self.get_stop_loss_price(entry_price, side, atr_value, True)
                take_profit = self.get_take_profit_price(entry_price, stop_loss, side)
                return True, orb_high, orb_low, {
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'atr_value': atr_value,
                    'adx_value': adx_value,
                    'vwap_value': vwap_value
                }
            
            return False, orb_high, orb_low, None
            
        except Exception as e:
            print(f"Error in ORB check: {e}")
            return False, None, None, None
    
    def check_ema15_pullback_conditions(self, ltf_data, htf_data, side):
        """Check EMA15 pullback conditions for fallback strategy."""
        try:
            if len(ltf_data) < 15:
                return False, None
            
            # Calculate EMA15
            ema15 = ema(ltf_data, 15).iloc[-1]
            current_price = ltf_data['close'].iloc[-1]
            
            # Check pullback to EMA15
            if side == 'long':
                pullback_ok = current_price <= ema15 * 1.001  # Small tolerance
                engulfing_ok, engulfing_type = engulfing_pattern(ltf_data)
                engulfing_ok = engulfing_ok and engulfing_type == 'bullish'
            else:
                pullback_ok = current_price >= ema15 * 0.999  # Small tolerance
                engulfing_ok, engulfing_type = engulfing_pattern(ltf_data)
                engulfing_ok = engulfing_ok and engulfing_type == 'bearish'
            
            if not pullback_ok or not engulfing_ok:
                return False, None
            
            # Check volume confirmation
            if not volume_confirmation(ltf_data, 20):
                return False, None
            
            # Calculate trade parameters
            entry_price = current_price
            atr_value = atr(ltf_data, 14).iloc[-1]
            stop_loss = self.get_stop_loss_price(entry_price, side, atr_value, False)
            take_profit = self.get_take_profit_price(entry_price, stop_loss, side)
            
            # Check R/R ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= self.min_rr_ok:
                return True, {
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'atr_value': atr_value,
                    'rr_ratio': rr_ratio,
                    'ema15': ema15
                }
            
            return False, None
            
        except Exception as e:
            print(f"Error in EMA15 pullback check: {e}")
            return False, None
    
    def get_trade_signal(self, ltf_data, htf_data, current_time):
        """Get trading signal for current timestamp."""
        try:
            # Check if we can trade today
            if not self.can_trade_today():
                return None
            
            # Check if we're in entry window
            if not is_entry_window(current_time):
                return None
            
            # Get macro bias (but don't restrict trades based on it)
            macro_bias = get_macro_bias(htf_data)
            
            # Try both long and short ORB strategies regardless of macro bias
            for side in ['long', 'short']:
                orb_ok, orb_high, orb_low, trade_params = self.check_orb_conditions(ltf_data, htf_data, side)
                if orb_ok and trade_params:
                    return {
                        'side': side,
                        'strategy': 'orb',
                        'entry_price': trade_params['entry_price'],
                        'stop_loss': trade_params['stop_loss'],
                        'take_profit': trade_params['take_profit'],
                        'orb_high': orb_high,
                        'orb_low': orb_low,
                        'confirmations': {
                            'atr': trade_params['atr_value'],
                            'adx': trade_params['adx_value'],
                            'vwap': trade_params['vwap_value']
                        }
                    }
            
            # Try fallback strategies if ORB didn't work and we're forcing one trade
            if self.force_one_trade and current_time.hour >= 13:
                if self.fallback_mode in ['EMA15_pullback', 'BestOfBoth']:
                    for side in ['long', 'short']:
                        ema_ok, trade_params = self.check_ema15_pullback_conditions(ltf_data, htf_data, side)
                        if ema_ok and trade_params:
                            return {
                                'side': side,
                                'strategy': 'ema15_pullback',
                                'entry_price': trade_params['entry_price'],
                                'stop_loss': trade_params['stop_loss'],
                                'take_profit': trade_params['take_profit'],
                                'rr_ratio': trade_params['rr_ratio'],
                                'ema15': trade_params['ema15']
                            }
            
            return None
            
        except Exception as e:
            print(f"Error getting trade signal: {e}")
            return None
    
    def should_exit_trade(self, trade, current_price, current_time, is_break_even=False):
        """Check if trade should be exited."""
        try:
            # Force close at session end
            if current_time.hour >= self.session_end:
                return True, 'session_end', current_price
            
            # Check stop loss
            if trade['side'] == 'long':
                if current_price <= trade['stop_loss']:
                    return True, 'stop_loss', current_price
                if current_price >= trade['take_profit']:
                    return True, 'take_profit', current_price
                if is_break_even and current_price >= trade['break_even_price']:
                    return True, 'break_even', current_price
            else:  # short
                if current_price >= trade['stop_loss']:
                    return True, 'stop_loss', current_price
                if current_price <= trade['take_profit']:
                    return True, 'take_profit', current_price
                if is_break_even and current_price <= trade['break_even_price']:
                    return True, 'break_even', current_price
            
            return False, None, None
            
        except Exception as e:
            print(f"Error checking exit conditions: {e}")
            return True, 'error', current_price
    
    def calculate_trade_pnl(self, trade, exit_price, exit_reason):
        """Calculate trade PnL."""
        try:
            entry_price = trade['entry_price']
            side = trade['side']
            position_size = trade['position_size']
            
            if side == 'long':
                pnl = (exit_price - entry_price) * position_size
            else:
                pnl = (entry_price - exit_price) * position_size
            
            return pnl
            
        except Exception as e:
            print(f"Error calculating PnL: {e}")
            return 0.0
