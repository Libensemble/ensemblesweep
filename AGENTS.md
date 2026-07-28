# AGENTS.md

Guidance for coding agents working in this repository. This file is intentionally more operational than the README: it captures architecture, current design decisions, and pitfalls that are easy to miss.

## Project overview

`ensemblesweep` is a small Python package for parameter sweeps backed by [libEnsemble](https://libensemble.readthedocs.io/). It supports:

- Sweeping Python objective functions.
- Sweeping external executables.
- A simple `Sweep` API.
- A `concurrent.futures`-style `SweepExecutor` API.
- A Click-based CLI.

The package source lives under `src/ensemblesweep/`.

## Important files

- `src/ensemblesweep/data.py`
  - Defines `Data`.
  - Builds the Cartesian product of input parameters.
  - Converts parameter combinations into libEnsemble `H0` arrays via `to_h0()`.

- `src/ensemblesweep/sweep.py`
  - Defines `Sweep`.
  - Owns libEnsemble setup and execution.
  - Keeps the raw libEnsemble history in `self._H_total`.
  - Tracks completed count in `self.evaluated`.
  - Exposes `self.results` as a `SweepResults` view over all completed rows.

- `src/ensemblesweep/results.py`
  - Defines canonical result types:
    - `SweepResult`: one completed evaluation.
    - `SweepResults`: collection view over completed rows or a submitted batch.
  - This replaces the older `ResultWrapper` concept. Do not reintroduce a parallel result wrapper unless there is a strong reason.

- `src/ensemblesweep/executor.py`
  - Defines `SweepExecutor`.
  - Provides a `concurrent.futures`-style interface.
  - `submit_sweep(...)` creates a `Sweep` and returns a single `Future`.
  - `submit(sweep, n=None)` submits an existing `Sweep`, optionally for a partial batch.

- `src/ensemblesweep/sim_funcs.py`
  - libEnsemble simulation functions for Python callables and external executables.

- `src/ensemblesweep/cli.py`
  - Click CLI entry points: `ensemblesweep py ...` and `ensemblesweep exe ...`.

- `README.md`
  - User-facing examples and API description.

- `.agents/skills/`
  - Agent skills for using the project as a tool. Keep these in sync when user-facing CLI/API behavior changes.

## Current API design decisions

### libEnsemble remains the execution engine

Do not replace libEnsemble with raw `concurrent.futures` for point-level execution. The desired architecture is:

```text
User API -> Sweep/SweepExecutor -> libEnsemble -> objective function/executable
```

libEnsemble is responsible for evaluating individual parameter points concurrently.

### `SweepExecutor` returns one future per libEnsemble run

A libEnsemble run is blocking at the batch level. The executor API intentionally returns one `Future` for a whole sweep or partial batch, not one future per parameter point.

Example:

```python
with SweepExecutor(nworkers=4) as executor:
    future = executor.submit_sweep(objective_function=f, input_data=data)
    results = future.result()  # SweepResults for this submitted batch
```

This means `as_completed(...)` is only useful across multiple submitted sweep/batch futures, not for individual points within one batch.

### Do not add multiple parallel libEnsemble instances by default

`SweepExecutor` currently uses an internal `ThreadPoolExecutor(max_workers=1)`. This is intentional. It avoids running multiple libEnsemble managers at the same time.

If changing this, discuss the implications first: output directory conflicts, resource oversubscription, MPI/local comms behavior, and unclear semantics around `nworkers`.

### Use `nworkers`, not `max_workers`, in public sweep APIs

`nworkers` maps to libEnsemble workers. Avoid `max_workers` in public `SweepExecutor`/`Sweep` APIs because it is ambiguous with Python's executor worker count.

### Results are canonicalized through `SweepResult` and `SweepResults`

Use:

```python
sweep.results        # SweepResults over all completed rows
future.result()      # SweepResults over only the submitted batch
```

A `SweepResult` has:

- `index`
- `params`
- `outputs`
- `eval_time`
- `status`

`SweepResults.to_numpy()` returns the raw completed libEnsemble rows for that view. `SweepResults.to_pandas()` returns a flattened DataFrame with `index`, params, outputs, `eval_time`, and `status`.

Do not assume the string/repr form is the stable serialization format. Prefer `to_pandas()`, `to_numpy()`, or explicit iteration.

## Execution model notes

`Sweep.run(n=None)`:

1. Determines how many total points remain.
2. Caps by `n` if supplied.
3. Sets libEnsemble `ExitCriteria(sim_max=target_sim_max)`.
4. Runs libEnsemble with local comms.
5. On the manager, stores `ensemble.H` back into `self._H_total` and updates `self.evaluated`.

Default worker count is:

```python
max(1, os.cpu_count() - 1)
```

unless `nworkers` is provided.

## Common pitfalls

### Do not validate Python objective functions with `python -c`

libEnsemble worker processes may need to import the objective function. A function defined in `python -c` or other non-importable `__main__` contexts can fail with errors like:

```text
AttributeError: module '__main__' has no attribute 'f'
```

Use a real script with an importable top-level function and an `if __name__ == "__main__":` guard.

Good validation pattern:

```python
from ensemblesweep import Data, SweepExecutor


def f(x, y):
    return x * y


if __name__ == "__main__":
    data = Data(x=[1, 2], y=[10, 20])
    with SweepExecutor(nworkers=2) as executor:
        future = executor.submit_sweep(objective_function=f, input_data=data)
        results = future.result()
    print(len(results))
    print(results[0])
```

### libEnsemble creates workflow/output directories

Validation runs may create directories such as `sweep_<timestamp>/` and libEnsemble log/stat files. Clean up generated artifacts after tests when appropriate. Do not delete user-created data.

### Batch-only executor results depend on completed-row ordering

`SweepExecutor` currently captures `previously_evaluated` before `sweep.run(n)` and returns:

```python
SweepResults(sweep, start_index=previously_evaluated)
```

This assumes the completed rows view is ordered compatibly with evaluation progress. If future changes allow cancellation, retries, out-of-order histories, or more complex libEnsemble allocation, consider selecting batch rows by explicit `sim_id`/row identity rather than by completed-row slice.

### Objective output fields

For Python objective functions:

- If `objective_output` is omitted, output field is `"output"`.
- If `objective_output` is a string, it is normalized to a single-item list.
- Output dtype is currently float for each output field.

For executables:

- The executable receives `Data` parameters as positional command-line arguments in key order.
- Output is read from `objective_output` if supplied, otherwise from the executable stdout path used by `sim_funcs.py`.

### `Data` dtype inference is simple

`Data` infers dtype from the first value for each parameter. Strings use `U100`; unknown types fall back to `object`. Be careful when changing dtype behavior because libEnsemble structured arrays depend on these dtypes.

### Keep CLI and README in sync with API changes

If changing constructor arguments, result shapes, worker options, or supported execution modes, update:

- `README.md`
- `src/ensemblesweep/cli.py`
- `.agents/skills/*/SKILL.md` when relevant
- `src/ensemblesweep/__init__.py` exports when adding/removing public classes

## Development and validation commands

This project uses Pixi. Useful commands:

```bash
pixi run python -m compileall src/ensemblesweep
```

For linting, use the dev environment if needed:

```bash
pixi run -e dev ruff check src
```

There may not be a full automated test suite yet. Prefer targeted real-script validations for libEnsemble behavior, especially for multiprocessing/importability-sensitive paths.

## Style and change guidance

- Make small, focused changes.
- Preserve libEnsemble as the core engine.
- Avoid broad rewrites of result semantics without updating all user-facing examples.
- Prefer existing dependencies and patterns.
- Do not run or leave long-lived servers/watchers.
- Do not commit changes unless explicitly asked.
