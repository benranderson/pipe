# -*- coding: utf-8 -*-

"""Main module."""


import os
import toml
from types import SimpleNamespace
import pandas as pd
import numpy as np
from scipy import constants, interpolate, optimize

HERE = os.path.abspath(os.path.dirname(__file__))
TEMP_PROF_FILE = os.path.join(HERE, "data", "temp_profile.csv")
INPUTS_FILE = os.path.join(HERE, "data", "inputs.toml")
RESULTS_FILE = os.path.join(HERE, "reports", "results.csv")
PLOTS_FILE = os.path.join(HERE, "reports", "plots.html")

# --------- Parse Input Data -----------


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


i = parse_input_file()
temp_profile = pd.read_csv(TEMP_PROF_FILE)


# --------- General Calculations -----------

D_i = i.D_p - 2 * i.t_p
D_c = i.D_p + 2 * i.t_c
D_conc = D_c + 2 * i.t_conc
D_m = D_conc + 2 * i.t_m


def calc_area(D_o, D_i):
    return np.pi / 4 * (D_o ** 2 - D_i ** 2)


A_p = calc_area(i.D_p, D_i)
A_c = calc_area(D_c, i.D_p)
A_conc = calc_area(D_conc, D_c)
A_m = calc_area(D_m, D_conc)
A_o = calc_area(D_m, 0)
A_i = calc_area(D_i, 0)

m_con = A_i * i.rho_con
m_p = A_p * i.rho_p
m_c = A_c * i.rho_c
m_conc = A_conc * i.rho_conc
m_m = A_m * i.rho_m
m_w = A_o * i.rho_w

W_s = constants.g * (m_con + m_p + m_c + m_conc + m_m - m_w)


def calc_I(D_o, D_i):
    return np.pi / 64 * (D_o ** 4 - D_i ** 4)


I_p = calc_I(i.D_p, D_i)
I_conc = calc_I(D_conc, D_c)

EI = i.E_p * I_p + i.Coff * i.E_conc * I_conc
P_o = i.rho_w * constants.g * i.h


# --------- Force Calculations -----------

L = temp_profile["KP"].max()
f = interpolate.interp1d(temp_profile["KP"], temp_profile["T"])
results = pd.DataFrame(np.linspace(0, L, int(L / i.step)), columns=["x"])
results["T"] = f(results["x"])

results["delta_T"] = results["T"] - i.T_a
results["F_t"] = -i.E_p * A_p * i.alpha * results["delta_T"]

F_p = A_p * i.v * ((i.P_i * D_i - P_o * i.D_p) / (2 * i.t_p) - 0.5 * (i.P_i + P_o))
F_e = -np.pi / 4 * (i.P_i * D_i ** 2 - P_o * i.D_p ** 2)
results["S_eff"] = results["F_t"] + F_p + F_e + i.N_lay

P_fmax = -i.mu_a * W_s * L / 2

results["P_fH"] = i.mu_a * W_s * -results["x"]
results["P_fC"] = i.mu_a * W_s * (results["x"] - L)
results["P_f"] = results[["P_fH", "P_fC"]].max(axis=1)
results["P"] = results[["S_eff", "P_f"]].max(axis=1)

P_max = results["P"].min()


# --------- Lateral Buckling Calculations -----------

k = np.matrix(
    [
        [80.76, 6.391e-5, 0.5, 2.407e-3, 0.06938],
        [4 * np.pi ** 2, 1.743e-4, 1, 5.532e-3, 0.1088],
        [34.06, 1.668e-4, 1.294, 1.032e-2, 0.1434],
        [28.20, 2.144e-4, 1.608, 1.047e-2, 0.1483],
    ]
)


def buckle_force(L, mode):
    rw = mode - 1
    term1 = (k[rw, 0] * EI) / L ** 2
    term2 = k[rw, 2] * i.mu_a * W_s * L
    term3 = (
        np.sqrt(
            1
            + (k[rw, 1] * A_p * i.E_p * i.mu_l ** 2 * W_s * L ** 5 / (i.mu_a * EI ** 2))
        )
        - 1
    )

    return term1 + term2 * term3


