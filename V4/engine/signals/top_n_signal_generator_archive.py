"""
engine/signals/top_n_signal_generator.py
Signal generator that implements Top-N asset allocation strategy.
CPS v4 compliance verified: 2025-06-21

This module uses the Central Parameter System v4 for configuration.
Parameters are loaded directly from the settings_parameters_v4.ini file.

Required parameters:
- system_top_n: Dictionary with optimizable parameter format containing:
    - default_value: Number of top assets to select (e.g., 2)
    - optimize: Whether to optimize this parameter
    - min_value: Minimum value for optimization
    - max_value: Maximum value for optimization
    - increment: Step size for optimization
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class TopNSignalGenerator:
    """Signal generator that selects top N assets based on trend strength."""
    
    def __init__(self, signal_params):
        """
        Initialize the signal generator.
        
        Args:
            signal_params (dict): Parameters from settings, must include system_top_n
        """
        if 'system_top_n' not in signal_params:
            raise ValueError("Required parameter 'system_top_n' not found in settings")
        
        system_top_n = signal_params['system_top_n']
        if not isinstance(system_top_n, dict) or 'default_value' not in system_top_n:
            raise ValueError("system_top_n must be an optimizable parameter dict with 'default_value'")
        
        self.top_n = system_top_n['default_value']
        self.signal_params = signal_params
        logger.info(f"Initialized TopNSignalGenerator with top_n={self.top_n}")
    
    def __call__(self, current_date, price_data):
        """
        Generate signals for the current date based on price data up to that date.
        
        Args:
            current_date: The date to generate signals for
            price_data: DataFrame of price data up to current_date
            
        Returns:
            dict: Asset weights {asset: weight}
        """
        logger.debug(f"Generating signals for {current_date}")
        
        # Calculate trend strength (simple returns for now)
        returns = price_data.pct_change()
        trend = returns.iloc[-1]  # Use most recent returns as trend indicator
        
        # Rank assets by trend strength (rank 1 = strongest trend)
        ranking = trend.rank(ascending=False, method='first')
        
        # Select top N assets with equal weights
        mask = ranking <= self.top_n
        selected_assets = mask[mask].index
        
        # Generate weights dictionary
        weights = {}
        weight = 1.0 / self.top_n
        for asset in price_data.columns:
            weights[asset] = weight if asset in selected_assets else 0.0
        
        logger.debug(f"Generated weights for {len(selected_assets)} assets: {weights}")
        return weights
