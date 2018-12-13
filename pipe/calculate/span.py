#%%
import os
import pandas as pd

from bokeh.io import output_file
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, PrintfTickFormatter, HoverTool
from bokeh.layouts import gridplot

#%%
os.chdir("C:\\dev\\pipe")

#%%
from pipe import logger
from pipe.config import DEFAULT_INPUTDATA_FOLDER, DEFAULT_REPORTS_FOLDER

POSITION_FILE = os.path.join(DEFAULT_INPUTDATA_FOLDER, "position.csv")
position_df = pd.read_csv(POSITION_FILE)

position_df["BOP [m]"] = -position_df["BOP (m)"]
position_df["MADJ [m]"] = -position_df["MADJ (m)"]


position_df.head()

#%%

pos_cds = ColumnDataSource(position_df)

#%%
route_fig = figure(
    title="Pipeline Route",
    x_axis_label="Easting [m]",
    y_axis_label="Northing [m]",
    match_aspect=True,
)

route_fig.line("Easting (m)", "Northing (m)", source=pos_cds)


#%%
profile_fig = figure(
    title="Pipeline Profile",
    x_axis_label="KP [km]",
    y_axis_label="BOP [m]",
)

profile_fig.line("KP", "BOP [m]", source=pos_cds)
profile_fig.line("KP", "MADJ [m]", color="red", source=pos_cds)


#%%
gp = gridplot([[route_fig], [profile_fig]])
show(gp)