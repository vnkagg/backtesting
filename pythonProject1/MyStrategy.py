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
from Metrics import get_metrics_object
from Visualisations import plot_all_traded_options, plot_futures_and_ema, filter_ticks, plot_PNL
from matplotlib import pyplot as plt
from Data_Processing import get_portion_data_with_overlapping_timelines, clean_and_normalize_futures_data, clean_and_normalize_options_data

host = "192.168.2.23"
port = 5432
user = "amt"
dbname = "qdap_test"




# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#
# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#
# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#

symbol = input(">> Enter symbol of the option you wanna trade on. Make sure the futures and options symbol are the same in the database: ")
fund_locked = int(input(">> Enter amount of fund you wanna block to your strategy (1 month) (in Rs): "))
fund_locked *= 100
window_short = 9
window_long = 26
wanna_enter_ema_window = input("Do you wanna provide EMA long (default = 26) and short (default = 9) window sizes? (YES/NO): ")
if wanna_enter_ema_window == "YES" or wanna_enter_ema_window == "yes":
    window_short = int(input(">> Enter short window length: "))
    window_long = int(input(">> Enter long window lenght: "))
moneyness_strike = int(input(">> Index for the moneyness of options to be traded (for every signal) (+ve => ITM, -ve => OTM): "))
wanna_enter = input("Do you wanna provide risk free rate per annum? (YES/NO): ")
risk_free_rate = 12
if wanna_enter == "yes" or wanna_enter == "YES":
    risk_free_rate = float(input(">> Enter risk free rate per annum: "))
transaction_costs = float(input(">> Enter transaction costs in basis points (1% = 100 basis points): "))
slippage = float(input(">> Enter slippage in basis points (1% = basis points): "))
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
# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#
# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#
# ========================+++++++++++++++++++++++++============== USER INPUT ==============++++++++++++++++================================#






print("=======================================================================================================")
print("                          Printing RAW-FETCHED FUTURES DATA")
print("=======================================================================================================")
print("RAW FUTURES DATA FETCHED:")
print("shape of the futures dataframe fetched:", df_futures.shape)
print("columns of the futures dataframe fetched:", df_futures.columns)
# futures_description = df_futures.describe()
# print("futures Dataframe statistics:", x)
print("saved the raw fetched futures data to excel sheet")
df_futures.to_csv(f"Saved_from_program_RAW_FUTURES_DATA_{symbol}")
print('\n\n\n')


print("=======================================================================================================")
print("                          Printing RAW-FETCHED OPTIONS DATA")
print("=======================================================================================================")
print("RAW OPTIONS DATA FETCHED:")
print("shape of the options dataframe fetched:", df_options.shape)
print("columns of the options dataframe fetched:", df_options.columns)
# options_description = df_options.describe()
# print("options Dataframe statistics:", options_description)
print("saved the raw fetched options data to excel sheet")
df_options.to_csv(f"Saved_from_program_RAW_OPTIONS_DATA_{symbol}")
print('\n\n\n')





# =============================================================== DATA PREPOCESSING ================================================================= #
df_futures = clean_and_normalize_futures_data(df_futures)
df_options, df_calls_puts_close, df_calls_puts_open, strikes_calls_puts, timestamps = clean_and_normalize_options_data(df_options)
df_options, df_futures, start_intersection, end_intersection = get_portion_data_with_overlapping_timelines(df_options, df_futures)

print("start_intersection:", start_intersection)
print("end_intersection:", end_intersection)
# =============================================================== DATA PREPOCESSING ================================================================= #



print()
print()
print("=======================SIGNALS====================SIGNALS======================== SIGNALS =======================SIGNALS=========================SIGNALS===============")
# bullish -> (1, signal_time, valid_trade_time), bearish -> (0, signal_time, valid_trade_time)
signals, df_signals = EMA(window_short, window_long, df_futures)
print("number of signals:", len(signals))
print_signals(signals)
df_signals.to_csv(f"signals_generated_from_EMA_{symbol}")
print("signals saved to excel sheet")
print("=======================SIGNALS====================SIGNALS======================== SIGNALS =======================SIGNALS=========================SIGNALS===============")

