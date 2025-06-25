# Central Parameter System v4 - Problem and Changes Log

## Introduction

This document tracks all changes, identified problems, solutions, and verification steps during the implementation of the Central Parameter System v4 (CPS v4).

**Log Format**:

- Each entry is prefixed with date and identifier
- Problems are noted with [PROBLEM]
- Changes are noted with [CHANGE]
- Fixes are noted with [FIX]
- Verifications are noted with [VERIFY]

## June 8, 2025 (Continued)

### [2025-06-12-001] [POLICY] Strict Production-Only Validation

**Change Description:**
- All validation and output verification must use ONLY the full production code flow (real backtest engine and reporting pipeline).
- Synthetic/test module validation is discontinued and must NOT be used for any output validation or debugging.
- All fixes, diagnostics, and verification must be performed in the production pipeline only.

**Rationale:**
- Ensures all outputs are based on real, production data and flow, preventing false positives/negatives from synthetic or test data.
- Improves transparency, reliability, and future-proofing of validation and reporting.

**Impact:**
- All synthetic/test validation modules are deprecated.
- All future debugging, validation, and verification must occur using production pipeline only.


### [2025-06-08-008] [STRATEGY] Shift in CPS V4 Rollout Priority

**Change Description**:

A strategic decision was made to adjust the CPS V4 implementation priorities. The new approach emphasizes stabilizing the core backtesting engine and the new V4 reporting system through direct configuration-driven testing *before* fully re-integrating and testing the GUI.

**Rationale**:

- Given the historical complexities with the parameter system and previous reporting implementations, ensuring the backend (engine and reports) is fundamentally sound is paramount.
- Testing directly with configuration files (`settings_parameters_v4.ini`) allows for focused debugging of core logic without the added variable of GUI interactions.
- This de-risks the project by building a reliable foundation first.
- Once the engine and V4 reporting are verified, GUI integration will be layered on top of a stable system.

**Impact on Task List (`Task_List_CPS_v4.md`)**:

- Phases have been reordered and redefined:
  - **Phase 1**: CPS V4 Foundation & Core Engine Conversion (Continues)
  - **Phase 2 (New Priority)**: V4 Reporting System Implementation & Engine-Reporting Integration Testing (Config-driven)
  - **Phase 3**: Advanced Parameter Structure & GUI Code Conversion (GUI *code* readiness, execution deferred)
  - **Phase 4**: Full GUI Integration & End-to-End Testing (Activates GUI for execution)
- Detailed tasks within these phases have been updated to reflect this flow.

**Next Steps**:

- Complete Phase 1 (Core Engine L2 Conversion).
- Proceed with Phase 2: Implement V4 reporting modules and develop config-driven test harnesses.
- Defer full operational testing of the GUI until Phase 4.

## June 8, 2025

### [2025-06-08-001] [CHANGE] Completed Level 2 CPS_v4 Conversion for Core Engine Modules

**Files Modified**:

- `engine/benchmark_v4.py`
- `engine/allocation_v4.py`
- `engine/backtest_v4.py`
- `engine/data_loader_v4.py`

**Change Description**:
Converted the specified engine modules to full Level 2 CPS_v4 compliance. This involved:

- Ensuring all parameters are sourced directly and exclusively from `settings_CPS_v4.py` (via `settings_parameters_v4.ini`).
- Removing any fallback default values for required parameters within the modules.
- Implementing hard failures (raising `ValueError`) if required parameters are missing from CPS_v4 settings.
- Updating function signatures to remove parameters now sourced from CPS_v4.
- Revising module and function docstrings to reflect CPS_v4 compliance and parameter sourcing.
- For `data_loader_v4.py`, all `data_params` section parameters (`tickers`, `start_date`, `end_date`, `price_field`, `data_storage_mode`) are now treated as required and will cause a hard fail if missing. Docstring placement and linting errors were also corrected.
- For `backtest_v4.py`, noted that the module exceeds the 450-line limit and requires future refactoring (task to be logged separately).

**Verification Steps**:

1. Manual code review of each module against Level 2 CPS_v4 conversion criteria.
2. Ensured parameters are loaded at module level from `settings`.
3. Verified `try-except KeyError` blocks for hard failures on missing required parameters.
4. Checked that function signatures and docstrings were updated.

