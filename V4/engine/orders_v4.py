"""
engine/orders_v4.py
Order and trade management module (CPS v4 compliant).
Handles order creation, execution, and trade logging.
# CPS v4 compliance verified: 2025-06-06

This module does not directly use any parameters requiring centralization. If future parameterization is needed (e.g. order types, trade log settings), all such parameters must be sourced from CPS v4 settings and not hardcoded or locally defaulted.
"""

import pandas as pd
import numpy as np
from datetime import date, datetime
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Order:
    """
    Order class for representing trading orders.
    """
    def __init__(self, symbol=None, quantity=None, price=None, order_type='MARKET', order_date=None, ticker=None):
        """
        Initialize order.
        
        Args:
            symbol (str): Symbol (can also use ticker parameter)
            ticker (str): Alternative to symbol parameter for backward compatibility
            quantity (float): Quantity (positive for buy, negative for sell)
            price (float): Limit price or market price estimate
            order_type (str): Order type ('MARKET', 'LIMIT')
            order_date (date): Order date
        """
        self.order_id = str(uuid.uuid4())
        # Handle ticker parameter as an alternative to symbol for backward compatibility
        self.symbol = symbol if symbol is not None else ticker
        self.ticker = self.symbol  # Ensure ticker is always set for backward compatibility
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.order_date = order_date if order_date else date.today()
        self.status = 'OPEN'  # OPEN, FILLED, CANCELLED, REJECTED
        
        # Validate required parameters
        if self.symbol is None:
            logger.debug("Order created without symbol/ticker parameter")
        if self.quantity is None:
            logger.debug("Order created without quantity parameter")
        
        logger.debug(f"Created order: {self}")
    
    def __str__(self):
        """String representation of order. Handles None values for price gracefully."""
        direction = "BUY" if self.quantity > 0 else "SELL"
        price_str = f"${self.price:.2f}" if self.price is not None else "N/A"
        return f"{direction} {abs(self.quantity)} {self.symbol} @ {price_str} ({self.order_type})"

class Trade:
    """
    Trade class for representing executed trades.
    """
    def __init__(self, order, execution_date, execution_price, commission, amount):
        """
        Initialize trade.
        
        Args:
            order (Order): Original order
            execution_date (date): Execution date
            execution_price (float): Execution price
            commission (float): Commission
            amount (float): Total amount (including commission)
        """
        self.trade_id = str(uuid.uuid4())
        self.order_id = order.order_id
        self.symbol = order.symbol
        self.quantity = order.quantity
        self.order_date = order.order_date
        self.order_type = order.order_type # Added to make it available on Trade object
        self.execution_date = execution_date
        self.execution_price = execution_price
        self.commission = commission
        self.amount = amount
        self.pnl = 0.0  # To be calculated later if applicable
        if self.execution_price is None or self.commission is None:
            logger.debug(f"Trade created with None for execution_price or commission: execution_price={self.execution_price}, commission={self.commission}")
        logger.debug(f"Created trade: {self}")
    
    def __str__(self):
        """
        String representation of trade.
        Handles None values for execution_price and commission gracefully, returning 'N/A' if missing.
        """
        direction = "BOUGHT" if self.quantity > 0 else "SOLD"
        exec_price = f"${self.execution_price:.2f}" if self.execution_price is not None else "N/A"
        commission = f"${self.commission:.2f}" if self.commission is not None else "N/A"
        return f"{direction} {abs(self.quantity)} {self.symbol} @ {exec_price}, Commission: {commission}"

    def to_dict(self):
        """
        Convert trade to dictionary.
        
        Returns:
            dict: Trade as dictionary
        """
        return {
            'trade_id': self.trade_id,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'order_date': self.order_date,
            'order_type': self.order_type,
            'execution_date': self.execution_date,
            'execution_price': self.execution_price,
            'commission': self.commission,
            'amount': self.amount,
            'pnl': self.pnl
        }

class TradeLog:
    """
    Trade log for tracking executed trades.
    """
    def __init__(self):
        """Initialize trade log."""
        self.trades = []
    
    def add_trade(self, trade):
        """
        Add trade to log.
        
        Args:
            trade (Trade): Executed trade
        """
        self.trades.append(trade)
        logger.debug(f"Added trade to log: {trade}")
    
    def get_trades(self):
        """Return list of trades (backward-compat helper)."""
        return self.trades

    def to_dataframe(self):
        """
        Convert trade log to DataFrame with standardized columns.
        
        Returns:
            DataFrame: Trade log as DataFrame with columns:
                date, ticker, action, quantity, price per share executed, total $s, execution_date, pnl
        """
        if not self.trades:
            return pd.DataFrame(columns=[
                'date', 'ticker', 'action', 'quantity', 
                'price per share executed', 'total $s', 'execution_date', 'pnl'
            ])
        
        # Create a list of safe dictionaries with all required fields
        safe_data = []
        for trade in self.trades:
            # Get the base dictionary
            trade_dict = trade.to_dict()
            
            # Create action based on quantity
            action = 'buy' if trade_dict.get('quantity', 0) > 0 else 'sell'
            
            # Calculate total amount if not present
            if 'amount' not in trade_dict or trade_dict['amount'] is None:
                quantity = abs(trade_dict.get('quantity', 0))
                price = trade_dict.get('execution_price', 0)
                if price is None:
                    price = 0
                total_amount = quantity * price
            else:
                total_amount = trade_dict['amount']
            
            # Create standardized dictionary with all required fields
            safe_dict = {
                'date': trade_dict.get('order_date'),
                'ticker': trade_dict.get('symbol'),
                'action': action,
                'quantity': abs(trade_dict.get('quantity', 0)),
                'price per share executed': trade_dict.get('execution_price'),
                'total $s': total_amount,
                'execution_date': trade_dict.get('execution_date'),
                'pnl': trade_dict.get('pnl', 0.0)
            }
            safe_data.append(safe_dict)
        
        # Create DataFrame from safe data
        df = pd.DataFrame(safe_data)
        
        # Sort by execution date and reset index
        if not df.empty and 'execution_date' in df.columns:
            df = df.sort_values('execution_date').reset_index(drop=True)
        
        return df
    
    def get_trades_for_symbol(self, symbol):
        """
        Get trades for a specific symbol.
        
        Args:
            symbol (str): Symbol
            
        Returns:
            list: Trades for symbol
        """
        return [trade for trade in self.trades if trade.symbol == symbol]
    
    def get_trades_for_date(self, date_val):
        """
        Get trades for a specific date.
        
        Args:
            date_val (date): Date
            
        Returns:
            list: Trades for date
        """
        return [trade for trade in self.trades if trade.execution_date == date_val]
    
    def calculate_pnl(self, cost_basis_dict):
        """
        Calculate P&L for trades based on cost basis.
        
        Args:
            cost_basis_dict (dict): Cost basis {symbol: cost_basis}
        """
        for trade in self.trades:
            if trade.quantity < 0 and trade.symbol in cost_basis_dict:
                # Sell trade
                cost_basis = cost_basis_dict[trade.symbol]
                trade.pnl = (-trade.quantity) * (trade.execution_price - cost_basis) - trade.commission
    
    def __len__(self):
        """Get number of trades."""
        return len(self.trades)
