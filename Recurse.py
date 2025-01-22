import os
import sys
import shutil
import numpy as np
import pandas as pd

backtesting_path = r'C:\Users\vinayak\Desktop\Backtesting'
if backtesting_path not in sys.path:
    sys.path.append(backtesting_path)

from Modules.Helpers import Metrics
from Modules.ParallelThreads import ThreadsForScript
from Modules.enums import Period
from Modules import Plot


def make_metrics_df(obj, period):
    return {
        'Max Margins': obj.get_fund_blocked(period, True),
        'Returns': obj.returns(period),
        'Sharpe' : obj.sharpe(period),
        'Sortino' : obj.sortino(period),
        'Information Ratio' : obj.information_ratio(period),
        'Max Drawdown' : obj.max_drawdowns(period),
        'Interval for Max Drawdown' : obj.drawdown_intervals(period),
        'Profits' : obj.profits(period),
        'Win Ratio (W-L)' : obj.win_percentage(period)
    }

def g(key, x):
    x = x.rename_axis("Period").reset_index(name=key)
    x['Year'] = pd.to_datetime(x['Period'], format='%Y %B').dt.year
    x['Month'] = pd.to_datetime(x['Period'], format='%Y %B').dt.month
    x = x.pivot(index='Month', columns='Year', values=key)
    x.index = pd.to_datetime(x.index, format='%m')
    x = x.sort_index()
    x.index = x.index.strftime('%B')
    return x
    
def main():
    obj = Metrics()
    pwd = os.getcwd()
    pwd = os.path.dirname(os.path.abspath(__file__))
    print("pwd:", pwd)
    src_path = os.path.join(pwd, "Recurse.py")
    startdate_foldername_mapping = obj.consolidate_margin_summary_pnl_file(pwd)
    if len(set(obj.daily_profit.index.year)) > 1:
        metrics_complete = make_metrics_df(obj, Period.Complete)
        metrics_annual = make_metrics_df(obj, Period.Annual)
        metrics_monthly = make_metrics_df(obj, Period.Monthly)
        excel_file = {
            'All Data Accumulated': pd.DataFrame([metrics_complete]).T.rename(columns={0: "All Time"}),
            'Year Wise Data': pd.DataFrame(metrics_annual).T
        }
        for key, value in metrics_monthly.items():
            excel_file[key] = g(key, value)
    elif len(set(obj.daily_profit.index.month)) > 1:
        metrics_complete = make_metrics_df(obj, Period.Complete)
        metrics_monthly = make_metrics_df(obj, Period.Monthly)
        excel_file = {
            'All Data Accumulated (This Year)': pd.DataFrame([metrics_complete]).T.rename(columns={0: "This Year"}),
            'Month wise': pd.DataFrame(metrics_monthly)
        }
    elif len(set(obj.daily_profit.index.day)) > 1:
        metrics_complete = make_metrics_df(obj, Period.Complete)
        excel_file = {
            'All Data Accumulated (This Month)': pd.DataFrame([metrics_complete]).T.rename(columns={0: "This Month"}),
        }
    else:
        return
    path_for_metrics = os.path.join(pwd, 'Metrics.csv')
    Plot.save_df_to_excel(excel_file, path_for_metrics)

    times = pd.to_datetime(list(startdate_foldername_mapping.keys()))
    check_trades_exist = len(times) > 0
    
    if not check_trades_exist:
        return

    files_to_recurse = []
    for start_date, folder_names in startdate_foldername_mapping.items():
        start_date = pd.to_datetime(start_date)
        for folder_name in folder_names:
            folder_path_old = os.path.join(pwd, folder_name)
            if len(set(times.year)) > 1:
                parent_folder_new = os.path.join(pwd, str(start_date.year))
            elif len(set(times.month)) > 1:
                parent_folder_new = os.path.join(pwd, str(start_date.strftime('%B')))
            else:
                return
            folder_path_new = os.path.join(parent_folder_new, folder_name)
            if not os.path.exists(parent_folder_new):
                os.mkdir(parent_folder_new)
                dest_path = os.path.join(parent_folder_new, "Recurse.py")
                files_to_recurse.append(dest_path)
                shutil.copy(src_path, dest_path)
            shutil.move(folder_path_old, folder_path_new)
    for file in files_to_recurse:
        runner = ThreadsForScript(file, 1)
        runner.run_script()


if __name__ == "__main__":
    main()
