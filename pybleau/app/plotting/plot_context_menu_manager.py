import logging

from traits.api import Event, HasStrictTraits, Instance, List
from pyface.action.api import Action, MenuManager, Separator
from pyface.api import confirm, YES
from chaco.api import OverlayPlotContainer

from app_common.chaco.plot_io import save_plot_to_file, to_png_file_requester
from app_common.std_lib.filepath_utils import open_file

logger = logging.getLogger(__name__)

STYLE_EDITOR_ACTION_NAME = "Edit Style..."

FILE_EXPORT_ACTION_NAME = "Export plot..."

DELETE_ACTION_NAME = "Delete plot..."


class PlotContextMenuManager(HasStrictTraits):
    target = Instance(OverlayPlotContainer)

    action_list = List

    style_edit_requested = Event

    delete_requested = Event

    def build_menu(self):
        menu_entries = []
        if STYLE_EDITOR_ACTION_NAME in self.action_list:
            action = Action(name=STYLE_EDITOR_ACTION_NAME,
                            on_perform=self.request_style_editor)
            menu_entries.append(action)
            menu_entries.append(Separator())
        if FILE_EXPORT_ACTION_NAME:
            action = Action(name=FILE_EXPORT_ACTION_NAME,
                            on_perform=self.export_plot_to_file)
            menu_entries.append(action)
            menu_entries.append(Separator())

        if DELETE_ACTION_NAME:
            action = Action(name=DELETE_ACTION_NAME,
                            on_perform=self.request_delete)
            menu_entries.append(action)
            menu_entries.append(Separator())

        menu = MenuManager(*menu_entries)
        return menu

    def request_style_editor(self):
        """ Trigger event and let DFPlotManager handle.
        """
        self.style_edit_requested = True

    def request_delete(self):
        """ Trigger event and let DFPlotManager handle.
        """
        if confirm(None, "Delete the plot?") == YES:
            self.delete_requested = True

    def export_plot_to_file(self):
        filepath = to_png_file_requester(title="Select export path")
        if filepath:
            save_plot_to_file(self.target, filepath)
            logger.info("Plot saved to {}".format(filepath))
            open_file(filepath)

    def _action_list_default(self):
        return [STYLE_EDITOR_ACTION_NAME, FILE_EXPORT_ACTION_NAME,
                DELETE_ACTION_NAME]
