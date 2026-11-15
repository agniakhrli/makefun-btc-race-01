import os
import sys

# Ensure vendor directory is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

# Strategy Parameters (robustified hybrid of 30-min momentum + V-bottom oversold dip)
LOOKBACK_MOMENTUM = 30
MOMENTUM_ENTRY = 0.010   # +1.0% 30-min return
MOMENTUM_EXIT = -0.005   # -0.5% 30-min return
RSI_PERIOD = 14
RSI_OVERSOLD = 32
RSI_OVERBOUGHT = 72
HIGH_LOOKBACK = 120
HIGH_DRAWDOWN_ENTRY = 0.030  # 3.0% below 120-bar high
TRAILING_STOP_PCT = 0.030    # 3.0% trailing stop from peak price since entry
STOP_LOSS_PCT = 0.035        # 3.5% hard stop loss from entry price
MAX_SLIPPAGE_BPS = 500       # 500 bps max slippage tolerance (5%)

class TradingState:
    def __init__(self):
        self.closes = []
        self.highs = []
        self.lows = []
        self.gains = []
        self.losses = []
        self.avg_gain = None
        self.avg_loss = None
        self.entry_price = None
        self.peak_price = None
        self.entry_kind = None
        self.next_entry_kind = None

state_tracker = TradingState()

def compute_rsi(t: TradingState, close: int):
    if len(t.closes) == 0:
        t.closes.append(close)
        return None
    
    prev_close = t.closes[-1]
    change = close - prev_close
    gain = max(0.0, float(change))
    loss = max(0.0, float(-change))
    
    t.closes.append(close)
    t.gains.append(gain)
    t.losses.append(loss)
    
    if len(t.closes) <= RSI_PERIOD:
        return None
    
    if t.avg_gain is None:
        # Initial SMA for first RSI_PERIOD changes
        t.avg_gain = sum(t.gains[-RSI_PERIOD:]) / RSI_PERIOD
        t.avg_loss = sum(t.losses[-RSI_PERIOD:]) / RSI_PERIOD
    else:
        # Wilder's smoothing
        t.avg_gain = (t.avg_gain * (RSI_PERIOD - 1) + gain) / RSI_PERIOD
        t.avg_loss = (t.avg_loss * (RSI_PERIOD - 1) + loss) / RSI_PERIOD
        
    if t.avg_loss == 0:
        return 100.0
    rs = t.avg_gain / t.avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def on_batch(state, batch):
    # Get primary symbol (e.g. CBBTC)
    symbol_list = [s["symbol"] for s in state.hello["symbols"]]
    if not symbol_list:
        return []
    symbol = symbol_list[0]
    
    bar = state.latest.get(symbol)
    if bar is None:
        return []
    
    close = int(bar["c"])
    high = int(bar["h"])
    low = int(bar["l"])
    
    t = state_tracker
    rsi = compute_rsi(t, close)
    t.highs.append(high)
    t.lows.append(low)
    
    # Check current position
    held = state.positions.get(symbol)
    is_long = held is not None and held.qty > 0
    
    if is_long:
        if t.entry_price is None:
            t.entry_price = close
            t.peak_price = close
            t.entry_kind = t.next_entry_kind or 'dip'
        else:
            if close > t.peak_price:
                t.peak_price = close
    else:
        t.entry_price = None
        t.peak_price = None
        t.entry_kind = None
        t.next_entry_kind = None
        
    # Compute 30-bar momentum
    mom_ret = 0.0
    if len(t.closes) > LOOKBACK_MOMENTUM:
        prev_mom_close = t.closes[-1 - LOOKBACK_MOMENTUM]
        if prev_mom_close > 0:
            mom_ret = (close - prev_mom_close) / prev_mom_close
            
    # Compute 120-bar high
    high_120 = close
    if len(t.highs) > 0:
        window_highs = t.highs[-min(len(t.highs), HIGH_LOOKBACK):]
        high_120 = max(window_highs)
        
    # Exit checks if long
    if is_long:
        exit_signal = False
        # Trailing stop or stop loss (applies to both)
        if t.peak_price is not None and close <= t.peak_price * (1.0 - TRAILING_STOP_PCT):
            exit_signal = True
        elif t.entry_price is not None and close <= t.entry_price * (1.0 - STOP_LOSS_PCT):
            exit_signal = True
        else:
            # Entry-type-aware signal exits
            if t.entry_kind == 'momentum':
                if mom_ret < MOMENTUM_EXIT:
                    exit_signal = True
            elif t.entry_kind == 'dip':
                if rsi is not None and rsi > RSI_OVERBOUGHT:
                    exit_signal = True
            
        if exit_signal:
            return [{
                "side": "sell",
                "symbol": symbol,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS
            }]
        return []
        
    # Entry checks if flat
    if not is_long and not state.warming_up:
        buy_signal = False
        kind = 'dip'
        
        # Signal 1: Strong 30-min momentum
        if mom_ret > MOMENTUM_ENTRY:
            buy_signal = True
            kind = 'momentum'
            
        # Signal 2: V-bottom / Oversold dip (close significantly below 120-bar high + low RSI)
        if high_120 > 0 and rsi is not None:
            drawdown_from_high = (high_120 - close) / high_120
            if drawdown_from_high >= HIGH_DRAWDOWN_ENTRY and rsi < RSI_OVERSOLD:
                # If both fire, prefer momentum
                if not buy_signal or mom_ret <= MOMENTUM_ENTRY:
                    buy_signal = True
                    kind = 'momentum' if mom_ret > MOMENTUM_ENTRY else 'dip'
                
        if buy_signal:
            # Check room / weight and cash
            room = state.weight_room(symbol)
            spend = min(state.cash, room)
            min_notional = int(state.hello["fees"]["min_notional_quote_units"])
            if spend >= min_notional:
                t.next_entry_kind = kind
                return [{
                    "side": "buy",
                    "symbol": symbol,
                    "notional_quote_units": spend,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS
                }]
                
    return []

if __name__ == "__main__":
    makefun_bars.run(on_batch)
