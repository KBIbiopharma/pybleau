from unittest import TestCase
import pandas as pd
import numpy as np
from functools import partial
import plotly.graph_objs as go

from pybleau.plotly_api.api import BLUE, GREEN, plotly_hist, RED
from pybleau.plotly_api.testing_utils import BaseFigureArguments

DATA = pd.DataFrame({"a": list("abcdcb"), "b": np.arange(6),
                     "c": np.arange(0, 60, 10), "d": np.arange(0, 60, 10),
                     "e": np.array([0, 1]*3, dtype="bool")},
                    index=list("xyzwvu"))

# Simplify all calls to plotly_scatter to return a figure
plotly_hist = partial(plotly_hist, target="fig")


class TestPlotlyHist(TestCase, BaseFigureArguments):
    def setUp(self):
        self.data = DATA
        self.plot_func = plotly_hist
        self.default_args = {"x": "b"}
        self.renderer_type = go.Histogram

    def test_missing_data(self):
        with self.assertRaises(ValueError):
            plotly_hist("b")

    def test_hist(self):
        fig = plotly_hist("b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_hist_list(self):
        fig = plotly_hist(["b", "c"], data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=2)

    def test_hist_pick_color(self):
        fig = plotly_hist("b", data=self.data, hue="rgb(122, 120, 120)")
        self.assert_valid_plotly_figure(fig, num_renderers=1)
        fig = plotly_hist("b", data=self.data, hue=RED)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_hist_list_pick_color(self):
        fig = plotly_hist(["b", "c", "d"], data=self.data,
                          hue=[BLUE, GREEN, RED])
        self.assert_valid_plotly_figure(fig, num_renderers=3)
