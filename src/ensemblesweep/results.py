from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np


@dataclass(frozen=True)
class SweepResult:
    index: int
    params: dict[str, Any]
    outputs: dict[str, Any]
    eval_time: float | None = None
    status: str = "completed"


class SweepResults:
    """Collection view over completed sweep results.

    Can represent all completed results on a sweep (``sweep.results``)
    or a subset corresponding to a single submitted batch
    (``future.result()``).
    """

    def __init__(self, sweep, start_index: int = 0, stop_index: int | None = None):
        self.sweep = sweep
        self.start_index = start_index
        self.stop_index = stop_index

    @property
    def _completed(self) -> np.ndarray:
        completed = self.sweep._H_total[self.sweep._H_total["sim_ended"]]
        start = self.start_index
        stop = self.stop_index if self.stop_index is not None else len(completed)
        return completed[start:stop]

    def __len__(self) -> int:
        return len(self._completed)

    def __getitem__(self, index):
        completed = self._completed
        if isinstance(index, slice):
            return [_row_to_result(row, self.sweep) for row in completed[index]]
        return _row_to_result(completed[index], self.sweep)

    def __iter__(self) -> Iterator[SweepResult]:
        for row in self._completed:
            yield _row_to_result(row, self.sweep)

    def to_numpy(self) -> np.ndarray:
        return self._completed

    def to_pandas(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required for to_pandas(). Install it with 'pip install pandas'.")

        return pd.DataFrame([self._result_to_row_dict(r) for r in self])

    def __str__(self) -> str:
        results = self._completed
        if len(results) == 0:
            return "[]"
        return str([self._result_to_row_dict(r) for r in self])

    def __repr__(self) -> str:
        return f"SweepResults({[self._result_to_row_dict(r) for r in self]!r})"

    @staticmethod
    def _result_to_row_dict(result: SweepResult) -> dict[str, Any]:
        row = {"index": result.index}
        row.update(result.params)
        row.update(result.outputs)
        row["eval_time"] = result.eval_time
        row["status"] = result.status
        return row


SweepBatchResult = SweepResults


def _row_to_result(row: np.void, sweep) -> SweepResult:
    input_keys = sweep.input_data._keys
    internal_fields = set(_internal_fields())
    result_fields = [name for name in row.dtype.names if name not in input_keys and name not in internal_fields]

    index = int(row["sim_id"]) if "sim_id" in row.dtype.names else 0
    eval_time = _to_python_value(row["eval_time"]) if "eval_time" in row.dtype.names else None
    status = "completed" if bool(row["sim_ended"]) else "pending"

    return SweepResult(
        index=index,
        params={key: _to_python_value(row[key]) for key in input_keys},
        outputs={key: _to_python_value(row[key]) for key in result_fields if key != "eval_time"},
        eval_time=eval_time,
        status=status,
    )


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
