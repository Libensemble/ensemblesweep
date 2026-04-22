---
name: cli_python_sweep
description: Perform a parameter sweep over a Python function using the ensemblesweep CLI.
---

# CLI Python Sweep

Use this skill to evaluate a Python function across a grid of parameters using `ensemblesweep py`. This is the fastest way to generate parallel data for any Python function without writing extra scripts.

## Prerequisites

- The Python function must be importable (i.e., in a file in the current directory or on the `PYTHONPATH`).
- The function should take named arguments corresponding to the variables in the sweep.

## Usage

### 1. Perform a Dry Run (Mandatory Guardrail)

Always perform a dry run first, especially for grids with more than 2 dimensions, to verify the total number of evaluations and parameter types.

```bash
ensemblesweep py --func module_name.function_name \
                 --var "param1=start:stop:num" \
                 --var "param2=val1,val2,val3" \
                 --dry-run
```

Review the output to ensure the "Total evaluations" is reasonable and the sample combinations look correct.

### 2. Execute the Sweep

Run the actual sweep, specifying the number of workers and desired output formats.

```bash
ensemblesweep py --func module_name.function_name \
                 --var "param1=-1.0:1.0:21" \
                 --var "param2=A,B,C" \
                 --workers 4 \
                 --save-csv results.csv \
                 --quiet
```

## Tips for Agents

- **Quiet Mode**: Use `--quiet` to suppress libEnsemble logs for cleaner terminal output.
- **Save Formats**:
  - Use `--save-csv` or `--save-json` for easy parsing.
  - Use `--save-pandas` for Parquet format (best for large datasets).
  - Use `--save-numpy` for raw binary data.
- **Variable Syntax**:
  - `key=val1,val2`: Discrete list.
  - `key=start:stop:num`: Linear range (`np.linspace`).
- **Imports**: Ensure you are in the same directory as the target module, as `ensemblesweep` automatically identifies the current working directory.
- **Remote Execution**: You can pass `--globus-compute-endpoint <UUID>` to execute the grid remotely. However, for complex environments/dependencies, prefer using the `programmatic_sweep_api` skill to handle data placement and imports correctly.
