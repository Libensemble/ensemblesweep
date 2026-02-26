import numpy as np
import itertools

class Data:
    def __init__(self, **kwargs):
        """
        Initializes the Data class.
        Takes arbitrary keyword arguments and computes the Cartesian product
        of all parameters that are list-like or array-like.
        """
        self._keys = []
        self._values = []
        self._shapes = {}
        
        parsed_args = {}
        for k, v in kwargs.items():
            self._keys.append(k)
            # Handle numpy arrays, lists, tuples
            if isinstance(v, (list, tuple)) or (isinstance(v, np.ndarray) and v.ndim > 0):
                parsed_args[k] = list(v)
            else:
                # Wrap scalars in a list so itertools.product works
                parsed_args[k] = [v]
        
        # Compute cartesian product
        product = list(itertools.product(*[parsed_args[k] for k in self._keys]))
        
        self.total = len(product)
        self.combinations = product
        
        # Prepare the libEnsemble dtype specification for inputs
        self.dtype_spec = []
        for k in self._keys:
            sample_val = parsed_args[k][0]
            if isinstance(sample_val, np.ndarray):
                self.dtype_spec.append((k, sample_val.dtype, sample_val.shape))
            elif isinstance(sample_val, int):
                self.dtype_spec.append((k, int))
            elif isinstance(sample_val, float):
                self.dtype_spec.append((k, float))
            elif isinstance(sample_val, str):
                self.dtype_spec.append((k, "U100")) # fallback string
            else:
                self.dtype_spec.append((k, object)) # Fallback
                
    def to_h0(self):
        """
        Converts the computed parameter space to a libEnsemble H0 array.
        """
        # Add basic libEnsemble fields
        full_dtype = self.dtype_spec + [("sim_id", int), ("sim_started", bool)]
        H0 = np.zeros(self.total, dtype=full_dtype)
        
        for i, combo in enumerate(self.combinations):
            for j, key in enumerate(self._keys):
                H0[key][i] = combo[j]
            H0["sim_id"][i] = i
            H0["sim_started"][i] = False
            
        return H0
