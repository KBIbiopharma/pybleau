from os.path import dirname
from unittest import TestCase, skipIf
from unittest.mock import patch

from pandas import DataFrame
import os
from numpy.testing import assert_array_equal
from six import string_types

from chaco.api import Legend
from pandas.testing import assert_frame_equal
from traits.has_traits import HasTraits, provides
from traits.testing.unittest_tools import UnittestTools

from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor
from pybleau.app.plotting.plot_config import BaseSinglePlotConfigurator

try:
    import kiwisolver  # noqa

    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if KIWI_AVAILABLE and BACKEND_AVAILABLE:
    from chaco.base_plot_container import BasePlotContainer
    from chaco.api import AbstractPlotRenderer, ArrayPlotData, BarPlot, \
        LinePlot, Plot, ScatterPlot

    from app_common.chaco.constraints_plot_container_manager import \
        ConstraintsPlotContainerManager

    from pybleau.app.model.dataframe_plot_manager import \
        CONTAINER_IDX_REMOVAL, DataFramePlotManager
    from pybleau.app.model.multi_canvas_manager import DEFAULT_NUM_CONTAINERS
    from pybleau.app.model.plot_descriptor import CUSTOM_PLOT_TYPE, \
        PlotDescriptor
    from pybleau.app.model.dataframe_analyzer import DataFrameAnalyzer
    from pybleau.app.plotting.multi_plot_config import \
        MultiHistogramPlotConfigurator
    from pybleau.app.plotting.plot_config import BarPlotConfigurator, \
        HistogramPlotConfigurator, LinePlotConfigurator, \
        ScatterPlotConfigurator
    from pybleau.app.plotting.scatter_factories import \
        SELECTION_METADATA_NAME, DISCONNECTED_SELECTION_COLOR, SELECTION_COLOR
    from pybleau.app.plotting.base_factories import DEFAULT_RENDERER_NAME
    from pybleau.app.plotting.renderer_style import DEFAULT_RENDERER_COLOR, \
        STYLE_R_ORIENT
    from pybleau.app.plotting.histogram_factory import HISTOGRAM_Y_LABEL
    from pybleau.app.utils.string_definitions import CMAP_SCATTER_PLOT_TYPE, \
        HEATMAP_PLOT_TYPE

TEST_DF = DataFrame({"a": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                     "b": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
                     "c": [1, 2, 3, 4, 2, 3, 1, 1, 4, 4, 5, 6, 4, 4, 5, 6],
                     "d": list("ababcabcdabcdeab"),
                     "e": range(16)
                     },
                    dtype="float")

NUM_D_VALUES = len(set(TEST_DF["d"]))

msg = "No UI backend to paint into or missing kiwisolver package"

CMAP_PLOT_TYPES = {CMAP_SCATTER_PLOT_TYPE, HEATMAP_PLOT_TYPE}

HERE = dirname(__file__)

