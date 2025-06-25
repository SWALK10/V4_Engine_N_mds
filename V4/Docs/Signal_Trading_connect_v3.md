# Signal to Trading Connection Implementation (Complete Code Version)

## 1. Signal Phase Script (`run_signal_phase.py`)
```python
import os
import sys
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import core V4 components
from v4.settings.settings_CPS_v4 import load_settings
from v4.engine.data_loader_v4 import load_data_for_backtest
from v4.engine.signal_generator_v4 import create_signal_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_signal_phase():
    """Run signal generation phase and save output."""
    logger.info("[MILESTONE] Starting Signal Generation Phase")
    
    # Load settings and data
    settings = load_settings()
    price_data = load_data_for_backtest()
    
    # Create and run signal generator
    signal_generator = create_signal_generator(
        model_name=settings.get('model', 'ema_allocation'),
        settings=settings
    )
    signals = signal_generator.generate_signals(price_data)
    
    # Save outputs
    output_dir = _project_root / "v4_trace_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = output_dir / "signals_output.parquet"
    signals.to_parquet(str(output_file))
    
    csv_file = output_dir / "signals_output.csv"
    signals.to_csv(str(csv_file))
    
    logger.info(f"Signal generation complete. Output saved to {output_file}")
    return str(output_file)

if __name__ == "__main__":
    run_signal_phase()
```

## 2. Trading Phase Script (`run_trading_phase.py`)
```python
import os
import sys
from pathlib import Path
import pandas as pd
import logging

# Add project root to path
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import core V4 components
from v4.settings.settings_CPS_v4 import load_settings
from v4.engine.data_loader_v4 import load_data_for_backtest
from v4.engine.backtest_v4 import BacktestEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_trading_phase(signals_file=None):
    """Run trading phase using signals from file."""
    logger.info("[MILESTONE] Starting Trading Phase")
    
    # Load settings and data
    settings = load_settings()
    price_data = load_data_for_backtest()
    
    # Load signals
    if signals_file is None:
        signals_file = _project_root / "v4_trace_outputs" / "signals_output.parquet"
    
    if not Path(signals_file).exists():
        logger.error(f"Signals file {signals_file} not found!")
        sys.exit(1)
    
    try:
        signals = pd.read_parquet(signals_file)
        logger.info(f"Loaded signals with shape {signals.shape}")
    except Exception as e:
        logger.error(f"Error loading signals file: {e}")
        sys.exit(1)
    
    # Run backtest
    engine = BacktestEngine(settings)
    results = engine.run_backtest_with_signals(signals, price_data)
    
    # Save results
    output_dir = _project_root / "v4_trace_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    allocation_history = results.get('allocation_history')
    trade_log = results.get('trade_log')
    
    if allocation_history is not None:
        allocation_file = output_dir / "allocation_history.csv"
        allocation_history.to_csv(str(allocation_file))
        logger.info(f"Saved allocation history to {allocation_file}")
    
    if trade_log is not None:
        trades_file = output_dir / "trade_log.csv"
        trade_log.to_csv(str(trades_file))
        logger.info(f"Saved trade log to {trades_file}")
    
    logger.info("Trading phase complete.")
    return results

if __name__ == "__main__":
    run_trading_phase()

```

## 3. Backtest Engine Modifications (`backtest_v4.py`)

```python
class BacktestEngine:
    # ... existing code ...

    def run_backtest_with_signals(self, signals, price_data):
        """Run backtest using pre-computed signals.
        
        Args:
            signals (pd.DataFrame): Pre-computed signals with datetime index
            price_data (pd.DataFrame): Price data for backtest period
        
        Returns:
            dict: Results including portfolio, allocation_history, and trade_log
        """
        # Initialize components
        self._initialize_components(price_data)
        
        # Extract date range
        start_date = price_data.index.min()
        end_date = price_data.index.max()
        date_range = price_data.index
        
        # Initialize tracking structures
        portfolio = self.portfolio
        signal_history = pd.DataFrame(0, index=date_range, columns=price_data.columns)
        
        # Main backtest loop - use pre-computed signals
        for i, current_date in enumerate(date_range):
            # Check if we have a signal for this date
            if current_date in signals.index:
                current_signals = signals.loc[current_date]
                
                # Generate orders based on signals
                orders = self.allocation_model.generate_orders(
                    portfolio=portfolio,
                    signals=current_signals,
                    prices=price_data.loc[current_date],
                    current_date=current_date
                )
                
                # Execute trades
                if orders and not orders.empty:
                    trade_results = self.execution_model.execute_orders(
                        orders=orders,
                        prices=price_data.loc[current_date]
                    )
                    self.trade_log.append(trade_results)
                    
                    # Update portfolio
                    portfolio.update_holdings(
                        trade_results,
                        current_date,
                        price_data.loc[current_date]
                    )
                
                # Record signal history
                signal_history.loc[current_date] = current_signals
        
        # Generate and return results
        return {
            'portfolio': portfolio,
            'allocation_history': portfolio.get_position_history(),
            'trade_log': pd.concat(self.trade_log) if self.trade_log else None,
            'signal_history': signal_history
        }
```

