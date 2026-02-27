import time
import numpy as np
import os
from libensemble.message_numbers import WORKER_DONE, TASK_FAILED

def generic_function_simf(H, persis_info, sim_specs, *args):
    """
    sim_f for executing generic Python functions.
    """
    start_time = time.time()
    
    # Get user function and expected parameters
    func = sim_specs["user"]["objective_function"]
    input_keys = sim_specs["user"]["input_keys"]
    
    # Extract arguments from H, passing only the first row's data
    args = [H[k][0] for k in input_keys]
    
    calc_status = WORKER_DONE
    result = np.nan
    try:
        # Evaluate function
        result = func(*args)
    except Exception as e:
        print(f"Error evaluating objective_function: {e}")
        calc_status = TASK_FAILED
        
    eval_time = time.time() - start_time
    
    # Format output based on the result type
    output = np.zeros(1, dtype=sim_specs["out"])
    out_fields = [n for n in output.dtype.names if n != 'eval_time']
    
    if isinstance(result, dict):
        matched = False
        for k, v in result.items():
            if k in output.dtype.names:
                output[k] = v
                matched = True
        if not matched:
            print(f"Warning: Objective function returned dictionary with keys {list(result.keys())}, but none match the expected output fields {out_fields}.")
    elif isinstance(result, (list, tuple)):
        # If it's a single-element list/tuple, treat it as a scalar or map to first field
        if len(result) == 1:
            if out_fields:
                output[out_fields[0]] = result[0]
        else:
            # Map elements to output fields in order
            for i, v in enumerate(result):
                if i < len(out_fields):
                    output[out_fields[i]] = v
    else:
        # Scalar result
        if out_fields:
            output[out_fields[0]] = result
            
    output["eval_time"] = eval_time
    return output, persis_info, calc_status

def generic_executable_simf(H, persis_info, sim_specs, libE_info):
    """
    sim_f for executing binaries using MPIExecutor.
    """
    start_time = time.time()
    calc_status = WORKER_DONE
    
    output_file = sim_specs["user"]["objective_output"]
    input_keys = sim_specs["user"]["input_keys"]
    
    # Build arguments string
    args_list = [str(H[k][0]) for k in input_keys]
    args = " ".join(args_list)
    
    exctr = libE_info["executor"]
    
    # Execute without redirecting stdout unless we don't have an output file
    if output_file:
        task = exctr.submit(app_name="executable", app_args=args)
    else:
        output_file = "sim.out" # pipe exe's stdout to file and assume the last line is the output
        task = exctr.submit(app_name="executable", app_args=args, stdout=output_file)
        
    task.wait()
    
    final_data = np.nan
    if task.state == "FINISHED":
        filepath = os.path.join(task.workdir, output_file)
        try:
            # We assume output can be processed by np.loadtxt
            data = np.loadtxt(filepath)
            final_data = data[-1] if data.ndim > 0 else data.item()
        except Exception as e:
            print(f"Error reading output file {filepath}: {e}")
            calc_status = TASK_FAILED
    else:
        calc_status = TASK_FAILED
        
    eval_time = time.time() - start_time
    
    output = np.zeros(1, dtype=sim_specs["out"])
    if "output" in output.dtype.names:
        output["output"] = final_data
    output["eval_time"] = eval_time
    
    return output, persis_info, calc_status
