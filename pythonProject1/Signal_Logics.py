import pandas as pd
def EMA(window_short, window_long, df):
    df['short'] = df['close'].ewm(span=window_short).mean()
    df['long'] = df['close'].ewm(span=window_long).mean()
    polarity = df['short'] - df['long']
    polarity = polarity > 0
    signals = []
    position_polarity_positive = polarity.iloc[window_long]
    for i in range(window_long, df.shape[0]):
        if(polarity.iloc[i] != position_polarity_positive):
            position_polarity_positive = polarity.iloc[i]
            signals.append((int(position_polarity_positive), df.index[i], df.index[i+1]))
            # bullish -> (1, signal_time, valid_trade_time), bearish -> (0, signal_time, valid_trade_time)
    df_signals = pd.DataFrame(signals, columns=['Signal Type', "Signal Time", "Valid Tradable Time"])
    df_signals.set_index('Signal Time', inplace=True)
    return signals, df_signals

def print_signals(signals):
    for signal in signals:
        print(f"{["BULLISH", "BEARISH"][signal[0]]} Signal at {signal[1]}. Valid tradable timestamp for this signal: {signal[2]}")