Key changes from original implementation:
- Removes direct signal generation dependency
- Uses pre-computed signals from input DataFrame
- Maintains same interface for order generation and execution
- Preserves all existing logging and reporting functionality

## 4. Pipeline Orchestrator (`run_v4_pipeline.py`)

```python
import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Add project root to path
_script_path = Path(__file__).resolve()
_project_root = _script_path.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Import phase runners
from v4.run_signal_phase import run_signal_phase
from v4.run_trading_phase import run_trading_phase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_pipeline():
    """Run complete V4 pipeline."""
    start_time = datetime.now()
    logger.info(f"[MILESTONE] Starting V4 Pipeline at {start_time}")
    
    # Phase 1: Signal Generation
    logger.info("Running Signal Phase...")
    signals_file = run_signal_phase()
    
    # Phase 2: Trading
    logger.info("Running Trading Phase...")
    results = run_trading_phase(signals_file)
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"[MILESTONE] Pipeline complete! Duration: {duration}")
    
    return results

if __name__ == "__main__":
    run_pipeline()
```

Key Features:
- Coordinates execution of all phases
- Tracks and reports overall pipeline timing
- Maintains consistent logging format
- Can be extended to include additional phases
- Provides single entry point for the complete workflow

## 5. Batch File Update (`run_main_v4_prod2.bat`)

```batch
@echo off
REM ============================================
REM Script: run_main_v4_prod2.bat
REM Description: Super-stable launcher for V4 pipeline
REM ============================================

SETLOCAL

REM --- Paths ---
SET "PYTHON_EXE=F:\AI_Library\my_quant_env\Scripts\python.exe"
SET "SCRIPT_DIR=%~dp0"
SET "SCRIPT_PATH=%SCRIPT_DIR%v4\run_v4_pipeline.py"
SET "OUTPUT_DIR=%SCRIPT_DIR%v4_trace_outputs"

REM --- Ensure output directory exists ---
IF NOT EXIST "%OUTPUT_DIR%" (
    mkdir "%OUTPUT_DIR%"
)

REM --- Timestamp (YYYYMMDD_HHMMSS) ---
SET "TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
SET "TIMESTAMP=%TIMESTAMP: =0%"

REM --- Log files ---
SET "FULL_LOG=%OUTPUT_DIR%\full_%TIMESTAMP%.txt"
SET "FILTERED_LOG=%OUTPUT_DIR%\filtered_%TIMESTAMP%.txt"

echo [%TIME%] Running V4 pipeline (full log: "%FULL_LOG%" )

REM --- Run Python and capture output ---
(
    "%PYTHON_EXE%" "%SCRIPT_PATH%"
    SET "EXIT_CODE=%ERRORLEVEL%"
) > "%FULL_LOG%" 2>&1

REM --- Create filtered log ---
echo ===== FILTERED OUTPUT ===== > "%FILTERED_LOG%"
echo Run Time: %DATE% %TIME% >> "%FILTERED_LOG%"
echo. >> "%FILTERED_LOG%"
echo ===== MILESTONES ===== >> "%FILTERED_LOG%"
findstr /C:"[MILESTONE]" "%FULL_LOG%" >> "%FILTERED_LOG%" 2>nul
echo. >> "%FILTERED_LOG%"
echo ===== WARNINGS ^& ERRORS ===== >> "%FILTERED_LOG%"
findstr /C:"[ERROR]" /C:"[WARNING]" "%FULL_LOG%" >> "%FILTERED_LOG%" 2>nul
findstr /i "error warning exception traceback failed fatal" "%FULL_LOG%" >> "%FILTERED_LOG%" 2>nul

echo [%TIME%] V4 pipeline finished with exit code %EXIT_CODE%
echo Full log: "%FULL_LOG%"
echo Filtered log: "%FILTERED_LOG%"

ENDLOCAL
exit /b %EXIT_CODE%
```

Key Features:
- Robust error handling and logging
- Timestamped output files
- Filtered logs for easier debugging
- Maintains existing environment path configuration
- Preserves all original functionality while adapting to new pipeline structure
