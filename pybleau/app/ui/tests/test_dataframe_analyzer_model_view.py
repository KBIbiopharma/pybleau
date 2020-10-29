import os
from sys import platform
from unittest import TestCase, skipIf
from unittest.mock import patch, MagicMock

from pandas import DataFrame
from pandas.testing import assert_frame_equal

from pybleau.app.tools.filter_expression_editor import \
    FilterExpressionEditorView

try:
    import kiwisolver  # noqa
    KIWI_AVAILABLE = True
except ImportError:
    KIWI_AVAILABLE = False

BACKEND_AVAILABLE = os.environ.get("ETS_TOOLKIT", "qt4") != "null"

if KIWI_AVAILABLE and BACKEND_AVAILABLE:
    from app_common.std_lib.sys_utils import IS_LINUX, IS_OSX
    from app_common.apptools.testing_utils import temp_bringup_ui_for
    from pybleau.app.api import DataFrameAnalyzer, DataFrameAnalyzerView, \
        DataFramePlotManager, DataFramePlotManagerView

FONT_DEFAULT_SIZE = {"darwin": 13,
                     "linux": 9,
                     "win32": 8}

msg = "No UI backend to paint into or missing kiwisolver package"


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDataFrameAnalyzerView(TestCase):
    def setUp(self):
        self.df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]})
        self.analyzer = DataFrameAnalyzer(source_df=self.df)

    def test_bring_up_analyzer(self):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=False)
        with temp_bringup_ui_for(view):
            pass

    def test_create_analyzer_from_df(self):
        view = DataFrameAnalyzerView(model=self.df,
                                     include_plotter=False)
        assert_frame_equal(view.model.source_df, self.df)

    def test_bring_up_analyzer_with_plotter(self):
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        with temp_bringup_ui_for(view):
            pass

    def test_analyzer_with_plotter_in_model(self):
        # Make sure that if a view is created with a model that has a plotter,
        # that's what is used to build the view rather than create a new one:
        plot_manager = DataFramePlotManager(source_analyzer=self.analyzer)
        self.analyzer.plot_manager_list.append(plot_manager)
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        self.assertIs(view.plotter.model, plot_manager)

    def test_bring_up_column_controls_as_popup(self):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=False)
        with temp_bringup_ui_for(view):
            self.assertIsNone(view._control_popup)
            view.open_column_controls = True
            self.assertIsNotNone(view._control_popup)
            self.assertIn("displayed_df", view._df_editors)
            self.assertIn("summary_df", view._df_editors)

    def test_bring_up_with_categorical_data(self):
        df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10],
                        "c": list("ababa")})
        analyzer = DataFrameAnalyzer(source_df=df)
        view = DataFrameAnalyzerView(model=analyzer,
                                     include_plotter=False)
        with temp_bringup_ui_for(view):
            pass

        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        with temp_bringup_ui_for(view):
            pass

    def test_bring_up_with_object_df(self):
        df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]},
                       dtype=object)
        analyzer = DataFrameAnalyzer(source_df=df)
        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True)
        with temp_bringup_ui_for(view):
            pass

        view = DataFrameAnalyzerView(model=analyzer, include_plotter=False)
        with temp_bringup_ui_for(view):
            pass

    def test_bring_up_all_layouts(self):
        for layout in ["Tabbed", "HSplit", "VSplit", "popup"]:
            view = DataFrameAnalyzerView(model=self.analyzer,
                                         include_plotter=True,
                                         plotter_layout=layout)
            with temp_bringup_ui_for(view):
                pass

    def test_bring_up_truncated(self):
        self.analyzer.num_displayed_rows = 5
        view = DataFrameAnalyzerView(model=self.analyzer)
        with temp_bringup_ui_for(view):
            pass

    def test_bring_up_column_control(self):
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        with temp_bringup_ui_for(view):
            view.show_column_controls = True

    def test_bring_up_hide_summary(self):
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        with temp_bringup_ui_for(view):
            view._show_summary = False

    @patch.object(DataFrameAnalyzerView, "view_cat_summary_group_builder")
    def test_show_categorical_summary(self, mock):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     show_categorical_summary=False)
        with temp_bringup_ui_for(view):
            self.assertFalse(mock.called)

    def test_change_column_list(self):
        view = DataFrameAnalyzerView(model=self.analyzer)
        init_len = len(view.visible_columns)
        with temp_bringup_ui_for(view):
            view.visible_columns = view.visible_columns[:1]
            self.assertNotEqual(len(view.visible_columns), init_len)

            # Both DFEditor's adapters are modified, now containing only 2
            # columns: the one requested and the index:
            editor = view.info.displayed_df
            self.assertEqual(len(editor.adapter.columns), 2)
            editor = view.info.summary_df
            self.assertEqual(len(editor.adapter.columns), 2)

            # The model data is unchanged:
            self.assertEqual(len(view.model.displayed_df.columns), init_len)
            self.assertEqual(len(view.model.summary_df.columns), init_len)
            self.assertEqual(len(view.model.filtered_df.columns), init_len)
            self.assertEqual(len(view.model.source_df.columns), init_len)

    def test_truncate(self):
        self.analyzer.num_displayed_rows = 3
        self.analyzer.num_display_increment = 1
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=False)
        self.assertEqual(len(self.analyzer.displayed_df), 3)
        view.show_more_button = True
        self.assertEqual(len(self.analyzer.displayed_df), 4)
        view.show_more_button = True
        self.assertEqual(len(self.analyzer.displayed_df), 5)
        # No more rows to add:
        view.show_more_button = True
        self.assertEqual(len(self.analyzer.displayed_df), 5)
        view.show_more_button = True
        self.assertEqual(len(self.analyzer.displayed_df), 5)

    def test_plot_manager_list_with_plotter(self):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=True)
        self.assertIsInstance(view.plotter, DataFramePlotManagerView)
        self.assertEqual(view.model.plot_manager_list, [view.plotter.model])

    def test_plot_manager_list_without_plotter(self):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=False)
        self.assertEqual(view.model.plot_manager_list, [])

    def test_selection_connected(self):
        view = DataFrameAnalyzerView(model=self.analyzer,
                                     include_plotter=True)

        view.model.selected_idx = [0, 2, 1]
        self.assertEqual(view.plotter.model.index_selected, [0, 2, 1])

        view.plotter.model.index_selected.append(3)
        self.assertEqual(view.model.selected_idx, [0, 2, 1, 3])

    def test_apply_filter_button_recomputes_filtered_df_correctly(self):
        self.analyzer.filter_auto_apply = False
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        view.model.filter_exp = "a != 3"
        expected_df = DataFrame({"a": [1, 2, 4, 5], "b": [10, 15, 15, 10]},
                                index=[0, 1, 3, 4])
        try:
            assert_frame_equal(view.model.filtered_df, expected_df)
        except AssertionError:
            pass
        else:
            msg = "The two dataframes should not be equal yet if " \
                  "`filter_auto_apply` is False."
            raise AssertionError(msg)
        view.apply_filter_button = True
        assert_frame_equal(view.model.filtered_df, expected_df)

    @patch.object(FilterExpressionEditorView, "edit_traits")
    def test_edit_filter_button_recomputes_filtered_df_correctly(self, edit):
        self.analyzer.filter_auto_apply = False
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True)
        view.model.filter_exp = "a != 3"
        expected_df = DataFrame({"a": [1, 2, 4, 5], "b": [10, 15, 15, 10]},
                                index=[0, 1, 3, 4])
        ui = MagicMock(result=False)
        edit.return_value = ui
        view._pop_out_filter_button_fired()
        try:
            assert_frame_equal(view.model.filtered_df, expected_df)
        except AssertionError:
            pass
        else:
            msg = "The two dataframes should not be equal yet if " \
                  "`filter_auto_apply` is False."
            raise AssertionError(msg)
        ui.result = True
        view._pop_out_filter_button_fired()
        assert_frame_equal(view.model.filtered_df, expected_df)


