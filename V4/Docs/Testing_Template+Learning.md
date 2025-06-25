# Testing Template and Learning Document

## Overview

> **NOTE (2025-06-12):**
> - All validation and output checking must be performed using ONLY the full production data flow (backtest engine → reporting module).
> - Synthetic/test validation modules are deprecated and must NOT be used for output verification or debugging.


This document captures lessons learned, best practices, and templates for testing in the CPS V4 system. It serves as a knowledge repository to improve testing efficiency and effectiveness for future development.

**Date Created:** 2025-06-11  
**Last Updated:** 2025-06-11

## Testing Best Practices

### 1. Test Execution with Bat Files (REQUIRED)

- **Use Bat Files**: ALWAYS use bat files for test execution instead of direct Python execution
- **Virtual Environment**: Bat files should activate the isolated virtual environment
- **Logging**: Send all test output to log files for review
- **AI-Driven Loop**: Enable AI to run bat files and review logs for fixes/next steps in a loop

### 2. Test Setup and Organization

- **Isolated Test Directories**: Create dedicated test output directories (e.g., `test_output/`) for each test module to avoid conflicts
- **Clear Test Naming**: Use descriptive test function names that indicate what's being tested
- **Test Independence**: Each test should be able to run independently without relying on other tests
- **Test Data Generation**: Include synthetic data generation functions in test scripts for consistent, reproducible testing

### 2. Error Handling and Reporting

- **Detailed Error Logging**: Capture full tracebacks and error details to separate log files
- **Structured Error Output**: Format error messages with clear headers and context information
- **Error Classification**: Categorize errors by type (parameter errors, initialization errors, execution errors)
- **Traceback Preservation**: Always capture and preserve the full traceback for debugging

### 3. Parameter Testing

- **Section Verification**: Verify that required parameter sections exist in settings files
- **Parameter Presence**: Check for specific required parameters before attempting to use them
- **Type Validation**: Validate parameter types match expected formats
- **Default Handling**: Test behavior with missing parameters when defaults should be used

### 4. Module Testing

- **Import Testing**: Test that modules can be imported correctly
- **Initialization Testing**: Verify modules initialize without errors
- **Function Testing**: Test individual functions with controlled inputs
- **Integration Testing**: Test module interactions with other components

## Common Testing Pain Points

### 1. Error Reporting Challenges

- **Issue**: Truncated error messages in console output
- **Solution**: Write detailed error logs to files and use structured error reporting
- **Example**:
  
  ```python
  try:
      # Test code
  except Exception as e:
      with open(error_log_path, "a") as error_file:
          error_file.write(f"\n\nTEST ERROR:\n{str(e)}\n\n")
          error_file.write(traceback.format_exc())
  ```

### 2. String Formatting Issues

- **Issue**: String formatting errors with '%' characters in f-strings or format strings
- **Solution**: Use double '%' for literal percent signs or switch to f-strings for complex formatting
- **Example**:
  
  ```python
  # Incorrect: timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  # Correct for format strings:
  timestamp = datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S')
  # Or better, use direct f-string:
  timestamp = f"{datetime.now():%Y%m%d_%H%M%S}"
  ```

### 3. Parameter Access Issues

- **Issue**: Incorrect section names when accessing parameters

- **Solution**: Standardize section naming and verify section existence before access

- **Example**:
  
  ```python
  # Verify section exists
  if 'report' not in settings:
      raise ValueError("Required 'report' section missing in settings")
  
  # Access parameters with defaults
  reporting_settings = settings.get('report', {})
  output_dir = reporting_settings.get('output_directory', 'default_output')
  ```

## Test Templates

### Bat File Test Execution Template

