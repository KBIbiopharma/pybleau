from unittest import TestCase

import numpy as np
import pandas as pd

from pybleau.app.plotting.api import factory_from_config
from pybleau.app.plotting.bar_factory import BarPlotFactory
from pybleau.app.plotting.heatmap_factory import HeatmapPlotFactory
from pybleau.app.plotting.histogram_factory import HistogramPlotFactory
from pybleau.app.plotting.line_factory import LinePlotFactory
from pybleau.app.plotting.plot_config import BarPlotConfigurator, \
    HeatmapPlotConfigurator, \
    HistogramPlotConfigurator, LinePlotConfigurator, ScatterPlotConfigurator
from pybleau.app.plotting.plot_factories import DEFAULT_FACTORIES
from pybleau.app.plotting.scatter_factories import ScatterPlotFactory

TEST_DF = pd.DataFrame({"Col_1": [1, 2, 3, 4, 5, 6, 7, 8],
                        "Col_2": np.array([1, 2, 3, 4, 5, 6, 7, 8])[::-1],
                        "Col_3": ["aa_aaa", "bb_bbb", "aa_aaa", "cc_ccc",
                                  "ee_eee", "dd_ddd", "ff_fff", "gg_ggg"],
                        "Col_4": np.random.randn(8),
                        })

TEST_DF2 = pd.DataFrame({"Col_1": [1, 2, 1, 2],
                         "Col_2": [1, 1, 2, 2],
                         "Col_3": np.random.randn(4)})


class TestAPI(TestCase):
    def test_heatmap_config_returns_heatmap_factory(self):
        config = HeatmapPlotConfigurator(data_source=TEST_DF2)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        config.z_col_name = "Col_3"
        def_factories = DEFAULT_FACTORIES
        actual = factory_from_config(config, def_factories)
        self.assertIsInstance(actual, HeatmapPlotFactory)

    def test_histogram_config_returns_historgram_factory(self):
        config = HistogramPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_4"
        def_factories = DEFAULT_FACTORIES
        actual = factory_from_config(config, def_factories)
        self.assertIsInstance(actual, HistogramPlotFactory)

    def test_bar_config_returns_bar_factory(self):
        config = BarPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_3"
        config.y_col_name = "Col_1"
        def_factories = DEFAULT_FACTORIES
        actual = factory_from_config(config, def_factories)
        self.assertIsInstance(actual, BarPlotFactory)

    def test_line_config_returns_line_factory(self):
        config = LinePlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        def_factories = DEFAULT_FACTORIES
        actual = factory_from_config(config, def_factories)
        self.assertIsInstance(actual, LinePlotFactory)

    def test_scatter_config_returns_scatter_factory(self):
        config = ScatterPlotConfigurator(data_source=TEST_DF)
        config.x_col_name = "Col_1"
        config.y_col_name = "Col_2"
        config.z_col_name = "Col_3"
        def_factories = DEFAULT_FACTORIES
        actual = factory_from_config(config, def_factories)
        self.assertIsInstance(actual, ScatterPlotFactory)