**Test Results**:

- Code review confirmed CPS_v4 Level 2 compliance for parameter handling and docstrings in all four modules.

**Next Steps**:

- Continue Level 2 CPS_v4 conversion for remaining modules in the `engine/` directory (`execution_v4.py`, `orders_v4.py`, `portfolio_v4.py`).
- Log a separate task for refactoring `engine/backtest_v4.py` due to its size.

### [2025-06-08-002] [CHANGE] Completed Level 2 CPS_v4 Conversion for execution_v4.py

**Files Modified**:

- `engine/execution_v4.py`

**Change Description**:
Converted `engine/execution_v4.py` to full Level 2 CPS_v4 compliance. This involved:

- Ensuring `commission_rate` and `slippage_rate` (from `settings['strategy']`) and `initial_capital` (from `settings['backtest']`) are sourced directly and exclusively from CPS_v4 settings at the module level.
- Removing any fallback default values for these required parameters.
- Implementing hard failures (raising `ValueError`) if these required parameters are missing from CPS_v4 settings.
- Updating `PercentSlippageModel.__init__`, `PercentCommissionModel.__init__`, and `ExecutionEngine.__init__` methods and their docstrings to remove direct parameter arguments for rates/capital and instead use the module-level variables sourced from CPS_v4.
- Ensuring default `PercentSlippageModel` and `PercentCommissionModel` instances within `ExecutionEngine` are created without arguments, relying on their updated `__init__` methods.
- Revising the module-level docstring to accurately reflect CPS_v4 compliance, list all required parameters, and specify their expected locations within the settings structure.

**Verification Steps**:

1. Manual code review of `engine/execution_v4.py` against Level 2 CPS_v4 conversion criteria.
2. Ensured parameters (`commission_rate`, `slippage_rate`, `initial_capital`) are loaded at module level from `settings`.
3. Verified `try-except KeyError as e: raise ValueError(...)` block for hard failures on missing required parameters.
4. Checked that `PercentSlippageModel`, `PercentCommissionModel`, and `ExecutionEngine` initializers and docstrings were updated to reflect sourcing from module-level CPS_v4 parameters.
5. Confirmed the module docstring accurately lists required parameters and their sources.

**Test Results**:

- Code review confirmed CPS_v4 Level 2 compliance for parameter handling, class initializers, and docstrings in `engine/execution_v4.py`.

**Next Steps**:

- Continue Level 2 CPS_v4 conversion for `engine/orders_v4.py`.
- Subsequently, convert `engine/portfolio_v4.py`.

### [2025-06-08-003] [VERIFY] Confirmed CPS_v4 Compliance for orders_v4.py

**Files Reviewed**:

- `engine/orders_v4.py`

**Change Description**:
Reviewed `engine/orders_v4.py` for Level 2 CPS_v4 compliance. The module currently does not utilize any parameters that require sourcing from the centralized CPS_v4 settings. Its existing module docstring correctly notes that any future parameterization must adhere to CPS_v4 standards (i.e., sourced from settings, no hardcoding or local defaults).

No code changes were required as the module is already compliant by not having configurable parameters that fall under CPS_v4 scope.

**Verification Steps**:

1. Manual code review of `engine/orders_v4.py`.
2. Confirmed no parameters are loaded from external configuration files or have hardcoded default values that should be centralized.
3. Verified the module docstring appropriately addresses future parameterization under CPS_v4.

**Test Results**:

- Code review confirmed `engine/orders_v4.py` is compliant with Level 2 CPS_v4 standards as it does not currently require centralized parameters.

**Next Steps**:

- Continue Level 2 CPS_v4 conversion for `engine/portfolio_v4.py`.

### [2025-06-08-004] [VERIFY] Completed Level 2 CPS_v4 Conversion for portfolio_v4.py


- `engine/portfolio_v4.py`

**Change Description**:
Successfully converted `engine/portfolio_v4.py` to Level 2 CPS_v4 compliance.
Key changes include:
1. Modified module-level parameter loading:
    - `initial_capital` is now strictly loaded from `settings['backtest']['initial_capital']`.
    - A `ValueError` is raised if `initial_capital` is not found in the settings, removing any fallback defaults.