class BasePlotManagerTools(UnittestTools):

    def setUp(self):
        self.model = DataFramePlotManager(data_source=TEST_DF)
        # Basic configurator for a histogram plot:
        self.config = HistogramPlotConfigurator(data_source=TEST_DF,
                                                plot_title="Plot")
        self.config.x_col_name = "a"

        self.config2 = HistogramPlotConfigurator(data_source=TEST_DF,
                                                 plot_title="Plot 2")
        self.config2.x_col_name = "a"

        self.config3 = ScatterPlotConfigurator(data_source=TEST_DF,
                                               plot_title="Plot")
        self.config3.x_col_name = "a"
        self.config3.y_col_name = "b"

        self.config4 = ScatterPlotConfigurator(data_source=TEST_DF,
                                               plot_title="Plot")
        self.config4.x_col_name = "a"
        self.config4.y_col_name = "b"
        self.config4.z_col_name = "d"

        self.config5 = ScatterPlotConfigurator(data_source=TEST_DF,
                                               plot_title="Plot")
        self.config5.x_col_name = "a"
        self.config5.y_col_name = "b"
        self.config5.z_col_name = "e"

    # Helper utilities --------------------------------------------------------

    def assert_plot_created(self, num_plots=1, container_idx=0,
                            num_plot_in_container=None, single_container=True,
                            renderer_type=None, num_renderers=1):

        if renderer_type is None:
            renderer_type = AbstractPlotRenderer

        if num_plot_in_container is None:
            num_plot_in_container = num_plots

        self.assertEqual(len(self.model.contained_plots), num_plots)
        container = self.model.canvas_manager.container_managers[
            container_idx
        ]
        self.assertEqual(len(container.plot_map), num_plot_in_container)

        for plot_desc in self.model.contained_plots:
            self.assertIsInstance(plot_desc, PlotDescriptor)
            self.assertIsInstance(plot_desc.id, string_types)
            self.assertIsInstance(plot_desc.plot, BasePlotContainer)
            if plot_desc.plot_type in CMAP_PLOT_TYPES:
                self.assertEqual(len(plot_desc.plot.components), 2)
                plot = plot_desc.plot.components[0]
            else:
                plot = plot_desc.plot

            self.assertEqual(len(plot.components), num_renderers)
            for renderer in plot.components:
                self.assertIsInstance(renderer, renderer_type)

            if single_container:
                self.assertIn(plot_desc.plot, container.container.components)

    def assert_no_plot_in_container(self, idx):
        container = self.model.canvas_manager.container_managers[idx]
        self.assertEqual(container.plot_map, {})
        self.assertEqual(container.container.components, [])


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerAddPlots(BasePlotManagerTools, TestCase):
    def test_create_manager(self):
        self.assert_empty_manager()

    def test_create_with_empty_plot_list(self):
        """ Create with empty list since may be serialized that way.
        """
        model = DataFramePlotManager(data_source=TEST_DF, contained_plots=[])
        self.assert_empty_manager(model)
        config = self.config
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)

    def test_add_histogram(self):
        config = self.config
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)
        # Plot is nowhere else:
        for i in range(1, DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_bar_plot(self):
        config = BarPlotConfigurator(data_source=TEST_DF,
                                     plot_title="Plot")
        config.x_col_name = "e"
        config.y_col_name = "b"

        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)
        # Plot is nowhere else:
        for i in range(1, DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "e")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_lineplot(self):
        config = LinePlotConfigurator(data_source=TEST_DF,
                                      plot_title="Plot")
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=LinePlot)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_scatter(self):
        self.model._add_new_plot(self.config3)
        self.assert_plot_created(renderer_type=ScatterPlot)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_colored_scatter(self):
        config = self.config4
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=ScatterPlot,
                                 num_renderers=NUM_D_VALUES)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.z_col_name, "d")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_cmap_scatter(self):
        config = self.config5
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=ScatterPlot)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.z_col_name, "e")
        self.assertEqual(plot_desc.plot_title, "Plot")

    def test_add_multi_histograms(self):
        config = MultiHistogramPlotConfigurator(data_source=TEST_DF,
                                                plot_title="Plot {i}")
        config.x_col_names = ["a", "b"]
        self.model._add_new_plots(config)
        self.assert_plot_created(num_plots=2, renderer_type=BarPlot)

        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.plot_title, "Plot 1")

        plot_desc = self.model.contained_plots[1]
        self.assertEqual(plot_desc.x_col_name, "b")
        self.assertEqual(plot_desc.plot_title, "Plot 2")

    def test_add_custom_plot_at_creation(self):
        cust_plot1 = self.create_custom_plot()
        model = DataFramePlotManager(data_source=TEST_DF,
                                     contained_plots=[cust_plot1])
        self.assertEqual(len(model.contained_plots), 1)
        self.assertIsInstance(model.contained_plots[0], PlotDescriptor)
        desc = model.contained_plots[0]
        self.assertTrue(desc.frozen)
        self.assertEqual(desc.plot_type, CUSTOM_PLOT_TYPE)
        self.assertEqual(desc.plot_title, "Blah")
        self.assertEqual(desc.x_axis_title, "x")
        self.assertEqual(desc.y_axis_title, "y")
        self.assertIs(desc.plot, cust_plot1)
        self.assertEqual(len(model.contained_plot_map), 1)
        container = model.canvas_manager.container_managers[0].container
        self.assertIn(cust_plot1, container.components)

    def test_add_custom_plot_after_creation(self):
        model = DataFramePlotManager(data_source=TEST_DF)

        cust_plot1 = self.create_custom_plot()
        model.add_new_plot(CUSTOM_PLOT_TYPE, cust_plot1)
        self.assertEqual(len(model.contained_plots), 1)
        self.assertIsInstance(model.contained_plots[0], PlotDescriptor)
        desc = model.contained_plots[0]
        self.assertTrue(desc.frozen)
        self.assertEqual(desc.plot_type, CUSTOM_PLOT_TYPE)
        self.assertEqual(desc.plot_title, "Blah")
        self.assertEqual(desc.x_axis_title, "x")
        self.assertEqual(desc.y_axis_title, "y")
        self.assertIs(desc.plot, cust_plot1)
        self.assertEqual(len(model.contained_plot_map), 1)
        container = model.canvas_manager.container_managers[0].container
        self.assertIn(cust_plot1, container.components)

    def test_add_custom_plot_as_descriptor_after_creation(self):
        model = DataFramePlotManager(data_source=TEST_DF)

        plot = self.create_custom_plot()
        cust_plot_desc = PlotDescriptor(
            plot_type=CUSTOM_PLOT_TYPE, plot=plot,
            plot_config=BaseSinglePlotConfigurator(),
            plot_title=plot.title,
            x_axis_title=plot.x_axis.title,
            y_axis_title=plot.y_axis.title, frozen=True,
        )

        model.add_new_plot(CUSTOM_PLOT_TYPE, cust_plot_desc)
        self.assertEqual(len(model.contained_plots), 1)
        self.assertIsInstance(model.contained_plots[0], PlotDescriptor)
        desc = model.contained_plots[0]
        self.assertIs(desc, cust_plot_desc)
        self.assertTrue(desc.frozen)
        self.assertEqual(desc.plot_type, CUSTOM_PLOT_TYPE)
        self.assertEqual(desc.plot_title, "Blah")
        self.assertEqual(desc.x_axis_title, "x")
        self.assertEqual(desc.y_axis_title, "y")
        self.assertIs(desc.plot, plot)
        self.assertEqual(len(model.contained_plot_map), 1)
        container = model.canvas_manager.container_managers[0].container
        self.assertIn(plot, container.components)

    # Supporting methods ------------------------------------------------------

    def assert_empty_manager(self, model=None):
        if model is None:
            model = self.model

        self.assertIsInstance(model, DataFramePlotManager)
        self.assertEqual(len(model.canvas_manager.container_managers),
                         DEFAULT_NUM_CONTAINERS)
        for container_manager in model.canvas_manager.container_managers:
            self.assertIsInstance(container_manager,
                                  ConstraintsPlotContainerManager)
            self.assertIsNotNone(container_manager.container)

        self.assertEqual(model.contained_plots, [])
        self.assertIsNone(model.source_analyzer)

    def create_custom_plot(self):
        cust_plot = Plot(ArrayPlotData(x=[1, 2, 3], y=[1, 2, 3]))
        cust_plot.plot(("x", "y"))
        cust_plot.title = "Blah"
        cust_plot.x_axis.title = "x"
        cust_plot.y_axis.title = "y"
        return cust_plot


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerUpdatePlots(BasePlotManagerTools, TestCase):

    def test_change_style_color_1_scatter(self):
        self.model._add_new_plot(self.config3)
        self.assert_plot_created(renderer_type=ScatterPlot)
        plot_desc = self.model.contained_plots[0]
        style = plot_desc.plot_config.plot_style
        renderer = plot_desc.plot_factory.renderers[DEFAULT_RENDERER_NAME]
        self.assertEqual(renderer.color, DEFAULT_RENDERER_COLOR)

        style.renderer_styles[0].color = "red"
        with self.assertTraitChanges(self.model, "contained_plots[]"):
            plot_desc.style_edited = True

        self.assertNotIn(plot_desc, self.model.contained_plots)
        plot_desc = self.model.contained_plots[0]
        renderer = plot_desc.plot_factory.renderers[DEFAULT_RENDERER_NAME]
        self.assertEqual(renderer.color, "red")

    def test_change_style_color_colored_scatter(self):
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        rend_styles = desc.plot_config.plot_style.renderer_styles
        colors = [style.color for style in rend_styles]
        self.assertEqual(len(colors), len(set(colors)))

        style = rend_styles[1]
        style.color = "blue"
        with self.assertTraitChanges(self.model, "contained_plots[]"):
            desc.style_edited = True

        plot_desc = self.model.contained_plots[0]
        renderer = plot_desc.plot.components[1]
        self.assertEqual(renderer.color, "blue")

    def test_change_style_hist_num_bin_2_plot(self):
        """ Edit style button works: style does change and plot gets replaced.
        """
        self.model._add_new_plot(self.config)
        self.model._add_new_plot(self.config2)

        plot_desc1, plot_desc2 = self.model.contained_plots

        style = plot_desc2.plot_config.plot_style
        bar_renderer2 = plot_desc2.plot_factory.renderers[
            DEFAULT_RENDERER_NAME]
        self.assertEqual(bar_renderer2.fill_color, DEFAULT_RENDERER_COLOR)
        self.assertEqual(len(plot_desc2.plot.data.arrays["a"]), 10)
        bar_renderer1 = plot_desc1.plot_factory.renderers[
            DEFAULT_RENDERER_NAME]
        self.assertEqual(bar_renderer1.fill_color, DEFAULT_RENDERER_COLOR)
        self.assertEqual(len(plot_desc1.plot.data.arrays["a"]), 10)

        # Set the renderer color to red:
        style.renderer_styles[0].color = "red"
        style.num_bins = 20
        with self.assertTraitChanges(self.model, "contained_plots[]"):
            plot_desc2.style_edited = True

        self.assertIn(plot_desc1, self.model.contained_plots)
        bar_renderer1 = plot_desc1.plot_factory.renderers[
            DEFAULT_RENDERER_NAME]
        self.assertEqual(bar_renderer1.fill_color,
                         DEFAULT_RENDERER_COLOR)
        self.assertEqual(len(plot_desc1.plot.data.arrays["a"]), 10)

        # The old plot_desc2 has been removed from the contained plots:
        self.assertNotIn(plot_desc2, self.model.contained_plots)
        # and the new one that replaced it has the new properties requested:
        new_plot_desc2 = self.model.contained_plots[1]
        bar_renderer2 = new_plot_desc2.plot_factory.renderers[
            DEFAULT_RENDERER_NAME]
        self.assertEqual(bar_renderer2.fill_color, "red")
        self.assertEqual(len(new_plot_desc2.plot.data.arrays["a"]), 20)

    def test_change_style_doesnt_lose_desc_attrs(self):
        self.model._add_new_plot(self.config)

        plot_desc1 = self.model.contained_plots[0]
        plot_desc1.container_idx = 1
        plot_desc1.plot_title = "New Blah"
        plot_desc1.x_axis_title = "FOOBAR"
        plot_desc1.visible = False

        with self.assertTraitChanges(self.model, "contained_plots[]"):
            plot_desc1.style_edited = True

        # The old plot_desc2 has been removed from the contained plots:
        self.assertNotIn(plot_desc1, self.model.contained_plots)
        # and the new one that replaced it has the new properties requested:
        new_plot_desc1 = self.model.contained_plots[0]

        # But editing the style didn't loose the other descriptor properties:
        check_desc_attrs = ["visible", "id", "plot_title", "x_axis_title",
                            "y_axis_title", "z_axis_title", "container_idx"]
        for attr in check_desc_attrs:
            self.assertEqual(getattr(new_plot_desc1, attr),
                             getattr(plot_desc1, attr))

    def test_change_style_range(self):
        """ Change style range in x and y dim and check all renderers update.
        """
        for config in [self.config, self.config3, self.config4]:
            for dim in ["x", "y"]:
                for end, new_val in zip(["low", "high"], [-2, 6.5]):
                    self.model._add_new_plot(config)
                    self.assert_change_style_range_changes_renderers(
                        config.plot_style, dim, end, new_val
                    )
                    # Clean up for the next loop
                    self.model.contained_plots.pop(0)

    def test_change_style_y_axis_orientation(self):
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        rend_styles = desc.plot_config.plot_style.renderer_styles
        self.assertFalse(hasattr(desc.plot, "second_y_axis"))
        renderer = desc.plot.components[1]
        self.assert_renderer_aligned(renderer, desc.plot.y_axis, dim="value")

        style = rend_styles[1]
        style.orientation = "right"
        desc.style_edited = True
        # Recollect the descriptor since it was replaced:
        desc = self.model.contained_plots[0]
        self.assertTrue(hasattr(desc.plot, "second_y_axis"))
        self.assert_renderer_aligned(renderer, desc.plot.second_y_axis,
                                     dim="value")

    def test_change_style_y_axis_orientation_back(self):
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        rend_styles = desc.plot_config.plot_style.renderer_styles
        self.assertFalse(hasattr(desc.plot, "second_y_axis"))

        style = rend_styles[1]
        style.orientation = "right"
        desc.style_edited = True
        desc = self.model.contained_plots[0]
        self.assertTrue(hasattr(desc.plot, "second_y_axis"))

        style.orientation = "left"
        desc.style_edited = True
        desc = self.model.contained_plots[0]
        renderer = desc.plot.components[1]
        self.assert_renderer_aligned(renderer, desc.plot.y_axis,
                                     dim="value")
        self.assertFalse(hasattr(desc.plot, "second_y_axis"))

    def test_change_plot_title(self):
        """ Plot title updated in the table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        self.assertIn(desc.plot.title, desc.plot.overlays)

        self.assertEqual(desc.plot.title.text, desc.plot_title)
        with self.assertTraitChanges(desc.plot.title, "text"):
            desc.plot_title += "2"

        self.assertEqual(desc.plot.title.text, desc.plot_title)

    def test_change_x_axis_title(self):
        """ X-axis title updated in table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        self.assertIn(desc.plot.x_axis, desc.plot.underlays)

        self.assertEqual(desc.plot.x_axis.title, desc.x_axis_title)
        with self.assertTraitChanges(desc.plot.x_axis, "title"):
            desc.x_axis_title += "2"

        self.assertEqual(desc.plot.x_axis.title, desc.x_axis_title)

    def test_change_y_axis_title(self):
        """ Y-axis title updated in table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        self.assertIn(desc.plot.y_axis, desc.plot.underlays)

        self.assertEqual(desc.plot.y_axis.title, desc.y_axis_title)
        with self.assertTraitChanges(desc.plot.y_axis, "title"):
            desc.y_axis_title += "2"

        self.assertEqual(desc.plot.y_axis.title, desc.y_axis_title)

    def test_change_second_y_axis_title(self):
        """ Y-axis title updated in table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]
        rend_style = desc.plot_config.plot_style.renderer_styles[1]
        rend_style.orientation = STYLE_R_ORIENT
        desc.style_edited = True
        # desc recreated so re-collect it:
        desc = self.model.contained_plots[0]
        plot = desc.plot
        self.assertTrue(hasattr(plot, "second_y_axis"))
        self.assertIn(plot.second_y_axis, plot.underlays)

        self.assertEqual(plot.second_y_axis.title, desc.secondary_y_axis_title)
        with self.assertTraitChanges(plot.second_y_axis, "title"):
            desc.secondary_y_axis_title += "2"

        self.assertEqual(plot.second_y_axis.title, desc.secondary_y_axis_title)

    def test_change_z_axis_title_regular_scatter(self):
        """ Z-axis title updated in table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config4)
        desc = self.model.contained_plots[0]

        self.assertEqual(desc.plot_factory.legend.title, desc.z_axis_title)
        with self.assertTraitChanges(desc.plot_factory.legend, "title"):
            desc.z_axis_title += "2"

        self.assertEqual(desc.plot_factory.legend.title, desc.z_axis_title)

    def test_change_z_axis_title_cmap_scatter(self):
        """ Z-axis title updated in table triggers an update of actual plot.
        """
        self.model._add_new_plot(self.config5)
        desc = self.model.contained_plots[0]

        colorbar = desc.plot.components[1]
        self.assertEqual(colorbar._axis.title, desc.z_axis_title)
        with self.assertTraitChanges(colorbar._axis, "title"):
            desc.z_axis_title += "2"

        self.assertEqual(colorbar._axis.title, desc.z_axis_title)

    # Utility methods ---------------------------------------------------------

    def assert_renderer_aligned(self, renderer, axis, dim="index"):
        axis_range = axis.mapper.range
        if dim == "index":
            rend_range = renderer.index_mapper.range
        else:
            rend_range = renderer.value_mapper.range

        self.assertEqual(rend_range.low, axis_range.low)
        self.assertEqual(rend_range.high, axis_range.high)

    def assert_change_style_range_changes_renderers(self, plot_style, dim, end,
                                                    new_val):
        plot = self.model.contained_plots[0].plot
        range = getattr(plot, dim + "_axis").mapper.range
        plot_val = getattr(range, end)
        style = getattr(plot_style, dim + "_axis_style")
        self.assertEqual(getattr(style, "range_" + end), plot_val)
        self.assertEqual(getattr(style, "auto_range_" + end), plot_val)

        # Change style
        self.assertNotAlmostEqual(plot_val, new_val)
        setattr(style, "range_" + end, new_val)

        # Trigger a regeneration of the plot (normally done by
        # clicking OK in GUI):
        plot_desc1 = self.model.contained_plots[0]
        plot_desc1.style_edited = True

        # The old plot_desc1 has been removed from the contained
        # plots:
        self.assertNotIn(plot_desc1, self.model.contained_plots)
        # so grab the new one:
        plot_desc1 = self.model.contained_plots[0]

        axis = getattr(plot_desc1.plot, dim + "_axis")
        plot_high = getattr(axis.mapper.range, end)
        self.assertAlmostEqual(plot_high, new_val)
        for i, renderer in enumerate(plot_desc1.plot.components):
            if dim == "x":
                mapper = renderer.index_mapper
            else:
                mapper = renderer.value_mapper

            self.assertAlmostEqual(getattr(mapper.range, end), new_val)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerMultiContainerHandling(BasePlotManagerTools, TestCase):

    def test_move_plot_to_new_row(self):
        config = self.config
        desc = self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot)
        self.assert_no_plot_in_container(1)
        # Emulate the user changing the row number from the UI
        desc.container_idx = 1
        self.assert_plot_created(renderer_type=BarPlot, container_idx=1)
        self.assert_no_plot_in_container(0)

    def test_move_plot_to_non_existent_row(self):
        config = self.config
        desc = self.model._add_new_plot(config)
        self.assert_plot_created(container_idx=0, renderer_type=BarPlot)
        self.assert_no_plot_in_container(idx=1)
        # Emulate the user changing the row number from the UI
        desc.container_idx = 100
        # Plot remains in the original location:
        self.assert_plot_created(container_idx=0, renderer_type=BarPlot)
        self.assert_no_plot_in_container(idx=1)

    def test_delete_plot(self):
        config = self.config
        desc = self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot)
        self.assert_no_plot_in_container(1)
        # Emulate the user changing the row number from the UI
        desc.container_idx = "delete"
        # Plot is nowhere:
        for i in range(DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

    def test_add_plot_non_default_row(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot")
        config.x_col_name = "a"
        container1 = self.model.canvas_manager.container_managers[1]
        self.model._add_new_plot(config, container=container1)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=1)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.plot_title, "Plot")
        # Desc is sync-ed
        self.assertEqual(plot_desc.container_idx, 1)

    def test_add_plot_non_default_row_using_int(self):
        config = self.config
        self.model._add_new_plot(config, container=1)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=1)
        # Plot is nowhere else:
        for i in range(DEFAULT_NUM_CONTAINERS):
            if i == 1:
                continue
            self.assert_no_plot_in_container(i)

        self.assert_plot_created(renderer_type=BarPlot, container_idx=1)

    def test_add_plot_default_row_using_int(self):
        config = self.config
        self.model._add_new_plot(config, container=-1)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)
        # Plot is nowhere else:
        for i in range(1, DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.container_idx, 0)

    def test_add_plot_non_existent_row(self):
        config = self.config
        num_containers = len(self.model.canvas_manager.container_managers)
        self.model._add_new_plot(config, container=num_containers + 1)
        # If non-existent container is requested, the last one is used:
        self.assert_plot_created(renderer_type=BarPlot,
                                 container_idx=num_containers - 1)
        # Desc is sync-ed
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.container_idx, num_containers - 1)

    def test_add_3_plots_mode0(self):
        config = self.config
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=2,
                                 container_idx=0)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=3,
                                 container_idx=0)
        # Plot is nowhere else:
        for i in range(1, DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

        # And plot descriptors are synchronized:
        for plot_desc in self.model.contained_plots:
            self.assertEqual(plot_desc.container_idx, 0)

    def test_add_3_plots_mode1(self):
        self.model.canvas_manager.multi_container_mode = 1
        self.model.canvas_manager.overflow_limit = 2

        config = self.config
        # Add 3 plots which should arrive in the first container for the first
        # 2 and the second container for the last plot because it overflow:
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, container_idx=0)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=2,
                                 container_idx=0)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=3,
                                 num_plot_in_container=1, container_idx=1,
                                 single_container=False)
        # Plot is nowhere else:
        for i in range(2, DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)

        # And plot descriptors are synchronized:
        self.assertEqual(self.model.contained_plots[0].container_idx, 0)
        self.assertEqual(self.model.contained_plots[1].container_idx, 0)
        self.assertEqual(self.model.contained_plots[2].container_idx, 1)

    def test_add_3_plots_mode2(self):
        self.model.canvas_manager.multi_container_mode = 2
        config = self.config
        # Add 3 plots which should arrive, each in its own container:
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=2,
                                 num_plot_in_container=1, container_idx=1,
                                 single_container=False)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=3,
                                 num_plot_in_container=1, container_idx=2,
                                 single_container=False)
        # And plot descriptors are synchronized:
        for i in range(3):
            self.assertEqual(self.model.contained_plots[i].container_idx, i)

    def test_add_4_plots_mode2_run_out(self):
        self.model.canvas_manager.num_container_managers = 3
        # New plots arrive on a new row of plots (container):
        self.model.canvas_manager.multi_container_mode = 2

        config = self.config
        # Add 3 plots which should arrive, each in its own container:
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=2,
                                 num_plot_in_container=1, container_idx=1,
                                 single_container=False)
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=3,
                                 num_plot_in_container=1, container_idx=2,
                                 single_container=False)
        # The last plot should run out of space and arrive in the
        # container_idx=2 also:
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot, num_plots=4,
                                 num_plot_in_container=2, container_idx=2,
                                 single_container=False)

        # And plot descriptors are synchronized:
        for i in range(3):
            self.assertEqual(self.model.contained_plots[i].container_idx, i)
        # The last one ran out of space:
        self.assertEqual(self.model.contained_plots[3].container_idx, 2)

    def test_add_delete_plot(self):
        config = self.config
        self.model._add_new_plot(config)
        self.assert_plot_created(renderer_type=BarPlot)
        desc = self.model.contained_plots[0]
        desc.container_idx = CONTAINER_IDX_REMOVAL
        self.assertEqual(self.model.contained_plots, [])
        for i in range(DEFAULT_NUM_CONTAINERS):
            self.assert_no_plot_in_container(i)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerCreateWithPlots(BasePlotManagerTools, TestCase):

    def test_create_with_contained_plot_no_datasource(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config)
        model = DataFramePlotManager(contained_plots=[desc])
        # No plot really reconstructed because no datasource:
        for container in model.canvas_manager.container_managers:
            self.assertEqual(container.plot_map, {})

    def test_create_with_contained_plot(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config)
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)
        container = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container.plot_map), 1)

    def test_create_with_contained_plot_listen_visible_flag(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config)
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)

        # Reconnect because the description object is (currently) replaced:
        desc = model.contained_plots[0]
        # Plot in plot container:
        container_manager = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container_manager.plot_map), 1)

        # PlotManager is listening to visible flag on descriptor --------------

        self.assertTrue(desc.visible)
        self.assertEqual(len(container_manager.container.components), 1)
        self.assertIs(container_manager.container.components[0], desc.plot)

        desc.visible = False
        self.assertEqual(container_manager.container.components, [])

        desc.visible = True
        self.assertEqual(len(container_manager.container.components), 1)
        self.assertIs(container_manager.container.components[0], desc.plot)

    def test_create_with_broken_contained_plot(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "DOESNT_EXIST"
        desc = PlotDescriptor(x_col_name="DOESNT_EXIST", plot_config=config)
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)
        # Make sure it fails gracefully:
        container_manager = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container_manager.plot_map), 0)
        self.assertEqual(len(model.contained_plots), 0)
        self.assertEqual(len(model.failed_plots), 1)

    def test_create_with_some_broken_contained_plot(self):
        # Add 2 valid plots interlaced with 1 broken one to make sure the
        # correct plot is removed:
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config)

        config2 = HistogramPlotConfigurator(data_source=TEST_DF)
        config2.x_col_name = "DOESNT_EXIST"
        desc2 = PlotDescriptor(x_col_name="DOESNT_EXIST", plot_config=config2)

        config3 = HistogramPlotConfigurator(data_source=TEST_DF,
                                            plot_title="Plot 1")
        config3.x_col_name = "b"
        desc3 = PlotDescriptor(x_col_name="b", plot_config=config3)

        model = DataFramePlotManager(contained_plots=[desc, desc2, desc3],
                                     data_source=TEST_DF)
        # Make sure the one that fails does so gracefully:
        container_manager = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container_manager.plot_map), 2)
        self.assertEqual(len(model.contained_plots), 2)
        self.assertEqual(len(model.failed_plots), 1)

        present_hist = [x.x_col_name for x in model.contained_plots]
        self.assertEqual(present_hist, ["a", "b"])

    def test_create_with_contained_plot_special_titles(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config,
                              plot_title="blah", x_axis_title="foobar")
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)

        # Reconnect because the description object is (currently) replaced:
        desc = model.contained_plots[0]
        self.assertEqual(desc.plot_title, "blah")
        self.assertEqual(desc.x_axis_title, "foobar")

    def test_create_with_frozen_contained_plot(self):
        reduced_df = TEST_DF.iloc[:2, :]
        config = HistogramPlotConfigurator(data_source=reduced_df,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config,
                              plot_title="blah", x_axis_title="foobar",
                              frozen=True)
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)

        # Reconnect because the description object is (currently) replaced:
        desc = model.contained_plots[0]
        self.assertIs(desc.plot_config.data_source, reduced_df)

    def test_create_with_2_contained_plots(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config)

        config2 = HistogramPlotConfigurator(data_source=TEST_DF,
                                            plot_title="Plot 2")
        config2.x_col_name = "b"
        desc2 = PlotDescriptor(x_col_name="b", plot_config=config2,
                               visible=False)
        model = DataFramePlotManager(contained_plots=[desc, desc2],
                                     data_source=TEST_DF)

        # Reconnect because the description object is (currently) replaced:
        desc = model.contained_plots[0]
        desc2 = model.contained_plots[1]
        self.assertTrue(desc.visible)
        self.assertFalse(desc2.visible)

        # Plot in plot container:
        container_manager = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container_manager.plot_map), 2)

        # PlotManager is listening to visible flag on descriptor:
        self.assertTrue(desc.visible)
        self.assertFalse(desc2.visible)
        self.assertEqual(len(container_manager.container.components), 1)
        self.assertIs(container_manager.container.components[0], desc.plot)

        desc2.visible = True
        self.assertEqual(container_manager.container.components,
                         [desc.plot, desc2.plot])

        desc.visible = False
        self.assertEqual(len(container_manager.container.components), 1)
        self.assertIs(container_manager.container.components[0], desc2.plot)

    def test_add_plot_to_non_default_row(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF,
                                           plot_title="Plot 1")
        config.x_col_name = "a"
        desc = PlotDescriptor(x_col_name="a", plot_config=config,
                              container_idx=1)
        model = DataFramePlotManager(contained_plots=[desc],
                                     data_source=TEST_DF)
        container = model.canvas_manager.container_managers[0]
        self.assertEqual(len(container.plot_map), 0)

        container1 = model.canvas_manager.container_managers[1]
        self.assertEqual(len(container1.plot_map), 1)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerFromDFAnalyzer(TestCase, UnittestTools):
    def setUp(self):
        self.source_analyzer = DataFrameAnalyzer(source_df=TEST_DF)
        self.source_analyzer.filter_exp = ""
        self.model = DataFramePlotManager(source_analyzer=self.source_analyzer)

    def test_create_manager(self):
        self.assertIsInstance(self.model, DataFramePlotManager)
        self.assertEqual(len(self.model.canvas_manager.container_managers),
                         DEFAULT_NUM_CONTAINERS)
        for container_manager in self.model.canvas_manager.container_managers:
            self.assertIsInstance(container_manager,
                                  ConstraintsPlotContainerManager)
            self.assertIsNotNone(container_manager.container)

        self.assertEqual(self.model.contained_plots, [])
        self.assertIs(self.model.source_analyzer, self.source_analyzer)

    def test_update_source_analyzer(self):
        config = ScatterPlotConfigurator(data_source=TEST_DF,
                                         plot_title="Plot")
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        self.assertEqual(plot_desc.plot_title, "Plot")

        with self.assertTraitChanges(self.model, "data_source"):
            with self.assertTraitChanges(plot_desc, "data_filter"):
                self.source_analyzer.filter_exp = "a > 1"

        self.assertEqual(plot_desc.data_filter, "a > 1")
        self.assertIs(self.model.source_analyzer, self.source_analyzer)
        assert_frame_equal(self.model.data_source, TEST_DF.query("a > 1"))

    def test_update_source_analyzer_frozen(self):
        config = ScatterPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)
        plot_desc = self.model.contained_plots[0]
        self.assertEqual(plot_desc.x_col_name, "a")
        self.assertEqual(plot_desc.y_col_name, "b")
        plot_desc.frozen = True

        config = ScatterPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)

        plot_desc2 = self.model.contained_plots[1]
        self.assertEqual(plot_desc2.x_col_name, "a")
        self.assertEqual(plot_desc2.y_col_name, "b")

        with self.assertTraitChanges(self.model, "data_source"):
            with self.assertTraitDoesNotChange(plot_desc, "data_filter"):
                with self.assertTraitChanges(plot_desc2, "data_filter"):
                    self.source_analyzer.filter_exp = "a > 1"

        self.assertEqual(plot_desc.data_filter, "")
        self.assertEqual(plot_desc2.data_filter, "a > 1")
        self.assertIs(self.model.source_analyzer, self.source_analyzer)
        assert_frame_equal(self.model.data_source, TEST_DF.query("a > 1"))


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerDataUpdate(TestCase, UnittestTools):
    def setUp(self):
        self.model = DataFramePlotManager(data_source=TEST_DF)

    def test_update_hist_on_data_update(self):
        config = MultiHistogramPlotConfigurator(data_source=TEST_DF,
                                                plot_title="Plot {i}")
        config.x_col_names = ["a", "b"]
        self.model._add_new_plots(config)
        self.assert_plot_created(2)

        data0 = self.model.contained_plots[0].plot.data
        data1 = self.model.contained_plots[1].plot.data

        new_df = self.model.data_source.query("a > 2")
        with self.assertTraitChanges(data0, "data_changed", 1):
            with self.assertTraitChanges(data1, "data_changed", 1):
                self.model.data_source = new_df

        # Make sure the histograms only contain half of the values
        self.assertEqual(data0[HISTOGRAM_Y_LABEL].sum(), len(TEST_DF) // 2)
        self.assertEqual(data1[HISTOGRAM_Y_LABEL].sum(), len(TEST_DF) // 2)

    def test_update_line_on_data_update(self):

        config = LinePlotConfigurator(data_source=TEST_DF,
                                      plot_title="Plot")
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)

        self.assert_plot_created()
        self.assert_renderer_data_is_from_df(TEST_DF)

        plot = self.model.contained_plots[0].plot
        new_df = self.model.data_source.query("a > 2")
        self.model.data_source = new_df

        # Make sure the plot still contains 1 renderer...
        self.assertEqual(len(plot.components), 1)
        # ... using the reduced data:
        self.assert_renderer_data_is_from_df(new_df)

    def test_update_scatter_on_data_update(self):

        config = ScatterPlotConfigurator(data_source=TEST_DF,
                                         plot_title="Plot")
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.model._add_new_plot(config)

        self.assert_plot_created()
        self.assert_renderer_data_is_from_df(TEST_DF)

        plot = self.model.contained_plots[0].plot
        new_df = self.model.data_source.query("a > 2")
        self.model.data_source = new_df

        # Make sure the plot still contains 1 renderer...
        self.assertEqual(len(plot.components), 1)
        # ... using the reduced data:
        self.assert_renderer_data_is_from_df(new_df)

    def test_remove_data_on_colored_scatter(self):
        """ Test data/renderer updates when removing new data to data source
        """
        config = ScatterPlotConfigurator(data_source=TEST_DF, x_col_name="a",
                                         y_col_name="b", z_col_name="d")
        self.model._add_new_plot(config)

        self.assert_plot_created()
        plot = self.model.contained_plots[0].plot

        self.assert_renderer_data_consistent(plot, TEST_DF)

        new_df = self.model.data_source.query("a > 2")
        # Make sure that changing the source DF changes the data for all plots:
        self.model.data_source = new_df

        self.assert_renderer_data_consistent(plot, new_df)

    def test_add_data_on_colored_scatter(self):
        """ Test data/renderer updates when adding new data to data source
        """
        reduced_df = TEST_DF.query("a > 2")
        model = DataFramePlotManager(data_source=reduced_df)
        config = ScatterPlotConfigurator(data_source=reduced_df,
                                         x_col_name="a", y_col_name="b",
                                         z_col_name="d")
        model._add_new_plot(config)

        plot = model.contained_plots[0].plot

        self.assert_renderer_data_consistent(plot, reduced_df)

        # Make sure that changing the source DF changes the data for all plots:
        model.data_source = TEST_DF

        self.assert_renderer_data_consistent(plot, TEST_DF)

    # Helper utilities --------------------------------------------------------

    def assert_renderer_data_consistent(self, plot, df, coloring_col="d"):
        grp = df.groupby(by="d")
        renderers = plot.components
        for i, color in enumerate(sorted(set(df[coloring_col]))):
            subdf = grp.get_group(color)
            self.assert_renderer_data_is_from_df(subdf,
                                                 renderer=renderers[i])

        self.assertEqual(len(plot.components), len(set(df[coloring_col])))
        for overlay in plot.overlays:
            if isinstance(overlay, Legend):
                self.assertEqual(set(overlay.plots.keys()),
                                 set(df[coloring_col]))
                break

    def assert_renderer_data_is_from_df(self, df, renderer=None, index_key="a",
                                        value_key="b"):
        if renderer is None:
            renderer = self.model.contained_plots[0].plot.components[0]

        assert_array_equal(renderer.index._data, df[index_key].values)
        assert_array_equal(renderer.value._data, df[value_key].values)

    def assert_plot_created(self, num_plots=1):
        self.assertEqual(len(self.model.contained_plots), num_plots)
        for i in range(num_plots):
            plot_desc = self.model.contained_plots[0]
            self.assertIsInstance(plot_desc, PlotDescriptor)
            self.assertIsInstance(plot_desc.id, str)
            self.assertIsInstance(plot_desc.plot, BasePlotContainer)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotManagerInspectorTools(TestCase, UnittestTools):
    def setUp(self):
        self.model = DataFramePlotManager(data_source=TEST_DF)
        config = ScatterPlotConfigurator(data_source=TEST_DF,
                                         plot_title="Plot")
        config.x_col_name = "a"
        config.y_col_name = "b"
        self.config = config

    def test_empty(self):
        self.assertEqual(len(self.model.inspectors), 0)
        self.assertEqual(self.model.index_selected, [])

    def test_store_inspectors(self):
        self.model._add_new_plot(self.config)
        self.assertEqual(len(self.model.inspectors), 1)

        self.config.y_col_name = "a"
        self.model._add_new_plot(self.config)
        self.assertEqual(len(self.model.inspectors), 2)
        self.assertEqual(set(self.model.inspectors), {"0", "1"})

    def test_inspectors_connected(self):
        self.model._add_new_plot(self.config)
        self.config.y_col_name = "a"
        self.model._add_new_plot(self.config)
        tool0 = self.model.inspectors["0"][0]
        tool1 = self.model.inspectors["1"][0]
        self.assertEqual(self.model.index_selected, [])

        tool0._select(3)
        self.assertEqual(self.model.index_selected, [3])
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, [3])
        selection1 = tool1.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection1, [3])

        tool1._select(0)
        self.assertEqual(self.model.index_selected, [3, 0])
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, [3, 0])
        selection1 = tool1.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection1, [3, 0])

        tool1._deselect(3)
        self.assertEqual(self.model.index_selected, [0])
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, [0])
        selection1 = tool1.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection1, [0])

    def test_inspectors_not_connected_if_frozen(self):
        self.model._add_new_plot(self.config)
        self.config.y_col_name = "a"
        self.model._add_new_plot(self.config)
        tool0, overlay0 = self.model.inspectors["0"]
        tool1, overlay1 = self.model.inspectors["1"]
        self.assertEqual(self.model.index_selected, [])

        tool0._select(3)
        first_selection = [3]
        self.assertEqual(self.model.index_selected, first_selection)
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, first_selection)
        selection1 = tool1.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection1, first_selection)

        # Disconnect the first plot:
        with self.assertTraitChanges(overlay0, "selection_color", 1):
            self.model.contained_plots[0].frozen = True

        second_selection = [2]
        self.model.index_selected = second_selection
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, first_selection)
        selection1 = tool1.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection1, second_selection)

        self.assertEqual(overlay0.selection_color,
                         DISCONNECTED_SELECTION_COLOR)
        self.assertEqual(overlay1.selection_color, SELECTION_COLOR)

        # Reconnect the first plot:
        with self.assertTraitChanges(overlay0, "selection_color", 1):
            self.model.contained_plots[0].frozen = False

        self.assertEqual(overlay0.selection_color, SELECTION_COLOR)
        selection0 = tool0.component.index.metadata[SELECTION_METADATA_NAME]
        self.assertEqual(selection0, second_selection)


@provides(IPlotTemplateInteractor)
class FakeInteractor(HasTraits):
    def get_template_saver(self):
        return self.saver

    def get_template_loader(self):
        return lambda filepath: filepath

    def get_template_ext(self):
        return ".tmpl"

    def get_template_dir(self):
        return HERE

    def saver(self, filepath, object_to_save):
        with open(filepath, 'w'):
            pass


class TestPlotManagerPlotTemplates(TestCase):

    def setUp(self) -> None:
        self.model = DataFramePlotManager(data_source=TEST_DF)
        self.target_dir = HERE
        self.model.template_interactor = FakeInteractor()

    @patch.object(DataFramePlotManager, '_get_desc_for_menu_manager')
    @patch.object(DataFramePlotManager, '_request_template_name_with_desc')
    def test_template_requested(self, get_name, get_desc):
        plot_config = BarPlotConfigurator()
        get_desc.return_value = PlotDescriptor(plot_config=plot_config)
        get_name.return_value = "plot template test"
        self.assertEqual(len(self.model.custom_configs), 0)

        self.model.action_template_requested(None, None, None)

        self.assertEqual(len(self.model.custom_configs), 1)
        ext = self.model.template_interactor.get_template_ext()
        file = os.path.join(self.target_dir, get_name.return_value + ext)
        if os.path.exists(file):
            os.remove(file)
