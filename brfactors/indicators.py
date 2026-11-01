"""Point-in-time accounting matrices and the indicators calculated from them."""
import numpy as np
import pandas as pd


# Builds a table to apply the point-in-time methodology, the table's index holds all dates
def pit_matrix(financial_col, stock_df, data_index, is_ltm = False):

    # Filters the financial information for the financial_col variable, removes duplicated information and fills empty fields with 0
    financial_info_long = stock_df.get([financial_col, 'statement_date', 'publication_date', 'collection_date']).drop_duplicates(subset = [financial_col, 'statement_date']).reset_index(drop = True)

    # Creates a column to determine which date is used as the reference for the financial information to appear in the matrix
    financial_info_long['startDate'] = financial_info_long.index.map(lambda row: financial_info_long.loc[row, 'publication_date'] if not financial_info_long.duplicated(subset = ['statement_date', 'publication_date'], keep='first').loc[row] else financial_info_long.loc[row, 'collection_date'])

    # Fills the pit_data dataframe, from the publication date onwards, with the financial information of the statement date
    # A publication on a non-trading day takes effect on the next trading day
    pit_data = financial_info_long.pivot_table(columns = 'statement_date', values = financial_col, index = 'startDate')
    pit_data = pit_data.reindex(pit_data.index.union(data_index)).ffill().reindex(data_index)

    if is_ltm:
        # Applies a sideways rolling sum on the dataframe for the LTM fields
        pit_data = pit_data.T.rolling(window = 4, min_periods = 4).sum().T

    return pit_data.dropna(how = 'all')

# Dictionary declaring which columns are turned into matrices and which must be calculated on an LTM basis
check_ltm = {'net_revenue': True, 'gross_profit': True, 'ebit': True, 'ebitda': True, 'net_income': True, 'depreciation_amortization': True, 'fco': True, 
             'total_assets': False, 'current_assets': False, 'nwc': False, 'tangible_assets': False, 'noa': False, 'ppe': False, 'intangibles': False, 
             'equity': False, 'current_liabilities': False, 'non_current_liabilities': False, 'net_debt' : False}

