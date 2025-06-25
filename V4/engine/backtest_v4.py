"""
engine/backtest_v4.py
Main backtest engine module (CPS v4 compliant).
Ties together all components for running backtests.
# CPS v4 compliance verified: 2025-06-08

This module uses the Central Parameter System v4 for configuration.
Parameters are loaded directly from the settings_parameters_v4.ini file.

Required parameters:
- backtest.initial_capital: Initial capital for the backtest
- backtest.benchmark_rebalance_freq: Rebalancing frequency for benchmarks
- backtest.commission_rate: Commission rate as percentage
- backtest.slippage_rate: Slippage rate as percentage
"""

import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
import logging
import os
import sys
from pathlib import Path

# Set pandas options to avoid warnings
pd.set_option('future.no_silent_downcasting', True)

# Import local modules
from v4.engine.portfolio_v4 import Portfolio
from v4.engine.orders_v4 import Order, Trade, TradeLog
from v4.engine.execution_v4 import (
    ExecutionEngine,
    PercentCommissionModel,
    PercentSlippageModel,
)
from v4.engine.allocation_v4 import calculate_rebalance_orders
from v4.engine.signal_generator_v4 import EMASignalGenerator
from v4.models.ema_allocation_model_v4 import calculate_ema_metrics
from v4.models.ema_signal_bridge import run_ema_model_with_tracing
from v4.utils.tracing_utils import setup_trace_directory, reset_trace_directory_for_run  # trace call removed
from v4.engine.results_calculator import calculate_results

