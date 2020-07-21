from unittest import skipIf, TestCase
import os

from .test_base_dataframe_analyzer import Analyzer, \
    DisplayingDataFrameAnalyzer, FilterDataFrameAnalyzer, \
    SortingDataFrameAnalyzer, SummaryDataFrameAnalyzer

try:
    import kiwisolver  # noqa
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if BACKEND_AVAILABLE and KIWI_AVAILABLE:
    from pybleau.app.model.dataframe_analyzer import DataFrameAnalyzer

msg = "No UI backend to paint into or no Kiwisolver"


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestAnalyzer(Analyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestFilterDataFrameAnalyzer(FilterDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestSummaryDataFrameAnalyzer(SummaryDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestSortingDataFrameAnalyzer(SortingDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDisplayingDataFrameAnalyzer(DisplayingDataFrameAnalyzer, TestCase):

    @classmethod
    def setUpClass(cls):
        cls.analyzer_klass = DataFrameAnalyzer
