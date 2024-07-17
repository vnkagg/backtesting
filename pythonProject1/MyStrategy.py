# IN THIS FILE
# FETCH DATA USING DATA MODULES
# DECIDE A SIGNALING STRATEGY USING A SIGNAL LOGIC DEFINED IN SIGNALS FILE
# DERIVE THE TRADES THAT SHALL BE EXECUTED USING THESE SIGNALS USING THE TRADES MODULES
# OBTAIN THE METRICS OBJECT USING THE METRICS CLASS DEFINED IN THE METRICS MODULE
# PLOT AND VISUALISE THE METRICS, AND THE DATA

from Data import fetch_with_expiry, fetch_with_ith_expiry
from Signal_Logics import EMA, print_signals
from Trades import make_trades, print_trades
import pandas as pd
from Metrics import draw_downs, PNL, get_metrics_object
from Visualisations import plot_all_traded_options, plot_futures_and_ema, filter_ticks, plot_PNL
from matplotlib import pyplot as plt

host = "192.168.2.23"
port = 5432
user = "amt"
dbname = "qdap_test"

symbol = input(">> Enter symbol of the option you wanna trade on. Make sure the futures and options symbol are the same in the database: ")
fund_locked = int(input(">> Enter amount of fund you wanna block to your strategy (1 month) (in Rs): "))
fund_locked *= 100
window_short = 9
window_long = 26
wanna_enter_ema_window = input("Do you wanna provide EMA long (default = 26) and short (default = 9) window sizes? (YES/NO): ")
if wanna_enter_ema_window == "YES" or wanna_enter_ema_window == "yes":
    window_short = int(input(">> Enter short window length: "))
    window_long = int(input(">> Enter long window lenght: "))
moneyness_strike = int(input("Index for the moneyness of options to be traded (for every signal) (+ve => ITM, -ve => OTM): "))
wanna_enter = input("Do you wanna provide risk free rate per annum? (YES/NO): ")
risk_free_rate = 12
if wanna_enter == "yes" or wanna_enter == "YES":
    risk_free_rate = float(input(">> Enter risk free rate per annum: "))
expiry_input_format = input("Do you know a valid expiry that exists in the database? (YES/NO): ")
if expiry_input_format == "YES" or expiry_input_format == "yes":
    date = int(input(">> Expiration Date: "))
    month = int(input(">> Expiration Month: "))
    year = int(input(">> Expiration Year: "))
    DF_FUTURES, DF_OPTIONS = fetch_with_expiry(host, port, user, dbname, symbol, date, month, year)
else:
    x = int(input(">> Enter an index of the array of all the expiries available on I type of futures and options you wanna analyse: "))
    DF_FUTURES, DF_OPTIONS = fetch_with_ith_expiry(host, port, user, dbname, symbol, x)

df_futures = DF_FUTURES.copy()
df_options = DF_OPTIONS.copy()


print("=======================================================================================================")
print("                          Printing RAW-FETCHED FUTURES DATA")
print("=======================================================================================================")
print("RAW FUTURES DATA FETCHED:")
print("shape of the futures dataframe fetched:", df_futures.shape)
print("columns of the futures dataframe fetched:", df_futures.columns)
print("futures Dataframe statistics:", df_futures.describe())
print(df_futures)
print('\n\n\n\n\n\n\n\n')
print("=======================================================================================================")
print("                          Printing RAW-FETCHED OPTIONS DATA")
print("=======================================================================================================")
print("RAW OPTIONS DATA FETCHED:")
print("shape of the options dataframe fetched:", df_options.shape)
print("columns of the options dataframe fetched:", df_options.columns)
print("options Dataframe statistics:", df_options.describe())
print(df_options)
# =============================================================== DATA PREPOCESSING ================================================================= #
# =============================================================== DATA PREPOCESSING ================================================================= #
# =============================================================== DATA PREPOCESSING ================================================================= #


df_futures = df_futures.drop_duplicates(subset='date_timestamp', keep='first')
df_options = df_options.drop_duplicates(subset=['date_timestamp', 'strike'], keep='first')
df_futures.set_index('date_timestamp', inplace=True)
df_options.set_index('date_timestamp', inplace=True)




# NOTE THAT OPTIONS AND FUTURES EXPIRY IN THE QDAP DATABASE ARE NOT FOLLOWING THE SAME FORMAT.
print()
print()
print("======================= OVERLAPPING DETAILS OF EXPIRIES =====================")
expiry_options = pd.Timestamp(df_options['expiry'].iloc[0]).date()
expiry_futures = pd.Timestamp(df_futures['expiry'].iloc[0]).date()
starts_options = pd.Timestamp(df_options.index[0]).date()
starts_futures = pd.Timestamp(df_futures.index[0]).date()

start_intersection = max(starts_options, starts_futures)
end_intersection = min(expiry_options, expiry_futures)
start_intersection = pd.Timestamp.combine(start_intersection, pd.Timestamp('09:15:00').time())
end_intersection = pd.Timestamp.combine(end_intersection, pd.Timestamp('15:29:00').time())

print("starts_options:", starts_options)
print("starts_futures:", starts_futures)
print("expiry_options:", expiry_options)
print("expiry_futures:", expiry_futures)
print("start_intersection:", start_intersection)
print("end_intersection:", end_intersection)


range_futures = (df_futures.index <= end_intersection) & (df_futures.index >= start_intersection)
range_options = (df_options.index <= end_intersection) & (df_options.index >= start_intersection)

