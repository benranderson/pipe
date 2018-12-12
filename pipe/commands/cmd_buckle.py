import os
import click
import toml
from types import SimpleNamespace

import pandas as pd
from bokeh.io import output_file
from bokeh.plotting import show
from tabulate import tabulate

from pipe import logger
from pipe.config import DEFAULT_INPUTDATA_FOLDER, DEFAULT_REPORTS_FOLDER
from pipe.calculate.calc_buckle import run_analysis
from pipe.plot import generate_plots


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
        "thick",
    ]

    INPUT_DATA_FILE = os.path.join(DEFAULT_INPUTDATA_FOLDER, "inputs.toml")

    input_dict = toml.load(INPUT_DATA_FILE)

    missing_params = set(PARAMS) - set(input_dict.keys())
    if len(missing_params) > 0:
        print(f"Input file is missing parameters: {', '.join(missing_params)}")
        exit()

    return SimpleNamespace(**input_dict)


def buckle(plot):

    i = parse_input_file()
    TEMP_PROF_FILE = os.path.join(DEFAULT_INPUTDATA_FOLDER, "temp_profile.csv")
    temp_profile = pd.read_csv(TEMP_PROF_FILE)

    logger.info("Running analysis...")
    results = run_analysis(i, temp_profile)

    F_res_max = results["F_res"].min()
    F_b = results["F_b"].min()

    headers = ["Parameter", "Units", "Value"]
    table = [
        ["Max. resultant effective axial force", "N", F_res_max],
        ["Min. buckle initiation forcee", "N", F_b],
    ]
    logger.info(tabulate(table, headers=headers, tablefmt="psql"))

    logger.info("Susceptible to lateral buckling?:")
    if F_res_max < F_b:
        logger.warning("Yes")
    else:
        logger.info("No")

    # create reports folder if it doesn't exist
    if not os.path.exists("reports"):
        os.makedirs("reports")

    RESULTS_FILE = os.path.join(DEFAULT_REPORTS_FOLDER, "results.csv")
    results.to_csv(RESULTS_FILE, index=False)

    if plot:
        logger.info("Plotting...")
        plots = generate_plots(results)
        PLOTS_FILE = os.path.join(DEFAULT_REPORTS_FOLDER, "plots.html")
        output_file(PLOTS_FILE, title="Buckle Plots")
        show(plots)

