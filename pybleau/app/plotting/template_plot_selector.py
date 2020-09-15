from app_common.traitsui.label_with_html import Label
from traits.api import Bool, Str, Property, Instance
from traitsui.api import CancelButton, EnumEditor, HGroup, Item, Spring, \
    VGroup, TextEditor, Action

from pybleau.app.ui.manage_templates_accessor import ManageTemplatesAccessor, \
    ManageTemplatesHandler


class TemplatePlotNameSelector(ManageTemplatesAccessor):
    """ Tiny UI to name a plot template, or select from the existing ones
    """
    #: Title of the window
    title = "Create a template plot..."

    #: The selected option in the dropdown
    selected_string = Str

    #: Property defining whether there is a string selected or not
    is_string_selected = Property(Bool(), depends_on="selected_string, "
                                                     "plot_types[]")

    #: Property defining whether the new name is valid
    new_name_entry_is_valid = Property(Bool(), depends_on="new_name")

    #: Property defining whether the new name should be marked as invalid
    new_name_is_required_and_invalid = Property(
        Bool(), depends_on="new_name, replace_old_template"
    )

    #: Property that defines if the user can click the OK button
    input_is_valid = Property(Bool(), depends_on="new_name_entry_is_valid, "
                                                 "string_is_selected")

    #: Checkbox used to define whether a template will be created or replaced
    replace_old_template = Bool(False)

    #: User input new name for the template
    new_name = Str

    ok_button = Instance(Action)

    def traits_view(self):
        dropdown_msg = "Replace an existing template by \nselecting it from " \
                       "the dropdown."
        error_message = "Name must contain only numbers and letters, <br>" \
                        "and cannot match an existing template."
        view = self.view_klass(
            HGroup(
                VGroup(
                    Item("new_name",
                         editor=TextEditor(
                             invalid="new_name_is_required_and_invalid"
                         ),
                         enabled_when='not replace_old_template',
                         label="New template name:"
                         ),
                    HGroup(
                        Label(error_message, color="red"),
                        visible_when="new_name_is_required_and_invalid"
                    ),
                    show_border=True
                ),
                VGroup(
                    Spring(),
                    Label("OR", font_size=20),
                    Spring(),
                    visible_when="len(plot_types) > 0"
                ),
                VGroup(
                    HGroup(
                        Item('replace_old_template', show_label=False),
                        Label(dropdown_msg),
                        Spring()
                    ),
                    HGroup(
                        Item("selected_string",
                             editor=EnumEditor(name='plot_types'),
                             enabled_when='replace_old_template',
                             show_label=False),
                        Spring(),
                    ),
                    visible_when="len(plot_types) > 0",
                    show_border=True
                ),
            ),
            buttons=[self.ok_button, self.man_temp_button, CancelButton],
            handler=ManageTemplatesHandler(),
            title=self.title,
            height=140
        )

        return view

    # Traits property getters/setters -----------------------------------------

    def _get_new_name_entry_is_valid(self):
        value = self.new_name
        no_spaces = value.replace(" ", "")
        no_underscores = no_spaces.replace("_", "")

        test1 = len(no_underscores) > 0
        test2 = no_underscores.isalnum()
        test3 = value not in self.plot_types

        return test1 and test2 and test3

    def _get_new_name_is_required_and_invalid(self):
        return not self.new_name_entry_is_valid and not \
            self.replace_old_template and len(self.new_name) > 0

    def _get_input_is_valid(self):
        if self.replace_old_template:
            return self.is_string_selected
        else:
            return self.new_name_entry_is_valid

    def _get_is_string_selected(self):
        return self.selected_string in self.plot_types

    # Traits initialization methods -------------------------------------------

    def _ok_button_default(self):
        return Action(name='OK', enabled_when='input_is_valid')


if __name__ == "__main__":
    y = list('abcde')
    select = TemplatePlotNameSelector(plot_types=y)
    select.edit_traits(kind="livemodal")
