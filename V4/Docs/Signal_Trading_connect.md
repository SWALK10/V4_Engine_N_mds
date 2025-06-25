# Signal to Trading Connection Implementation

## Overview
This document outlines the file-based decoupling approach for connecting the Signal Generation phase to the Trading/Portfolio phase in the V4 backtest engine. This implementation follows a modular architecture where each phase is independent and communicates through well-defined file interfaces.

## File Structure
```
project_root/
├── v4/
│   ├── run_signal_phase.py     # Signal generation script
│   ├── run_trading_phase.py    # Trading execution script
│   ├── run_v4_pipeline.py      # Pipeline orchestrator
│   └── engine/
│       └── backtest_v4.py      # Modified to accept pre-computed signals
├── v4_trace_outputs/           # Output directory for all phase outputs
│   ├── signals_output.parquet  # Signal phase output
│   ├── signals_output.csv      # Human-readable signals
│   ├── allocation_history.csv  # Trading phase output
│   └── trade_log.csv           # Trade execution log
└── run_main_v4_prod2.bat       # Updated batch file
```

## Implementation Details

### 1. Signal Phase (`run_signal_phase.py`)

This script handles the signal generation process and saves the output to a standardized file format.

**Key Features:**
- Loads price data using the existing data loader
- Generates signals using the configured signal generator
- Saves signals in both Parquet (efficient) and CSV (human-readable) formats
- Includes comprehensive logging for debugging

**Output File Format (`signals_output.parquet`):
- Index: DatetimeIndex (aligned with price data)
- Columns: One per asset (e.g., 'SPY', 'TLT')
- Values: Signal weights (0-1 for long-only, -1 to 1 for long-short)

### 2. Trading Phase (`run_trading_phase.py`)

This script loads pre-computed signals and executes the trading strategy.

**Key Features:**
- Loads signals from the specified file
- Validates signal data before processing
- Executes trades based on signal changes
- Generates trade logs and allocation history

### 3. Backtest Engine Modifications (`backtest_v4.py`)

Added new method to handle pre-computed signals:

```python
def run_backtest_with_signals(self, signals, price_data):
    """Run backtest using pre-computed signals.
    
    Args:
        signals (pd.DataFrame): Pre-computed signals with datetime index
        price_data (pd.DataFrame): Price data for the backtest period
        
    Returns:
        dict: Results including portfolio, allocation_history, and trade_log
    """
    # Implementation details...
```

### 4. Pipeline Orchestrator (`run_v4_pipeline.py`)

Coordinates the execution of all phases in sequence.

**Execution Flow:**
1. Run Signal Phase
2. Validate Signal Output
3. Run Trading Phase with Signal Output
4. Generate Final Reports

## Usage

### Running the Complete Pipeline
```bash
python v4/run_v4_pipeline.py
```

### Running Individual Phases

**Signal Generation Only:**
```bash
python v4/run_signal_phase.py
```

**Trading Only (with existing signals):**
```bash
python v4/run_trading_phase.py [path/to/signals.parquet]
```

### Batch Execution
```batch
call run_main_v4_prod2.bat
```

## Error Handling and Validation

### Signal File Validation
The trading phase performs the following validations:
1. File existence check
2. Required columns verification
3. Date range alignment with price data
4. Signal value validation (e.g., sum to 1 for long-only)

### Error Recovery
- Each phase is atomic - if one fails, previous outputs remain valid
- Detailed logs are saved in `v4_trace_outputs/`
- Intermediate files are preserved for debugging

## Performance Considerations

1. **File Formats:**
   - Parquet for efficient binary storage
   - CSV for manual inspection

2. **Memory Management:**
   - Each phase loads only the data it needs
   - Large DataFrames are processed in chunks when possible

3. **Parallel Processing:**
   - Phases can be run on separate machines
   - Input/output directories can be on fast storage

## Example Output Files

### signals_output.csv
```csv
date,SPY,TLT,SHY
2023-01-03,0.6,0.3,0.1
2023-01-04,0.55,0.35,0.1
...
```

### trade_log.csv
```csv
date,symbol,quantity,price,commission,side
2023-01-03,SPY,100,380.25,0.001,buy
2023-01-03,TLT,50,115.75,0.001,buy
...
```

### allocation_history.csv
```csv
date,SPY,TLT,SHY,Cash
2023-01-03,60.0,30.0,10.0,0.0
2023-01-04,55.0,35.0,10.0,0.0
...
```

## Troubleshooting

### Common Issues

1. **Missing Signal File**
   - Verify the signal phase completed successfully
   - Check file permissions in the output directory

2. **Date Mismatch**
   - Ensure signal dates align with price data
   - Check for timezone issues

3. **Signal Validation Errors**
   - Verify signal weights sum to 1 (for long-only)
   - Check for NaN or infinite values

## Future Enhancements

1. **Data Versioning**
   - Add hashes to output files for validation
   - Implement a simple versioning system

2. **Performance Monitoring**
   - Add timing information to logs
   - Track memory usage

3. **Advanced Validation**
   - Add statistical tests for signal quality
   - Implement cross-validation for signal parameters
