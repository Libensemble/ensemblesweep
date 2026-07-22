---
name: programmatic-sweep-api
description: Perform a parameter sweep programmatically using the ensemblesweep Python API.
---

# Programmatic Sweep API

Use this skill when the CLI is insufficient (e.g., when integrating into a larger Python pipeline that requires dynamic adjustment of inputs). This uses the `Sweep` and `Data` classes directly.

## Usage

### 1. Define Your Function

```python
import numpy as np

def my_function(param1, param2):
    # Perform calculation
    result = param1**2 + param2
    return result
```

### 2. Configure Your Data

Define the parameter space using the `Data` class.

```python
from ensemblesweep import Data

data = Data(
    param1=np.linspace(-10, 10, 21),
    param2=[1.0, 5.0, 10.0]
)
```

### 3. Initialize and Run the Sweep

```python
from ensemblesweep import Sweep

sweep = Sweep(
    objective_function=my_function,
    input_data=data,
    num_workers=4
)

# Optional: Perform a dry run by checking the total evaluations first
print(f"Total Evaluations: {data.total}")

# Run the sweep
sweep.run()
```

### 4. Retrieve Results

```python
# Access results as a NumPy structured array
results = sweep.results.to_numpy()

# Or convert to a Pandas DataFrame
import pandas as pd
df = pd.DataFrame(results)
print(df.head())
```

## Tips for Agents

- **Incremental Runs**: You can call `sweep.run(n)` to evaluate only `n` points. Subsequent calls will continue from the last point.
- **Estimated Time**: Use `sweep.estimated_time()` after a few runs to get an estimate (in seconds) for the remaining work.
- **Dtype Mapping**: `ensemblesweep` automatically maps Python types to libEnsemble dtypes. If you return multiple values from your function, they will be stored in separate columns in the results.
- **Persistence**: Results are stored in the `Sweep` object's internal state. You can save them using standard Python/Pandas file operations.
