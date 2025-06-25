"""
engine/allocation_v4.py
Allocation module (CPS v4 compliant).
Handles position comparison and order generation.
# CPS v4 conversion complete: 2025-06-06

Logging for order/cash/portfolio/trade adjustments is set to DEBUG level. These messages will only appear when BACKTEST_LOG_LEVEL is set to DEBUG or lower.

CRITICAL: commission_rate and slippage_rate are now sourced ONLY from CPS v4 settings. No local fallback defaults are allowed. If missing, this module will raise an error and execution will halt.
"""

import pandas as pd
import logging
# Use package-qualified import to ensure correct resolution within v4 package
from v4.engine.orders_v4 import Order

# --- CPS v4 Integration ---
from v4.settings.settings_CPS_v4 import load_settings
settings = load_settings()
try:
    backtest_params = settings['backtest']
    commission_rate = backtest_params['commission_rate']
    slippage_rate = backtest_params['slippage_rate']
except KeyError as e:
    logger.error(f"Missing required parameter in CPS_v4 settings: {e}")
    raise ValueError(f"Missing required parameter in CPS_v4 settings") from e
# --- END CPS v4 Integration ---

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_positions(current_positions, target_allocations, portfolio_value, prices):
    # Create a copy to avoid modifying the original dictionary passed to the function
    target_allocations = target_allocations.copy()
    """
    Compare current positions to target allocations.
    
    Args:
        current_positions (dict): Current positions {symbol: position_dict}
        target_allocations (dict): Target allocations {symbol: weight}
        portfolio_value (float): Total portfolio value
        prices (dict): Current prices {symbol: price}
        
    Returns:
        dict: Dollar changes required {symbol: dollar_change}
    """
    # Calculate current allocations
    current_allocations = {}
    for symbol, position in current_positions.items():
        if symbol in prices:
            current_allocations[symbol] = (position['quantity'] * prices[symbol]) / portfolio_value
        else:
            logger.warning(f"No price for {symbol}, using last known value")
            current_allocations[symbol] = position['value'] / portfolio_value
    
    # Calculate dollar changes
    dollar_changes = {}
    
    # Handle symbols in target but not in current
    for symbol in target_allocations:
        if symbol not in current_allocations:
            current_allocations[symbol] = 0.0
    
    # Handle symbols in current but not in target
    for symbol in current_allocations:
        if symbol not in target_allocations:
            target_allocations[symbol] = 0.0
    
    # Calculate dollar changes
    for symbol in set(current_allocations.keys()) | set(target_allocations.keys()):
        current_weight = current_allocations.get(symbol, 0.0)
        target_weight = target_allocations.get(symbol, 0.0)
        
        # Calculate dollar change
        dollar_change = (target_weight - current_weight) * portfolio_value
        
        # Only include significant changes
        if abs(dollar_change) > 0.01:
            dollar_changes[symbol] = dollar_change
    
    return dollar_changes

