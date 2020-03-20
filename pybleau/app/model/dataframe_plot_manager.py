import pandas as pd
import logging
from uuid import UUID
import numpy as np

from traits.api import Dict, Enum, Instance, Int, List, on_trait_change, \
    Property, Set, Str
from chaco.api import BasePlotContainer, HPlotContainer, Plot

from app_common.std_lib.sys_utils import extract_traceback
from app_common.chaco.constraints_plot_container_manager import \
    ConstraintsPlotContainerManager
from app_common.model_tools.data_element import DataElement

from .plot_descriptor import CONTAINER_IDX_REMOVAL, CUSTOM_PLOT_TYPE, \
    PlotDescriptor
from ..plotting.plot_config import BaseSinglePlotConfigurator
from ..plotting.plot_factories import DEFAULT_FACTORIES, \
    DISCONNECTED_SELECTION_COLOR, HistogramPlotFactory, ScatterPlotFactory, \
    SELECTION_COLOR, SELECTION_METADATA_NAME
from ..plotting.base_factories import DEFAULT_RENDERER_NAME
from ..plotting.api import HEATMAP_PLOT_TYPE
from ..model.multi_canvas_manager import MultiCanvasManager

logger = logging.getLogger(__name__)

DATA_COLUMN_TYPES = ["Input", "Output", "Index"]


