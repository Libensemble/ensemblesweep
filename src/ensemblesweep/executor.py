from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np

from .sweep import Sweep


@dataclass(frozen=True)
class SweepResult:
    index: int
    params: dict[str, Any]
    outputs: dict[str, Any]
    eval_time: float | None = None
    status: str = "completed"


@dataclass(frozen=True)
class SweepBatchResult:
    results: list[SweepResult]
    sweep: Sweep

    def __iter__(self) -> Iterator[SweepResult]:
        return iter(self.results)

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, index):
        return self.results[index]

    def to_numpy(self):
        return self.sweep.results.to_numpy()

    def to_pandas(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required for to_pandas(). Install it with 'pip install pandas'.")

        return pd.DataFrame(
            [
                {
                    "index": result.index,
                    **result.params,
                    **result.outputs,
                    "eval_time": result.eval_time,
                    "status": result.status,
                }
                for result in self.results
            ]
        )


class SweepExecutor:
    def __init__(self, nworkers=None):
        self.nworkers = nworkers
        self._executor = ThreadPoolExecutor(max_workers=1)

    def submit(self, sweep: Sweep, n=None) -> Future:
        if self.nworkers is not None:
            sweep.nworkers = self.nworkers
        return self._executor.submit(_run_sweep, sweep, n)

    def submit_sweep(
        self,
        *,
        objective_function=None,
        input_data=None,
        objective_executable=None,
        objective_output=None,
        n=None,
    ) -> Future:
        sweep = Sweep(
            objective_function=objective_function,
            input_data=input_data,
            objective_executable=objective_executable,
            objective_output=objective_output,
            nworkers=self.nworkers,
        )
        return self.submit(sweep, n=n)

    def shutdown(self, wait=True, cancel_futures=False):
        self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.shutdown()


def _run_sweep(sweep: Sweep, n=None) -> SweepBatchResult:
    previously_evaluated = int(sweep.evaluated)
    sweep.run(n)
    return _batch_result_from_sweep(sweep, start_index=previously_evaluated)


def _batch_result_from_sweep(sweep: Sweep, start_index=0) -> SweepBatchResult:
    completed = sweep.results.to_numpy()
    if len(completed) == 0:
        return SweepBatchResult(results=[], sweep=sweep)

    input_keys = set(sweep.input_data._keys)
    internal_fields = set(_internal_fields())
    result_fields = []

    for name in completed.dtype.names:
        if name in input_keys or name in internal_fields:
            continue
        result_fields.append(name)

    batch_rows = completed[start_index:]
    results = []
    for row in batch_rows:
        index = int(row["sim_id"]) if "sim_id" in row.dtype.names else start_index + len(results)
        eval_time = _to_python_value(row["eval_time"]) if "eval_time" in row.dtype.names else None
        status = "completed" if bool(row["sim_ended"]) else "pending"

        results.append(
            SweepResult(
                index=index,
                params={key: _to_python_value(row[key]) for key in sweep.input_data._keys},
                outputs={key: _to_python_value(row[key]) for key in result_fields if key != "eval_time"},
                eval_time=eval_time,
                status=status,
            )
        )

    return SweepBatchResult(results=results, sweep=sweep)


def _to_python_value(value):
    if isinstance(value, np.generic):
        return value.item()
    return value


def _internal_fields():
    return [
        "sim_id",
        "sim_started",
        "sim_started_time",
        "sim_ended",
        "sim_ended_time",
        "sim_worker",
        "sim_time",
        "given",
        "given_time",
        "cancel_requested",
        "kill_sent",
        "gen_informed",
        "gen_informed_time",
        "gen_started_time",
        "gen_ended_time",
        "gen_worker",
    ]
