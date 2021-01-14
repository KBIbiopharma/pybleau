from chaco.api import OverlayPlotContainer
from unittest import TestCase

from pybleau.app.plotting.multi_mapper_plot import MultiMapperPlot
from pybleau.app.plotting.plot_container_style import PlotContainerStyle


class TestMultiMapperPlot(TestCase):
    def test_create(self):
        plot = MultiMapperPlot()
        self.assertIsInstance(plot, OverlayPlotContainer)

    def test_create_control_padding(self):
        plot = MultiMapperPlot(left_padding=10)
        self.assertIsInstance(plot, OverlayPlotContainer)

    def test_create_control_attr_via_container_style(self):
        attrs = PlotContainerStyle().to_traits()
        plot = MultiMapperPlot(**attrs)
        self.assertIsInstance(plot, OverlayPlotContainer)
