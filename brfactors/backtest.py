"""Backtest engine: daily returns of a portfolio rebalanced on given dates."""
import pandas as pd

from .weights import compute_directional_weights, compute_longshort_weights


def backtest_quintiles(df_prices, quintile, trade_dates, market_value):
    # Calculates the return of a stock portfolio over time

    # Creates a dataframe with the percentage price changes of each stock
    prices_pct = df_prices.pct_change(fill_method = None).fillna(0)
    backtest_dates = prices_pct.loc[trade_dates[0]:].index

    daily_return = pd.Series(index = prices_pct.index, name = 'Daily return')
    return_by_stock = pd.DataFrame(index = prices_pct.index, columns = prices_pct.columns)
    daily_weights = pd.DataFrame(index = prices_pct.index, columns = prices_pct.columns)
    
    for dt0 in backtest_dates[:-1]:
        date_location = backtest_dates.get_loc(dt0)
        dt1 = backtest_dates[date_location + 1]

        if dt0 in trade_dates:

            return_by_stock.loc[dt0] = (daily_weights.loc[dt0] * (prices_pct.loc[dt0]))
            daily_return.loc[dt0] = return_by_stock.loc[dt0].sum()
            dtm1 = prices_pct.index[prices_pct.index.get_loc(dt0) - 1]
            daily_weights.loc[dt1] = compute_directional_weights(quintile.loc[dtm1], dtm1, market_value, weight_type = 'equal', stock_returns = prices_pct)

        else:

            return_by_stock.loc[dt0] = (daily_weights.loc[dt0] * (prices_pct.loc[dt0]))
            daily_return.loc[dt0] = return_by_stock.loc[dt0].sum()
            daily_weights.loc[dt1] = (daily_weights.loc[dt0] * (1 + prices_pct.loc[dt0])) / (1 + daily_return.loc[dt0])

    return_by_stock.loc[dt1] = (daily_weights.loc[dt1] * (prices_pct.loc[dt1]))
    daily_return.loc[dt1] = return_by_stock.loc[dt1].sum()

    return daily_return

def backtest_longshort(df_prices, short_sig, long_sig, trade_dates, market_value):
    # Calculates the return of a stock portfolio over time

    # Creates a dataframe with the percentage price changes of each stock
    prices_pct = df_prices.pct_change(fill_method = None).fillna(0)
    backtest_dates = prices_pct.loc[trade_dates[0]:].index

    daily_return = pd.Series(index = prices_pct.index, name = 'Daily return')
    return_by_stock = pd.DataFrame(index = prices_pct.index, columns = prices_pct.columns)
    daily_weights = pd.DataFrame(index = prices_pct.index, columns = prices_pct.columns)
    
    for dt0 in backtest_dates[:-1]:
        date_location = backtest_dates.get_loc(dt0)
        dt1 = backtest_dates[date_location + 1]

        if dt0 in trade_dates:

            return_by_stock.loc[dt0] = (daily_weights.loc[dt0] * (prices_pct.loc[dt0]))
            daily_return.loc[dt0] = return_by_stock.loc[dt0].sum()
            dtm1 = prices_pct.index[prices_pct.index.get_loc(dt0) - 1]
            daily_weights.loc[dt1] = compute_longshort_weights(short_sig.loc[dtm1], long_sig.loc[dtm1], dtm1, market_value, weight_type = 'equal', stock_returns = prices_pct)

        else:

            return_by_stock.loc[dt0] = (daily_weights.loc[dt0] * (prices_pct.loc[dt0]))
            daily_return.loc[dt0] = return_by_stock.loc[dt0].sum()
            daily_weights.loc[dt1] = (daily_weights.loc[dt0] * (1 + prices_pct.loc[dt0])) / (1 + daily_return.loc[dt0])

    return_by_stock.loc[dt1] = (daily_weights.loc[dt1] * (prices_pct.loc[dt1]))
    daily_return.loc[dt1] = return_by_stock.loc[dt1].sum() 

    return daily_return
