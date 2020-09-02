
from unittest import TestCase
import pandas as pd
import numpy as np

from app_common.apptools.io.assertion_utils import assert_roundtrip_identical

from pybleau.app.io.serializer import serialize
from pybleau.app.io.deserializer import deserialize
from pybleau.app.api import DataFrameAnalyzer, DataFramePlotManager
from pybleau.app.model.plot_descriptor import PlotDescriptor
from pybleau.app.plotting.plot_config import BarPlotConfigurator, \
    HeatmapPlotConfigurator, HistogramPlotConfigurator, LinePlotConfigurator, \
    ScatterPlotConfigurator

TEST_DF = pd.DataFrame({"Col_1": [1, 2, 3, 4, 5, 6, 7, 8],
                        "Col_2": np.array([1, 2, 3, 4, 5, 6, 7, 8])[::-1],
                        "Col_3": ["aa_aaa", "bb_bbb", "aa_aaa", "cc_ccc",
                                  "ee_eee", "dd_ddd", "ff_fff", "gg_ggg"],
                        "Col_4": np.random.randn(8),
                        })


TEST_DF2 = pd.DataFrame({"Col_1": [1, 2, 1, 2],
                         "Col_2": [1, 1, 2, 2],
                         "Col_3": np.random.randn(4)})


class TestRoundTripDataFramePlotManager(TestCase):
    def setUp(self):
        # Ignore the content of the canvas manager, the data source and the
        # next_plot_id because the plots cannot be rebuilt since the data
        # source isn't rebuilt:
        self.ignore = ("source_analyzer", "data_source", "canvas_manager",
                       "plot", "plot_factory", "contained_plot_map",
                       "inspectors", "next_plot_id")

    def test_round_trip_df_plotter_with_hist(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_4"
        desc = PlotDescriptor(x_col_name="Col_4", plot_config=config,
                              plot_title="Plot 1")
        self.assert_df_plotter_roundtrip(desc)

    def test_round_trip_df_plotter_with_bar(self):
        config2 = BarPlotConfigurator(data_source=TEST_DF)
        config2.x_col_name = "Col_1"
        config2.y_col_name = "Col_2"
        desc2 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               plot_config=config2, plot_title="Plot 2")
        self.assert_df_plotter_roundtrip(desc2)

    def test_round_trip_df_plotter_with_scatter(self):
        config3 = ScatterPlotConfigurator(data_source=TEST_DF)
        config3.x_col_name = "Col_1"
        config3.y_col_name = "Col_2"
        desc3 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               plot_config=config3, plot_title="Plot 3")
        self.assert_df_plotter_roundtrip(desc3)

    def test_round_trip_df_plotter_with_colored_scatter(self):
        config4 = ScatterPlotConfigurator(data_source=TEST_DF)
        config4.x_col_name = "Col_1"
        config4.y_col_name = "Col_2"
        config4.z_col_name = "Col_3"
        desc4 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               z_col_name="Col_3",
                               plot_config=config4, plot_title="Plot 4")
        self.assert_df_plotter_roundtrip(desc4)

    def test_round_trip_df_plotter_with_line_plot(self):
        config5 = LinePlotConfigurator(data_source=TEST_DF)
        config5.x_col_name = "Col_1"
        config5.y_col_name = "Col_2"
        desc5 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               plot_config=config5, plot_title="Plot 5")
        self.assert_df_plotter_roundtrip(desc5)

    def test_round_trip_df_plotter_bar(self):
        config6 = BarPlotConfigurator(data_source=TEST_DF)
        config6.x_col_name = "Col_3"
        config6.y_col_name = "Col_1"
        desc6 = PlotDescriptor(x_col_name="Col_3", y_col_name="Col_1",
                               plot_config=config6, plot_title="Plot 6")
        self.assert_df_plotter_roundtrip(desc6)

    def test_round_trip_df_plotter_cmap_scatter_type(self):
        config = ScatterPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        config.z_col_name = "Col_4"
        desc = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                              z_col_name="Col_4",
                              plot_config=config, plot_title="Plot 6")

        self.assert_df_plotter_roundtrip(desc)

    def test_round_trip_df_plotter_heatmap_types(self):
        config7 = HeatmapPlotConfigurator(data_source=TEST_DF2)
        config7.x_col_name = "Col_1"
        config7.y_col_name = "Col_2"
        config7.z_col_name = "Col_3"
        desc7 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               z_col_name="Col_3",
                               plot_config=config7, plot_title="Plot 7")

        self.assert_df_plotter_roundtrip(desc7)

    # Support methods ---------------------------------------------------------

    def assert_df_plotter_roundtrip(self, desc):
        analyzer = DataFrameAnalyzer(source_df=TEST_DF)

        options = [[desc], [desc.plot_config], [desc.plot_config] * 3]
        for contained_plots in options:
            plot_manager = DataFramePlotManager(
                contained_plots=contained_plots,
                data_source=TEST_DF, source_analyzer=analyzer
            )
            self.assert_roundtrip_identical(plot_manager, ignore=self.ignore)

    def assert_roundtrip_identical(self, obj, **kwargs):
        assert_roundtrip_identical(obj, serial_func=serialize,
                                   deserial_func=deserialize, **kwargs)
