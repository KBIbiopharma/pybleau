import os
from pathlib import Path

from traits.api import cached_property, Str, List, Instance, Directory, \
    Property, Event, HasStrictTraits

from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor


class PlotTemplateManager(HasStrictTraits):
    """ Model for the dialog used to manage plot templates
    """
    #: Names of all the available plot templates
    names = Property(List(Str), depends_on="templates_changed")

    #: IPlotTemplateInteractor used to save/load/locate plot templates
    interactor = Instance(IPlotTemplateInteractor, args=())

    #: Directory of plot templates
    plot_template_directory = Property(Directory)

    #: Set to True whenever the list of templates changes or to refresh list
    templates_changed = Event

    # Public interface --------------------------------------------------------

    def delete_templates(self, templates_names: list):
        removed = self.interactor.delete_templates(templates_names)
        if removed:
            self.templates_changed = True

    def rescan_template_dir(self):
        self.templates_changed = True

    # Traits property getters/setters -----------------------------------------

    @cached_property
    def _get_names(self):
        path = self.plot_template_directory
        ext = self.interactor.get_template_ext()
        result = []
        for filename in os.listdir(path):
            if filename.endswith(ext):
                result.append(Path(filename).stem)
        return result

    def _get_plot_template_directory(self):
        return self.interactor.get_template_dir()
