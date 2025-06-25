"""
engine/data_loader_v4.py
Data loader module (CPS v4 compliant).

This module is responsible for loading historical price data for specified tickers
based on parameters sourced exclusively from the CPS_v4 settings system.
It supports reading data from and saving data to local Excel files.

CPS_v4 Parameters Required (under 'data_params'):
- tickers (list): List of ticker symbols to load.
- start_date (str): Start date for data loading (YYYY-MM-DD).
- end_date (str): End date for data loading (YYYY-MM-DD).
- price_field (str): The price field to use from the raw data (e.g., 'Close', 'Adj Close').
- data_storage_mode (str): Mode for data handling ('Save' to fetch and save, 'Read' to load from file, 'Live' to only fetch).

If any of these parameters are missing from the 'data_params' section in the
CPS_v4 settings, the module will raise a ValueError and halt execution.
"""
import pandas as pd
import logging
import os
import datetime
from typing import Optional
from pathlib import Path
from v4.settings.settings_CPS_v4 import load_settings
from v4.config.paths_v4 import DATA_DIR
from ..utils.date_utils_v4 import (
    standardize_date, standardize_date_range,
    standardize_dataframe_index, filter_dataframe_by_dates
)

# Configure logging first to ensure it's available for all module-level operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_adjusted_close_data(tickers_list: list, start_date_obj: Optional[datetime.date], end_date_obj: Optional[datetime.date], price_field_str: str):
    """
    Load and return adjusted close price data for the given tickers, date range, and price field.

    Args:
        tickers_list: List of ticker symbols.
        start_date_obj: Standardized start date (datetime.date object or None).
        end_date_obj: Standardized end date (datetime.date object or None).
        price_field_str: Price field to extract (e.g., 'Close', 'Adj Close').

    Returns:
        DataFrame: Adjusted close prices for the specified tickers and date range.
    """
    from utils.date_utils import (
        standardize_date, standardize_date_range,
        standardize_dataframe_index, filter_dataframe_by_dates
    )
    # Dates are already standardized if not None
    start_ts = start_date_obj
    end_ts = end_date_obj
    price_data = pd.DataFrame()
    for ticker in tickers_list:
        data = pd.DataFrame()
        try:
            from market_data import data_fetch_stock_data
            data = data_fetch_stock_data(ticker=ticker, period="max", interval="1d")
            if hasattr(data.index, 'tz') and data.index.tz is not None:
                data.index = data.index.tz_localize(None)
            data = standardize_dataframe_index(data)
            data = filter_dataframe_by_dates(data, start_ts, end_ts)
            # pick price field
            for field in [price_field_str, 'Adj Close', 'Close']:
                if field in data.columns:
                    price_data[ticker] = data[field]
                    break
        except Exception as e:
            logger.error(f"Error retrieving data for {ticker}: {e}")
    price_data = price_data.ffill().fillna(0)
    return price_data

def load_ticker_data(tickers_list: list, start_date_str: str, end_date_str: Optional[str], price_field_str: str, current_mode: str):
    """
    Manage ticker data based on passed-in parameters.

    Args:
        tickers_list: List of ticker symbols.
        start_date_str: Start date string (YYYY-MM-DD).
        end_date_str: End date string (YYYY-MM-DD) or None.
        price_field_str: Price field to use.
        current_mode: Data storage mode ('Read', 'Save', 'New').

    Returns:
        DataFrame: Loaded ticker data.
    """
    # Ensure data dir exists
    DATA_DIR.mkdir(exist_ok=True)
    # Use a consistent format for end_date in filename, e.g., 'None' or actual date
    end_date_for_filename = end_date_str if end_date_str is not None else 'None'
    file_name = f"tickerdata_{'_'.join(tickers_list)}_{start_date_str}_{end_date_for_filename}.xlsx"
    xlsx_path = DATA_DIR / file_name
    logger.info(f"[TickerData] Mode={current_mode}, file={xlsx_path}")
    if current_mode.lower() == 'read':
        if not xlsx_path.exists():
            raise FileNotFoundError(f"Ticker data file not found: {xlsx_path}")
        df = pd.read_excel(xlsx_path, index_col=0, parse_dates=True)
    else: # 'Save' or 'New' mode
        # Standardize dates before passing to get_adjusted_close_data
        # standardize_date returns None if input is None or invalid
        start_date_obj = standardize_date(start_date_str)
        end_date_obj = standardize_date(end_date_str) # Can be None

        if start_date_obj is None:
            # This case should ideally be caught earlier in load_data_for_backtest
            # or by settings validation, but as a safeguard:
            err_msg = f"Invalid or missing start_date_str ('{start_date_str}') for get_adjusted_close_data."
            logger.error(err_msg)
            raise ValueError(err_msg)

        df = get_adjusted_close_data(tickers_list, start_date_obj, end_date_obj, price_field_str)
        if current_mode.lower() == 'save':
            df.to_excel(xlsx_path)
            logger.info(f"[TickerData] Saved data to {xlsx_path}")
    return df

