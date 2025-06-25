"""
engine/benchmark_v4.py
Benchmark calculation module for the backtest engine (CPS v4 compliant).
Provides functions to calculate benchmark returns for performance comparison.
# CPS v4 compliance verified: 2025-06-08

This module uses the Central Parameter System v4 for configuration.
Parameters are loaded directly from the settings_parameters_v4.ini file.

Required parameters:
- backtest.benchmark_rebalance_freq: Rebalancing frequency for benchmarks
"""

import pandas as pd
import numpy as np
import logging
from v4.settings.settings_CPS_v4 import load_settings

# --- CPS_v4 Integration ---
settings = load_settings()
# --- END CPS_v4 Integration ---

# Configure logger
logger = logging.getLogger(__name__)

# Try to import debug logger
try:
    from utils.debug_logger import get_benchmark_debug_logger
except ImportError:
    # Create a dummy logger if import fails
    def get_benchmark_debug_logger(config=None):
        return None

def calculate_equal_weight_benchmark(asset_returns, config=None):
    """
    Calculate equal-weight benchmark returns with configurable rebalancing frequency.
    
    Args:
        asset_returns (DataFrame): Asset returns data
        config (dict): Configuration dictionary for debug logging
            
    Returns:
        Series: Benchmark returns
    """
    # Get required parameters from CPS_v4
    try:
        backtest_params = settings['backtest']
        rebalance_freq = backtest_params['benchmark_rebalance_freq']
    except (KeyError, TypeError) as e:
        logger.error(f"Missing required parameter 'backtest.benchmark_rebalance_freq' in CPS_v4 settings: {e}")
        raise ValueError(f"Missing required parameter 'backtest.benchmark_rebalance_freq' in CPS_v4 settings") from e
        
    # Get debug logger
    debug_logger = get_benchmark_debug_logger(config)
    # Check if asset_returns is empty
    if asset_returns.empty:
        logger.warning("Empty asset returns provided for benchmark calculation")
        if debug_logger:
            debug_logger.log("Empty asset returns provided for benchmark calculation")
        return pd.Series(index=asset_returns.index)
    
    # Initialize weights
    tickers = asset_returns.columns
    n_assets = len(tickers)
    
    if n_assets == 0:
        logger.warning("No assets found for benchmark calculation")
        if debug_logger:
            debug_logger.log("No assets found for benchmark calculation")
        return pd.Series(0, index=asset_returns.index)
        
    if debug_logger:
        debug_logger.log(f"Found {n_assets} assets for benchmark calculation: {list(tickers)}")
    
    # Equal weight for each asset
    equal_weight = 1.0 / n_assets
    
    # Initialize weights DataFrame with equal weights
    weights = pd.DataFrame(equal_weight, index=asset_returns.index, columns=tickers)
    
    # Get rebalance dates based on frequency
    rebalance_dates = []
    
    if rebalance_freq == 'yearly' or rebalance_freq == 'Y' or rebalance_freq == 'AS':
        # Annual rebalance - first trading day of each year
        years = asset_returns.index.year.unique()
        
        for year in years:
            year_dates = asset_returns.index[asset_returns.index.year == year]
            if len(year_dates) > 0:
                rebalance_dates.append(year_dates[0])  # First trading day of the year
    
    elif rebalance_freq == 'quarterly' or rebalance_freq == 'Q' or rebalance_freq == 'QS':
        # Quarterly rebalance - first trading day of each quarter
        for year in asset_returns.index.year.unique():
            for quarter in [1, 4, 7, 10]:  # First month of each quarter
                quarter_dates = asset_returns.index[
                    (asset_returns.index.year == year) & 
                    (asset_returns.index.month == quarter)
                ]
                if len(quarter_dates) > 0:
                    rebalance_dates.append(quarter_dates[0])
    
    elif rebalance_freq == 'monthly' or rebalance_freq == 'M' or rebalance_freq == 'MS':
        # Monthly rebalance - first trading day of each month
        for year in asset_returns.index.year.unique():
            for month in range(1, 13):
                month_dates = asset_returns.index[
                    (asset_returns.index.year == year) & 
                    (asset_returns.index.month == month)
                ]
                if len(month_dates) > 0:
                    rebalance_dates.append(month_dates[0])
    
    elif rebalance_freq == 'weekly' or rebalance_freq == 'W':
        # Weekly rebalance - first trading day of each week
        # Get isocalendar data as a DataFrame
        isocal = asset_returns.index.isocalendar()
        # Create a unique identifier for each week using year and week
        week_ids = isocal['year'].astype(str) + '-' + isocal['week'].astype(str)
        unique_weeks = week_ids.unique()
        
        for week_id in unique_weeks:
            week_dates = asset_returns.index[week_ids == week_id]
            if len(week_dates) > 0:
                rebalance_dates.append(week_dates[0])
    
    elif rebalance_freq == 'daily' or rebalance_freq == 'D':
        # Daily rebalance - every trading day
        rebalance_dates = asset_returns.index.tolist()
    
    else:
        # Default to annual rebalance if frequency not recognized
        logger.warning(f"Unrecognized rebalance frequency '{rebalance_freq}', defaulting to yearly")
        years = asset_returns.index.year.unique()
        
        for year in years:
            year_dates = asset_returns.index[asset_returns.index.year == year]
            if len(year_dates) > 0:
                rebalance_dates.append(year_dates[0])
    
    # Ensure the first date is always a rebalance date
    if len(asset_returns.index) > 0 and asset_returns.index[0] not in rebalance_dates:
        rebalance_dates.append(asset_returns.index[0])
        rebalance_dates.sort()
    
    logger.info(f"Benchmark rebalance dates: {rebalance_dates}")
    
    if debug_logger:
        debug_logger.log_benchmark_calculation(asset_returns, rebalance_freq, rebalance_dates)
    
    # Calculate benchmark returns
    benchmark_returns = pd.Series(0.0, index=asset_returns.index)
    portfolio_weights = pd.DataFrame(equal_weight, index=[asset_returns.index[0]], columns=tickers)
    
    # First day has no return
    benchmark_returns.iloc[0] = 0.0
    
    if debug_logger:
        debug_logger.log(f"Initial portfolio weights: {equal_weight}")
    
    # For each subsequent day
    for i in range(1, len(asset_returns.index)):
        current_date = asset_returns.index[i]
        prev_date = asset_returns.index[i-1]
        
        # Check if this is a rebalance date
        if current_date in rebalance_dates:
            # Reset to equal weights
            current_weights = pd.Series(equal_weight, index=tickers)
        else:
            # Update weights based on previous day's returns
            prev_weights = portfolio_weights.iloc[-1].copy()
            current_weights = pd.Series(index=tickers)
            
            for ticker in tickers:
                # Update weight based on return
                current_weights[ticker] = prev_weights[ticker] * (1 + asset_returns.loc[prev_date, ticker])
            
            # Normalize weights to sum to 1
            current_weights = current_weights / current_weights.sum()
        
        # Store weights for this date
        portfolio_weights.loc[current_date] = current_weights
        
        # Calculate portfolio return for this day
        day_return = 0.0
        for ticker in tickers:
            day_return += current_weights[ticker] * asset_returns.loc[current_date, ticker]
        
        benchmark_returns.loc[current_date] = day_return
    
    if debug_logger:
        debug_logger.log_benchmark_result(benchmark_returns)
    return benchmark_returns