2. Updated `Portfolio.__init__` method:
    - Removed the `initial_capital` argument and its default value from the method signature.
    - The method now exclusively uses the module-level `initial_capital` variable sourced from CPS_v4 settings.
3. Updated Docstrings:
    - The main module docstring has been revised to declare CPS_v4 compliance and list `initial_capital` (sourced from `settings['backtest']['initial_capital']`) as a required parameter.
    - The `Portfolio` class docstring was updated to indicate that `initial_capital` is sourced from module-level CPS_v4 settings.

**Verification Steps**:

1. Manual code review of `engine/portfolio_v4.py` to confirm all changes.
2. Ensured `initial_capital` is loaded directly from `settings['backtest']['initial_capital']` with no fallbacks.
{{ ... }}

- `models/ema_allocation_model_v4.py`

**Change Description**:
Converted `models/ema_allocation_model_v4.py` to Level 2 CPS_v4 compliance.
Key changes:
1. Removed `get_ema_parameters()` function.
2. Loaded `st_lookback`, `mt_lookback`, `lt_lookback`, `min_weight`, `max_weight` strictly from `settings['strategy']['ema_model']` at module level, raising `ValueError` on missing or invalid parameters.
3. Updated signatures and internal logic of `calculate_ema_metrics`, `ema_allocation_model`, and both `ema_allocation_model_updated` functions to use these module-level CPS_v4 parameters, removing them as arguments.
4. Revised module and relevant function docstrings for CPS_v4 compliance.

**Verification Steps**:

1. Manual code review of `models/ema_allocation_model_v4.py`.
2. Confirmed parameters are sourced strictly from `settings['strategy']['ema_model']`.
3. Verified function signatures and calls are updated.
4. Checked docstring updates.

**Test Results**:

- Code review suggests `models/ema_allocation_model_v4.py` is now compliant with Level 2 CPS_v4 standards.

**Next Steps**:

- Update `docs/CPS_v4/convert_param_to_v4.md` with overall status.
- `engine/data_loader_v4.py`

**Change Description**:
Reviewed `engine/data_loader_v4.py` for Level 2 CPS_v4 compliance.
Identified and corrected a `TypeError` in the `load_ticker_data` function. The call to `get_adjusted_close_data(tickers, start_date, end_date, price_field)` was incorrect as `get_adjusted_close_data` is defined to take no arguments and uses module-level parameters.
The call was changed to `get_adjusted_close_data()`.

With this correction, the module is now fully compliant with Level 2 CPS_v4 standards:
1. Settings are loaded via `CPS_v4.settings_CPS_v4.load_settings()`.
2. Required parameters (`tickers`, `start_date`, `end_date`, `price_field`, `data_storage_mode`) are sourced strictly from `settings['data_params']` at the module level.
3. A `ValueError` is raised if any of these parameters are missing.
4. Module docstring and function designs align with CPS_V4 parameter sourcing.

**Verification Steps**:

1.  Manual code review of `engine/data_loader_v4.py`.
2.  Identified incorrect function call signature for `get_adjusted_close_data`.
3.  Corrected the function call.
4.  Confirmed strict parameter sourcing from CPS_V4 settings.
5.  Verified error handling for missing parameters.
6.  Checked function signatures and docstrings.

**Test Results**:

-   `engine/data_loader_v4.py` is now confirmed to be compliant with Level 2 CPS_v4 standards after the fix.

**Next Steps**:

-   Proceed with next module conversion based on `docs/CPS_v4/convert_param_to_v4.md`.


### [2025-06-08-006] [VERIFY] Confirmed Level 2 CPS_v4 Compliance for engine/benchmark_v4.py

**Files Reviewed**:

- `engine/benchmark_v4.py`

**Change Description**:
Reviewed `engine/benchmark_v4.py` and confirmed it is already compliant with Level 2 CPS_v4 standards.
Key observations:
1.  Settings are loaded via `CPS_v4.settings_CPS_v4.load_settings()`.
2.  The required parameter `benchmark_rebalance_freq` is sourced strictly from `settings['backtest']['benchmark_rebalance_freq']`.
3.  A `ValueError` is raised if the parameter is missing.
4.  The function `calculate_equal_weight_benchmark` uses the module-level parameter, not an argument.
5.  Module docstring correctly reflects CPS_V4 compliance.
No code changes were necessary.

**Verification Steps**:

