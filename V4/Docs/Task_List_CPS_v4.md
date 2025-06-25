# Central Parameter System v4 - Active Task List

> **Last Updated**: 2025-06-21  
> **Current Focus**: Signal Generator Validation

## Active Work Items

### 1. Signal Generator Validation (In Progress)
**Objective**: Verify signal generation outputs match expected Top-N allocation strategy

**Key Files**:
- `run_main_v4_prod2.bat` - Main execution script
- `v4/run_signal_generation.py` - Core signal logic
- `v4/engine/signal_generator_v4.py` - Signal generation implementation

**Verification Steps**:

1. Run `run_main_v4_prod2.bat`
2. Check console for errors/warnings
3. Verify output files in `v4_trace_outputs/`:
   - `ranking_{timestamp}.csv` - Asset ranks (1 = best)
   - `signal_history_full_{timestamp}.csv` - Allocation weights
4. Confirm Top N assets have equal weights (1/N)
5. Verify all other assets have 0 weight

**Key Parameters**:
- `system_top_n` - Number of top assets to select
- `st_lookback`, `mt_lookback`, `lt_lookback` - EMA periods

### 2. Reporting System (Next Up)
**Objective**: Implement performance and allocation reporting

**Tasks**:

- [ ] Complete `v4_performance_report.py` implementation
- [ ] Implement `v4_allocation_report.py`
- [ ] Add XLSX and PNG output generation
- [ ] Document reporting parameters
- [ ] Integrate with production pipeline

## Completed Items

- Core engine refactoring (100% complete)
- Signal generator factory implementation
- T+0 execution in core engine
- Comprehensive tracing utilities

## Important Notes

- All required parameters must be present in CPS v4 settings
- Never use `.get(..., fallback)` for required parameters
- Preserve all production logic during conversions

> **Last Updated**: 2025-06-21  
> **Current Focus**: Signal Generator Validation

## Active Work Items

### 1. Signal Generator Validation (In Progress)
**Objective**: Verify signal generation outputs match expected Top-N allocation strategy

**Key Files**:
- `run_main_v4_prod2.bat` - Main execution script
- `v4/run_signal_generation.py` - Core signal logic
- `v4/engine/signal_generator_v4.py` - Signal generation implementation

**Verification Steps**:
1. Run `run_main_v4_prod2.bat`
2. Check console for errors/warnings
3. Verify output files in `v4_trace_outputs/`:
   - `ranking_{timestamp}.csv` - Asset ranks (1 = best)
   - `signal_history_full_{timestamp}.csv` - Allocation weights
4. Confirm Top N assets have equal weights (1/N)
5. Verify all other assets have 0 weight

**Key Parameters**:
- `system_top_n` - Number of top assets to select
- `st_lookback`, `mt_lookback`, `lt_lookback` - EMA periods

### 2. Reporting System (Next Up)
**Objective**: Implement performance and allocation reporting

**Tasks**:
- [ ] Complete `v4_performance_report.py` implementation
- [ ] Implement `v4_allocation_report.py`
- [ ] Add XLSX and PNG output generation
- [ ] Document reporting parameters
- [ ] Integrate with production pipeline

## Completed Items
- Core engine refactoring (100% complete)
- Signal generator factory implementation
- T+0 execution in core engine
- Comprehensive tracing utilities

## Important Notes
- All required parameters must be present in CPS v4 settings
- Never use `.get(..., fallback)` for required parameters
- Preserve all production logic during conversions
**Priority**: High

**Key Tasks**:

- [ ] Profile order execution performance
- [ ] Optimize trade processing pipeline
- [ ] Implement batch processing for orders
- [ ] Add performance metrics for execution
- [ ] Optimize memory usage during execution
- [ ] Improve concurrent order handling

**Success Criteria**:

- 25% improvement in order processing speed
- Reduced memory footprint during execution
- Maintained or improved accuracy of execution
- Comprehensive performance metrics in place

### [Task 3.3] Optimize Benchmark Module

**Status**: NOT STARTED  
**Priority**: Medium

**Key Tasks**:

- [ ] Profile benchmark calculation
- [ ] Optimize performance-critical sections
- [ ] Add caching for benchmark data
- [ ] Document performance characteristics
- [ ] Implement lazy loading where applicable
- [ ] Optimize memory usage in benchmark calculations

**Success Criteria**:

