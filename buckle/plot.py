import numpy as np
from bokeh.io import output_file
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, PrintfTickFormatter, HoverTool
from bokeh.layouts import gridplot


def generate_fig(results, title, series, x_axis_label, y_axis_label):

    results_cds = ColumnDataSource(results)

    fig = figure(
        title=title,
        plot_height=300,
        plot_width=700,
        x_range=(results["x"].min(), results["x"].max()),
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )

    fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

    for s in series:
        x, y, legend, color, line_dash = s
        fig.line(
            x, y, legend=legend, color=color, line_dash=line_dash, source=results_cds
        )

    return fig


# def generate_buckle_fig(results):

#     buckle_fig = figure(
#         title="Buckling Force",
#         plot_height=300,
#         plot_width=700,
#         x_range=(60, 140),
#         y_axis_type="log",
#         x_axis_label="Minimum Buckle Length [m]",
#         y_axis_label="Buckling Force [N]",
#     )
#     buckle_fig.yaxis[0].formatter = PrintfTickFormatter(format="%4.1e")

#     x = np.linspace(60, 140, 100)

#     colors = ("red", "blue", "purple", "pink")

#     for mode in np.arange(1, 5):
#         P_bucs = np.array([buckle_force(L, mode) for L in x])
#         color = colors[mode - 1]
#         buckle_fig.line(x=x, y=P_bucs, legend=f"Mode {mode}", color=color)

#     # buckle_fig.line(x=x, y=-P_max, legend="P_max", color="black", line_dash="dashed")

#     buckle_fig.legend.location = "top_left"

#     return buckle_fig


def generate_plots(results):

    temp_fig = generate_fig(
        results,
        "Temperature Profile",
        [
            ("x", "T", "Internal Temperature", "blue", []),
            ("x", "delta_T", "Temperature Difference", "red", []),
        ],
        "KP [m]",
        "Temperature [degC]",
    )
    force_fig = generate_fig(
        results,
        "Fully Restrained Effective Axial Force",
        [("x", "F_eff", None, "blue", [])],
        "KP [m]",
        "Axial Force [N]",
    )
    friction_fig = generate_fig(
        results,
        "Friction Force",
        [("x", "F_f", None, "blue", [])],
        "KP [m]",
        "Friction Force [N]",
    )
    resultant_fig = generate_fig(
        results,
        "Resultant Effective Axial Force",
        [("x", "F_res", None, "blue", [])],
        "KP [m]",
        "Axial Force [N]",
    )
    all_fig = generate_fig(
        results,
        "Pipeline Axial Force",
        [
            ("x", "F_actual", "Resultant", "blue", []),
            ("x", "F_res", "EAF", "grey", "dashed"),
            ("x", "F_b", "BIF", "red", "dashed"),
        ],
        "KP [m]",
        "Axial Force [N]",
    )

    return gridplot(
        [[temp_fig], [force_fig], [friction_fig], [resultant_fig], [all_fig]]
    )

