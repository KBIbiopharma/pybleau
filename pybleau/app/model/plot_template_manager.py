import os
from pathlib import Path

from traits.api import cached_property, Str, List, Instance, Directory, \
    Property, Event, HasStrictTraits

from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor


class PlotTemplateManager(HasStrictTraits):

    #: Names of all the available plot templates
    names = Property(List(Str), depends_on="list_changed")

    #: IPlotTemplateInteractor used to save/load/locate plot templates
    interactor = Instance(IPlotTemplateInteractor, args=())

    #: Directory of plot templates
    plot_template_directory = Property(Directory)

    #: Set to True whenever the list of templates changes or to refresh list
    list_changed = Event

    # Public interface --------------------------------------------------------

    def delete_template(self, template_name: str):
        """ Given a template name (e.g. 'ecd_time') delete the template file.

        Fires the list_changed event upon successful deletion.

        Parameters
        ----------
        template_name : Str
            Name of the template, without the file extension.
        """
        path = self.interactor.get_template_dir()
        ext = self.interactor.get_template_ext()
        filepath = os.path.join(path, template_name + ext)
        if os.path.exists(filepath):
            os.remove(filepath)
            self.list_changed = True

    def rescan_template_dir(self):
        self.list_changed = True

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
