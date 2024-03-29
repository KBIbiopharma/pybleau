from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from traits.api import HasStrictTraits, Instance, List, Str, Button, Bool, \
    Property, Any
from traitsui.api import ListStrEditor, VGroup, HGroup, Spring, Readonly, \
    Item, View

from pybleau.app.model.plot_template_manager import PlotTemplateManager


class PlotTemplateManagerView(HasStrictTraits):
    """ Pop-up dialog for viewing and deleting available plot templates
    """
    # View model
    model = Instance(PlotTemplateManager)

    # Templates in the list that are selected
    selected_plot_templates = List(Str)

    # Delete button - to delete the selected template(s)
    delete_from_templates = Button("Delete Selected")

    #: Rescan button - to refresh the list of templates
    rescan_for_templates = Button("Rescan Template Directory")

    #: Bool for whether a template (or templates) is selected
    is_selected = Property(Bool(False), depends_on="selected_plot_templates")

    #: View class to use. Modify to customize.
    view_klass = Any(View)

    #: Is the UI interactive? Set to False for testing
    interactive = Bool(True)

    def traits_view(self):
        self.model.rescan_template_dir()
        plot_template_edit = ListStrEditor(selected="selected_plot_templates",
                                           multi_select=True,
                                           drag_move=False)
        delete_tooltip = "Deleting a template is irreversible."
        rescan_tooltip = "Rescanning the template directory will refresh " \
                         "the list of available templates."
        view = self.view_klass(
            VGroup(
                Spring(),
                Readonly('object.model.plot_template_directory'),
                Item('object.model.names', editor=plot_template_edit,
                     label='Existing Plot Templates'),
                HGroup(
                    Spring(),
                    Item("delete_from_templates", show_label=False,
                         tooltip=delete_tooltip, enabled_when="is_selected"),
                    Item("rescan_for_templates", show_label=False,
                         tooltip=rescan_tooltip),
                    Spring()
                ),
                Spring(),
                show_border=True
            ),
            title="Manage plot templates..."
        )
        return view

    def _get_is_selected(self):
        return len(self.selected_plot_templates) > 0

    def _delete_from_templates_fired(self):
        selected_templates = self.selected_plot_templates
        self._delete_templates(selected_templates)

    def _delete_templates(self, selected_templates):
        confirmed = YES
        if self.interactive:
            num = len(selected_templates)
            msg = f"Delete the {num} selected items?\n\n" \
                  f"Once deleted, a template is not recoverable."
            confirmed = confirm(None, msg)
        if confirmed == YES:
            self.model.delete_templates(selected_templates)
            self.selected_plot_templates = []

    def _rescan_for_templates_fired(self):
        self.model.rescan_template_dir()


if __name__ == "__main__":
    from pybleau.app.model.tests.test_plot_template_manager import \
        FakePlotTemplateInteractor

    model = PlotTemplateManager(interactor=FakePlotTemplateInteractor())
    temp = PlotTemplateManagerView(model=model)
    temp.configure_traits()
