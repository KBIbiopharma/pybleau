from unittest import TestCase
from unittest.mock import MagicMock

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.manage_templates_accessor import ManageTemplatesAccessor


class TestManageTemplatesAccessor(TestCase):

    def setUp(self) -> None:
        model = MagicMock(PlotTemplateManager)
        model.names = MagicMock(list)
        self.accessor = ManageTemplatesAccessor(model=model)

    def test_templates_exist_returns_correct(self):
        self.accessor.model.names = list('abc')
        self.assertTrue(self.accessor.templates_exist)
        self.accessor.model.names = []
        self.assertFalse(self.accessor.templates_exist)

    def test_reconcile_plot_types_list(self):
        current_list = list('abc')
        self.accessor.plot_types = current_list

        # test none removed, some added
        old_list = None
        new_list = list('de')
        self.accessor._reconcile_plot_types_list(old_list, new_list)
        self.assertCountEqual(self.accessor.plot_types, list('abcde'))

        # test some removed, none added
        self.accessor.plot_types = current_list
        self.accessor._reconcile_plot_types_list(current_list, list('ab'))
        self.assertCountEqual(self.accessor.plot_types, list('ab'))

        # test some removed, some added
        self.accessor.plot_types = current_list
        self.accessor._reconcile_plot_types_list(current_list, list('ad'))
        self.assertCountEqual(self.accessor.plot_types, list('ad'))
