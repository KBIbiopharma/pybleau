from unittest import TestCase

import pandas as pd
from app_common.apptools.testing_utils import assert_obj_gui_works
from pandas import DataFrame
from traits.testing.unittest_tools import UnittestTools

from pybleau.app.ui.filter_expression_editor import \
    FilterExpressionEditorView, COPY_TO_CLIPBOARD


class TestFilterExpressionEditor(TestCase, UnittestTools):
    def setUp(self):
        self.df = DataFrame(
            {
                "a": [1, 2, 4, 5],
                "b": list("zxyh"),
                "c_column": list("test"),
                "d": ["1 alpha", "MM_TT_BB_03-92", "2zeta", "spacE Bar"],
                "e_column": ["03_06 04_STANDARD.name",
                             "about this", "._ a93", "d!@#.$% ^&*()_+d"],
                "bool_col": [True, False, True, True],
                "datetime_col": pd.date_range('1/1/2011', periods=4, freq='H')
            },
            index=[0, 1, 3, 4]
        )

    def test_bring_up_filter_expression(self):
        view = FilterExpressionEditorView(expr="a == 4",
                                          source_df=self.df)
        assert_obj_gui_works(view)

    def test_click_type_changed(self):
        view = FilterExpressionEditorView(expr="a == 4",
                                          source_df=self.df)
        self.assertTrue(view.auto_append)
        with self.assertTraitChanges(view, "auto_append"):
            view.click_type = COPY_TO_CLIPBOARD
        self.assertFalse(view.auto_append)

    def test_edit_iniaialized_True(self):
        view = FilterExpressionEditorView(expr="a == 4",
                                          source_df=self.df)
        self.assertTrue(view.is_initialized)

    def test_include_col_not_in_dataframe(self):
        with self.assertRaises(AttributeError):
            FilterExpressionEditorView(expr="a == 4",
                                       source_df=self.df,
                                       included_cols=["NON-EXISTANT"])

    def test_source_df_is_empty(self):
        with self.assertRaises(AttributeError):
            FilterExpressionEditorView(expr="a == 4", source_df=DataFrame())

    def test_empty_included_columns_still_makes_name_traits(self):
        view = FilterExpressionEditorView(expr="a == 4",
                                          source_df=self.df)
        # still makes buttons for column names
        expected_trait_names = [f"trait_{n}" for n in sorted(self.df)]
        col_name_traits = view._scrollable_column_names.trait_names()
        self.assertTrue(set(expected_trait_names).issubset(col_name_traits))

    def test_scroll_traits_made_for_included_cols(self):
        view = FilterExpressionEditorView(source_df=self.df,
                                          included_cols=["b", "c_column"])
        expected_scrolls = [f"{view.traited_names[col]}_col_scroll_list"
                            for col in view.included_cols]
        self.assertTrue(set(expected_scrolls).issubset(view.trait_names()))

    def test_filter_button_clicked_with_append(self):
        view = FilterExpressionEditorView(expr="a != 4", source_df=self.df,
                                          included_cols=["d", "c_column"])
        # these trait names are dynamically created by the view, so they do
        # not exist in the normal sense in the list of attributes.
        view.trait_d_col_scroll_list.trait_2zeta = True
        self.assertEqual(view.expr, 'a != 4"2zeta"')
        view._scrollable_column_names.trait_c_column = True
        self.assertEqual(view.expr, 'a != 4"2zeta"c_column')

    def test_filter_button_clicked_without_append(self):
        view = FilterExpressionEditorView(expr="a != 4", source_df=self.df,
                                          included_cols=["d", "c_column"])
        view.click_type = COPY_TO_CLIPBOARD
        # these trait names are dynamically created by the view, so they do
        # not exist in the normal sense in the list of attributes.
        view.trait_d_col_scroll_list.trait_2zeta = True
        self.assertEqual(view.expr, "a != 4")
        view._scrollable_column_names.trait_c_column = True
        self.assertEqual(view.expr, "a != 4")
