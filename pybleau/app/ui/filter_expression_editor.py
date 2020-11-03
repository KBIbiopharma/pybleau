from operator import itemgetter

from app_common.std_lib.str_utils import sanitize_string
from pandas import DataFrame
from pyface.action.api import StatusBarManager
from traits.api import HasStrictTraits, Instance, List, Button, Bool, Str, Any
from traits.trait_types import Dict
from traitsui.api import VGroup, Item, OKCancelButtons, View, Tabbed, HSplit
from traitsui.ui_traits import StatusItem


class FilterExpressionEditorView(HasStrictTraits):
    """ Provides a resizeable edit view of the filter string (or any string).
    """

    #: Expression representing the dataframe filter
    exp = Str

    #: Dataframe upon which filter will operate
    source_df = Instance(DataFrame)

    #: Class to use to create TraitsUI window to open controls
    view_klass = Any(View)

    #: column buttons
    column_buttons = List

    #: flag describing the initialization status of this instance
    edit_initialized = Bool(False)

    #: Selected columns which should have their own tab
    included_cols = List

    status_bar = Instance(StatusBarManager)

    status_bar_message = Str

    #: Dictionary of translated trait names with original names as keys
    traited_names = Dict

    #: Dictionary of original names with translated trait names as keys
    original_names = Dict

    included_col_values = Dict

    def _create_trait_translators(self):
        # create for each column name
        self._add_values_to_translators(sorted(self.source_df))
        # create for each value in the included columns
        for column in self.included_cols:
            column_values = list(self.source_df[column].unique())
            self.included_col_values[column] = column_values
            self._add_values_to_translators(column_values)

    def _add_values_to_translators(self, column_values):
        for name in column_values:
            trait_name = f"trait_{sanitize_string(name)}"
            self.traited_names[name] = trait_name
            self.original_names[trait_name] = name

    def __init__(self, source_df: DataFrame, **traits):
        super(FilterExpressionEditorView, self).__init__(**traits)
        self.source_df = source_df
        if "included_cols" in traits:
            # if any of the specified columns have value dtypes that are
            # numerical, then throw an error
            self.included_cols = traits["included_cols"]
        self._create_trait_translators()
        self._create_button_traits_from_column_names()
        self._create_button_traits_from_column_values()
        self.edit_initialized = True

    def traits_view(self):
        col_names = sorted(self.source_df)
        col_traited_names = list(itemgetter(*col_names)(self.traited_names))
        col_name_bttns = [Item(n, show_label=False) for n in col_traited_names]
        included_column_button_list = self._create_included_col_view_tabs()
        view = self.view_klass(
            HSplit(
                Tabbed(
                    VGroup(
                        *col_name_bttns,
                        label="Column Names",
                        scrollable=True,
                    ),
                    *included_column_button_list,
                ),
                VGroup(
                    Item("exp", style="custom", show_label=False, width=450),
                    show_border=True,
                ),
            ),
            resizable=True,
            buttons=OKCancelButtons,
            title="Edit the filter...",
            statusbar=StatusItem(name="status_bar_message")
        )
        return view

    def _create_included_col_view_tabs(self):
        tab_list = []
        for column in self.included_col_values.keys():
            uniques = self.included_col_values[column]
            value_bttns = [Item(self.traited_names[name], show_label=False)
                           for name in uniques]
            new_group = VGroup(
                *value_bttns,
                label=column,
                scrollable=True
            )
            tab_list.append(new_group)
        return tab_list

    def _create_button_traits_from_column_values(self):
        for cat_item in self.included_cols:
            column_values = [str(x) for x in self.source_df[cat_item].unique()]
            self._create_button_traits(column_values)

    def _create_button_traits_from_column_names(self):
        self._create_button_traits(sorted(self.source_df))

    def _create_button_traits(self, names):
        for name in names:
            trait_name = self.traited_names[name]
            self.add_trait(trait_name, Button(name))
            self.observe(self.filter_button_clicked, trait_name)

    def filter_button_clicked(self, event):
        if not self.edit_initialized:
            return
        from pyface.clipboard import Clipboard
        cb = Clipboard()
        copied_value = self.original_names[event.name]
        if self.original_names[event.name] in self.source_df.columns.tolist():
            cb.text_data = copied_value
        else:
            cb.text_data = f'"{copied_value}"'
        self.status_bar_message = f"'{copied_value}' copied to the clipboard."

    def _status_bar_default(self):
        return StatusBarManager(messages=[self.status_bar_message],
                                text_color="black")


if __name__ == "__main__":
    test_df = DataFrame(
        {
            "a": [1, 2, 4, 5],
            "b_ff": list("zxyh"),
            "c": list("test"),
            "d": ["1 alpha", "MM_TT_BB_03-92", "2zeta", "kAPPa pappa"],
            "e_column": ["03_06 04_STANDARD.name",
                         "about this", "._ a93", "d!@#.$% ^&*()_+d"]
        },
        index=[0, 1, 3, 4]
    )
    test = FilterExpressionEditorView(exp="a == 3", source_df=test_df,
                                      included_cols=["d", "e_column", "b_ff"])
    test.configure_traits()