df_futures = df_futures[range_futures]
df_options = df_options[range_options]
# df_futures = df_futures[range_futures]
# df_options = df_options[range_options]
print("======================= (END) OVERLAPPING DETAILS OF EXPIRIES (END) =====================")


df_calls = df_options[(df_options['opt_type'] == 'CE')]
df_puts  = df_options[(df_options['opt_type'] == 'PE')]
df_calls_ram = df_calls.pivot(columns='strike', values='close').ffill()
df_puts_ram = df_puts.pivot(columns='strike', values='close').ffill()
market_holidays = [
    (1, 26), (3, 8), (3, 29), (4, 19), (5, 1),
    (8, 15), (10, 2), (10, 24), (11, 12), (12, 25)
]
trading_days = pd.date_range(start=start_intersection, end=end_intersection, freq='B')
trading_days = trading_days[~trading_days.to_series().apply(lambda x: (x.month, x.day) in market_holidays)]
trading_minutes = pd.date_range(start='09:15:00', end='15:29:00', freq='min').time
complete_index = pd.DatetimeIndex([pd.Timestamp.combine(day, time) for day in trading_days for time in trading_minutes])
df_futures = df_futures.reindex(complete_index).ffill()
df_calls_ram = df_calls_ram.reindex(complete_index).ffill()
df_puts_ram = df_puts_ram.reindex(complete_index).ffill()
df = [df_puts_ram, df_calls_ram]


# =============================================================== DATA PREPOCESSING ================================================================= #
# =============================================================== DATA PREPOCESSING ================================================================= #
# =============================================================== DATA PREPOCESSING ================================================================= #




strikes = df_options["strike"].unique()
signals = EMA(window_short, window_long, df_futures)
print()
print()
print("=======================SIGNALS====================SIGNALS======================== SIGNALS =======================SIGNALS=========================SIGNALS===============")
print("number of signals:", len(signals))
# bullish -> (1, signal_time, valid_trade_time), bearish -> (0, signal_time, valid_trade_time)
print_signals(signals)
print("=======================SIGNALS====================SIGNALS======================== SIGNALS =======================SIGNALS=========================SIGNALS===============")

print()
print()
print("======================== TRADES ==================== TRADES ======================== TRADES ========================== TRADES ============================= TRADES =================")
trades = make_trades(signals, moneyness_strike, end_intersection, df_futures, df_options, df, fund_locked, strikes)
df_trades = pd.DataFrame(trades, columns=['Price', 'Call/Put', 'Position', 'date_timestamp', 'strike_price'])
df_trades = df_trades.set_index('date_timestamp')
print("number of trades:", len(trades))
print("trades:", print_trades(df_trades, df_options, df, fund_locked))
print("======================== TRADES ==================== TRADES ======================== TRADES ========================== TRADES ============================= TRADES =================")
print()
print()
print("======================== PROFITS ==================== PROFITS ======================== PROFITS ========================== PROFITS ============================= PROFITS =================")
net_profit, profits = PNL(trades)
print("length of profits array:", len(profits))
print("net profit (RS):", net_profit/100)
print("profits:", profits)
print("======================== PROFITS ==================== PROFITS ======================== PROFITS ========================== PROFITS ============================= PROFITS =================")

print()
print()
print("======================== DRAWDOWNS ==================== DRAWDOWNS ======================== DRAWDOWNS ========================== DRAWDOWNS ============================= DRAWDOWNS =================")
max_dd, dds = draw_downs(profits)
print("max drawdown (rs):", max_dd[0]/100)
print("drawdowns:", dds)
print("======================== DRAWDOWNS ==================== DRAWDOWNS ======================== DRAWDOWNS ========================== DRAWDOWNS ============================= DRAWDOWNS =================")




metrics = get_metrics_object(df_trades, profits, fund_locked, risk_free_rate)

print()
print()
print("======================= SUMMARY METRICS =====================")
number_of_trades = metrics.number_of_trades()
sharpe = metrics.sharpe()
net_profit = metrics.net_profit()
net_expenditure = metrics.net_expenditure()
net_return = metrics.net_return()
max_drawdown = metrics.max_drawdown()

print("stock/index:", symbol)
print("expiry:", expiry_options)
print("net fund blocked for the strategy (1 month):", f"₹{fund_locked/100}")
print("risk free rate per annum:", risk_free_rate)
print("number of trades:", number_of_trades)
print("sharpe:", sharpe)
print("net profit:", f"₹{net_profit/100}")
print("net expenditure (transaction costs + slippage):", f"₹{net_expenditure/100}")
print("net return:", f"{net_return}%")
print("max drawdown in PNL:", f"₹{abs(max_drawdown)/100}")
print("======================= SUMMARY METRICS =====================")


plot_PNL(profits, dds, max_dd, symbol, end_intersection, "EMA")
print()
print()
futures_check_date_start = input("Enter a date to check futures crossover on (start) (yyyy-mm-dd): ")

futures_check_date_end = input("Enter a date to check futures crossover on (end) (yyyy-mm-dd): ")

plot_futures_and_ema(df_futures, futures_check_date_start, futures_check_date_end, symbol, end_intersection, "EMA")

option_check_date = input("Enter a date to check options trades on (start) (yyyy-mm-dd): ")

plot_all_traded_options(df_options, df, option_check_date, df_trades, filter_ticks, symbol, end_intersection, "EMA")




plt.show()
