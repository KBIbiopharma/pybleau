from unittest import TestCase
from functools import partial
import pandas as pd
import numpy as np
import plotly.graph_objs as go

from pybleau.plotly_api.api import BLUE, GREEN, plotly_bar, RED
from pybleau.plotly_api.testing_utils import BaseFigureArguments


DATA = pd.DataFrame({"a": list("abcdcb"), "b": np.arange(6),
                     "c": np.arange(0, 60, 10), "d": np.arange(0, 60, 10),
                     "e": np.array([0, 1]*3, dtype="bool")},
                    index=list("xyzwvu"))

# Simplify all calls to plotly_scatter to return a figure
plotly_bar = partial(plotly_bar, target="fig")


class TestPlotlyBar(TestCase, BaseFigureArguments):
    def setUp(self):
        self.data = DATA
        self.plot_func = plotly_bar
        self.default_args = {"x": "c", "y": "b"}
        self.renderer_type = go.Bar

    def test_missing_data(self):
        with self.assertRaises(ValueError):
            plotly_bar()

    def test_bar_all_columns(self):
        # If you don't specify what to plot along y, all columns are plotted:
        data2 = DATA[list("bcd")]
        fig = plotly_bar(data=data2)
        self.assert_valid_plotly_figure(fig, num_renderers=3)

    def test_bar_against_index(self):
        fig = plotly_bar(y="b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

        fig = plotly_bar(x="index", y="b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

        fig = plotly_bar(x=DATA.index.name, y="b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_bar_against_str_col(self):
        fig = plotly_bar(x="a", y="b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_bar_against_float_col(self):
        fig = plotly_bar(x="c", y="b", data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_bar_list(self):
        fig = plotly_bar(y=["b", "c"], data=self.data)
        self.assert_valid_plotly_figure(fig, num_renderers=2)

    def test_stacked_bar_list(self):
        fig = plotly_bar(y=["b", "c"], data=self.data, barmode="stack")
        self.assert_valid_plotly_figure(fig, num_renderers=2)

        fig = plotly_bar(x="a", y=["b", "c"], data=self.data, barmode="stack")
        self.assert_valid_plotly_figure(fig, num_renderers=2)

    def test_bar_pick_color(self):
        fig = plotly_bar(y="b", data=self.data, hue="rgb(122, 120, 120)")
        self.assert_valid_plotly_figure(fig, num_renderers=1)
        fig = plotly_bar(y="b", data=self.data, hue=RED)
        self.assert_valid_plotly_figure(fig, num_renderers=1)

    def test_bar_list_pick_color(self):
        fig = plotly_bar(y=["b", "c", "d"], data=self.data,
                         hue=[BLUE, GREEN, RED])
        self.assert_valid_plotly_figure(fig, num_renderers=3)

    def test_bar_list_pick_color_as_palette(self):
        # Same as above but the list of colors is passed as the palette
        fig = plotly_bar(y=["b", "c", "d"], data=self.data,
                         palette=[BLUE, GREEN, RED])
        self.assert_valid_plotly_figure(fig, num_renderers=3)

    def test_bar_list_pick_color_palette(self):
        fig = plotly_bar(y=["b", "c", "d"], data=self.data,
                         palette="RdBu")
        self.assert_valid_plotly_figure(fig, num_renderers=3)

        with self.assertRaises(ValueError):
            plotly_bar(y=["b", "c", "d"], data=self.data,
                       palette="NON-EXISTENT")

    def test_bar_list_pick_color_bad_length(self):
        with self.assertRaises(ValueError):
            plotly_bar(y=["b", "c", "d"], data=self.data, hue=[BLUE, GREEN])

    def test_bar_plot_silly_x_scale(self):
        # In the case of bar plots, x_scale is overwritten if the x_axis is
        # made of strings, so this doesn't break:
        fig = plotly_bar(y=["b"], data=self.data, x_scale="BLAH BLAH")
        self.assert_valid_plotly_figure(fig)
