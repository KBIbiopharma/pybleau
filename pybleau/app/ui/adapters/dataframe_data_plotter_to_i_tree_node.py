from traits.api import Instance, List

from app_common.traitsui.adapters.data_element_to_i_tree_node import \
    DataElementToITreeNode

from pybleau.app.model.dataframe_plot_manager import DataFramePlotManager


class DataFramePlotManagerToITreeNode(DataElementToITreeNode):
    """ Adapts a DataFramePlotManager to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any DataElement.
    """
    #: Representation of a DFPlotManager
    adaptee = Instance(DataFramePlotManager)

    #: Make the children an empty list since it has its own view class
    children = List
