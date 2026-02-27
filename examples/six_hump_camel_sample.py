import numpy as np
from ensemblesweep import Sweep, Data

def six_hump_camel_func(x0, x1):
    """
    Definition of the six-hump camel
    """
    term1 = (4 - 2.1 * x0**2 + (x0**4) / 3) * x0**2
    term2 = x0 * x1
    term3 = (-4 + 4 * x1**2) * x1**2

    f = term1 + term2 + term3
    return f, term1, term2, term3


if __name__ == "__main__":
    
    data = Data(
        x0 = np.linspace(-3, 3, 10),
        x1 = np.linspace(-2, 2, 10)
    )

    sweep = Sweep(
        objective_function=six_hump_camel_func,
        objective_output=["f", "t1", "t2", "t3"],
        input_data=data,
    )

    sweep.run()
    print(sweep.results)