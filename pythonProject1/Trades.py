import pandas as pd
def make_trades(signals, expiry, df_futures, df_options, df, fund_locked):
    available_funds = fund_locked
    trades = []
    # (number, 1/0, 1/0, t, s)
    # (price, call/put, long/short, timestamp, strike)
    ix = 0
    while ix < len(signals):
        first_signal_type = signals[ix][0]
        first_valid_tradable_timestamp = signals[ix][2]
        futures_price = df_futures['close'].loc[first_valid_tradable_timestamp]
        # Finding the ITM-1 or ATM option
        strike = futures_price
        if first_signal_type:
            eligible_candidates = df_options[(df_options.index == first_valid_tradable_timestamp) & (df_options['strike'] <= strike)]
            strike = eligible_candidates["strike"].max()
        else:
            eligible_candidates = df_options[(df_options.index == first_valid_tradable_timestamp) & (df_options['strike'] >= strike)]
            strike = eligible_candidates["strike"].min()
        price = df[first_signal_type][strike].loc[first_valid_tradable_timestamp]
        if price <= available_funds:
            trades.append((price, first_signal_type, 1, first_valid_tradable_timestamp, strike))
            available_funds -= price
            break
        ix += 1
    for i, signal in enumerate(signals[ix+1:]):
        last_trade = trades[len(trades) - 1]
        last_trade_price = last_trade[0]
        last_trade_opt_type = last_trade[1]
        last_trade_position = last_trade[2]
        last_strike = last_trade[4]
        signal_nature = signal[0]
        signal_time_stamp = signal[1]
        valid_tradable_time_stamp = signal[2]
        square_off_price = df[last_trade_opt_type][last_strike].loc[valid_tradable_time_stamp]
        current_strike = df_futures['close'].loc[valid_tradable_time_stamp]
        if first_signal_type:
            eligible_candidates = df_options[(df_options.index == first_valid_tradable_timestamp) & (df_options['strike'] <= current_strike)]
            current_strike = eligible_candidates["strike"].max()
        else:
            eligible_candidates = df_options[(df_options.index == first_valid_tradable_timestamp) & (df_options['strike'] >= currrent_strike)]
            current_strike = eligible_candidates["strike"].min()

        buying_price = df[signal_nature][current_strike].loc[valid_tradable_time_stamp]
        if last_trade_position == 1:
            trades.append((square_off_price, last_trade_opt_type, 1-last_trade_position, valid_tradable_time_stamp, last_strike))
            available_funds += min(square_off_price, last_trade_price)
        if buying_price <= available_funds:
            trades.append((buying_price, signal_nature, 1, valid_tradable_time_stamp, current_strike))
            available_funds -= buying_price

    last_trade = trades[len(trades) - 1]
    last_trade_opt_type = last_trade[1]
    last_trade_strike = last_trade[4]
    expiry = pd.to_datetime(expiry, format = '%d-%m-%Y')
    last_valid_tradable_time_stamp = pd.Timestamp(f"{expiry} 15:29:00")
    last_square_off_price = df[last_trade_opt_type][last_trade_strike].loc[last_valid_tradable_time_stamp]
    trades.append((last_square_off_price, last_trade_opt_type, 0, last_valid_tradable_time_stamp, last_trade_strike))
    return trades