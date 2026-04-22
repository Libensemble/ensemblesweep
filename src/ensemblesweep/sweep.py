import math
import os
import time
import numpy as np

from libensemble import Ensemble
from libensemble import logger
from libensemble.comms.logs import LogConfig
from libensemble.specs import SimSpecs, AllocSpecs, ExitCriteria
from libensemble.alloc_funcs.give_pregenerated_work import give_pregenerated_sim_work as alloc_f

from .sim_funcs import generic_function_simf, generic_executable_simf

logs = LogConfig.config
logs.stat_filename = "stats.txt"

class ResultWrapper:
    def __init__(self, sweep):
        self.sweep = sweep
        
    def __len__(self):
        return int(np.sum(self.sweep._H_total["sim_ended"]))

    def __getitem__(self, i):
        results = self.sweep._H_total[self.sweep._H_total["sim_ended"]]
        if len(results) == 0:
            return []
        
        sliced = results[i]
        
        # format out fields, exclude internal libEnsemble properties
        ignore_fields = ["sim_id", "sim_started", "sim_started_time", "sim_ended", "sim_ended_time", 
                         "sim_worker", "sim_time", "given", "given_time", "cancel_requested", "kill_sent",
                         "gen_informed", "gen_informed_time", "gen_started_time", "gen_ended_time", "gen_worker"]
                         
        if isinstance(sliced, np.void):
            out = {}
            for name in sliced.dtype.names:
                if name not in ignore_fields:
                    out[name] = sliced[name]
            return out
        else:
            out_list = []
            for item in sliced:
                out = {}
                for name in item.dtype.names:
                    if name not in ignore_fields:
                        out[name] = item[name]
                out_list.append(out)
            return out_list

    def to_numpy(self):
        return self.sweep._H_total[self.sweep._H_total["sim_ended"]]

    def to_pandas(self):
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required for to_pandas(). Install it with 'pip install pandas'.")
        return pd.DataFrame(self[:])
        
    def __str__(self):
        # We can format it nicely
        results = self.sweep._H_total[self.sweep._H_total["sim_ended"]]
        if len(results) == 0:
            return "[]"
        return str(self[:])
        
    def __repr__(self):
        return repr(self[:])

class Sweep:
    def __init__(self, objective_function=None, input_data=None, objective_executable=None, objective_output=None):
        self.objective_function = objective_function
        self.objective_executable = objective_executable
        self.objective_output = objective_output
        self.input_data = input_data
        
        if self.objective_function and self.objective_executable:
            raise ValueError("Provide either objective_function or objective_executable, not both.")
            
        self._H_total = input_data.to_h0()
        self.evaluated = 0
        self.results = ResultWrapper(self)
        
    def run(self, n=None):
        total_points = len(self._H_total)
        if self.evaluated >= total_points:
            print("All points already evaluated.")
            return

        to_evaluate = total_points - self.evaluated
        if n is not None:
            to_evaluate = min(n, to_evaluate)
            
        target_sim_max = self.evaluated + to_evaluate

        cores = max(1, os.cpu_count() - 1)
        libE_specs = {
            "comms": "local", 
            "nworkers": cores,
            "sim_dirs_make": True,
            "ensemble_dir_path": f"sweep_{int(time.time())}",
            "reuse_output_dir": True,
            "use_workflow_dir": True,
            "save_H_and_persis_on_abort": False,
        }
        ensemble = Ensemble(parse_args=False, libE_specs=libE_specs)
        ensemble.H0 = self._H_total
        
        if self.objective_function:
            out_fields = self.objective_output if self.objective_output else "output"
            if isinstance(out_fields, str):
                out_fields = [out_fields]
            
            out_spec = [(f, float) for f in out_fields] + [("eval_time", float)]
            
            sim_specs = SimSpecs(
                sim_f=generic_function_simf,
                inputs=self.input_data._keys,
                out=out_spec,
                user={
                    "objective_function": self.objective_function,
                    "input_keys": self.input_data._keys
                }
            )
        else:
            out_spec = [("output", float), ("eval_time", float)] 
            sim_specs = SimSpecs(
                sim_f=generic_executable_simf,
                inputs=self.input_data._keys,
                out=out_spec,
                user={
                    "objective_executable": self.objective_executable,
                    "objective_output": self.objective_output,
                    "input_keys": self.input_data._keys
                }
            )

        ensemble.sim_specs = sim_specs
        ensemble.alloc_specs = AllocSpecs(alloc_f=alloc_f)
        ensemble.exit_criteria = ExitCriteria(sim_max=target_sim_max)
        
        if self.objective_executable:
            from libensemble.executors.mpi_executor import MPIExecutor
            exctr = MPIExecutor()
            # Register using absolute path effectively
            exctr.register_app(full_path=self.objective_executable, app_name="executable")

        ensemble.run()
        
        if ensemble.is_manager:
            self._H_total = ensemble.H
            self.evaluated = np.sum(self._H_total["sim_ended"])
            
    def estimated_time(self, n=None):
        if self.evaluated == 0:
            print("Cannot estimate time without running at least one evaluation.")
            return -1.0
            
        results = self._H_total[self._H_total["sim_ended"]]
        if "eval_time" not in results.dtype.names:
            return -1.0
            
        avg_time = np.mean(results["eval_time"])
        
        if n is None:
            n = len(self._H_total) - self.evaluated
            
        cores = max(1, os.cpu_count() - 1)
        
        batches = math.ceil(n / cores)
        return batches * avg_time