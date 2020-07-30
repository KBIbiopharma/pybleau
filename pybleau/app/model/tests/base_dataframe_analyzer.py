import pandas as pd
from pandas.core.computation.ops import UndefinedVariableError
from pandas.util.testing import assert_frame_equal, assert_series_equal
import numpy as np

from traits.api import TraitError
from traits.testing.unittest_tools import UnittestTools

from app_common.apptools.testing_utils import \
    reraise_traits_notification_exceptions
from pybleau.app.model.dataframe_analyzer import \
    DEFAULT_CATEG_SUMMARY_ELEMENTS, DEFAULT_SUMMARY_ELEMENTS, \
    REVERSED_SUFFIX, DataFramePlotManager, NO_SORTING_ENTRY
from pybleau.app.plotting.plot_config import ScatterPlotConfigurator


class FilterDataFrameAnalyzer(UnittestTools):
    """ Tests around filtering a DFAnalyzer.
    """
    def setUp(self):
        self.df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                                "c": list("abcdeabcaab")})
        self.df2 = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                                 "b": [10, 15, 20, 15, 10]})

    def test_sanitize_columns_remove_special_char(self):
        df = self.df
        df.columns = ["~a./", "&)b[", "*@c;"]
        analyzer = self.analyzer_klass(source_df=df)
        self.assertEqual(set(analyzer.source_df.columns), set("abc"))

    def test_sanitize_columns_remove_special_char_collision(self):
        df = self.df
        df.columns = ["~a./", "&)b[", "@b."]
        analyzer = self.analyzer_klass(source_df=df)
        self.assertEqual(set(analyzer.source_df.columns), {"a", "b", "b_2"})

    def test_filter_numerical_columns(self):
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df)
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        analyzer.filter_exp = "a > 2"
        expected = pd.DataFrame({"a": [3, 4, 5], "b": [20, 15, 10]},
                                index=[2, 3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)
        analyzer.filter_exp = "a > 2 and b < 18"
        expected = pd.DataFrame({"a": [4, 5], "b": [15, 10]},
                                index=[3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)
        analyzer.filter_exp = ""
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)

    def test_filter_no_auto_apply(self):
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df, filter_auto_apply=False)
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = "a > 2"
        analyzer.recompute_filtered_df()
        expected = pd.DataFrame({"a": [3, 4, 5], "b": [20, 15, 10]},
                                index=[2, 3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)

        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = "a > 2 and b < 18"

        analyzer.recompute_filtered_df()
        expected = pd.DataFrame({"a": [4, 5], "b": [15, 10]},
                                index=[3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)
        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = ""

        analyzer.recompute_filtered_df()
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)

    def test_filter_string_column(self):
        df = self.df
        analyzer = self.analyzer_klass(source_df=df)
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        analyzer.filter_exp = "c == 'a'"
        expected = pd.DataFrame({"a": [0, 5, 8, 9], "b": [0, 50, 80, 90],
                                 "c": list("aaaa")},
                                index=[0, 5, 8, 9])
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_bad_filter(self):
        """ If filter set to a bad value, filtered DF unchanged.
        """
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       filter_error_handling="ignore")
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        # Request that involves a non-existent column leads to unchanged DF
        analyzer.filter_exp = "c > 3"
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        analyzer.filter_exp = "a > 2 and b < 18"
        expected = pd.DataFrame({"a": [4, 5], "b": [15, 10]},
                                index=[3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)
        # Request that involves a, invalid syntax leads to no-change too:
        analyzer.filter_exp = "a <"
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_incomplete_filter(self):
        """ If filter unfinished, filtered DF unchanged.
        """
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       filter_error_handling="ignore")
        self.assertEqual(analyzer.filter_exp, "")

        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = "a"

        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = "a "

        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = "a > "

        # DF finally changes because expression is complete:
        with self.assertTraitChanges(analyzer, "filtered_df", 1):
            analyzer.filter_exp = "a > 1"

        expected = pd.DataFrame({"a": [2, 3, 4, 5],
                                 "b": [15, 20, 15, 10]}, index=[1, 2, 3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_bad_filter_with_raise(self):
        """ If filter set to a bad value, and raise behavior, error raised in
        listener.
        """
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       filter_error_handling="raise")
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        # Request that involves an invalid expression raises a syntax error
        # inside the listener:
        with reraise_traits_notification_exceptions():
            with self.assertRaises(SyntaxError):
                analyzer.filter_exp = "a > "

            with self.assertRaises(UndefinedVariableError):
                analyzer.filter_exp = "c > 1"

    def test_no_significant_filter_change(self):
        """ Make sure that insignificant changes to the filter expression don't
        trigger updates.
        """
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       filter_error_handling="raise")
        self.assertEqual(analyzer.filter_exp, "")
        assert_frame_equal(analyzer.filtered_df, analyzer.source_df)
        # Spaces are ignored
        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = " "

        # And so are space-like characters
        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = " \n"

        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            analyzer.filter_exp = " \n  \t \r\n"

    def test_new_line_in_filter(self):
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       filter_exp="a > \n1")

        expected = pd.DataFrame({"a": [2, 3, 4, 5],
                                 "b": [15, 20, 15, 10]}, index=[1, 2, 3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_subclass_filter_applied(self):
        class DFAnalyzer(self.analyzer_klass):
            def _filter_exp_default(self):
                return "a > 1"

        df = self.df2
        analyzer = DFAnalyzer(source_df=df)
        expected = pd.DataFrame({"a": [2, 3, 4, 5],
                                 "b": [15, 20, 15, 10]}, index=[1, 2, 3, 4])
        assert_frame_equal(analyzer.filtered_df, expected)


class SummaryDataFrameAnalyzer(UnittestTools):
    """ Tests around summarizing a DFAnalyzer.
    """
    def setUp(self):
        self.df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                                "c": list("abcdeabcaab")})
        self.df2 = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                                 "b": [10, 15, 20, 15, 10]})

    def test_compute_summary(self):
        analyzer = self.analyzer_klass(source_df=self.df)
        summary = analyzer.compute_summary()
        self.assertIsInstance(analyzer.summary_df, pd.DataFrame)
        self.assertEqual(summary.columns.tolist(), ["a", "b"])
        self.assertEqual(summary.index.tolist(), DEFAULT_SUMMARY_ELEMENTS)
        self.assertEqual(summary.loc["mean", "a"], 5)
        self.assertEqual(summary.loc["mean", "b"], 50)
        self.assertEqual(summary.loc["min", "a"], 0)
        self.assertEqual(summary.loc["min", "b"], 0)
        self.assertEqual(summary.loc["max", "a"], 10)
        self.assertEqual(summary.loc["max", "b"], 100)
        self.assertEqual(summary.loc["25%", "a"], 2.5)
        self.assertEqual(summary.loc["25%", "b"], 25)
        self.assertFalse(np.any(np.isnan(summary)))

    def test_compute_summary_if_empty_filtered(self):
        analyzer = self.analyzer_klass(source_df=self.df)
        # Set filter so there is no filtered data:
        analyzer.filter_exp = "a > 100"
        with reraise_traits_notification_exceptions():
            summary = analyzer.compute_summary()
        assert_frame_equal(summary, pd.DataFrame([]))

    def test_compute_categorical_summary(self):
        analyzer = self.analyzer_klass(source_df=self.df)
        summary = analyzer.compute_categorical_summary()
        self.assertIsInstance(analyzer.summary_categorical_df, pd.DataFrame)
        expected = pd.DataFrame({"c": [11, 5, "a", 4, "b", 3]},
                                index=DEFAULT_CATEG_SUMMARY_ELEMENTS)
        assert_frame_equal(summary, expected)

    def test_change_summary_when_filter(self):
        analyzer = self.analyzer_klass(source_df=self.df)
        analyzer.compute_summary()
        summary = analyzer.summary_df
        self.assertEqual(summary.loc["mean", "a"], 5)
        self.assertEqual(summary.loc["mean", "b"], 50)

        with self.assertTraitChanges(analyzer, "summary_df"):
            analyzer.filter_exp = "a == 2"

        summary = analyzer.summary_df
        self.assertEqual(summary.loc["mean", "a"], 2)
        self.assertEqual(summary.loc["mean", "b"], 20)

    def test_special_summary_list(self):
        # Replace 0.5% by 0.1%
        summary_index = [u'mean', u'std', u'min', u'0.1%', u'1%', u'25%',
                         u'50%', u'75%', u'99%', u'99.5%', u'max', u'count']
        df = self.df2
        analyzer = self.analyzer_klass(source_df=df,
                                       summary_index=summary_index)
        summary = analyzer.compute_summary()
        self.assertEqual(summary.index.tolist(), summary_index)
        self.assertFalse(np.any(np.isnan(summary)))

        # Make a default one and make sure they match
        orig_summarizer = self.analyzer_klass(source_df=df)
        orig_summarizer.compute_summary()
        for col in DEFAULT_SUMMARY_ELEMENTS:
            if col != "0.5%":
                assert_series_equal(orig_summarizer.summary_df.loc[col, :],
                                    analyzer.summary_df.loc[col, :])


