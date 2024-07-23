import pandas as pd
from datetime import time


class metrics:
    def __init__(self, df_trades, df_call_put_open, df_call_put_close, fund_locked, risk_free_rate=12,
                 transaction_costs=11.5, slippage=10):
        self.fund_locked = fund_locked
        self.risk_free_rate = risk_free_rate
        self.df_trades = df_trades
        self.df_call_put_close = df_call_put_close
        self.df_call_put_open = df_call_put_open
        self.transaction_costs = transaction_costs
        self.slippage = slippage

    def get_expense_cost(self, amount):
        transaction_costs = self.transaction_costs
        slippage = self.slippage
        return amount * (transaction_costs + slippage) * 1 / 100 * 1 / 100

    def number_of_trades(self):
        return self.df_trades.count().iloc[0]

    def PNL(self):
        df_trades = self.df_trades
        profit, net_profit, expenses = 0, 0, 0
        profits = []
        open_position = False
        for i, trade in df_trades.iterrows():
            price = trade['Price']
            position = trade['Position']
            cash_flow_nature = 1
            if position:  # long -> pos = 1, short -> pos = 0
                cash_flow_nature = -1
            net_profit += cash_flow_nature * price
            profit += cash_flow_nature * price
            expenses += self.get_expense_cost(price)
            if open_position and not position:
                profits.append(profit - expenses)
                profit, expenses = 0, 0
            open_position = position
        return net_profit, profits

    def net_turnover(self):
        prices = self.df_trades['Price']
        return prices.sum()

    def net_expenditure(self):
        # 1% = 100 basis points => total_turnover * 0.01/100 * total_basis_points
        turnover = self.net_turnover()
        return self.get_expense_cost(turnover)

    def net_return(self):
        net_profit, _ = self.PNL()
        return 100 * net_profit / self.fund_locked

    def sharpe(self):
        profits_per_day = self.per_day_pnl()
        profits_per_day = pd.Series(profits_per_day['pnl'])
        sharpe_ratio = profits_per_day.mean()
        sharpe_ratio -= self.fund_locked * self.risk_free_rate * 1 / 100 * 1 / 365
        sharpe_ratio /= profits_per_day.std()
        return sharpe_ratio

    def max_drawdown(self):
        _, profits = self.PNL()
        increments = [(profits[i] - profits[i - 1]) for i in range(1, len(profits))]
        dd = 0
        max_dd = 0
        for inc in increments:
            dd += inc
            dd = min(0, dd)
            max_dd = min(dd, max_dd)
        return max_dd

    def per_day_pnl(self):
        df_trades = self.df_trades
        df_call_put_close = self.df_call_put_close
        df_call_put_open = self.df_call_put_open
        trades_timestamps = df_trades.index.normalize().unique()
        pnl_per_day = []
        carry_over = False
        expense = 0
        for date in trades_timestamps:
            pnl_this_day = 0
            df_trades_this_day = df_trades[df_trades.index.normalize() == date]
            if carry_over:
                call_put = df_trades_this_day["Call/Put"].iloc[0]
                strike = df_trades_this_day["strike_price"].iloc[0]
                pnl_this_day = df_trades_this_day["Price"].iloc[0] - df_call_put_open[call_put][strike].loc[
                    pd.Timestamp.combine(date, time(9, 15))]
                df_trades_this_day = df_trades_this_day.iloc[1:]
                carry_over = False
            df_prices = df_trades_this_day['Price']
            df_cashflow_nature = 1 * df_trades_this_day['Position'] + (-1) * (1 - df_trades_this_day['Position'])
            df_profits = df_prices * df_cashflow_nature
            df_expenses = self.get_expense_cost(df_prices)
            pnl_this_day += df_profits.sum() - df_expenses.sum()
            if df_trades_this_day['Position'].iloc[-1] == 1:
                call_put = df_trades_this_day['Call/Put'].iloc[-1]
                strike = df_trades_this_day['strike_price'].iloc[-1]
                date_timestamp = pd.Timestamp.combine(date, time(15, 29))
                pnl_this_day -= df_call_put_close[call_put][strike].loc[date_timestamp]
                carry_over = True
            pnl_per_day.append((date, pnl_this_day))
        pnl_per_day = pd.DataFrame(pnl_per_day, columns=['date', 'pnl'])
        pnl_per_day.set_index('date', inplace=True)
        return pnl_per_day

