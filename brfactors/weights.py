"""Portfolio weighting schemes."""


def compute_directional_weights(stocks, ref_date, market_value, weight_type):
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

    return weights

def compute_longshort_weights(short_sig, long_sig, ref_date, market_value, weight_type):
    # Calculates the weights of the stocks in the portfolio
    
    if weight_type == 'equal':
        # Returns a list with 1/n for each stock
        weights = long_sig.div(long_sig.sum()) - short_sig.div(short_sig.sum())

    elif weight_type == 'market_value':
        # Calculates the weights based on each stock's market value
        long_mv = market_value.loc[ref_date] * long_sig
        short_mv = market_value.loc[ref_date] * short_sig

        weights = long_mv.div(long_mv.sum()) - short_mv.div(short_mv.sum())

    return weights