def get_buckle_length(mode):
    x0 = np.array([100])
    return optimize.minimize(buckle_force, x0, args=mode).x[0]


modes = np.arange(1, 5)
buckle_lengths = np.array([get_buckle_length(mode) for mode in modes])

buckle_forces = np.array(
    [-buckle_force(L, mode) for L, mode in zip(buckle_lengths, modes)]
)

results["Buckle Force"] = buckle_forces.max()
results["Actual Force"] = results[["P", "Buckle Force"]].max(axis=1)

results.to_csv(RESULTS_FILE, index=False)

# --------- Plots -----------

from bokeh.io import output_file
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, PrintfTickFormatter, HoverTool
from bokeh.layouts import gridplot

output_file(PLOTS_FILE, title="Buckle Plots")


def generate_plots(results):

    results_cds = ColumnDataSource(results)

    temp_fig = figure(
        title="Temperature Profile",
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label="KP [m]",
        y_axis_label="Temperature [degC]",
    )

    temp_fig.line("x", "T", source=results_cds)
    temp_fig.line("x", "delta_T", color="red", source=results_cds)

    force_fig = figure(
        title="Fully Restrained Effective Axial Force",
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label="KP [m]",
        y_axis_label="Axial Force [N]",
    )
    force_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    force_fig.line("x", "S_eff", source=results_cds)

    friction_fig = figure(
        title="Friction Force",
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label="KP [m]",
        y_axis_label="Friction Force [N]",
    )
    friction_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    friction_fig.line("x", "P_f", source=results_cds)

    resultant_fig = figure(
        title="Resultant Effective Axial Force",
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label="KP [m]",
        y_axis_label="Axial Force [N]",
    )
    resultant_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    resultant_fig.line("x", "P", source=results_cds)

    all_fig = figure(
        title="Pipeline Axial Force",
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label="KP [m]",
        y_axis_label="Axial Force [N]",
    )
    all_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    all_fig.line(
        "x", "P", legend="EAF", color="grey", line_dash="dashed", source=results_cds
    )

    all_fig.line(
        "x",
        "Buckle Force",
        legend="BIF",
        color="red",
        line_dash="dashed",
        source=results_cds,
    )
    all_fig.line("x", "Actual Force", legend="Actual", color="blue", source=results_cds)
    all_fig.legend.location = "top_left"

    # format the tooltip
    tooltips = [
        ("KP", "@x"),
        ("Actual Force", "@{Actual Force}"),
        ("Buckle Force", "@{Buckle Force}"),
        ("EAF", "@P"),
    ]

    # add the HoverTool to the figure
    all_fig.add_tools(HoverTool(tooltips=tooltips))

    buckle_fig = figure(
        title="Buckling Force",
        plot_height=300,
        plot_width=700,
        x_range=(60, 140),
        y_axis_type="log",
        x_axis_label="Minimum Buckle Length [m]",
        y_axis_label="Buckling Force [N]",
    )
    buckle_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    x = np.linspace(60, 140, 100)

    colors = ("red", "blue", "purple", "pink")

    for mode in np.arange(1, 5):
        P_bucs = np.array([buckle_force(L, mode) for L in x])
        color = colors[mode - 1]
        buckle_fig.line(x=x, y=P_bucs, legend=f"Mode {mode}", color=color)

    buckle_fig.line(x=x, y=-P_max, legend="P_max", color="black", line_dash="dashed")

    buckle_fig.legend.location = "top_left"

    return gridplot(
        [
            [all_fig],
            [temp_fig],
            [force_fig],
            [friction_fig],
            [resultant_fig],
            [buckle_fig],
        ]
    )


plots = generate_plots(results)

show(plots)
