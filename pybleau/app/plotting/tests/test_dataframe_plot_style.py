import os
from unittest import skipIf, TestCase

from app_common.apptools.testing_utils import temp_bringup_ui_for

try:
    from chaco.api import ArrayPlotData, Plot
    from pybleau.app.plotting.plot_style import BarPlotStyle, \
        HistogramPlotStyle, LinePlotStyle, ScatterPlotStyle, HeatmapPlotStyle
except ImportError:
    pass

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestPlotStyleAsView(TestCase):
    """ Make sure any styling object can be brought up as a standalone view.

    Needed to support editing the style of a plot after creation.
    """
    def test_open_hist_style_as_view(self):
        with temp_bringup_ui_for(HistogramPlotStyle()):
            pass

    def test_open_bar_style_as_view(self):
        with temp_bringup_ui_for(BarPlotStyle()):
            pass

    def test_open_line_style_as_view(self):
        with temp_bringup_ui_for(LinePlotStyle()):
            pass

    def test_open_scatter_style_as_view(self):
        with temp_bringup_ui_for(ScatterPlotStyle()):
            pass

    def test_open_heatmap_style_as_view(self):
        with temp_bringup_ui_for(HeatmapPlotStyle()):
            pass


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestPlotStyleBehaviors(TestCase):
    def test_initialize_range(self):
        style = LinePlotStyle()
        plot = Plot(ArrayPlotData(x=[1, 2], y=[3, 4]))
        plot.plot(("x", "y"))

        self.assertNotEqual(style.x_axis_range_low, 1)
        self.assertNotEqual(style.x_axis_range_high, 2)
        self.assertNotEqual(style.y_axis_range_low, 3)
        self.assertNotEqual(style.y_axis_range_high, 4)

        self.assertNotEqual(style.auto_x_axis_range_low, 1)
        self.assertNotEqual(style.auto_x_axis_range_high, 2)
        self.assertNotEqual(style.auto_y_axis_range_low, 3)
        self.assertNotEqual(style.auto_y_axis_range_high, 4)

        style.initialize_axis_ranges(plot)

        self.assertEqual(style.x_axis_range_low, 1)
        self.assertEqual(style.x_axis_range_high, 2)
        self.assertEqual(style.y_axis_range_low, 3)
        self.assertEqual(style.y_axis_range_high, 4)

        self.assertEqual(style.auto_x_axis_range_low, 1)
        self.assertEqual(style.auto_x_axis_range_high, 2)
        self.assertEqual(style.auto_y_axis_range_low, 3)
        self.assertEqual(style.auto_y_axis_range_high, 4)

    def test_initialize_range_with_transform(self):
        style = LinePlotStyle()
        plot = Plot(ArrayPlotData(x=[1.1, 2.1], y=[3.1, 4.1]))
        plot.plot(("x", "y"))

        self.assertNotEqual(style.x_axis_range_low, 1.1)
        self.assertNotEqual(style.x_axis_range_high, 2.1)
        self.assertNotEqual(style.y_axis_range_low, 3.1)
        self.assertNotEqual(style.y_axis_range_high, 4.1)

        self.assertNotEqual(style.auto_x_axis_range_low, 1.1)
        self.assertNotEqual(style.auto_x_axis_range_high, 2.1)
        self.assertNotEqual(style.auto_y_axis_range_low, 3.1)
        self.assertNotEqual(style.auto_y_axis_range_high, 4.1)

        style.initialize_axis_ranges(plot)

        self.assertEqual(style.x_axis_range_low, 1.1)
        self.assertEqual(style.x_axis_range_high, 2.1)
        self.assertEqual(style.y_axis_range_low, 3.1)
        self.assertEqual(style.y_axis_range_high, 4.1)

        self.assertEqual(style.auto_x_axis_range_low, 1.1)
        self.assertEqual(style.auto_x_axis_range_high, 2.1)
        self.assertEqual(style.auto_y_axis_range_low, 3.1)
        self.assertEqual(style.auto_y_axis_range_high, 4.1)

        # Initialize rounding numbers at the integer level:
        style.initialize_axis_ranges(plot, transform=0)

        self.assertEqual(style.x_axis_range_low, 1)
        self.assertEqual(style.x_axis_range_high, 2)
        self.assertEqual(style.y_axis_range_low, 3)
        self.assertEqual(style.y_axis_range_high, 4)

        self.assertEqual(style.auto_x_axis_range_low, 1)
        self.assertEqual(style.auto_x_axis_range_high, 2)
        self.assertEqual(style.auto_y_axis_range_low, 3)
        self.assertEqual(style.auto_y_axis_range_high, 4)

    def test_change_plot_range_and_reset(self):
        style = LinePlotStyle()
        # Initial state:
        self.assertEqual(style.x_axis_range_low, style.auto_x_axis_range_low)
        self.assertEqual(style.y_axis_range_low, style.auto_y_axis_range_low)
        self.assertEqual(style.x_axis_range_high, style.auto_x_axis_range_high)
        self.assertEqual(style.y_axis_range_high, style.auto_y_axis_range_high)

        # Change x range
        style.x_axis_range_low = 10
        self.assertNotEqual(style.x_axis_range_low,
                            style.auto_x_axis_range_low)
        style.reset_x_axis_range = True
        self.assertEqual(style.x_axis_range_low, style.auto_x_axis_range_low)

        # Change y range
        style.y_axis_range_low = 10
        style.y_axis_range_high = 20
        self.assertNotEqual(style.y_axis_range_low,
                            style.auto_y_axis_range_low)
        self.assertNotEqual(style.y_axis_range_high,
                            style.auto_y_axis_range_high)
        style.reset_y_axis_range = True
        self.assertEqual(style.y_axis_range_low, style.auto_y_axis_range_low)
        self.assertEqual(style.y_axis_range_high, style.auto_y_axis_range_high)
