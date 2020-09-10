from app_common.traitsui.common_modal_dialogs import BaseDlg
from traits.api import Bool, Instance, Property
from traitsui.api import Handler, Action

from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.ui.plot_template_manager_view import PlotTemplateManagerView


class ManageTemplatesHandler(Handler):
    def do_manage(self, info):
        manager = PlotTemplateManagerView(model=info.object.template_manager,
                                          view_klass=info.object.view_klass)
        manager.edit_traits(kind='modal')


class ManageTemplatesAccessor(BaseDlg):
    #: PlotTemplateManager for creating a template manager view
    template_manager = Instance(PlotTemplateManager)

    #: Button to bring up the plot templates manager view
    man_temp_button = Instance(Action)

    #: Boolean flag for whether templates exist
    templates_exist = Property(Bool)

    # Traits initialization methods -------------------------------------------

    def _get_templates_exist(self) -> bool:
        return len(self.template_manager.names) > 0

    def _man_temp_button_default(self):
        return Action(name='Manage templates...',
                      enabled_when='templates_exist',
                      action='do_manage')
