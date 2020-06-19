""" See base class module for general documentation on factories.
"""
from traits.api import Constant
from .plot_config import LINE_PLOT_TYPE
from .base_factories import StdXYPlotFactory


class LinePlotFactory(StdXYPlotFactory):
    """ Factory to build an XY plot containing line plot.
    """
    #: Plot type as selected by user
    plot_type = Constant(LINE_PLOT_TYPE)
