from __future__ import print_function, division
import os
from unittest import TestCase, skipIf
from pandas import DataFrame
from numpy import arange, array, nan, random
from numpy.testing import assert_array_almost_equal

from traits.testing.unittest_tools import UnittestTools

try:
    from chaco.api import BarPlot, LinePlot, Plot, PlotGraphicsContext, \
        ScatterInspectorOverlay, ScatterPlot
    from chaco.plot_containers import HPlotContainer
    from chaco.color_bar import ColorBar
    from chaco.cmap_image_plot import CMapImagePlot
    from chaco.contour_line_plot import ContourLinePlot
    from chaco.tools.api import LegendTool, LegendHighlighter, PanTool
    from chaco.colormapped_selection_overlay import ColormappedSelectionOverlay
    from chaco.colormapped_scatterplot import ColormappedScatterPlot
    from chaco.ticks import DefaultTickGenerator, ShowAllTickGenerator

    from app_common.chaco.scatter_position_tool import \
        DataframeScatterInspector
    from app_common.apptools.testing_utils import temp_bringup_ui_for, \
        wrap_chaco_plot

    from pybleau.app.plotting.plot_factories import BAR_PLOT_TYPE, \
        DEFAULT_FACTORIES, HIST_PLOT_TYPE, LINE_PLOT_TYPE, \
        SCATTER_PLOT_TYPE, HEATMAP_PLOT_TYPE, CMAP_SCATTER_PLOT_TYPE
    from pybleau.app.plotting.bar_factory import BAR_SQUEEZE_FACTOR, \
        ERROR_BAR_DATA_KEY_PREFIX
    from pybleau.app.plotting.histogram_factory import HISTOGRAM_Y_LABEL
    from pybleau.app.plotting.plot_style import HistogramPlotStyle
except ImportError as e:
    print("ERROR: Module imports failed with error: {}".format(e))

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

LEN = 16

