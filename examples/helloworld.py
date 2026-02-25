from ensemblesweep import Sweep, Data
import random
import numpy as np
import os

# Just prototyping an interface for now

# Define the function to be evaluated
def my_function(*args):
    return args[0] * args[1] * args[2]


# by default the "objective" value we'll call "output". So a single function return is called "output".
# if we get multiple unlabled returns, those will be "output_0", "output_1", etc.
# if we get a dictionary return, the output labels will simply be the keys of the dictionary

lb = (-2 - np.pi / 10) * np.ones(3),
ub = 2 * np.ones(3),

# Create an input data object
# should accept arbitrary-ish input data types, as long as they're list/array-like
data = Data(
    core=random.sample(["rocm", "cuda", "cpu"]*6, 6),
    edge=random.sample(range(10), 4),
    x = np.random.uniform(lb, ub, (3, 3))
)

# total is the total number of points to evaluate. for the above it'll be 6*4*3 = 72
total = data.total

# Create a sweep object
sweep = Sweep(
    objective_function=my_function,
    input_data=data,
)

# do a single sample, run against the function/simulation. *This will update both the object with a single result, **and** an estimated time*
sweep.run(1)
print(sweep.results[0])

# estimated time is in seconds, for the entire sweep
if sweep.estimated_time() > 10:
    print("Estimated time is too long, only doing a little bit")
    sweep.run(10) # run 10 concurrently. Max concurrency is number of cores
else:
    print("Estimated time is acceptable, continuing")
    sweep.run() # run all concurrently. Max concurrency is number of cores.

sweep.estimated_time(4) # estimate time for 4 points. Parallelism matters, so if this value <= number of cores, assume same amount of time as 1 point.
# if cores == 10 and sweep.estimated_time(20), assume same amount of time as 2 points.

# Print the results, jsonlines
print(sweep.results)

# print the results, numpy
print(sweep.results.to_numpy())

###################

# an objective can also be an *executable*
objective_path = os.path.join(os.path.dirname(__file__), "forces.x")

data = Data(
    num_particles=random.sample(range(100, 1000, 10), 10),
    num_steps = [10, 100, 1000],
    rand_seed = 100,
    kill_rate = [0.01, 0.1, 0.5]
)

# each of the samples will be given to the executable as arguments, in the exact order. Parallel runs.

sweep = Sweep(
    objective_executable=objective_path,
    objective_output="forces.stat", # the output file name, otherwise pipe exe's stdout to file and assume the last line is the output
    input_data=data,
)

sweep.run()
print(sweep.results)

    
