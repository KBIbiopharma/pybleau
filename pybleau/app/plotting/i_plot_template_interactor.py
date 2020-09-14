from traits.api import Interface, Callable, Union


class IPlotTemplateInteractor(Interface):
    """ Interface for a plot template interactor, which provides the
    functions, directory, and extension to save/load plot template files.
    """

    def get_template_saver(self) -> Callable:
        """Returns the function required to save plot template objects.
        Function should take as arguments a `filepath` and an `object_to_save`.
        """

    def get_template_loader(self) -> Callable:
        """Returns the function required to load a plot template
        Function should take as arguments a `filepath` and return a single
        object of type `Configurator`.
        """

    def get_template_ext(self) -> str:
        """Return a string like '.ext' that the plot template files use"""

    def get_template_dir(self) -> str:
        """Return a directory object giving the location of the plot
        templates"""