TEST_DF = DataFrame({"a": [1, 2, 3, 4] * (LEN//4),
                     "b": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, nan],
                     # Same as above but no nan
                     "b2": sorted(list(range(1, 5)) * (LEN // 4)),
                     "c": list(range(1, LEN+1)),
                     # Non-unique strings:
                     "d": list("ababcabcdabcdeab"),
                     # unique strings:
                     "e": list("abcdefghijklmnop"),
                     "f": random.randn(LEN),
                     # Highly repetitive column to split the entire data into 2
                     "h": array([0, 1] * (LEN // 2), dtype=bool),
                     # Same as above but as a string:
                     "i": ["F", "T"] * (LEN // 2),
                     # Same as above but as a string:
                     "j": ["A", "B", "C", "D"] * (LEN // 4),
                     "k": sorted(list("abcdefgh") * 2),
                     "l": sorted(list("abcd") * 4)})

SCATTER_STYLE = {'z_title_font_size': 18, 'color': 'blue',
                 'y_title_font_size': 18, 'title_font_name': 'modern',
                 'title_font_size': 18, 'alpha': 1.0,
                 'x_title_font_size': 18, 'marker_size': 6, "marker": "circle",
                 "color_palette": "hsv"}

msg = "No UI backend to paint into"


class BaseTestMakePlot(object):
    def setUp(self):
        self.plot_factories = DEFAULT_FACTORIES
        self.plot_factory_klass = self.plot_factories[self.type]

    # Helpers -----------------------------------------------------------------

    def assert_valid_plot(self, plot, desc, num_renderers=1, main_renderer="",
                          test_view=True):
        if isinstance(plot, HPlotContainer):
            is_cmaped = True
            colorbar = plot.plot_components[1]
            self.assertIsInstance(colorbar, ColorBar)
            plot = plot.plot_components[0]
        else:
            is_cmaped = False

        self.assertIsInstance(plot, Plot)
        self.assertIsInstance(desc, dict)
        self.assertIs(desc["plot"], plot)
        if not is_cmaped:
            self.assertEqual(desc["plot_type"], self.type)

        self.assertTrue(desc['visible'])
        self.assertEqual(len(plot.plots), num_renderers)
        for plot_list in plot.plots.values():
            self.assertEqual(len(plot_list), 1)

        if not main_renderer:
            main_renderer = list(plot.plots.values())[0][0]
        else:
            main_renderer = plot.plots[main_renderer][0]

        self.assertIsInstance(main_renderer, self.renderer_class)

        if test_view:
            # Test that we can bring that plot up in a UI:
            with temp_bringup_ui_for(wrap_chaco_plot(plot)):
                pass


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeHistogramPlot(BaseTestMakePlot, TestCase):
    def setUp(self):
        self.renderer_class = BarPlot
        style = {'z_title_font_size': 18, 'bar_width_type': 'data',
                 'color': 'blue', 'y_title_font_size': 18,
                 'bar_width_factor': 1.0, 'title_font_name': 'modern',
                 'title_font_size': 18, 'alpha': 1.0, 'num_bins': 10,
                 'x_title_font_size': 18, "bin_limits": ()}

        self.hist_kw = {'plot_title': 'Foo', 'x_axis_title': 'blah',
                        'plot_style': style}
        self.type = HIST_PLOT_TYPE
        super(TestMakeHistogramPlot, self).setUp()

    def test_histogram_simple_array(self):
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          **self.hist_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.assertEqual(len(plot.data.arrays['a']), 10)
        self.assertAlmostEqual(plot.data.arrays['a'][0], 1.15)
        self.assertAlmostEqual(plot.data.arrays['a'][-1], 3.85)

    def test_histogram_simple_array_different_num_bins(self):
        self.hist_kw['plot_style']["num_bins"] = 20
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          **self.hist_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.assertEqual(len(plot.data.arrays['a']), 20)

    def test_histogram_simple_array_control_bin_limits(self):
        self.hist_kw['plot_style']["bin_limits"] = (0, 10)
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          **self.hist_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        # Range change
        self.assertAlmostEqual(plot.data.arrays['a'][0], 0.5)
        self.assertAlmostEqual(plot.data.arrays['a'][-1], 9.5)

    def test_histogram_array_with_nan(self):
        factory = self.plot_factory_klass(x_col_name="b", x_arr=TEST_DF["b"],
                                          **self.hist_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    def test_make_histgram_no_style(self):
        factory = self.plot_factory_klass(x_col_name="b", x_arr=TEST_DF["b"])
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    def test_make_histogram_from_style_object(self):
        style = HistogramPlotStyle(alpha=0.5)

        factory = self.plot_factory_klass(x_col_name="b", x_arr=TEST_DF["b"],
                                          plot_style=style)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    # Helpers -----------------------------------------------------------------

    def assert_valid_plot(self, plot, desc):
        super(TestMakeHistogramPlot, self).assert_valid_plot(plot, desc)
        self.assertEqual(desc["y_col_name"], HISTOGRAM_Y_LABEL)
        self.assertEqual(desc["y_axis_title"], HISTOGRAM_Y_LABEL)


class BaseTestMakeXYPlot(BaseTestMakePlot):
    """ Tests for the scatter and line plots.
    """
    def setUp(self):
        # Mocking the generation of the style dictionary generated when
        # exporting a configurator to dict:
        style = {'z_title_font_size': 18, 'color': 'blue',
                 "color_palette": "hsv", 'y_title_font_size': 18,
                 'title_font_name': 'modern', 'title_font_size': 18,
                 'alpha': 1.0, 'x_title_font_size': 18,
                 "show_all_x_ticks": False}

        self.plot_kw = {'plot_title': 'Plot 1', 'x_axis_title': 'foo',
                        'plot_style': style}
        super(BaseTestMakeXYPlot, self).setUp()

    def test_plot_simple_array(self):
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    def test_plot_fail_no_y(self):
        with self.assertRaises(ValueError):
            self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                    **self.plot_kw)

    def test_plot_fail_no_x(self):
        with self.assertRaises(ValueError):
            self.plot_factory_klass(y_col_name="a", y_arr=TEST_DF["a"],
                                    **self.plot_kw)

    def test_plot_array_with_nan_along_x(self):
        factory = self.plot_factory_klass(x_col_name="b", x_arr=TEST_DF["b"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    def test_plot_array_with_nan_along_y(self):
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          y_col_name="b", y_arr=TEST_DF["b"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

    def test_with_str_color_dimension(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("a", "b", "d")
        factory = self.plot_factory_klass(x_col_name="a", x_arr=x_arr,
                                          y_col_name="b", y_arr=y_arr,
                                          z_col_name="d", **self.plot_kw)
        plot, desc = factory.generate_plot()
        d_values = TEST_DF["d"].unique()
        self.assert_valid_plot(plot, desc, num_renderers=len(d_values))
        self.assert_renderers_have_distinct_colors(plot)

    def test_with_bool_color_dimension(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("a", "b", "h")
        factory = self.plot_factory_klass(x_col_name="a", x_arr=x_arr,
                                          y_col_name="b", y_arr=y_arr,
                                          z_col_name="h", **self.plot_kw)
        plot, desc = factory.generate_plot()
        h_values = TEST_DF["h"].unique()
        self.assert_valid_plot(plot, desc, num_renderers=len(h_values))

    def test_with_int_color_dimension(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("a", "b", "c")
        factory = self.plot_factory_klass(x_col_name="a", x_arr=x_arr,
                                          y_col_name="b", y_arr=y_arr,
                                          z_col_name="c", **self.plot_kw)
        plot, desc = factory.generate_plot()
        c_values = TEST_DF["c"].unique()
        self.assert_valid_plot(plot, desc, num_renderers=len(c_values))
        self.assert_renderers_have_distinct_colors(plot)

    # Utilities ---------------------------------------------------------------

    def assert_renderers_have_distinct_colors(self, plot):
        if self.type == BAR_PLOT_TYPE:
            # For BarPlots, the color is called fill_color:
            color_list = [plot.plots[name][0].fill_color
                          for name in plot.plots]
        else:
            color_list = [plot.plots[name][0].color for name in plot.plots]

        self.assertEqual(len(color_list), len(set(color_list)))

    def compute_x_y_arrays_split_by(self, x_col, y_col, z_col):
        """ Collect x and y dict of arrays split on specified column.

        Designed to match how BaseSingleXYPlotConfigurator splits the data
        before passing to factories when colored renderers are needed.
        """
        grpby = TEST_DF.groupby(z_col)
        x_arr = {}
        y_arr = {}
        for z_val, subdf in grpby:
            x_arr[z_val] = subdf[x_col].values
            y_arr[z_val] = subdf[y_col].values

        return x_arr, y_arr


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeScatterPlot(BaseTestMakeXYPlot, TestCase):
    def setUp(self):
        self.type = SCATTER_PLOT_TYPE
        self.renderer_class = ScatterPlot
        super(TestMakeScatterPlot, self).setUp()
        self.plot_kw['plot_style']["marker"] = "square"
        self.plot_kw['plot_style']["marker_size"] = 6


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeCmapScatterPlot(BaseTestMakeXYPlot, TestCase):
    def setUp(self):
        self.type = CMAP_SCATTER_PLOT_TYPE
        self.renderer_class = ColormappedScatterPlot
        super(TestMakeCmapScatterPlot, self).setUp()
        self.plot_kw['plot_style']["marker"] = "square"
        self.plot_kw['plot_style']["marker_size"] = 6
        self.plot_kw['z_col_name'] = "b"
        self.plot_kw['z_arr'] = TEST_DF["b"].values

    def test_with_str_color_dimension(self):
        # Cannot be the case, because then it wouldn't be a CmapScatterPlot but
        # a regular ScatterPlot
        pass

    def test_with_bool_color_dimension(self):
        # Cannot be the case, because then it wouldn't be a CmapScatterPlot but
        # a regular ScatterPlot
        pass

    def test_with_int_color_dimension(self):
        # Cannot be the case, because then it wouldn't be a CmapScatterPlot but
        # a regular ScatterPlot
        pass


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeLinePlot(BaseTestMakeXYPlot, TestCase):
    def setUp(self):
        self.type = LINE_PLOT_TYPE
        self.renderer_class = LinePlot
        super(TestMakeLinePlot, self).setUp()


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeBarPlot(BaseTestMakeXYPlot, TestCase, UnittestTools):
    def setUp(self):
        self.type = BAR_PLOT_TYPE
        self.renderer_class = BarPlot
        super(TestMakeBarPlot, self).setUp()
        self.plot_kw['plot_style']["bar_width"] = 0.5
        self.plot_kw["plot_style"]['x_axis_label_rotation'] = 0
        self.plot_kw['plot_style']['data_duplicate'] = "ignore"
        self.plot_kw['plot_style']['bar_style'] = "group"
        self.plot_kw['plot_style']['show_error_bars'] = False

    def test_compute_bar_width(self):
        # bar_plot: if bar_width=0, it's computed from index spacing
        self.plot_kw['plot_style']["bar_width"] = 0.
        factory = self.plot_factory_klass(x_col_name="c", x_arr=TEST_DF["c"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        # distance between x values is 1, so bar width is BAR_SQUEEZE_FACTOR
        renderer = plot.plots['plot0'][0]
        self.assertEqual(renderer.bar_width, BAR_SQUEEZE_FACTOR)

    def test_unique_str_index_no_aggregation(self):
        factory = self.plot_factory_klass(x_col_name="e", x_arr=TEST_DF["e"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        renderer = plot.plots['plot0'][0]
        assert_array_almost_equal(plot.data.arrays["e"],
                                  arange(len(TEST_DF["e"])))
        self.assertEqual(renderer.bar_width, 0.5)

        self.assert_x_axis_labels_equal(plot, TEST_DF["e"].tolist())

    def test_compute_bar_width_single_bar(self):
        """" Regression test: compute bar width when only 1 bar.
        """
        self.plot_kw['plot_style']["bar_width"] = 0.
        factory = self.plot_factory_klass(x_col_name="e", x_arr=TEST_DF["e"][:1],  # noqa
                                          y_col_name="a", y_arr=TEST_DF["a"][:1],  # noqa
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        for arr in plot.data.arrays:
            self.assertEqual(len(arr), 1)

    def test_redundant_str_index_no_aggregation(self):
        factory = self.plot_factory_klass(x_col_name="d", x_arr=TEST_DF["d"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        assert_array_almost_equal(plot.data.arrays["d"], arange(LEN))

        self.assert_x_axis_labels_equal(plot, TEST_DF["d"].tolist())

    def test_redundant_str_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(x_col_name="d", x_arr=TEST_DF["d"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        d_values = set(TEST_DF["d"])
        assert_array_almost_equal(plot.data.arrays["d"], arange(len(d_values)))

        self.assert_x_axis_labels_equal(plot, sorted(TEST_DF["d"].unique()))

    def test_bool_index_no_aggregation(self):
        factory = self.plot_factory_klass(
            x_col_name="h", x_arr=TEST_DF["h"][:2],
            y_col_name="a", y_arr=TEST_DF["a"][:2],
            **self.plot_kw
        )

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["h"], arange(2))

        # Labels are the original DF values converted to strings:
        self.assert_x_axis_labels_equal(plot, ["False", "True"])

    def test_redundant_bool_index_no_aggregation(self):
        factory = self.plot_factory_klass(x_col_name="h", x_arr=TEST_DF["h"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["h"], arange(LEN))

        # Labels are the original DF values converted to strings:
        self.assert_x_axis_labels_equal(plot, [str(x) for x in TEST_DF["h"]])

    def test_bool_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(x_col_name="h", x_arr=TEST_DF["h"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["h"], arange(2))
        # Labels are the original DF values converted to strings:
        self.assert_x_axis_labels_equal(plot, ["False", "True"])

        expected_values = array([TEST_DF["a"][::2].mean(),
                                 TEST_DF["a"][1::2].mean()])
        assert_array_almost_equal(plot.data.arrays["a"], expected_values)

    def test_bool_index_with_aggregation_control_x_labels(self):
        # Same as above but controlling the order of the x_labels
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(
            x_col_name="h", x_arr=TEST_DF["h"], y_col_name="a",
            y_arr=TEST_DF["a"], x_labels=[True, False], **self.plot_kw
        )

        plot, desc = factory.generate_plot()

        self.assert_valid_plot(plot, desc)
        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["h"], arange(2))
        # Labels are the original DF values converted to strings:
        self.assert_x_axis_labels_equal(plot, ["True", "False"])

        expected_values = array([TEST_DF["a"][1::2].mean(),
                                 TEST_DF["a"][::2].mean()])
        assert_array_almost_equal(plot.data.arrays["a"], expected_values)

    def test_str_index_with_aggregation_1_value(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(x_col_name="e", x_arr=TEST_DF["e"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)

        # Make sure all e values are presenting along the index axis
        assert_array_almost_equal(plot.data.arrays["e"],
                                  arange(len(TEST_DF["e"])))

        self.assert_x_axis_labels_equal(plot, TEST_DF["e"].tolist())

        # Single value contributed to each bar so y values are unchanged
        # compared to the DF:
        assert_array_almost_equal(plot.data.arrays["a"], TEST_DF["a"].values)

    def test_str_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(x_col_name="d", x_arr=TEST_DF["d"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.assert_bar_height_averaged(plot)

    def test_str_index_with_aggregation_control_x_labels(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        factory = self.plot_factory_klass(x_col_name="d", x_arr=TEST_DF["d"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          x_labels=list("edcba"),
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.assert_bar_height_averaged(plot, reverse_order=True)

    def test_str_index_with_aggregation_and_errorbars(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        self.plot_kw['plot_style']['show_error_bars'] = True

        factory = self.plot_factory_klass(x_col_name="d", x_arr=TEST_DF["d"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        num_bars = len(TEST_DF["d"].unique())
        self.assert_valid_plot(plot, desc, num_renderers=1+num_bars,
                               main_renderer="plot0")
        self.assert_bar_height_averaged(plot)
        # Make sure the error bar renderers are there too:
        for i in range(len(TEST_DF["d"].unique())):
            key = "plot{}".format(i+1)
            self.assertIn(key, plot.plots)
            self.assertIsInstance(plot.plots[key][0], LinePlot)

    def test_colors_from_str_int_index_no_aggregation(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("b2", "c", "j")
        factory = self.plot_factory_klass(x_col_name="b2", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="j", **self.plot_kw)
        plot, desc = factory.generate_plot()

        j_values = set(TEST_DF["j"])
        self.assert_valid_plot(plot, desc, num_renderers=len(j_values))
        for hue_val in j_values:
            key = "b2"+hue_val
            self.assertIn(key, plot.data.arrays)
            assert_array_almost_equal(plot.data.arrays[key], arange(1, 5))

    def test_colors_from_str_str_index_no_aggregation(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("k", "c", "i")
        factory = self.plot_factory_klass(x_col_name="k", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i", **self.plot_kw)
        plot, desc = factory.generate_plot()

        hue_values = set(TEST_DF["i"])
        self.assert_valid_plot(plot, desc, num_renderers=len(hue_values))
        assert_array_almost_equal(plot.data.arrays["kF"], arange(8))
        assert_array_almost_equal(plot.data.arrays["kT"], arange(8) + 0.4)

        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, list("abcdefgh"))

    def test_colors_from_str_str_index_aggregation_1_value(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        x_arr, y_arr = self.compute_x_y_arrays_split_by("l", "c", "j")
        factory = self.plot_factory_klass(x_col_name="l", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="j", **self.plot_kw)
        plot, desc = factory.generate_plot()

        j_values = set(TEST_DF["j"])
        self.assert_valid_plot(plot, desc, num_renderers=len(j_values))
        assert_array_almost_equal(plot.data.arrays["lA"], arange(4))
        assert_array_almost_equal(plot.data.arrays["lB"],
                                  arange(4) + BAR_SQUEEZE_FACTOR/4.)
        assert_array_almost_equal(plot.data.arrays["lC"],
                                  arange(4) + 2 * BAR_SQUEEZE_FACTOR/4.)
        assert_array_almost_equal(plot.data.arrays["lD"],
                                  arange(4) + 3 * BAR_SQUEEZE_FACTOR/4.)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, list("abcd"))

    def test_colors_from_str_str_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        x_arr, y_arr = self.compute_x_y_arrays_split_by("d", "c", "i")
        factory = self.plot_factory_klass(x_col_name="d", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i", **self.plot_kw)
        plot, desc = factory.generate_plot()
        i_values = set(TEST_DF["i"])
        d_values = set(TEST_DF["d"])
        self.assert_valid_plot(plot, desc, num_renderers=len(i_values))
        assert_array_almost_equal(plot.data.arrays["dF"],
                                  arange(len(d_values)))
        assert_array_almost_equal(plot.data.arrays["dT"],
                                  arange(len(d_values)) + 0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, sorted(d_values))

    def test_colors_from_str_str_index_with_aggregation_and_error_bars(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        self.plot_kw['plot_style']['show_error_bars'] = True

        x_arr, y_arr = self.compute_x_y_arrays_split_by("l", "c", "i")
        factory = self.plot_factory_klass(x_col_name="l", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i", **self.plot_kw)
        plot, desc = factory.generate_plot()
        hue_values = set(TEST_DF["i"])
        x_values = set(TEST_DF["l"])
        self.assert_valid_plot(plot, desc,
                               num_renderers=len(hue_values)*(1+len(x_values)))
        assert_array_almost_equal(plot.data.arrays["lF"],
                                  arange(len(x_values)))
        assert_array_almost_equal(plot.data.arrays["lT"],
                                  arange(len(x_values)) + 0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, sorted(x_values))

        num_error_bars = len(hue_values) * len(x_values)
        self.assert_error_bars_present(plot, num_error_bars)

    def test_colors_from_bool_str_index_with_aggregation_and_error_bars(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        self.plot_kw['plot_style']['show_error_bars'] = True

        x_arr, y_arr = self.compute_x_y_arrays_split_by("l", "c", "h")
        factory = self.plot_factory_klass(x_col_name="l", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="h", **self.plot_kw)
        plot, desc = factory.generate_plot()
        hue_values = set(TEST_DF["h"])
        x_values = set(TEST_DF["l"])
        self.assert_valid_plot(plot, desc,
                               num_renderers=len(hue_values)*(1+len(x_values)))
        assert_array_almost_equal(plot.data.arrays["lFalse"],
                                  arange(len(x_values)))
        assert_array_almost_equal(plot.data.arrays["lTrue"],
                                  arange(len(x_values)) + 0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, sorted(x_values))

        num_error_bars = len(hue_values) * len(x_values)
        self.assert_error_bars_present(plot, num_error_bars)

    def test_colors_from_str_bool_index_with_aggregation_and_error_bars(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        self.plot_kw['plot_style']['show_error_bars'] = True

        x_arr, y_arr = self.compute_x_y_arrays_split_by("h", "c", "i")
        factory = self.plot_factory_klass(x_col_name="h", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i", **self.plot_kw)
        plot, desc = factory.generate_plot()
        hue_values = set(TEST_DF["i"])
        x_values = set(TEST_DF["h"])
        self.assert_valid_plot(plot, desc,
                               num_renderers=len(hue_values)*(1+len(x_values)))
        assert_array_almost_equal(plot.data.arrays["hF"],
                                  arange(len(x_values)))
        assert_array_almost_equal(plot.data.arrays["hT"],
                                  arange(len(x_values)) + 0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, sorted([str(x) for x in x_values]))

        num_error_bars = len(hue_values) * len(x_values)
        self.assert_error_bars_present(plot, num_error_bars)

    def test_colors_from_bool_str_index_no_aggregation(self):
        x_arr, y_arr = self.compute_x_y_arrays_split_by("k", "c", "h")
        factory = self.plot_factory_klass(x_col_name="k", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="h", **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, num_renderers=2)

        assert_array_almost_equal(plot.data.arrays["kFalse"], arange(8))
        assert_array_almost_equal(plot.data.arrays["kTrue"], arange(8)+0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, list("abcdefgh"))

    def test_colors_from_bool_str_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        x_arr, y_arr = self.compute_x_y_arrays_split_by("d", "c", "h")
        factory = self.plot_factory_klass(x_col_name="d", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="h", **self.plot_kw)
        plot, desc = factory.generate_plot()

        i_values = set(TEST_DF["i"])
        d_values = set(TEST_DF["d"])
        self.assert_valid_plot(plot, desc, num_renderers=len(i_values))

        assert_array_almost_equal(plot.data.arrays["dFalse"],
                                  arange(len(d_values)))
        assert_array_almost_equal(plot.data.arrays["dTrue"],
                                  arange(len(d_values)) + 0.4)
        self.force_plot_rendering(plot)
        labels = [x.text for x in plot.x_axis.ticklabel_cache]
        self.assertEqual(labels, sorted(d_values))

    def test_colors_from_str_bool_index_with_aggregation(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        x_arr, y_arr = self.compute_x_y_arrays_split_by("h", "c", "i")
        factory = self.plot_factory_klass(x_col_name="h", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i", **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, num_renderers=2)

        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["hF"], arange(2))
        assert_array_almost_equal(plot.data.arrays["hT"],
                                  arange(2)+BAR_SQUEEZE_FACTOR/2.)
        self.assert_x_axis_labels_equal(plot, ["False", "True"])

        assert_array_almost_equal(plot.data.arrays["cF"],
                                  array([TEST_DF["c"][::2].mean(), nan]))
        assert_array_almost_equal(plot.data.arrays["cT"],
                                  array([nan, TEST_DF["c"][1::2].mean()]))

    def test_colors_from_str_bool_index_with_aggregation_control_xlabels(self):
        self.plot_kw['plot_style']['data_duplicate'] = "mean"
        x_arr, y_arr = self.compute_x_y_arrays_split_by("h", "c", "i")
        factory = self.plot_factory_klass(x_col_name="h", x_arr=x_arr,
                                          y_col_name="c", y_arr=y_arr,
                                          z_col_name="i",
                                          x_labels=[True, False],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, num_renderers=2)

        # Index overwritten to be a list of ints:
        assert_array_almost_equal(plot.data.arrays["hF"], arange(2))
        assert_array_almost_equal(plot.data.arrays["hT"],
                                  arange(2)+BAR_SQUEEZE_FACTOR/2.)
        # Labels are the original DF values converted to strings:
        self.assert_x_axis_labels_equal(plot, ["True", "False"])

        # Values are flipped too:
        assert_array_almost_equal(plot.data.arrays["cF"],
                                  array([nan, TEST_DF["c"][::2].mean()]))
        assert_array_almost_equal(plot.data.arrays["cT"],
                                  array([TEST_DF["c"][1::2].mean(), nan]))

    def test_str_index_dont_force_all_ticks(self):
        """ String index ticks are decimated w/ show_all_x_ticks=False.
        """
        self.plot_kw['plot_style']['show_all_x_ticks'] = False

        factory = self.plot_factory_klass(x_col_name="e", x_arr=TEST_DF["e"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.force_plot_rendering(plot)
        self.assertIsInstance(plot.x_axis.tick_generator, DefaultTickGenerator)
        # Ticks are decimated: every other label isn't displayed:
        self.assertEqual(set(plot.x_axis._tick_label_list),
                         set(TEST_DF["e"][::2]))

    def test_str_index_do_force_all_ticks(self):
        """ String index ticks are NOT decimated w/ show_all_x_ticks=True.
        """
        self.plot_kw['plot_style']['show_all_x_ticks'] = True

        factory = self.plot_factory_klass(x_col_name="e", x_arr=TEST_DF["e"],
                                          y_col_name="a", y_arr=TEST_DF["a"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc)
        self.force_plot_rendering(plot)
        self.assertIsInstance(plot.x_axis.tick_generator, ShowAllTickGenerator)
        self.assertEqual(set(plot.x_axis._tick_label_list), set(TEST_DF["e"]))

    # utilities ---------------------------------------------------------------

    def force_plot_rendering(self, plot):
        # Force plot rendering to make sure all attributes are computed, for
        # example axis labels:
        width = plot.outer_width
        height = plot.outer_height
        gc = PlotGraphicsContext((width, height), dpi=72)
        gc.render_component(plot)

    def assert_x_axis_labels_equal(self, plot, expected):
        with temp_bringup_ui_for(wrap_chaco_plot(plot)):
            self.assertEqual(plot.x_axis.labels, expected)

    def assert_error_bars_present(self, plot, num_error_bars):

        for i in range(num_error_bars):
            key = "plot{}".format(i)
            self.assertIn(key, plot.plots)
            self.assertIsInstance(plot.plots[key][0], LinePlot)
            if plot.legend:
                # Make sure the error bars are not present in the legend:
                self.assertNotIn(key, plot.legend.labels)

        error_bar_x_data = [x for x in plot.data.arrays
                            if x.startswith(ERROR_BAR_DATA_KEY_PREFIX) and
                            x.endswith("_x")]
        error_bar_y_data = [x for x in plot.data.arrays
                            if x.startswith(ERROR_BAR_DATA_KEY_PREFIX) and
                            x.endswith("_y")]
        self.assertEqual(len(error_bar_x_data), num_error_bars)
        self.assertEqual(len(error_bar_y_data), num_error_bars)

    def assert_bar_height_averaged(self, plot, x_col="d", y_col="c",
                                   reverse_order=False):
        # Now that averages are computed, the index is made of the **unique**
        # letters in the d column:
        index_values = sorted([str(x) for x in TEST_DF[x_col].unique()])
        num_uniq_index = len(index_values)
        assert_array_almost_equal(plot.data.arrays[x_col],
                                  arange(num_uniq_index))
        if reverse_order:
            self.assert_x_axis_labels_equal(plot, index_values[::-1])
        else:
            self.assert_x_axis_labels_equal(plot, index_values)

        # And values are averaged:
        if x_col == "d" and y_col == "c":
            a = (1+3+6+10+15) / 5.
            b = (2+4+7+11+16) / 5.
            c = (5+8+12) / 3.
            d = (9+13) / 2.
            e = 14
            if reverse_order:
                assert_array_almost_equal(plot.data.arrays[y_col],
                                          array([e, d, c, b, a]))
            else:
                assert_array_almost_equal(plot.data.arrays[y_col],
                                          array([a, b, c, d, e]))


@skipIf(not BACKEND_AVAILABLE, msg)
class TestMakeHeatmapPlot(BaseTestMakePlot, TestCase):
    def setUp(self):
        self.type = HEATMAP_PLOT_TYPE
        self.renderer_class = CMapImagePlot
        style = {'z_title_font_size': 18, 'y_title_font_size': 18,
                 'title_font_name': 'modern', 'title_font_size': 18,
                 'x_title_font_size': 18, "colormap_str": "cool",
                 "contour_levels": 5, "contour_styles": "solid",
                 "contour_widths": 1, 'contour_alpha': 1.}

        self.heatmap_kw = {'plot_title': 'Plot 1', 'x_axis_title': 'foo',
                           'plot_style': style}

        super(TestMakeHeatmapPlot, self).setUp()

    def test_create_no_contour(self):
        self.heatmap_kw['plot_style']['add_contours'] = False
        factory = self.plot_factory_klass(TEST_DF, x_col_name="a",
                                          y_col_name="b2", z_col_name="c",
                                          **self.heatmap_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, with_contours=False)

    def test_create_with_interpolation(self):
        self.heatmap_kw['plot_style']['add_contours'] = False
        self.heatmap_kw['plot_style']["interpolation"] = "bilinear"

        factory = self.plot_factory_klass(TEST_DF, x_col_name="a",
                                          y_col_name="b2", z_col_name="c",
                                          **self.heatmap_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, with_contours=False)

    def test_create_with_contour(self):
        self.heatmap_kw['plot_style']['add_contours'] = True
        self.heatmap_kw['plot_style']["interpolation"] = "bilinear"
        factory = self.plot_factory_klass(TEST_DF, x_col_name="a",
                                          y_col_name="b2", z_col_name="c",
                                          **self.heatmap_kw)
        plot, desc = factory.generate_plot()
        self.assert_valid_plot(plot, desc, with_contours=True)

    # Helpers -----------------------------------------------------------------

    def assert_valid_plot(self, plot, desc, with_contours=False):
        """ Overridden since plot container generated instead of Plot.
        """
        self.assertIsInstance(plot, HPlotContainer)
        self.assertIsInstance(desc, dict)
        self.assertIs(desc["plot"], plot)
        self.assertEqual(desc["plot_type"], self.type)
        self.assertTrue(desc['visible'])

        # 2 plot areas in the container
        self.assertEqual(len(plot.plot_components), 2)

        main_plot = plot.plot_components[0]
        self.assertIsInstance(main_plot, Plot)
        self.assertIsInstance(plot.plot_components[1], ColorBar)

        # Normally only the image plot in the main plot, except if contours are
        # turned on:
        if with_contours:
            num_renderers = 2
        else:
            num_renderers = 1
        self.assertEqual(len(main_plot.plots), num_renderers)
        self.assertIsInstance(main_plot.plots["plot0"][0],
                              self.renderer_class)
        if with_contours:
            self.assertIsInstance(main_plot.plots["plot1"][0], ContourLinePlot)


class BaseScatterPlotTools(object):
    """ Utilities to test the presence or absence of tools in generated plots.
    """

    def _split_df_for_factory_arrays(self, df=None, color_col="d", x_col="a",
                                     y_col="b"):
        if df is None:
            df = TEST_DF

        grpby = df.groupby(color_col)
        all_x_arr = {}
        for z_val, subdf in grpby:
            all_x_arr[z_val] = subdf[x_col].values

        all_y_arr = {}
        for z_val, subdf in grpby:
            all_y_arr[z_val] = subdf[y_col].values

        return all_x_arr, all_y_arr

    def assert_no_tools(self, plot):
        self.assertEqual(plot.tools, [])
        self.assertEqual(plot.legend.tools, [])
        # Legend and title:
        self.assertEqual(len(plot.overlays), 2)
        for renderers in plot.plots.values():
            for renderer in renderers:
                self.assertEqual(renderer.tools, [])

    def assert_zoom_pan_tools_present(self, factory=None, plot=None):
        if factory is None:
            factory = self.factory

        if plot is None:
            plot = self.plot

        self.assertIn("pan", factory.plot_tools)
        self.assertGreaterEqual(len(plot.tools), 1)
        self.assertIsInstance(plot.tools[0], PanTool)

        self.assertIn("zoom", factory.plot_tools)
        klasses = {o.__class__.__name__ for o in plot.overlays}
        self.assertIn("BetterSelectingZoom", klasses)

    def assert_legend_with_tool(self, factory=None, plot=None,
                                color_values=None):
        if factory is None:
            factory = self.factory

        if plot is None:
            plot = self.plot

        if color_values is None:
            color_values = TEST_DF["d"]

        self.assertIn("legend", factory.plot_tools)
        self.assertTrue(plot.legend.visible)
        self.assertEqual(set(plot.legend.plots.keys()), set(color_values))
        self.assertEqual(len(plot.legend.tools), 2)
        self.assertIsInstance(plot.legend.tools[0], LegendTool)
        self.assertIsInstance(plot.legend.tools[1], LegendHighlighter)

    def assert_click_selector_present(self, factory=None, plot=None):
        if factory is None:
            factory = self.factory

        if plot is None:
            plot = self.plot

        self.assertIn("click_selector", factory.plot_tools)

        for name, renderers in plot.plots.items():
            renderer = renderers[0]
            self.assertEqual(len(renderer.tools), 1)
            # It's a DataFrameInspector because it can then drive both click
            # and hover events/tools:
            self.assertIsInstance(renderer.tools[0], DataframeScatterInspector)
            self.assertGreaterEqual(len(renderer.overlays), 1)
            self.assertIsInstance(renderer.overlays[0],
                                  ScatterInspectorOverlay)

    def assert_hover_tool_present(self, factory, plot):
        self.assertIn("hover", factory.plot_tools)
        klasses = {o.__class__.__name__ for o in plot.overlays}
        self.assertIn("DataframeScatterOverlay", klasses)

        overlay_inspectors = set(plot.overlays[-1].inspectors)
        for name, renderer in plot.plots.items():
            renderer = renderer[0]
            self.assertEqual(len(renderer.tools), 1)
            inspector = renderer.tools[0]
            self.assertIsInstance(inspector, DataframeScatterInspector)
            self.assertIn(inspector, overlay_inspectors)


@skipIf(not BACKEND_AVAILABLE, msg)
class TestScatterPlotTools(TestCase, BaseScatterPlotTools):
    def setUp(self):
        self.type = SCATTER_PLOT_TYPE
        self.style = SCATTER_STYLE

        self.plot_kw = {'plot_title': 'Plot 1', 'x_axis_title': 'foo',
                        'plot_style': self.style}

        self.plot_factory_klass = DEFAULT_FACTORIES[self.type]
        self.factory = self.plot_factory_klass(
            x_col_name="a", x_arr=TEST_DF["a"].values,
            y_col_name="c", y_arr=TEST_DF["c"].values, **self.plot_kw
        )
        self.plot, desc = self.factory.generate_plot()

    def test_tools_present_default(self):
        """ By default, zoom, pan, click selector and legend tools.
        """
        self.assert_zoom_pan_tools_present()
        self.assert_click_selector_present()
        # No legend tool per se since only 1 renderer
        self.assertFalse(self.plot.legend.visible)

        self.assertIn("hover", self.factory.plot_tools)
        # But by default, no hover columns so no overlay:
        self.assertEqual(self.factory.hover_col_names, [])

    def test_hover_tool_no_color(self):
        factory = self.plot_factory_klass(
            x_col_name="a", x_arr=TEST_DF["a"].values,
            y_col_name="c", y_arr=TEST_DF["c"].values,
            hover_col_names=["a"], **self.plot_kw
        )
        plot, desc = factory.generate_plot()
        self.assert_hover_tool_present(factory, plot)

    def test_request_no_tools_present(self):
        factory = self.plot_factory_klass(
            x_col_name="a", x_arr=TEST_DF["a"].values,
            y_col_name="c", y_arr=TEST_DF["c"].values, plot_tools=set(),
            **self.plot_kw
        )
        plot, desc = factory.generate_plot()
        self.assert_no_tools(plot)

    def test_request_no_inspector_tools_present_basic_scatter(self):
        factory = self.plot_factory_klass(
            x_col_name="a", x_arr=TEST_DF["a"].values,
            y_col_name="c", y_arr=TEST_DF["c"].values,
            plot_tools={"pan", "zoom"}, **self.plot_kw
        )
        plot, desc = factory.generate_plot()
        self.assert_zoom_pan_tools_present()
        # Pan is a tool
        self.assertEqual(len(plot.tools), 1)
        # Zoom is an overlay, just like the plot title and legend
        self.assertEqual(len(plot.overlays), 3)
        for renderers in plot.plots.values():
            for renderer in renderers:
                self.assertEqual(renderer.tools, [])

    def test_tools_present_colored_scatter_by_str(self):
        """ Tools present on scatter when color dimension specified.
        """
        all_x_arr, all_y_arr = self._split_df_for_factory_arrays()
        factory = self.plot_factory_klass(x_col_name="a", x_arr=all_x_arr,
                                          y_col_name="b", y_arr=all_y_arr,
                                          z_col_name="d", **self.plot_kw)
        plot, desc = factory.generate_plot()

        self.assert_zoom_pan_tools_present()
        self.assert_legend_with_tool(factory, plot)
        self.assert_click_selector_present(factory, plot)

    def test_tools_present_colored_scatter_by_str_and_hover(self):
        """ Tools present on scatter when color and hover dimensions specified.
        """
        all_x_arr, all_y_arr = self._split_df_for_factory_arrays()
        factory = self.plot_factory_klass(
            x_col_name="a", x_arr=all_x_arr, y_col_name="b", y_arr=all_y_arr,
            z_col_name="d", hover_col_names=["a", "b", "d"], **self.plot_kw
        )
        plot, desc = factory.generate_plot()

        self.assert_zoom_pan_tools_present(factory, plot)
        self.assert_legend_with_tool(factory, plot)
        self.assert_click_selector_present(factory, plot)
        self.assert_hover_tool_present(factory, plot)

    def test_tools_present_colored_scatter_by_str_1_color_and_hover(self):
        # Same as above, but with only 1 color (regression test)
        df = TEST_DF.loc[TEST_DF["d"] == "a", :]
        all_x_arr, all_y_arr = self._split_df_for_factory_arrays(df=df)
        factory = self.plot_factory_klass(
            x_col_name="a", x_arr=all_x_arr, y_col_name="b", y_arr=all_y_arr,
            z_col_name="d", hover_col_names=["a", "b", "d"], **self.plot_kw
        )
        plot, desc = factory.generate_plot()

        self.assert_zoom_pan_tools_present(factory, plot)
        self.assert_click_selector_present(factory, plot)
        self.assert_hover_tool_present(factory, plot)

    def test_selector_tool_overlay_follow_marker(self):
        # Default marker is a circle:
        renderer = list(self.plot.plots.values())[0][0]
        inspector_overlay = renderer.overlays[0]
        self.assertEqual(inspector_overlay.selection_marker, "circle")
        self.assertEqual(inspector_overlay.selection_marker_size, 6)

        # Make another plot with square markers and make sure the overlay
        # follows that:
        self.plot_kw['plot_style']["marker"] = "square"
        self.plot_kw['plot_style']["marker_size"] = 9
        factory = self.plot_factory_klass(x_col_name="a", x_arr=TEST_DF["a"],
                                          y_col_name="c", y_arr=TEST_DF["c"],
                                          **self.plot_kw)
        plot, desc = factory.generate_plot()
        renderer = list(plot.plots.values())[0][0]
        inspector_overlay = renderer.overlays[0]
        self.assertEqual(inspector_overlay.selection_marker, "square")
        self.assertEqual(inspector_overlay.selection_marker_size, 9)


@skipIf(not BACKEND_AVAILABLE, msg)
class TestCmapScatterPlotTools(TestCase, BaseScatterPlotTools):
    def setUp(self):
        self.type = CMAP_SCATTER_PLOT_TYPE
        self.style = SCATTER_STYLE

        self.plot_kw = {'plot_title': 'Plot 1', 'x_axis_title': 'foo',
                        'plot_style': self.style}

        self.plot_factory_klass = DEFAULT_FACTORIES[self.type]
        self.factory = self.plot_factory_klass(
            x_col_name="a", x_arr=TEST_DF["a"],
            y_col_name="c", y_arr=TEST_DF["c"],
            z_col_name="b", z_arr=TEST_DF["b"], **self.plot_kw
        )
        self.container, desc = self.factory.generate_plot()

    def test_tools_present_colored_scatter_by_float(self):
        """ Tools present when building a scatter plot colored by float column.
        """
        factory = self.factory
        container = self.container
        plot = container.plot_components[0]

        self.assert_zoom_pan_tools_present(factory, plot)
        self.assert_click_selector_present(factory, plot)

    def test_tools_present_colored_scatter_by_float_with_hover_col(self):
        """ Tools present for scatter plot colored by float column and hover.
        """
        factory = self.factory
        factory.hover_col_names = ["a", "b"]
        container, desc = self.factory.generate_plot()
        plot = container.plot_components[0]

        self.assert_zoom_pan_tools_present(factory, plot)
        self.assert_click_selector_present(factory, plot)
        self.assert_hover_tool_present(factory, plot)

    # Utilities ---------------------------------------------------------------

    def assert_colorbar_tool_present(self, factory, plot):
        self.assertIn("colorbar_selector", factory.plot_tools)
        for name, renderer in plot.plots.items():
            renderer = renderer[0]
            # First overlay is the click_inspector tool's:
            self.assertIsInstance(renderer.overlays[1],
                                  ColormappedSelectionOverlay)
