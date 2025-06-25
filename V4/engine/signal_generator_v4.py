"""
v4/engine/signal_generator.py
Signal generator interface module for the backtest engine.
Part of the backtest engine system (CPS v4 compliant).
"""

import pandas as pd
import numpy as np
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

def _get_int_param_value(param_value, param_name):
    """
    Extracts an integer 'default_value' from a ComplexN dictionary parameter.
    Raises ValueError if the parameter is not a dict, missing 'default_value',
    or if 'default_value' cannot be converted to an integer.
    """
    if not isinstance(param_value, dict):
        err_msg = (
            f"Parameter '{param_name}' must be a dictionary (ComplexN type) for EMA lookback, "
            f"but got type {type(param_value)} with value: {param_value}. Ensure strategy parameters are correctly passed."
        )
        logger.error(err_msg)
        raise ValueError(err_msg)

    if 'default_value' not in param_value:
        err_msg = (
            f"Parameter '{param_name}' (dictionary: {param_value}) is missing "
            f"the required 'default_value' key for EMA lookback. Ensure ComplexN structure."
        )
        logger.error(err_msg)
        raise ValueError(err_msg)

    val_to_cast = param_value['default_value']

    try:
        return int(val_to_cast)
    except (ValueError, TypeError) as e:
        err_msg = (
            f"Could not convert 'default_value' ('{val_to_cast}') of EMA lookback parameter "
            f"'{param_name}' to int. Error: {e}"
        )
        logger.error(err_msg)
        raise ValueError(err_msg) from e

class SignalGenerator(ABC):
    """
    Abstract base class for signal generators.
    All signal generation strategies should inherit from this class.
    """
    
    @abstractmethod
    def generate_signals(self, price_data, **params):
        """
        Generate allocation signals from price data.
        
        Args:
            price_data (DataFrame): Historical price data
            **params: Additional parameters for signal generation
            
        Returns:
            dict: Allocation signals {symbol: weight}
        """
        pass
    
    def validate_signals(self, signals):
        """
        Validate allocation signals.
        
        Args:
            signals (dict): Allocation signals {symbol: weight}
            
        Returns:
            dict: Validated signals
        """
        # Check for None or empty signals
        if signals is None or len(signals) == 0:
            logger.warning("Empty signals generated")
            return {}
            
        # Check for negative weights
        for symbol, weight in list(signals.items()):
            if weight < 0:
                logger.warning(f"Negative weight for {symbol}: {weight}. Setting to 0.")
                signals[symbol] = 0
                
        # Normalize weights to sum to 1.0
        total_weight = sum(signals.values())
        if total_weight > 0:
            signals = {symbol: weight / total_weight for symbol, weight in signals.items()}
        else:
            logger.warning("Total weight is zero or negative. Equal weighting applied.")
            if signals:
                equal_weight = 1.0 / len(signals)
                signals = {symbol: equal_weight for symbol in signals}
                
        return signals

class EqualWeightSignalGenerator(SignalGenerator):
    """
    Equal weight signal generator.
    Allocates equal weight to all assets.
    """
    
    def generate_signals(self, price_data, **params):
        """
        Generate equal weight allocation signals.
        
        Args:
            price_data (DataFrame): Historical price data
            **params: Additional parameters (unused)
            
        Returns:
            dict: Equal weight allocation signals
        """
        print("\n=== EqualWeightSignalGenerator.generate_signals ===")
        print(f"Price data shape: {price_data.shape if price_data is not None else 'None'}")
        print(f"Price data columns: {price_data.columns.tolist() if price_data is not None else 'None'}")
        print(f"Price data head:\n{price_data.head() if price_data is not None else 'None'}")
        print(f"Additional params: {params}")
        
        symbols = price_data.columns
        equal_weight = 1.0 / len(symbols)
        signals = {symbol: equal_weight for symbol in symbols}
        
        print(f"Generated equal weight signals: {signals}")
        validated_signals = self.validate_signals(signals)
        print(f"Validated signals: {validated_signals}")
        print("=== EqualWeightSignalGenerator.generate_signals completed ===\n")
        return validated_signals

# Momentum strategy removed to keep the codebase simple and focused

