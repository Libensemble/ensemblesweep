from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor

from .results import SweepResults
from .sweep import Sweep


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


def _run_sweep(sweep: Sweep, n=None) -> SweepResults:
    previously_evaluated = int(sweep.evaluated)
    sweep.run(n)
    return SweepResults(sweep, start_index=previously_evaluated)
