import pandas as pd


class metrics:
    def __init__(self, trades, profits, fund_locked, risk_free_rate=12):
        self.fund_locked = fund_locked
        self.risk_free_rate = risk_free_rate
        self.trades = trades
        self.profits = pd.Series(profits)

    def number_of_trades(self):
        return self.trades.count().iloc[0]

    def net_profit(self):
        profits = self.profits
        return profits.sum()

    def net_turnover(self):
        prices = self.trades['Price']
        return prices.sum()

    def net_expenditure(self, transaction_costs=11.5, slippage=10):
        # 1% = 100 basis points => total_turnover * 0.01/100 * total_basis_points
        expenses = self.net_turnover() * (0.01 / 100) * (transaction_costs + slippage)
        return expenses

    def net_return(self):
        return 100 * self.net_profit() / self.fund_locked

    def sharpe(self):
        std_profits = self.profits.std()
        std_returns = std_profits / self.fund_locked
        sharpe_ratio = self.net_return() - (self.risk_free_rate / 12)
        sharpe_ratio /= 100
        sharpe_ratio /= std_returns
        return sharpe_ratio

    def max_drawdown(self):
        profits = self.profits
        # cumulative PnL
        profits = [(profits[i] + profits[i-1]) for i in range(1, len(profits))]
        increments = [(profits[i] - profits[i - 1]) for i in range(1, len(profits))]
        dd = 0
        max_dd = 0
        for inc in increments:
            dd += inc
            dd = min(0, dd)
            max_dd = min(dd, max_dd)
        return max_dd

def get_metrics_object(trades, profits, fund_locked, risk_free_rate=12):
    Metrics = metrics(trades, profits, fund_locked, risk_free_rate)
    return Metrics

def PNL(trades):
    net_profit = 0
    profit = 0
    profits = []
    open_position = False
    for i, trade in enumerate(trades):
        price = trade[0]
        position = trade[2]
        cash_flow_nature = 1
        if position: # long -> pos = 1, short -> pos = 0
            cash_flow_nature = -1
        net_profit += cash_flow_nature * price
        profit += cash_flow_nature * price
        if open_position and ~position:
            profits.append(profit)
            profit = 0
        open_position = position
    return net_profit, profits

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