1.  Manual code review of `engine/benchmark_v4.py`.
2.  Confirmed strict parameter sourcing from CPS_V4 settings.
3.  Verified error handling for missing parameters.
4.  Checked function signatures and docstrings.

**Test Results**:

-   `engine/benchmark_v4.py` is confirmed to be compliant with Level 2 CPS_v4 standards.

**Next Steps**:

-   Await user verification.
-   Proceed with next module conversion based on `docs/CPS_v4/convert_param_to_v4.md`.



### [2025-06-08-008] [VERIFY] Confirmed Level 1 CPS_v4 Verification for utils/date_utils.py

**Files Reviewed**:

- `utils/date_utils.py`

**Change Description**:
Reviewed `utils/date_utils.py` for Level 1 CPS_v4 verification.
- Confirmed that the module primarily contains utility functions.
- Default parameters within functions (e.g., `default_start_offset` in `standardize_date`, `freq_map` in `map_rebalance_frequency`) are internal to the utility's operation or provide sensible defaults for utility behavior, not system-wide configurable parameters that need to be sourced from CPS_v4 settings.
- No changes to parameter sourcing are required for this module.
- Added filename comment at the top of the file as per standard practice.

**Verification Steps**:

1.  Manual code review of `utils/date_utils.py`.
2.  Analyzed function parameters to distinguish between utility defaults and configurable system parameters.
3.  Confirmed that no parameters require sourcing from the central CPS_v4 settings.
4.  Updated module status in `docs/CPS_v4/convert_param_to_v4.md` to "L1 Verified (No Param Changes)" with approach "Keep".

**Test Results**:

-   `utils/date_utils.py` is confirmed as L1 Verified (No Param Changes) for CPS_v4.

**Next Steps**:

-   Proceed with Level 1 CPS_v4 verification for `utils/trade_log.py`.


### [2025-06-08-009] [CHANGE] Completed Level 1 CPS_v4 Verification for utils/trade_log.py

**Files Reviewed**:

- `utils/trade_log.py`

**Change Description**:
Completed Level 1 CPS_v4 verification and necessary modifications for `utils/trade_log.py`.
- Added filename comment: `# filename: utils/trade_log.py` at the top of the file.
- Removed unused import: `from config.config import config` (legacy V3 configuration).
- Modified the `create_trade_log_from_trades` method by removing the default value for the `transaction_cost` parameter. This parameter must now be explicitly passed by the calling module, which is expected to source it from CPS_V4 settings (e.g., `settings['strategy']['transaction_cost']`).

**Verification Steps**:

1.  Manual code review of `utils/trade_log.py`.
2.  Identified `transaction_cost` in `create_trade_log_from_trades` as a parameter whose default value could conflict with CPS_V4 sourcing principles.
3.  Removed the default value for `transaction_cost` to enforce explicit provision by the caller.
4.  Added the standard filename comment.
5.  Removed the unused V3 `config` import.
6.  Updated module status in `docs/CPS_v4/convert_param_to_v4.md` to "L1 Verified (Default Removed)" with approach "Edit".

**Test Results**:

-   `utils/trade_log.py` is now L1 Verified for CPS_V4. Calling modules are now required to explicitly provide the `transaction_cost`.

**Next Steps**:

-   Proceed with Level 1 CPS_V4 verification for the next applicable module in `docs/CPS_v4/convert_param_to_v4.md`.


### [2025-06-08-010] [ARCHIVE] Archived reporting/performance_reporting.py for CPS_v4

**Files Reviewed**:

- `reporting/performance_reporting.py`
- `docs/CPS_v4/convert_param_to_v4.md`

**Change Description**:
The module `reporting/performance_reporting.py` was identified for archival as per `docs/CPS_v4/convert_param_to_v4.md`.

- Status updated to "Archived (No L1 Conversion)".

**Verification Steps**:

1. Confirmed "Approach" in `convert_param_to_v4.md` is "Archive".
2. Updated status in `convert_param_to_v4.md`.

**Next Steps**:

- Proceed with L1 verification for `reporting/allocation_report.py`.

### [2025-06-08-011] [ARCHIVE] Archived reporting/performance_reporting_BU.py for CPS_v4

**Files Reviewed**:

- `reporting/performance_reporting_BU.py`
- `docs/CPS_v4/convert_param_to_v4.md`

