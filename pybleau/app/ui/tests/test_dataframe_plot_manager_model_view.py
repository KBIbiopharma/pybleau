from os.path import dirname
from unittest import TestCase, skipIf

from pandas.testing import assert_frame_equal
from pandas import DataFrame
import os

from traits.has_traits import HasTraits, provides

from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor
from pybleau.app.plotting.plot_config import ScatterPlotConfigurator

try:
    import kiwisolver  # noqa

    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if KIWI_AVAILABLE and BACKEND_AVAILABLE:
    from app_common.apptools.testing_utils import assert_obj_gui_works
    from pybleau.app.api import DataFrameAnalyzer, DataFramePlotManager
    from pybleau.app.ui.dataframe_plot_manager_view import \
        DataFramePlotManagerView, PlotTypeSelector
    from pybleau.app.model.multi_canvas_manager import MultiCanvasManager

msg = "No UI backend to paint into or missing kiwisolver package"


@provides(IPlotTemplateInteractor)
class FakeInteractor(HasTraits):
    def get_template_saver(self):
        return self.saver

    def get_template_loader(self):
        return lambda filepath: ScatterPlotConfigurator()

    def get_template_ext(self):
        return ".tmpl"

    def get_template_dir(self):
        return dirname(__file__)

    def saver(self, filepath, object_to_save):
        with open(filepath, 'w'):
            pass


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDataFramePlotManagerView(TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]})
        self.analyzer = DataFrameAnalyzer(source_df=self.df)
        self.plotter = DataFramePlotManager(source_analyzer=self.analyzer)

    def test_bring_up_plot_manager_view(self):
        view = DataFramePlotManagerView(model=self.plotter)
        assert_obj_gui_works(view)

    def test_bring_up_plot_manager_view_non_default_num_containers(self):
        model = DataFramePlotManager(
            source_analyzer=self.analyzer,
            canvas_manager=MultiCanvasManager(num_container_managers=5)
        )
        view = DataFramePlotManagerView(model=model)
        assert_obj_gui_works(view)

    def test_bring_up_custom_columns(self):
        view = DataFramePlotManagerView(model=self.plotter,
                                        plot_control_cols=["x_col_name"])
        assert_obj_gui_works(view)

    def test_create_configurator_from_file(self):
        view = DataFramePlotManagerView(model=self.plotter)
        plot_type = 'template plot'
        with self.assertRaises(AttributeError):
            view.create_config_for_custom_type(plot_type)
        self.plotter.template_interactor = FakeInteractor()
        config = view.create_config_for_custom_type(plot_type)
        self.assertIsInstance(config, ScatterPlotConfigurator)
        self.assertEqual(config.source_template, plot_type)
        assert_frame_equal(config.data_source, self.plotter.data_source)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotTypePopup(TestCase):

    def test_bring_up_plot_type_popup(self):
        selector = PlotTypeSelector()
        assert_obj_gui_works(selector)
