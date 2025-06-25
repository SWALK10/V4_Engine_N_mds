"""
engine/portfolio_v4.py
Portfolio state management module (CPS v4 compliant).

Maintains a single source of truth for portfolio positions, cash, and history.

CPS_v4 Parameters Required:
- backtest:
    - initial_capital (float): The starting cash balance for the portfolio.

If 'initial_capital' is missing from the 'backtest' section in CPS_v4 settings,
the module will raise a ValueError.
"""

import pandas as pd
import numpy as np
from datetime import date
import logging
from copy import deepcopy
from v4.settings.settings_CPS_v4 import load_settings

settings = load_settings()
try:
    backtest_cfg = settings['backtest']
    initial_capital = backtest_cfg['initial_capital']
except KeyError as e:
    raise ValueError(f"Missing required CPS v4 parameter in 'backtest' settings: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PortfolioSnapshot:
    """
    Represents the state of a portfolio at a specific point in time.
    """
    def __init__(self, date, cash, positions, prices):
        """
        Create a portfolio snapshot.
        
        Args:
            date (date): The date of the snapshot
            cash (float): Cash balance
            positions (dict): Asset positions {symbol: quantity}
            prices (dict): Asset prices {symbol: price}
        """
        self.date = date
        self.cash = cash
        self.positions = positions.copy()  # Make a copy to avoid reference issues
        self.prices = prices.copy()
        
        # Calculate portfolio value
        self.position_value = sum(positions.get(asset, 0) * prices.get(asset, 0) 
                                for asset in positions.keys())
        self.total_value = self.cash + self.position_value
        
        # Calculate weights
        self.weights = {}
        if self.total_value > 0:
            for asset, quantity in positions.items():
                self.weights[asset] = (quantity * prices.get(asset, 0)) / self.total_value
    
    def to_dict(self):
        """Convert snapshot to dictionary for reporting."""
        return {
            'date': self.date,
            'cash': self.cash,
            'position_value': self.position_value,
            'total_value': self.total_value,
            'positions': self.positions,
            'weights': self.weights
        }


class Portfolio:
    """
    Maintains the state of a portfolio over time.
    Acts as the single source of truth for positions, cash, and performance.
    The initial_capital is sourced from module-level CPS_v4 settings.
    """
    def __init__(self):
        """
        Initialize a portfolio.
        The starting cash balance (initial_capital) is sourced from module-level
        CPS_v4 settings under the 'backtest' section.
        """
        self.initial_capital = initial_capital  # Module-level variable from CPS_v4
        self.cash = initial_capital  # Module-level variable from CPS_v4
        self.positions = {}  # {symbol: {'quantity': float, 'value': float, 'cost_basis': float}}
        self.history = {}  # {date: {'cash': float, 'positions': dict, 'total_value': float}}
        
        logger.debug(f"Initialized portfolio with ${initial_capital:,.2f} capital")
    
    def add_cash(self, amount):
        """
        Add cash to portfolio.
        
        Args:
            amount (float): Amount to add
        """
        self.cash += amount
        logger.debug(f"Added ${amount:,.2f} cash to portfolio")
    
    def remove_cash(self, amount):
        """
        Remove cash from portfolio.
        
        Args:
            amount (float): Amount to remove
        
        Returns:
            bool: True if successful, False if insufficient cash
        """
        if amount <= self.cash:
            self.cash -= amount
            logger.debug(f"Removed ${amount:,.2f} cash from portfolio")
            return True
        else:
            logger.warning(f"Insufficient cash to remove ${amount:,.2f}")
            return False
    
    def add_position(self, symbol, quantity, price, cost_basis=None):
        """
        Add position to portfolio.
        
        Args:
            symbol (str): Symbol
            quantity (float): Quantity
            price (float): Current price
            cost_basis (float, optional): Cost basis. Defaults to price.
        """
        if cost_basis is None:
            cost_basis = price
        
        if symbol in self.positions:
            # Update existing position
            current_quantity = self.positions[symbol]['quantity']
            current_cost = self.positions[symbol]['cost_basis'] * current_quantity
            
            # Calculate new position
            new_quantity = current_quantity + quantity
            new_cost = current_cost + (quantity * cost_basis)
            
            # Update position
            if new_quantity != 0:
                self.positions[symbol]['quantity'] = new_quantity
                self.positions[symbol]['cost_basis'] = new_cost / new_quantity
                self.positions[symbol]['value'] = new_quantity * price
            else:
                # Remove position if quantity is zero
                del self.positions[symbol]
        else:
            # Create new position
            self.positions[symbol] = {
                'quantity': quantity,
                'cost_basis': cost_basis,
                'value': quantity * price
            }
        
        logger.debug(f"Added {quantity} shares of {symbol} at ${price:,.2f}")
    
    def remove_position(self, symbol, quantity, price):
        """
        Remove position from portfolio.
        
        Args:
            symbol (str): Symbol
            quantity (float): Quantity
            price (float): Current price
        
        Returns:
            bool: True if successful, False if insufficient quantity
        """
        # Initialize date_str to avoid UnboundLocalError
        date_str = getattr(self, 'current_date', '')
        if date_str:
            date_str = f"[{date_str}] "
        if symbol in self.positions:
            current_quantity = self.positions[symbol]['quantity']
            
            if quantity <= current_quantity:
                # Calculate realized P&L
                cost_basis = self.positions[symbol]['cost_basis']
                pnl = (price - cost_basis) * quantity
                
                # Update position
                new_quantity = current_quantity - quantity
                
                if new_quantity > 0:
                    self.positions[symbol]['quantity'] = new_quantity
                    self.positions[symbol]['value'] = new_quantity * price
                else:
                    # Remove position if quantity is zero
                    del self.positions[symbol]
                
                # Use the current date from the trade if available
                date_str = getattr(self, 'current_date', '')
                if date_str:
                    date_str = f"[{date_str}] "
                
                logger.debug(f"{date_str}Removed {quantity} shares of {symbol} at ${price:,.2f}, P&L: ${pnl:,.2f}")
                return True, pnl
            else:
                logger.warning(f"{date_str}Insufficient quantity to remove {quantity} shares of {symbol}")
                return False, 0
        else:
            logger.warning(f"{date_str}Position {symbol} not found")
            return False, 0
    
    def get_position(self, symbol):
        """
        Get position information for a symbol.
        
        Args:
            symbol (str): Symbol to retrieve position for
            
        Returns:
            dict: Position information including quantity, cost_basis, and value
                 Returns None if position does not exist
        """
        if symbol in self.positions:
            return self.positions[symbol]
        else:
            logger.debug(f"Position {symbol} not found in portfolio")
            return None
    
    def update_from_trade(self, trade):
        """
        Update portfolio based on an executed trade.
        
        Args:
            trade (Trade): Executed trade
            
        Returns:
            tuple: (success, pnl) - success is True if the trade was processed, pnl is the profit/loss for sell trades
        """
        symbol = trade.symbol
        quantity = trade.quantity
        price = trade.execution_price
        
        # Update cash
        self.cash -= trade.amount
        
        # Update position and track PnL for sells
        pnl = 0.0
        if quantity > 0:
            # Buy
            self.add_position(symbol, quantity, price)
            success = True
        else:
            # Sell - capture PnL
            success, pnl = self.remove_position(symbol, abs(quantity), price)
        
        # Use the trade date if available
        date_str = ""
        if hasattr(trade, 'execution_date'):
            self.current_date = trade.execution_date.strftime('%Y-%m-%d')
            date_str = f"[{self.current_date}] "
        
        logger.debug(f"{date_str}Updated portfolio from trade: {symbol} {quantity} @ ${price:.2f}")
        logger.debug(f"{date_str}New cash balance: ${self.cash:.2f}")
        
        return success, pnl
    
    def mark_to_market(self, current_date, prices):
        """
        Mark portfolio to market.
        
        Args:
            current_date (date): Current date
            prices (dict): Dictionary of prices {symbol: price}
        """
        # Update position values
        for symbol in list(self.positions.keys()):
            if symbol in prices:
                price = prices[symbol]
                quantity = self.positions[symbol]['quantity']
                self.positions[symbol]['value'] = quantity * price
            else:
                logger.warning(f"Price for {symbol} not found, using previous value")
        
        # Calculate total value
        total_value = self.cash + sum(pos['value'] for pos in self.positions.values())
        
        # Save snapshot to history
        self.history[current_date] = {
            'cash': self.cash,
            'positions': deepcopy(self.positions),
            'total_value': total_value
        }
        
        # Update current date for logging
        self.current_date = current_date.strftime('%Y-%m-%d')
        logger.debug(f"[{self.current_date}] Marked portfolio to market, total value: ${total_value:,.2f}")
    
    def get_positions(self):
        """
        Get current positions in the portfolio.
        
        Returns:
            dict: Dictionary of positions {symbol: position_dict}
        """
        return self.positions
    
    def get_total_value(self, prices=None):
        """
        Get total portfolio value.
        
        Args:
            prices (dict, optional): Dictionary of prices {symbol: price}. Defaults to None.
        
        Returns:
            float: Total portfolio value
        """
        if prices is None:
            # Use latest values
            return self.cash + sum(pos['value'] for pos in self.positions.values())
        else:
            # Calculate with provided prices
            position_value = 0.0
            for symbol, position in self.positions.items():
                if symbol in prices:
                    position_value += position['quantity'] * prices[symbol]
                else:
                    # Use last known value
                    position_value += position['value']
            
            return self.cash + position_value
    
    def get_weights(self, prices=None):
        """
        Get current portfolio weights.
        
        Args:
            prices (dict, optional): Dictionary of prices {symbol: price}. Defaults to None.
        
        Returns:
            dict: Portfolio weights {symbol: weight}
        """
        logger.debug(f"Portfolio.get_weights called with prices of type: {type(prices)}")
        if isinstance(prices, pd.Series):
            logger.warning("Portfolio.get_weights received prices as a pandas Series. Converting to dict. This may indicate an issue upstream.")
            prices = prices.to_dict()
        elif prices is not None and not isinstance(prices, dict):
            logger.error(f"Portfolio.get_weights received prices of unexpected type: {type(prices)}. Expected dict or None.")
            # Potentially raise an error or handle as if prices were None
            prices = None # Fallback to using stored values

        total_value = self.get_total_value(prices) # prices here is now guaranteed to be a dict or None
        
        if total_value == 0:
            # This can happen if initial capital is 0 or all assets are valueless and no cash
            logger.warning("Total portfolio value is 0. Returning empty weights.")
            return {asset: 0.0 for asset in self.positions.keys()} | {'Cash': 1.0 if self.cash == 0 and not self.positions else 0.0} 

        weights = {}
        
        # Calculate position weights
        for symbol, position in self.positions.items():
            if prices is not None and symbol in prices:
                value = position['quantity'] * prices[symbol]
            else:
                # Use last known value if prices not provided or symbol not in current prices
                value = position['value'] 
            
            weights[symbol] = value / total_value
        
        # Add cash weight, ensure it's not negative due to float precision with total_value
        cash_weight = self.cash / total_value if total_value else 0 # Avoid division by zero if total_value became zero after check
        weights['Cash'] = max(0.0, cash_weight) # Ensure cash weight isn't negative

        # Normalize weights to sum to 1 if necessary (e.g. due to floating point issues or fallback logic)
        current_sum = sum(weights.values())
        if not np.isclose(current_sum, 1.0) and current_sum != 0:
            logger.debug(f"Normalizing weights. Current sum: {current_sum}")
            for k in weights:
                weights[k] = weights[k] / current_sum
        
        return weights
    
    def get_history(self):
        """
        Get portfolio history.
        
{{ ... }}
            dict: Portfolio history
        """
        return self.history
    
    def get_position_history(self):
        """
        Get position history as a DataFrame, sorted by date.

        Returns:
            DataFrame: Position history with columns for each asset and 'Cash',
                       indexed by date and sorted chronologically.
        """
        if not self.history:
            return pd.DataFrame()

        position_history_records = []
        
        # Sort history by date before processing to ensure chronological order
        sorted_history = sorted(self.history.items())

        for date, snapshot in sorted_history:
            positions = snapshot.get('positions', {})
            # Safely get position values
            position_data = {symbol: pos.get('value', 0) for symbol, pos in positions.items()}
            position_data['Cash'] = snapshot.get('cash', 0)
            position_data['Date'] = date
            position_history_records.append(position_data)
        
        if not position_history_records:
            return pd.DataFrame()

        # Create DataFrame and ensure it's sorted by date index
        df = pd.DataFrame(position_history_records).set_index('Date')
        df.index = pd.to_datetime(df.index)
        return df.sort_index()
    
    def get_value_history(self):
        """Return portfolio total value history as a pandas Series (sorted by date)."""
        if not self.history:
            return pd.Series()
        values = pd.Series({date: snap['total_value'] for date, snap in self.history.items()})
        return values.sort_index()

    def get_returns_series(self):
        """
        Get portfolio returns as a Series.
        
        Returns:
            Series: Portfolio returns
        """
        if len(self.history) < 2:
            return pd.Series()
        
        # Extract portfolio values
        values = pd.Series({date: snapshot['total_value'] for date, snapshot in self.history.items()})
        values = values.sort_index()
        
        # Calculate returns
        returns = values.pct_change().dropna()
        
        return returns
    
    def get_drawdowns(self):
        """
        Calculate drawdowns.
        
        Returns:
            Series: Drawdowns
        """
        returns = self.get_returns_series()
        
        if returns.empty:
            return pd.Series()
        
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()
        
        # Calculate running maximum
        running_max = cum_returns.cummax()
        
        # Calculate drawdowns
        drawdowns = (cum_returns / running_max) - 1
        
        return drawdowns
    
    def __str__(self):
        """String representation of portfolio."""
        total_value = self.get_total_value()
        
        output = [
            f"Portfolio Summary:",
            f"Cash: ${self.cash:,.2f}",
            f"Positions: {len(self.positions)}",
            f"Total Value: ${total_value:,.2f}"
        ]
        
        if self.positions:
            output.append("\nPositions:")
            for symbol, position in self.positions.items():
                output.append(f"  {symbol}: {position['quantity']} shares, ${position['value']:,.2f}")
        
        return "\n".join(output)
