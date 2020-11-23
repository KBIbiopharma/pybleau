from __future__ import division

from unittest import skipIf, TestCase
import os
from pandas import DataFrame
import numpy as np
from numpy.testing import assert_array_equal

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE:
    from app_common.apptools.testing_utils import assert_obj_gui_works
    from pybleau.app.plotting.plot_config import HeatmapPlotConfigurator, \
        HEATMAP_PLOT_TYPE, HistogramPlotConfigurator, HIST_PLOT_TYPE, \
        LinePlotConfigurator, BarPlotConfigurator, ScatterPlotConfigurator, \
        SCATTER_PLOT_TYPE, CMAP_SCATTER_PLOT_TYPE, LINE_PLOT_TYPE, \
        BAR_PLOT_TYPE

LEN = 16

TEST_DF = DataFrame({"a": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                     "b": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
                     "c": [1, 2, 3, 4, 2, 3, 1, 1, 4, 4, 5, 6, 4, 4, 5, 6],
                     "d": list("ababcabcdabcdeab"),
                     "e": np.random.randn(LEN),
                     "f": range(LEN),
                     # Highly repetitive column to split the entire data into 2
                     "g": np.array(["0", "1"] * (LEN // 2)),
                     "h": np.array([0, 1] * (LEN // 2), dtype=bool),
                     })


class BasePlotConfig(object):
    def test_creation_fails_if_no_df(self):
        with self.assertRaises(ValueError):
            config = self.configurator()
            config.to_dict()

    def test_bring_up(self):
        obj = self.configurator(data_source=TEST_DF)
        assert_obj_gui_works(obj)

    # Assertion utilities -----------------------------------------------------

    def assert_editor_options(self, editor):
        editor_options = editor.values
        if self.numerical_cols_only:
            for col in editor_options:
                if col != "index":
                    self.assertIn(TEST_DF[col].dtype, (np.int64, np.float64))
        else:
            self.assertEqual(set(editor_options),
                             set(TEST_DF.columns) | {"index"})


class BaseXYPlotConfig(BasePlotConfig):

    def test_plot_basic(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b")
        self.assertEqual(config.plot_type, self.basic_type)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        assert_array_equal(config_dict["x_arr"], TEST_DF["a"].values)
        self.assertIn("y_arr", config_dict)
        assert_array_equal(config_dict["y_arr"], TEST_DF["b"].values)

    def test_data_choices(self):
        """ Make sure different configurators provide the right data choices.
        """
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b")
        view_items = config._data_selection_items()
        x_editor = view_items[0].content[0].editor
        self.assert_editor_options(x_editor)
        y_editor = view_items[1].content[0].editor
        self.assert_editor_options(y_editor)

    def test_plot_colored_by_str_col(self):
        # Color by a column filled with boolean values
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="d")
        self.assertIn(config.plot_type, self.basic_type)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertIsInstance(config_dict["x_arr"], dict)
        d_values = TEST_DF["d"].unique()
        self.assertEqual(set(config_dict["x_arr"].keys()), set(d_values))
        for arr in config_dict["x_arr"].values():
            self.assertIsInstance(arr, np.ndarray)
        # For example:
        assert_array_equal(config_dict["x_arr"]["c"], np.array([1, 4, 4]))

        self.assertIn("y_arr", config_dict)
        self.assertIsInstance(config_dict["y_arr"], dict)
        self.assertEqual(set(config_dict["y_arr"].keys()), set(d_values))
        for arr in config_dict["y_arr"].values():
            self.assertIsInstance(arr, np.ndarray)
        # For example:
        assert_array_equal(config_dict["y_arr"]["c"], np.array([2, 2, 3]))

    def test_plot_colored_by_bool_col(self):
        # Color by a column filled with boolean values
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="h")
        self.assertIn(config.plot_type, self.basic_type)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertIsInstance(config_dict["x_arr"], dict)

        hue_values = set(TEST_DF["h"])
        self.assertEqual(set(config_dict["x_arr"].keys()), hue_values)
        assert_array_equal(config_dict["x_arr"][False], TEST_DF["a"][::2])
        assert_array_equal(config_dict["x_arr"][True], TEST_DF["a"][1::2])

        self.assertIn("y_arr", config_dict)
        self.assertIsInstance(config_dict["y_arr"], dict)
        self.assertEqual(set(config_dict["y_arr"].keys()), hue_values)
        assert_array_equal(config_dict["y_arr"][False], TEST_DF["b"][::2])
        assert_array_equal(config_dict["y_arr"][True], TEST_DF["b"][1::2])

    def test_plot_colored_by_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="NON-EXISTENT")
        with self.assertRaises(KeyError):
            config.to_dict()


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestScatterPlotConfig(TestCase, BaseXYPlotConfig):
    def setUp(self):
        self.configurator = ScatterPlotConfigurator
        self.basic_type = SCATTER_PLOT_TYPE
        self.numerical_cols_only = True

    def test_plot_scatter_colored_by_int_col(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="c")
        self.assertEqual(config.plot_type, CMAP_SCATTER_PLOT_TYPE)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertIsInstance(config_dict["x_arr"], np.ndarray)
        self.assertIn("y_arr", config_dict)
        self.assertIsInstance(config_dict["y_arr"], np.ndarray)
        self.assertIn("z_arr", config_dict)
        self.assertIsInstance(config_dict["z_arr"], np.ndarray)

    def test_plot_scatter_colored_by_float_col(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="e")
        self.assertEqual(config.plot_type, CMAP_SCATTER_PLOT_TYPE)
        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertIsInstance(config_dict["x_arr"], np.ndarray)
        self.assertIn("y_arr", config_dict)
        self.assertIsInstance(config_dict["y_arr"], np.ndarray)
        self.assertIn("z_arr", config_dict)
        self.assertIsInstance(config_dict["z_arr"], np.ndarray)

    def test_style_colorize_by_float_changes_on_color_column_change(self):
        """ The dtype of the column to colorize controls colorize_by_float.
        """
        # Color by a string:
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="d")
        self.assertFalse(config.plot_style.colorize_by_float)

        # Color by a float:
        config.z_col_name = "e"
        self.assertTrue(config.plot_style.colorize_by_float)


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestLinePlotConfig(TestCase, BaseXYPlotConfig):
    def setUp(self):
        self.configurator = LinePlotConfigurator
        self.basic_type = LINE_PLOT_TYPE
        self.numerical_cols_only = True


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestBarPlotConfig(TestCase, BaseXYPlotConfig):
    def setUp(self):
        self.configurator = BarPlotConfigurator
        self.basic_type = BAR_PLOT_TYPE
        self.numerical_cols_only = False

    def test_data_choices(self):
        """ Make sure different configurators provide the right data choices.
        """
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b")
        view_items = config._data_selection_items()
        x_editor = view_items[0].content[3].content[0].content[0].editor
        self.assert_editor_options(x_editor)

    def test_melt_mode_no_effect(self):
        config = self.configurator(data_source=TEST_DF, melt_source_data=True)
        self.assertEqual(config.plot_type, self.basic_type)
        # No columns to melt, so no transformation:
        self.assertIs(config.data_source, TEST_DF)
        self.assertIs(config.transformed_data, TEST_DF)

    def test_melt_mode_with_melted_columns(self):
        config = self.configurator(data_source=TEST_DF, melt_source_data=True,
                                   columns_to_melt=["e", "f"])

        self.assertIsNot(config.transformed_data, TEST_DF)
        self.assertIs(config.data_source, TEST_DF)

        # Pulling the x_arr forces a reset of the x_col_name
        x_values = np.array(["e"]*LEN+["f"]*LEN)
        assert_array_equal(config.x_arr, x_values)
        self.assertEqual(config.x_col_name, "variable")

        self.assertEqual(len(config.y_arr), 2 * LEN)
        self.assertEqual(config.y_col_name, "value")

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        assert_array_equal(config_dict["x_arr"], x_values)
        self.assertIn("y_arr", config_dict)
        self.assertEqual(len(config_dict["y_arr"]), 2 * LEN)

    def test_melt_mode_with_melted_columns_and_str_color(self):
        config = self.configurator(data_source=TEST_DF, melt_source_data=True,
                                   columns_to_melt=["e", "f"], z_col_name="g")

        self.assertIsNot(config.transformed_data, TEST_DF)
        self.assertIs(config.data_source, TEST_DF)

        hue_values = TEST_DF["g"].unique()

        # Pulling the x_arr forces a reset of the x_col_name
        x_values = np.array(["e"] * (LEN // 2) + ["f"] * (LEN // 2))
        self.assertEqual(set(config.x_arr.keys()), set(hue_values))
        for key in hue_values:
            assert_array_equal(config.x_arr[key], x_values)
        self.assertEqual(config.x_col_name, "variable")

        for key in hue_values:
            self.assertEqual(len(config.y_arr[key]), LEN)

        self.assertEqual(config.y_col_name, "value")
        self.assertIn("g", config.transformed_data.columns)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertEqual(set(config_dict["x_arr"].keys()), set(hue_values))
        for key in hue_values:
            assert_array_equal(config_dict["x_arr"][key], x_values)

        self.assertIn("y_arr", config_dict)
        for key in hue_values:
            self.assertEqual(len(config_dict["y_arr"][key]), LEN)

    def test_melt_mode_with_melted_columns_and_bool_color(self):
        config = self.configurator(data_source=TEST_DF, melt_source_data=True,
                                   columns_to_melt=["e", "f"], z_col_name="h")

        self.assertIsNot(config.transformed_data, TEST_DF)
        self.assertIs(config.data_source, TEST_DF)

        hue_values = TEST_DF["h"].unique()

        # Pulling the x_arr forces a reset of the x_col_name
        x_values = np.array(["e"] * (LEN // 2) + ["f"] * (LEN // 2))
        self.assertEqual(set(config.x_arr.keys()), set(hue_values))
        for key in hue_values:
            assert_array_equal(config.x_arr[key], x_values)
        self.assertEqual(config.x_col_name, "variable")

        for key in hue_values:
            self.assertEqual(len(config.y_arr[key]), LEN)

        self.assertEqual(config.y_col_name, "value")
        self.assertIn("h", config.transformed_data.columns)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        self.assertEqual(set(config_dict["x_arr"].keys()), set(hue_values))
        for key in hue_values:
            assert_array_equal(config_dict["x_arr"][key], x_values)

        self.assertIn("y_arr", config_dict)
        for key in hue_values:
            self.assertEqual(len(config_dict["y_arr"][key]), LEN)


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestHistogramPlotConfig(BasePlotConfig, TestCase):
    def setUp(self):
        self.configurator = HistogramPlotConfigurator
        self.basic_type = HIST_PLOT_TYPE
        self.numerical_cols_only = True

    # Tests -------------------------------------------------------------------

    def test_plot_basic(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a")
        self.assertEqual(config.plot_type, self.basic_type)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)
        self.assertIn("x_arr", config_dict)
        assert_array_equal(config_dict["x_arr"], TEST_DF["a"].values)

    def test_plot_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF,
                                   x_col_name="NON-EXISTENT")
        with self.assertRaises(KeyError):
            config.to_dict()

    def test_data_choices(self):
        """ Make sure different configurators provide the right data choices.
        """
        config = self.configurator(data_source=TEST_DF, x_col_name="a")
        view_items = config._data_selection_items()
        x_editor = view_items[0].content[0].editor
        self.assert_editor_options(x_editor)


@skipIf(not BACKEND_AVAILABLE, "No UI backend available")
class TestHeatmapPlotConfig(BasePlotConfig, TestCase):
    def setUp(self):
        self.configurator = HeatmapPlotConfigurator
        self.basic_type = HEATMAP_PLOT_TYPE
        self.numerical_cols_only = True

    # Tests -------------------------------------------------------------------

    def test_plot_basic(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="e")
        self.assertEqual(config.plot_type, self.basic_type)

        config_dict = config.to_dict()
        self.assertIsInstance(config_dict, dict)

    def test_plot_colored_by_NON_EXISTENT_col(self):
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="NON-EXISTENT")
        with self.assertRaises(KeyError):
            config.to_dict()

    def test_data_choices(self):
        """ Make sure different configurators provide the right data choices.

        Passing non-numerical
        """
        config = self.configurator(data_source=TEST_DF, x_col_name="a",
                                   y_col_name="b", z_col_name="e")
        view_items = config._data_selection_items()
        x_editor = view_items[0].content[0].editor
        self.assert_editor_options(x_editor)
        y_editor = view_items[1].content[0].editor
        self.assert_editor_options(y_editor)
