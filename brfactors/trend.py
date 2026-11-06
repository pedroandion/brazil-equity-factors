"""Trend indicator of a return series, the same formula as the trend index of 05_multi_factor_strategy."""
import numpy as np
import pandas as pd


def trend_signal(returns):
    # Returns the trend indicator, between -1 and 1, of each column of a daily return series or dataframe

    # Cumulative return of the series
    cumulative = returns.add(1).cumprod()

    # Exponential moving averages (EWMA)
    ewm_mean_5d = cumulative.ewm(span = 10).mean()
    ewm_mean_21d = cumulative.ewm(span = 21).mean()
    ewm_mean_63d = cumulative.ewm(span = 63).mean()
    ewm_mean_126d = cumulative.ewm(span = 126).mean()
    ewm_mean_252d = cumulative.ewm(span = 252).mean()

    # Spreads between the moving averages
    spreads = [ewm_mean_5d - ewm_mean_21d,
               ewm_mean_21d - ewm_mean_63d,
               ewm_mean_63d - ewm_mean_126d,
               ewm_mean_126d - ewm_mean_252d]

    # Each spread is normalized by its standard deviation over the last 252 days and passed through the hyperbolic tangent
    signals = [np.tanh(spread / spread.rolling(252).std()) for spread in spreads]

    # Average of the four signals
    return sum(signals) / 4