class EMASignalGenerator(SignalGenerator):
    """
    EMA-based signal generator.
    Allocates based on exponential moving average crossovers.
    """
    
    def generate_signals(self, price_data, st_lookback=10, mt_lookback=50, lt_lookback=150, precomputed_emas=None, **params):
        """
        Generate EMA-based allocation signals by delegating to core EMA allocation model.
        
        Args:
            price_data (DataFrame): Historical price data
            **params: Additional parameters including system_top_n and signal_algo
        Returns:
            dict: EMA-based allocation signals {symbol: weight}
        """
        from v4.models.ema_signal_bridge import run_ema_model_with_tracing
        
        logger.info("EMASignalGenerator: Using ema_signal_bridge for signal generation with tracing")
        # Call the model through the bridge to ensure trace files are generated
        signals_dict = run_ema_model_with_tracing(price_data=price_data, **params)
        
        # Validate and normalize signals for each date
        validated_signals_dict = {}
        for date, weights in signals_dict.items():
            validated_signals_dict[date] = self.validate_signals(weights)
        return validated_signals_dict
        print(f"Price data shape: {price_data.shape if price_data is not None else 'None'}")
        print(f"Price data columns: {price_data.columns.tolist() if price_data is not None else 'None'}")
        print(f"Price data head:\n{price_data.head() if price_data is not None else 'None'}")
        # Extract integer values for lookbacks if they are passed as ComplexN dicts
        st_lookback_int = _get_int_param_value(st_lookback, 'st_lookback')
        mt_lookback_int = _get_int_param_value(mt_lookback, 'mt_lookback')
        lt_lookback_int = _get_int_param_value(lt_lookback, 'lt_lookback')

        print(f"EMA parameters - st_lookback: {st_lookback_int}, mt_lookback: {mt_lookback_int}, lt_lookback: {lt_lookback_int}")
        print(f"Additional params: {params}")
        
        # Use precomputed EMAs if available, otherwise calculate them
        if precomputed_emas is None:
            print("Calculating EMAs from price data...")
            # Calculate EMAs
            st_ema = price_data.ewm(span=st_lookback_int).mean()
            mt_ema = price_data.ewm(span=mt_lookback_int).mean()
            lt_ema = price_data.ewm(span=lt_lookback_int).mean()
            print(f"Calculated EMAs - shapes: st_ema: {st_ema.shape}, mt_ema: {mt_ema.shape}, lt_ema: {lt_ema.shape}")
        else:
            print("Using precomputed EMAs")
            st_ema = precomputed_emas['st_ema']
            mt_ema = precomputed_emas['mt_ema']
            lt_ema = precomputed_emas['lt_ema']
            print(f"Precomputed EMAs - shapes: st_ema: {st_ema.shape}, mt_ema: {mt_ema.shape}, lt_ema: {lt_ema.shape}")
            
        # Get the most recent values
        st_current = st_ema.iloc[-1]
        mt_current = mt_ema.iloc[-1]
        lt_current = lt_ema.iloc[-1]
        print(f"Most recent EMA values (sample):\nst_ema: {dict(list(st_current.items())[:3])}...\nmt_ema: {dict(list(mt_current.items())[:3])}...\nlt_ema: {dict(list(lt_current.items())[:3])}...")
        
        # Calculate trend strength
        # Short above medium and medium above long indicates strong uptrend
        print("Calculating trend strength for each symbol...")
        trend_strength = {}
        for symbol in price_data.columns:
            # Skip if any EMA is missing
            if (pd.isna(st_current[symbol]) or 
                pd.isna(mt_current[symbol]) or 
                pd.isna(lt_current[symbol])):
                trend_strength[symbol] = 0
                print(f"  {symbol}: Missing EMA values, setting trend strength to 0")
                continue
                
            # Calculate trend strength
            st_mt_ratio = st_current[symbol] / mt_current[symbol] - 1
            mt_lt_ratio = mt_current[symbol] / lt_current[symbol] - 1
            
            # Combine ratios (positive values indicate uptrend)
            strength = st_mt_ratio + mt_lt_ratio
            trend_strength[symbol] = max(0, strength)  # Only consider positive trends
            if symbol in list(price_data.columns)[:3]:
                print(f"  {symbol}: st_mt_ratio={st_mt_ratio:.4f}, mt_lt_ratio={mt_lt_ratio:.4f}, strength={strength:.4f}, final={trend_strength[symbol]:.4f}")
            
        # Filter for positive trend strength
        positive_trends = {s: v for s, v in trend_strength.items() if v > 0}
        print(f"Positive trends: {len(positive_trends)}/{len(trend_strength)} assets")
        if not positive_trends:
            logger.warning("No assets with positive trend strength")
            print("WARNING: No assets with positive trend strength, returning empty signals")
            validated_signals = self.validate_signals({})
            print(f"Validated signals: {validated_signals}")
            print("=== EMASignalGenerator.generate_signals completed ===\n")
            return validated_signals
            
        # Allocate proportionally to trend strength
        total_strength = sum(positive_trends.values())
        print(f"Total trend strength: {total_strength:.4f}")
        if total_strength <= 0:
            # Equal weight if no positive trends
            equal_weight = 1.0 / len(positive_trends)
            signals = {symbol: equal_weight for symbol in positive_trends}
            print(f"Using equal weights ({equal_weight:.4f}) due to zero total strength")
        else:
            # Weight proportional to trend strength
            signals = {symbol: strength / total_strength for symbol, strength in positive_trends.items()}
            print(f"Allocated weights proportionally to trend strength")
            print(f"Sample allocations (first 3): {dict(list(signals.items())[:3])}...")
        
        validated_signals = self.validate_signals(signals)
        print(f"Validated signals sample (first 3): {dict(list(validated_signals.items())[:3])}...")
        print("=== EMASignalGenerator.generate_signals completed ===\n")
        return validated_signals

