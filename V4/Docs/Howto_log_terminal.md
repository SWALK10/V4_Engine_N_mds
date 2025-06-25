# Terminal Logging Best Practices for CPS v4

*Document Version: 2.0*  
*Last Updated: 2025-06-20*  
*New simplified approach proven reliable*

## Overview

This document captures the proven methods for capturing terminal output in the CPS v4 backtest system. These practices ensure reliable logging of all console output, which is critical for debugging and auditing.

## Key Principles

1. **Single Execution** - Run Python script just once
2. **Robust Path Handling** - Proper quoting for paths with spaces
3. **Simple Filtering** - Use findstr on full output file
4. **Clear Log Levels** - Standardized message prefixes in Python

## Implementation

### Batch Script Template

```batch
@echo off
REM --- Configuration (quoted paths) ---
SET "PYTHON_EXE=F:\AI_Library\my_quant_env\Scripts\python.exe"
SET "SCRIPT_PATH=%~dp0main_v4_production_run.py"
SET "OUTPUT_DIR=S:\Dropbox\Scott Only Internal\Quant_Python_24\Backtest_FinAsset_Alloc_Template\v4_trace_outputs"

REM --- Simple timestamp ---
SET "TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
SET "TIMESTAMP=%TIMESTAMP: =0%"

REM --- Run once, filter after ---
"%PYTHON_EXE%" "%SCRIPT_PATH%" > "%OUTPUT_DIR%\full_%TIMESTAMP%.txt" 2>&1
findstr /i "\[MILESTONE\] \[ERROR\] \[CRITICAL\]" "%OUTPUT_DIR%\full_%TIMESTAMP%.txt" > "%OUTPUT_DIR%\filtered_%TIMESTAMP%.txt"
```

### Python Logging

```python
import sys
import datetime

def log_message(message, level="INFO"):
    """Standardized logging for CPS v4"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")
    sys.stdout.flush()

# Usage examples:
log_message("Process started", "MILESTONE")
log_message("Data loaded successfully")
log_message("Invalid parameter detected", "WARNING")
log_message("Failed to connect to API", "ERROR")
```

## Best Practices for CPS v4

1. **Log File Naming**
   - Use format: `full_YYYYMMDD_HHMMSS.txt` and `filtered_YYYYMMDD_HHMMSS.txt`
   - Include strategy name and parameters in the filename when possible

2. **Output Directory Structure**

   ```
   project_root/
   ├── output/
   │   ├── logs/
   │   │   ├── full_20250619_143000.txt
   │   │   ├── filtered_20250619_143000.txt
   │   │   └── full_20250619_150000.txt
   │   │   └── filtered_20250619_150000.txt
   │   └── results/
   ```

3. **Error Handling**
   - Always check for the existence of required output files
   - Include validation steps in your batch script
   - Document expected files and their formats

4. **Performance Considerations**
   - For high-frequency logging, consider using Python's `logging` module
   - Rotate log files to prevent them from growing too large
   - Compress old log files

## Troubleshooting

### Log File is Empty

1. Check if the script is actually producing output
2. Verify write permissions to the output directory
3. Try running with `python -u` to disable output buffering

### Encoding Issues

1. Set console to UTF-8: `CHCP 65001`
2. Ensure your Python script specifies encoding when writing files

### Python Path Issues

1. Always use absolute paths to the Python executable
2. Consider adding Python to your system PATH for easier access

## Conclusion

Following these practices will ensure reliable logging and output capture for your CPS v4 backtests. The key is consistency and thorough error handling at every step.
