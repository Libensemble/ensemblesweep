---
name: cli_executable_sweep
description: Perform a parameter sweep over an external executable using the ensemblesweep CLI.
---

# CLI Executable Sweep

Use this skill to evaluate a compiled binary or shell script across a parameter grid using `ensemblesweep exe`. The variables in the sweep are passed as positional arguments to the executable.

## Prerequisites

- The executable must be runnable (e.g., `./my_binary` or `/path/to/exe`).
- Arguments are passed in the order they are defined in the command line or `Data` object.

## Usage

### 1. Perform a Dry Run (Mandatory Guardrail)

Always perform a dry run first to verify the total number of evaluations and parameter types.

```bash
ensemblesweep exe --app ./my_binary \
                  --var "param1=start:stop:num" \
                  --var "param2=val1,val2,val3" \
                  --dry-run
```

### 2. Execute the Sweep

Run the actual sweep, specifying the number of workers and how to read the output.

```bash
ensemblesweep exe --app ./my_binary \
                  --out-file results.stat \
                  --var "mass=1.0,2.0,3.0" \
                  --var "velocity=10.0:100.0:10" \
                  --workers 4 \
                  --save-csv sweep_results.csv \
                  --quiet
```

### Expectations for Output Format

- **Stdout**: If `--out-file` is NOT specified, `ensemblesweep` will read the **last line of the executable's stdout**. This line must contain the result (e.g., a single float or a space-separated row of floats).
- **File Output**: If `--out-file` IS specified, the executable must write its results into that file. `ensemblesweep` will read the last line of that file.
- **Reading Data**: The output (either from stdout or a file) is read using `np.loadtxt`. The last row will be taken as the result for that evaluation.

## Communication Policy (Critical)

Executables often involve complex MPI environments or library path dependencies that are brittle.

- **DO NOT attempt to auto-fix environmental issues** (like MPI runtime errors, library loading failures, or segmentation faults) by repeatedly changing environment variables or re-compiling without explicit user approval.
- **COMMUNICATE IMMEDIATELY**: If the output column is empty or results are not being produced, examine the worker error logs (usually in `workflow_xxxx/sweep_xxxx/simxxxx/*.err`) and report the findings to the user.
- **Request Guidance**: State clearly what you've found (e.g., "MPI initialization failed with PMI1 error") and ask for the next step.

## Tips for Agents

- **Absolute Paths**: For the `--app` flag, it is often safer to use an absolute path (`$(pwd)/my_binary`) or a clear relative path (`./my_binary`).
- **Dry-Run first**: Use `--dry-run` to check the grid size before launching parallel processes.
- **Save results**: Always use one of the `--save-*` flags to ensure the final data is persisted in a format you can easily parse later.
- **Remote Execution**: You can pass `--globus-compute-endpoint <UUID>` to execute the sequence remotely. However, for executables with complex file dependencies, prefer using the `programmatic_sweep_api` skill to handle data movement explicitly.