print()
print()
print("======================== TRADES ==================== TRADES ======================== TRADES ========================== TRADES ============================= TRADES =================")
trades, df_trades = make_trades(signals, moneyness_strike, end_intersection, df_futures, df_calls_puts_open, fund_locked, strikes_calls_puts)

print("number of trades:", len(trades))
print("trades")
print_trades(df_trades, timestamps, df_calls_puts_open)
print("trades saved to excel sheet")
df_trades.to_csv(f"trades_executed_from_signals_fundlocked_{fund_locked}_{symbol}")
print("======================== TRADES ==================== TRADES ======================== TRADES ========================== TRADES ============================= TRADES =================")



metrics = get_metrics_object(df_trades, df_calls_puts_open, df_calls_puts_close, fund_locked, risk_free_rate, transaction_costs, slippage)

print()
print()
print("======================= SUMMARY METRICS =====================")
number_of_trades = metrics.number_of_trades()
sharpe = metrics.sharpe()
net_profit, profits = metrics.PNL()
net_expenditure = metrics.net_expenditure()
net_return = metrics.net_return()
max_drawdown = metrics.max_drawdown()
per_day_pnl = metrics.per_day_pnl()
per_day_pnl.to_csv(f"per_day_pnl_{symbol}")
print("saved per day pnl to excel sheet")

print("stock/index:", symbol)
print("expiry/ end overlapping:", end_intersection)
print("net fund blocked for the strategy (1 month):", f"₹{fund_locked/100}")
print("risk free rate per annum:", risk_free_rate)
print("number of trades:", number_of_trades)
print("sharpe:", sharpe)
print("net profit:", f"₹{net_profit/100}")
print("net expenditure (transaction costs + slippage):", f"₹{net_expenditure/100}")
print("net return:", f"{net_return}%")
print("max drawdown in PNL:", f"₹{abs(max_drawdown)/100}")
print("======================= SUMMARY METRICS =====================")


# print()
# print()
# print("======================== PROFITS ==================== PROFITS ======================== PROFITS ========================== PROFITS ============================= PROFITS =================")
# net_profit, profits = PNL(trades)
# print("length of profits array:", len(profits))
# print("net profit (RS):", net_profit/100)
# print("profits:", profits)
# print("======================== PROFITS ==================== PROFITS ======================== PROFITS ========================== PROFITS ============================= PROFITS =================")
#
# print()
# print()
# print("======================== DRAWDOWNS ==================== DRAWDOWNS ======================== DRAWDOWNS ========================== DRAWDOWNS ============================= DRAWDOWNS =================")
# max_dd, dds = draw_downs(profits)
# print("max drawdown (rs):", max_dd[0]/100)
# print("drawdowns:", dds)
# print("======================== DRAWDOWNS ==================== DRAWDOWNS ======================== DRAWDOWNS ========================== DRAWDOWNS ============================= DRAWDOWNS =================")
#

#
# plot_PNL(profits, dds, max_dd, symbol, end_intersection, "EMA")
# print()
# print()
# futures_check_date_start = input("Enter a date to check futures crossover on (start) (yyyy-mm-dd): ")
#
# futures_check_date_end = input("Enter a date to check futures crossover on (end) (yyyy-mm-dd): ")
#
# plot_futures_and_ema(df_futures, futures_check_date_start, futures_check_date_end, symbol, end_intersection, "EMA")
#
# option_check_date = input("Enter a date to check options trades on (start) (yyyy-mm-dd): ")
#
# plot_all_traded_options(df_options, df_calls_puts_close, option_check_date, df_trades, filter_ticks, symbol, end_intersection, "EMA")




plt.show()
