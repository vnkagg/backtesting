# format of trades
# (number, 1/0, 1/0, t, s)
# (price, call/put, long/short, timestamp, strike)
import pandas as pd
def choose_strike_of_moneyness(opt_type, index_strike, futures_price, df_target):
    try:
        # decision logic
        call_put = (1)*(opt_type) + (-1)*(1-opt_type)
        moneyness = (1)*(index_strike >= 0) + (-1)*(index_strike < 0)
        decision = call_put * moneyness
        # ITM calls (+1 * +1) and OTM puts (-1 * -1) will have a strike < futures_price
        # OTM calls (-1 * +1) and ITM puts (+1 * -1) will have a strike > futures_price
        eligible_candidates = [df_target[df_target['strike'] >= futures_price], df_target[df_target['strike'] <= futures_price]]
        eligible_candidates = eligible_candidates[int(decision == 1)]
        strike = eligible_candidates["strike"].iloc[max(0, abs(index_strike)-1)]
        return strike
    except:
        # print(eligible_candidates)
        moneyness = "ATM" if index_strike == 0 else ["OTM", "ITM"][index_strike >= 0]
        print(f"SIGNAL WASTED: Couln't find an {moneyness}-{abs(index_strike)} option trade in the database at {df_target.index[0]}.")
        print(f">>> Futures price: {futures_price}.")
        print(f">>> Eligible strikes traded on/or before the current timestamp: {[i for i in eligible_candidates["strike"]]}")
        print()
        return -1


# format of trades
# (number, 1/0, 1/0, t, s)
# (price, call/put, long/short, timestamp, strike)
def make_trades(signals, moneyness_strike, expiry, df_futures, df_options, df, fund_locked, strikes):
    available_funds = fund_locked
    trades = []
    ix = 0
    df_target = None

    # brute forcing the first trade (fund locking)
    while ix < len(signals):
        # first signal details
        first_signal_type = signals[ix][0]
        first_valid_tradable_timestamp = signals[ix][2]
        futures_price = df_futures['close'].loc[first_valid_tradable_timestamp]

        # calculation and logic
        opt_type = ["PE", "CE"][first_signal_type]
        df_target = df_options[df_options["opt_type"] == opt_type]
        df_target = df_target[df_target.index == first_valid_tradable_timestamp]
        strike = choose_strike_of_moneyness(first_signal_type, moneyness_strike, futures_price, df_target)
        if strike == -1:
            ix += 1
            continue
        price = df[first_signal_type][strike].loc[first_valid_tradable_timestamp]
        # validity of positions (fund locking)
        if price <= available_funds:
            trades.append((price, first_signal_type, 1, first_valid_tradable_timestamp, strike))
            available_funds -= price
            break
        ix += 1

    # executing trades as per the signals generated
    for i, signal in enumerate(signals[ix + 1:]):
        # last trade details
        last_trade = trades[len(trades) - 1]
        last_trade_price = last_trade[0]
        last_trade_opt_type = last_trade[1]
        last_trade_position = last_trade[2]
        last_strike = last_trade[4]

        # current signal details
        signal_nature = signal[0]
        signal_time_stamp = signal[1]
        valid_tradable_time_stamp = signal[2]

        # calculation and logic
        square_off_price = df[last_trade_opt_type][last_strike].loc[valid_tradable_time_stamp]
        futures_price = df_futures['close'].loc[valid_tradable_time_stamp]
        opt_type = ["PE", "CE"][signal_nature]  # df of calls/puts (rows-> timestamps, cols-> strikes, values-> close)
        df_target = df_options[df_options["opt_type"] == opt_type]
        df_target = df_target[df_target.index == first_valid_tradable_timestamp]
        current_strike = choose_strike_of_moneyness(first_signal_type, moneyness_strike, futures_price, df_target)
        if current_strike == -1:
            continue
        buying_price = df[signal_nature][current_strike].loc[valid_tradable_time_stamp]

        # validity of positions (fund locking)
        if last_trade_position == 1:
            trades.append((square_off_price, last_trade_opt_type, 1 - last_trade_position, valid_tradable_time_stamp,
                           last_strike))
            available_funds += min(square_off_price, last_trade_price)
        if buying_price <= available_funds:
            trades.append((buying_price, signal_nature, 1, valid_tradable_time_stamp, current_strike))
            available_funds -= buying_price

    # manually squaring off the last trade at the last tradable minute
    last_trade = trades[len(trades) - 1]
    last_trade_opt_type = last_trade[1]
    last_trade_strike = last_trade[4]
    expiry = pd.to_datetime(expiry, format='%d-%m-%Y')
    last_valid_tradable_time_stamp = pd.Timestamp(f"{expiry} 15:29:00")
    last_square_off_price = df[last_trade_opt_type][last_trade_strike].loc[last_valid_tradable_time_stamp]
    trades.append((last_square_off_price, last_trade_opt_type, 0, last_valid_tradable_time_stamp, last_trade_strike))
    return trades


def stats_per_trade(open, close, df_options, df_ram, fund_blocked, risk_free=12):
    opt_type = open['Call/Put']
    strike = open['strike_price']

    open_time = open.name
    close_time = close.name
    time_stamps = df_options.loc[open_time:close_time].index
    holding_period = (close_time - open_time).total_seconds() / 60

    open_price = open['Price']
    close_price = close['Price']
    profit = close_price - open_price

    dd = 0
    max_dd = 0
    last_max_price = close_price
    closes = df_ram[int(opt_type)][int(strike)]
    variations = []
    for timestamp in time_stamps:
        last_max_price = max(last_max_price, closes[timestamp])
        dd = min(dd, closes[timestamp] - last_max_price)
        max_dd = min(dd, max_dd)
        variations.append(closes[timestamp] - close_price)

    variations = pd.Series(variations)
    std_granularity = variations.std()
    if std_granularity == 0:
        std_granularity = 1
    sharpe = profit - risk_free * 1 / 365 * 1 / 24 * 1 / 60 * 1 / 100 * fund_blocked * holding_period
    sharpe /= std_granularity
    return max_dd, profit, holding_period, std_granularity, sharpe
def print_trades(df_trades, df_options, df_ram, fund_blocked):
    open_position = None
    open_details = []
    close_details = []
    sharpes = []
    for i, row in df_trades.iterrows():
        pos = "Sell"
        open_position = False
        close_details = row
        if row["Position"]:
            pos = "Buy "
            open_position = True
            open_details = row
        type = "Put"
        if row["Call/Put"]:
            type = "Call"
        strike = row["strike_price"]
        price = row["Price"]
        print(f"at time: {i} || {pos} {type} option of strike = {strike} for a price of {price}")
        if not open_position:
            print("==> TRADE STATS")
            max_dd, profit, holding_period, std, sharpe = stats_per_trade(open_details, close_details, df_options, df_ram, fund_blocked)
            sharpes.append(sharpe)
            print(">>>> maximum drawdown:", max_dd)
            print(">>>> profit:", profit)
            print(">>>> holding period:", holding_period, "minutes")
            print(">>>> standard deviation:", std)
            print(">>>> sharpe:", sharpe)
            print("=========================================================================================================")
    sharpes = pd.Series(sharpes)
    print(sharpes.mean())

