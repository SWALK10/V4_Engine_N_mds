# CPS v4 Parameter Conversion Plan

This document outlines the parameters to convert and the production modules to update for CPS v4 migration.

## Revised Strategy: Targeted Edits vs Adapter Replacement

> **CRITICAL RULE:** For all required parameters, do **NOT** use `.get(..., fallback)`. All required parameters must be present in CPS v4 settings. If missing, raise an error and halt execution. Only optional/reporting parameters may use `.get(..., fallback)` if their absence is truly non-fatal.

After reviewing the module list, we've identified that many files are adapters/bridges between parameter systems. For CPS v4's "clean break" philosophy, we'll use two approaches:

1. **Targeted Edits**: For core production modules, make minimal targeted edits to use the new parameter system - keep simple and preserve existing functionality
2. **Phased Elimination**: For adapter/bridge modules, plan for elimination rather than conversion

This approach aligns with the "NO fallbacks or backward compatibility" principle while minimizing risk of introducing new errors.

## 1. Parameter Conversion Matrix

List of all parameters to find and swap with CPS v4 `settings.get(...)` calls.

| Parameter Name           | Old Access Pattern                               | New CPS v4 Call Pattern                                                  |
| ------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------ |
| create_excel             | `registry.get_parameter('create_excel').value`   | `settings.get('report', {}).get('create_excel', True)`                   |
| save_trade_log           | `registry.get_parameter('save_trade_log').value` | `settings.get('report', {}).get('save_trade_log', True)`                 |
| metrics                  | `registry.get_parameter('metrics').value`        | `settings.get('performance', {}).get('metrics', [])`                     |
| create_charts            | `registry.get_parameter('create_charts').value`  | `settings.get('visualization', {}).get('create_charts', True)`           |
| chart_types              | `registry.get_parameter('chart_types').value`    | `settings.get('visualization', {}).get('chart_types', [])`               |
| chart_format             | `registry.get_parameter('chart_format').value`   | `settings.get('visualization', {}).get('chart_format', 'png')`           |
| chart_dpi                | `registry.get_parameter('chart_dpi').value`      | `settings.get('visualization', {}).get('chart_dpi', 300)`                |
| signal_history           | `registry.get_parameter('signal_history')`       | `settings.get('backtest', {}).get('signal_history', False)`              |
| allocation_history       | (implicit in reporting df code)                  | `settings.get('allocation', {}).get('history', True)`                    |
| execution_delay          | `registry.get_parameter('execution_delay')`      | `settings.get('strategy', {}).get('execution_delay', 0)`                 |
| signal_algo              | `registry.get_parameter('signal_algo')`          | `settings.get('strategy', {}).get('signal_algo', 'ema')`                 |
| lookback                 | `registry.get_parameter('lookback')`             | `settings.get('system', {}).get('lookback', 60)`                         |
| top_n                    | `registry.get_parameter('top_n')`                | `settings.get('system', {}).get('top_n', 2)`                             |
| st_lookback              | `registry.get_parameter('st_lookback')`          | `settings.get('system', {}).get('st_lookback', 15)`                      |
| mt_lookback              | `registry.get_parameter('mt_lookback')`          | `settings.get('system', {}).get('mt_lookback', 70)`                      |
| lt_lookback              | `registry.get_parameter('lt_lookback')`          | `settings.get('system', {}).get('lt_lookback', 100)`                     |
| core                     | `registry.get_parameter('core')`                 | `settings.get('system', {}).get('core', None)`                           |
| strategy_ema             | `registry.get_parameter('strategy_ema')`         | `settings.get('system', {}).get('strategy_ema', None)`                   |
| visualization            | `registry.get_parameter('visualization')`        | `settings.get('system', {}).get('visualization', None)`                  |
| reporting                | `registry.get_parameter('reporting')`            | `settings.get('report', {}).get('reporting', None)`                      |
| min_weight               | (in function signature)                          | `settings.get('strategy', {}).get('min_weight', 0.0)`                    |
| max_weight               | (in function signature)                          | `settings.get('strategy', {}).get('max_weight', 1.0)`                    |
| initial_capital          | (in **init** signature)                          | `settings.get('backtest', {}).get('initial_capital', 100000.0)`          |
| commission_rate          | (in **init** signature)                          | `settings['strategy']['commission_rate']`                                |
| slippage_rate            | (in **init** signature)                          | `settings['strategy']['slippage_rate']`                                  |
| benchmark_rebalance_freq | (in **init** signature)                          | `settings.get('backtest', {}).get('benchmark_rebalance_freq', 'yearly')` |
| rebalance_freq           | (in run_backtest signature)                      | `settings.get('backtest', {}).get('rebalance_freq', 'monthly')`          |
| execution_delay          | (in run_backtest signature)                      | `settings.get('strategy', {}).get('execution_delay', 0)`                 |

