""" Illustrates how to programmatically create a DF analyzer with populated
plots in the plotter tool.
"""
from app_common.apptools.testing_utils import wrap_chaco_plot
from pandas import DataFrame

from pybleau.app.plotting.api import plot_from_config

from pybleau.app.plotting.plot_config import HeatmapPlotConfigurator

TEST_DF2 = DataFrame({"col 1": ["a", "b", "c", "a", "b", "c", "a", "b", "c"],
                      "col 2": ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
                      "col 3":  [1,   2,   3,   2,   3,   4,   2,   1,   3]})

config1 = HeatmapPlotConfigurator(data_source=TEST_DF2, plot_title="plot 1",
                                  x_col_name="col 1", y_col_name="col 2",
                                  z_col_name="col 3")

plot, _, _ = plot_from_config(config1)
view = wrap_chaco_plot(plot)
view.configure_traits()
