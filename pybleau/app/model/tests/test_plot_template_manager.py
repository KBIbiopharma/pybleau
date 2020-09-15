import os
from os.path import dirname
from unittest import TestCase

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

    def test_delete_template_calls_interactor_delete(self):
        self.assertEqual(len(self.manager.names), 2)
        with self.assertTraitChanges(self.manager, "templates_changed"):
            self.manager.delete_templates([self.template_names[0]])

    def test_rescan_template_dir_raises_event(self):
        with self.assertTraitChanges(self.manager, "templates_changed"):
            self.manager.rescan_template_dir()

    def test_get_names_returns_list(self):
        names = ["temp1", "temp2"]
        self.assertListEqual(names, self.manager.names)
