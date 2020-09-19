from unittest import skipIf, TestCase
import os
import pandas as pd
from pandas.util.testing import assert_frame_equal, assert_series_equal

from .base_dataframe_analyzer import Analyzer, DisplayingDataFrameAnalyzer, \
    FilterDataFrameAnalyzer, SelectionPlotDataFrameAnalyzer, \
    SortingDataFrameAnalyzer, SummaryDataFrameAnalyzer

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE:
    from pybleau.app.model.multi_dfs_dataframe_analyzer import \
        MultiDataFrameAnalyzer

msg = "No UI backend to paint into"


@skipIf(not BACKEND_AVAILABLE, msg)
class TestAnalyzer(Analyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer

    def test_create_inconsistent_df_cols_map(self):
        with self.assertRaises(ValueError):
            self.analyzer_klass(source_df=self.df, _source_df_columns={})

    def test_create_from_source_dfs_1_df(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df})
        assert_frame_equal(analyzer.source_df, self.df)

    def test_create_from_source_dfs_2_dfs(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df,
                                                    "b": self.df3})
        self.assertEqual(analyzer.source_df.columns.tolist(),
                         self.df.columns.tolist() + self.df3.columns.tolist())
        assert_frame_equal(analyzer.source_df,
                           pd.concat([self.df, self.df3], axis=1))

    def test_create_from_source_dfs_as_list(self):
        analyzer = self.analyzer_klass(_source_dfs=[self.df, self.df3])
        assert_frame_equal(analyzer.source_df,
                           pd.concat([self.df, self.df3], axis=1))

    def test_create_from_overlapping_source_dfs(self):
        common_columns = set(self.df.columns) & set(self.df2.columns)
        self.assertGreater(len(common_columns), 0)
        with self.assertRaises(ValueError):
            self.analyzer_klass(_source_dfs={"a": self.df, "b": self.df2})

    def test_modify_source_df_value(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df,
                                                    "b": self.df3})
        analyzer.set_source_df_val(1, "a", "xyz")
        self.assertEqual(analyzer.source_df.loc[1, "a"], "xyz")
        analyzer.set_source_df_val(3, "x", 15)
        self.assertEqual(analyzer.source_df.loc[3, "x"], 15)

    def test_modify_source_df_value_bad_col(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df,
                                                    "b": self.df3})
        with self.assertRaises(KeyError):
            analyzer.set_source_df_val(1, "NON-EXISTENT", "xyz")

    def test_modify_existing_source_df_col(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df,
                                                    "b": self.df3})
        analyzer.set_source_df_col("a", "xyz")
        expected = pd.Series(["xyz"]*len(analyzer.source_df), name="a")
        assert_series_equal(analyzer.source_df["a"], expected)

    def test_add_source_df_col(self):
        analyzer = self.analyzer_klass(_source_dfs={"a": self.df,
                                                    "b": self.df3})
        with self.assertRaises(ValueError):
            # This has to fail because a new column is supposed to be created
            # but no target DF is specified:
            analyzer.set_source_df_col("NEW_COL", "xyz")

        # Now, this is supposed to work:
        analyzer.set_source_df_col("NEW_COL", "xyz", target_df="b")
        self.assertIn("NEW_COL", analyzer.source_df.columns)


@skipIf(not BACKEND_AVAILABLE, msg)
class TestFilterDataFrameAnalyzer(FilterDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSummaryDataFrameAnalyzer(SummaryDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSortingDataFrameAnalyzer(SortingDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestDisplayingDataFrameAnalyzer(DisplayingDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSelectionPlotDataFrameAnalyzer(SelectionPlotDataFrameAnalyzer,
                                         TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer
