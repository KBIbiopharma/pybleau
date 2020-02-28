import os
from unittest import skipIf, TestCase

from app_common.apptools.testing_utils import assert_obj_gui_works

try:
    from chaco.api import ArrayPlotData, Plot
    from pybleau.app.plotting.bar_plot_style import BarPlotStyle
    from pybleau.app.plotting.histogram_plot_style import HistogramPlotStyle
    from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle
    from pybleau.app.plotting.plot_style import SingleLinePlotStyle, \
        SingleScatterPlotStyle, BaseXYPlotStyle
    from pybleau.app.plotting.title_style import TitleStyle
    from pybleau.app.plotting.axis_style import AxisStyle
    from pybleau.app.plotting.contour_style import ContourStyle
    from pybleau.app.plotting.renderer_style import BarRendererStyle, \
        LineRendererStyle, ScatterRendererStyle
except ImportError:
    pass

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestRendererStyleAsView(TestCase):
    """ Make sure any styling renderer object can be brought up as views.
    """
    def test_open_bar_renderer_style_as_view(self):
        assert_obj_gui_works(BarRendererStyle())

    def test_open_line_renderer_style_as_view(self):
        assert_obj_gui_works(LineRendererStyle())

    def test_open_scatter_renderer_style_as_view(self):
        assert_obj_gui_works(ScatterRendererStyle())


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestComponentStyleAsView(TestCase):
    """ Make sure any styling component objects can be brought up as view.
    """
    def test_open_title_style_as_view(self):
        assert_obj_gui_works(TitleStyle())

    def test_open_axis_style_as_view(self):
        assert_obj_gui_works(AxisStyle())

    def test_open_contour_style_as_view(self):
        assert_obj_gui_works(ContourStyle())


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestAxisStyle(TestCase):
    def test_auto_set_auto_range(self):
        axis_style = AxisStyle(range_low=2, range_high=17)
        self.assertEqual(axis_style.range_low, axis_style.auto_range_low)
        self.assertEqual(axis_style.range_high, axis_style.auto_range_high)

    def test_reset_range(self):
        axis_style = AxisStyle(range_low=0, range_high=1, auto_range_low=0,
                               auto_range_high=10)
        axis_style.reset_range = True
        self.assertEqual(axis_style.range_low, axis_style.auto_range_low)
        self.assertEqual(axis_style.range_low, 0)
        self.assertEqual(axis_style.range_high, axis_style.auto_range_high)
        self.assertEqual(axis_style.range_high, 10)


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestPlotStyleAsView(TestCase):
    """ Make sure any styling object can be brought up as a standalone view.

    Needed to support editing the style of a plot after creation.
    """
    def test_open_hist_style_as_view(self):
        assert_obj_gui_works(HistogramPlotStyle())

    def test_open_bar_style_as_view(self):
        assert_obj_gui_works(BarPlotStyle())

    def test_open_line_style_as_view(self):
        assert_obj_gui_works(SingleLinePlotStyle())

    def test_open_scatter_style_as_view(self):
        assert_obj_gui_works(SingleScatterPlotStyle())

    def test_open_heatmap_style_as_view(self):
        assert_obj_gui_works(HeatmapPlotStyle())

    def test_open_base_xy_plot_style(self):
        assert_obj_gui_works(BaseXYPlotStyle())


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestPlotStyleBehaviors(TestCase):
    def test_initialize_range(self):
        style = SingleLinePlotStyle()
        plot = Plot(ArrayPlotData(x=[1, 2], y=[3, 4]))
        plot.plot(("x", "y"))

        self.assertNotEqual(style.x_axis_style.range_low, 1)
        self.assertNotEqual(style.x_axis_style.range_high, 2)
        self.assertNotEqual(style.y_axis_style.range_low, 3)
        self.assertNotEqual(style.y_axis_style.range_high, 4)

        self.assertNotEqual(style.x_axis_style.auto_range_low, 1)
        self.assertNotEqual(style.x_axis_style.auto_range_high, 2)
        self.assertNotEqual(style.y_axis_style.auto_range_low, 3)
        self.assertNotEqual(style.y_axis_style.auto_range_high, 4)

        style.initialize_axis_ranges(plot)

        self.assertEqual(style.x_axis_style.range_low, 1)
        self.assertEqual(style.x_axis_style.range_high, 2)
        self.assertEqual(style.y_axis_style.range_low, 3)
        self.assertEqual(style.y_axis_style.range_high, 4)

        self.assertEqual(style.x_axis_style.auto_range_low, 1)
        self.assertEqual(style.x_axis_style.auto_range_high, 2)
        self.assertEqual(style.y_axis_style.auto_range_low, 3)
        self.assertEqual(style.y_axis_style.auto_range_high, 4)

    def test_initialize_range_with_transform(self):
        style = SingleLinePlotStyle()
        plot = Plot(ArrayPlotData(x=[1.1, 2.1], y=[3.1, 4.1]))
        plot.plot(("x", "y"))

        self.assertNotEqual(style.x_axis_style.range_low, 1.1)
        self.assertNotEqual(style.x_axis_style.range_high, 2.1)
        self.assertNotEqual(style.y_axis_style.range_low, 3.1)
        self.assertNotEqual(style.y_axis_style.range_high, 4.1)

        self.assertNotEqual(style.x_axis_style.auto_range_low, 1.1)
        self.assertNotEqual(style.x_axis_style.auto_range_high, 2.1)
        self.assertNotEqual(style.y_axis_style.auto_range_low, 3.1)
        self.assertNotEqual(style.y_axis_style.auto_range_high, 4.1)

        style.initialize_axis_ranges(plot)

        self.assertEqual(style.x_axis_style.range_low, 1.1)
        self.assertEqual(style.x_axis_style.range_high, 2.1)
        self.assertEqual(style.y_axis_style.range_low, 3.1)
        self.assertEqual(style.y_axis_style.range_high, 4.1)

        self.assertEqual(style.x_axis_style.auto_range_low, 1.1)
        self.assertEqual(style.x_axis_style.auto_range_high, 2.1)
        self.assertEqual(style.y_axis_style.auto_range_low, 3.1)
        self.assertEqual(style.y_axis_style.auto_range_high, 4.1)

        # Initialize rounding numbers at the integer level:
        style.initialize_axis_ranges(plot, transform=0)

        self.assertEqual(style.x_axis_style.range_low, 1)
        self.assertEqual(style.x_axis_style.range_high, 2)
        self.assertEqual(style.y_axis_style.range_low, 3)
        self.assertEqual(style.y_axis_style.range_high, 4)

        self.assertEqual(style.x_axis_style.auto_range_low, 1)
        self.assertEqual(style.x_axis_style.auto_range_high, 2)
        self.assertEqual(style.y_axis_style.auto_range_low, 3)
        self.assertEqual(style.y_axis_style.auto_range_high, 4)

    def test_change_plot_range_and_reset(self):
        style = SingleLinePlotStyle()
        # Initial state:
        self.assertEqual(style.x_axis_style.range_low,
                         style.x_axis_style.auto_range_low)
        self.assertEqual(style.y_axis_style.range_low,
                         style.y_axis_style.auto_range_low)
        self.assertEqual(style.x_axis_style.range_high,
                         style.x_axis_style.auto_range_high)
        self.assertEqual(style.y_axis_style.range_high,
                         style.y_axis_style.auto_range_high)

        # Change x range
        style.x_axis_style.range_low = 10
        self.assertNotEqual(style.x_axis_style.range_low,
                            style.x_axis_style.auto_range_low)
        style.x_axis_style.reset_range = True
        self.assertEqual(style.x_axis_style.range_low,
                         style.x_axis_style.auto_range_low)

        # Change y range
        style.y_axis_style.range_low = 10
        style.y_axis_style.range_high = 20
        self.assertNotEqual(style.y_axis_style.range_low,
                            style.y_axis_style.auto_range_low)
        self.assertNotEqual(style.y_axis_style.range_high,
                            style.y_axis_style.auto_range_high)
        style.y_axis_style.reset_range = True
        self.assertEqual(style.y_axis_style.range_low,
                         style.y_axis_style.auto_range_low)
        self.assertEqual(style.y_axis_style.range_high,
                         style.y_axis_style.auto_range_high)
