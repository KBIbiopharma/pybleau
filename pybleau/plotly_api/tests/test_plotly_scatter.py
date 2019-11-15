from unittest import TestCase
import pandas as pd
import numpy as np
from functools import partial
import plotly.graph_objs as go

from pybleau.plotly_api.api import BLACK, BLUE, GREEN, plotly_scatter, RED
from pybleau.plotly_api.testing_utils import BaseFigureArguments

DATA = pd.DataFrame({"a": list("abcdcb"), "b": np.arange(6),
                     "c": np.arange(0, 60, 10), "d": np.arange(0, 60, 10),
                     "e": np.array([0, 1]*3, dtype="bool")},
                    index=list("xyzwvu"))

NUM_A_VALUES = len(set(DATA["a"]))

# Simplify all calls to plotly_scatter to return a figure
plotly_scatter = partial(plotly_scatter, target="fig")


class TestPlotlyScatter(TestCase, BaseFigureArguments):
    def setUp(self):
        self.data = DATA
        self.plot_func = plotly_scatter
        self.default_args = {"x": "c", "y": "b"}
        self.renderer_type = go.Scatter

    def test_missing_data(self):
        with self.assertRaises(ValueError):
            plotly_scatter("b", "c")

    def test_x_y(self):
        fig = plotly_scatter("b", "c", data=self.data)
        self.assert_valid_plotly_figure(fig)

    def test_x_y_pick_color(self):
        fig = plotly_scatter("b", "c", data=self.data, hue="rgb(255, 0, 0)")
        self.assert_valid_plotly_figure(fig)

    def test_x_y_pick_symbol(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="square")
        self.assert_valid_plotly_figure(fig)

    def test_x_y_pick_color_and_symbol(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="square",
                             hue="rgb(255, 0, 0)")
        self.assert_valid_plotly_figure(fig)

    def test_x_y_hue(self):
        fig = plotly_scatter("b", "c", data=self.data, hue="a")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_hue_and_hue_map(self):
        color_map = {"a": BLACK, "b": BLUE, "c": RED, "d": GREEN}
        fig = plotly_scatter("b", "c", data=self.data, hue="a",
                             palette=color_map)
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_2_prop_hue(self):
        self.skipTest("Not supported yet")
        fig = plotly_scatter("b", "c", data=self.data, hue=["a", "index"])
        self.assert_valid_plotly_figure(fig)

    def test_x_y_hover(self):
        fig = plotly_scatter("b", "c", data=self.data, hover="a")
        self.assert_valid_plotly_figure(fig)

    def test_x_y_symbol(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="a")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_symbol_int_col(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="c")
        self.assert_valid_plotly_figure(fig, num_renderers=6)

    def test_x_y_symbol_pick_hue(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="a",
                             hue="rgb(255, 0, 0)")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_symbol_index_on_hover(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="a",
                             hover="index")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_symbol_col_on_hover(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="a", hover="a")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_x_y_symbol_hue_hover(self):
        fig = plotly_scatter("b", "c", data=self.data, symbol="a", hue="index",
                             hover="index")
        num_a_index_pairs = 6
        self.assert_valid_plotly_figure(fig, num_renderers=num_a_index_pairs)


class TestPlotlyScatter3D(TestCase, BaseFigureArguments):
    def setUp(self):
        self.data = DATA
        self.plot_func = plotly_scatter
        self.default_args = {"x": "c", "y": "b", "z": "d"}
        self.renderer_type = go.Scatter3d

    def test_create_x_y_z(self):
        fig = plotly_scatter(x="b", y="c", z="d", data=self.data)
        self.assert_valid_plotly_figure(fig)

    def test_create_x_y_z_hue(self):
        fig = plotly_scatter(x="b", y="c", z="d", data=self.data, hue="a")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_create_x_y_z_hue_hover(self):
        fig = plotly_scatter(x="b", y="c", z="d", data=self.data, hue="a",
                             hover="index")
        self.assert_valid_plotly_figure(fig, num_renderers=NUM_A_VALUES)

    def test_create_x_y_z_hue_hover_symbol(self):
        self.skipTest("Not supported yet")
        fig = plotly_scatter(x="b", y="c", z="d", data=self.data, hue="a",
                             hover="index", symbol="a")
        self.assert_valid_plotly_figure(fig)

    def test_create_x_y_z_hue_hover_symbol_on_bool_col(self):
        self.skipTest("Not supported yet")
        fig = plotly_scatter(x="b", y="c", z="d", data=self.data, hue="a",
                             hover="index", symbol="e")
        self.assert_valid_plotly_figure(fig)
