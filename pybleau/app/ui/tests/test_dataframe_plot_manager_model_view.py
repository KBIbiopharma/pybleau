from unittest import TestCase, skipIf
from pandas import DataFrame
import os

try:
    import kiwisolver  # noqa
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if KIWI_AVAILABLE and BACKEND_AVAILABLE:
    from app_common.apptools.testing_utils import temp_bringup_ui_for
    from pybleau.app.api import DataFrameAnalyzer, DataFramePlotManager
    from pybleau.app.ui.dataframe_plot_manager_view import \
        DataFramePlotManagerView, PlotTypeSelector
    from pybleau.app.model.multi_canvas_manager import MultiCanvasManager


msg = "No UI backend to paint into or missing kiwisolver package"


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDataFramePlotManagerView(TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]})
        self.analyzer = DataFrameAnalyzer(source_df=self.df)
        self.plotter = DataFramePlotManager(source_analyzer=self.analyzer)

    def test_bring_up_plot_manager_view(self):
        view = DataFramePlotManagerView(model=self.plotter)
        with temp_bringup_ui_for(view):
            pass

    def test_bring_up_plot_manager_view_non_default_num_containers(self):
        model = DataFramePlotManager(
            source_analyzer=self.analyzer,
            canvas_manager=MultiCanvasManager(num_container_managers=5)
        )
        view = DataFramePlotManagerView(model=model)
        with temp_bringup_ui_for(view):
            pass


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestPlotTypePopup(TestCase):

    def test_bring_up_plot_type_popup(self):
        selector = PlotTypeSelector()
        with temp_bringup_ui_for(selector):
            pass