```batch
@echo off
REM run_tests.bat - Test execution script for [module_name]
REM Created: [date]

echo Starting [module_name] test execution at %date% %time%
echo ===============================================

REM Activate the virtual environment
call F:\AI_Library\my_quant_env\Scripts\activate.bat

REM Create logs directory if it doesn't exist
if not exist "test_logs" mkdir "test_logs"

REM Set log file with timestamp
set timestamp=%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set log_file=test_logs\test_run_%timestamp%.log

echo Test execution started > %log_file%
echo Timestamp: %date% %time% >> %log_file%
echo =============================================== >> %log_file%

REM Run the test script and log output
echo Running [module_name] tests... >> %log_file%
python test_[module_name].py >> %log_file% 2>&1
echo. >> %log_file%

REM Check test results file and append to log
echo Test Results Summary: >> %log_file%
echo ---------------------- >> %log_file%
if exist "test_output\test_results.txt" (
    type test_output\test_results.txt >> %log_file%
) else (
    echo No test results file found! >> %log_file%
)

REM Check error log file and append to log if it exists
echo. >> %log_file%
echo Error Details: >> %log_file%
echo -------------- >> %log_file%
if exist "test_output\error_log.txt" (
    type test_output\error_log.txt >> %log_file%
) else (
    echo No error log file found. >> %log_file%
)

echo. >> %log_file%
echo Test execution completed at %date% %time% >> %log_file%
echo =============================================== >> %log_file%

REM Display completion message
echo Test execution completed. Results saved to %log_file%
echo.

REM Deactivate virtual environment
call deactivate

REM Display the log file
type %log_file%
```

### Basic Module Test Template

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test_module_name.py
"""
Test script for module_name.py

This script provides isolated tests for the module functionality.
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Create test output directory
test_output_dir = Path(os.path.dirname(__file__)) / 'test_output'
test_output_dir.mkdir(exist_ok=True, parents=True)

# Set up error log
error_log_path = test_output_dir / "error_log.txt"

def setup_test_environment():
    """Set up the test environment"""
    # Initialize test environment
    pass

def generate_test_data():
    """Generate synthetic test data"""
    # Create test data
    return {}

def test_module_import():
    """Test module import"""
    try:
        # Import the module
        from path.to import module_name
        logger.info("✓ Module import successful")
        return True
    except Exception as e:
        log_error("Module import", e)
        return False

def test_functionality():
    """Test specific functionality"""
    try:
        # Test code
        logger.info("✓ Functionality test passed")
        return True
    except Exception as e:
        log_error("Functionality test", e)
        return False

def log_error(test_name, error):
    """Log error details to file and console"""
    error_message = f"\n\n==== ERROR: {test_name.upper()} ====\n"
    error_message += f"Error type: {type(error).__name__}\n"
    error_message += f"Error message: {str(error)}\n\n"
    error_message += traceback.format_exc()
    error_message += "\n==== END ERROR TRACEBACK ====\n"

    # Print to console
    print(error_message)

    # Write to log file
    with open(error_log_path, "a") as error_file:
        error_file.write(error_message)

    logger.error(f"✗ {test_name} failed: {error}")

def run_all_tests():
    """Run all tests and report results"""
    logger.info("Starting tests...")

    # Initialize error log
    with open(error_log_path, "w") as error_file:
        error_file.write(f"Test Error Log - {datetime.datetime.now()}\n\n")

    # Run tests
    results = {
        "module_import": test_module_import(),
        "functionality": test_functionality()
    }

    # Print summary
    logger.info("\n--- Test Results Summary ---")
    all_passed = True

    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {status}")
        all_passed = all_passed and passed

    logger.info(f"\nOverall status: {'PASSED' if all_passed else 'FAILED'}")
    logger.info(f"Detailed error log: {error_log_path}")

    return all_passed

if __name__ == "__main__":
    run_all_tests()
```

## Lessons Learned

### From CPS V4 Reporting Testing (2025-06-11)

1. **Parameter Section Naming**: Ensure consistent section naming between code and settings files. The mismatch between 'reporting' and 'report' sections caused initial test failures.

2. **Missing Imports**: The ast module was used in settings_CPS_v4.py but not imported, causing cryptic errors during testing. Always verify all required imports are present.

3. **String Formatting Issues**: Timestamp formatting with strftime() caused '%' formatting errors. When using '%' in format strings, be careful about proper escaping.

4. **Error Reporting Challenges**: Console output often truncates error messages, making debugging difficult. Implement dedicated error logging to files.

5. **Test Independence**: Each test should be isolated and not depend on the success of previous tests to provide clear failure points.

## Future Improvements

1. **Automated Test Discovery**: Implement pytest or similar framework for automatic test discovery and execution

2. **Parameterized Testing**: Create parameterized tests to test multiple scenarios with minimal code duplication

3. **Test Coverage Reporting**: Add test coverage reporting to identify untested code paths

4. **Continuous Integration**: Set up automated testing on code changes

5. **Visual Test Results**: Generate visual reports of test results for easier interpretation

---

*This document will be continuously updated as new testing lessons and best practices are discovered.*