- 40% improvement in benchmark calculation speed
- Reduced memory usage during benchmark calculations
- Comprehensive documentation of performance characteristics
- No impact on benchmark accuracy

## Phase 4: Full System Integration (0% Complete)

### [Task 4.1] GUI Integration

**Status**: NOT STARTED  
**Priority**: High

**Key Tasks**:

- [ ] Connect GUI to V4 engine
- [ ] Implement V4 parameter controls in GUI
- [ ] Add progress reporting for long-running operations
- [ ] Implement error handling and user feedback
- [ ] Ensure all V4 parameters are exposed in the GUI
- [ ] Implement parameter validation in the UI
- [ ] Add tooltips and help text for all parameters

**Success Criteria**:

- All V4 parameters accessible through the GUI
- Intuitive and responsive user interface
- Clear error messages and validation feedback
- Smooth integration with the V4 engine

### [Task 4.2] End-to-End Testing

**Status**: NOT STARTED  
**Priority**: High

**Key Tasks**:

- [ ] Create test scenarios covering all major features
- [ ] Validate GUI-Engine-Reporting integration
- [ ] Test error conditions and recovery
- [ ] Document test procedures and results
- [ ] Create automated test scripts
- [ ] Test with various parameter combinations
- [ ] Verify all reporting outputs

**Success Criteria**:

- 100% test coverage for critical paths
- All test cases documented and passing
- Clear documentation of test procedures
- Automated regression test suite in place

## Phase 5: Documentation and Production Validation (0% Complete)

### [Task 5.1] User Documentation

**Status**: NOT STARTED  
**Priority**: Medium

**Key Deliverables**:

- [ ] User guide for V4 features
- [ ] API documentation
- [ ] Migration guide from V3
- [ ] Example configurations
- [ ] Video tutorials for key workflows
- [ ] FAQ and troubleshooting guide

**Success Criteria**:

- Comprehensive coverage of all V4 features
- Clear, step-by-step instructions
- Examples for common use cases
- Easy navigation and search functionality

### [Task 5.2] Developer Documentation

**Status**: NOT STARTED  
**Priority**: Medium

**Key Deliverables**:

- [ ] Architecture overview
- [ ] Module documentation
- [ ] Contribution guidelines
- [ ] Testing methodology
- [ ] Code style guide
- [ ] Performance optimization guide
- [ ] API reference documentation

**Success Criteria**:

- Complete API reference
- Clear contribution workflow
- Comprehensive testing guidelines
- Easy onboarding for new developers

## Phase 6: Deployment and Verification (0% Complete)

### [Task 6.1] Deployment Planning

**Status**: NOT STARTED  
**Priority**: High

**Key Tasks**:

- [ ] Create deployment checklist
- [ ] Document deployment procedure
- [ ] Prepare rollback plan
- [ ] Verify environment requirements
- [ ] Create deployment scripts
- [ ] Document post-deployment verification steps
- [ ] Train operations team

**Success Criteria**:

- Clear, step-by-step deployment guide
- Automated deployment scripts
- Comprehensive rollback procedure
- Documented environment requirements

### [Task 6.2] Production Verification

**Status**: NOT STARTED
**Priority**: Critical

**Key Tasks**:

- [ ] Verify all core functionality
- [ ] Validate performance in production environment
- [ ] Monitor for any issues
- [ ] Document verification results
- [ ] Conduct load testing
- [ ] Verify data integrity
- [ ] Validate security controls

**Success Criteria**:

- All core functionality verified
- Performance meets requirements
- No critical issues in production
- Comprehensive verification report


- All V4 reporting modules use CPS V4 parameters directly.
- No dependencies on V3 reporting code.

**Implementation Steps**:

1. Create `v4_reporting` directory.
2. Implement `v4_performance_report.py` (referencing logic from V3 but using CPS V4; keep under 450 lines).
3. Implement `v4_allocation_report.py` (similarly, referencing V3 logic, using CPS V4; keep under 450 lines).
4. Develop unit/integration tests for new reporting modules.

### [Task 2.2] Develop Configuration-Driven Test Harness for Engine & Reporting

**Priority**: HIGH
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Scripts or procedures to execute `engine/backtest_v4.py` (or main backtest runner) using parameters solely from `settings_parameters_v4.ini`.
- Ability to easily run various test scenarios by modifying the INI file or providing scenario-specific INI files.

**Implementation Steps**:

