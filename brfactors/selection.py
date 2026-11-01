"""Stock selection from a signal: quantiles, percentiles and top/bottom N."""
import numpy as np
import pandas as pd


def get_quintiles(lower, upper, value_df):
    # Returns the investable companies based on the percentile given in the parameters

    # Calculates the lower and upper bounds of a quintile
    bottom = value_df.quantile(lower, axis = 1)
    top = value_df.quantile(upper, axis = 1)

    if lower == 0:
        value_df = value_df.apply(lambda col: np.where((col >= bottom) & (col <= top), 1, 0))
    else:
        value_df = value_df.apply(lambda col: np.where((col > bottom) & (col <= top), 1, 0))

    return value_df

def get_longshort_decile(percentile: float, value_df: pd.DataFrame, use_filter: bool = False, filter_signal: list = None, filter_percentile: list = None):
    # Returns the investable companies based on the percentile given in the parameters

    if use_filter:

        if filter_signal is None or filter_percentile is None:

            raise ValueError("filter_signal and filter_percentile must be provided when use_filter is True.")
        
        else:

            sup_sig = value_df.copy()
            inf_sig = value_df.copy()

            for signal, perc in zip(filter_signal, filter_percentile):
                
                upper_cut = signal.quantile(1 - perc, axis = 1)
                lower_cut = signal.quantile(perc, axis = 1)

                sup = signal.apply(lambda col: np.where(col >= lower_cut, 1, np.nan))
                inf = signal.apply(lambda col: np.where(col < upper_cut, 1, np.nan))

                sup_sig = sup_sig * sup
                inf_sig = inf_sig * inf

        top = sup_sig.quantile(1 - percentile, axis = 1)
        bottom = inf_sig.quantile(percentile, axis = 1)

        long = sup_sig.apply(lambda col: np.where(col >= top, 1, 0))
        short = inf_sig.apply(lambda col: np.where(col <= bottom, 1, 0))

        return short, long

    else:
        # Calculates the lower and upper bounds of a quintile
        bottom = value_df.quantile(percentile, axis = 1)
        top = value_df.quantile(1 - percentile, axis = 1)

        short = value_df.apply(lambda col: np.where(col <= bottom, 1, 0))
        long = value_df.apply(lambda col: np.where(col >= top, 1, 0))
        

        return short, long
    
def get_longshort_amount(amount: int, value_df: pd.DataFrame, use_filter: bool = False, filter_signal: list = None, filter_percentile: list = None):
    # Returns the investable companies based on the percentile given in the parameters

    if use_filter:

        if filter_signal is None or filter_percentile is None:

            raise ValueError("filter_signal and filter_percentile must be provided when use_filter is True.")
        
        else:

            sup_sig = value_df.copy()
            inf_sig = value_df.copy()

            for signal, perc in zip(filter_signal, filter_percentile):
                
                upper_cut = signal.quantile(1 - perc, axis = 1)
                lower_cut = signal.quantile(perc, axis = 1)

                sup = signal.apply(lambda col: np.where(col >= lower_cut, 1, np.nan))
                inf = signal.apply(lambda col: np.where(col < upper_cut, 1, np.nan))

                sup_sig = sup_sig * sup
                inf_sig = inf_sig * inf

        top = sup_sig.rank(ascending = False, axis = 1)
        bottom = inf_sig.rank(ascending = True, axis = 1)

        long = pd.DataFrame(np.where(top <= amount, 1, 0), columns = top.columns, index = top.index)
        short = pd.DataFrame(np.where(bottom <= amount, 1, 0), columns = bottom.columns, index = bottom.index)

        return short, long

    else:
        top = value_df.rank(ascending = False, axis = 1)
        bottom = value_df.rank(ascending = True, axis = 1)

        long = pd.DataFrame(np.where(top <= amount, 1, 0), columns = top.columns, index = top.index)
        short = pd.DataFrame(np.where(bottom <= amount, 1, 0), columns = bottom.columns, index = bottom.index)
        

        return short, long