# def per_day_pnl(df_trades, df_call_put_close, df_call_put_open):
#     trades_timestamps = df_trades.index.normalize().unique()
#     pnl_per_day = []
#     carry_over = False
#     carry_date = None
#     for date in trades_timestamps:
#         pnl_this_day = 0
#         df_trades_this_day = df_trades[df_trades.index.normalize() == date]
#         if carry_over:
#             call_put = df_trades_this_day["Call/Put"].iloc[0]
#             strike = df_trades_this_day["strike_price"].iloc[0]
#             pnl_this_day = df_trades_this_day["Price"].iloc[0] - df_call_put_open[call_put][strike].loc[carry_date]
#             df_trades_this_day = df_trades_this_day.iloc[1:]
#             carry_over = False
#         df_prices = df_trades_this_day['Price']
#         df_cashflow_nature = 1 * df_trades_this_day['Position'] + (-1) * (1 - df_trades_this_day['Position'])
#         df_profits = df_prices * df_cashflow_nature
#         pnl_this_day += df_profits.sum()
#         if df_trades_this_day['Position'].iloc[-1] == 1:
#             call_put = df_trades_this_day['Call/Put'].iloc[-1]
#             strike = df_trades_this_day['strike_price'].iloc[-1]
#             date_timestamp = pd.Timestamp.combine(date, time(15, 29))
#             pnl_this_day -= df_call_put_close[call_put][strike].loc[date_timestamp]
#             carry_over = True
#             carry_date = pd.Timestamp.combine(date, time(9, 15))
#         pnl_per_day.append(pnl_this_day)
#     return pnl_per_day
def get_metrics_object(trades, df_calls_puts_open, df_calls_puts_close, fund_locked, risk_free_rate=12, transaction_costs = 11.5, slippage = 10):
    Metrics = metrics(trades, df_calls_puts_open, df_calls_puts_close, fund_locked, risk_free_rate, transaction_costs, slippage)
    return Metrics

# def PNL(trades):
#     net_profit = 0
#     profit = 0
#     profits = []
#     open_position = False
#     for i, trade in enumerate(trades):
#         price = trade[0]
#         position = trade[2]
#         cash_flow_nature = 1
#         if position: # long -> pos = 1, short -> pos = 0
#             cash_flow_nature = -1
#         net_profit += cash_flow_nature * price
#         profit += cash_flow_nature * price
#         if open_position and ~position:
#             profits.append(profit)
#             profit = 0
#         open_position = position
#     return net_profit, profits

def draw_downs(profits):
    dd = 0
    max_dd = 0
    profits = [(profits[i] + profits[i-1]) for i in range(1, len(profits))]
    increments = [(profits[i] - profits[i-1]) for i in range(1, len(profits))]
    dds = []
    dd_falls = 0
    falls_peak_height = 0
    peak = 0
    max_dds_peak_height = 0
    max_dds_peak = 0
    max_dds_peak_temp = 0
    max_dds_peak_height_temp = 0
    max_dds_trough_temp = 0
    max_dds_trough_height_temp = 0
    max_dds_trough_depth = 0
    max_dds_peak_till_now = 0
    max_dds_peak_height_till_now = 0
    max_dds_trough_till_now = 0
    max_dds_trough_depth_till_now = 0
    max_dd_till_now = 0
    max_dds_trough = 0
    began = False
    for i, inc in enumerate(increments):
        # ending of individual drawdowns
        if(inc > 0 and dd_falls != 0):
            dds.append((dd_falls, (peak, falls_peak_height), (i, profits[i])))
            dd_falls = 0
            began = False
        # marking the beginning of the downfall
        if(inc <= 0):
            if began == False:
                peak = i
                falls_peak_height = profits[i]
            began = True
            peak = min(peak, i)
            dd_falls += inc
        # tracking maximum drawdown
        dd += inc
        if(dd > 0):
            dd  = 0
            max_dds_peak_temp = i+1
            max_dds_peak_height_temp = profits[i+1]
        if(max_dd > dd):
            max_dd = dd
            max_dds_trough_temp = i+1
            max_dds_trough_depth_temp = profits[i+1]
        if(max_dd_till_now > max_dd):
            max_dds_peak_till_now = max_dds_peak_temp
            max_dds_peak_height_till_now = max_dds_peak_height_temp
            max_dds_trough_till_now = max_dds_trough_temp
            max_dds_trough_depth_till_now = max_dds_trough_depth_temp
            max_dd_till_now = max_dd

    max_dd = [max_dd, (max_dds_peak_till_now, max_dds_peak_height_till_now), (max_dds_trough_till_now, max_dds_trough_depth_till_now)]
    return max_dd, dds