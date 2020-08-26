from traits.api import Interface, Directory, Callable


class IPlotTemplateInteractor(Interface):
    """ Interface for a plot template interactor, which provides the
    functions, directory, and extension to save/load plot template files.
    """
    def get_template_saver(self) -> Callable:
        """Returns the function required to save plot template objects"""

    def get_template_loader(self) -> Callable:
        """Returns the function required to load a plot template"""

    def get_template_ext(self) -> str:
        """Return a string like '.ext' that the plot template files use"""

    def get_template_dir(self) -> Directory:
        """Return a directory object giving the location of the plot
        templates"""
