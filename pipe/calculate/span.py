import os
import pandas as pd
import numpy as np

from bokeh.io import output_file
from bokeh.plotting import figure, show
from bokeh.models import (
    ColumnDataSource,
    PrintfTickFormatter,
    HoverTool,
    LinearAxis,
    Range1d,
    LabelSet,
    Label,
    Span,
)
from bokeh.layouts import gridplot


from sys import platform

if platform == "win32":
    os.chdir("C:\\dev\\pipe")
else:
    os.chdir("/Users/benranderson/OneDrive/dev/work/pipe/")


from pipe import logger
from pipe.config import DEFAULT_INPUTDATA_FOLDER, DEFAULT_REPORTS_FOLDER

POSITION_FILE = os.path.join(DEFAULT_INPUTDATA_FOLDER, "position.csv")
position_df = pd.read_csv(POSITION_FILE)

allow_len = 10

position_df["BOP [m]"] = -position_df["BOP (m)"]
position_df["MADJ [m]"] = -position_df["MADJ (m)"]

position_df["Allowable Length"] = allow_len

position_df.head()


EVENTS_FILE = os.path.join(DEFAULT_INPUTDATA_FOLDER, "events.csv")
events_df = pd.read_csv(EVENTS_FILE)

spans_df = events_df[events_df["Event"] == "Start of FreeSpan"]
spans_df = spans_df.replace(np.nan, "", regex=True)
spans_df["Midspan"] = spans_df["KP"] + spans_df["Length (m)"] / 2000


anomalies_df = spans_df[spans_df["Length (m)"] > allow_len]
ok_spans_df = spans_df[spans_df["Length (m)"] <= allow_len]


position_cds = ColumnDataSource(position_df)
ok_spans_cds = ColumnDataSource(ok_spans_df)
anomalies_cds = ColumnDataSource(anomalies_df)


route_fig = figure(
    title="Pipeline Route",
    x_axis_label="Easting [m]",
    y_axis_label="Northing [m]",
    match_aspect=True,
)

route_fig.line("Easting (m)", "Northing (m)", source=position_cds)


x_range = (np.floor(position_df["KP"].min()), np.ceil(position_df["KP"].max()))
y_range = (
    np.floor(position_df["BOP [m]"].min()),
    np.ceil(position_df["MADJ [m]"].max()),
)


profile_fig = figure(
    title="Pipeline Profile",
    plot_height=500,
    plot_width=1400,
    x_range=x_range,
    y_range=y_range,
    x_axis_label="KP [km]",
    y_axis_label="BOP [m]",
)

max_span = np.ceil(spans_df["Length (m)"].max()) + 1

# add twin axis for span lengths
profile_fig.extra_y_ranges = {"span_length": Range1d(start=0, end=max_span)}
profile_fig.add_layout(
    LinearAxis(y_range_name="span_length", axis_label="Span Length [m]"), "right"
)

profile_fig.line(
    "KP",
    "Allowable Length",
    legend=dict(value="Allowable Length"),
    color="green",
    source=position_cds,
    line_dash="dashed",
    y_range_name="span_length",
)

profile_fig.line(
    "KP", "BOP [m]", legend="BOP", color="black", source=position_cds, name="BOP"
)
profile_fig.line(
    "KP", "MADJ [m]", legend="MADJ", color="orange", source=position_cds, name="MADJ"
)
profile_fig.scatter(
    "Midspan",
    "Length (m)",
    legend="Span",
    source=ok_spans_cds,
    y_range_name="span_length",
    color="green",
    marker="x",
    size=6,
    name="spans",
)

profile_fig.scatter(
    "Midspan",
    "Length (m)",
    legend="Anomalous",
    source=anomalies_cds,
    y_range_name="span_length",
    color="red",
    marker="x",
    size=6,
    name="anomalies",
)

labels = LabelSet(
    x="Midspan",
    y="Length (m)",
    text="Anomaly",
    level="glyph",
    x_offset=3,
    y_offset=3,
    text_font_size="9pt",
    source=anomalies_cds,
    y_range_name="span_length",
)
profile_fig.add_layout(labels)

tooltips = [
    ("Midspan", "@Midspan km"),
    ("Length", "@{Length (m)} m"),
    ("Height", "@{Height (m)} m"),
]
profile_fig.add_tools(HoverTool(tooltips=tooltips, names=["spans", "anomalies"]))

tooltips2 = [("KP", "@KP km"), ("BOP", "@{BOP [m]} m"), ("MADJ", "@{MADJ [m]} m")]
profile_fig.add_tools(HoverTool(tooltips=tooltips2, names=["BOP", "MADJ"]))


gp = gridplot([[route_fig], [profile_fig]])
show(gp)