def generate_orders(dollar_changes, prices, order_date=None, available_cash=None, current_positions=None):
    """
    Convert dollar changes into specific order objects with cash constraints awareness.
    
    Args:
        dollar_changes (dict): Required dollar changes {symbol: dollar_change}
        prices (dict): Current prices {symbol: price}
        order_date (date, optional): Date for the orders
        available_cash (float, optional): Available cash for buys
        current_positions (dict, optional): Current positions {symbol: position_dict} for validation
        
    Returns:
        list: Order objects
    """
    # Add a small cash buffer (0.1%) to avoid rounding issues
    cash_buffer_factor = 0.999
    orders = []
    date_str = f"[{order_date.strftime('%Y-%m-%d')}] " if order_date else ""
    
    # First, separate buys and sells with validation
    buy_changes = {}
    sell_changes = {}
    
    for symbol, change in dollar_changes.items():
        if symbol not in prices:
            logger.warning(f"{date_str}No price available for {symbol}, skipping")
            continue
            
        if change > 0:
            buy_changes[symbol] = change
        elif change < 0 and current_positions and symbol in current_positions:
            # Only add to sell_changes if we have the position
            current_qty = current_positions[symbol]['quantity']
            if current_qty > 0:
                sell_changes[symbol] = change
            else:
                logger.warning(f"{date_str}No position to sell for {symbol}, skipping")
        elif change < 0:
            logger.warning(f"{date_str}No position to sell for {symbol} (no position data), skipping")
    
    # Track cash freed up by sells and used by buys
    cash_freed = 0.0
    cash_used = 0.0
    
    # Process sells first (they free up cash)
    for symbol, dollar_change in sell_changes.items():
        price = prices[symbol]
        
        # Calculate target quantity (negative for sells)
        target_quantity = dollar_change / price
        
        # Get current position quantity
        current_qty = current_positions[symbol]['quantity'] if current_positions and symbol in current_positions else 0
        
        # Ensure we don't sell more than we own
        max_sellable = abs(round(target_quantity))
        if max_sellable > current_qty:
            logger.warning(f"{date_str}Adjusting sell order for {symbol} from {max_sellable} to {current_qty} shares (insufficient position)")
            max_sellable = current_qty
            
        # Skip if no shares to sell
        if max_sellable <= 0:
            logger.warning(f"{date_str}No shares to sell for {symbol}, skipping")
            continue
            
        # Use the adjusted quantity
        quantity = -max_sellable  # Negative for sells
        
        # Skip if quantity is zero
        if quantity == 0:
            continue
        
        # Calculate actual dollar amount after rounding (including commission)
        actual_dollars = abs(quantity * price)
        commission = actual_dollars * commission_rate
        
        # Update cash freed (sell orders free up cash minus commission)
        cash_freed += actual_dollars - commission
        
        # Create order
        order = Order(symbol, quantity, order_date)
        orders.append(order)
    
    # Calculate total available cash for buys (initial + freed from sells)
    total_available_cash = (available_cash or 0.0) + cash_freed
    
    if total_available_cash <= 0 or not buy_changes:
        return orders  # No cash for buys or no buy orders
    
    # First pass: Calculate estimated costs including commission and slippage
    buy_order_estimates = {}
    total_estimated_cost = 0.0
    
    for symbol, dollar_change in buy_changes.items():
        if symbol not in prices:
            continue
            
        price = prices[symbol]
        # Apply slippage to price (buy orders pay higher price)
        adjusted_price = price * (1 + slippage_rate)
        
        # Calculate quantity
        quantity = dollar_change / price  # Use original price for quantity calculation
        quantity = round(quantity)  # Round to whole shares
        
        if quantity <= 0:
            continue
            
        # Calculate actual cost with rounded quantity and adjusted price
        cost = quantity * adjusted_price
        commission_cost = cost * commission_rate
        total_cost = cost + commission_cost
        
        # Check if a single share is too expensive
        single_share_cost = adjusted_price * (1 + commission_rate)
        
        buy_order_estimates[symbol] = {
            'quantity': quantity,
            'price': price,
            'adjusted_price': adjusted_price,
            'cost': cost,
            'commission': commission_cost,
            'total_cost': total_cost,
            'single_share_cost': single_share_cost,
            'dollar_change': dollar_change  # Store for prioritization
        }
        
        total_estimated_cost += total_cost
    
    # Second pass: Scale down if necessary and create orders
    if total_estimated_cost > total_available_cash * cash_buffer_factor and buy_order_estimates:
        # Apply buffer to available cash
        buffered_cash = total_available_cash * cash_buffer_factor
        date_str = f"[{order_date.strftime('%Y-%m-%d')}] " if order_date else ""
        logger.debug(f"{date_str}Available cash (${buffered_cash:,.2f}) is less than estimated cost (${total_estimated_cost:,.2f})")
        
        # Calculate scaling factor to proportionally reduce all orders
        scaling_factor = buffered_cash / total_estimated_cost
        
        # Sort orders by priority (highest dollar change first)
        prioritized_orders = sorted(
            buy_order_estimates.items(), 
            key=lambda x: x[1]['dollar_change'], 
            reverse=True
        )
        
        # First pass: Try to allocate proportionally
        adjusted_orders = {}
        remaining_cash = buffered_cash
        
        for symbol, estimate in prioritized_orders:
            # Scale down quantity proportionally
            scaled_quantity = int(estimate['quantity'] * scaling_factor)
            
            # Ensure at least one share if possible
            if scaled_quantity < 1 and estimate['single_share_cost'] <= remaining_cash:
                scaled_quantity = 1
            
            if scaled_quantity > 0:
                # Calculate cost with adjusted quantity
                adjusted_cost = scaled_quantity * estimate['adjusted_price']
                adjusted_commission = adjusted_cost * commission_rate
                adjusted_total = adjusted_cost + adjusted_commission
                
                # Store adjusted order if we can afford it
                if adjusted_total <= remaining_cash:
                    adjusted_orders[symbol] = {
                        'quantity': scaled_quantity,
                        'cost': adjusted_cost,
                        'commission': adjusted_commission,
                        'total': adjusted_total,
                        'original': estimate['quantity']
                    }
                    remaining_cash -= adjusted_total
        
        # Second pass: Use remaining cash for additional shares if possible
        if remaining_cash > 0:
            for symbol, estimate in prioritized_orders:
                if symbol in adjusted_orders and estimate['single_share_cost'] <= remaining_cash:
                    # See how many more shares we can buy
                    additional_shares = int(remaining_cash / estimate['single_share_cost'])
                    if additional_shares > 0:
                        # Don't exceed original quantity
                        max_additional = estimate['quantity'] - adjusted_orders[symbol]['quantity']
                        additional_shares = min(additional_shares, max_additional)
                        
                        if additional_shares > 0:
                            # Update quantity and costs
                            adjusted_orders[symbol]['quantity'] += additional_shares
                            additional_cost = additional_shares * estimate['adjusted_price']
                            additional_commission = additional_cost * commission_rate
                            additional_total = additional_cost + additional_commission
                            
                            adjusted_orders[symbol]['cost'] += additional_cost
                            adjusted_orders[symbol]['commission'] += additional_commission
                            adjusted_orders[symbol]['total'] += additional_total
                            
                            remaining_cash -= additional_total
        
        # Create orders based on adjusted quantities
        for symbol, adjusted in adjusted_orders.items():
            if adjusted['quantity'] > 0:
                if adjusted['quantity'] < adjusted['original']:
                    date_str = f"[{order_date.strftime('%Y-%m-%d')}] " if order_date else ""
                    logger.debug(f"{date_str}Adjusted order from {adjusted['original']} to {adjusted['quantity']} shares of {symbol} due to cash constraints")
                
                # Create order with proper parameters
                price = prices.get(symbol)
                if price is None:
                    logger.warning(f"No price available for {symbol} when creating order, using adjusted price")
                    price = adjusted.get('adjusted_price', 0)
                
                # Always pass parameters in correct order: symbol, quantity, price, order_type, order_date
                order = Order(symbol, adjusted['quantity'], price, 'MARKET', order_date)
                orders.append(order)
                
                # Update cash tracking
                cash_used += adjusted['total']
    else:
        # We have enough cash for all orders, create them as is
        for symbol, estimate in buy_order_estimates.items():
            price = prices.get(symbol)
            if price is None:
                logger.warning(f"No price available for {symbol} when creating order, using estimate")
                price = estimate.get('price', 0)
                
            # Always pass parameters in correct order: symbol, quantity, price, order_type, order_date
            order = Order(symbol, estimate['quantity'], price, 'MARKET', order_date)
            orders.append(order)
            
            # Update cash tracking
            total_available_cash -= estimate['total_cost']
            cash_used += estimate['total_cost']
    
    return orders

