from unittest import skipIf, TestCase
import os
import pandas as pd
from pandas.util.testing import assert_frame_equal

try:
    import kiwisolver  # noqa
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE and KIWI_AVAILABLE:
    from .test_base_dataframe_analyzer import Analyzer, \
        DisplayingDataFrameAnalyzer, FilterDataFrameAnalyzer, \
        SortingDataFrameAnalyzer, SummaryDataFrameAnalyzer
    from pybleau.app.model.multi_dfs_dataframe_analyzer import \
        MultiDataFrameAnalyzer

msg = "No UI backend to paint into or no Kiwisolver"


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
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


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestFilterDataFrameAnalyzer(FilterDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestSummaryDataFrameAnalyzer(SummaryDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestSortingDataFrameAnalyzer(SortingDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDisplayingDataFrameAnalyzer(DisplayingDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = MultiDataFrameAnalyzer
