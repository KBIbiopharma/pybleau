""" Make sure Multi-plot configurators can be created, viewed and export
properly to a list of regular configurators.
"""
from __future__ import division

from unittest import skipIf, TestCase
import os
from pandas import DataFrame
import numpy as np

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE:
    from app_common.apptools.testing_utils import temp_bringup_ui_for
    from pybleau.app.plotting.multi_plot_config import \
        HistogramPlotConfigurator, MultiHistogramPlotConfigurator, \
        MULTI_HIST_PLOT_TYPE, MultiLinePlotConfigurator, MULTI_LINE_PLOT_TYPE,\
        LinePlotConfigurator, SINGLE_CURVE, MULTI_CURVE

LEN = 16

TEST_DF = DataFrame({"a": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                     "a_b": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                     "b": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
                     "c": [1, 2, 3, 4, 2, 3, 1, 1, 4, 4, 5, 6, 4, 4, 5, 6],
                     "d": list("ababcabcdabcdeab"),
                     "e": np.random.randn(LEN),
                     "f": range(LEN),
                     # Highly repetitive column to split the entire data into 2
                     "g": np.array(["0", "1"] * (LEN // 2)),
                     "h": np.array([0, 1] * (LEN // 2), dtype=bool),
                     })


class BaseMultiPlotConfig(object):
    def test_creation_fails_if_no_df(self):
        with self.assertRaises(ValueError):
            config = self.configurator()
            config.to_dict()

    def test_bring_up(self):
        obj = self.configurator(data_source=TEST_DF)
        with temp_bringup_ui_for(obj):
            pass

    def test_cleanup_axis_title(self):
        config = self.configurator(data_source=TEST_DF, **self.config_params)
        for c in config.to_config_list():
            self.assertNotIn("_", c.x_axis_title)
            self.assertNotIn("_", c.y_axis_title)

    def test_create_export(self):
        config = self.configurator(data_source=TEST_DF, **self.config_params)
        self.assertEqual(config.plot_type, self.basic_type)
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        config_list = config.to_config_list()
        self.assertIsInstance(config_list, list)

    def test_styles_are_distinct(self):
        multi_config = self.configurator(data_source=TEST_DF,
                                         **self.config_params)
        config_list = multi_config.to_config_list()
        styles = [config.plot_style for config in config_list]
        self.assertEqual(len(styles), len(set(styles)))


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestMultiHistogramPlotConfig(TestCase, BaseMultiPlotConfig):
    def setUp(self):
        self.configurator = MultiHistogramPlotConfigurator
        self.basic_type = MULTI_HIST_PLOT_TYPE
        self.config_params = {"x_col_names": ["a_b", "c"]}

    def test_create_config_list(self):
        x_names = ["a", "b"]
        multi_config = self.configurator(data_source=TEST_DF,
                                         x_col_names=["a", "b"])
        config_list = multi_config.to_config_list()
        self.assertIsInstance(config_list, list)
        self.assertEqual(len(config_list), 2)
        for i, config in enumerate(config_list):
            self.assertIsInstance(config, HistogramPlotConfigurator)
            self.assertEqual(config.x_col_name, x_names[i])
            self.assertEqual(config.x_axis_title, x_names[i])

    def test_plot_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF,
                                   x_col_names=["b", "NON-EXISTENT"])
        with self.assertRaises(KeyError):
            config.to_config_list()[1].to_dict()


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestLinePlotConfig(TestCase, BaseMultiPlotConfig):
    def setUp(self):
        self.configurator = MultiLinePlotConfigurator
        self.basic_type = MULTI_LINE_PLOT_TYPE
        self.config_params = {"x_col_name": "a_b", "y_col_names": ["b", "c"]}

    def test_create_config_list_single_curve_mode(self):
        y_names = ["b", "c", "e"]
        multi_config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                         y_col_names=y_names,
                                         multi_mode=SINGLE_CURVE)
        config_list = multi_config.to_config_list()
        self.assertEqual(len(config_list), len(y_names))
        for i, config in enumerate(config_list):
            self.assertIsInstance(config, LinePlotConfigurator)
            self.assertEqual(config.x_col_name, "a")
            self.assertEqual(config.x_axis_title, "a")
            self.assertEqual(config.y_col_name, y_names[i])
            self.assertEqual(config.y_axis_title, y_names[i])

    def test_create_config_list_multi_curve_mode(self):
        y_names = ["b", "c", "e"]
        multi_config = self.configurator(data_source=TEST_DF, x_col_name="a_b",
                                         y_col_names=y_names,
                                         multi_mode=MULTI_CURVE)
        config_list = multi_config.to_config_list()
        self.assertEqual(len(config_list), 1)
        config = config_list[0]
        self.assertIsInstance(config, MultiLinePlotConfigurator)
        self.assertEqual(config.x_col_name, "a_b")
        self.assertEqual(config.x_axis_title, "a b")
        self.assertEqual(config.y_col_name, "")
        for y in y_names:
            self.assertIn(y, config.y_axis_title)

    def test_plot_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF,
                                   multi_mode=SINGLE_CURVE, x_col_name="a",
                                   y_col_names=["b", "NON-EXISTENT"])
        with self.assertRaises(KeyError):
            config.to_config_list()[1].to_dict()

    def test_plot_against_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF,
                                   x_col_name="NON-EXISTENT",
                                   multi_mode=SINGLE_CURVE, y_col_names=["b"])
        with self.assertRaises(KeyError):
            config.to_config_list()[0].to_dict()
