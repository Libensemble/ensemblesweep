
def run_executable(H, persis_info, sim_specs, libE_info):

    calc_status = 0

    # # Parse out num particles, from generator function
    particles = str(int(H["x"][0][0]))

    # # app arguments: num particles, timesteps, also using num particles as seed
    args = particles + " " + str(10) + " " + particles

    # Retrieve our MPI Executor
    exctr = libE_info["executor"]

    # Submit our forces app for execution.
    task = exctr.submit(app_name="executable", app_args=args)

    # Block until the task finishes
    task.wait()

    # Try loading final energy reading, set the sim's status
    # statfile = "forces.stat"
    try:
        data = np.loadtxt(statfile)
        final_data = data[-1]
        calc_status = WORKER_DONE
    except Exception:
        final_data = np.nan
        calc_status = TASK_FAILED

    # Define our output array, populate with energy reading
    output = np.zeros(1, dtype=sim_specs["out"])
    output["output"] = final_data

    # Return final information to worker, for reporting to manager
    return output, persis_info, calc_status

from libensemble import Ensemble
from libensemble.specs import SimSpecs, GenSpecs, AllocSpecs, LibeSpecs
from libensemble.alloc_funcs.give_pregenerated_work import give_pregenerated_sim_work as alloc_f
from libensemble.executors.mpi_executor import MPIExecutor

class Sweep:
    def __init__(self, objective_function=None, input_data=None, objective_executable=None, objective_output=None):
        self.objective_function = objective_function
        self.objective_executable = objective_executable
        self.objective_output = objective_output
        self.input_data = input_data
        self.ensemble = Ensemble()
        self.sim_specs = SimSpecs()