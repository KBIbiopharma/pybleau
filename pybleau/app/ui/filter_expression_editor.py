import logging
from collections import Iterable

from app_common.std_lib.str_utils import sanitize_string
from pandas import DataFrame
from pyface.action.api import StatusBarManager
from pyface.api import Clipboard
from traits.api import Enum
from traits.api import HasStrictTraits, Instance, List, Bool, Str, Any, Dict
from traitsui.api import VGroup, Item, OKCancelButtons, View, Tabbed, \
    HSplit, StatusItem, HGroup, Spring
from traitsui.editors import InstanceEditor

from pybleau.app.utils.scrollable_button_list_view import \
    ScrollableButtonListView

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
    is_initialized = Bool(False)

    #: List of actions that can occur when clicking a button
    _click_action_options = List([APPEND_TO_FILTER, COPY_TO_CLIPBOARD])

    #: Provider of a scrollable view for the column name buttons
    _scrollable_column_names = Instance(ScrollableButtonListView)

    #: List of scroll list views for each column in included_cols
    _included_col_scroll_list = List

    def __init__(self, source_df: DataFrame, **traits):
        super(FilterExpressionEditorView, self).__init__(**traits)
        if not source_df.columns:
            msg = "The source_df contains no columns"
            logger.exception(msg)
            raise KeyError(msg)
        self.source_df = source_df
        if "included_cols" in traits:
            # if any of the specified columns have value dtypes that are
            # numerical, then throw an error
            included = traits["included_cols"]
            if not set(included).issubset(source_df.columns):
                msg = "The source_df does not contain all columns in the " \
                      "included_cols list."
                logger.exception(msg)
                raise AttributeError(msg)
            self.included_cols = traits["included_cols"]
        self._create_trait_translators()
        self._create_col_name_scrollable_view()
        self._create_included_col_scroll_list()
        self.is_initialized = True

    def traits_view(self):
        view = self.view_klass(
            HSplit(
                VGroup(
                    Tabbed(
                        Item("_scrollable_column_names", style="custom",
                             editor=InstanceEditor(), show_label=False,
                             label="Column Names"),
                        *self._included_col_scroll_list
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
                    show_border=True
                )
            ),
            resizable=True,
            buttons=OKCancelButtons,
            title="Edit the filter...",
            statusbar=StatusItem(name="status_bar_message"),
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
            self.traited_names[name] = trait_name
            self.original_names[trait_name] = name

    def _create_col_name_scrollable_view(self):
        # create a scrollable list of col name buttons
        col_names = sorted(self.source_df)
        # create a {trait_name:name} dict for the ScrollableButtonListView
        col_dict = {self.traited_names[name]: name for name in col_names}
        self._scrollable_column_names = ScrollableButtonListView(
            traits_and_names=col_dict, handler=self.filter_button_clicked
        )

    def _create_included_col_scroll_list(self):
        included_scroll_list = []
        # create scrollable lists for column value buttons
        for column in self.included_col_values.keys():
            uniques = self.included_col_values[column]
            # create a {trait_name:name} dict for the ScrollableButtonListView
            col_dict = {self.traited_names[name]: name for name in uniques}
            scroll_view = ScrollableButtonListView(
                traits_and_names=col_dict, handler=self.filter_button_clicked
            )
            # make a trait for this ScrollableButtonListView
            scroll_trait = f"{self.traited_names[column]}_col_scroll_list"
            self.add_trait(scroll_trait, scroll_view)
            # make an Item for the new scroll_trait
            new_item = Item(scroll_trait, style="custom", show_label=False,
                            editor=InstanceEditor(), label=column)
            included_scroll_list.append(new_item)
        self._included_col_scroll_list = included_scroll_list

    def filter_button_clicked(self, event):
        """ Appends the clicked value to the filter or copies to the clipboard
        """
        if not self.is_initialized:
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
            "b": list("1234"),
            "c": list("1234"),
            "d": list("1234"),
            "e": list("1234"),
            "f": list("1234"),
            "g": list("1234"),
            "h": list("1234"),
            "i": list("1234"),
            "j": list("1234"),
            "k": list("1234"),
            "l": list("1234"),
            "m": list("1234"),
            "n": list("1234"),
            "o": list("1234"),
            "p": list("1234"),
            "q": list("1234"),
            "r": list("1234"),
            "s": list("1234"),
            "t": list("1234"),
            "u": list("1234"),
            "v": list("1234"),
            "w": list("1234"),
            "x": list("1234"),
            "y": ["1 alpha", "MM_TT_BB_03-92", "2zeta", "kAPPa pappa"],
            "e_column": ["03_06 04_STANDARD.name",
                         "about this", "._ a93", "d!@#.$% ^&*()_+d"]
        },
        index=[0, 1, 3, 4]
    )
    test = FilterExpressionEditorView(expr="a == 4", source_df=test_df,
                                      included_cols=["y", "e_column", "w"])
    test.configure_traits()