class Analyzer(UnittestTools):
    """ Tests around creating a DFAnalyzer.
    """
    def setUp(self):
        self.df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                                "c": list("abcdeabcaab")})
        self.df2 = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                                 "b": [10, 15, 20, 15, 10]})
        self.df3 = pd.DataFrame({"x": [1, 2, 3, 4, 5],
                                 "y": [10, 15, 20, 15, 10]})

    def test_create_no_data(self):
        analyzer = self.analyzer_klass()
        self.assertIsNone(analyzer.source_df)
        self.assertIsNone(analyzer.filtered_df)
        self.assertIsNone(analyzer.displayed_df)

    def test_sanitize_source_df_columns(self):
        df = pd.DataFrame({"a b": [1, 2], "c*d": [3, 4], "e.f": [5, 6]})
        analyzer = self.analyzer_klass(source_df=df)
        self.assertIsNot(analyzer.source_df, df)
        self.assertEqual(analyzer.source_df.columns.tolist(),
                         ["a_b", "c_d", "e_f"])
        analyzer.filter_exp = "e_f == 5"
        expected = pd.DataFrame({"a_b": [1], "c_d": [3], "e_f": [5]})
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_df_with_strings(self):
        df = pd.DataFrame({"a": ["x", "x", "x"], "b": ["x", "y", "y"]})
        analyzer = self.analyzer_klass(source_df=df)
        assert_frame_equal(analyzer.summary_df, pd.DataFrame([]))
        expected = pd.DataFrame({"a": [3, 1, "x", 3, np.nan, np.nan],
                                 "b": [3, 2, "y", 2, "x", 1]},
                                index=DEFAULT_CATEG_SUMMARY_ELEMENTS)
        assert_frame_equal(analyzer.summary_categorical_df, expected)

    def test_object_df_with_conversion(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, dtype=object)
        analyzer = self.analyzer_klass(source_df=df,
                                       convert_source_dtypes=True)
        expected = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, dtype=np.float64)
        assert_frame_equal(analyzer.source_df, expected)
        assert_frame_equal(analyzer.filtered_df, expected)

    def test_object_col_in_df(self):
        """ Changing the column list changes the filtered DF and summary DF.
        """
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]},
                          dtype=object)
        df["a"] = df["a"].astype("float64")
        analyzer = self.analyzer_klass(source_df=df)
        self.assertEqual(list(analyzer.source_df.columns), ["a", "b"])
        self.assertEqual(list(analyzer.summary_df.columns), ["a"])
        self.assertEqual(list(analyzer.summary_categorical_df.columns), ["b"])

    def test_time_dtype_cols_in_df(self):
        """ Changing the column list changes the filtered DF and summary DF.
        """
        df = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                           "b": [pd.Timestamp("2000-1-1")]*5,
                           "c": [pd.Timedelta("00:00:0{}".format(i))
                                 for i in range(5)]})

        analyzer = self.analyzer_klass(source_df=df,
                                       summary_index=["mean", "3%"])
        self.assertEqual(list(analyzer.source_df.columns), ["a", "b", "c"])
        self.assertEqual(list(analyzer.summary_df.columns), ["a", "c"])
        self.assertEqual(list(analyzer.summary_categorical_df.columns), ["b"])

    def test_keep_index_name_sort_options_synced(self):
        """ Make sure index_name & sort options update on data update.

        This update may be triggered by programmatic modification of an
        analyzer or during its deserialization or creation.
        """
        analyzer = self.analyzer_klass(source_df=self.df)
        self.assertEqual(analyzer.index_name, "index")
        self.assertIn("index", analyzer.sort_by_col_list)

        # Change source_df
        df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                           "c": list("abcdeabcaab")}, index=range(11))
        df.index.name = "new index"
        with self.assertTraitChanges(analyzer, "index_name"):
            with self.assertTraitChanges(analyzer, "sort_by_col_list"):
                analyzer.source_df = df

        self.assertEqual(analyzer.index_name, "new index")
        self.assertNotIn("index", analyzer.sort_by_col_list)
        self.assertIn("new index", analyzer.sort_by_col_list)


