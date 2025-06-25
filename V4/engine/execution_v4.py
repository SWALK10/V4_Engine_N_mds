"""
engine/execution_v4.py
Order execution engine for asset allocation backtesting (CPS v4 compliant).

This module handles the execution of trading orders, applying commission and slippage
based on parameters sourced exclusively from the CPS_v4 settings system.

CPS_v4 Parameters Required:
- strategy:
    - commission_rate (float): The rate used to calculate commission for trades.
    - slippage_rate (float): The rate used to model slippage for trades.
- backtest:
    - initial_capital (float): The starting capital for the backtest.

If any of these parameters are missing from their respective sections in the
CPS_v4 settings, the module will raise a ValueError and halt execution.

The PercentSlippageModel and PercentCommissionModel within this module are
initialized using these module-level CPS_v4 parameters. The ExecutionEngine
is initialized using the module-level initial_capital.
"""

import pandas as pd
import numpy as np
from datetime import date
import logging

# Use package-qualified imports to ensure proper resolution
from v4.engine.portfolio_v4 import Portfolio
from v4.engine.orders_v4 import Order, Trade, TradeLog
# --- CPS v4 Integration ---
from v4.settings.settings_CPS_v4 import load_settings
settings = load_settings()

# Attempt to pull commission and slippage from the more granular [strategy]
# section first.  If they are not defined fall back to the generic values
# in the [backtest] section so that tests can run even when the strategy
# section is omitted in early templates.

# Required core backtest parameters
backtest_cfg = settings.get('backtest', {})

# Strategy-level overrides (optional)
strategy_cfg = settings.get('strategy', {})

commission_rate = strategy_cfg.get('commission_rate', backtest_cfg.get('commission_rate'))
slippage_rate   = strategy_cfg.get('slippage_rate',   backtest_cfg.get('slippage_rate'))
initial_capital = backtest_cfg.get('initial_capital')

# Validate we have the essentials; raise if still missing so that failure is
# explicit.
missing = []
if commission_rate is None:
    missing.append('commission_rate')
if slippage_rate is None:
    missing.append('slippage_rate')
if initial_capital is None:
    missing.append('initial_capital')

if missing:
    raise ValueError(f"Missing required CPS v4 parameter(s) in settings: {', '.join(missing)}")
# --- END CPS v4 Integration ---

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SlippageModel:
    """Base class for slippage models."""
    def calculate_slippage(self, order, price):
        """Calculate slippage for an order."""
        raise NotImplementedError("Subclasses must implement calculate_slippage")

class PercentSlippageModel(SlippageModel):
    """Percentage-based slippage model. Uses module-level slippage_rate from CPS_v4 settings."""
    def __init__(self):
        """
        Initialize the slippage model.
        The slippage_rate is sourced from module-level CPS_v4 settings.
        """
        self.slippage_rate = slippage_rate  # Uses module-level variable
        
    @property
    def rate(self):
        """Get the slippage rate."""
        return self.slippage_rate
    
    def calculate_slippage(self, order, price):
        """
        Calculate slippage for an order.
        
        Args:
            order (Order): Order
            price (float): Current price
            
        Returns:
            float: Execution price with slippage
        """
        # Apply slippage in the direction of the trade
        if order.quantity > 0:
            # Buy order: price increases
            execution_price = price * (1 + self.slippage_rate)
        else:
            # Sell order: price decreases
            execution_price = price * (1 - self.slippage_rate)
        
        return execution_price

class CommissionModel:
    """Base class for commission models."""
    def calculate_commission(self, order, execution_price):
        """Calculate commission for an order."""
        raise NotImplementedError("Subclasses must implement calculate_commission")

class PercentCommissionModel(CommissionModel):
    """Percentage-based commission model. Uses module-level commission_rate from CPS_v4 settings."""
    def __init__(self):
        """
        Initialize the commission model.
        The commission_rate is sourced from module-level CPS_v4 settings.
        """
        self.commission_rate = commission_rate  # Uses module-level variable
        
    @property
    def rate(self):
        """Get the commission rate."""
        return self.commission_rate
    
    def calculate_commission(self, order, execution_price):
        """
        Calculate commission for an order.
        
        Args:
            order (Order): Order
            execution_price (float): Execution price
            
        Returns:
            float: Commission amount
        """
        return abs(order.quantity * execution_price * self.commission_rate)

