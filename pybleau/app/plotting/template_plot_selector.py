from app_common.traitsui.common_modal_dialogs import GuiStringSelector, \
    StringSelectorHandler
from traits.api import Bool, Str, Property
from traitsui.api import CancelButton, EnumEditor, HGroup, Item, Label, \
    Spring, View, VGroup, TextEditor, Action


class TemplatePlotNameSelector(GuiStringSelector):
    """Tiny UI to name a plot template, or select from the existing ones
    """
    title = "Create a template plot..."

    label = "Replace an existing template:"

    new_name_is_valid = Property(Bool(False), depends_on="new_name")

    input_is_valid = Property(Bool(False), depends_on="new_name_is_valid, "
                                                      "string_is_selected")

    replace_old_template = Bool(False)

    new_name = Str

    def traits_view(self):
        top_instructions = "\nType a name for the new plot template in the " \
                           "input below.\nTo replace an existing template, " \
                           "select its name in the dropdown:\n"
        bottom_instructions = '\nOnce a name has been provided or selected, ' \
                              'click "OK" to save the plot template.\nAll ' \
                              'plot templates are visible and configurable ' \
                              'via the "Plot Templates" tab in the ' \
                              'Preferences'
        view = View(
            VGroup(
                HGroup(
                    Label(top_instructions),
                    Spring()
                ),
                VGroup(
                    HGroup(
                        Item("new_name",
                             editor=TextEditor(),
                             enabled_when='not replace_old_template',
                             springy=True,
                             label="Create a new template:"
                             ),
                        Spring()
                    ),
                    HGroup(
                        Item('replace_old_template', show_label=False),
                        Item("selected_string",
                             editor=EnumEditor(name='string_options'),
                             enabled_when='replace_old_template',
                             show_label=True, label=self.label)
                    ),
                ),
                HGroup(
                    Label(bottom_instructions),
                    Spring()
                ),
            ),
            buttons=[self.ok_button, CancelButton],
            handler=StringSelectorHandler(),
        )

        return view

    def check_name_validity(self, value):
        no_spaces = value.replace(" ", "")
        no_underscores = no_spaces.replace("_", "")

        test1 = len(no_underscores) > 0
        test2 = no_underscores.isalnum()
        test3 = value not in self.string_options

        if test1 and test2 and test3:
            return True
        else:
            return False

    def _get_new_name_is_valid(self):
        return self.check_name_validity(self.new_name)

    def _ok_button_default(self):
        return Action(name='OK', enabled_when='input_is_valid')

    def _get_input_is_valid(self):
        if self.replace_old_template:
            return self.is_string_selected
        else:
            return self.new_name_is_valid
