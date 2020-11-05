import logging
from collections import Iterable
from operator import itemgetter

from app_common.std_lib.str_utils import sanitize_string
from pandas import DataFrame
from pyface.action.api import StatusBarManager
from pyface.api import Clipboard
from traits.api import Enum
from traits.api import HasStrictTraits, Instance, List, Button, Bool, Str, \
    Any, Dict
from traitsui.api import VGroup, Item, OKCancelButtons, View, Tabbed, \
    HSplit, StatusItem, HGroup, Spring

COPY_TO_CLIPBOARD = "copy to clipboard"
APPEND_TO_FILTER = "append to filter"

logger = logging.getLogger(__name__)


class FilterExpressionEditorView(HasStrictTraits):
    """ Provides a resizeable edit view of the filter string (or any string).
    """

    #: Expression representing the dataframe filter
    expr = Str

    #: Dataframe upon which filter will operate
    source_df = Instance(DataFrame)

    #: Class to use to create TraitsUI window to open controls
    view_klass = Any(View)

    #: Selected columns which should have their own tab
    included_cols = List

    #: Status bar for the window
    status_bar = Instance(StatusBarManager)

    #: Message that is displayed in the status bar
    status_bar_message = Str

    #: Dictionary of translated trait names with original names as keys
    traited_names = Dict

    #: Dictionary of original names with translated trait names as keys
    original_names = Dict

    #: List of column names that should have their own tabs
    included_col_values = Dict

    #: Boolean that determines whether the clicked value is copied or appended
    auto_append = Bool(True)

    #: Enum that allows selection of action that occurs when clicking
    click_type = Enum(values="_click_action_options")

    #: flag describing the initialization status of this instance
    _edit_initialized = Bool(False)

    #: List of actions that can occur when clicking a button
    _click_action_options = List([APPEND_TO_FILTER, COPY_TO_CLIPBOARD])

    def __init__(self, source_df: DataFrame, **traits):
        super(FilterExpressionEditorView, self).__init__(**traits)
        if not any(sorted(source_df)):
            msg = f"The source_df contains no columns"
            logger.exception(msg)
            raise KeyError(msg)
        self.source_df = source_df
        if "included_cols" in traits:
            # if any of the specified columns have value dtypes that are
            # numerical, then throw an error
            included = traits["included_cols"]
            if not set(included).issubset(sorted(source_df)):
                msg = f"The source_df does not contain all columns in the " \
                      f"included_cols list."
                logger.exception(msg)
                raise KeyError(msg)
            self.included_cols = traits["included_cols"]
        self._create_trait_translators()
        self._create_button_traits_from_column_names()
        self._create_button_traits_from_column_values()
        self._edit_initialized = True

    def traits_view(self):
        # create Items for each column name Button trait
        col_names = sorted(self.source_df)
        col_traited_names = list(itemgetter(*col_names)(self.traited_names))
        col_name_bttns = [Item(n, show_label=False) for n in col_traited_names]
        # create Items for each column value Button trait
        included_column_button_list = self._create_included_col_view_tabs()

        # make the view
        view = self.view_klass(
            HSplit(
                VGroup(
                    Tabbed(
                        VGroup(
                            *col_name_bttns,
                            label="Column Names"
                        ),
                        *included_column_button_list,
                    ),
                    HGroup(
                        Item('click_type', style='custom', show_label=False),
                        Spring(),
                        label="When clicking a button...",
                        show_border=True
                    )
                ),
                VGroup(
                    Item("expr", style="custom", show_label=False, width=450),
                    show_border=True,
                ),
            ),
            resizable=True,
            buttons=OKCancelButtons,
            title="Edit the filter...",
            statusbar=StatusItem(name="status_bar_message")
        )
        return view

    def _create_trait_translators(self):
        """ Create translators that associate column names/values with traits
        """
        # create for each column name
        self._add_values_to_translators(sorted(self.source_df))
        # create for each value in the included columns
        for column in self.included_cols:
            column_values = list(self.source_df[column].unique())
            self.included_col_values[column] = column_values
            self._add_values_to_translators(column_values)

    def _add_values_to_translators(self, column_values: Iterable):
        """ Add values from `column_values` to two translation dicts
        """
        for name in column_values:
            # make a traited-version of the value
            trait_name = f"trait_{sanitize_string(name)}"
            # track the traited name with the original name key
            self.traited_names[name] = trait_name
            # track the original name with a traited name key
            self.original_names[trait_name] = name

    def _create_included_col_view_tabs(self):
        """ Create a list of View Items for each value of each included column
        """
        tab_list = []
        for column in self.included_col_values.keys():
            uniques = self.included_col_values[column]
            value_bttns = [Item(self.traited_names[name], show_label=False)
                           for name in uniques]
            new_group = VGroup(
                *value_bttns,
                label=column
            )
            tab_list.append(new_group)
        return tab_list

    def _create_button_traits_from_column_values(self):
        """ Create `Button` traits for each value of each included_cols item
        """
        for cat_item in self.included_cols:
            column_values = [str(x) for x in self.source_df[cat_item].unique()]
            self._create_button_traits(column_values)

    def _create_button_traits_from_column_names(self):
        """ Create `Button` traits for every column name in the source df
        """
        self._create_button_traits(sorted(self.source_df))

    def _create_button_traits(self, names):
        """ Create `Button` traits for each item in an `Iterable`

        Parameters
        ----------
        names : Iterable
            Iterable of values from which to create a set of `Button` traits
        """
        for name in names:
            trait_name = self.traited_names[name]
            self.add_trait(trait_name, Button(name))
            self.observe(self.filter_button_clicked, trait_name)

    def filter_button_clicked(self, event):
        """ Appends the clicked value to the filter or copies to the clipboard
        """
        if not self._edit_initialized:
            return
        selected_value = self.original_names[event.name]
        # if the selected value is not in the list of column names, add quotes
        if selected_value not in self.source_df.columns.tolist():
            selected_value = f'"{selected_value}"'
        if self.auto_append:
            self.expr = f"{self.expr}{selected_value}"
            self.status_bar_message = f"'{selected_value}' appended to filter."
            return

        cb = Clipboard()
        cb.text_data = selected_value
        self.status_bar_message = f"'{cb.text_data}' copied to the clipboard."

    def _click_type_changed(self, new):
        if new == APPEND_TO_FILTER:
            self.auto_append = True
        else:
            self.auto_append = False

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
    test = FilterExpressionEditorView(expr="a == 4", source_df=test_df,
                                      included_cols=["c", "e_column"])
    test.configure_traits()