def calculate_rebalance_orders(portfolio, target_allocations, prices, order_date=None):
    """
    Calculate orders required to rebalance a portfolio with cash awareness.
    
    Args:
        portfolio (Portfolio): Portfolio object
        target_allocations (dict): Target allocations {symbol: weight}
        prices (dict): Current prices {symbol: price}
        order_date (date, optional): Date for the orders
        
    Returns:
        list: Order objects
    """
    date_str = f"[{order_date.strftime('%Y-%m-%d')}] " if order_date else ""
    
    # Get current positions and portfolio value
    current_positions = portfolio.get_positions()
    portfolio_value = portfolio.get_total_value(prices)
    
    logger.debug(f"{date_str}Portfolio value before rebalancing: ${portfolio_value:,.2f}")
    logger.debug(f"{date_str}Current positions: {current_positions}")
    
    # Calculate required dollar changes
    dollar_changes = compare_positions(
        current_positions=current_positions,
        target_allocations=target_allocations,
        portfolio_value=portfolio_value,
        prices=prices
    )
    
    logger.debug(f"{date_str}Calculated dollar changes: {dollar_changes}")
    
    # Generate orders with cash awareness and position validation
    available_cash = portfolio.cash  # Get available cash from portfolio
    
    logger.debug(f"{date_str}Available cash for rebalancing: ${available_cash:,.2f}")
    
    orders = generate_orders(
        dollar_changes=dollar_changes,
        prices=prices,
        order_date=order_date,
        available_cash=available_cash,
        current_positions=current_positions  # Pass current positions for validation
    )
    
    logger.debug(f"{date_str}Generated {len(orders)} orders for execution")
    
    return orders
