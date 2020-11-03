from pandas import DataFrame
from pyface.action.api import StatusBarManager
from traits.api import HasStrictTraits, Instance, List, Button, Bool, Str, Any
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

    def __init__(self, source_df: DataFrame, **traits):
        super(FilterExpressionEditorView, self).__init__(**traits)
        self.source_df = source_df
        self._create_button_traits(sorted(source_df))
        if "included_cols" in traits:
            # if any of the specified columns have value dtypes that are
            # numerical, then throw an error
            self.included_cols = traits["included_cols"]
        # else:
        #     # if any of the specified columns have value dtypes that are
        #     # numerical, then don't include them
        #     for column in sorted(source_df):
        #         if source_df[column].dtype in ['datetime64', 'object']:
        #             self.included_cols.append(column)
        self._create_column_value_button_traits()
        self.edit_initialized = True

    def traits_view(self):
        all_column_button_list = [Item(name, show_label=False) for name in
                                  sorted(self.source_df)]
        included_column_button_list = self._create_included_col_view_tabs()
        view = self.view_klass(
            HSplit(
                Tabbed(
                    VGroup(
                        *all_column_button_list,
                        label="All Columns",
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
        for column in self.included_cols:
            # casting as a str is probably not necessary
            uniques = [str(x) for x in self.source_df[column].unique()]
            value_list = [Item(name, show_label=False) for name in uniques]
            new_group = VGroup(
                *value_list,
                label=column,
                scrollable=True
            )
            tab_list.append(new_group)
        return tab_list

    def _create_column_value_button_traits(self):
        for cat_item in self.included_cols:
            column_values = [str(x) for x in self.source_df[cat_item].unique()]
            self._create_button_traits(column_values)

    def _create_button_traits(self, names):
        values = {}
        for name in names:
            self.add_trait(name, Button())
            #  How do I keep the button from formatting the text I put on it?
            column_button = Button(name)
            self.observe(self.filter_button_clicked, name)
            values[name] = column_button
        self.trait_set(**values)

    def filter_button_clicked(self, event):
        if not self.edit_initialized:
            return
        from pyface.clipboard import Clipboard
        cb = Clipboard()
        cb.text_data = event.name
        self.status_bar_message = f"'{event.name}' copied to the clipboard."

    def _status_bar_default(self):
        return StatusBarManager(messages=[self.status_bar_message],
                                text_color="black")


if __name__ == "__main__":
    source_df = DataFrame(
        {
            "a": [1, 2, 4, 5],
            "b": list("zxyh"),
            "c": list("test"),
            "d": ["alpha", "beta", "zeta", "kAPPa pappa"],
            "e_column": ["print", "about this", "a#93", "__"]
        },
        index=[0, 1, 3, 4]
    )
    test = FilterExpressionEditorView(exp="a == 3", source_df=source_df,
                                      included_cols=["b", "c"])
    test.edit_traits(kind="livemodal")
