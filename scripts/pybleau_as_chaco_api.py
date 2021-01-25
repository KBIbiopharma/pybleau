""" Illustrates how to programmatically create a DF analyzer with populated
plots in the plotter tool.
"""

import numpy as np
from app_common.apptools.testing_utils import wrap_chaco_plot
from app_common.std_lib.logging_utils import initialize_logging
from pandas import DataFrame

from pybleau.app.plotting.api import plot_from_config

from pybleau.app.plotting.plot_config import HeatmapPlotConfigurator, \
    BarPlotConfigurator

initialize_logging(logging_level="DEBUG")

col4 = np.random.randn(8)

TEST_DF = DataFrame({"a": [1, 2, 1, 2],
                     "b": [1, 1, 2, 2],
                     "c": [1, 2, 3, 4]})

TEST_DF2 = DataFrame({"a": ["a", "b", "c", "a", "b", "c", "a", "b", "c"],
                      "b": ["a", "a", "a", "b", "b", "b", "c", "c", "c"],
                      "c": [1, 2, 3, 2, 3, 4, 2, 1, 3]})

config1 = HeatmapPlotConfigurator(data_source=TEST_DF2, plot_title="plot 1",
                                  x_col_name="a", y_col_name="b",
                                  z_col_name="c")

config2 = BarPlotConfigurator(data_source=TEST_DF2, plot_title="plot 2",
                              x_col_name="a", y_col_name="c")

plot, _, _ = plot_from_config(config1)
view = wrap_chaco_plot(plot)
view.configure_traits()
