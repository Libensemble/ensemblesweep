from ensemblesweep import Sweep, Data
import random
import os

objective_path = os.path.join(os.path.dirname(__file__), "forces.x")

data = Data(
    num_particles=random.sample(range(100, 1000, 10), 10),
    num_steps = [10, 100, 1000],
    rand_seed = 100,
    kill_rate = [0.01, 0.1, 0.5]
)

sweep = Sweep(
    objective_executable=objective_path,
    objective_output="forces.stat",
    input_data=data,
)

if __name__ == "__main__":

    sweep.run()
    print(sweep.results)