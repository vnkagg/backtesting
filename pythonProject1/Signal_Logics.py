def EMA(window_short, window_long, df):
    df.loc[:,'short'] = df['close'].ewm(window_short).mean()
    df.loc[:,'long'] = df['close'].ewm(window_long).mean()
    polarity = df['short'] - df['long']
    polarity = polarity > 0
    signals = []
    position_polarity_positive = polarity.iloc[0]
    for i in range(0, df.shape[0]):
        if(polarity.iloc[i] != position_polarity_positive):
            position_polarity_positive = polarity.iloc[i]
            signals.append((int(position_polarity_positive), df.index[i], df.index[i+1]))
            # bullish -> (1, signal_time, valid_trade_time), bearish -> (0, signal_time, valid_trade_time)
    return signals