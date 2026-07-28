import importlib
import logging
import os
import sys

import click
import numpy as np

from .data import Data
from .sweep import Sweep
from .utils import parse_var_string

sys.path.append(os.getcwd())


@click.group()
def cli():
    """EnsembleSweep CLI: Parameter sweeps made easy with libEnsemble."""
    pass


def common_options(f):
    options = [
        click.option(
            "--var",
            "-v",
            multiple=True,
            help="Variables in format key=val,val or key=start:stop:num",
        ),
        click.option("--workers", "-w", type=int, help="Number of workers"),
        click.option("--save-csv", type=click.Path(), help="Save results to CSV"),
        click.option("--save-json", type=click.Path(), help="Save results to JSON"),
        click.option("--save-numpy", type=click.Path(), help="Save results to .npy file"),
        click.option("--save-pandas", type=click.Path(), help="Save results to Parquet file"),
        click.option("--quiet", "-q", is_flag=True, help="Suppress libEnsemble logs"),
        click.option("--dry-run", is_flag=True, help="Show sample of combinations and exit"),
    ]
    for option in reversed(options):
        f = option(f)
    return f


def handle_sweep(
    data,
    sweep,
    save_csv,
    save_json,
    save_numpy,
    save_pandas,
    quiet,
    dry_run,
    **kwargs,
):
    if dry_run:
        click.echo(f"Dry run: Total evaluations = {data.total}")
        click.echo("First 10 combinations:")
        for i, combo in enumerate(data.combinations[:10]):
            click.echo(f"  {i}: {dict(zip(data._keys, combo))}")
        return

    if quiet:
        # Silence libensemble and other loggers
        for logger_name in logging.root.manager.loggerDict:
            if "libensemble" in logger_name or "ensemblesweep" in logger_name:
                logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        logging.getLogger("libensemble").setLevel(logging.CRITICAL)

    sweep.run()

    results = sweep.results
    df = results.to_pandas()

    if save_csv:
        df.to_csv(save_csv, index=False)
        click.echo(f"Results saved to {save_csv}")
    if save_json:
        df.to_json(save_json, orient="records", indent=4)
        click.echo(f"Results saved to {save_json}")
    if save_numpy:
        np.save(save_numpy, sweep.results.to_numpy())
        click.echo(f"Results saved to {save_numpy}")
    if save_pandas:
        df.to_parquet(save_pandas)
        click.echo(f"Results saved to {save_pandas}")

    if not quiet and not (save_csv or save_json or save_numpy or save_pandas):
        click.echo("Sweep completed. Results:")
        click.echo(df)


@cli.command()
@click.option("--func", "-f", required=True, help="Path to function (module.func)")
@common_options
def py(func, var, **kwargs):
    """Sweep over a Python function."""
    # Parse variables
    input_vars = {}
    for v_str in var:
        k, v = parse_var_string(v_str)
        input_vars[k] = v

    # Import function
    try:
        module_path, func_name = func.rsplit(".", 1)
        module = importlib.import_module(module_path)
        objective_function = getattr(module, func_name)
    except Exception as e:
        click.echo(f"Error importing function {func}: {e}", err=True)
        sys.exit(1)

    data = Data(**input_vars)
    sweep = Sweep(
        objective_function=objective_function,
        input_data=data,
        nworkers=kwargs.get("workers"),
    )

    handle_sweep(data, sweep, **kwargs)


@cli.command()
@click.option("--app", "-a", required=True, help="Path to executable binary")
@click.option("--out-file", "-o", help="File where executable writes results")
@common_options
def exe(app, out_file, var, **kwargs):
    """Sweep over an external executable."""
    # Parse variables
    input_vars = {}
    for v_str in var:
        k, v = parse_var_string(v_str)
        input_vars[k] = v

    data = Data(**input_vars)
    sweep = Sweep(
        objective_executable=app,
        objective_output=out_file,
        input_data=data,
        nworkers=kwargs.get("workers"),
    )

    handle_sweep(data, sweep, **kwargs)


if __name__ == "__main__":
    cli()