**Change Description**:
As per the `convert_param_to_v4.md` plan, `reporting/performance_reporting_BU.py` is designated to be "Archived" and will not undergo L1 or L2 CPS_v4 conversion.
- Updated `docs/CPS_v4/convert_param_to_v4.md` to reflect status as "Archived (No L1 Conversion)".

**Verification Steps**:

1. Confirmed "Approach" in `convert_param_to_v4.md` is "Archive".
2. Updated status in `convert_param_to_v4.md`.

**Next Steps**:

- Proceed with L1 verification for `reporting/allocation_report.py`.

### [2025-06-08-012] [CHANGE] Completed Level 1 CPS_v4 Verification for reporting/allocation_report.py

**Files Reviewed**:

- `reporting/allocation_report.py`

**Change Description**:
Completed Level 1 CPS_v4 verification and necessary modifications for `reporting/allocation_report.py`.
- Added filename comment: `# reporting/allocation_report.py` at the top of the file.
- Confirmed that default parameters (`sheet_name` in `_write_default_parameters`, `portfolio_values` and `include_cash` in `generate_rebalance_report`) are acceptable for L1 as they are either internal formatting choices or local operational flags, not global system parameters requiring CPS_v4 sourcing.
- Confirmed no legacy config/parameter access.
- Updated module status in `docs/CPS_v4/convert_param_to_v4.md` to "L1 Verified (Comment Added)" with approach "Edit".

**Verification Steps**:

1. Reviewed `reporting/allocation_report.py` for filename comment, default parameters, and legacy config access.
2. Added filename comment.
3. Confirmed no other L1 changes were required.
4. Updated `docs/CPS_v4/convert_param_to_v4.md`.

**Next Steps**:

- Await user verification.
- Proceed with Level 1 CPS_V4 verification for the next applicable module in `docs/CPS_v4/convert_param_to_v4.md`.

### [2025-06-08-013] [CHANGE] Completed Level 1 CPS_v4 Verification for v3_engine/V3_perf_repadapt_legacybridge.py

**Files Reviewed**:

- `v3_engine/V3_perf_repadapt_legacybridge.py`
- `docs/CPS_v4/convert_param_to_v4.md`

**Files Modified**:

- `v3_engine/V3_perf_repadapt_legacybridge.py`
- `docs/CPS_v4/convert_param_to_v4.md`

**Change Description**:
Completed Level 1 CPS_v4 verification for the legacy adapter module `v3_engine/V3_perf_repadapt_legacybridge.py`.
- This module is marked for "Phase Out" in `convert_param_to_v4.md`.
- The module is 593 lines long, exceeding the 450-line limit.
- As per protocol for "Phase Out" and large modules, only minimal L1 changes were made.
- Added filename comment: `# filename: v3_engine/V3_perf_repadapt_legacybridge.py` at the top of the file.
- No other code changes were made to preserve existing logic and due to its phase-out status.
- Updated the status of `v3_engine/V3_perf_repadapt_legacybridge.py` in `docs/CPS_v4/convert_param_to_v4.md` from "Not Converted" to "L1 Verified (Comment Added)" with "Phase Out" approach.

**Verification Steps**:

1. Reviewed `v3_engine/V3_perf_repadapt_legacybridge.py` to confirm its "Phase Out" status and size.
2. Confirmed the filename comment was correctly added to the top of `v3_engine/V3_perf_repadapt_legacybridge.py`.
3. Verified that no other code modifications were made to the module.
4. Confirmed the status update in `docs/CPS_v4/convert_param_to_v4.md` reflects "L1 Verified (Comment Added)".

**Next Steps**:

- Proceed with Level 1 CPS_V4 verification for the next "Legacy Adapter Module", `v3_engine/V3_perf_repadapt_paramconvert.py`, as listed in `docs/CPS_v4/convert_param_to_v4.md`.

### [2025-06-08-014] [VERIFY] Level 1 CPS_V4 Verification for `v3_engine/V3_perf_repadapt_paramconvert.py` (Phase Out)

**Date**: June 8, 2025
**Status**: Completed

**Objective**: Perform Level 1 CPS_V4 verification for the legacy adapter module `v3_engine/V3_perf_repadapt_paramconvert.py`, which is marked for "Phase Out". This involves adding the mandatory filename comment and updating documentation.