## CPS V4 Parameter Structure and GUI Considerations

### Labels and Grouping

- **Description/Label**: For each GUI widget, we need a human-readable label (e.g., "Initial Capital:"). The current INI approach includes a description field for this.
- **Grouping**: For GUI organization (e.g., "Core Parameters", "EMA Strategy Parameters"), we need a way to group parameters. The current INI approach uses section name prefixes (e.g., GuiParam_Core_...) for this.

### Complex Parameter Types: AlphaList and AlphaGroup

- **AlphaList**: Represents a direct, simple list of items.
- **AlphaGroup**: Represents a selection where each choice can route to different modules, algorithms, or separately defined data lists (e.g., selecting "ema strategy" might use different processing modules than "min variance"; selecting TickerGrp1 might use a different list of tickers than TickerGrp2). This allows for conditional logic based on parameter selection.

### Additional Data for GUI and Reporting

- Consideration for additional fields or separate lookup tables to manage what appears in GUIs or specific reports.
- **Preference**: Separate lookup tables are generally preferred for clarity and decoupling.
- **Alternative**: If separate tables significantly complicate coding, additional flag fields could be added to each parameter definition.
- **Defaults and Overrides**:
  - All parameters in the INI file should have a reasoned default value.
  - Users (via direct INI edit) or the GUI should be able to override these defaults.
  - The GUI must load current settings from the INI file upon startup.

## 2. Production Module Conversion Status

Modules are categorized by conversion approach. Core production modules will be edited, while adapter modules will be phased out.

### Core Engine Modules

| Module                      | Path                                 | Status                      | Approach |
| --------------------------- | ------------------------------------ | --------------------------- | -------- |
| EMA Allocation Model        | `models/ema_allocation_model_v4.py`  | **L2 Converted**            | Edit     |
| Orders Engine (V4)          | `engine/orders_v4.py`                | **L2 Verified (No Change)** | Edit     |
| Portfolio Manager (V4)      | `engine/portfolio_v4.py`             | **L2 Converted**            | Edit     |
| Trade Execution Engine (V4) | `engine/execution_v4.py`             | **L2 Converted**            | Edit     |
| Data Loader (V4)            | `engine/data_loader_v4.py`           | Converted                   | Keep     |
| Legacy Data Loader          | `data/data_loader.py`                | Not Converted               | Archive  |
| Performance Reporting       | `reporting/performance_reporting.py` | Not Converted               | Archive  |

### V4 Reporting Implementation Plan

**Strategic Priority**: Implementation and stabilization of V4 reporting (config-driven) is now a high priority (Phase 2 in `Task_List_CPS_v4.md`) before full GUI integration.

Based on analysis of the v3_reporting modules and reporting directory structure, the following implementation plan will be followed:

1. **Directory Structure**

   - Create new `v4_reporting` directory at the same level as `v3_reporting`
   - Mirror the structure of `v3_reporting` with v4 equivalents
   - No legacy adapters or parameter registry integration

2. **Module Conversion Strategy**

   - Each v3 module will have a v4 equivalent with `v4_` prefix
   - Split any module approaching 450 lines into smaller modules
   - Implement direct CPS v4 parameter access (no adapters)
   - Maintain function signatures where possible but remove v3-specific parameters
   - Follow the same pattern as `engine/data_loader_v4.py` for CPS v4 integration

3. **Modules to Create**

   | V3 Module                              | V4 Module                  | Description                                  | Status      |
   | -------------------------------------- | -------------------------- | -------------------------------------------- | ----------- |
   | `v3_performance_report.py` (168 lines) | `v4_performance_report.py` | Performance reporting with CPS v4 parameters | Not Started |
   | `v3_allocation_report.py` (247 lines)  | `v4_allocation_report.py`  | Allocation reporting with CPS v4 parameters  | Not Started |
   | `parameter_registry_integration.py`    | N/A                        | Not needed in v4 (direct parameter access)   | N/A         |

