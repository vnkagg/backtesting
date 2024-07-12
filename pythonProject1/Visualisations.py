import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import re

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?* ]', '-', filename)
def plot_PNL(profits, dds, max_dd, symbol, expiry, strat):
    plt.figure(figsize=(12,6))
    plt.plot(profits)
    for dd in dds:
        plt.plot(dd[1][0], dd[1][1], marker='v', color='r')
        plt.plot(dd[2][0], dd[2][1], marker='^', color='g')
    plt.plot([max_dd[1][0], max_dd[2][0]], [max_dd[1][1], max_dd[2][1]], marker = '.', linestyle='--', color='black')
    plt.grid(True)
    plt.title("Profit/Loss on every position completion")
    plt.xlabel("xth completed trade")
    plt.ylabel("Profit/Loss")
    # plt.show()
    filename = f"{symbol}_expiry_'{expiry}'_{strat}_PNL.png"
    plt.savefig(sanitize_filename(filename))

def plot_futures_and_ema(df, start_date, end_date, symbol, expiry, strat):
    symbol = df['symbol'].iloc[0]
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    df = df.copy()
    df = df.loc[start:end]
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df['close']/100, color='black')
    plt.plot(df.index, df['short']/100, color='green')
    plt.plot(df.index, df['long']/100, color='red')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.title(f'{symbol} Future Close Prices Over Time')
    plt.xlabel('Time')
    plt.ylabel('Close Price (in Rs)')
    plt.tight_layout()
    # plt.show()
    filename = f"{symbol}_expiry_{expiry}_{strat}_futures_emacrossovers_{start_date}_end_date.png"
    plt.savefig(sanitize_filename(filename))

def plot_options_and_trades(df_options, df_options_in_ram, opt_type, start_date, df_trades, filter_ticks, symbol, expiry, strat):
    symbol = df_options['symbol'].iloc[0]

    start = pd.to_datetime(start_date)
    # end = pd.to_datetime(end_date)

    df_lala_options = df_options_in_ram[opt_type].copy()
    # df_lala_options = df_lala_options.loc[start:end]
    df_lala_options = df_lala_options[df_lala_options.index.date == start.date()]

    df_lala_trades = df_trades[df_trades['Call/Put'] == opt_type]
    # df_lala_trades = df_lala_trades.copy().loc[start:end]
    df_lala_trades = df_lala_trades[df_lala_trades.index.date == start.date()]

    strikes_traded = df_lala_trades['strike_price'].unique()
    num_strikes = len(strikes_traded)
    cols = 1
    rows = (num_strikes // cols) + (num_strikes % cols > 0)

    figure, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows), squeeze=False)
    axes = axes.flatten()

    for i, strike in enumerate(strikes_traded):
        ax = axes[i]
        ax.plot(df_lala_options.index, df_lala_options[strike] / 100)
        trade_lines = df_lala_trades['strike_price'] == strike
        trade_lines = df_lala_trades[trade_lines]

        start_loop = int(trade_lines['Position'].iloc[0] == 0)
        for j in range(start_loop, len(trade_lines) - 1, 2):
            ax.plot([trade_lines.index[j], trade_lines.index[j + 1]],
                    [trade_lines['Price'].iloc[j] / 100, trade_lines['Price'].iloc[j + 1] / 100], color='green',
                    marker="o")
            # ax.plot(trade_lines.index[j], trade_lines['Price'].iloc[j]/100, color = 'green', marker="o")
            # ax.plot(trade_lines.index[j+1], trade_lines['Price'].iloc[j+1]/100, color = 'green', marker="o")

        name = "Put"
        if opt_type:
            name = "Call"
        ax.set_title(f"{name} Options price and trades with strike = {strike}")
        ax.set_xlabel("time stamps")
        ax.set_ylabel("close prices in Rs")
        ax.tick_params(axis='x', rotation=45)
        ax.legend()

        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(FuncFormatter(filter_ticks))

    for j in range(len(strikes_traded), len(axes)):
        figure.delaxes(axes[j])

    plt.tight_layout()
    # plt.show()
    ot = "put"
    if opt_type:
        ot = "call"
    filename = f"{symbol}_expiry_{expiry}_{strat}_options_and_trades_{ot}_{start_date}.png"
    figure.savefig(sanitize_filename(filename))


def filter_ticks(x, pos=None):
    dt = mdates.num2date(x)
    if dt.hour < 9 or (dt.hour == 15 and dt.minute > 29) or dt.hour > 15:
        return ''
    return dt.strftime('%Y-%m-%d %H:%M')

def plot_all_traded_options(df_options, df_ram, start, df_trades, filter_ticks, symbol, expiry, strat):
    plot_options_and_trades(df_options, df_ram, 1, start, df_trades, filter_ticks, symbol, expiry, strat)
    plot_options_and_trades(df_options, df_ram, 0, start, df_trades, filter_ticks, symbol, expiry, strat)