**Files Reviewed**:

- `v3_engine/V3_perf_repadapt_paramconvert.py`
- `docs/CPS_v4/convert_param_to_v4.md`
- `docs/CPS_v4/Problem_Changes_Log_CPS_v4.md`

**Changes Made**:

1. **`v3_engine/V3_perf_repadapt_paramconvert.py`**:
    - Added the mandatory filename comment `# filename: v3_engine/V3_perf_repadapt_paramconvert.py` at the top of the file.
    - No other code changes were made as the module is marked for "Phase Out" and is under the 450-line limit (176 lines).
2. **`docs/CPS_v4/convert_param_to_v4.md`**:
    - Updated the status of `v3_engine/V3_perf_repadapt_paramconvert.py` in the "Legacy Adapter Modules" table from "Not Converted" to "L1 Verified (Comment Added)" with the approach remaining "Phase Out".
3. **`docs/CPS_v4/Problem_Changes_Log_CPS_v4.md`**:
    - Added this log entry `[2025-06-08-014]` to document the verification process.

**Verification Steps**:

1. Reviewed `v3_engine/V3_perf_repadapt_paramconvert.py` to confirm its "Phase Out" status and size (176 lines).
2. Confirmed the filename comment was correctly added to the top of `v3_engine/V3_perf_repadapt_paramconvert.py`.
3. Verified that no other code modifications were made to the module.
4. Confirmed the status update in `docs/CPS_v4/convert_param_to_v4.md` reflects "L1 Verified (Comment Added)".

**Next Steps**:

- Proceed with Level 1 CPS_V4 verification for the next "Legacy Adapter Module", `v3_engine/performance_reporter_adapter.py`, as listed in `docs/CPS_v4/convert_param_to_v4.md`.

## June 7, 2025

### [2025-06-07-002] [CHANGE] Implemented Consolidated Settings System with Automatic Type Detection

**Files Modified**:
- `CPS_v4/settings_CPS_v4.py`
- `CPS_v4/settings_parameters_v4.ini`
- `docs/CPS_v4/Task_List_CPS_v4.md`

**Change Description**:

Implemented a consolidated settings system with automatic parameter type detection, eliminating the need for separate default/user INI files. The new system dynamically identifies and handles all four parameter types (SimpleA, SimpleN, ComplexN, AlphaList) based on their structure and format.

**Key Features**:
- Single source of truth in `settings_parameters_v4.ini`
- Automatic type detection without requiring explicit type flags
- Support for named lists via the [Lists] section
- Robust type conversion and validation
- Comprehensive debug and summary utilities

**Implementation Details**:
- Dynamic parameter type detection based on value structure:
  - SimpleA: Default type for strings, booleans
  - SimpleN: Numeric values (int, float)
  - ComplexN: Optimizable parameters with min/max bounds
  - AlphaList: Lists or named list references
- Support for named lists that can be referenced by multiple parameters
- Clean, minimal codebase following radical simplicity principles

**Verification Steps**:
1. Run `python settings_CPS_v4.py` to test settings loading
2. Verify all parameter types are correctly identified
3. Check debug output for any parsing issues

**Next Steps**:
- Begin parameter discovery and migration from legacy code
- Update GUI to work with the new parameter structure

### [2025-06-07-001] [FIX] Data Loader File Confusion

**Problem:** Confusion between two data loader files:

- `data/data_loader.py` (legacy, 241 lines)
- `engine/data_loader_v4.py` (CPS v4, 83 lines)

**Analysis:**

- Initially modified `data/data_loader.py` to add CPS v4 support
- Later discovered `engine/data_loader_v4.py` already existed as the proper CPS v4 implementation
- This caused confusion and potential duplication

**Changes Made:**

1. Reverted changes to `data/data_loader.py` to maintain legacy functionality
2. Confirmed `engine/data_loader_v4.py` is the correct CPS v4 implementation
3. Updated documentation to reflect correct file statuses:
   - Marked `data/data_loader.py` for archiving
   - Confirmed `engine/data_loader_v4.py` as the active CPS v4 implementation

**Rationale:**

- Maintain clear separation between legacy and CPS v4 code
- Avoid code duplication and potential maintenance issues
- Follow project structure where `engine/` contains active CPS v4 modules