# Configure logging
lvl = os.getenv("BACKTEST_LOG_LEVEL", "DEBUG").upper()
numeric = getattr(logging, lvl, logging.INFO)
logging.basicConfig(
    level=numeric,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- CPS_v4 Integration ---
from v4.settings.settings_CPS_v4 import load_settings
settings = load_settings()
try:
    backtest_params = settings['backtest']
    initial_capital = backtest_params['initial_capital']
    benchmark_rebalance_freq = backtest_params['benchmark_rebalance_freq']
    commission_rate = backtest_params['commission_rate']
    slippage_rate = backtest_params['slippage_rate']
except KeyError as e:
    logger.error(f"Missing required parameter in CPS_v4 settings: {e}")
    raise ValueError(f"Missing required parameter in CPS_v4 settings") from e
# --- END CPS_v4 Integration ---

class BacktestEngine:
    """
    Main backtest engine that orchestrates the simulation.
    
    The engine supports two primary modes of operation:
    1. Standard mode: Generate signals and run backtest in one step (run_backtest)
    2. Decoupled mode: Use pre-computed signals for backtest (run_backtest_with_signals)
    """
    def __init__(self, config=None):
        """
        Initialize backtest engine.
        
        Args:
            config (None): Configuration object (currently unused but kept for potential future extension).
        """
        # CPS_v4 parameters are loaded at module level
        # Store configuration
        self.benchmark_rebalance_freq = benchmark_rebalance_freq
        self.config = config
        
        # Store price data for benchmark calculation
        self.price_data = None
        # Create commission and slippage models
        commission_model = PercentCommissionModel()
        slippage_model = PercentSlippageModel()
        
        # Create execution engine
        self.execution_engine = ExecutionEngine(
            commission_model=commission_model,
            slippage_model=slippage_model
        )
        
        # Track dates for rebalancing
        self.last_rebalance_date = None
        
        # Store initial capital for reference
        self.initial_capital = initial_capital
        
        # Track pending orders for execution delay
        self.pending_orders = {}  # {execution_date: [orders]}
        
        logger.info(f"Initialized backtest engine with ${initial_capital:,.2f} capital")
        logger.info(f"Commission rate: {commission_rate:.2%}")
        logger.info(f"Slippage rate: {slippage_rate:.2%}")
    
    def run_backtest(self, price_data, signal_generator, **signal_params):
         # CSC-MILESTONE
        
        
        
        

        """
        Run a backtest.
        
        Args:
            price_data (DataFrame): Historical price data
            signal_generator (function): Function that generates allocation signals
            **signal_params: Additional parameters for the signal generator
            
        Returns:
            dict: Backtest results
        """
        # Fetch configuration parameters from CPS v4 settings
        back_cfg = settings.get('backtest', {})
        if 'rebalance_freq' not in back_cfg:
            raise ValueError("Missing required setting: backtest.rebalance_freq")
        rebalance_freq = back_cfg['rebalance_freq']
        # If the setting is a dict with default/picklist, extract default value
        if isinstance(rebalance_freq, dict):
            rebalance_freq = str(rebalance_freq.get('default', '')).strip("'\"")
        strat_cfg = settings.get('strategy', {})
        if 'execution_delay' not in strat_cfg:
            raise ValueError("Missing required setting: strategy.execution_delay")
        execution_delay = strat_cfg['execution_delay']
        logger.info(f"Starting backtest with {rebalance_freq} rebalancing")
        logger.info(f"Execution delay: {execution_delay} days")
        
        # Store price data for benchmark calculation
        self.price_data = price_data
        logger.debug(f"Price data shape: {price_data.shape if price_data is not None else 'None'}")
        logger.info(f"Using provided signal generator: {signal_generator.__class__.__name__}")

        # Pre-calculate all signals at once before the main loop
        logger.info("Pre-calculating all signals...")
        signals_dict = signal_generator.generate_signals(price_data, **signal_params)
        logger.info("Signal pre-calculation complete")

        # --- TRACING: Setup trace directory and save initial price data ---
        reset_trace_directory_for_run() # Ensure a fresh directory for this specific run_backtest call
        trace_dir = setup_trace_directory(sub_dir_prefix="backtest_run_")
        # trace call removed(price_data, "00_initial_price_data.csv", trace_dir_override=trace_dir, step_description="Initial Price Data")
        # --- END TRACING ---
        
        # Get portfolio and trade log from the execution engine
        portfolio = self.execution_engine.portfolio
        trade_log = self.execution_engine.trade_log
        
        # Convert rebalance frequency to pandas offset using the utility function
        from utils.date_utils_v4 import map_rebalance_frequency
        pd_freq = map_rebalance_frequency(rebalance_freq)
        
        # EMA precompute removed — the signal generator now handles EMA calculations internally
        
        # Generate rebalance dates
        if rebalance_freq.lower() == 'daily':
            rebalance_dates = price_data.index
        else:
            # Use pandas date_range with the appropriate frequency
            rebalance_dates = pd.date_range(
                start=price_data.index[0],
                end=price_data.index[-1],
                freq=pd_freq
            )
            # Filter to only include dates in the price data
            rebalance_dates = [d.date() if isinstance(d, pd.Timestamp) else d for d in rebalance_dates]
            rebalance_dates = [d for d in rebalance_dates if pd.Timestamp(d) in price_data.index]
        
        # Track signals and actual allocations for reporting
        signal_history = pd.DataFrame(index=price_data.index, columns=price_data.columns)
        signal_history = signal_history.fillna(0)
        logger.info(f"Initialized signal_history with shape: {signal_history.shape}")
        weights_history = pd.DataFrame(index=price_data.index, columns=price_data.columns)
        weights_history = weights_history.fillna(0.0)

        # --- TRACING: Initialize dataframes for detailed trace outputs ---
        emax_avg_history = pd.DataFrame(index=price_data.index, columns=price_data.columns).fillna(0.0)
        ranks_history = pd.DataFrame(index=price_data.index, columns=price_data.columns).fillna(0)
        raw_signal_history = pd.DataFrame(index=price_data.index, columns=price_data.columns).fillna(0.0)
        # --- END TRACING ---
        
        logger.info(f"Initialized signal_history with shape {signal_history.shape}")
        logger.info(f"Initialized weights_history with shape {weights_history.shape}")
        
        # Main backtest loop
        logger.info("\n===== Starting date iteration =====")
        date_count = 0
        for current_date in price_data.index:
            date_count += 1
            if date_count <= 5 or date_count > len(price_data.index) - 5:
                logger.info(f"\nProcessing date {date_count}/{len(price_data.index)}: {current_date}")

            # Get current prices
            current_prices = price_data.loc[current_date]
            if date_count <= 5 or date_count > len(price_data.index) - 5:
                logger.info(f"  Current prices: {current_prices.to_dict()}")

            # Check for pending orders to execute on this date
            pending_date_match = current_date in self.pending_orders
            if pending_date_match:
                pending_orders = self.pending_orders.pop(current_date)
                logger.debug(f"Executing {len(pending_orders)} pending orders on {current_date}")
                self.execution_engine.execute_orders(pending_orders, current_date, current_prices)
                logger.info(f"  Executed and cleared {len(pending_orders)} pending orders for {current_date}")

            # Always mark to market to update portfolio value
            portfolio.mark_to_market(current_date, current_prices)
            if date_count <= 5 or date_count > len(price_data.index) - 5:
                logger.info(f"  Portfolio value: ${portfolio.get_total_value():,.2f}")

            # --- START: CRITICAL FIX - DAILY WEIGHTS HISTORY UPDATE ---
            # Update weights_history EVERY DAY based on current portfolio state.
            # This ensures continuous and accurate allocation history, not just on trade days.
            portfolio_total_value = portfolio.get_total_value()
            if portfolio_total_value > 0:
                current_weights = portfolio.get_weights()
                weights_history.loc[current_date] = [current_weights.get(symbol, 0.0) for symbol in weights_history.columns]
            else:
                weights_history.loc[current_date] = 0.0
            # --- END: CRITICAL FIX ---

            # Store daily portfolio values for later reference
            if not hasattr(self, 'portfolio_history'):
                self.portfolio_history = pd.DataFrame(index=price_data.index, columns=['total_value', 'cash_value'])
            self.portfolio_history.loc[current_date, 'total_value'] = portfolio_total_value
            self.portfolio_history.loc[current_date, 'cash_value'] = portfolio.cash

            # Check if we need to rebalance
            should_rebalance = self._should_rebalance(current_date, rebalance_dates)
            if date_count <= 5 or date_count > len(price_data.index) - 5:
                logger.info(f"  Should rebalance: {should_rebalance}")

            if should_rebalance:
                logger.info(f"  Looking up signals for {current_date}")
                # Get pre-calculated signals for current date
                signals = signals_dict.get(current_date, pd.Series(dtype=float))
                logger.debug(f"Retrieved signals for {current_date}: {signals.to_dict()}")
                

                
                
                    
                    

                     



                    
                date_str = current_date.strftime('%Y%m%d')
                    # trace call removed(pd.DataFrame(ratios_series), f"{date_str}_01_ema_ratios_current.csv", trace_dir_override=trace_dir, step_description="EMA Ratios (current date)")
                    # trace call removed(ranks_df, f"{date_str}_02_asset_ranks_current.csv", trace_dir_override=trace_dir, step_description="Asset Ranks (current date)")
                    # trace call removed(pd.DataFrame(raw_signal_series), f"{date_str}_03_raw_signals_current.csv", trace_dir_override=trace_dir, step_description="Raw Signals (current date)")
                    # trace call removed(short_ema_hist_df, f"{date_str}_04a_short_ema_history.csv", trace_dir_override=trace_dir, step_description="Short EMA History")
                    # trace call removed(med_ema_hist_df, f"{date_str}_04b_med_ema_history.csv", trace_dir_override=trace_dir, step_description="Medium EMA History")
                    # trace call removed(long_ema_hist_df, f"{date_str}_04c_long_ema_history.csv", trace_dir_override=trace_dir, step_description="Long EMA History")
                    # trace call removed(stmtemax_hist_df, f"{date_str}_05a_stmt_ratio_history.csv", trace_dir_override=trace_dir, step_description="ST/MT Ratio History")
                    # trace call removed(mtltemax_hist_df, f"{date_str}_05b_mtlt_ratio_history.csv", trace_dir_override=trace_dir, step_description="MT/LT Ratio History")
                    
                    # --- END TRACING ---
            
            # Store signals in history
            # Store signals in history using proper DataFrame loc accessor
            signal_history.loc[current_date] = signals
            logger.debug(f"  Stored signals for {current_date.date()} in signal_history")

            # Generate orders based on the signals if we have any
            if not signals.empty:
                logger.debug(f"Generating orders for signals: {signals.to_dict()}")
                orders = calculate_rebalance_orders(
                    portfolio,
                    signals,
                    current_prices,
                    current_date
                )

                # Execute orders
                if execution_delay > 0:
                    execution_date = current_date + pd.Timedelta(days=execution_delay)
                    logger.info(f"  Execution delay {execution_delay}, executing orders on {execution_date.date()}")
                    if execution_date in price_data.index:
                        execution_prices = price_data.loc[execution_date]
                        self.execution_engine.execute_orders(orders, execution_date, execution_prices)
                else:
                    logger.info(f"  Execution delay 0, executing orders immediately")
                    self.execution_engine.execute_orders(orders, current_date, current_prices)

                # Update last rebalance date
                self.last_rebalance_date = current_date
        
        # Forward fill the weights_history to ensure continuous allocation data
        weights_history = weights_history.ffill()
        
        # Validate and clean up signal and weights history before returning
        # Replace any remaining NaN values with zeros
        signal_history = signal_history.fillna(0.0)
        weights_history = weights_history.fillna(0.0)
        
        # Log final data shapes and sample values
        logger.info(f"Final signal_history shape: {signal_history.shape}")
        logger.info(f"Final weights_history shape: {weights_history.shape}")
        logger.info(f"Signal history sample (first 5 rows):\n{signal_history.head()}")
        logger.info(f"Weights history sample (first 5 rows):\n{weights_history.head()}")

        # --- TRACING: Save final signal and weights history ---
        # trace call removed(signal_history, "06_signal_history_target_allocations.csv", trace_dir_override=trace_dir, step_description="Full Signal History (Target Allocations)")
        # trace call removed(weights_history, "07_weights_history_actual_allocations.csv", trace_dir_override=trace_dir, step_description="Full Weights History (Actual Allocations)")
        # Save detailed trace DataFrames to CSV
        # trace call removed(emax_avg_history, "02_ema_average_history.csv", trace_dir_override=trace_dir, step_description="EMA Average History")
        # trace call removed(ranks_history, "03_ranks_history.csv", trace_dir_override=trace_dir, step_description="Ticker Ranks History")
        # trace call removed(raw_signal_history, "04_raw_signal_history.csv", trace_dir_override=trace_dir, step_description="Raw Signal History")
        # --- END TRACING ---

        # Check for empty dataframes
        if signal_history.empty:
            logger.error("Signal history is empty")
        if weights_history.empty:
            logger.error("Weights history is empty")

        # Compile results using helper for consistency
        results = self._calculate_results(
            portfolio,
            trade_log,
            signal_history,
            price_data=price_data,
            weights_history=weights_history,
        )

        # --- FIX: Add initial_capital to the results dictionary for reporting ---
        results['initial_capital'] = self.initial_capital

        # Add trace histories to results for potential use in reporting
        results['emax_avg_history'] = emax_avg_history
        results['ranks_history'] = ranks_history
        results['raw_signal_history'] = raw_signal_history

        logger.info("\n===== Results summary =====")
        logger.info(f"Initial capital: ${results['initial_capital']:,.2f}")
        logger.info(f"MILESTONE: Final portfolio value: ${results['final_value']:,.2f}") # CSC-MILESTONE
        logger.info(f"Total return: {results['total_return']:.2%}")
        logger.info(f"CAGR: {results['performance']['cagr']:.2%}")
        logger.info(f"Sharpe: {results['performance']['sharpe']:.2f}")
        logger.info(f"Volatility: {results['performance']['volatility']:.2%}")
        logger.info(f"Max Drawdown: {results['performance']['max_drawdown']:.2%}")
        logger.info(f"Turnover: {results['performance']['turnover']:.2%}")
        logger.info(f"Win Rate: {results['performance']['win_rate']:.2%}")
        logger.info("===== BACKTEST ENGINE: run_backtest COMPLETED =====\n")
        return results
    def _should_rebalance(self, current_date, rebalance_dates):
        """Return True if current_date matches one of the preset rebalance dates."""
        # Ensure current_date is compared as a date object if it's a Timestamp
        compare_date = current_date.date() if isinstance(current_date, pd.Timestamp) else current_date
        return compare_date in rebalance_dates

    def _calculate_benchmark_returns(self, price_data):
        """Calculate equal-weight benchmark returns (series)."""
        # Daily returns per symbol
        returns = price_data.pct_change().fillna(0)
        # Equal-weight average
        return returns.mean(axis=1)

    def _initialize_components(self, price_data):
        """
        Initialize components needed for backtesting.
        
        Args:
            price_data (pd.DataFrame): Price data for backtest period
        """
        logger.info("Initializing backtest components")
        
        # Store price data for reference
        self.price_data = price_data
        
        # Create portfolio (initial_capital is loaded from module-level settings)
        self.portfolio = Portfolio()
        self.execution_engine.portfolio = self.portfolio
        
        # Create trade log
        self.trade_log = TradeLog()
        self.execution_engine.trade_log = self.trade_log
        
        # Reset pending orders
        self.pending_orders = {}
        
    def _validate_portfolio_state(self, portfolio, prices, date_str=""):
        """
        Validate portfolio state and log any issues.
        
        Args:
            portfolio: Portfolio instance to validate
            prices: Current prices as dict {symbol: price}
            date_str: Optional date string for logging
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        valid = True
        positions = portfolio.get_positions()
        
        for symbol, position in positions.items():
            if symbol not in prices:
                logger.warning(f"{date_str} No price available for {symbol} in validation")
                continue
                
            if position['quantity'] < 0:
                logger.warning(f"{date_str} Negative position detected for {symbol}: {position['quantity']}")
                valid = False
                
        return valid
        
    def run_backtest_with_signals(self, signals, price_data):
        """
        Run backtest using pre-computed signals with enhanced state management.
        
        Args:
            signals (pd.DataFrame): Pre-computed signals with datetime index
            price_data (pd.DataFrame): Price data for backtest period
        
        Returns:
            dict: Results including portfolio, allocation_history, and trade_log
        """
        logger.info("Starting backtest with pre-computed signals")
        
        # Initialize components
        self._initialize_components(price_data)
        
        # Extract date range
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        date_range = price_data.index
        
        # Initialize tracking structures
        portfolio = self.portfolio
        trade_log = TradeLog()
        signal_history = pd.DataFrame(0, index=date_range, columns=price_data.columns, dtype=float)
        weights_history = pd.DataFrame(0, index=date_range, columns=price_data.columns, dtype=float)
        
        # Main backtest loop - use pre-computed signals
        for i, current_date in enumerate(date_range):
            # Format date for logging
            date_str = f"[{current_date.strftime('%Y-%m-%d')}]"
            
            # Skip if current_date is not in signals index
            if current_date not in signals.index:
                logger.debug(f"{date_str} No signals available, skipping")
                continue
                
            # Update portfolio with current prices before any actions
            current_prices = price_data.loc[current_date].to_dict()
            portfolio.mark_to_market(current_date, current_prices)
            
            # Validate portfolio state before order generation
            if not self._validate_portfolio_state(portfolio, current_prices, date_str):
                logger.warning(f"{date_str} Portfolio validation failed before order generation")
            
            # Get signals for current date
            current_signals = signals.loc[current_date]
            
            # Log current portfolio value and positions before rebalancing
            portfolio_value = portfolio.get_total_value(current_prices)
            logger.debug(f"{date_str} Pre-rebalance portfolio value: ${portfolio_value:,.2f}")
            logger.debug(f"{date_str} Current signals: {current_signals.to_dict()}")
            
            # Generate orders based on signals
            try:
                orders = calculate_rebalance_orders(
                    portfolio=portfolio,
                    target_allocations=current_signals,
                    prices=current_prices,  # Use dict instead of Series
                    order_date=current_date
                )
                logger.debug(f"{date_str} Generated {len(orders)} orders")
            except Exception as e:
                logger.error(f"{date_str} Error generating orders: {str(e)}")
                continue
            
            # Execute trades if we have orders
            if orders:
                try:
                    trade_results = self.execution_engine.execute_orders(
                        orders=orders,
                        execution_date=current_date,
                        prices=current_prices  # Use dict instead of Series
                    )
                    
                    # Process trade results
                    for trade in trade_results:
                        trade_log.add_trade(trade)
                        portfolio.update_from_trade(trade)
                        
                    logger.debug(f"{date_str} Executed {len(trade_results)} trades")
                    
                except Exception as e:
                    logger.error(f"{date_str} Error executing orders: {str(e)}")
                    continue
                
                # Validate portfolio state after trades
                portfolio.mark_to_market(current_date, current_prices)
                if not self._validate_portfolio_state(portfolio, current_prices, date_str):
                    logger.warning(f"{date_str} Portfolio validation failed after trades")
            
            # Update history
            signal_history.loc[current_date] = current_signals
            weights = portfolio.get_weights(current_prices)
            weights_history.loc[current_date] = weights
        
        # Calculate and return results
        results = self._calculate_results(
            portfolio=portfolio,
            trade_log=trade_log,
            signal_history=signal_history,
            price_data=price_data,
            weights_history=weights_history
        )
        
        logger.info("Backtest with pre-computed signals completed")
        return results
        
    def _should_rebalance(self, current_date, rebalance_dates):
        """Return True if current_date matches one of the preset rebalance dates."""
        # Ensure current_date is compared as a date object if it's a Timestamp
        compare_date = current_date.date() if isinstance(current_date, pd.Timestamp) else current_date
        return compare_date in rebalance_dates

    def _calculate_benchmark_returns(self, price_data):
        """Calculate equal-weight benchmark returns (series)."""
        # Daily returns per symbol
        returns = price_data.pct_change().fillna(0)
        # Equal-weight average
        return returns.mean(axis=1)

    def _calculate_results(self, portfolio, trade_log, signal_history, price_data=None, weights_history=None):
        logger.info("Calculating final results...") # CSC-MILESTONE
        logger.debug("Entering _calculate_results")
        
        results = {}
        performance = {}

        # --- START: DIAGNOSTIC CHECK FOR WEIGHTS_HISTORY ---
        debug_dir = Path('debug_allocation_history')
        debug_dir.mkdir(exist_ok=True)
        debug_file_path = debug_dir / 'weights_history_debug.txt'

        is_invalid = False
        log_message = ""

        if weights_history is None:
            is_invalid = True
            log_message = "CRITICAL ERROR: weights_history is None. No allocation data was generated."
        elif weights_history.empty:
            is_invalid = True
            log_message = "CRITICAL ERROR: weights_history is empty."
        elif weights_history.sum().sum() < 1e-6:
            is_invalid = True
            log_message = "CRITICAL ERROR: weights_history contains all zeros or is negligible."

        if is_invalid:
            error_content = f"{log_message}\n\nData sample:\n{weights_history.head().to_string() if weights_history is not None else 'None'}"
            logger.error(error_content)
            with open(debug_file_path, 'w') as f:
                f.write(error_content)
        else:
            success_message = f"SUCCESS: weights_history appears valid.\n\nData sample:\n{weights_history.head().to_string()}"
            logger.info(success_message)
            with open(debug_file_path, 'w') as f:
                f.write(success_message)
        # --- END: DIAGNOSTIC CHECK ---

        # Convert trade log to DataFrame
        logger.debug("Converting trade log to DataFrame.")
        trade_df = trade_log.to_dataframe()
        trades = trade_log.get_trades()
        portfolio_values = portfolio.get_value_history()
        logger.debug("Trade log converted. Portfolio values obtained.")

        if len(portfolio_values) > 1:
            strategy_returns = portfolio_values.pct_change().fillna(0)
            total_return = (portfolio_values.iloc[-1] / portfolio_values.iloc[0]) - 1
        else:
            strategy_returns = pd.Series(0, index=portfolio_values.index)
            total_return = 0

        benchmark_returns = self._calculate_benchmark_returns(price_data) if price_data is not None else None
        logger.debug("Calculated returns.")

        # Calculate performance metrics
        logger.debug("Calculating CAGR.")
        if len(portfolio_values) > 1:
            days = (portfolio_values.index[-1] - portfolio_values.index[0]).days
            years = days / 365.25
            cagr = ((portfolio_values.iloc[-1] / portfolio_values.iloc[0]) ** (1/years) - 1) if years > 0 else 0
        else:
            cagr = 0
        
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
            # Use 'total $s' column instead of 'amount' which was renamed in TradeLog.to_dataframe()
            if 'total $s' in trade_df.columns:
                total_traded_value = trade_df['total $s'].abs().sum()
            elif 'amount' in trade_df.columns:
                # Fallback to 'amount' if it exists (for backward compatibility)
                total_traded_value = trade_df['amount'].abs().sum()
            else:
                logger.warning("Neither 'total $s' nor 'amount' columns found in trade_df. Setting total_traded_value to 0.")
                total_traded_value = 0
                
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
        # --- END: Generate Allocation History ---

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
        results['final_value'] = portfolio_values.iloc[-1] if not portfolio_values.empty else self.initial_capital
        results['performance'] = performance

        print("MILESTONE: Final results calculation complete.") # CSC-MILESTONE
        logger.debug("Exiting _calculate_results successfully.")
        return results
