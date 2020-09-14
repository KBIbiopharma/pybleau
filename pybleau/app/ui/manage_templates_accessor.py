from app_common.traitsui.common_modal_dialogs import BaseDlg
from traits.api import Bool, Instance, Property, List, Str, observe
from traits.observation.expression import trait
from traitsui.api import Handler, Action

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.plot_template_manager_view import PlotTemplateManagerView


class ManageTemplatesHandler(Handler):
    def do_manage(self, info):
        manager = PlotTemplateManagerView(model=info.object.model,
                                          view_klass=info.object.view_klass)
        manager.edit_traits(kind='livemodal')


class ManageTemplatesAccessor(BaseDlg):
    """ Base class for UI elements that want to include a button for managing
    plot templates
    """

    #: Available plot types
    plot_types = List(Str)

    #: PlotTemplateManager for creating a template manager view
    model = Instance(PlotTemplateManager)

    #: Button to bring up the plot templates manager view
    man_temp_button = Instance(Action)

    #: Boolean flag for whether templates exist
    templates_exist = Property(Bool)

    # Traits initialization methods -------------------------------------------

    def _get_templates_exist(self) -> bool:
        return len(self.model.names) > 0

    def _man_temp_button_default(self):
        return Action(name='Manage templates...',
                      enabled_when='templates_exist',
                      action='do_manage')

    # Traits listeners --------------------------------------------------------

    @observe("model:names", post_init=True)
    def template_list_changed(self, event):
        """ Based on the new and old items in the event, change the
        templates list"""
        if event.old == event.new:
            # no changes
            return
        if event.old is None:
            # there is no old list, so all items are new
            added = event.new
            removed = False
        else:
            # there are both new and old items, so find the differences
            added = set(event.new).difference(set(event.old))
            removed = set(event.old).difference(set(event.new))
        if added:
            # add all the new items that aren't in the old list
            for item in added:
                if item not in self.plot_types:
                    self.plot_types.append(item)
        if removed:
            # remove all the old items that aren't in the new list
            for item in removed:
                self.plot_types.remove(item)
                if item in self.plot_types:
                    self.plot_types.append(item)
