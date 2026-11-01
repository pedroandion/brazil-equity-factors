"""Portfolio weighting schemes."""
from datetime import timedelta

import numpy as np
import pandas as pd
import scipy.optimize as sc

path = 'data/'


def standard_deviation(weights, cov_matrix):
    variance = weights.T @ cov_matrix @ weights
    return np.sqrt(variance)

def get_rf(start, end):
    # Returns the risk-free rate for the period
    # The function uses the Selic rate for the period
    rf = pd.read_csv(path + 'benchmarks.csv.gz', index_col='Date', date_format='%Y-%m-%d')
    rf = rf.loc[start:end, 'CDI']
    return rf.mean()

def neg_sharpe(weights, prices_pct, cov_matrix, rf):
    # Calculates the negative Sharpe ratio
    # The function is used to minimize the Sharpe ratio
    returns = np.sum(weights * prices_pct.mean()) * 252
    std = standard_deviation(weights, cov_matrix)
    return -(returns - rf) / std

def min_variance(prices_pct, signal):
    # Calculates the minimum variance portfolio
    # The function minimizes the portfolio variance, subject or not to an expected return
    cov_matrix = prices_pct.cov() * 252
    # Number of stocks
    n = len(signal.replace(0,np.nan).dropna()) / 2 if (signal == -1).any() else len(signal.replace(0,np.nan).dropna())
    # Initial guess of equal weights
    x0 = np.array([1/n] * len(signal))
    # Weight constraint
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    # Weight bounds
    bounds = [(0.01, 2*(1/n)) if v == 1 else (-0.01, -2*(1/n)) for v in signal] if (signal == -1).any() else [(0.01, 2*(1/n)) for v in signal]
    # Minimization of the variance function
    result = sc.minimize(standard_deviation, x0, args = (cov_matrix), constraints = constraints, bounds = bounds)
    return result.x

def max_sharpe(prices_pct, rf, signal):
    # Calculates the maximum Sharpe ratio portfolio
    
    cov_matrix = prices_pct.cov() * 252
    n = len(signal.replace(0,np.nan).dropna()) / 2 if (signal == -1).any() else len(signal.replace(0,np.nan).dropna())
    x0 = np.array([1/n] * len(signal))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = [(0.01, 2*(1/n)) if v == 1 else (-0.01, -2*(1/n)) for v in signal] if (signal == -1).any() else [(0.01, 2*(1/n)) for v in signal]
    
    result = sc.minimize(neg_sharpe, x0, args = (prices_pct, cov_matrix, rf), constraints = constraints, bounds = bounds)
    
    return result.x

def ewma_cov_wgts(returns, decay_factor, ls_sig):
    # Calculates the minimum variance portfolio weights with EWMA
    # The function uses the exponentially weighted average to calculate the covariance matrix
    returns = returns.fillna(0)
    returns_shape = returns.shape[0]

    ls_sig[ls_sig >= 1] = 1

    w = decay_factor ** np.arange(returns_shape)[::-1]
    cov = ((w * returns.T) @ returns) / w.sum()

    vol = np.sqrt(np.diag(cov)) * ls_sig
    inv_vol = 1/vol
    inv_vol[inv_vol == np.inf] = 0

    w = (inv_vol[inv_vol > 0] / inv_vol[inv_vol > 0].sum())
    w = (ls_sig * w).fillna(0)

    return w

def compute_directional_weights(stocks, ref_date, market_value, weight_type, stock_returns):
    # Calculates the weights of the stocks in the portfolio
    if len(stocks) == 0:
        weights = 0
    
    elif weight_type == 'equal':
        # Returns a list with 1/n for each stock
        weights = stocks.div(stocks.sum())

    elif weight_type == 'market_value':
        # Calculates the weights based on each stock's market value
        market_values = market_value.loc[ref_date] * stocks
        weights = market_values / market_values.sum()

    elif weight_type == 'ewmavol':
        # Calculates the weights based on each stock's volatility, giving more weight to less volatile stocks
        returns = stock_returns.loc[ref_date - timedelta(days = 252):ref_date, stocks.index].dropna(how = 'all', axis = 1).add(1)
        weights = ewma_cov_wgts(returns, 1 - (2/(252+1)), stocks)

    elif weight_type == 'minvar':
        # Calculates the weights seeking to minimize the portfolio variance based on historical variance
        returns = stock_returns.loc[ref_date - timedelta(days = 252):ref_date, stocks.index].dropna(how = 'all', axis = 1).add(1)
        weights = min_variance(returns, stocks)

    elif weight_type == 'maxsharpe':
        # Calculates the weights seeking to maximize the portfolio's Sharpe ratio
        returns = stock_returns.loc[ref_date - timedelta(days = 252):ref_date, stocks.index].dropna(how = 'all', axis = 1).add(1)
        rf = get_rf(ref_date - timedelta(days = 252), ref_date)
        weights = max_sharpe(returns, rf, stocks)

    return weights

def compute_longshort_weights(short_sig, long_sig, ref_date, market_value, weight_type, stock_returns):
    # Calculates the weights of the stocks in the portfolio
    
    if weight_type == 'equal':
        # Returns a list with 1/n for each stock
        weights = long_sig.div(long_sig.sum()) - short_sig.div(short_sig.sum())

    elif weight_type == 'market_value':
        # Calculates the weights based on each stock's market value
        long_mv = market_value.loc[ref_date] * long_sig
        short_mv = market_value.loc[ref_date] * short_sig

        weights = long_mv.div(long_mv.sum(axis = 1), axis = 0) - short_mv.div(short_mv.sum(axis = 1), axis = 0)

    elif weight_type == 'ewmavol':
        # Calculates the weights based on each stock's volatility, giving more weight to less volatile stocks
        ls_sig = (long_sig - short_sig).loc[ref_date]
        dt_loc = stock_returns.index.get_loc(ref_date)
        stocks = ls_sig.replace(0,np.nan).dropna().index

        returns = stock_returns.iloc[dt_loc - 252 : dt_loc]
        weights = ewma_cov_wgts(returns, 1 - (2/(252+1)), stocks)

    elif weight_type == 'minvar':
        # Calculates the weights seeking to minimize the portfolio variance based on historical variance
        ls_sig = (long_sig - short_sig).loc[ref_date]
        dt_loc = stock_returns.index.get_loc(ref_date)

        returns = stock_returns.iloc[dt_loc - 252 : dt_loc]
        weights = min_variance(returns)

    elif weight_type == 'maxsharpe':
        # Calculates the weights seeking to maximize the portfolio's Sharpe ratio
        ls_sig = (long_sig - short_sig).loc[ref_date]
        dt_loc = stock_returns.index.get_loc(ref_date)

        returns = stock_returns.iloc[dt_loc - 252 : dt_loc]
        rf = get_rf(ref_date - timedelta(days = 252), ref_date)
        weights = max_sharpe(returns, rf)

    return weights