1. Identify or create a main script for command-line backtest execution (e.g., `run_backtest_cli.py`).
2. Ensure this script loads parameters from `settings_CPS_v4.py`.
3. Create a suite of test INI files covering different strategies, data, and edge cases.
4. Document procedure for running tests via this harness.

### [Task 2.3] Engine & Reporting Integration Testing and Debugging

**Priority**: HIGHEST
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Verified accuracy of backtest engine outputs (e.g., trade logs, portfolio values) across multiple scenarios.
- Verified correctness, completeness, and formatting of all V4 reports.
- Comprehensive log of all issues found and fixed in `engine_v4` modules or `v4_reporting` modules during this phase.
- Confirmation that V4 system (engine + reporting) is stable and reliable when driven by configuration files.

**Implementation Steps**:

1. Execute multiple backtest runs using the test harness (Task 2.2) and diverse configurations.
2. Systematically compare V4 report outputs against expectations (and V3 reports for logic validation, where applicable).
3. Analyze engine outputs (logs, intermediate data if any) for correctness.
4. Identify, log (in `Problem_Changes_Log_CPS_v4.md`), and fix any discrepancies or bugs.

## Phase 3: Advanced Parameter Structure & GUI Code Conversion

**Overall Goal**: Prepare GUI components for V4 by completing code-level conversion and implementing any advanced parameter structures needed for optimal user experience. Full GUI operational integration is deferred to Phase 4.

**Priority**: Medium

### [Task 3.1] Define and Implement Advanced Parameter Structure Enhancements (If Needed)

**Priority**: Medium (Evaluate necessity based on GUI display/interaction needs)
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Updated `settings_CPS_v4.py` (or new modules) if enhancements for GUI (e.g., AlphaList, AlphaGroup, more metadata) are required.
- Clear documentation on defining parameters for GUI consumption.
- Example INI configurations demonstrating any new structures.

**Implementation Steps**:

1. Review GUI requirements for parameter display, grouping, and conditional logic.
2. If current CPS V4 structure is insufficient, design and implement enhancements (e.g., for AlphaList, AlphaGroup).
3. Update `settings_CPS_v4.py` and INI examples accordingly.

### [Task 3.2] Complete GUI Module Code Conversion to CPS V4

**Priority**: Medium
**Status**: IN PROGRESS (e.g., `gui_core_v4.py` parameter collection)
**Est. Completion**: TBD

**Key Deliverables**:

