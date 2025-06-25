# User-Defined Parameter Reference CPS V4

This document outlines the user's preferred conceptual model for parameter types within the CPS V4 system.

## Parameter Classifications

The following are the four primary classes of parameter types:

1. **`SimpleA`**: A simple alphanumeric single value.
   * Example: `risk_free_ticker = '^IRX'`

2. **`SimpleN`**: A simple numeric single value.
   * Example: `initial_capital = 1000000`

3. **`ComplexN`**: A structure containing `optimize` (TRUE/FALSE), `default_value`, `min_value`, `max_value`, and `increment`.
   * All values (except optimize) are numeric.
   * Example: For a parameter like `ema_short_period`, it might be `(optimize=True, default_value=12, min_value=5, max_value=20, increment=1)`

4. **`AlphaList`**: A comma-separated list of alphanumeric values.
   * Example: `tickers = ('SPY', 'SHV', 'EFA', 'TLT', 'PFF')`
   * Note: This could represent a list of items to iterate over, or a list of choices for a selection.

Each variable is one of the things below, not all of them at once - their structure defines the way the work; still confused?

-------
For now

* we will define GUI placement each parameter map to specific locations
* how they function/can be optimized is a function of their structure
* we dont need gui_display_name = display system name
  .description = can be just a comment - no "field" needed I think
  .choices (for categorical/AlphaList) = that is a pick list, just assume we will need to tweak custom code - think of a list or loop depending on parameter - for each one. Can you do super simple flag that more needed later; for now we run with just default setting.

`tickers = ('SPY', 'SHV', 'EFA', 'TLT', 'PFF')` = this is wrong. It should be
tickers = (Group1ETFBase, ETFpicklist) ; Group1ETFBase = current default. ETFpicklist = multiple lists to pick from = dropdown list etc

ETFpicklist
Group1ETFBase = ('SPY', 'SHV', 'EFA', 'TLT', 'PFF')`
Group2ETF= ('GLD', 'SLV', 'OIL')`

### Type Recognition by Structure

The system recognizes parameter types based on these structural patterns:

1. **SimpleA**: Default type for string values, booleans, or anything that doesn't match other patterns
   * Example:

     ```ini
     risk_free_ticker = ^IRX
     ```

2. **SimpleN**: Automatically detected when the value is a numeric type (int or float)
   * Example:

     ```ini
     initial_capital = 1000000
     ```

3. **ComplexN**: Detected when the value is a tuple/dictionary containing optimization metadata
   * Example:

     ```ini
     ema_short_period = (optimize=True, default_value=12, min_value=5, max_value=20, increment=1)
     ```

4. **AlphaList**: Detected when the value is either:
   * A list/tuple of values
   * A tuple reference to named lists:

     ```ini
     tickers = (Group1ETFBase, ETFpicklist)
     ```

### No Type Flags Required

The beauty of this approach is that users don't need to add explicit type flags. They simply format their parameters according to the structure that matches their intended type:

* To make a parameter optimizable (ComplexN), they just need to use the tuple format with optimization attributes

* To convert a SimpleN to a ComplexN, they just change the format from

  ```ini
  value = 10
  ```

  to

  ```ini
  value = (optimize=False, default_value=10, min_value=5, max_value=15, increment=1)
  ```

* To create an AlphaList, they either use a comma-separated list or reference named lists

## Parameter Runtime Behavior and Optimization

### 1. Parameter Overrides in `run_params`

The `run_params` dictionary, passed from `MainWindowV4` to `run_backtest_action_v4`, holds specific values explicitly set or modified by the user through the GUI for a particular backtest run. These GUI-driven values act as overrides to the default configurations loaded from the `settings` object (which originates from INI files).

**Logic Flow:**

1. **Base Configuration**: Default parameter values are loaded from INI files into the global `settings` object.
2. **GUI Display**: The GUI (`MainWindowV4` using `v3_parameter_widgets_v4`) displays these parameters, allowing users to modify them for the upcoming backtest.
3. **Parameter Collection**: When "Run Backtest" is initiated, `MainWindowV4` collects all current values from GUI widgets into the `run_params` dictionary.
4. **Passing to Backtest Action**: This `run_params` dictionary is passed to `run_backtest_action_v4`.
5. **Parameter Precedence**: Inside `run_backtest_action_v4` (and subsequently in data loaders, models, engines, and reporting modules that consume these parameters):
   * The system first checks if a required parameter value is present in `run_params`.
   * If yes, the value from `run_params` (the GUI override) is used.
   * If no, the default value is retrieved from the global `settings` object.

This hierarchy ensures that GUI-set values in `run_params` take precedence over `settings` defaults.

### 2. Optimization Loop Handling in CPS_v4

Optimization loops are controlled by INI file definitions and GUI checkboxes, with `run_backtest_action_v4` processing only a single parameter set per call.

**The Locus of Control Moves**: The optimization loop itself is managed by the calling GUI component, `MainWindowV4` (or a dedicated optimization manager module invoked by `MainWindowV4`), not within `run_backtest_action_v4`.

**Detailed Workflow:**

1. **INI File Configuration (`settings`)**:
   * Parameters intended to be optimizable are defined in INI files.
   * Attributes for optimizable parameters include:
     * `optimizable: true` (indicates GUI should offer an "Optimize" checkbox).
     * `optimize_values: [value1, value2, value3]` (for discrete value optimization).
     * `optimize_range: [min, max, step]` (for numeric range optimization).
   * `v3_parameter_widgets_v4.py` uses `param_details.get('optimizable', False)` to determine if an "Optimize" checkbox should be displayed.

2. **GUI Control (`MainWindowV4` & `v3_parameter_widgets_v4.py`)**:
   * `create_parameter_widgets_v4` generates an "Optimize" `QCheckBox` for each parameter marked `optimizable: true` in its settings definition.
   * Users can check/uncheck these "Optimize" boxes in the GUI.

3. **Optimization Execution (Responsibility of `MainWindowV4` or a helper module)**:
   * When the user clicks "Run Backtest":
     * a. `MainWindowV4` gathers all current values from GUI widgets (including the state of "Optimize" checkboxes and any manually entered values, min/max/step for optimization if GUI allows editing these). This forms `base_run_params`.
     * b. It identifies all parameters for which the "Optimize" checkbox is ticked and for which optimization values/ranges are defined.
     * c. **Parameter Combination Generation**: `MainWindowV4` (or its helper) generates all unique combinations of parameter values (e.g., using `itertools.product`).
     * d. **Iterative Calls to `run_backtest_action_v4`**:
       * `MainWindowV4` loops through each generated parameter combination.
       * In each iteration, it prepares `iteration_run_params` (a copy of `base_run_params` updated with the specific parameter values for the current optimization combination).
       * It then calls `run_backtest_action_v4(self, iteration_run_params)`.
     * e. **Single Run Focus**: `run_backtest_action_v4` receives `iteration_run_params` and executes a single backtest using exactly those parameters, unaware of any outer optimization loop.

4. **Results Aggregation**:
   * If a combined report or comparison of all optimization runs is needed, `MainWindowV4` (or its helper) is responsible for collecting key metrics from the results of each `run_backtest_action_v4` call and compiling a summary.
   * Individual reports for each run are still generated by `run_backtest_action_v4`.

**Summary of Change**: The core backtest logic (`run_backtest_action_v4`) is simplified to handle only one scenario at a time. The complexity of generating parameter sets for optimization and iterating through them is moved to the GUI/controller layer (`MainWindowV4`). This modular approach facilitates maintenance and future extensions of optimization strategies.
