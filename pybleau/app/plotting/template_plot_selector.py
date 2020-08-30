from app_common.traitsui.common_modal_dialogs import StringSelectorHandler, \
    BaseDlg
from traits.api import Bool, Str, Property, List
from traits.trait_types import Instance
from traitsui.api import CancelButton, EnumEditor, HGroup, Item, Label, \
    Spring, VGroup, TextEditor, Action


class TemplatePlotNameSelector(BaseDlg):
    """Tiny UI to name a plot template, or select from the existing ones
    """
    #: Title of the window
    title = "Create a template plot..."

    #: The available options in the dropdown
    string_options = List(Str)

    #: The selected option in the dropdown
    selected_string = Str

    #: Property defining whether there is a string selected or not
    is_string_selected = Property(Bool(), depends_on="selected_string, "
                                                     "string_options[]")

    #: Property defining whether the new name is valid
    new_name_is_valid = Property(Bool(), depends_on="new_name")

    #: Property defining whether the new name should be marked as invalid
    new_name_is_invalid = Property(
        Bool(), depends_on="new_name, replace_old_template"
    )

    #: Property that defines if the user can click the OK button
    input_is_valid = Property(Bool(), depends_on="new_name_is_valid, "
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
        name_error_msg = f'<p style="color:red">{error_message}</p>'
        or_msg = '<p style="font-size:20px"> OR </p>'
        view = self.view_klass(
            HGroup(
                VGroup(
                    Item("new_name",
                         editor=TextEditor(invalid="new_name_is_invalid"),
                         enabled_when='not replace_old_template',
                         label="New template name:"
                         ),
                    HGroup(
                        Label(name_error_msg),
                        visible_when="new_name_is_invalid"
                    ),
                    show_border=True
                ),
                VGroup(
                    Spring(),
                    Label(or_msg),
                    Spring(),
                    visible_when="len(string_options) > 0"
                ),
                VGroup(
                    HGroup(
                        Item('replace_old_template', show_label=False),
                        Label(dropdown_msg),
                        Spring()
                    ),
                    HGroup(
                        Item("selected_string",
                             editor=EnumEditor(name='string_options'),
                             enabled_when='replace_old_template',
                             show_label=False),
                        Spring(),
                    ),
                    visible_when="len(string_options) > 0",
                    show_border=True
                ),
            ),
            buttons=[self.ok_button, CancelButton],
            handler=StringSelectorHandler(),
            title=self.title,
            height=140
        )

        return view

    # Traits property getters/setters -----------------------------------------

    def _get_new_name_is_valid(self):
        value = self.new_name
        no_spaces = value.replace(" ", "")
        no_underscores = no_spaces.replace("_", "")

        test1 = len(no_underscores) > 0
        test2 = no_underscores.isalnum()
        test3 = value not in self.string_options

        return test1 and test2 and test3

    def _get_new_name_is_invalid(self):
        return not self.new_name_is_valid and not self.replace_old_template \
               and len(self.new_name) > 0

    def _get_input_is_valid(self):
        if self.replace_old_template:
            return self.is_string_selected
        else:
            return self.new_name_is_valid

    def _get_is_string_selected(self):
        return self.selected_string in self.string_options

    # Traits initialization methods -------------------------------------------

    def _ok_button_default(self):
        return Action(name='OK', enabled_when='input_is_valid')


if __name__ == "__main__":
    y = list('abcde')
    select = TemplatePlotNameSelector(string_options=y)
    select.edit_traits(kind="livemodal")
