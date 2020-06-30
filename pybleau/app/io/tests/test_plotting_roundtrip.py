
from unittest import TestCase
import pandas as pd
import numpy as np

from app_common.apptools.io.assertion_utils import assert_roundtrip_identical

from pybleau.app.io.serializer import serialize
from pybleau.app.io.deserializer import deserialize
from pybleau.app.api import DataFrameAnalyzer
from pybleau.app.model.plot_descriptor import PlotDescriptor
from pybleau.app.plotting.api import BarPlotConfigurator, \
    HeatmapPlotConfigurator, HistogramPlotConfigurator, LinePlotConfigurator, \
    ScatterPlotConfigurator
from pybleau.app.model.dataframe_plot_manager import DataFramePlotManager

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
        self.ignore = ("source_analyzer", "data_source", "canvas_manager",
                       "plot", "plot_factory", "contained_plot_map",
                       "inspectors")

    def test_round_trip_df_plotter_basic_types(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_4"
        desc = PlotDescriptor(x_col_name="Col_4", plot_config=config,
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

        config6 = BarPlotConfigurator(data_source=TEST_DF)
        config6.x_col_name = "Col_3"
        config6.y_col_name = "Col_1"
        desc6 = PlotDescriptor(x_col_name="Col_3", y_col_name="Col_1",
                               plot_config=config6, plot_title="Plot 6")

        analyzer = DataFrameAnalyzer(source_df=TEST_DF)

        plot_manager = DataFramePlotManager(
            contained_plots=[desc, desc2, desc3, desc4, desc5, desc6],
            data_source=TEST_DF, source_analyzer=analyzer
        )
        self.assert_roundtrip_identical(plot_manager, ignore=self.ignore)

    def test_round_trip_df_plotter_cmap_scatter_type(self):
        config = ScatterPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        config.z_col_name = "Col_4"
        desc = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                              z_col_name="Col_4",
                              plot_config=config, plot_title="Plot 6")

        analyzer = DataFrameAnalyzer(source_df=TEST_DF)

        plot_manager = DataFramePlotManager(
            contained_plots=[desc],
            data_source=TEST_DF, source_analyzer=analyzer
        )

        self.assert_roundtrip_identical(plot_manager, ignore=self.ignore)

    def test_round_trip_df_plotter_heatmap_types(self):
        config7 = HeatmapPlotConfigurator(data_source=TEST_DF2)
        config7.x_col_name = "Col_1"
        config7.y_col_name = "Col_2"
        config7.z_col_name = "Col_3"
        desc7 = PlotDescriptor(x_col_name="Col_1", y_col_name="Col_2",
                               z_col_name="Col_3",
                               plot_config=config7, plot_title="Plot 6")

        analyzer2 = DataFrameAnalyzer(source_df=TEST_DF2)

        plot_manager2 = DataFramePlotManager(
            contained_plots=[desc7],
            data_source=TEST_DF2, source_analyzer=analyzer2
        )

        self.assert_roundtrip_identical(plot_manager2, ignore=self.ignore)

    # Support methods ---------------------------------------------------------

    def assert_roundtrip_identical(self, obj, **kwargs):
        assert_roundtrip_identical(obj, serial_func=serialize,
                                   deserial_func=deserialize, **kwargs)
