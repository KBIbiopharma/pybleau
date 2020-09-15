from unittest import TestCase
from unittest.mock import MagicMock

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.plot_template_manager_view import PlotTemplateManagerView


class TestPlotTemplateManagerView(TestCase):

    def setUp(self) -> None:
        model = MagicMock(PlotTemplateManager)
        model.delete_templates = MagicMock()
        model.rescan_template_dir = MagicMock()
        self.view = PlotTemplateManagerView(model=model)
        self.view.interactive = False

    def test_delete_templates_calls_delete_templates(self):
        selected = list('ac')
        self.view.selected_plot_templates = selected
        self.view.delete_from_templates = True
        self.view.model.delete_templates.assert_called_with(selected)
        self.assertEqual(self.view.selected_plot_templates, [])

    def test_rescan_calls_rescan_template_dir(self):
        self.view.rescan_for_templates = True
        self.view.model.rescan_template_dir.assert_called_with()