def get_returns_data(price_data):
    returns = price_data.pct_change().fillna(0)
    return returns

def load_data_for_backtest(current_settings):
    """
    Load all necessary data for backtesting using the provided settings object.

    Args:
        current_settings (dict): The current, freshly loaded settings object.
    """
    try:
        # Use the passed-in current_settings object
        data_params = current_settings.get('data_params', {})
        # Tickers may be simple list or AlphaList dict
        tickers_raw = data_params.get('tickers', ('SPY', 'QQQ', 'IWM', 'GLD', 'TLT'))
        tickers = tickers_raw['default'] if isinstance(tickers_raw, dict) and 'default' in tickers_raw else tickers_raw
        
        # Get date range from data_params
        start_date_str = data_params.get('start_date')
        end_date_str = data_params.get('end_date')

        if start_date_str is None:
            error_msg = "Required parameter 'start_date' not found in [data_params] section of settings."
            logger.critical(error_msg)
            raise ValueError(error_msg)

        # Validate dates
        valid_start_date = standardize_date(start_date_str)
        if not valid_start_date:
            error_msg = f"Invalid 'start_date' format: '{start_date_str}' in [data_params]. Expected YYYY-MM-DD or YYYYMMDD."
            logger.critical(error_msg)
            raise ValueError(error_msg)

        if end_date_str:
            valid_end_date = standardize_date(end_date_str)
            if not valid_end_date:
                error_msg = f"Invalid 'end_date' format: '{end_date_str}' in [data_params]. Expected YYYY-MM-DD or YYYYMMDD."
                logger.critical(error_msg)
                raise ValueError(error_msg)

        price_field = data_params.get('price_field', 'Close')
        local_price_field = data_params.get('price_field', 'Close')
        local_mode = data_params.get('data_storage_mode', 'Read')

        # Determine tickers from current_settings
        local_tickers_raw = data_params.get('tickers', ('SPY', 'QQQ', 'IWM', 'GLD', 'TLT'))
        if isinstance(local_tickers_raw, dict) and 'default' in local_tickers_raw:
            local_tickers = local_tickers_raw['default']
        else:
            local_tickers = local_tickers_raw

        logger.debug(
            f"Data params from current_settings - Tickers: {local_tickers}, Dates: {start_date_str}-{end_date_str}, "
            f"Field: {local_price_field}, Mode: {local_mode}"
        )
    except KeyError as e:
        logger.error(f"Missing required parameter in CPS_v4 settings [data_params]: {e}")
        raise ValueError(f"Missing required parameter in [data_params] of CPS_v4 settings: {e}") from e

    # Fetch price data using current parameters
    raw_df = load_ticker_data(local_tickers, start_date_str, end_date_str, local_price_field, local_mode)

    # Filter price data by the specified date range
    df = filter_dataframe_by_dates(raw_df, start_date=start_date_str, end_date=end_date_str)

    if df.empty:
        warn_msg = (
            f"Price data is empty after filtering for dates: {start_date_str} to {end_date_str}. "
            f"Check data availability and date settings. Raw data had {len(raw_df)} rows."
        )
        logger.warning(warn_msg)

    # Build risk-free rate series aligned with the (potentially filtered) df index
    rf_value = current_settings.get('performance', {}).get('risk_free_rate', 0.0)
    rf = pd.Series(rf_value, index=df.index)

    return {
        'price_data': df,
        'returns_data': get_returns_data(df),
        'risk_free_rate': rf
    }
