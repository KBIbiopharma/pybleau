import os
from unittest import skipIf, TestCase

from app_common.apptools.testing_utils import assert_obj_gui_works

# try:
from chaco.api import ArrayPlotData, Plot
import pandas as pd
from pybleau.app.api import DataFramePlotManager
from pybleau.app.plotting.api import ScatterPlotConfigurator
from pybleau.app.plotting.bar_plot_style import BarPlotStyle
from pybleau.app.plotting.histogram_plot_style import HistogramPlotStyle
from pybleau.app.plotting.heatmap_plot_style import HeatmapPlotStyle, \
    HeatmapRendererStyle
from pybleau.app.plotting.plot_style import SingleLinePlotStyle, \
    SingleScatterPlotStyle, BaseColorXYPlotStyle, BaseXYPlotStyle
from pybleau.app.plotting.title_style import TitleStyle
from pybleau.app.plotting.axis_style import AxisStyle
from pybleau.app.plotting.contour_style import ContourStyle
from pybleau.app.plotting.renderer_style import LineRendererStyle, \
    ScatterRendererStyle
# except ImportError:
#     pass

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"


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
        # Passing initial values at creation automatically sets the auto values
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

    def test_open_base_color_xy_plot(self):
        assert_obj_gui_works(BaseColorXYPlotStyle())

    def test_open_hybrid_plot(self):
        renderer_styles = [LineRendererStyle(), ScatterRendererStyle()]
        assert_obj_gui_works(BaseXYPlotStyle(renderer_styles=renderer_styles))

    def test_open_hybrid_color_plot_style(self):
        renderer_styles = [LineRendererStyle(), ScatterRendererStyle()]
        obj = BaseColorXYPlotStyle(renderer_styles=renderer_styles)
        assert_obj_gui_works(obj)

    def test_colored_scatter_plot_style_view(self):
        """ Make sure plot style displays renderer styles labeled correctly.
        """
        # Create data for a colored scatter plot where the labels aren't sorted
        # alphabetically:
        test_df = pd.DataFrame({"Col_1": range(4),
                                "Col_2": range(4),
                                "Col_3": ["xyz", "fpq", "abc", "xyz"]})

        config = ScatterPlotConfigurator(data_source=test_df)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        config.z_col_name = "Col_3"
        plot_manager = DataFramePlotManager(contained_plots=[config],
                                            data_source=test_df)
        desc = plot_manager.contained_plots[0]
        style = desc.plot_config.plot_style
        # Check view building works:
        elements = style._get_view_elements()
        all_labels = set()
        col_3_values = set(test_df["Col_3"].values)
        for group in elements[0].content[2].content:
            group_label = group.label
            all_labels.add(group_label)
            trait_name = group.content[0].name
            rend_style = style.trait_get(trait_name)[trait_name]
            self.assertEqual(rend_style.renderer_name, group_label)

        self.assertEqual(all_labels, col_3_values)


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
        style.range_transform = lambda x: int(x)
        style.initialize_axis_ranges(plot)

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


class TestHeatmapPlotStyle(TestCase):
    def test_create_with_renderer(self):
        self.style_klass = HeatmapPlotStyle
        style = self.style_klass(renderer_styles=[
                HeatmapRendererStyle(color_palette="bone", alpha=0.3)
        ])
        self.assertIsInstance(style, HeatmapPlotStyle)
        assert_obj_gui_works(style)
