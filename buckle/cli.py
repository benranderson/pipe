# -*- coding: utf-8 -*-

"""Console script for buckle."""

import sys
import click
import toml
import os
from types import SimpleNamespace

import pandas as pd
from bokeh.io import output_file
from bokeh.plotting import show

from buckle.buckle import run_analysis
from buckle.plot import generate_plots

TEMP_PROF_FILE = os.path.join("data", "temp_profile.csv")
INPUTS_FILE = os.path.join("data", "inputs.toml")
RESULTS_FILE = os.path.join("reports", "results.csv")
PLOTS_FILE = os.path.join("reports", "plots.html")


def parse_input_file():

    PARAMS = [
        "D_p",
        "t_p",
        "E_p",
        "rho_p",
        "alpha",
        "v",
        "rho_c",
        "t_c",
        "rho_conc",
        "t_conc",
        "E_conc",
        "Coff",
        "h",
        "rho_w",
        "T_a",
        "t_m",
        "rho_m",
        "rho_con",
        "P_i",
        "N_lay",
        "mu_a",
        "mu_l",
        "step",
    ]

    input_dict = toml.load(INPUTS_FILE)

    missing_params = set(PARAMS) - set(input_dict.keys())
    if len(missing_params) > 0:
        print(f"Input file is missing parameters: {', '.join(missing_params)}")
        exit()

    return SimpleNamespace(**input_dict)


@click.command()
def main(args=None):
    """Console script for buckle."""

    click.secho("Parsing inputs...", fg="yellow")
    i = parse_input_file()
    temp_profile = pd.read_csv(TEMP_PROF_FILE)

    click.secho("Running analysis...", fg="yellow")
    results = run_analysis(i, temp_profile)
    F_eff_max = results["F_eff"].min()
    click.echo("Maximum fully restrained effective axial force [N]:")
    click.secho(f"{F_eff_max}", fg="green")

    F_res_max = results["F_res"].min()
    click.echo("Maximum resultant effective axial force [N]:")
    click.secho(f"{F_res_max}", fg="green")

    F_b = results["F_b"].min()
    click.echo("Minimum buckle initiation force [N]:")
    click.secho(f"{F_b}", fg="green")

    click.echo("Susceptible to lateral buckling:")
    if F_res_max < F_b:
        click.secho("Yes", fg="red")
    else:
        click.secho("No", fg="green")

    results.to_csv(RESULTS_FILE, index=False)

    click.secho("Generating plots...", fg="yellow")
    plots = generate_plots(results)
    output_file(PLOTS_FILE, title="Buckle Plots")
    show(plots)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