# Calculates the indicators for all days in the prices dataframe
def build_indicators(financial_data: pd.DataFrame, ticker: str, data_index) -> pd.DataFrame:

    # Filters the accounting information dataframe for the desired ticker
    stock_df = financial_data[financial_data['ticker'] == ticker].copy()

    # Creates a dictionary with all matrices for the check_ltm keys
    financial_matrixes = dict(map(lambda item: (item[0], pit_matrix(item[0], stock_df, data_index, item[1])), check_ltm.items()))

    # Magic Formula factors
    financial_matrixes['roc_mf'] = financial_matrixes['ebit'] / (financial_matrixes['nwc'] + financial_matrixes['tangible_assets']).shift(4, axis = 1)
    financial_matrixes['debt_ebit_mf'] =  financial_matrixes['net_debt'] / financial_matrixes['ebit'].map(lambda x: x if x > 0 else np.nan)

    # Profitability factors
    financial_matrixes['roe'] = financial_matrixes['net_income'] / financial_matrixes['equity'].shift(4, axis = 1)
    financial_matrixes['roa'] = financial_matrixes['ebit'] / financial_matrixes['total_assets'].shift(4, axis = 1)
    financial_matrixes['gpoa'] = financial_matrixes['gross_profit'] / financial_matrixes['total_assets'].shift(4, axis = 1)
    financial_matrixes['fcf'] = financial_matrixes['fco'] - financial_matrixes['ppe'].diff(4, axis = 1) + financial_matrixes['depreciation_amortization']
    financial_matrixes['cfoa'] = financial_matrixes['fcf'] / financial_matrixes['total_assets'].shift(4, axis = 1)
    delta_noa = financial_matrixes['noa'].diff(4, axis = 1)
    financial_matrixes['acc'] = -delta_noa / financial_matrixes['total_assets'].shift(4, axis = 1)

    # Growth factors
    financial_matrixes['g_earnings'] = financial_matrixes['net_income'] / financial_matrixes['net_income'].shift(4, axis = 1) - 1
    financial_matrixes['g_revenue'] = financial_matrixes['net_revenue'] / financial_matrixes['net_revenue'].shift(4, axis = 1) - 1
    financial_matrixes['g_ebitda'] = (financial_matrixes['ebit'] + financial_matrixes['depreciation_amortization']) / (financial_matrixes['ebit'] + financial_matrixes['depreciation_amortization']).shift(4, axis = 1) - 1

    financial_matrixes['g_revenue'] = np.where(financial_matrixes['net_revenue'].shift(4, axis = 1) > 0, 1, np.nan) * financial_matrixes['g_revenue']
    financial_matrixes['g_ebitda'] = np.where((financial_matrixes['ebit'] + financial_matrixes['depreciation_amortization']).shift(4, axis = 1) > 0, 1, np.nan) * financial_matrixes['g_ebitda']
    financial_matrixes['g_earnings'] = np.where(financial_matrixes['net_income'].shift(4, axis = 1) > 0, 1, np.nan) * financial_matrixes['g_earnings']

    # Leverage factors
    financial_matrixes['debt_to_equity'] = financial_matrixes['net_debt'] / financial_matrixes['equity']
    financial_matrixes['debt_to_assets'] = financial_matrixes['net_debt'] / financial_matrixes['total_assets']
    financial_matrixes['debt_to_ebitda'] = financial_matrixes['net_debt'] / (financial_matrixes['ebit'] + financial_matrixes['depreciation_amortization']).map(lambda x: x if x > 0 else np.nan)
    financial_matrixes['liab_to_equity'] = (financial_matrixes['current_liabilities'] + financial_matrixes['non_current_liabilities']) / financial_matrixes['equity']

    # Investments
    financial_matrixes['investments'] = -(financial_matrixes['total_assets'] - financial_matrixes['total_assets'].shift(4, axis = 1)) / financial_matrixes['total_assets'].shift(4, axis = 1)

    # Filters the dictionary to keep only the main keys used in the rest of the code
    key_indicators = ['gpoa', 'cfoa', 'roe', 'roa', 'acc', 'roc_mf', 'g_revenue', 'g_ebitda', 'g_earnings', 'debt_to_assets', 'debt_to_ebitda', 'liab_to_equity', 'debt_ebit_mf', 'debt_to_equity',
                         'net_debt', 'equity', 'net_revenue', 'ebit', 'ebitda', 'net_income', 'fcf', 'investments']
    financial_matrixes = {key: value for key, value in financial_matrixes.items() if key in key_indicators}

    # After all calculations, we remove the values that could interfere with building the indicator's point-in-time column
    # To do so, we create a dataframe with the publication dates and the statement date
    statement_dates = stock_df[['statement_date', 'publication_date']].groupby('statement_date').first()

    # This way, a value is considered valid until the next date in publication_date
    for k, v in financial_matrixes.items():
        for i, col in enumerate(v.columns[1:]):
            idx_dt = statement_dates.loc[col, 'publication_date']
            v.loc[idx_dt:,v.columns[i]] = np.nan

        financial_matrixes[k] = v

    # Creates a dictionary with the point-in-time series holding the most recent value for each date in the index
    financial_ts = dict(map(lambda item: (item[0], item[1].dropna(how = 'all').apply(lambda row: row[row.last_valid_index()], axis = 1)), financial_matrixes.items()))
    
    # Checks whether any dataframe is empty and replaces it with a pd.Series
    financial_ts = {k: v if not v.empty else pd.Series(index = data_index) for k,v in financial_ts.items()}

    # Creates a dataframe from the time series dictionary
    financial_ts = pd.DataFrame(financial_ts).dropna(how = 'all')

    # Creates a column to indicate which stock the information refers to
    financial_ts['ticker'] = ticker
    
    return financial_ts
