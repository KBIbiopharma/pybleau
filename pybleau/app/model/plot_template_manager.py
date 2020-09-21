import logging
import os
from pathlib import Path
from typing import Union

from traits.api import Str, List, Instance, Directory, Property, \
    HasStrictTraits

from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor

logger = logging.getLogger(__name__)


class PlotTemplateManager(HasStrictTraits):
    """ Model for the dialog used to manage plot templates
    """
    #: Names of all the available plot templates
    names = List(Str)

    #: IPlotTemplateInteractor used to save/load/locate plot templates
    interactor = Instance(IPlotTemplateInteractor, args=())

    #: Directory of plot templates
    plot_template_directory = Property(Directory)

    # Public interface --------------------------------------------------------

    def delete_templates(self, template_names: Union[list, str]):
        removed = self.interactor.delete_templates(template_names)
        if removed:
            self._update_names()

    def rescan_template_dir(self):
        self._update_names()

    # Traits property getters/setters -----------------------------------------

    def _get_names_from_directory(self):
        result = []
        if self.interactor is None:
            logger.warning("No interactor found; returning []")
            return result
        path = self.plot_template_directory
        ext = self.interactor.get_template_ext()
        for filename in os.listdir(path):
            if filename.endswith(ext):
                result.append(Path(filename).stem)
        return result

    def _get_plot_template_directory(self):
        return self.interactor.get_template_dir()

    # Traits initialization methods -------------------------------------------

    def _names_default(self):
        return self._get_names_from_directory()

    # Private Interface -------------------------------------------------------

    def _update_names(self):
        result = self._get_names_from_directory()
        self.names = result
