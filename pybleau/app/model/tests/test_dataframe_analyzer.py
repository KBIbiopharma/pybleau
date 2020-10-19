from unittest import skipIf, TestCase
import os

from .base_dataframe_analyzer import Analyzer, DisplayingDataFrameAnalyzer, \
    FilterDataFrameAnalyzer, SelectionPlotDataFrameAnalyzer, \
    SortingDataFrameAnalyzer, SummaryDataFrameAnalyzer

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE:
    from pybleau.app.model.dataframe_analyzer import DataFrameAnalyzer

msg = "No UI backend to paint into"


@skipIf(not BACKEND_AVAILABLE, msg)
class TestAnalyzer(Analyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer

    def test_remove_column_description_when_remove_source_df_col(self):
        analyzer = self.analyzer_klass(source_df=self.df)
        self.assertEqual(analyzer.column_metadata, {})
        analyzer.column_metadata["a"] = "Cool column!"
        analyzer.column_metadata["b"] = "Another cool column!"
        # Remove a column from the source df:
        analyzer.source_df = self.df[["a", "c"]]
        self.assertNotIn("b", set(analyzer.column_metadata.keys()))


@skipIf(not BACKEND_AVAILABLE, msg)
class TestFilterDataFrameAnalyzer(FilterDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSummaryDataFrameAnalyzer(SummaryDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSortingDataFrameAnalyzer(SortingDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestDisplayingDataFrameAnalyzer(DisplayingDataFrameAnalyzer, TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE, msg)
class TestSelectionPlotDataFrameAnalyzer(SelectionPlotDataFrameAnalyzer,
                                         TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer
