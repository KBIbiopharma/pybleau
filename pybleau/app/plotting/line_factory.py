""" See base class module for general documentation on factories.
"""
from __future__ import print_function, division

import logging

from traits.api import Constant
from .plot_config import LINE_PLOT_TYPE
from .base_factories import StdXYPlotFactory

BAR_SQUEEZE_FACTOR = 0.8

ERROR_BAR_COLOR = "black"

ERROR_BAR_DATA_KEY_PREFIX = "__error_"

logger = logging.getLogger(__name__)


class LinePlotFactory(StdXYPlotFactory):
    """ Factory to build a line plot.
    """
    #: Plot type as used by Plot.plot
    plot_type_name = Constant("line")

    #: Plot type as selected by user
    plot_type = Constant(LINE_PLOT_TYPE)

    def _plot_tools_default(self):
        return {"zoom", "pan", "legend"}
