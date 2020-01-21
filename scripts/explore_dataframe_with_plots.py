
from pandas import DataFrame
import numpy as np
from chaco.api import Plot, ArrayPlotData

from app_common.std_lib.logging_utils import initialize_logging

from pybleau.app.api import DataFrameAnalyzer, DataFrameAnalyzerView, \
    DataFramePlotManager
from pybleau.app.model.plot_descriptor import PlotDescriptor
from pybleau.app.plotting.api import BarPlotConfigurator, \
    HistogramPlotConfigurator, LinePlotConfigurator, ScatterPlotConfigurator

initialize_logging(logging_level="DEBUG")

TEST_DF = DataFrame({"Col_1": [1, 2, 3, 4, 5, 6, 7, 8],
                     "Col_2": np.array([1, 2, 3, 4, 5, 6, 7, 8])[::-1],
                     "Col_3": ["aa_aaa", "bb_bbb", "aa_aaa", "cc_ccc",
                               "ee_eee", "dd_ddd", "ff_fff", "gg_ggg"],
})

config = HistogramPlotConfigurator(data_source=TEST_DF)
config.x_col_name = "Col_1"
desc = PlotDescriptor(x_col_name="Col_1", plot_config=config,
                      plot_title="Plot 1")

config2 = BarPlotConfigurator(data_source=TEST_DF)
config2.x_col_name = "Col_1"
config2.y_col_name = "Col_2"
desc2 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                       plot_config=config2, plot_title="Plot 2")

config3 = ScatterPlotConfigurator(data_source=TEST_DF)
config3.x_col_name = "Col_1"
config3.y_col_name = "Col_2"
desc3 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                       plot_config=config3, plot_title="Plot 3")

config4 = ScatterPlotConfigurator(data_source=TEST_DF)
config4.x_col_name = "Col_1"
config4.y_col_name = "Col_2"
config4.z_col_name = "Col_3"
desc4 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                       z_col_name="Col_3",
                       plot_config=config4, plot_title="Plot 4")

config5 = LinePlotConfigurator(data_source=TEST_DF)
config5.x_col_name = "Col_1"
config5.y_col_name = "Col_2"
desc5 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                       plot_config=config5, plot_title="Plot 5")

cust_plot1 = Plot(ArrayPlotData(x=[1, 2, 3], y=[1, 2, 3]))
cust_plot1.plot(("x", "y"))
cust_plot1.title = "Blah"
cust_plot1.x_axis.title = "x"
cust_plot1.y_axis.title = "y"

config6 = BarPlotConfigurator(data_source=TEST_DF)
config6.x_col_name = "Col_3"
config6.y_col_name = "Col_1"
desc6 = PlotDescriptor(x_col_name="Col_3", y_col_name="Col_1",
                       plot_config=config6, plot_title="Plot 6")

analyzer = DataFrameAnalyzer(source_df=TEST_DF)

plot_manager = DataFramePlotManager(
    contained_plots=[desc, desc2, desc3, desc4, desc5, cust_plot1, desc6],
    data_source=TEST_DF, source_analyzer=analyzer
)

view = DataFrameAnalyzerView(
    model=analyzer, include_plotter=True, plotter_layout="Tabbed",
    plotter_kw={"container_layout_type": "horizontal",
                "num_container_managers": 5, "multi_container_mode": 0}
)

view.configure_traits()