class ExecutionEngine:
    """
    Execution engine for handling order execution.
    """
    def __init__(self, commission_model=None, slippage_model=None):
        """
        Initialize execution engine.
        Initial capital is sourced from module-level CPS_v4 settings.
        
        Args:
            commission_model (CommissionModel): Commission model to use. If None, a default PercentCommissionModel is created.
            slippage_model (SlippageModel): Slippage model to use. If None, a default PercentSlippageModel is created.
        """
        # Create portfolio using module-level initial_capital from CPS_v4
        self.portfolio = Portfolio()
        
        # Create trade log
        self.trade_log = TradeLog()
        
        # Set commission model
        if commission_model is None:
            # --- CPS v4: Use module-level rate ---
            self.commission_model = PercentCommissionModel()  # Uses module-level rate from CPS_v4
        else:
            self.commission_model = commission_model
        
        # Set slippage model
        if slippage_model is None:
            # --- CPS v4: Use module-level rate ---
            self.slippage_model = PercentSlippageModel()  # Uses module-level rate from CPS_v4
        else:
            self.slippage_model = slippage_model
        
        logger.debug(f"Initialized execution engine with ${initial_capital:,.2f} capital (CPS v4 rates: commission={commission_rate}, slippage={slippage_rate})")
    
    def validate_sell_order(self, order, prices, execution_date):
        """
        Validate a sell order before execution.
        
        Args:
            order (Order): Sell order to validate
            prices (dict): Current prices
            execution_date (date): Execution date
            
        Returns:
            tuple: (is_valid, adjusted_order, error_message)
        """
        symbol = order.symbol
        date_str = f"[{execution_date.strftime('%Y-%m-%d')}]" if execution_date else ""
        
        if symbol not in prices:
            return False, None, f"{date_str} No price for {symbol}, skipping sell order"
        
        # Get current position
        position = self.portfolio.get_position(symbol)
        if not position or position['quantity'] <= 0:
            return False, None, f"{date_str} No position to sell for {symbol}"
        
        # Calculate absolute quantity (order.quantity is negative for sells)
        sell_quantity = abs(order.quantity)
        current_quantity = position['quantity']
        
        # Check if we have enough shares to sell
        if sell_quantity > current_quantity:
            # Adjust order to max available
            adjusted_order = Order(
                symbol=order.symbol,
                quantity=-current_quantity,  # Keep it negative for sell
                price=order.price,
                order_type=order.order_type,
                order_date=order.order_date
            )
            return True, adjusted_order, f"{date_str} Adjusted sell order for {symbol} from {sell_quantity} to {current_quantity} shares"
        
        return True, order, None
    
    def execute_orders(self, orders, execution_date, prices):
        """
        Execute orders with enhanced validation and error handling.
        
        Args:
            orders (list): List of Order objects
            execution_date (date): Execution date
            prices (dict): Dictionary of prices {symbol: price}
            
        Returns:
            list: List of executed Trade objects
        """
        if not orders:
            return []
            
        date_str = f"[{execution_date.strftime('%Y-%m-%d')}]" if execution_date else ""
        logger.debug(f"{date_str} Executing {len(orders)} orders")
        
        executed_trades = []
        
        # Separate buy and sell orders
        sell_orders = [order for order in orders if order.quantity < 0]
        buy_orders = [order for order in orders if order.quantity > 0]
        
        # Track total cash that will be freed up by sells
        total_freed_cash = 0.0
        sell_trades = []
        
        # First process all sell orders to calculate freed cash
        for order in sell_orders:
            symbol = order.symbol
            
            # Validate sell order
            is_valid, validated_order, message = self.validate_sell_order(order, prices, execution_date)
            if not is_valid:
                if message:  # Only log if there's a message
                    logger.warning(message)
                continue
                
            if validated_order != order:
                logger.warning(message)  # Log adjustment message
                order = validated_order
            
            price = prices[symbol]
            execution_price = self.slippage_model.calculate_slippage(order, price)
            commission = self.commission_model.calculate_commission(order, execution_price)
            
            # For sell orders, amount is negative (cash inflow)
            amount = order.quantity * execution_price - commission  # Note: order.quantity is negative
            
            # Create trade
            trade = Trade(
                order=order,
                execution_date=execution_date,
                execution_price=execution_price,
                commission=commission,
                amount=amount
            )
            
            # Track freed cash (negative amount means cash inflow)
            total_freed_cash += abs(amount)
            sell_trades.append(trade)
        
        # Execute all sell trades first
        for trade in sell_trades:
            success, pnl = self.portfolio.update_from_trade(trade)
            if success:
                trade.pnl = pnl
                executed_trades.append(trade)
                logger.debug(f"[{execution_date.strftime('%Y-%m-%d')}] Sold {abs(trade.quantity)} shares of {trade.symbol} at ${trade.execution_price:.2f}, P&L: ${pnl:,.2f}")
                self.trade_log.add_trade(trade)
        
        # Cash from sells is already updated in the portfolio by update_from_trade
        
    def validate_buy_order(self, order, prices, execution_date, available_cash):
        """
        Validate a buy order before execution.
        
        Args:
            order (Order): Buy order to validate
            prices (dict): Current prices
            execution_date (date): Execution date
            available_cash (float): Available cash for the order
            
        Returns:
            tuple: (is_valid, adjusted_order, error_message)
        """
        symbol = order.symbol
        date_str = f"[{execution_date.strftime('%Y-%m-%d')}]" if execution_date else ""
        
        if symbol not in prices:
            return False, None, f"{date_str} No price for {symbol}, skipping buy order"
        
        price = prices[symbol]
        execution_price = self.slippage_model.calculate_slippage(order, price)
        commission = self.commission_model.calculate_commission(order, execution_price)
        
        # Calculate total amount needed
        total_amount = (order.quantity * execution_price) + commission
        
        # Check if we have enough cash
        if total_amount > available_cash:
            # Try to adjust quantity to fit available cash
            if available_cash <= commission:
                return False, None, f"{date_str} Insufficient cash for even 1 share of {symbol} (commission: ${commission:.2f})"
            
            # Calculate max shares we can buy with available cash (after commission)
            max_shares = int((available_cash - commission) / execution_price)
            
            if max_shares <= 0:
                return False, None, f"{date_str} Insufficient cash for even 1 share of {symbol} (price: ${execution_price:.2f}, commission: ${commission:.2f})"
            
            # Create adjusted order
            adjusted_order = Order(
                symbol=order.symbol,
                quantity=max_shares,
                price=order.price,
                order_type=order.order_type,
                order_date=order.order_date
            )
            
            return True, adjusted_order, f"{date_str} Adjusted buy order for {symbol} from {order.quantity} to {max_shares} shares due to cash constraints"
        
        return True, order, None
        
    def execute_orders(self, orders, execution_date, prices):
        """
        Execute orders with enhanced validation and error handling.
        
        Args:
            orders (list): List of Order objects
            execution_date (date): Execution date
            prices (dict): Dictionary of prices {symbol: price}
            
        Returns:
            list: List of executed Trade objects
        """
        if not orders:
            return []
            
        date_str = f"[{execution_date.strftime('%Y-%m-%d')}]" if execution_date else ""
        logger.debug(f"{date_str} Executing {len(orders)} orders")
        
        executed_trades = []
        
        # Separate buy and sell orders
        sell_orders = [order for order in orders if order.quantity < 0]
        buy_orders = [order for order in orders if order.quantity > 0]
        
        # Track total cash that will be freed up by sells
        total_freed_cash = 0.0
        sell_trades = []
        
        # First process all sell orders to calculate freed cash
        for order in sell_orders:
            symbol = order.symbol
            
            # Validate sell order
            is_valid, validated_order, message = self.validate_sell_order(order, prices, execution_date)
            if not is_valid:
                if message:  # Only log if there's a message
                    logger.warning(message)
                continue
                
            if validated_order != order:
                logger.warning(message)  # Log adjustment message
                order = validated_order
            
            price = prices[symbol]
            execution_price = self.slippage_model.calculate_slippage(order, price)
            commission = self.commission_model.calculate_commission(order, execution_price)
            
            # For sell orders, amount is negative (cash inflow)
            amount = order.quantity * execution_price - commission  # Note: order.quantity is negative
            
            # Create trade
            trade = Trade(
                order=order,
                execution_date=execution_date,
                execution_price=execution_price,
                commission=commission,
                amount=amount
            )
            
            # Track freed cash (negative amount means cash inflow)
            total_freed_cash += abs(amount)
            sell_trades.append(trade)
        
        # Execute all sell trades first
        for trade in sell_trades:
            success, pnl = self.portfolio.update_from_trade(trade)
            if success:
                trade.pnl = pnl
                executed_trades.append(trade)
                logger.debug(f"{date_str} Sold {abs(trade.quantity)} shares of {trade.symbol} at ${trade.execution_price:.2f}, P&L: ${pnl:,.2f}")
                self.trade_log.add_trade(trade)
        
        # Cash from sells is already updated in the portfolio by update_from_trade
        
        # Now process buy orders with updated cash position
        for order in buy_orders:
            symbol = order.symbol
            
            # Validate buy order
            is_valid, validated_order, message = self.validate_buy_order(order, prices, execution_date, self.portfolio.cash)
            if not is_valid:
                if message:  # Only log if there's a message
                    logger.warning(message)
                continue
                
            if validated_order != order:
                logger.warning(message)  # Log adjustment message
                order = validated_order
            
            # Recalculate with potentially adjusted order
            price = prices[symbol]
            execution_price = self.slippage_model.calculate_slippage(order, price)
            commission = self.commission_model.calculate_commission(order, execution_price)
            amount = order.quantity * execution_price + commission
            
            # Create trade for buy order
            trade = Trade(
                order=order,
                execution_date=execution_date,
                execution_price=execution_price,
                commission=commission,
                amount=amount
            )
            
            # Update portfolio for buy order
            success, _ = self.portfolio.update_from_trade(trade)
            if not success:
                logger.error(f"{date_str} Failed to execute buy order for {symbol}")
                continue
                
            logger.debug(f"{date_str} Bought {order.quantity} shares of {symbol} at ${execution_price:.2f} (total: ${amount:,.2f})")
            
            # Add to trade log
            self.trade_log.add_trade(trade)
            
            # Add to executed trades
            executed_trades.append(trade)
        
        return executed_trades
    
    def get_portfolio_state(self):
        """
        Get current portfolio state.
        
        Returns:
            Portfolio: Current portfolio
        """
        return self.portfolio
    
    def get_trade_log(self):
        """
        Get trade log.
        
        Returns:
            TradeLog: Trade log
        """
        return self.trade_log