- All GUI modules (`gui_actions_v4.py`, `gui_core_v4.py`, `parameter_widgets_v4.py`, and `main_v4.py` if it's the target launcher) are fully compliant with CPS V4 for parameter definition, loading, display, and collection.
- GUI can correctly load and display parameters from `settings_CPS_v4.py`.
- Obsolete V3 GUI helper functions/logic removed or updated.

**Implementation Steps**:

1. Test and finalize `gui_core_v4.py` parameter collection and display logic.
2. Review and update `gui_actions_v4.py` for V4 parameter handling.
3. Confirm `parameter_widgets_v4.py` is fully V4 compliant.
4. Clarify the role of `app/gui/main_v4.py`. If it's the intended V4 GUI launcher, convert its backtest execution logic to use V4 methods (e.g., instantiating `MainWindowV4` from `gui_core_v4.py` or calling `run_backtest_action_v4`). If `gui_core_v4.py`'s `if __name__ == "__main__":` is the entry, `main_v4.py` might be archived or repurposed.

## Phase 4: Full GUI Integration & End-to-End Testing

**Overall Goal**: Integrate the V4-compliant GUI with the stabilized backtesting engine and reporting system. Conduct comprehensive end-to-end testing through the GUI.

**Priority**: High (After Phases 1-3 are complete)

### [Task 4.1] Integrate GUI to Trigger V4 Backtests

**Priority**: HIGH
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- GUI successfully launches backtests using parameters collected from widgets, processed by `gui_core_v4.py`.
- Backtest results or status are appropriately communicated back to the GUI (e.g., completion message, link to reports).

**Implementation Steps**:

1. Ensure the "Run Backtest" action in the GUI correctly calls `_run_backtest` in `gui_core_v4.MainWindowV4`.
2. Implement any necessary feedback mechanisms to the user (e.g., "Running...", "Backtest Complete", error messages).

### [Task 4.2] Comprehensive End-to-End System Testing via GUI

**Priority**: HIGHEST
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Successful execution of various backtest scenarios initiated from the GUI.
- Verification that GUI-driven runs produce identical results (engine outputs and reports) to config-driven runs from Phase 2.
- All GUI functionalities related to parameter input, backtest execution, and status display are working correctly.

**Implementation Steps**:

1. Define a suite of test cases covering different parameter configurations available in the GUI.
2. Execute these test cases via the GUI.
3. Compare results with baseline results from Phase 2 testing.
4. Debug any discrepancies found in the GUI-to-engine pipeline.

## Phase 5: Documentation and Production Validation

(Content remains largely the same, ensure it aligns with V4 components)

**Overall Goal**: Finalize all project documentation, including user guides for the V4 system (parameters, GUI, reporting). Conduct production validation exercises.

**Priority**: High
**Status**: NOT STARTED

## Phase 6: Deployment and Verification

(Content remains largely the same)

**Overall Goal**: Deploy the fully tested and validated CPS V4 system. Verify its operation in the production/target environment.

**Priority**: High
**Status**: NOT STARTED

## Appendix A: Parameter Discovery and Migration Plan (Task 1.2)

1. Design data structures/classes within the settings system to store:
  - GUI display labels/descriptions.
  - GUI grouping information (e.g., for tabs or sections).
2. Implement logic in the settings system to parse and manage this new metadata from INI files or other definition sources.
3. Develop mechanisms for parameter access functions (e.g., `settings.get_with_metadata()`) to retrieve this enhanced information.
4. Define and implement the `AlphaList` parameter type:
  - Storage format in INI/definitions.
  - Retrieval logic.
5. Define and implement the `AlphaGroup` parameter type:
  - Storage format for choices and their associated routing/data.
  - Logic for handling conditional routing based on selection.
6. Design and implement a system for additional parameter metadata (e.g., flags for GUI visibility, reporting inclusion):
  - Evaluate and decide between separate lookup tables vs. embedded flags.
  - Implement the chosen approach.
7. Enhance the parameter loading system:
  - Ensure robust handling of default values from INI for all new structural elements.
  - Solidify mechanisms for user/GUI overrides.
8. Write unit tests for all new structural components and logic.

**Success Criteria**:

- Parameter system can store and retrieve labels, grouping, AlphaList, AlphaGroup, and other metadata.
- INI configurations clearly define these new structures.
- Unit tests pass for all new functionalities.

### [Task 2.2] Integrate Enhanced Structure into System & Existing Conversions

**Priority**: HIGH
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Updated parameter access patterns across the codebase.
- Revised INI configuration files (`default_settings_CPS_v4.ini` and examples) using the new structure.
- Report on necessary tweaks to already-converted V4 modules.

**Implementation Steps**:

1. Update core parameter access mechanisms (e.g., `settings.get()`, or introduce new ones) to expose and utilize the new structural information where appropriate.
2. Review and refactor the `default_settings_CPS_v4.ini` file to fully utilize the new parameter structure (labels, groups, AlphaList/Group, metadata).
3. Review all previously converted V4 modules (e.g., `data_loader_v4.py`, `ema_allocation_model_v4.py`):
   - Identify parameters that should be updated to use `AlphaList`, `AlphaGroup`, or require new metadata.
   - Implement necessary tweaks to these modules to align with the enhanced structure.
4. Document any changes to parameter access patterns for developers.

**Success Criteria**:

- INI files are updated and validated against the new structure.
- Previously converted modules correctly use the enhanced parameter definitions.
- Parameter access throughout the system is consistent with the new capabilities.

### [Task 2.3] GUI Framework Integration

**Priority**: HIGH
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- GUI components capable of rendering and managing parameters based on labels, grouping, AlphaList, and AlphaGroup.
- Demonstration of GUI loading parameters from INI and reflecting their structure.

**Implementation Steps**:

1. Design and develop GUI widgets/components to:
   - Display parameters using their defined labels.
   - Organize parameters into groups (e.g., tabs, expandable sections) based on grouping metadata.
   - Handle `AlphaList` type parameters (e.g., editable lists).
   - Handle `AlphaGroup` type parameters (e.g., dropdowns that trigger conditional display/logic).
2. Ensure the GUI framework can load parameter definitions (including all new metadata) from the CPS V4 settings system.
3. Implement logic for the GUI to correctly reflect default values and allow user overrides, saving them back if applicable.
4. Test GUI interaction with various parameter types and structures.

**Success Criteria**:

- GUI dynamically renders based on parameter labels, groups, and types.
- `AlphaList` and `AlphaGroup` parameters are manageable through the GUI.
- GUI correctly loads and reflects INI settings, including defaults and overrides.

### [Task 2.4] Continue Module Conversions with Advanced Structure

**Priority**: MEDIUM
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Additional core modules converted to CPS V4, fully utilizing the advanced parameter structure.

**Implementation Steps**:

1. Identify the next set of core modules for conversion based on the project plan.
2. For each module, define its parameters using the full CPS V4 structure (labels, grouping, AlphaList/Group, metadata) in the INI/definition files.
3. Refactor the module to use the CPS V4 settings system for all parameter access.
4. Develop/update unit tests for the converted modules.

**Success Criteria**:

- Newly converted modules seamlessly integrate with the advanced parameter system.
- Parameters for these modules are fully defined with all necessary metadata.

### [Task 2.5] Comprehensive Testing and Documentation Update

**Priority**: MEDIUM
**Status**: NOT STARTED
**Est. Completion**: TBD

**Key Deliverables**:

- Test suite for the advanced parameter structure and its integrations.
- Updated developer documentation regarding the parameter system.

**Implementation Steps**:

1. Develop comprehensive integration tests for the advanced parameter features, including GUI interaction.
2. Update all relevant documentation (`Parameter_Reference_CPS_v4.md`, developer guides) to reflect the new parameter structures, types, and usage patterns.
3. Ensure examples in documentation are updated.

**Success Criteria**:

- Robust test coverage for the advanced parameter system.
- Documentation is complete and accurately describes the enhanced CPS V4.

## Phase 3: Core Module Conversion and Review

### Phase Specific Deliverables

- Converted core modules using CPS V4 parameters
- Review and validation of converted modules

### Steps

1. Continue converting core modules to use CPS V4 parameters
2. Review and validate converted modules for correctness and functionality
3. Ensure all converted modules are thoroughly tested

### Success Criteria

- All core modules are converted to use CPS V4 parameters
- Converted modules are reviewed and validated for correctness and functionality
- All converted modules are thoroughly tested

## Phase 4: Core Reporting (Week 2)

### Phase Specific Deliverables

- Performance report module
- Allocation report module
- Chart generator module
- Production validation cases

### Phase Specific Implementation Plan

1. Create performance_report_CPS_v4.py
  - Implement core metrics calculation
  - Support all V3 report features
  - Direct parameter passing
2. Create allocation_report_CPS_v4.py
  - Implement allocation analysis
  - Support all V3 report features
  - Direct parameter passing
3. Create chart_generator_CPS_v4.py
  - Implement visualization functions
  - Support all V3 chart types
  - Direct parameter passing
4. Develop production validation cases
  - Compare with V3 outputs using production data
  - Verify numerical accuracy
  - Validate visual consistency

### Success Criteria

- All reports generate correctly with production data
- Output matches V3 reports with same inputs
- All charts render correctly
- Validation cases pass with 100% accuracy

### Dependencies

- Phase 1 completion
  **Implementation Steps**:
1. Implement chart formatting functions matching current visuals
2. Create chart generation utilities for production data
3. Add support for multiple output formats
4. Add validation cases using production chart data

**Success Criteria**:

- Charts generated with production data match current outputs
- Visual formatting exactly matches current production charts
- Validation passes with actual production parameters

## Phase 4: Integration and API Design

### [Task 3.1] Create High-Level API

**Priority**: HIGH  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-14

**Key Deliverables**:

- `reports_CPS_v4.py`: High-level API module
- API documentation

**Implementation Steps**:

1. Define simple API functions
2. Implement parameter handling
3. Create integration with core modules
4. Write API documentation

**Success Criteria**:

- API functions are simple and intuitive
- Parameters correctly flow to underlying modules
- Documentation is clear and comprehensive

### [Task 3.2] Batch Processing Integration

**Priority**: MEDIUM  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-15

**Key Deliverables**:

- `batch_processor_CPS_v4.py`: Batch processing module
- Batch configuration files

**Implementation Steps**:

1. Implement batch processing functions
2. Create batch configuration handling
3. Add logging and error handling
4. Write integration tests

**Success Criteria**:

- Multiple reports can be processed in batch
- Configuration correctly controls processing
- Errors handled gracefully with logging

## Phase 5: Documentation and Production Validation

### [Task 4.1] User Documentation

**Priority**: HIGH  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-16

**Key Deliverables**:

- `User_Guide_CPS_v4.md`: User documentation
- `Parameter_Reference_CPS_v4.md`: Parameter reference

**Implementation Steps**:

1. Write user guide for parameter editing in production
2. Create comprehensive parameter reference with actual production values
3. Add examples from real production scenarios
4. Review and finalize documentation

**Success Criteria**:

- Documentation is clear and comprehensive for production use
- All parameters are documented with actual production effects
- Examples cover real production use cases

### [Task 4.2] Comprehensive Production Validation

**Priority**: HIGHEST  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-18

**Key Deliverables**:

- Production validation suite
- Performance comparison with current system
- Compliance verification with production standards

**Implementation Steps**:

1. Run validation across all modules with production data
2. Compare output against current production outputs
3. Validate all production scenarios and edge cases
4. Verify performance characteristics with production workloads

**Success Criteria**:

- All validation passes with production data
- Output exactly matches current production specifications
- All production edge cases handled correctly
- Performance meets or exceeds current production system

### [Task 4.3] Cutover Planning

**Priority**: HIGH  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-19

**Key Deliverables**:

- Cutover plan document
- Migration scripts
- Rollback procedures

**Implementation Steps**:

1. Identify all entry points to update
2. Create migration scripts for data
3. Define rollback procedures
4. Test cutover in staging environment

**Success Criteria**:

- All entry points identified
- Migration scripts work correctly
- Rollback procedures are viable

## Phase 6: Deployment and Verification

### [Task 5.1] Deployment

**Priority**: HIGHEST  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-20

**Key Deliverables**:

- Updated codebase with new system
- Deployment verification report

**Implementation Steps**:

1. Execute cutover plan
2. Update all entry points
3. Verify functionality
4. Monitor for issues

**Success Criteria**:

- System functions correctly after cutover
- All reports generate as expected
- No regression in functionality

### [Task 5.2] Final Documentation Update

**Priority**: MEDIUM  
**Status**: NOT STARTED  
**Est. Completion**: 2025-06-20

**Key Deliverables**:

- Updated user documentation
- Final system documentation

**Implementation Steps**:

1. Update documentation with final changes
2. Verify accuracy of all documentation
3. Ensure all examples are current
4. Add any additional notes from deployment

**Success Criteria**:

- Documentation accurately reflects deployed system
- All examples work as described

## Production Validation Procedures

### Running Production Validation

```batch
cd S:\Dropbox\Scott Only Internal\Quant_Python_24\Backtest_FinAsset_Alloc_Template
run_verify_CPS_v4.bat
```

### Validating Production Reports

1. Check output against current production reports
2. Verify all parameters flow correctly in production scenarios
3. Confirm formatting exactly matches current production outputs
4. Validate calculations against actual production data

## Dependency Table

**Note**: This table will require review and updates to reflect the new Phase 2 tasks and renumbering of subsequent phases.

| Task ID | Depends On                   | Blocks                  |
| ------- | ---------------------------- | ----------------------- |
| 1.1     | -                            | 1.2, 1.3, 2.1, 2.2, 2.3 |
| 1.2     | 1.1                          | 2.1, 2.2, 2.3           |
| 1.3     | 1.1                          | 2.1, 2.2, 2.3, 4.2      |
| 2.1     | 1.1, 1.2, 1.3                | 3.1                     |
| 2.2     | 1.1, 1.2, 1.3                | 3.1                     |
| 2.3     | 1.1, 1.2, 1.3                | 3.1                     |
| 3.1     | 2.1, 2.2, 2.3                | 3.2, 4.2                |
| 3.2     | 3.1                          | 4.2                     |
| 4.1     | 1.2                          | 5.2                     |
| 4.2     | 1.3, 2.1, 2.2, 2.3, 3.1, 3.2 | 4.3                     |
| 4.3     | 4.2                          | 5.1                     |
| 5.1     | 4.3                          | 5.2                     |
| 5.2     | 4.1, 5.1                     | -                       |

## Related Documents

- [Overview](./Overview_CPS_v4.md)
- [Changes Log](./Problem_Changes_Log_CPS_v4.md)
- [User Guide](./User_Guide_CPS_v4.md)
- [Parameter Reference](./Parameter_Reference_CPS_v4.md)

**Last Updated**: 2025-06-06