**Next Steps:**

- Archive `data/data_loader.py` after confirming all references are updated
- Update any imports to use `engine.data_loader_v4`
- Proceed with converting reporting modules to CPS v4

## June 6, 2025

### [2025-06-06-001] [CHANGE] Initial CPS v4 Documentation Created

**Files Created**:

- `docs/para_R/Overview_CPS_v4.md`
- `docs/para_R/Task_List_CPS_v4.md`
- `docs/para_R/Problem_Changes_Log_CPS_v4.md`

**Description:**

Created initial documentation for the CPS v4 project, including high-level overview, detailed task list, and this change log.

**Next Steps:**

- Create parameter system architecture
- Create default settings structure

### [2025-06-06-002] [PROBLEM] Legacy Parameter System Complexity

**Problem Description:**

The existing parameter system relies on a complex registry pattern with multi-layered adapters, causing maintenance difficulties and poor AI debugging capabilities. Current legacy bridge module `V3_perf_repadapt_legacybridge.py` exceeds 593 lines, violating the maximum module size rule of 450 lines.

**Root Cause Analysis:**

- Registry pattern creates indirect parameter flow
- Legacy adapters add complexity for backward compatibility
- Multiple conversion layers obfuscate parameter origin and usage

**Proposed Solution:**

Complete redesign with INI-based configuration and direct function arguments. Zero backward compatibility layers to ensure clean break from legacy complexity.

**Next Steps:**

- Document exact legacy parameters to migrate
- Create parameter discovery tool

### [2025-06-06-003] [CHANGE] Manual parameter mapping and reference updates

**Files Modified:**

- `default_settings_CPS_v4.ini`
- `docs/CPS_v4/Parameter_Reference_CPS_v4.md`
- `docs/CPS_v4/Task_List_CPS_v4.md`
- `docs/CPS_v4/Problem_Changes_Log_CPS_v4.md`

**Change Description:**

- Manually copied parameters from `config/config_v3.py` into `default_settings_CPS_v4.ini` using `define_numparam` and `define_alphaparam`
- Updated parameter reference with entries for `rebalance_freq`, `signal_algo`, `tickers`, and helper definitions
- Updated task list documentation with current task/subtask status

**Verification Steps:**

1. Run `run_cps_v4_full_test.bat` and ensure manual mappings apply correctly

**Test Results:**

- `run_cps_v4_full_test.bat` executed successfully without errors

**Next Steps:**

- Integrate settings loader to handle `define_numparam` and `define_alphaparam` conventions

### [2025-06-08-015] [CHANGE] Renamed _v4 modules and updated V3_perf_repadapt_legacybridge.py archival status

**Files Modified/Reviewed**:

- `docs/CPS_v4/convert_param_to_v4.md` (Updated)
- `utils/date_utils.py` -> `utils/date_utils_v4.py` (Renamed)
- `utils/trade_log.py` -> `utils/trade_log_v4.py` (Renamed)
- `reporting/allocation_report.py` -> `reporting/allocation_report_v4.py` (Renamed)
- `v3_engine/V3_perf_repadapt_legacybridge.py` (Archival status updated in `convert_param_to_v4.md`)

**Change Description**:

- Updated `docs/CPS_v4/convert_param_to_v4.md`:
  - Reflected new `_v4` suffixes for `date_utils`, `trade_log`, and `allocation_report`.
  - Updated `V3_perf_repadapt_legacybridge.py` status to "Archived (No L1 Conversion)" and approach to "Archive".
- Renamed Python files:
  - `utils/date_utils.py` to `utils/date_utils_v4.py`
  - `utils/trade_log.py` to `utils/trade_log_v4.py`
  - `reporting/allocation_report.py` to `reporting/allocation_report_v4.py`
- `v3_engine/V3_perf_repadapt_legacybridge.py` was not renamed, consistent with "Archive" status.

**Verification Steps**:

1. Confirmed file renames executed successfully on the filesystem.
2. Verified changes in `docs/CPS_v4/convert_param_to_v4.md` reflect the new names and archival status.

**Test Results**:

- N/A (Documentation and file system changes)

**Next Steps**:

- Create a sub-task to update all import statements across the project to reflect new `_v4` filenames.
- Continue Level 1 CPS V4 verification for `v3_engine/performance_reporter_adapter.py`.

