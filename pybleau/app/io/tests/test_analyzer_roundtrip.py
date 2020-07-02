
from unittest import TestCase
import pandas as pd
import numpy as np

from app_common.apptools.io.assertion_utils import assert_roundtrip_identical

from pybleau.app.io.serializer import serialize
from pybleau.app.io.deserializer import deserialize
from pybleau.app.api import DataFrameAnalyzer
from pybleau.app.plotting.api import BAR_PLOT_TYPE, BarPlotConfigurator, \
    HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator, HIST_PLOT_TYPE, \
    HistogramPlotConfigurator, LINE_PLOT_TYPE, LinePlotConfigurator, \
    SCATTER_PLOT_TYPE, ScatterPlotConfigurator
from pybleau.app.plotting.bar_plot_style import BarPlotStyle
from pybleau.app.plotting.histogram_plot_style import HistogramPlotStyle
from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle
from pybleau.app.plotting.plot_style import BaseColorXYPlotStyle, \
    ScatterRendererStyle, SingleLinePlotStyle
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


class TestRoundTripAnalyzerWithPlots(TestCase):
    """ Serialize an analyzer containing plots.
    """
    def test_part_analysis_and_plotter_scatter_plot(self):
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2")
        self.base_round_trip_analysis_and_plotter_with_plot(
            SCATTER_PLOT_TYPE, ScatterPlotConfigurator, **config_kw
        )

    def test_plotter_scatter_plot_custom_plot_title(self):
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2",
                         plot_title="BLAH")
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            SCATTER_PLOT_TYPE, ScatterPlotConfigurator, **config_kw
        )
        desc = new_analysis.plot_manager_list[0].contained_plots[0]
        self.assertEqual(desc.plot.title.text, "BLAH")

    def test_plotter_scatter_plot_change_descr_plot_title_after(self):
        # Emulate changing the title of the descriptors, as if done in the UI,
        # and make sure the new title isn't lost during serialization:
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2")
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            SCATTER_PLOT_TYPE, ScatterPlotConfigurator, change_title="BLAH",
            **config_kw
        )
        desc = new_analysis.plot_manager_list[0].contained_plots[0]
        self.assertEqual(desc.plot.title.text, "BLAH")

    def test_plotter_frozen_scatter_plot(self):
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2")
        self.base_round_trip_analysis_and_plotter_with_plot(
            SCATTER_PLOT_TYPE, ScatterPlotConfigurator, frozen=True,
            **config_kw
        )

    def test_plotter_styled_scatter_plot(self):
        plot_style = BaseColorXYPlotStyle(
            renderer_styles=[ScatterRendererStyle(marker_size=1)]
        )
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2",
                         plot_style=plot_style)
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            SCATTER_PLOT_TYPE, ScatterPlotConfigurator, **config_kw
        )
        plot_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        renderer_style = plot_desc.plot_config.plot_style.renderer_styles[0]
        self.assertEqual(renderer_style.marker_size, 1)

    def test_plotter_line_plot(self):
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2")
        self.base_round_trip_analysis_and_plotter_with_plot(
            LINE_PLOT_TYPE, LinePlotConfigurator, **config_kw
        )

    def test_plotter_styled_line_plot(self):
        plot_style = SingleLinePlotStyle()
        val = 1.
        self.assertNotEqual(plot_style.renderer_styles[0].line_width, val)
        plot_style.renderer_styles[0].line_width = val

        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2",
                         plot_style=plot_style)
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            LINE_PLOT_TYPE, LinePlotConfigurator, **config_kw
        )
        plot_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        renderer_style = plot_desc.plot_config.plot_style.renderer_styles[0]
        self.assertEqual(renderer_style.line_width, val)

    def test_plotter_bar_plot(self):
        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2")
        self.base_round_trip_analysis_and_plotter_with_plot(
            BAR_PLOT_TYPE, BarPlotConfigurator, **config_kw
        )

    def test_plotter_bar_plot_from_melted_df(self):
        config_kw = dict(columns_to_melt=["Col_1"],
                         melt_source_data=True, x_col_name="variable",
                         y_col_name="value")
        self.base_round_trip_analysis_and_plotter_with_plot(
            BAR_PLOT_TYPE, BarPlotConfigurator, **config_kw
        )

    def test_and_plotter_styled_bar_plot(self):
        plot_style = BarPlotStyle()
        val = 0.1
        self.assertNotEqual(plot_style.renderer_styles[0].bar_width, val)
        plot_style.renderer_styles[0].bar_width = val

        config_kw = dict(x_col_name="Col_1",
                         y_col_name="Col_2",
                         plot_style=plot_style)
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            BAR_PLOT_TYPE, BarPlotConfigurator, **config_kw
        )
        plot_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        renderer_style = plot_desc.plot_config.plot_style.renderer_styles[0]
        self.assertEqual(renderer_style.bar_width, val)

    def test_plotter_hist_plot(self):
        config_kw = dict(x_col_name="Col_1")
        self.base_round_trip_analysis_and_plotter_with_plot(
            HIST_PLOT_TYPE, HistogramPlotConfigurator, **config_kw
        )

    def test_plotter_styled_hist_plot(self):
        config_kw = dict(x_col_name="Col_1",
                         plot_style=HistogramPlotStyle(num_bins=5))
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            HIST_PLOT_TYPE, HistogramPlotConfigurator, **config_kw
        )
        plot_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        self.assertEqual(plot_desc.plot_config.plot_style.num_bins, 5)

    def test_plotter_heatmap_plot(self):
        analysis = DataFrameAnalyzer(source_df=TEST_DF2, filter_exp="")
        config_kw = dict(x_col_name="Col_1", y_col_name="Col_2",
                         z_col_name="Col_3")
        self.base_round_trip_analysis_and_plotter_with_plot(
            HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator, analysis=analysis,
            **config_kw
        )

    def test_plotter_styled_heatmap_plot(self):
        analysis = DataFrameAnalyzer(source_df=TEST_DF2, filter_exp="")
        config_kw = dict(x_col_name="Col_1", y_col_name="Col_2",
                         z_col_name="Col_3",
                         plot_style=HeatmapPlotStyle(interpolation="bilinear"))
        new_analysis = self.base_round_trip_analysis_and_plotter_with_plot(
            HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator, analysis=analysis,
            **config_kw
        )
        plot_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        self.assertEqual(plot_desc.plot_config.plot_style.interpolation,
                         "bilinear")

    # Utility methods ---------------------------------------------------------

    def base_round_trip_analysis_and_plotter_with_plot(self, style, config_klass, analysis=None,  # noqa
                                                       frozen=False, change_title="", **config_kw):  # noqa
        """ Build a task with analysis with plots and check serializability of
        resulting task.
        """
        if analysis is None:
            analysis = make_sample_analysis()

        data_len = len(analysis.filtered_df)
        orig_filter = analysis.filter_exp

        plot_manager = DataFramePlotManager(source_analyzer=analysis,
                                            data_source=analysis.filtered_df)
        configurator = config_klass(
            data_source=analysis.filtered_df, **config_kw
        )
        plot_manager.add_new_plot(style, configurator)
        if frozen:
            # Setting the descriptor as frozen was requested: freeze it and
            # decouple the analysis:
            desc = plot_manager.contained_plots[0]
            desc.frozen = True
            # Change the analysis filter to test that the frozen plot is made
            # with the original threshold
            analysis.filter_exp = "Col_1 > 22"
            analysis.recompute_filtered_df()
            self.assertEqual(desc.data_filter, orig_filter)

        if change_title:
            desc = plot_manager.contained_plots[0]
            desc.plot_title = change_title

        new_analysis = self.assert_roundtrip_identical(analysis)

        # A few manual checks:
        new_desc = new_analysis.plot_manager_list[0].contained_plots[0]
        self.assertEqual(len(new_desc.plot_config.data_source), data_len)
        if frozen:
            self.assertIsNot(new_desc.plot_config.data_source,
                             new_analysis.filtered_df)
        else:
            self.assertIs(new_desc.plot_config.data_source,
                          new_analysis.filtered_df)

        if change_title:
            self.assertEqual(new_desc.plot.title.text, change_title)
            self.assertEqual(new_desc.plot_title, change_title)
            self.assertEqual(new_desc.plot_config.plot_title, change_title)

        plot_managers = new_analysis.plot_manager_list
        self.assertEqual(len(plot_managers), 1)
        self.assertEqual(len(plot_managers[0].contained_plots), 1)
        plot_desc = plot_managers[0].contained_plots
        container_manager = plot_managers[0].canvas_manager.container_managers[0]  # noqa
        plot_container_map = container_manager.plot_map
        plot_container = container_manager.container
        self.assertEqual(len(plot_container_map), 1)
        self.assertIn(plot_desc[0].plot,
                      [plot for plot, position in plot_container_map.values()])
        self.assertEqual(len(plot_container.components), 1)
        self.assertIs(plot_desc[0].plot, plot_container.components[0])
        return new_analysis

    def assert_roundtrip_identical(self, obj, **kwargs):
        SKIPS = {"source_analyzer", "canvas_manager", "uuid", "plot",
                 "inspectors", "plot_factory"}
        return assert_roundtrip_identical(obj, serial_func=serialize,
                                          deserial_func=deserialize,
                                          ignore=SKIPS, **kwargs)


def make_sample_analysis():
    from pybleau.app.model.dataframe_analyzer import DataFrameAnalyzer
    return DataFrameAnalyzer(source_df=TEST_DF)
