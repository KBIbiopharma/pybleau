import logging
import numpy as np
import pandas as pd
from copy import copy

from pyface.api import warning
from traits.api import Any, Bool, Button, cached_property, Dict, Either, Enum,\
    Instance, Int, List, on_trait_change, Property, Set, Str
import traitsui
from traitsui.api import ButtonEditor, CheckListEditor, HGroup, HSplit, \
    InstanceEditor, Item, Label, ModelView, OKButton, Spring, Tabbed, VGroup, \
    View, VSplit
from traitsui.ui_editors.data_frame_editor import DataFrameEditor

from app_common.traitsui.common_traitsui_groups import make_window_title_group
from app_common.pyface.ui.extra_file_dialogs import request_csv_file
from app_common.std_lib.filepath_utils import open_file

from pybleau.app.model.dataframe_analyzer import DataFrameAnalyzer
try:
    from pybleau.app.ui.dataframe_plot_manager_view import \
        DataFramePlotManager, DataFramePlotManagerView
except ImportError:
    DataFramePlotManager = object
    DataFramePlotManagerView = object

from pybleau.app.tools.filter_expression_manager import FilterExpression, \
    FilterExpressionManager

logger = logging.getLogger(__name__)

DEFAULT_FONT = 'Courier'


class DataFrameAnalyzerView(ModelView):
    """ Flexible ModelView class for a DataFrameAnalyzer.

    The view is built using many methods to build each component of the view so
    it can easily be subclassed and customized.

    TODO: add traits events to pass update/refresh notifications to the
    DFEditors once we have updated TraitsUI.

    TODO: Add traits events to receive notifications that a column/row was
    clicked/double-clicked.
    """
    #: Model being viewed
    model = Instance(DataFrameAnalyzer)

    #: Selected list of data columns to display and analyze
    visible_columns = List(Str)

    #: Complete list of data columns to display and analyze
    all_data_columns = List(Str)

    #: Check box to hide/show what stats are included in the summary DF
    show_summary_controls = Bool

    #: Check box to hide/show what columns to analyze (panel when few columns)
    show_column_controls = Bool

    #: Open control for what columns to analyze (popup when many columns)
    open_column_controls = Button("Show column control")

    #: Button to launch the plotter tool when plotter_layout=popup
    plotter_launcher = Button("Launch Plot Tool")

    # Plotting tool attributes ------------------------------------------------

    #: Does the UI expose a DF plotter?
    include_plotter = Bool

    #: Plot manager view to display. Ignored if include_plotter is False.
    plotter = Instance(DataFramePlotManagerView)

    # Styling and branding attributes -----------------------------------------

    #: String describing the font to use, or dict mapping column names to font
    fonts = Either(Str, Dict)

    #: Name of the font to use if same across all columns
    font_name = Str(DEFAULT_FONT)

    #: Size of the font to use if same across all columns
    font_size = Int(14)

    #: Number of digits to display in the tables
    display_precision = Int(-1)

    #: Formatting to use to include
    formats = Either(Str, Dict)

    #: UI title for the Data section
    data_section_title = Str("Data")

    #: Exploration group label: visible only when plotter_layout="Tabbed"
    exploration_group_label = Str("Exploration Tools")

    #: PLotting group label: visible only when plotter_layout="Tabbed"
    plotting_group_label = Str("Plotting Tools")

    #: UI title for the data summary section
    summary_section_title = Str

    #: UI title for the categorical data summary section
    cat_summary_section_title = Str("Categorical data summary")

    #: UI title for the column list section
    column_list_section_title = Str("Column content")

    #: UI title for the summary content section
    summary_content_section_title = Str("Summary content")

    #: UI summary group (tab) name for numerical columns
    num_summary_group_name = Str("Numerical data")

    #: UI summary group (tab) name for categorical columns
    cat_summary_group_name = Str("Categorical data")

    #: Text to display in title bar of the containing window (if applicable)
    app_title = Str("Tabular Data Analyzer")

    #: How to place the plotter tool with respect to the exploration tool?
    plotter_layout = Enum("Tabbed", "HSplit", "VSplit", "popup")

    #: DFPlotManager traits to customize it
    plotter_kw = Dict

    #: Message displayed below the table if truncated
    truncation_msg = Property(Str, depends_on="model.num_displayed_rows")

    # Functionality controls --------------------------------------------------

    #: Button to shuffle the order of the filtered data
    shuffle_button = Button("Shuffle")

    show_shuffle_button = Bool(True)

    #: Button to display more rows in the data table
    show_more_button = Button

    #: Button to display all rows in the data table
    show_all_button = Button("Show All")

    #: Apply button for the filter if model not in auto-apply mode
    apply_filter_button = Button("Apply")

    #: Whether to support saving, and loading filters
    filter_manager = Bool

    #: Button to launch filter expression manager to load an existing filter
    load_filter_button = Button("Load...")

    #: Button to save current filter expression
    save_filter_button = Button("Save")

    #: Button to launch filter expression manager to modify saved filters
    manage_filter_button = Button("Manage...")

    #: List of saved filtered expressions
    _known_expr = Property(Set, depends_on="model.known_filter_exps")

    #: Show the bottom panel with the summary of the data:
    _show_summary = Bool(True)

    allow_show_summary = Bool(True)

    #: Button to export the analyzed data to a CSV file
    data_exporter = Button("Export Data to CSV")

    #: Button to export the summary data to a CSV file
    summary_exporter = Button("Export Summary to CSV")

    # Detailed configuration traits -------------------------------------------

    #: View class to use. Modify to customize.
    view_klass = Any(View)

    #: Width of the view
    view_width = Int(1100)

    #: Height of the view
    view_height = Int(700)

    #: Width of the filter box
    filter_item_width = Int(400)

    max_names_per_column = Int(12)

    truncation_msg_template = Str("Table truncated at {} rows")

    warn_if_sel_hidden = Bool(True)

    hidden_selection_msg = Str

    # Implementation details --------------------------------------------------

    #: Evaluate number of columns to select panel or popup column control
    _many_columns = Property(Bool, depends_on="all_data_columns")

    #: Popped-up UI to control the visible columns
    _control_popup = Any

    #: Collected traitsUI editors for both the data DF and the summary DF
    _df_editors = Dict

    # HasTraits interface -----------------------------------------------------

    def __init__(self, **traits):
        if "model" in traits and isinstance(traits["model"], pd.DataFrame):
            traits["model"] = DataFrameAnalyzer(source_df=traits["model"])

        super(DataFrameAnalyzerView, self).__init__(**traits)

        if self.include_plotter:
            # If a plotter view was specified, its model should be in the
            # model's list of plot managers:
            if self.plotter.model not in self.model.plot_manager_list:
                self.model.plot_manager_list.append(self.plotter.model)

    def traits_view(self):
        """ Putting the view components together.

        Each component of the view is built in a separate method so it can
        easily be subclassed and customized.
        """
        # Construction of view groups -----------------------------------------

        data_group = self.view_data_group_builder()
        column_controls_group = self.view_data_control_group_builder()
        summary_group = self.view_summary_group_builder()
        summary_controls_group = self.view_summary_control_group_builder()
        cat_summary_group = self.view_cat_summary_group_builder()
        plotter_group = self.view_plotter_group_builder()

        button_content = [
            Item("data_exporter", show_label=False),
            Spring(),
            Item("summary_exporter", show_label=False)
        ]

        if self.plotter_layout == "popup":
            button_content += [
                Spring(),
                Item("plotter_launcher", show_label=False)
            ]

        button_group = HGroup(*button_content)

        # Organization of item groups -----------------------------------------

        # If both types of summary are available, display as Tabbed view:
        if summary_group is not None and cat_summary_group is not None:
            summary_container = Tabbed(
                HSplit(
                    summary_controls_group,
                    summary_group,
                    label=self.num_summary_group_name
                ),
                cat_summary_group,
            )
        elif cat_summary_group is not None:
            summary_container = cat_summary_group
        else:
            summary_container = HSplit(
                summary_controls_group,
                summary_group
            )

        # Allow to hide all summary information:
        summary_container.visible_when = "_show_summary"

        exploration_groups = VGroup(
            VSplit(
                HSplit(
                    column_controls_group,
                    data_group,
                ),
                summary_container
            ),
            button_group,
            label=self.exploration_group_label
        )

        if self.include_plotter and self.plotter_layout != "popup":
            layout = getattr(traitsui.api, self.plotter_layout)
            groups = layout(
                exploration_groups,
                plotter_group
            )
        else:
            groups = exploration_groups

        view = self.view_klass(
            groups,
            resizable=True,
            title=self.app_title,
            width=self.view_width, height=self.view_height
        )
        return view

    # Traits view building methods --------------------------------------------

    def view_data_group_builder(self):
        """ Build view element for the Data display
        """
        editor_kw = dict(show_index=True, columns=self.visible_columns,
                         fonts=self.fonts, formats=self.formats)
        data_editor = DataFrameEditor(selected_row="selected_idx",
                                      multi_select=True, **editor_kw)

        filter_group = HGroup(
            Item("model.filter_exp", label="Filter",
                 width=self.filter_item_width),
            Item("apply_filter_button", show_label=False,
                 visible_when="not model.filter_auto_apply"),
            Item("save_filter_button", show_label=False,
                 enabled_when="model.filter_exp not in _known_expr",
                 visible_when="filter_manager"),
            Item("load_filter_button", show_label=False,
                 visible_when="filter_manager"),
            Item("manage_filter_button", show_label=False,
                 visible_when="filter_manager"),
        )

        truncated = ("len(model.displayed_df) < len(model.filtered_df) and "
                     "not model.show_selected_only")
        more_label = "Show {} More".format(self.model.num_display_increment)
        display_control_group = HGroup(
            Item("model.show_selected_only", label="Selected rows only"),
            Item("truncation_msg", style="readonly", show_label=False,
                 visible_when=truncated),
            Item("show_more_button", editor=ButtonEditor(label=more_label),
                 show_label=False, visible_when=truncated),
            Item("show_all_button", show_label=False,
                 visible_when=truncated),
        )

        data_group = VGroup(
            make_window_title_group(self.data_section_title, title_size=3,
                                    include_blank_spaces=False),
            HGroup(
                Item("model.sort_by_col", label="Sort by"),
                Item("shuffle_button", show_label=False,
                     visible_when="show_shuffle_button"),
                Spring(),
                filter_group
            ),
            HGroup(
                Item("model.displayed_df", editor=data_editor,
                     show_label=False),
            ),
            HGroup(
                Item("show_column_controls",
                     label="\u2190 Show column control",
                     visible_when="not _many_columns"),
                Item("open_column_controls", show_label=False,
                     visible_when="_many_columns"),
                Spring(),
                Item("_show_summary", label=u'\u2193 Show summary',
                     visible_when="allow_show_summary"),
                Spring(),
                display_control_group
            ),
            show_border=True
        )
        return data_group

    def view_data_control_group_builder(self, force_visible=False):
        """ Build view element for the Data column control.

        Parameters
        ----------
        force_visible : bool
            Controls visibility of the created group. Don't force for the group
            embedded in the global view, but force it when opened as a popup.
        """
        num_cols = 1 + len(self.all_data_columns) // self.max_names_per_column

        column_controls_group = VGroup(
            make_window_title_group(self.column_list_section_title,
                                    title_size=3, include_blank_spaces=False),
            Item("visible_columns", show_label=False,
                 editor=CheckListEditor(values=self.all_data_columns,
                                        cols=num_cols),
                 # The custom style allows to control a list of options rather
                 # than having a checklist editor for a single value:
                 style='custom'),
            show_border=True
        )
        if force_visible:
            column_controls_group.visible_when = ""
        else:
            column_controls_group.visible_when = "show_column_controls"

        return column_controls_group

    def view_summary_group_builder(self):
        """ Build view element for the numerical data summary display
        """
        editor_kw = dict(show_index=True, columns=self.visible_columns,
                         fonts=self.fonts, formats=self.formats)
        summary_editor = DataFrameEditor(**editor_kw)

        summary_group = VGroup(
            make_window_title_group(self.summary_section_title, title_size=3,
                                    include_blank_spaces=False),
            Item("model.summary_df", editor=summary_editor, show_label=False,
                 visible_when="len(model.summary_df) != 0"),
            # Workaround the fact that the Label's visible_when is buggy:
            # encapsulate it into a group and add the visible_when to the group
            HGroup(
                Label("No data columns with numbers were found."),
                visible_when="len(model.summary_df) == 0"
            ),
            HGroup(
                Item("show_summary_controls"),
                Spring(),
                visible_when="len(model.summary_df) != 0"
            ),
            show_border=True,
        )
        return summary_group

    def view_summary_control_group_builder(self):
        """ Build view element for the column controls for data summary.
        """
        summary_controls_group = VGroup(
            make_window_title_group(self.summary_content_section_title,
                                    title_size=3, include_blank_spaces=False),
            Item("model.summary_index", show_label=False),
            visible_when="show_summary_controls",
            show_border=True
        )

        return summary_controls_group

    def view_cat_summary_group_builder(self):
        """ Build view element for the categorical data summary display.
        """
        editor_kw = dict(show_index=True, fonts=self.fonts,
                         formats=self.formats)
        summary_editor = DataFrameEditor(**editor_kw)

        cat_summary_group = VGroup(
            make_window_title_group(self.cat_summary_section_title,
                                    title_size=3, include_blank_spaces=False),
            Item("model.summary_categorical_df", editor=summary_editor,
                 show_label=False,
                 visible_when="len(model.summary_categorical_df)!=0"),
            # Workaround the fact that the Label's visible_when is buggy:
            # encapsulate it into a group and add the visible_when to the group
            HGroup(
                Label("No data columns with numbers were found."),
                visible_when="len(model.summary_categorical_df)==0"
            ),
            show_border=True, label=self.cat_summary_group_name
        )
        return cat_summary_group

    def view_plotter_group_builder(self):
        """ Build view element for the plotter tool.
        """
        plotter_group = VGroup(
            Item("plotter", editor=InstanceEditor(), show_label=False,
                 style="custom"),
            label=self.plotting_group_label
        )
        return plotter_group

    # Public interface --------------------------------------------------------

    def destroy(self):
        """ Clean up resources.
        """
        if self._control_popup:
            self._control_popup.dispose()

    # Traits listeners --------------------------------------------------------

    def _open_column_controls_fired(self):
        """ Pop-up a new view on the column list control.
        """
        if self._control_popup and self._control_popup.control:
            # If there is an existing window, bring it in focus:
            # Discussion: https://stackoverflow.com/questions/2240717/in-qt-how-do-i-make-a-window-be-the-current-window  # noqa
            self._control_popup.control._mw.activateWindow()
            return

        # Before viewing self with a simplified view, make sure the original
        # view editors are collected so they can be modified when the controls
        # are used:
        if not self._df_editors:
            self._collect_df_editors()

        view = self.view_klass(
            self.view_data_control_group_builder(force_visible=True),
            buttons=[OKButton],
            width=600, resizable=True,
            title="Control visible columns"
        )
        # WARNING: this will modify the info object the view points to!
        self._control_popup = self.edit_traits(view=view, kind="live")

    def _shuffle_button_fired(self):
        self.model.shuffle_filtered_df()

    def _apply_filter_button_fired(self):
        self.model.recompute_filtered_df()

    def _manage_filter_button_fired(self):
        """ TODO: review if replaceing the copy by a deepcopy or removing the
        copy altogether would help traits trigger listeners correctly
        """

        # Make a copy of the list of filters so the model can listen to changes
        # even if only a field of an existing filter is modified:
        filter_manager = FilterExpressionManager(
            known_filter_exps=copy(self.model.known_filter_exps),
            mode="manage", view_klass=self.view_klass
        )
        ui = filter_manager.edit_traits(kind="livemodal")
        if ui.result:
            # FIXME: figure out why this simpler assignment doesn't trigger the
            # traits listener on the model when changing a FilterExpression
            # attribute:
            # self.model.known_filter_exps = filter_manager.known_filter_exps

            self.model.known_filter_exps = [
                FilterExpression(name=e.name, expression=e.expression) for e in
                filter_manager.known_filter_exps
            ]

    def _load_filter_button_fired(self):
        filter_manager = FilterExpressionManager(
            known_filter_exps=self.model.known_filter_exps,
            mode="load", view_klass=self.view_klass
        )
        ui = filter_manager.edit_traits(kind="livemodal")
        if ui.result:
            selection = filter_manager.selected_expression
            self.model.filter_exp = selection.expression

    def _save_filter_button_fired(self):
        exp = self.model.filter_exp
        if exp in [e.expression for e in self.model.known_filter_exps]:
            return

        expr = FilterExpression(name=exp, expression=exp)
        self.model.known_filter_exps.append(expr)

    def _show_more_button_fired(self):
        self.model.num_displayed_rows += self.model.num_display_increment

    def _show_all_button_fired(self):
        self.model.num_displayed_rows = -1

    @on_trait_change("model:selected_data_in_plotter_updated", post_init=True)
    def warn_if_selection_hidden(self):
        """ Pop up warning msg if some of the selected rows aren't displayed.
        """
        if not self.warn_if_sel_hidden:
            return

        if not self.model.selected_idx:
            return

        truncated = len(self.model.displayed_df) < len(self.model.filtered_df)
        max_displayed = self.model.displayed_df.index.max()
        some_selection_hidden = max(self.model.selected_idx) > max_displayed
        if truncated and some_selection_hidden:
            warning(None, self.hidden_selection_msg, "Hidden selection")

    @on_trait_change("visible_columns[]", post_init=True)
    def update_filtered_df_on_columns(self):
        """ Just show the columns that are set to visible.

        Notes
        -----
        We are not modifying the filtered data because if we remove a column
        and then bring it back, the adapter breaks because it is missing data.
        Breakage happen when removing a column if the model is changed first,
        or when bring a column back if the adapter column list is changed
        first.
        """
        if not self.info.initialized:
            return

        if not self._df_editors:
            self._collect_df_editors()

        # Rebuild the column list (col name, column id) for the tabular
        # adapter:
        all_visible_cols = [(col, col) for col in self.visible_columns]

        df = self.model.source_df
        cat_dtypes = self.model.categorical_dtypes
        summarizable_df = df.select_dtypes(exclude=cat_dtypes)
        summary_visible_cols = [(col, col) for col in self.visible_columns
                                if col in summarizable_df.columns]

        for df_name, cols in zip(["displayed_df", "summary_df"],
                                 [all_visible_cols, summary_visible_cols]):
            df = getattr(self.model, df_name)
            index_name = df.index.name
            if index_name is None:
                index_name = ''

            # This grabs the corresponding _DataFrameEditor (not the editor
            # factory) which has access to the adapter object:
            editor = self._df_editors[df_name]
            editor.adapter.columns = [(index_name, 'index')] + cols

    def _collect_df_editors(self):
        for df_name in ["displayed_df", "summary_df"]:
            try:
                # This grabs the corresponding _DataFrameEditor (not the editor
                # factory) which has access to the adapter object:
                self._df_editors[df_name] = getattr(self.info, df_name)
            except Exception as e:
                msg = "Error trying to collect the tabular adapter: {}"
                logger.error(msg.format(e))

    def _plotter_launcher_fired(self):
        """ Pop up plot manager view. Only when self.plotter_layout="popup".
        """
        self.plotter.edit_traits(kind="livemodal")

    def _data_exporter_fired(self):
        filepath = request_csv_file(action="save as")
        if filepath:
            self.model.filtered_df.to_csv(filepath)
            open_file(filepath)

    def _summary_exporter_fired(self):
        filepath = request_csv_file(action="save as")
        if filepath:
            self.model.summary_df.to_csv(filepath)
            open_file(filepath)

    # Traits property getters/setters -----------------------------------------

    def _get__known_expr(self):
        return {e.expression for e in self.model.known_filter_exps}

    @cached_property
    def _get_truncation_msg(self):
        num_displayed_rows = self.model.num_displayed_rows
        return self.truncation_msg_template.format(num_displayed_rows)

    @cached_property
    def _get__many_columns(self):
        return len(self.all_data_columns) > 2 * self.max_names_per_column

    # Traits initialization methods -------------------------------------------

    def _plotter_default(self):
        if self.include_plotter:
            if self.model.plot_manager_list:
                if len(self.model.plot_manager_list) > 1:
                    num_plotters = len(self.model.plot_manager_list)
                    msg = "Model contains {} plot manager, but only " \
                          "initializing the Analyzer view with the first " \
                          "plot manager available.".format(num_plotters)
                    logger.warning(msg)

                plot_manager = self.model.plot_manager_list[0]
            else:
                plot_manager = DataFramePlotManager(
                    data_source=self.model.filtered_df,
                    source_analyzer=self.model,
                    **self.plotter_kw
                )

            view = DataFramePlotManagerView(model=plot_manager,
                                            view_klass=self.view_klass)
            return view

    def _formats_default(self):
        if self.display_precision < 0:
            return '%s'
        else:
            formats = {}
            float_format = '%.{}g'.format(self.display_precision)
            for col in self.model.source_df.columns:
                col_dtype = self.model.source_df.dtypes[col]
                if np.issubdtype(col_dtype, np.number):
                    formats[col] = float_format
                else:
                    formats[col] = '%s'

            return formats

    def _visible_columns_default(self):
        return self.all_data_columns

    def _all_data_columns_default(self):
        return self.model.source_df.columns.tolist()

    def _hidden_selection_msg_default(self):
        msg = "The displayed data is truncated and some of the selected " \
              "rows isn't displayed in the data table."
        return msg

    def _summary_section_title_default(self):
        if len(self.model.summary_categorical_df) == 0:
            return "Data summary"
        else:
            return "Numerical data summary"

    def _fonts_default(self):
        return "{} {}".format(self.font_name, self.font_size)


if __name__ == "__main__":
    from pandas import DataFrame
    from numpy import random

    df = DataFrame({"a": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                    "b": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
                    "c": random.randn(16),
                    "d": list("abcdefghijklmnop")},
                   dtype=float)
    df.index.name = "BALH"

    summarizer = DataFrameAnalyzer(source_df=df, num_displayed_rows=5)
    print(summarizer.compute_summary())

    view = DataFrameAnalyzerView(model=summarizer, include_plotter=True,
                                 display_precision=5,
                                 plotter_layout="HSplit")
    view.configure_traits()
