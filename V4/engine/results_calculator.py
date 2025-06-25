"""
engine/results_calculator.py
Results calculation module for backtest engine (CPS v4 compliant).
Handles performance metrics calculation and results formatting.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_results(portfolio, trade_log, signal_history, price_data=None, weights_history=None):
    """Calculate backtest results and performance metrics.
    
    Args:
        portfolio (Portfolio): Portfolio instance with position history
        trade_log (TradeLog): Trade log containing executed trades
        signal_history (pd.DataFrame): History of signals generated
        price_data (pd.DataFrame, optional): Price data used in backtest
        weights_history (pd.DataFrame, optional): History of target weights
        
    Returns:
        dict: Results including portfolio values, returns, and performance metrics
    """
    logger.debug("Entering calculate_results")
    results = {}
    performance = {}
    
    # Get trade DataFrame from trade log
    trade_df = trade_log.get_trade_df() if trade_log else pd.DataFrame()
    trades = trade_log.trades if trade_log else []
    
    # Get portfolio value history
    portfolio_values = portfolio.get_value_history()
    
    logger.debug("Calculating strategy returns.")
    if len(portfolio_values) > 1:
        strategy_returns = portfolio_values.pct_change().fillna(0)
        total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
        
        # Calculate CAGR
        days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
        if days > 0:
            cagr = ((1 + total_return) ** (365 / days)) - 1
        else:
            cagr = 0
    else:
        strategy_returns = pd.Series()
        total_return = 0
        cagr = 0
    
    # Calculate benchmark returns if price data is available
    benchmark_returns = None
    if price_data is not None and not price_data.empty:
        logger.debug("Calculating benchmark returns.")
        # Equal-weight benchmark
        benchmark_weights = pd.DataFrame(1/len(price_data.columns), 
                                      index=price_data.index,
                                      columns=price_data.columns)
        benchmark_returns = (price_data.pct_change() * benchmark_weights).sum(axis=1)
    
    logger.debug("Calculating volatility.")
    if len(strategy_returns) > 1:
        volatility = strategy_returns.std() * np.sqrt(252)
    else:
        volatility = 0
        
    logger.debug("Calculating Sharpe ratio.")
    if volatility > 0:
        sharpe = (cagr - 0.0) / volatility
    else:
        sharpe = 0
        
    logger.debug("Calculating max drawdown.")
    if len(portfolio_values) > 1:
        rolling_max = portfolio_values.cummax()
        drawdown = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
    else:
        max_drawdown = 0
        
    logger.debug("Calculating turnover.")
    if not trade_df.empty and not portfolio_values.empty:
        total_traded_value = trade_df['amount'].abs().sum()
        avg_portfolio_value = portfolio_values.mean()
        turnover = (total_traded_value / 2) / avg_portfolio_value if avg_portfolio_value > 0 else 0
    else:
        turnover = 0

    logger.debug("Calculating win rate.")
    if len(trades) > 0:
        wins = sum(1 for trade in trades if trade.pnl > 0)
        win_rate = wins / len(trades)
    else:
        win_rate = 0

    logger.debug("Calculating monthly returns.")
    if len(strategy_returns) > 0:
        monthly_returns = strategy_returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
    else:
        monthly_returns = pd.Series()

    logger.debug("Calculating yearly returns.")
    if len(strategy_returns) > 0:
        yearly_returns = strategy_returns.resample('Y').apply(lambda x: (1 + x).prod() - 1)
    else:
        yearly_returns = pd.Series()

    # --- START: Generate Allocation History from Portfolio Snapshots ---
    logger.debug("Generating allocation history from portfolio snapshots.")
    position_history_df = portfolio.get_position_history()
    allocation_history = pd.DataFrame()

    if not position_history_df.empty:
        # Calculate total value for each row (day) by summing all asset values and cash
        daily_total_value = position_history_df.sum(axis=1)
        
        # Divide each position value by the daily total value to get weights
        # Avoid division by zero if total value is zero for a day
        allocation_history = position_history_df.div(daily_total_value, axis=0).fillna(0)

        # Drop the 'Cash' column to only have asset allocations
        if 'Cash' in allocation_history.columns:
            allocation_history = allocation_history.drop(columns=['Cash'])

        logger.info(f"Successfully generated allocation_history with shape: {allocation_history.shape}")
    else:
        logger.warning("Position history was empty. Cannot generate allocation_history.")

    # Populate results dictionary
    results['portfolio_values'] = portfolio_values
    results['strategy_returns'] = strategy_returns
    results['total_return'] = total_return
    results['benchmark_returns'] = benchmark_returns
    results['trade_log'] = trade_df
    performance['cagr'] = cagr
    performance['volatility'] = volatility
    performance['sharpe'] = sharpe
    performance['max_drawdown'] = max_drawdown
    performance['turnover'] = turnover
    performance['win_rate'] = win_rate
    results['monthly_returns'] = monthly_returns
    results['yearly_returns'] = yearly_returns
    results['signal_history'] = signal_history
    results['weights_history'] = weights_history
    results['allocation_history'] = allocation_history
    results['final_value'] = portfolio_values.iloc[-1] if not portfolio_values.empty else portfolio.initial_capital
    results['performance'] = performance

    print("MILESTONE: Final results calculation complete.") # CSC-MILESTONE
    logger.debug("Exiting calculate_results successfully.")
    return results
