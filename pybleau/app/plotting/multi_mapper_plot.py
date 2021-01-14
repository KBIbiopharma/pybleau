""" New Chaco plot container class to support OverlayPlotContainer objects that
keep handles on plot elements and support secondary y-axis.
"""
from traits.api import Bool, Instance, Int

from chaco.api import ArrayPlotData, Legend, OverlayPlotContainer, PlotAxis, \
    PlotLabel


class MultiMapperPlot(OverlayPlotContainer):
    """ Container to store renderers and std plot elements(axes, legend, ...).

    Like the chaco DataView, this is a subclass of the chaco
    OverlayPlotContainer that keeps a handle on axes and other plot elements.
    But it supports containing renderers with different mappers, is capable of
    aligning them, and supports multiple y-axes. Its additional attribute names
    are often inspired from chaco's Plot class since the goal is a more
    flexible version of that end-user level class.
    """
    # -------------------------------------------------------------------------
    # Axes
    # -------------------------------------------------------------------------

    #: The default (bottom) horizontal axis
    x_axis = Instance(PlotAxis)

    #: The default (left) vertical axis
    y_axis = Instance(PlotAxis)

    #: The secondary vertical axis
    second_y_axis = Instance(PlotAxis)

    # -------------------------------------------------------------------------
    # Other plot elements
    # -------------------------------------------------------------------------

    #: The data storage for the plot
    data = Instance(ArrayPlotData)

    #: The label displaying a title for the plot
    title = Instance(PlotLabel)

    #: The legend of the plot
    legend = Instance(Legend)

    # -------------------------------------------------------------------------
    # Appearance
    # -------------------------------------------------------------------------

    #: Background color (overrides Enable Component)
    bgcolor = "white"

    #: Padding defaults.
    padding_top = Int(50)
    padding_bottom = Int(50)
    padding_left = Int(50)
    padding_right = Int(50)

    #: Is the border visible?
    border_visible = Bool(True)
