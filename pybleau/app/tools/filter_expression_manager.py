""" Module to manage filter expressions for dataframe analyzer.
"""
import numpy as np
import six

from traits.api import Any, Button, cached_property, Enum, HasStrictTraits, \
    Instance, List, on_trait_change, Property, Set, Str
from traitsui.api import HGroup, Item, Label, OKCancelButtons,\
    Spring, TableEditor, VGroup, View
from traitsui.table_column import ObjectColumn

from app_common.traitsui.common_modal_dialogs import request_string

WIDTH_EXP = 400

WIDTH_EXP_NAME = 200


def build_filter_expression_editor(editable=True):
    """ Build a TableEditor for a list of FilterExpressions.
    """
    editor = TableEditor(
        columns=[
            ObjectColumn(name="name", width=WIDTH_EXP_NAME),
            ObjectColumn(name="expression", width=WIDTH_EXP)
        ],
        show_row_labels=True,
        row_factory=FilterExpression,
        editable=editable,
        deletable=editable,
        selected="selected_expression",
    )
    return editor


class FilterExpression(HasStrictTraits):
    name = Str

    expression = Str

    def __init__(self, **traits):
        super(FilterExpression, self).__init__(**traits)
        if not self.name:
            self.name = self.expression


class FilterExpressionManager(HasStrictTraits):
    """ Manager to view, search, select or modify a list of filter expressions.

    The set of tasks the tool will support is controlled by the "mode"
    attribute.
    """

    #: Mode of the UI: UI used to select existing expression or add/delete expr
    mode = Enum("load", "manage")

    #: Known filters to pick from or manage
    known_filter_exps = List(FilterExpression)

    #: View class to use. Modify to customize.
    view_klass = Any(View)

    #: Expr selected to be deleted ('manage' mode) or loaded ('load' mode)
    selected_expression = Instance(FilterExpression)

    # Manage mode attributes --------------------------------------------------

    #: Button to add a new filter
    add_button = Button("Add")

    #: Button to delete the selected filter
    delete_button = Button("Delete")

    #: List of string versions of the known expressions
    _known_expressions = Property(Set, depends_on="known_filter_exps[]")

    # Load mode attributes --------------------------------------------------

    #: String to filter filters based on their names
    search_names = Str

    #: String to filter filters based on their expression
    search_expressions = Str

    #: Filters displayed: differs from known when filtering (load mode only)
    displayed_filter_exps = List(FilterExpression)

    # Masks to support filtering:

    _all_true_mask = Property(List, depends_on="known_filter_exps")

    _name_mask = Property(List, depends_on="known_filter_exps, search_names")

    _expression_mask = Property(
        List, depends_on="known_filter_exps, search_expressions"
    )

    def traits_view(self):
        known_expr_editor = build_filter_expression_editor(
            editable=self.mode == "manage"
        )
        if self.mode == "load":
            title = "Search and select filter"
        else:
            title = "Add, rename or remove filters"

        manage_instructions = "Click on an name/expression to modify it or " \
            "use the buttons below to add/remove expressions."
        load_instructions = "Select the expression to load and click 'OK'."

        is_load = "mode == 'load'"
        is_manage = "mode == 'manage'"

        view = self.view_klass(
            VGroup(
                HGroup(Label(manage_instructions), visible_when=is_manage),
                HGroup(Label(load_instructions), visible_when=is_load),
                HGroup(
                    Item("search_names", width=WIDTH_EXP_NAME),
                    Spring(),
                    Item("search_expressions", width=WIDTH_EXP),
                    show_border=True, visible_when=is_load
                ),
                Item("displayed_filter_exps", editor=known_expr_editor,
                     label="Filter list", visible_when=is_load),
                Item("known_filter_exps", editor=known_expr_editor,
                     label="Filter list", visible_when=is_manage),
                HGroup(
                    Spring(),
                    Item("add_button", show_label=False),
                    Item("delete_button", show_label=False,
                         enabled_when="selected_expression"),
                    Spring(),
                    visible_when=is_manage
                ),
            ),
            buttons=OKCancelButtons,
            title=title,
        )
        return view

    # Traits listener methods -------------------------------------------------

    def _add_button_fired(self):
        new_exp = request_string(title="New filter expression",
                                 forbidden_values=self._known_expressions)
        if not isinstance(new_exp, six.string_types):
            return

        # The button is disabled when `new_filter_exp` is empty so no need to
        # handle that case here.
        exp = FilterExpression(name=new_exp, expression=new_exp)
        self.known_filter_exps.append(exp)

    def _delete_button_fired(self):
        self.known_filter_exps.remove(self.selected_expression)

    @on_trait_change("_expression_mask, _name_mask")
    def filter_changed(self):
        tuples = zip(self.known_filter_exps, self._name_mask,
                     self._expression_mask)
        self.displayed_filter_exps = [exp for exp, valid_name, valid_exp in
                                      tuples if valid_name and valid_exp]

    # Traits property getters/setters -----------------------------------------

    @cached_property
    def _get__known_expressions(self):
        return {exp.expression for exp in self.known_filter_exps}

    @cached_property
    def _get__expression_mask(self):
        if not self.search_expressions.strip():
            return self._all_true_mask
        else:
            return [self.search_expressions in exp.expression
                    for exp in self.known_filter_exps]

    @cached_property
    def _get__name_mask(self):
        if not self.search_names.strip():
            return self._all_true_mask
        else:
            return [self.search_names in exp.name
                    for exp in self.known_filter_exps]

    def _get__all_true_mask(self):
        return list(np.ones(len(self.known_filter_exps), dtype="bool"))

    # Traits initialization methods -------------------------------------------

    def _displayed_filter_exps_default(self):
        return self.known_filter_exps


if __name__ == "__main__":
    known_filter_exps = [FilterExpression(name="test", expression="a > 2"),
                         FilterExpression(name="test2", expression="a > 5")]
    manager = FilterExpressionManager(mode="manage",
                                      known_filter_exps=known_filter_exps)
    manager.configure_traits()
