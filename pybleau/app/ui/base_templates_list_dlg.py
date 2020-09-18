from app_common.traitsui.common_modal_dialogs import BaseDlg
from traits.api import Bool, Instance, Property, List, Str, observe
from traitsui.api import Handler, Action

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.plot_template_manager_view import PlotTemplateManagerView


class ManageTemplatesHandler(Handler):
    def do_manage(self, info):
        manager = PlotTemplateManagerView(model=info.object.model,
                                          view_klass=info.object.view_klass)
        manager.edit_traits(kind='livemodal')


class BaseTemplateListDlg(BaseDlg):
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
        """ Based on the new and old versions of the template name list,
        change the templates in the plot types list"""
        if event.old == event.new:
            # no changes
            return
        else:
            old = event.old
            new = event.new
            self._reconcile_plot_types_list(old, new)

    # Private interface -------------------------------------------------------

    def _reconcile_plot_types_list(self, old_list, new_list):
        if old_list is None:
            # there is no old list, so all items are new
            added = new_list
            removed = False
        else:
            # there are both new and old items, so find the differences
            added = set(new_list).difference(set(old_list))
            removed = set(old_list).difference(set(new_list))
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
