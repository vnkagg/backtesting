import pandas as pd
import numpy as np
from datetime import time

def get_market_holidays():
    return [
        (1, 26), # republic day (fixed)
        (3, 8), # international womens day
        (3, 29), # holi (floating)
        (4, 19), # Good Friday (floating)
        (5, 1), # International workers day
        (7, 17), # Muharram (floating)
        (8, 15), # Independence day (fixed)
        (10, 2), # Gandhi Jayanti (fixed)
        (10, 24), # Dusshera (floating)
        (11, 12), # Diwali (floating)
        (12, 25) # Christmas (fixed)
    ]

def get_continuous_date_timeframe(start, end):
    market_holidays = get_market_holidays()
    trading_days = pd.date_range(start=start, end=end, freq='B')
    trading_days = trading_days[~trading_days.to_series().apply(lambda x: (x.month, x.day) in market_holidays)]

    # Generate a complete range of trading minutes for each trading day
    trading_minutes = pd.date_range(start='09:15:00', end='15:29:00', freq='min').time

    # Create a complete index of trading timestamps
    complete_index = pd.DatetimeIndex(
        [pd.Timestamp.combine(day, time) for day in trading_days for time in trading_minutes])

    return complete_index

def get_portion_data_with_overlapping_timelines(df1, df2):
    df1 = df1.copy()
    df2 = df2.copy()
    df1.index = pd.to_datetime(df1.index)
    df2.index = pd.to_datetime(df2.index)

    expiry_1 = pd.Timestamp(df1['expiry'].iloc[0]).date()
    expiry_2 = pd.Timestamp(df2['expiry'].iloc[0]).date()
    starts_1 = pd.Timestamp(df1.index[0]).date()
    starts_2 = pd.Timestamp(df2.index[0]).date()

    start_intersection = max(starts_1, starts_2)
    end_intersection = min(expiry_1, expiry_2)
    start_intersection = pd.Timestamp.combine(start_intersection, pd.Timestamp('09:15:00').time())
    end_intersection = pd.Timestamp.combine(end_intersection, pd.Timestamp('15:29:00').time())

    range_booleans1 = (df1.index <= end_intersection) & (df1.index >= start_intersection)
    range_booleans2 = (df2.index <= end_intersection) & (df2.index >= start_intersection)

    df1 = df1[range_booleans1]
    df2 = df2[range_booleans2]

    return df1, df2, start_intersection, end_intersection

def clean_and_normalize_options_data(df_options):
    df_options = df_options.copy()
    timestamps = df_options['date_timestamp'].unique()
    df_options = df_options.drop_duplicates(subset=['date_timestamp', 'strike', 'opt_type'], keep='first')
    starts_options = pd.Timestamp(timestamps[0]).date()
    expiry_options = pd.Timestamp(df_options['expiry'].iloc[0]).date()

    df_calls = df_options[(df_options['opt_type'] == 'CE')]
    df_puts = df_options[(df_options['opt_type'] == 'PE')]
    df_calls.set_index('date_timestamp', inplace=True)
    df_puts.set_index('date_timestamp', inplace=True)
    df_calls_close = df_calls.pivot(columns='strike', values='close').ffill()
    df_puts_close = df_puts.pivot(columns='strike', values='close').ffill()
    df_calls_open = df_calls.pivot(columns='strike', values='open').ffill()
    df_puts_open = df_puts.pivot(columns='strike', values='open').ffill()

    complete_index = get_continuous_date_timeframe(starts_options, expiry_options)

    df_calls_open = df_calls_open.reindex(complete_index).ffill()
    df_puts_open = df_puts_open.reindex(complete_index).ffill()
    df_calls_close = df_calls_close.reindex(complete_index).ffill()
    df_puts_close = df_puts_close.reindex(complete_index).ffill()

    strikes_calls = np.array(df_calls_close.columns, dtype=int)
    strikes_puts = np.array(df_puts_close.columns, dtype=int)

    return df_options, [df_puts_close, df_calls_close], [df_puts_open, df_calls_open], [strikes_puts, strikes_calls]

def clean_and_normalize_futures_data(df_futures):
    df_futures = df_futures.copy()
    df_futures = df_futures.drop_duplicates(subset='date_timestamp', keep='first')
    df_futures = df_futures.set_index('date_timestamp')
    start_futures = pd.Timestamp(df_futures.index[0]).date()
    expiry_futures = pd.Timestamp(df_futures['expiry'].iloc[0]).date()

    complete_index = get_continuous_date_timeframe(start_futures, expiry_futures)

    df_futures = df_futures.reindex(complete_index).ffill()
    timestamps = df_futures.index.unique()
    timestamps = pd.Series(timestamps)

    return df_futures, timestamps