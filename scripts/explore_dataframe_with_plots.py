""" Illustrates how to programmatically create a DF analyzer with populated
plots in the plotter tool.
"""
from pandas import DataFrame
import numpy as np
from chaco.api import Plot, ArrayPlotData

from app_common.std_lib.logging_utils import initialize_logging

from pybleau.app.api import DataFrameAnalyzer, DataFrameAnalyzerView, \
    DataFramePlotManager
from pybleau.app.model.plot_descriptor import PlotDescriptor
from pybleau.app.plotting.api import BarPlotConfigurator, \
    HistogramPlotConfigurator, LinePlotConfigurator, ScatterPlotConfigurator
from pybleau.app.plotting.multi_plot_config import MultiLinePlotConfigurator

initialize_logging(logging_level="DEBUG")

TEST_DF = DataFrame({"Col_1": [1, 2, 3, 4, 5, 6, 7, 8],
                     "Col_2": 5*np.array([1, 2, 3, 4, 5, 6, 7, 8])[::-1],
                     "Col_3": ["aa_aaa", "bb_bbb", "aa_aaa", "cc_ccc",
                               "ee_eee", "dd_ddd", "ff_fff", "gg_ggg"],
                     "Col_4": np.random.randn(8),
                     })

config = HistogramPlotConfigurator(data_source=TEST_DF)
config.x_col_name = "Col_4"

config2 = BarPlotConfigurator(data_source=TEST_DF)
config2.x_col_name = "Col_1"
config2.y_col_name = "Col_2"
desc2 = PlotDescriptor(plot_config=config2, plot_title="Plot 2")

config3 = ScatterPlotConfigurator(data_source=TEST_DF)
config3.x_col_name = "Col_1"
config3.y_col_name = "Col_2"
desc3 = PlotDescriptor(plot_config=config3, plot_title="Plot 3")

config4 = ScatterPlotConfigurator(data_source=TEST_DF)
config4.x_col_name = "Col_1"
config4.y_col_name = "Col_2"
config4.z_col_name = "Col_3"
desc4 = PlotDescriptor(plot_config=config4, plot_title="Plot 4")

config5 = LinePlotConfigurator(data_source=TEST_DF)
config5.x_col_name = "Col_1"
config5.y_col_name = "Col_2"
desc5 = PlotDescriptor(plot_config=config5, plot_title="Plot 5")

cust_plot1 = Plot(ArrayPlotData(x=[1, 2, 3], y=[1, 2, 3]))
cust_plot1.plot(("x", "y"))
cust_plot1.title = "Blah"
cust_plot1.x_axis.title = "x"
cust_plot1.y_axis.title = "y"

config6 = BarPlotConfigurator(data_source=TEST_DF)
config6.x_col_name = "Col_3"
config6.y_col_name = "Col_1"
desc6 = PlotDescriptor(plot_config=config6, plot_title="Plot 6")

config7 = MultiLinePlotConfigurator(data_source=TEST_DF)
config7.x_col_name = "Col_1"
config7.y_col_names = ["Col_1", "Col_2", "Col_4"]
desc7 = PlotDescriptor(plot_config=config7, plot_title="Plot 7",
                       container_idx=1)

config8 = ScatterPlotConfigurator(data_source=TEST_DF)
config8.x_col_name = "Col_1"
config8.y_col_name = "Col_2"
config8.z_col_name = "Col_4"
desc8 = PlotDescriptor(plot_config=config8, plot_title="Plot 8",
                       container_idx=1)

analyzer = DataFrameAnalyzer(source_df=TEST_DF)

plot_manager = DataFramePlotManager(
    contained_plots=[
        config,
        desc2,
        desc3,
        desc4,
        desc5,
        cust_plot1,
        desc6,
        desc7,
        # desc8
    ],
    data_source=TEST_DF, source_analyzer=analyzer
)

view = DataFrameAnalyzerView(
    model=analyzer, include_plotter=True, plotter_layout="Tabbed",
    plotter_kw={"container_layout_type": "horizontal",
                "num_container_managers": 5, "multi_container_mode": 0}
)

view.configure_traits()
