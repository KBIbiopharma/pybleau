
import logging

from traits.api import Dict, Enum, Instance, Int, List, Property

from app_common.chaco.constraints_plot_container_manager import \
    ConstraintsPlotContainerManager
from app_common.model_tools.data_element import DataElement

logger = logging.getLogger(__name__)

CONTAINER_TRAIT_NAME = "container_{}"

DEFAULT_NUM_CONTAINERS = 10

DEFAULT_OVERFLOW_SIZE = 4

NUM_MODES = 3


class MultiCanvasManager(DataElement):
    """ Handles multiple ConstraintsPlotContainerManager.

    Offers the ability to use multiple constraint based enable canvases and to
    specify a strategy for how to choose where to add a plot. In mode 0 or if
    there is only 1 container, all plots are added to container 0. In mode 1,
    all plots are added to the last used plot, unless it contains more than the
    overflow_limit. In that case, the plot is added to the next container if
    any. In mode 2, the container used is the one immediately after the last
    one used.
    """
    #: All plot canvases
    container_managers = List(Instance(ConstraintsPlotContainerManager))

    #: Number of available canvases
    num_container_managers = Int(DEFAULT_NUM_CONTAINERS)

    #: Type of container manager: how to lay plots out
    container_layout_type = Enum(["horizontal", "vertical"])

    #: Mode to auto-select a container: 0 -> first row, 1 -> last row (with
    # overflow), 2 -> new row
    multi_container_mode = Enum(list(range(NUM_MODES)))

    #: Number of plots beyond which to overflow to next container (mode 1 only)
    overflow_limit = Int(DEFAULT_OVERFLOW_SIZE)

    #: Number of plots for each container
    container_content = Property(Dict, depends_on="container_managers")

    # Container padding parameters --------------------------------------------

    # Outer paddings:
    padding_top = Int(0)

    padding_bottom = Int(5)

    padding_left = Int(0)

    padding_right = Int(0)

    # Padding in between plots:
    layout_spacing = Int(60)

    layout_margins = Int(60)

    def __init__(self, **traits):
        super(MultiCanvasManager, self).__init__(**traits)

        # Create a trait pointing to each of the containers so it can be
        # displayed in the DFPlotter view:
        all_containers = {}
        for i, container in enumerate(self.container_managers):
            self.add_trait(CONTAINER_TRAIT_NAME.format(i),
                           Instance(ConstraintsPlotContainerManager))
            all_containers[CONTAINER_TRAIT_NAME.format(i)] = container

        self.trait_set(**all_containers)
        self._initialize_all_managers()

    # Public interface --------------------------------------------------------

    def add_plot_to_container(self, desc, position=None, container=None):
        """ Insert the plot in the correct container.

        Parameters
        ----------
        desc : PlotDescriptor
            Descriptor of the plot to add.

        position : int or None
            Position of the plot. Leave as None to append.

        container : None or int or ConstraintsPlotContainerManager
            Container to add the plot to.
        """
        key = self.build_container_key(desc)

        if container is None:
            container = self.get_container_for_plot(desc)
        elif isinstance(container, int):
            container = self.container_managers[container]

        container.add_plot(key, desc.plot, position=position)

        # ...and hide the plot if it is supposed to be hidden
        if not desc.visible:
            container.hide_plot(key)

    def remove_plot_from_container(self, desc, container=None):
        """ Remove the plot from corresponding container.

        Parameters
        ----------
        desc : PlotDescriptor
            Descriptor of the plot to add.

        container : None or ConstraintsPlotContainerManager
            Container to add the plot to.
        """
        key = self.build_container_key(desc)

        if container is None:
            container = self.get_container_for_plot(desc)
        elif isinstance(container, int):
            container = self.container_managers[container]

        if key in container.plot_map:
            container.delete_plot(key, desc.plot)

    def get_container_for_plot(self, desc):
        """ Return the container a plot should be in.
        """
        idx = desc.container_idx
        if idx < 0:
            idx = desc.container_idx = self._get_container_idx()

        if idx < len(self.container_managers):
            return self.container_managers[idx]
        else:
            # This could happen when serializing a project, and re-opening it
            # with different preferences, where the number of containers is
            # less.
            msg = "Failed to find the requested container for {}: sending " \
                  "the plot to the last container."
            logger.info(msg)
            desc.container_idx = len(self.container_managers) - 1
            return self.container_managers[-1]

    @staticmethod
    def build_container_key(desc):
        # Isolated in a method to allow changing the mapping.
        return desc.plot_type, desc.id

    # Private interface -------------------------------------------------------

    def _initialize_all_managers(self):
        """ Create the container inside each container manager to allow plots
        to be added
        """
        for manager in self.container_managers:
            manager.init()

    def _get_container_idx(self):
        """ Compute index of container to use based on mode and current state.
        """
        if self.multi_container_mode == 0 or len(self.container_managers) == 1:
            return 0

        content = self.container_content
        used_containers = [key for key, val in content.items() if val]
        if not used_containers:
            return 0

        container_idx = max(used_containers)
        if self.multi_container_mode == 1:
            if content[container_idx] >= self.overflow_limit:
                container_idx += 1
        elif self.multi_container_mode == 2:
            container_idx += 1
        else:
            msg = "Multi-container mode {} not supported."
            msg = msg.format(self.multi_container_mode)
            logger.exception(msg)
            raise NotImplementedError(msg)

        if container_idx == len(self.container_managers):
            container_idx -= 1

        return container_idx

    # Traits listeners --------------------------------------------------------

    def _num_container_managers_changed(self):
        self.container_managers = self._container_managers_default()
        self._initialize_all_managers()

    # Traits property getters/setters -----------------------------------------

    def _get_container_content(self):
        counts = {}
        for i, container in enumerate(self.container_managers):
            counts[i] = len(container.plot_map)

        return counts

    # Traits initialization methods -------------------------------------------

    def _container_managers_default(self):
        managers = [ConstraintsPlotContainerManager(
            layout_type=self.container_layout_type,
            padding_top=self.padding_top,
            padding_bottom=self.padding_bottom,
            padding_left=self.padding_left,
            padding_right=self.padding_right,
            layout_spacing=self.layout_spacing,
            layout_margins=self.layout_margins
        ) for _ in range(self.num_container_managers)]

        return managers