4. **Implementation Approach**

   - Create each module from scratch (no copy/paste from v3)
   - Implement only the functionality needed for v4
   - Use type hints and proper docstrings
   - Keep each module under 450 lines
   - Create utility modules for shared functionality if needed
   - Follow the same CPS v4 pattern as `engine/data_loader_v4.py`

5. **Testing Strategy**
   
   - Create test cases for each v4 module
   - Compare outputs with v3 modules to ensure consistency
   - Document any differences in behavior
   - Verify all parameters are accessed through CPS v4 settings

6. **Dependencies**
   
   - Depends on `engine/data_loader_v4.py` for data loading
   - Should not depend on any v3 modules
   - Must work with existing CPS v4 parameter system

### Next Steps

1. Create `v4_reporting` directory structure
2. Implement `v4_performance_report.py` as the first module
3. Update any imports to use the new v4 modules
4. Test thoroughly before archiving v3 modules

### GUI Modules

**Note on GUI Module Status**: "Converted" for GUI modules primarily indicates that the codebase has been updated for CPS V4 parameter handling (e.g., reading from `settings`, widget creation, parameter collection logic). Full operational integration and testing of the GUI for triggering backtests is deferred until after the core engine and V4 reporting system are stabilized via direct configuration-driven testing (see `Task_List_CPS_v4.md` Phase 4).

| Module                 | Path                                | Status        | Approach |
| ---------------------- | ----------------------------------- | ------------- | -------- |
| Config Interface       | `app/gui/config_interface.py`       | Not Converted | Archive  |
| Main GUI               | `app/gui/main.py`                   | Not Converted | Archive  |
| Main GUI V3            | `app/gui/main_v3.py`                | Not Converted | Archive (pending `main_v4.py` finalization)  |
| V3 GUI Actions         | `app/gui/gui_actions_v4.py`         | Converted     | Edit     |
| V3 GUI Core            | `app/gui/gui_core_v4.py`            | Converted     | Edit     |
| V3 Parameter Widgets   | `app/gui/parameter_widgets_v4.py`   | Converted     | Edit     |
| V3 Register Parameters | `app/gui/v3_register_parameters.py` | Not Converted | Archived |

### Reporting Modules

| Module                   | Path                                    | Status        | Approach |
| ------------------------ | --------------------------------------- | ------------- | -------- |
| Performance Reporting    | `reporting/performance_reporting.py`    | Not Converted | Archived |
| Allocation Report        | `reporting/allocation_report.py`        | Not Converted | Convert  |
| Performance Reporting BU | `reporting/performance_reporting_BU.py` | Not Converted | Archive  |

### Utility Modules

| Module     | Path                  | Status        | Approach |
| ---------- | --------------------- | ------------- | -------- |
| Date Utils | `utils/date_utils.py` | Not Converted | Convert  |
| Trade Log  | `utils/trade_log.py`  | Not Converted | Convert  |

### Legacy Adapter Modules (To Phase Out)

| Module                       | Path                                         | Status        | Approach  |
| ---------------------------- | -------------------------------------------- | ------------- | --------- |
| Legacy Bridge Report Adapter | `v3_engine/V3_perf_repadapt_legacybridge.py` | Not Converted | Phase Out |
| Parameter Conversion Helper  | `v3_engine/V3_perf_repadapt_paramconvert.py` | Not Converted | Phase Out |
| Performance Reporter Adapter | `v3_engine/performance_reporter_adapter.py`  | Not Converted | Phase Out |
| Parameter Registry           | `v3_engine/parameter_registry.py`            | Not Converted | Phase Out |
| Parameter Optimizer          | `v3_engine/parameter_optimizer.py`           | Not Converted | Phase Out |
| GUI Sync Interface           | `v3_engine/parameter_gui_sync.py`            | Not Converted | Phase Out |
| EMA Strategy Adapter         | `v3_engine/ema_v3_adapter.py`                | Not Converted | Phase Out |
| Config Adapter               | `v3_engine/config_adapter.py`                | Not Converted | Phase Out |