class DataFramePlotManager(DataElement):
    """ Manager to create, update, reorder, hide, delete plots from DataFrame.

    It uses its :meth:`add_new_plot` method to create a Plot instance from a
    PlotConfigurator passed to the appropriate PlotFactory. The configurator
    contains all information about what data to plot and how to plot it
    (PlotStyle). A plot can be removed using :meth:`delete_plots`.

    New Plot instances are added to one of the container_managers, the list of
    which and properties is controlled by the MultiCanvasManager. Each of these
    containers is a constraints based enable canvas to display any number of
    plots. For the logic to which container a given plot is stored in if not
    specified by the user, refer to the MultiCanvasManager. In addition, for
    each plot a PlotDescriptor is created to summarize the plot, and store it
    in contained_plots.

    TODO: Add support for adding new plots (renderers) to an existing Plot.
     That will require to add a legend.
    """
    #: Analyzer this plot manager was created from
    source_analyzer = Instance("pybleau.app.model.dataframe_analyzer."
                               "DataFrameAnalyzer")

    #: Source analyzer name, to reconnect during serialization/deserialization
    source_analyzer_id = Instance(UUID)

    #: Initial data_source container to build ArrayPlotData instances from it
    data_source = Instance(pd.DataFrame)

    #: Description of the columns in data_source. Used to guess what to plot
    data_column_types = Dict(Str, Enum(DATA_COLUMN_TYPES))

    #: List of supported plot types mapped to factories to build the Plot
    plot_factories = Dict

    #: Id of the next plot. Must be incremented after use to ensure unicity
    next_plot_id = Int

    #: Canvas manager
    canvas_manager = Instance(MultiCanvasManager, ())

    #: List of active plots (may be hidden)
    contained_plots = List(PlotDescriptor)

    #: List of plots that failed to get (re)built (for error reporting)
    failed_plots = List

    #: Map of description ids to plot
    contained_plot_map = Dict

    #: Map of all inspector tools from their plot description id
    inspectors = Dict

    #: List of indices selected
    index_selected = List

    containers_in_use = Property(Set,
                                 depends_on="contained_plots:container_idx")

    def __init__(self, **traits):
        if "source_analyzer" in traits:
            traits["source_analyzer_id"] = traits["source_analyzer"].uuid
            traits["data_source"] = traits["source_analyzer"].filtered_df

        # Support passing a custom Chaco plot/container to the list of
        # contained plots:
        if "contained_plots" in traits:
            contained_plots = self.preprocess_plot_list(
                traits["contained_plots"])
            traits["contained_plots"] = contained_plots

        super(DataFramePlotManager, self).__init__(**traits)

        if self.contained_plots and self.data_source is not None:
            self._create_initial_plots_from_descriptions()

        # Make sure the source analyzer and self are connected, so
        # filtered_data changes trigger data_source updates:
        if self.source_analyzer:
            if self not in self.source_analyzer.plot_manager_list:
                self.source_analyzer.plot_manager_list.append(self)

    def preprocess_plot_list(self, plot_list):
        """ Preprocess the list of plots so they can be embeded in the manager.

        1. Expand MultiConfigurators into a list of single plot configurators.
        2. Convert Chaco containers and raw Configurators into descriptors.
        """
        from ..plotting.multi_plot_config import BaseMultiPlotConfigurator

        if not plot_list:
            return

        contained_plots = []
        for i, desc in enumerate(plot_list):
            if isinstance(desc, BasePlotContainer):
                new_desc = embed_plot_in_desc(desc)
                contained_plots.append(new_desc)
            elif isinstance(desc, BaseMultiPlotConfigurator):
                config_list = desc.to_config_list()
                contained_plots += [PlotDescriptor.from_config(x)
                                    for x in config_list]
            elif isinstance(desc, PlotDescriptor) and \
                    isinstance(desc.plot_config, BaseMultiPlotConfigurator):
                config_list = desc.plot_config.to_config_list()
                contained_plots += [PlotDescriptor.from_config(x)
                                    for x in config_list]
            elif isinstance(desc, BaseSinglePlotConfigurator):
                contained_plots.append(PlotDescriptor.from_config(desc))
            else:
                contained_plots.append(desc)

        return contained_plots

    # Public interface --------------------------------------------------------

    def add_new_plot(self, plot_type, config_or_plot, position=None, **kwargs):
        """ Create or add one or more new Plots to the canvas.

        If a configurator is provided, the plot is generated from it, and added
        to the canvas. If a CUSTOM_PLOT_TYPE type is provided, a Chaco
        container is provided as the config_or_plot instead and it is wrapped
        in a PlotDescriptor and included in the canvas directly.

        Parameters
        ----------
        plot_type : str
            Name of the type of plot to create.

        config_or_plot : PlotConfigurator or chaco Plot/Container
            Plot to add to the manager.

        position : int
            Location of the plot to add at.
        """
        if plot_type.startswith("Multi"):
            self._add_new_plots(config_or_plot, position=position, **kwargs)
        elif plot_type == CUSTOM_PLOT_TYPE:
            if isinstance(config_or_plot, PlotDescriptor):
                desc = config_or_plot
            elif isinstance(config_or_plot, BasePlotContainer):
                desc = embed_plot_in_desc(config_or_plot)
            else:
                msg = "The config_or_plot argument for the 'custom' type can" \
                      " be a Chaco container or a PlotDescriptor, but a {} " \
                      "was provided.".format(type(config_or_plot))
                logger.exception(msg)
                raise ValueError(msg)

            self._add_raw_plot(desc, position=position, **kwargs)
        else:
            self._add_new_plot(config_or_plot, position=position, **kwargs)

    def delete_plots(self, plot_descriptions, container=None):
        """ Remove a (list of) plot(s). Clean up resources.
        """
        if isinstance(plot_descriptions, PlotDescriptor):
            plot_descriptions = [plot_descriptions]

        for plot_desc in plot_descriptions:
            if plot_desc in self.contained_plots:
                self.contained_plots.remove(plot_desc)

            self.contained_plot_map.pop(plot_desc.id, None)

            self.canvas_manager.remove_plot_from_container(plot_desc,
                                                           container=container)

            if plot_desc.id in self.inspectors:
                tool, overlay = self.inspectors.pop(plot_desc.id)
                tool.on_trait_change(self._update_selection,
                                     "component.index.metadata_changed",
                                     remove=True)

    # Private interface -------------------------------------------------------

    def _create_initial_plots_from_descriptions(self):
        """ Initialize from list of plot descriptions (which gets serialized).
        """
        for i, desc in enumerate(self.contained_plots):
            try:
                # Enforce the id since it will drive what plot gets removed and
                # replaced by the updated version:
                desc.id = str(i)
                # Set/sync config data sources unless frozen
                if not desc.frozen:
                    desc.plot_config.data_source = self.data_source

                # The following attributes are only stored in the descriptors
                # so they shouldn't be lost:
                attrs = ["visible", "frozen", "data_filter", "container_idx"]
                desc_attrs = {attr: getattr(desc, attr) for attr in attrs}

                if desc.plot_config.plot_type in self.plot_factories.keys():
                    self._add_new_plot(desc.plot_config, position=i,
                                       list_op="replace", **desc_attrs)
                else:
                    self._add_raw_plot(desc, position=i, list_op="replace")
            except Exception as e:
                tb = extract_traceback()
                msg = "Failed to recreate the plot number {} ({} of '{}' vs " \
                      "'{}', z_col '{}').\nError was {}. Traceback was:\n{}"
                msg = msg.format(i, desc.plot_type, desc.x_col_name,
                                 desc.y_col_name, desc.z_col_name, e, tb)
                logger.error(msg)
                self.failed_plots.append(desc)

        if self.failed_plots:
            self.delete_plots(self.failed_plots)

    def _add_raw_plot(self, desc, position=None, list_op="insert",
                      container=None):
        """ Add descriptor holding already made plot to the canvas.

        Parameters
        ----------
        desc : PlotDescriptor
            Plot descriptor holding the (already made) plot to insert.

        position : int or None, optional
            Where to insert the first plot in the list. Leave as None to append
            it to the end of the current plot list.

        list_op : str, optional
            How to add the created description to the list of contained plots:
            'insert' in the right position (default) or 'replace' an existing
            plot?

        container : ConstraintsPlotContainerManager or None, optional
            Container to add the plot to. If left as None, it's up to the
            canvas' to select the container based on its configuration.
        """
        if position is None:
            position = self.next_plot_id

        # If a container is specified, record it in the descriptor:
        if isinstance(container, int):
            desc.container_idx = container
            container = None
        elif isinstance(container, ConstraintsPlotContainerManager):
            containers = self.canvas_manager.container_managers
            desc.container_idx = containers.index(container)

        # Store the description into a list for display in UI
        if list_op == "insert":
            self.contained_plots.insert(position, desc)
        else:
            self.contained_plots[position] = desc

        # ...and into a dict for quick access:
        self.contained_plot_map[desc.id] = desc

        self.canvas_manager.add_plot_to_container(desc, position,
                                                  container=container)
        self.next_plot_id += 1
        return

    def _add_new_plot(self, config, position=None, list_op="insert",
                      container=None, initial_creation=True, **desc_traits):
        """ Build a new plot and add to the list of plots.

        Parameters
        ----------
        config : PlotConfigurator
            Configuration object used to describe the plot to create.

        position : int or None, optional
            Where to insert the first plot in the list. Leave as None to append
            it to the end of the current plot list.

        list_op : str, optional
            How to add the created description to the list of contained plots:
            'insert' in the right position (default) or 'replace' an existing
            plot?

        desc_traits : dict, optional
            Descriptor traits to override.

        container : ConstraintsPlotContainerManager or None, optional
            Container to add the plot to. If left as None, it's up to the
            canvas' to select the container based on its configuration.
        """
        if position is None:
            position = self.next_plot_id

        factory = self._factory_from_config(config)
        plot, desc = factory.generate_plot()
        if initial_creation:
            self._initialize_config_plot_ranges(config, plot)
        else:
            self._apply_config_plot_ranges(config, plot)

        desc["id"] = str(position)
        # Store the config so it be recreated...
        desc["plot_config"] = config
        desc["plot_factory"] = factory
        if self.source_analyzer:
            desc["data_filter"] = self.source_analyzer.filter_exp
        else:
            desc["data_filter"] = ""

        # If a container is specified, record it in the descriptor:
        if isinstance(container, int):
            desc["container_idx"] = container
            container = None
        elif isinstance(container, ConstraintsPlotContainerManager):
            containers = self.canvas_manager.container_managers
            desc["container_idx"] = containers.index(container)

        desc.update(desc_traits)
        desc = PlotDescriptor(**desc)

        # Store the description into a list for display in UI
        if list_op == "insert":
            self.contained_plots.insert(position, desc)
        else:
            self.contained_plots[position] = desc

        # ...and into a dict for quick access:
        self.contained_plot_map[desc.id] = desc

        self.canvas_manager.add_plot_to_container(desc, position,
                                                  container=container)

        if factory.inspector is not None:
            self.inspectors[desc.id] = factory.inspector

        self.next_plot_id += 1
        return desc

    def _initialize_config_plot_ranges(self, config, plot):
        """ Initialize the styler's range attributes from the created plot.
        """
        if isinstance(plot, HPlotContainer):
            for comp in plot.components:
                if isinstance(comp, Plot):
                    plot = comp
                    break

        config.plot_style.initialize_axis_ranges(plot)

    def _apply_config_plot_ranges(self, config, plot):
        """ Apply the styler's range attributes to the created plot.
        """
        style = config.plot_style
        style.apply_axis_ranges(plot)

    def _factory_from_config(self, config):
        """ Return plot factory capable of building a plot described by config.
        """
        plot_type = config.plot_type
        plot_factory_klass = self.plot_factories[plot_type]
        return plot_factory_klass(**config.to_dict())

    def _add_new_plots(self, multi_config, position=None, **kwargs):
        """ Converts request to build multiple plots into multiple requests to
        build 1.

        Parameters
        ----------
        multi_config : PlotConfigurator
            Configuration object used to describe the multiple plots to create.

        position : int or None
            Where to insert the first plot in the list. Leave as None to append
            them all to the end of the current plot list.
        """
        for i, config in enumerate(multi_config.to_config_list()):
            if position is None:
                pos = self.next_plot_id + 1
            else:
                pos = position + i

            config.plot_title = config.plot_title.format(i=pos)
            self._add_new_plot(config, position=pos, **kwargs)

    def _update_selection(self, object, name, old, new):
        """ Store the new selection and apply it to all inspectors.
        """
        selection = object.metadata[SELECTION_METADATA_NAME]
        if self.index_selected != selection:
            self.index_selected = selection

    def _set_selection_to(self, tool, selection):
        for datasource_name in ["index", "value"]:
            datasource = getattr(tool.component, datasource_name)
            datasource.metadata[SELECTION_METADATA_NAME] = selection

    # Traits property getters/setters -----------------------------------------

    def _get_containers_in_use(self):
        return {desc.container_idx for desc in self.contained_plots}

    # Traits listeners --------------------------------------------------------

    @on_trait_change("contained_plots:container_idx")
    def plot_container_changed(self, desc, _, old, new):
        """ The descriptor's container_idx was changed: move or remove.
        """
        num_containers = len(self.canvas_manager.container_managers)
        if new == CONTAINER_IDX_REMOVAL:
            # The requested container is no container: it needs to be deleted
            desc.container_idx = old
            self.delete_plots(desc, container=old)
            return
        elif new >= num_containers:
            # The requested container isn't possible: revert
            desc.container_idx = old
            return

        if old == CONTAINER_IDX_REMOVAL or old < 0 or old >= num_containers:
            # otherwise, nothing to do, value just being set
            return

        old_container = self.canvas_manager.container_managers[old]
        self.canvas_manager.remove_plot_from_container(desc,
                                                       container=old_container)

        new_container = self.canvas_manager.container_managers[new]
        # FIXME: position=None will force adding at the end of that container.
        self.canvas_manager.add_plot_to_container(desc, position=None,
                                                  container=new_container)

    def _source_analyzer_changed(self):
        self.data_source = self.source_analyzer.filtered_df

    def _data_source_changed(self, new_df):
        """ Change the data source: update plot data & descriptions as needed.

        We can't rebuild the plots, because they are currently inserted in the
        enable container.

        FIXME: rebuilding histogram or scatters is unnecessary when sorting DF:
         should we try to detect situations when a full rebuilding isn't
         necessary.
        """
        for desc in self.contained_plots:
            if desc.frozen or desc.plot is None:
                # The plot is not created yet or set to not change: skip
                continue

            if self.source_analyzer:
                desc.data_filter = self.source_analyzer.filter_exp
            else:
                desc.data_filter = ""

            config = desc.plot_config
            config.data_source = new_df
            old_factory = desc.plot_factory
            factory = self._factory_from_config(config)

            # Rebuild the factory with all the required data ------------------

            new_plotdata = factory.plot_data.arrays
            old_plotdata = desc.plot.data.arrays
            new_data_added = set(new_plotdata.keys()) - set(old_plotdata.keys())  # noqa

            # If some keys are missing in the new ArrayPlotData, set them as
            # empty arrays so their renderers update too:
            for key in set(old_plotdata.keys()) - set(new_plotdata.keys()):
                new_plotdata[key] = np.array([])

            desc.plot.data.update_data(new_plotdata)

            # If new data was added, add missing renderers --------------------

            if isinstance(factory, ScatterPlotFactory) and new_data_added:
                styles = factory.plot_style.renderer_styles
                for style, renderer_desc in zip(styles, factory.renderer_desc):
                    if renderer_desc in old_factory.renderer_desc:
                        continue

                    desc.plot.plot(
                        (renderer_desc["x"], renderer_desc["y"]),
                        type=style.renderer_type,
                        name=renderer_desc["name"], **style.to_plot_kwargs()
                    )

            # Plot type specific updates --------------------------------------

            elif isinstance(factory, HistogramPlotFactory):
                x_arr = new_df[desc.x_col_name]
                num_bins = factory.plot_style.num_bins
                _, edges = factory.build_hist_data(desc.x_col_name, x_arr,
                                                   num_bins)
                # Recompute the bar width since bin edges changed
                bar_width = factory.compute_bar_width(edges, num_bins)
                desc.plot.plots[DEFAULT_RENDERER_NAME].bar_width = bar_width

            desc.plot_factory = factory

    @on_trait_change("contained_plots:style_edited", post_init=True)
    def update_styling(self, plot_desc, attr_name, new):
        """ Styling changed: update the corresponding plot

        FIXME: this implementation involves very little code but is
         inefficient. For example, if we are just changing a renderer's
         attribute, we don't need to rebuild the entire plot. Can we find
         better?
        """
        position = self.contained_plots.index(plot_desc)
        self.contained_plots.remove(plot_desc)

        # Make sure user controllable attributes are not lost when rebuilding
        # the plot:
        desc_kw = {}
        desc_attrs = ["container_idx", "plot_title", "x_axis_title",
                      "y_axis_title", "z_axis_title", "frozen", "data_filter",
                      "visible", "id"]
        for attr in desc_attrs:
            desc_kw[attr] = getattr(plot_desc, attr)

        self._add_new_plot(plot_desc.plot_config, position=position,
                           initial_creation=False, **desc_kw)

    def _contained_plots_items_changed(self, event):
        if event.removed:
            self.delete_plots(event.removed)

    @on_trait_change("contained_plots:visible", post_init=True)
    def hide_plot(self, plot_desc, attr_name, old, visible):
        key = self.canvas_manager.build_container_key(plot_desc)
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if visible:
            container.show_plot(key)
        else:
            container.hide_plot(key)

    @on_trait_change("contained_plots:plot_title", post_init=True)
    def update_plot_title(self, plot_desc, attr_name, old, new_title):
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if plot_desc.plot_type == HEATMAP_PLOT_TYPE:
            plot = plot_desc.plot.components[0]
        else:
            plot = plot_desc.plot

        plot.title = new_title
        container.refresh_container()

    @on_trait_change("contained_plots:x_axis_title", post_init=True)
    def update_plot_x_title(self, plot_desc, attr_name, old, new_title):
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if plot_desc.plot_type == HEATMAP_PLOT_TYPE:
            plot = plot_desc.plot.components[0]
        else:
            plot = plot_desc.plot

        plot.index_axis.title = new_title
        container.refresh_container()

    @on_trait_change("contained_plots:y_axis_title", post_init=True)
    def update_plot_y_title(self, plot_desc, attr_name, old, new_title):
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if plot_desc.plot_type == HEATMAP_PLOT_TYPE:
            plot = plot_desc.plot.components[0]
        else:
            plot = plot_desc.plot

        plot.value_axis.title = new_title
        container.refresh_container()

    @on_trait_change("contained_plots:z_axis_title", post_init=True)
    def update_plot_z_title(self, plot_desc, attr_name, old, new_title):
        if plot_desc.plot_type == HEATMAP_PLOT_TYPE:
            container = self.canvas_manager.get_container_for_plot(plot_desc)
            # Change the plot's colorbar:
            plot_desc.plot.components[1]._axis.title = new_title

            container.refresh_container()

    @on_trait_change("index_selected")
    def sync_all_inspectors(self):
        """ Notify all inspector tools that selection has changed, except if
        plot is frozen.
        """
        for desc_id, inspector in self.inspectors.items():
            if self.contained_plot_map[desc_id].frozen:
                continue

            tool = inspector[0]
            current_selection = tool.component.index.metadata[
                SELECTION_METADATA_NAME
            ]
            if current_selection != self.index_selected:
                self._set_selection_to(tool, self.index_selected)

    def _inspectors_items_changed(self, event):
        for tool, _ in event.added.values():
            tool.on_trait_change(self._update_selection,
                                 "component.index.metadata_changed")
            # Initialize the selection
            tool.component.index.metadata[SELECTION_METADATA_NAME] = \
                self.index_selected

    @on_trait_change("contained_plots:frozen", post_init=True)
    def disconnect_selection(self, object, name, old, new):
        """ Since the data of frozen plots doesn't update, its selection
        listener must be turned off.
        """
        desc_id = object.id
        tool, overlay = self.inspectors[desc_id]
        attr = "component.index.metadata_changed"
        if new:
            tool.on_trait_change(self._update_selection, attr, remove=True)
            overlay.selection_color = DISCONNECTED_SELECTION_COLOR
            object.plot.request_redraw()
        else:
            tool.on_trait_change(self._update_selection, attr)
            overlay.selection_color = SELECTION_COLOR
            object.plot.request_redraw()
            self.sync_all_inspectors()

    def _get_source_analyzer_id(self):
        return self.source_analyzer.uuid

    # Traits initialization methods -------------------------------------------

    def _plot_factories_default(self):
        return DEFAULT_FACTORIES

    def _name_default(self):
        return "Data plotter"


def embed_plot_in_desc(plot):
    """ Embed chaco plot in PlotDescriptor so it can be displayed in DFPlotter.

    Parameters
    ----------
    plot : BasePlotContainer
        Chaco plot to be embedded.
    """
    if isinstance(plot, Plot):
        desc = PlotDescriptor(
            plot_type=CUSTOM_PLOT_TYPE,
            plot=plot,
            plot_config=BaseSinglePlotConfigurator(),
            plot_title=plot.title,
            x_axis_title=plot.x_axis.title,
            y_axis_title=plot.y_axis.title, frozen=True
        )
    else:
        msg = "Automatically embedding {} isn't supported. Please manually " \
              "embed the plot into a PlotDescriptor before providing as the " \
              "initial list of plots.".format(type(plot))
        logger.exception(msg)
        raise ValueError(msg)

    return desc
