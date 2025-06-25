# Signal to Trading Connection Implementation (Complete Code Version)

## Overview
[Previous overview content...]

## Complete Implementation Code

### 1. Signal Phase Script (`run_signal_phase.py`)
```python
import os
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
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
    """Run the signal generation phase and save output to a file."""
    logger.info("[MILESTONE] Starting Signal Generation Phase")
    
    # 1. Load settings
    logger.info("Loading settings...")
    settings = load_settings()
    
    # 2. Load data
    logger.info("Loading price data...")
    price_data = load_data_for_backtest()
    
    # 3. Create signal generator
    logger.info("Creating signal generator...")
    signal_generator = create_signal_generator(
        model_name=settings.get('model', 'ema_allocation'),
        settings=settings
    )
    
    # 4. Generate signals for all dates
    logger.info("Generating signals...")
    signals = signal_generator.generate_signals(price_data)
    
    # 5. Create output directory if it doesn't exist
    output_dir = _project_root / "v4_trace_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # 6. Save signals to file
    output_file = output_dir / "signals_output.parquet"
    logger.info(f"Saving signals to {output_file}...")
    signals.to_parquet(str(output_file))
    
    # 7. Also save a CSV version for easier inspection
    csv_file = output_dir / "signals_output.csv"
    signals.to_csv(str(csv_file))
    
    logger.info(f"Signal generation complete. Output saved to {output_file}")
    return str(output_file)

if __name__ == "__main__":
    run_signal_phase()
```

[Remaining sections with full code implementations...]