class SortingDataFrameAnalyzer(UnittestTools):
    """ Tests around sorting a DFAnalyzer.
    """
    def setUp(self):
        self.df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                                "c": list("abcdeabcaab")})
        self.df2 = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                                 "b": [10, 15, 20, 15, 10]})

    def test_sorting_options_no_index_name(self):
        """ Changing the sort_by_col changes the filtered DF and summary DF.
        """
        b_vals = [10, 15, 20, 16, 11, 12, 21]
        a_vals = [1, 2, 3, 4, 5, 2, 1]
        df = pd.DataFrame({"a": a_vals, "b": b_vals})
        # Enforce column order:
        df = df[["a", "b"]]

        analyzer = self.analyzer_klass(source_df=df)
        # Initially, data unchanged/unsorted
        self.assertEqual(analyzer.sort_by_col, "index")
        assert_frame_equal(analyzer.filtered_df, df)
        expected = [NO_SORTING_ENTRY, "index", "index" + REVERSED_SUFFIX, "a",
                    "a" + REVERSED_SUFFIX, "b", "b" + REVERSED_SUFFIX]
        self.assertEqual(analyzer.sort_by_col_list, expected)

    def test_sorting_options_with_index_name(self):
        b_vals = [10, 15, 20, 16, 11, 12, 21]
        a_vals = [1, 2, 3, 4, 5, 2, 1]
        df = pd.DataFrame({"a": a_vals, "b": b_vals})
        df.index.name = "FOO"
        # Enforce column order:
        df = df[["a", "b"]]

        analyzer = self.analyzer_klass(source_df=df)
        # Initially, data unchanged/unsorted
        self.assertEqual(analyzer.sort_by_col, "FOO")
        assert_frame_equal(analyzer.filtered_df, df)
        expected = [NO_SORTING_ENTRY, "FOO", "FOO" + REVERSED_SUFFIX, "a",
                    "a" + REVERSED_SUFFIX, "b", "b" + REVERSED_SUFFIX]
        self.assertEqual(analyzer.sort_by_col_list, expected)

    def test_initial_index_sort(self):
        unsorted_df = pd.DataFrame({"a": range(5)})
        unsorted_df.index = [1, 2, 5, 6, 3]
        # By default, the DF is sorted along the index: data_sorted=True
        analyzer = self.analyzer_klass(source_df=unsorted_df)
        self.assertEqual(analyzer.displayed_df.index.tolist(), [1, 2, 3, 5, 6])
        self.assertEqual(analyzer.displayed_df.a.tolist(), [0, 1, 4, 2, 3])
        self.assertEqual(analyzer.sort_by_col, "index")
        self.assertIn(NO_SORTING_ENTRY, analyzer.sort_by_col_list)

    def test_turn_off_initial_index_sort(self):
        unsorted_df = pd.DataFrame({"a": range(5)})
        unsorted_df.index = [1, 2, 5, 6, 3]
        # Turn off initial sorting:
        analyzer = self.analyzer_klass(source_df=unsorted_df,
                                       data_sorted=False)
        self.assertEqual(analyzer.displayed_df.index.tolist(), [1, 2, 5, 6, 3])
        self.assertEqual(analyzer.displayed_df.a.tolist(), list(range(5)))
        self.assertEqual(analyzer.sort_by_col, NO_SORTING_ENTRY)

    def test_sorting_variables_updates_when_source_df_changes(self):
        unsorted_df = pd.DataFrame({"a": range(5)})
        unsorted_df.index = [1, 2, 5, 6, 3]
        # Turn off initial sorting:
        analyzer = self.analyzer_klass(source_df=unsorted_df,
                                       data_sorted=False)
        self.assertEqual(analyzer.displayed_df.index.tolist(), [1, 2, 5, 6, 3])
        self.assertEqual(analyzer.displayed_df.a.tolist(), list(range(5)))
        self.assertIn(NO_SORTING_ENTRY, analyzer.sort_by_col_list)
        self.assertEqual(analyzer.sort_by_col, NO_SORTING_ENTRY)
        self.assertFalse(analyzer.data_sorted)

        analyzer.source_df = pd.DataFrame({"a": range(5)})
        self.assertEqual(analyzer.sort_by_col, "index")
        self.assertTrue(analyzer.data_sorted)
        self.assertIn(NO_SORTING_ENTRY, analyzer.sort_by_col_list)

        analyzer.source_df = unsorted_df
        self.assertIn(NO_SORTING_ENTRY, analyzer.sort_by_col_list)
        self.assertEqual(analyzer.sort_by_col, NO_SORTING_ENTRY)
        self.assertFalse(analyzer.data_sorted)

    def test_sorting_by_columns(self):
        """ Changing the sort_by_col changes the filtered DF and summary DF.
        """
        b_vals = [10, 15, 20, 16, 11, 12, 21]
        a_vals = [1, 2, 3, 4, 5, 2, 1]
        df = pd.DataFrame({"a": a_vals, "b": b_vals})
        analyzer = self.analyzer_klass(source_df=df)
        with self.assertTraitChanges(analyzer, "filtered_df"):
            with self.assertTraitChanges(analyzer, "displayed_df"):
                analyzer.sort_by_col = "b" + REVERSED_SUFFIX

        idx_b_sorted = np.argsort(np.array(b_vals))[::-1]
        expected = list(sorted(b_vals, reverse=True))
        self.assertEqual(analyzer.filtered_df["b"].tolist(), expected)
        self.assertEqual(analyzer.displayed_df["b"].tolist(), expected)
        expected = list(np.array(a_vals)[idx_b_sorted])
        self.assertEqual(analyzer.filtered_df["a"].tolist(), expected)
        self.assertEqual(analyzer.displayed_df["a"].tolist(), expected)

        # Invalid option
        with self.assertTraitDoesNotChange(analyzer, "filtered_df"):
            with self.assertTraitDoesNotChange(analyzer, "displayed_df"):
                with self.assertRaises(TraitError):
                    analyzer.sort_by_col = "BLAH"

    def test_sorting_by_index(self):
        """ Changing the column list changes the filtered DF and summary DF.
        """
        b_vals = [10, 15, 20, 16, 11, 12, 21]
        a_vals = [1, 2, 3, 4, 5, 2, 1]
        df = pd.DataFrame({"a": a_vals, "b": b_vals})
        analyzer = self.analyzer_klass(source_df=df)
        # Initially, data unchanged/unsorted
        self.assertEqual(analyzer.sort_by_col, "index")

        with self.assertTraitChanges(analyzer, "filtered_df"):
            with self.assertTraitChanges(analyzer, "displayed_df"):
                analyzer.sort_by_col = "index" + REVERSED_SUFFIX

        self.assertEqual(analyzer.filtered_df["a"].tolist(), a_vals[::-1])
        self.assertEqual(analyzer.displayed_df["a"].tolist(), a_vals[::-1])
        self.assertEqual(analyzer.filtered_df["b"].tolist(), b_vals[::-1])
        self.assertEqual(analyzer.displayed_df["b"].tolist(), b_vals[::-1])

    def test_filter_transformation(self):
        df = self.df
        with self.assertRaises(UndefinedVariableError):
            with reraise_traits_notification_exceptions():
                self.analyzer_klass(source_df=df, filter_exp="A > 2")

        analysis = self.analyzer_klass(
            source_df=df, filter_exp="A > 2",
            filter_transformation=lambda x: x.lower()
        )
        filtered = df.iloc[3:, :]
        assert_frame_equal(analysis.source_df, df)
        assert_frame_equal(analysis.filtered_df, filtered)
        assert_frame_equal(analysis.displayed_df, filtered)

    def test_plotter_selection_connected(self):
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = DataFramePlotManager(data_source=df)
        # Connect the 2 managers:
        model.plot_manager_list.append(plot_manager)

        # Set analyzer selection:
        model.selected_idx = [0, 2, 5]
        self.assertEqual(plot_manager.index_selected, [0, 2, 5])

        # Append to analyzer selection
        model.selected_idx.append(6)
        self.assertEqual(plot_manager.index_selected, [0, 2, 5, 6])

        # Set analyzer selection:
        plot_manager.index_selected = [1, 4]
        self.assertEqual(model.selected_idx, [1, 4])

        # Append to analyzer selection
        plot_manager.index_selected.append(3)
        self.assertEqual(model.selected_idx, [1, 4, 3])

    def test_multi_plotter_selection_connected(self):
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = DataFramePlotManager(data_source=df)
        plot_manager2 = DataFramePlotManager(data_source=df)
        # Connect the 3 managers:
        model.plot_manager_list.append(plot_manager)
        model.plot_manager_list.append(plot_manager2)

        # Set analyzer selection:
        model.selected_idx = [0, 2, 5]
        self.assertEqual(plot_manager.index_selected, [0, 2, 5])
        self.assertEqual(plot_manager2.index_selected, [0, 2, 5])

        # Append to analyzer selection
        model.selected_idx.append(6)
        self.assertEqual(plot_manager.index_selected, [0, 2, 5, 6])
        self.assertEqual(plot_manager2.index_selected, [0, 2, 5, 6])

        # Set plot_manager selection:
        plot_manager.index_selected = [1, 4]
        self.assertEqual(model.selected_idx, [1, 4])
        self.assertEqual(plot_manager2.index_selected, [1, 4])

        # Append to plot_manager selection
        plot_manager.index_selected.append(3)
        self.assertEqual(model.selected_idx, [1, 4, 3])
        self.assertEqual(plot_manager2.index_selected, [1, 4, 3])

        # Set plot_manager2 selection:
        plot_manager2.index_selected = [1, 4]
        self.assertEqual(model.selected_idx, [1, 4])
        self.assertEqual(plot_manager.index_selected, [1, 4])

        # Append to plot_manager2 selection
        plot_manager2.index_selected.append(3)
        self.assertEqual(model.selected_idx, [1, 4, 3])
        self.assertEqual(plot_manager.index_selected, [1, 4, 3])

    def test_change_plotter_datasource_when_filter(self):
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = DataFramePlotManager(data_source=df)
        plot_manager2 = DataFramePlotManager(data_source=df)
        # Connect the 3 managers:
        model.plot_manager_list.append(plot_manager)
        model.plot_manager_list.append(plot_manager2)

        with self.assertTraitChanges(plot_manager, "data_source"):
            with self.assertTraitChanges(plot_manager2, "data_source"):
                model.filter_exp = "a == 2"

    def test_change_plotter_datasource_when_sorting(self):
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = DataFramePlotManager(data_source=df)
        plot_manager2 = DataFramePlotManager(data_source=df)
        # Connect the 3 managers:
        model.plot_manager_list.append(plot_manager)
        model.plot_manager_list.append(plot_manager2)

        with self.assertTraitChanges(plot_manager, "data_source"):
            with self.assertTraitChanges(plot_manager2, "data_source"):
                model.sort_by_col = "b"

    def test_change_plot_data_when_sorting(self):
        """ Check that plotted data gets updated when changing sorting order.
        """
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = self.create_plot_manager(n_plots=2)
        model.plot_manager_list.append(plot_manager)

        plot_data1 = plot_manager.contained_plots[0].plot.data
        plot_data2 = plot_manager.contained_plots[1].plot.data

        with self.assertTraitChanges(plot_data1, "data_changed"):
            with self.assertTraitChanges(plot_data2, "data_changed"):
                model.sort_by_col = "b"

    def test_frozen_plot_data_doesnt_change_when_sorting(self):
        """ Check that plotted data gets updated when changing sorting order.
        """
        df = self.df
        model = self.analyzer_klass(source_df=df)
        plot_manager = self.create_plot_manager(n_plots=2)
        model.plot_manager_list.append(plot_manager)

        plot_manager.contained_plots[0].frozen = False
        plot_data1 = plot_manager.contained_plots[0].plot.data
        plot_manager.contained_plots[1].frozen = True
        plot_data2 = plot_manager.contained_plots[1].plot.data

        with self.assertTraitChanges(plot_data1, "data_changed"):
            with self.assertTraitDoesNotChange(plot_data2, "data_changed"):
                model.sort_by_col = "b"

    def test_change_selection_idx_vs_data_selected(self):
        """ Check that plotted data gets updated when changing sorting order.
        """
        df = self.df
        model = self.analyzer_klass(source_df=df)
        model.selected_idx = [0]
        self.assertEqual(model.data_selected, [df.index[0]])

    def test_change_selection_idx_when_sorting(self):
        """ Check that plotted data gets updated when changing sorting order.
        """
        df = self.df
        model = self.analyzer_klass(source_df=df)
        self.assertEqual(model.sort_by_col, "index")

        model.selected_idx = [0]
        self.assertEqual(model.data_selected, [df.index[0]])

        with self.assertTraitChanges(model, "selected_idx"):
            with self.assertTraitDoesNotChange(model, "data_selected"):
                model.sort_by_col = "index" + REVERSED_SUFFIX

        self.assertEqual(model.selected_idx, [len(df)-1])

    def test_shuffle(self):
        df = self.df
        model = self.analyzer_klass(source_df=df)
        index0 = list(model.filtered_df.index)
        model.shuffle_filtered_df()
        index1 = list(model.filtered_df.index)
        self.assertNotEqual(index0, index1)
        self.assertEqual(index0, sorted(index1))

    # Helper methods ----------------------------------------------------------

    def create_plot_manager(self, df=None, n_plots=0):
        if df is None:
            df = self.df

        plot_manager = DataFramePlotManager(data_source=df)
        if n_plots > 0:
            config1 = ScatterPlotConfigurator(data_source=df,
                                              plot_title="Plot1")
            config1.x_col_name = "a"
            config1.y_col_name = "b"
            plot_manager._add_new_plot(config1)

        if n_plots > 1:
            config2 = ScatterPlotConfigurator(data_source=df,
                                              plot_title="Plot2")
            config2.x_col_name = "a"
            config2.y_col_name = "b"
            plot_manager._add_new_plot(config2)

        return plot_manager


