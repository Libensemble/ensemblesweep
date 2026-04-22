import numpy as np


def infer_type(val_str):
    """Infers type from string in order of int, float, str."""
    try:
        if "." in val_str or "e" in val_str.lower():
            return float(val_str)
        return int(val_str)
    except ValueError:
        try:
            return float(val_str)
        except ValueError:
            return val_str


def parse_var_string(var_str):
    """
    Parses a string of format key=value.
    Supports lists (a,b,c) and ranges (start:stop:num).
    """
    if "=" not in var_str:
        raise ValueError(f"Invalid variable format: {var_str}. Expected key=value.")

    key, value_str = var_str.split("=", 1)

    # Handle ranges (start:stop:num)
    if ":" in value_str:
        parts = value_str.split(":")
        if len(parts) == 3:
            start = float(parts[0])
            stop = float(parts[1])
            num = int(parts[2])
            return key, np.linspace(start, stop, num).tolist()
        else:
            raise ValueError(
                f"Invalid range format for {key}: {value_str}. Expected start:stop:num."
            )

    # Handle lists (comma separated)
    if "," in value_str:
        items = value_str.split(",")
        return key, [infer_type(i.strip()) for i in items]

    # Handle scalar
    return key, infer_type(value_str.strip())


def get_dtype(key, val):
    """Determines the libEnsemble dtype for a specific value."""
    if isinstance(val, np.ndarray):
        return (key, val.dtype, val.shape)
    elif isinstance(val, (int, np.integer)):
        return (key, int)
    elif isinstance(val, (float, np.floating)):
        return (key, float)
    elif isinstance(val, str):
        # Dynamic string length with some padding
        return (key, "U" + str(len(val) + int(len(val) / 10) + 1))
    else:
        return (key, object)
