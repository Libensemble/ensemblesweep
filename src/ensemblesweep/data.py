import numpy as np

class _InputData:
    def __init__(self, data=None):
        self._data = None
        if data is not None:
            self.data = data

    @property
    def data(self):
        """The data stored in the InputData object, always as a NumPy array."""
        return self._data

    @data.setter
    def data(self, value):
        if value is None:
            self._data = None
        elif hasattr(value, "to_numpy"):
            # Handles pandas.DataFrame/Series and polars.DataFrame/Series
            self._data = value.to_numpy()
        elif isinstance(value, np.ndarray):
            self._data = value
        else:
            # Fallback for list, tuple, etc.
            self._data = np.asarray(value)

    def load(self, filename):
        """Load data from a .npy file."""
        self.data = np.load(filename)

    def save(self, filename):
        """Save data to a .npy file."""
        if self._data is not None:
            np.save(filename, self._data)