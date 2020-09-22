import os
from os.path import dirname
from unittest import TestCase
from unittest.mock import patch

from traits.api import Callable
from traits.has_traits import provides, HasStrictTraits
from traits.testing.unittest_tools import UnittestTools

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor

HERE = dirname(__file__)


@provides(IPlotTemplateInteractor)
class FakePlotTemplateInteractor(HasStrictTraits):
    def get_template_saver(self) -> Callable:
        return lambda x: x

    def get_template_loader(self) -> Callable:
        return lambda x, y: x

    def get_template_ext(self) -> str:
        return ".tmpl"

    def get_template_dir(self) -> str:
        return HERE

    def delete_templates(self, temps) -> bool:
        return True


class TestPlotTemplateManager(TestCase, UnittestTools):

    def setUp(self) -> None:
        self.interactor = FakePlotTemplateInteractor()
        self.manager = PlotTemplateManager(interactor=self.interactor)

        self.template_paths = []
        self.template_names = []
        self.template_ext = ".tmpl"
        self.template_names.append("temp1")
        self.template_names.append("temp2")

        for name in self.template_names:
            path = os.path.join(HERE, name + self.template_ext)
            self.template_paths.append(path)
            with open(path, "w"):
                pass

    def tearDown(self) -> None:
        for file in self.template_paths:
            if os.path.isfile(file):
                os.remove(file)

    @patch.object(FakePlotTemplateInteractor, "delete_templates")
    def test_delete_template_calls_interactor_delete(self, delete):
        self.assertEqual(len(self.manager.names), 2)
        self.manager.delete_templates(self.template_names[0])
        delete.assert_called_with(self.template_names[0])

    def test_rescan_template_dir_raises_event(self):
        self.assertCountEqual(self.manager.names, self.template_names)
        self.assertEqual(len(self.manager.names), 2)

        self.template_names.append("new_template")
        path = os.path.join(HERE, "new_template" + self.template_ext)
        self.template_paths.append(path)
        with open(path, "w"):
            pass
        with self.assertTraitChanges(self.manager, "names"):
            self.manager.rescan_template_dir()

        self.assertCountEqual(self.manager.names, self.template_names)
        self.assertEqual(len(self.manager.names), 3)

    def test_get_names_returns_list(self):
        self.assertCountEqual(["temp1", "temp2"], self.manager.names)
        os.remove(self.template_paths[0])
        self.manager.rescan_template_dir()
        self.assertCountEqual(["temp2"], self.manager.names)
        os.remove(self.template_paths[1])
        self.manager.rescan_template_dir()
        self.assertCountEqual([], self.manager.names)

    def test_get_names_returns_empty_without_interactor(self):
        names = ["temp1", "temp2"]
        self.assertCountEqual(names, self.manager.names)
        self.manager.interactor = None
        names = self.manager._get_names_from_directory()
        self.assertCountEqual(names, [])
