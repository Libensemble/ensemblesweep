# ensemblesweep

``ensemblesweep`` is a small library based on [libEnsemble](https://libensemble.readthedocs.io/en/latest/) 
for parallel parameter sweeps of objective functions or executables.

Installation
============

In the project directory:

```bash
pip install .
```

Usage
=====

Simple usage
------------

1. Specify any number of iterable inputs to a ``Data`` object.

2. Specify an objective function to the ``Sweep`` object. Provide the input data.

3. Run the sweep. All instances are run in parallel, up to the number of available cores.

```python

import numpy as np
from ensemblesweep import Sweep, Data

# Define the function to be evaluated
def my_function(core, edge, x):
    return float(edge) * np.sum(x) + core

data = Data(
    core=random.sample(["rocm", "cuda", "cpu"]*6, 6),
    edge=random.sample(range(10), 4),
    x = np.random.uniform(lb, ub, (3, 3))
)

# Create a sweep object
sweep = Sweep(
    objective_function=my_function,
    input_data=data,
)

if __name__ == "__main__":

    sweep.run()
    print(sweep.results)
```

Executables
-----------


- Specify an *executable* to the ``Sweep`` object.
    - The ``Data`` parameters will be passed as arguments to the executable in the order they are defined.
    - The output of the executable will be read:
        - from the file specified by ``objective_output`` (if provided).
        - or, if ``objective_output`` is not specified, the last line of the executable's stdout.

```python

import random
from ensemblesweep import Sweep, Data

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
    objective_output="forces.stat",
    input_data=data,
)

sweep.run()
```

CLI Interface
-------------

Sweep a Python function:

```bash
ensemblesweep py --func mod.func --var "x=0:1:10" --var "y=1,2" --workers 4
```

Sweep an executable:

```bash
ensemblesweep exe --app ./sim.x --var "m=1,2,3" --out-file out.stat
```

Additional Features
-------------------

- Run a subset of the total points. This also updates the estimated time (in seconds) to run the entire sweep.

```python

if __name__ == "__main__":

    sweep.run(10)

    # estimated time is in seconds, for the entire sweep
    if sweep.estimated_time() > 10:
        print("Estimated time is too long, only doing a little bit")
        sweep.run(10) # run 10 concurrently. Max concurrency is number of cores
    else:
        print("Estimated time is acceptable, continuing")
        sweep.run()
```

- Estimate the runtime for a subset of the total points. Parallelism is considered.

```python

sweep.estimated_time(4)
```

- Get results as NumPy

```python

# print the results, numpy
print(sweep.results.to_numpy())
```

- Get results as Pandas

```python
print(sweep.results.to_pandas())
```