def create_signal_generator(strategy_name, **params):
    """
    Factory function to create a signal generator.
    
    Args:
        strategy_name (str): Name of the strategy
        **params: Additional parameters for the strategy
        
    Returns:
        SignalGenerator: Signal generator instance
    """
    print(f"\n=== create_signal_generator ===\nStrategy: {strategy_name}\nParams: {params}")
    strategies = {
        'equal_weight': EqualWeightSignalGenerator,
        'EMA_Crossover': EMASignalGenerator
    }
    
    if strategy_name not in strategies:
        logger.error(f"Unknown strategy: {strategy_name}")
        logger.info(f"Available strategies: {list(strategies.keys())}")
        print(f"ERROR: Unknown strategy: {strategy_name}")
        print(f"Available strategies: {list(strategies.keys())}")
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    generator = strategies[strategy_name]()
    print(f"Created signal generator: {type(generator).__name__}")
    print("=== create_signal_generator completed ===\n")
    return generator

# Function wrapper for backward compatibility
def generate_signals(price_data, strategy='equal_weight', **params):
    """
    Generate allocation signals using the specified strategy.
    
    Args:
        price_data (DataFrame): Historical price data
        strategy (str): Strategy name
        **params: Additional parameters for the strategy
        
    Returns:
        dict: Timestamp-keyed dictionary of allocation signals e.g. {pd.Timestamp: {symbol: weight}}
    """
    print(f"\n=== generate_signals wrapper ===")
    print(f"Strategy: {strategy}")
    print(f"Price data shape: {price_data.shape if price_data is not None else 'None'}")
    print(f"Additional params: {params}")
    generator = create_signal_generator(strategy)
    signals = generator.generate_signals(price_data, **params)
    
    # Get the latest timestamp from the price data
    last_date = price_data.index[-1]
    
    # Wrap the signals in a timestamped dictionary
    timestamped_signals = {last_date: signals}
    
    print(f"Signals returned from generator: {type(signals)}")
    if isinstance(signals, dict):
        print(f"Number of symbols with allocations: {len(signals)}")
        if signals:
            print(f"Sample allocations (first 3): {dict(list(signals.items())[:3])}...")
    elif isinstance(signals, pd.Series):
        print(f"Signals shape: {signals.shape}")
        print(f"Sample allocations (first 3): {dict(list(signals.items())[:3])}...")
    print("=== generate_signals wrapper completed ===\n")
    return timestamped_signals