@skipIf(not BACKEND_AVAILABLE or not KIWI_AVAILABLE, msg)
class TestDataFrameAnalyzerTableView(TestCase):
    def setUp(self):
        self.df = DataFrame(
            {"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]})
        self.analyzer = DataFrameAnalyzer(source_df=self.df)

    def test_bring_up_control_precision_float_df(self):
        analyzer = self.analyzer
        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     display_precision=3)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.info.displayed_df.adapter.format, "%.3g")

        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     formats="%.5e")
        with temp_bringup_ui_for(view):
            self.assertEqual(view.info.displayed_df.adapter.format, "%.5e")

        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     formats={"a": "%.5e", "b": "%.8f"})
        with temp_bringup_ui_for(view):
            self.assertEqual(view.info.displayed_df.adapter._formats,
                             {"a": "%.5e", "b": "%.8f"})

    def test_bring_up_control_precision_object_df_can_convert_to_float(self):
        df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]},
                       dtype=object)
        analyzer = DataFrameAnalyzer(source_df=df)
        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     display_precision=3)
        with temp_bringup_ui_for(view):
            # Because the DF is set as `dtype=object` but columns can be
            # converted to float:
            self.assertEqual(view.info.displayed_df.adapter.format, "%s")

        df = DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 15, 20, 15, 10]},
                       dtype=object)
        analyzer = DataFrameAnalyzer(source_df=df, convert_source_dtypes=True)
        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     display_precision=3)
        with temp_bringup_ui_for(view):
            # Because the DF is set as `dtype=object` but columns can be
            # converted to float:
            self.assertEqual(view.info.displayed_df.adapter.format, "%.3g")

    def test_bring_up_control_precision_object_df(self):
        df = DataFrame({"a": list('abcd')})
        analyzer = DataFrameAnalyzer(source_df=df)
        view = DataFrameAnalyzerView(model=analyzer, include_plotter=True,
                                     display_precision=3)
        with temp_bringup_ui_for(view):
            # Because the DF is set as `dtype=object`:
            self.assertEqual(view.info.displayed_df.adapter.format, "%s")

    @skipIf(IS_LINUX or IS_OSX, "Linux and OSX's OS overrides this.")
    def test_bring_up_control_fonts(self):
        # FIXME: figure out if we need to remove or improve
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True,
                                     fonts="Roman 24")
        with temp_bringup_ui_for(view):
            self.assert_font_equal(view, "Times New Roman 24")

    def test_bring_up_control_different_fonts(self):
        fonts = {"a": "Roman 24", "b": "Courier 12"}
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True,
                                     fonts=fonts)
        with temp_bringup_ui_for(view):
            self.assertEqual(view.info.displayed_df.adapter._fonts, fonts)

    def test_bring_up_control_font_name(self):
        view = DataFrameAnalyzerView(model=self.analyzer, font_name="Arial")
        with temp_bringup_ui_for(view):
            # Here, size is set by DFAnalyzer:
            self.assert_font_equal(view, "Arial 14")

        view = DataFrameAnalyzerView(model=self.analyzer, fonts="Arial")
        with temp_bringup_ui_for(view):
            # Here, size is set by traitsUI's font handling:
            expected = "Arial " + str(FONT_DEFAULT_SIZE[platform])
            self.assert_font_equal(view, expected)

    def test_bring_up_attempt_non_existent_fonts(self):
        view = DataFrameAnalyzerView(model=self.analyzer, include_plotter=True,
                                     fonts="NON-EXISTENT")
        with temp_bringup_ui_for(view):
            # Here, size is set by traitsUI's font handling:
            expected = "NON-EXISTENT " + str(FONT_DEFAULT_SIZE[platform])
            self.assert_font_equal(view, expected)

    def test_bring_up_control_font_size(self):
        view = DataFrameAnalyzerView(model=self.analyzer, font_size=20)
        with temp_bringup_ui_for(view):
            self.assert_font_equal(view, "Courier 20")

    # Assertion utilities -----------------------------------------------------

    def assert_font_equal(self, view, expected_font):
        exp_font_name = " ".join(expected_font.split()[:-1])
        exp_font_size = expected_font.split()[-1]

        effective_font = view.info.displayed_df.adapter._fonts.toString()
        font_name, font_size = effective_font.split(",")[:2]
        self.assertEqual(font_name, exp_font_name)
        self.assertEqual(font_size, exp_font_size)
