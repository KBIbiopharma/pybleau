from unittest import TestCase
from unittest.mock import Mock

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.manage_templates_accessor import ManageTemplatesAccessor


class TestManageTemplatesAccessor(TestCase):

    def setUp(self) -> None:
        self.accessor = ManageTemplatesAccessor(
            model=Mock(PlotTemplateManager))

    def test_templates_exist_returns_correct(self):
        self.accessor.model.names = list('abc')
        self.assertTrue(self.accessor.templates_exist)
        self.accessor.model.names = []
        self.assertFalse(self.accessor.templates_exist)