class DisplayingDataFrameAnalyzer(UnittestTools):

    def setUp(self):
        self.df = pd.DataFrame({"a": range(11), "b": range(0, 110, 10),
                                "c": list("abcdeabcaab")})
        self.df2 = pd.DataFrame({"a": [1, 2, 3, 4, 5],
                                 "b": [10, 15, 20, 15, 10]})

    def test_show_selected_only(self):
        df = self.df
        analyzer = self.analyzer_klass(source_df=df)
        with self.assertTraitChanges(analyzer, "displayed_df"):
            analyzer.show_selected_only = True

        self.assertEqual(len(analyzer.displayed_df), 0)
        analyzer.selected_idx.append(0)
        self.assertEqual(len(analyzer.displayed_df), 1)
        self.assertEqual(analyzer.displayed_df.index.tolist(), [df.index[0]])
        analyzer.selected_idx.append(3)
        analyzer.selected_idx.append(2)
        self.assertEqual(len(analyzer.displayed_df), 3)
        self.assertEqual(analyzer.displayed_df.index.tolist(),
                         [df.index[0], df.index[3], df.index[2]])

        with self.assertTraitChanges(analyzer, "displayed_df"):
            analyzer.show_selected_only = False

        self.assertIs(analyzer.displayed_df, analyzer.filtered_df)

    def test_truncating_data(self):
        df = self.df
        analyzer = self.analyzer_klass(source_df=df, num_displayed_rows=100)
        self.assertIs(analyzer.displayed_df, analyzer.filtered_df)

        with self.assertTraitChanges(analyzer, "displayed_df"):
            analyzer.num_displayed_rows = 5

        self.assertIsNot(analyzer.displayed_df, analyzer.filtered_df)
        self.assertEqual(len(analyzer.displayed_df), 5)
        self.assertEqual(analyzer.displayed_df.a.tolist(), [0, 1, 2, 3, 4])
        self.assertEqual(analyzer.displayed_df.b.tolist(), [0, 10, 20, 30, 40])

        with self.assertTraitChanges(analyzer, "displayed_df"):
            analyzer.num_displayed_rows = 0

        self.assertIs(analyzer.displayed_df, analyzer.filtered_df)

    def test_truncating_data_non_trivial_index(self):
        import pdb ; pdb.set_trace()
        df = self.df
        df.index = [1, 2, 5, 6, 3, 8, 10, 12, 4, 13, 14]
        analyzer = self.analyzer_klass(source_df=df, num_displayed_rows=100,
                                       data_sorted=False)
        self.assertIs(analyzer.displayed_df, analyzer.filtered_df)

        with self.assertTraitChanges(analyzer, "displayed_df"):
            analyzer.num_displayed_rows = 5

        self.assertIsNot(analyzer.displayed_df, analyzer.filtered_df)
        self.assertEqual(len(analyzer.displayed_df), 5)
        # Truncation done correctly:
        self.assertEqual(analyzer.displayed_df.index.tolist(), [1, 2, 5, 6, 3])
        self.assertEqual(analyzer.displayed_df.a.tolist(), [0, 1, 2, 3, 4])
        self.assertEqual(analyzer.displayed_df.b.tolist(), [0, 10, 20, 30, 40])