### [2025-06-06-004] [CHANGE] Converted EMA Strategy Core to CPS v4 and added min_weight/max_weight parameters

**Files Modified:**

- `models/ema_allocation_model.py` → `models/ema_allocation_model_v4.py`

**Change Description:**

- Replaced legacy registry calls with `settings.get(...)` from CPS v4
- Enforced hard failure for missing `system_top_n` setting
- Integrated `min_weight` and `max_weight` from `settings` instead of function defaults

**Fix Implementation:**

- Updated `get_ema_parameters()`, settings import, and `top_n` logic
- Removed fallback logic for weights allocation
- Renamed module file and adjusted imports accordingly

**Verification Steps:**

1. Import and instantiate `ema_allocation_model_v4.py` without errors
2. Confirm `get_ema_parameters()` yields correct lookback values from default_settings_CPS_v4.ini
3. Execute existing backtests to ensure output consistency

**Test Results:**

- EMA allocation tests passed under CPS v4 configuration

**Next Steps:**

- Continue conversion of Backtest Engine (`engine/backtest.py`)

### [2025-06-06-005] [CHANGE] Converted Backtest Engine to CPS v4 and parameter mapping

**Files Modified:**

- `engine/backtest_v4.py`
- `docs/CPS_v4/convert_param_to_v3.md`
- `docs/CPS_v4/Task_List_CPS_v4.md`
- `docs/CPS_v4/Problem_Changes_Log_CPS_v4.md`

**Change Description**:

- Replaced legacy parameter access with `settings.get(...)` in constructor and `run_backtest`.
- Mapped parameters: initial_capital, commission_rate, slippage_rate, benchmark_rebalance_freq, rebalance_freq, execution_delay.
- Introduced facade module `backtest_v4.py` for consistent imports.

**Fix Implementation**:

- Added settings overrides at beginning of `__init__`.
- Updated `run_backtest` to fetch `rebalance_freq` and `execution_delay` via settings.
- Created `engine/backtest_v4.py` wrapping `BacktestEngine`.

**Verification Steps**:

1. Import `backtest_v4.BacktestEngine` without errors.
2. Confirm default parameter values align with `default_settings_CPS_v4.ini`.
3. Run a sample backtest to verify functionality.

**Test Results**:

- Backtest engine import and basic sample run: PASS.

**Next Steps**:

- Begin conversion of Portfolio Manager (`engine/portfolio.py`).

## Template for Future Entries

### [YYYY-MM-DD-XXX] [TYPE] Brief Description

**Files Modified**:

- `path/to/file1`
- `path/to/file2`

**Problem Description**:

[For problems] Detailed description of the issue, including context and impact.

**Change Description**:

[For changes] What was changed and why.

**Fix Implementation**:

[For fixes] How the fix was implemented, including code changes or configuration updates.

**Verification Steps**:

1. Step 1 to verify the fix
2. Step 2 to verify the fix
3. ...

**Test Results**:

- Test 1: PASS/FAIL
- Test 2: PASS/FAIL
- ...

**Next Steps**:

- Follow-up actions needed
- Related tasks to address

## Known Issues and TODOs

| ID | Issue | Priority | Related Task | Status |
|----|-------|----------|--------------|--------|
| 1  | Define complete parameter migration approach | HIGH | 1.2 | PENDING |
| 2  | Create test data fixtures for verification | MEDIUM | 1.3 | PENDING |
| 3  | Define final cutover strategy | MEDIUM | 4.3 | PENDING |

## Verification Commands

Standard verification commands to use throughout the project:

```batch
# Run unit tests for CPS v4
cd S:\Dropbox\Scott Only Internal\Quant_Python_24\Backtest_FinAsset_Alloc_Template
run_verify_CPS_v4.bat

# Compare output reports with reference standards
python tests\compare_reports_CPS_v4.py --output-dir=output\test_reports --reference-dir=tests\reference_data
```

## Related Resources

- [Task List](./Task_List_CPS_v4.md)
- [Overview](./Overview_CPS_v4.md)
- [User Guide](./User_Guide_CPS_v4.md) (TBD)
- [Parameter Reference](./Parameter_Reference_CPS_v4.md) (TBD)

**Last Updated**: 2025-06-06
