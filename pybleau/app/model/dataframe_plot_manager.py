import logging
import os
from collections import OrderedDict
from pathlib import Path
from typing import Optional
from uuid import UUID

import pandas as pd
from app_common.chaco.constraints_plot_container_manager import \
    ConstraintsPlotContainerManager
from app_common.model_tools.data_element import DataElement
from app_common.std_lib.logging_utils import ACTION_LEVEL
from app_common.std_lib.sys_utils import extract_traceback
from chaco.api import BasePlotContainer, HPlotContainer, \
    OverlayPlotContainer, Plot
from traits.api import Dict, Enum, Instance, Int, List, on_trait_change, \
    Property, Set, Str

from pybleau.app.model.multi_canvas_manager import MultiCanvasManager
from pybleau.app.model.plot_descriptor import CONTAINER_IDX_REMOVAL, \
    CUSTOM_PLOT_TYPE, PlotDescriptor
from pybleau.app.model.plot_template_manager import PlotTemplateManager
from pybleau.app.plotting.i_plot_template_interactor import \
    IPlotTemplateInteractor
from pybleau.app.plotting.multi_plot_config import \
    MultiHistogramPlotConfigurator, MULTI_LINE_PLOT_TYPE, \
    MultiLinePlotConfigurator
from pybleau.app.plotting.plot_config import BAR_PLOT_TYPE, \
    BarPlotConfigurator, HeatmapPlotConfigurator, LINE_PLOT_TYPE, \
    LinePlotConfigurator, SCATTER_PLOT_TYPE, ScatterPlotConfigurator, \
    BasePlotConfigurator
from pybleau.app.plotting.plot_config import BaseSinglePlotConfigurator, \
    HistogramPlotConfigurator
from pybleau.app.plotting.plot_factories import DEFAULT_FACTORIES, \
    DISCONNECTED_SELECTION_COLOR, SELECTION_COLOR, SELECTION_METADATA_NAME
from pybleau.app.plotting.template_plot_selector import \
    TemplatePlotNameSelector
from pybleau.app.utils.string_definitions import CMAP_SCATTER_PLOT_TYPE, \
    HEATMAP_PLOT_TYPE, HIST_PLOT_TYPE, MULTI_HIST_PLOT_TYPE

logger = logging.getLogger(__name__)

DATA_COLUMN_TYPES = ["Input", "Output", "Index"]

CMAP_PLOT_TYPES = [CMAP_SCATTER_PLOT_TYPE, HEATMAP_PLOT_TYPE]


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

    To enable plot template creation and usage, a template_interactor
    attribute must be passed at creation. The template_interactor must provide
    the IPlotTemplateInteractor interface, implementing how to save, load and
    delete Configurator objects/files.

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

    #: Plot template manager
    template_manager = Instance(PlotTemplateManager)

    #: Plot template interactor
    template_interactor = Instance(IPlotTemplateInteractor)

    #: OrderedDict of all user-created (custom) plot configs
    custom_configs = Property(Instance(OrderedDict, args=()),
                              depends_on="template_interactor")

    #: Combination of default and custom plot configs
    plot_configs = Property(Instance(OrderedDict, args=()),
                            depends_on="custom_configs")

    #: List of all plot types
    plot_types = Property(Instance(List), depends_on="custom_configs")

    #: Default plot type configurators
    default_configs = Dict

    def __init__(self, **traits):
        if "source_analyzer" in traits:
            traits["source_analyzer_id"] = traits["source_analyzer"].uuid
            traits["data_source"] = traits["source_analyzer"].filtered_df

        # Support passing a custom Chaco plot/container to the list of
        # contained plots:
        if "contained_plots" in traits:
            traits["contained_plots"] = self.preprocess_plot_list(
                traits["contained_plots"])

        super(DataFramePlotManager, self).__init__(**traits)

        if self.contained_plots and self.data_source is not None:
            self._create_initial_plots_from_descriptions()

        # Make sure the source analyzer and self are connected, so
        # filtered_data changes trigger data_source updates:
        if self.source_analyzer:
            if self not in self.source_analyzer.plot_manager_list:
                self.source_analyzer.plot_manager_list.append(self)

    def clear_all_plots(self):
        """ Remove all contained plots.
        """
        self.delete_plots(self.contained_plots)
        self.contained_plots = []

    def preprocess_plot_list(self, plot_list):
        """ Pre-process the list of plots so they can be embedded in manager.

        1. Expand MultiConfigurators into a list of single plot configurators.
        2. Convert Chaco containers and raw Configurators into descriptors.
        """
        from ..plotting.multi_plot_config import BaseMultiPlotConfigurator

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
            elif isinstance(desc, PlotDescriptor):
                contained_plots.append(desc)
            else:
                msg = "Unsupported object type to provided a plot in a " \
                      "DFPlotManager. Supported types are PlotDescriptor " \
                      "instances or PlotConfigurator instances but a {} was " \
                      "provided for item {}. Skipping...".format(type(desc), i)
                logger.error(msg)

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
                                       list_op="replace",
                                       initial_creation=False, **desc_attrs)
                else:
                    self._add_raw_plot(desc, position=i, list_op="replace")
            except Exception as e:
                tb = extract_traceback()
                msg = "Failed to recreate the plot number {} ({} named {}" \
                      " of '{}' vs '{}', z_col '{}').\nError was {}. " \
                      "Traceback was:\n{}"
                msg = msg.format(i, desc.plot_type, desc.plot_title,
                                 desc.x_col_name, desc.y_col_name,
                                 desc.z_col_name, e, tb)
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
        logger.log(ACTION_LEVEL, "Embedding raw plot...")

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

        initial_creation : bool
            Set to True during initial creation of a plot. Set to False when
            loading a plot from disk (either from a save file or from a
            custom template file)

        """
        if position is None:
            position = self.next_plot_id

        msg = f"Generating {config.plot_type} plot..."
        logger.log(ACTION_LEVEL, msg)

        factory = self._factory_from_config(config)
        desc = factory.generate_plot()
        plot = desc["plot"]
        if initial_creation:
            self._initialize_config_plot_ranges(config, plot)
        else:
            self._apply_style_ranges(config, plot, factory)

        desc["id"] = str(position)
        # Store the config so it be recreated...
        desc["plot_config"] = config
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
        # Collect the plot instance which holds the mappers to initialize from:
        if isinstance(plot, HPlotContainer):
            for comp in plot.components:
                if isinstance(comp, OverlayPlotContainer):
                    plot = comp
                    break

        config.plot_style.initialize_axis_ranges(plot)

    def _apply_style_ranges(self, config, plot, factory):
        """ Apply the styler's range attributes to the created plot.
        """
        style = config.plot_style

        # Override the plot by collecting the OverlayPlotContainer instance
        # which holds the axis instances to apply to:
        if isinstance(plot, HPlotContainer):
            for comp in plot.components:
                if isinstance(comp, OverlayPlotContainer):
                    plot = comp
                    break

        # Apply style range to plot's axis
        style.apply_axis_ranges(plot)

        # Align all renderers to all plot's axis
        factory.align_all_renderers(plot)

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

    def _get_custom_configs(self):
        result = OrderedDict()
        if self.template_interactor is None:
            return result
        path = self.template_interactor.get_template_dir()

        for filename in os.listdir(path):
            if filename.endswith(self.template_interactor.get_template_ext()):
                result[Path(filename).stem] = BasePlotConfigurator
        return result

    def _get_plot_configs(self):
        return OrderedDict(**self.default_configs, **self.custom_configs)

    def _get_plot_types(self):
        return list(self.plot_configs.keys())

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
        """ Change the data source: update non-frozen plots.

        We can't rebuild the plots, because they are currently inserted in the
        enable container.

        FIXME: rebuilding histogram or scatters is unnecessary when sorting DF:
         should we try to detect situations when a full rebuilding isn't
         necessary.
        """
        contained_plots = self.contained_plots
        for plot_desc in contained_plots:
            if plot_desc.frozen or plot_desc.plot is None:
                # The plot is not created yet or set to not change: skip
                continue

            # Keep a filter in sync:
            if self.source_analyzer:
                plot_desc.data_filter = self.source_analyzer.filter_exp
            else:
                plot_desc.data_filter = ""

            config = plot_desc.plot_config
            config.data_source = new_df
            factory = plot_desc.plot_factory

            # Create a new factory to see what datasets/renderers need to be
            # added/removed:
            new_factory = self._factory_from_config(config)

            new_data = new_factory.plot_data.arrays
            existing_data = factory.plot_data.arrays
            removed_datasets = set(existing_data.keys()) - set(new_data.keys())

            # Update data and existing renderers
            factory.plot_data.update_data(new_data)
            factory.update_renderers_from_data(removed=removed_datasets)

            # Add new renderers
            new_descs = []
            new_styles = []
            desc_list = new_factory.renderer_desc
            style_list = new_factory.plot_style.renderer_styles
            existing_renderers = {(desc['x'], desc['y']) for desc in
                                  factory.renderer_desc}
            for desc, style in zip(desc_list, style_list):
                if (desc['x'], desc['y']) not in existing_renderers:
                    new_descs.append(desc)
                    new_styles.append(style)

            factory.append_new_renderers(desc_list=new_descs,
                                         styles=new_styles)

    @on_trait_change("contained_plots:plot_factory:context_menu_manager:"
                     "style_edit_requested", post_init=True)
    def action_edit_style_requested(self, manager, attr_name, new):
        """ A factory requested its style to be edited. Launch dialog.
        """
        desc = self._get_desc_for_menu_manager(manager)
        desc.edit_plot_style = True

    @on_trait_change("contained_plots:plot_factory:context_menu_manager:"
                     "delete_requested", post_init=True)
    def action_delete_requested(self, manager, attr_name, new):
        """ A factory requested a plot be deleted. Launch dialog.
        """
        desc = self._get_desc_for_menu_manager(manager)
        desc.container_idx = CONTAINER_IDX_REMOVAL

    @on_trait_change("contained_plots:plot_factory:context_menu_manager:"
                     "template_requested", post_init=True)
    def action_template_requested(self, manager, attr_name, new):
        """ A plot requested a plot template be created.
        """
        interactor = self.template_interactor
        if interactor is None:
            return

        desc = self._get_desc_for_menu_manager(manager)
        template_name = self._request_template_name_with_desc(desc)
        if template_name is None:
            return

        filepath = os.path.join(interactor.get_template_dir(), template_name +
                                interactor.get_template_ext())
        saver = interactor.get_template_saver()
        try:
            saver(filepath, desc.plot_config)
        except Exception as e:
            msg = f"The {type(interactor)}'s save function is expected to " \
                  f"receive a filepath and a Configurator object to save to " \
                  f"a template file. Error was {e}"
            logger.exception(msg)
            raise ValueError(msg)

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
        # Warning: replacing an element of the contained_plot list by the same
        # element will lead to that element being in both the event's added and
        # removed lists. Therefore the need to remove only what is removed and
        # not added (back):
        removed = set(event.removed) - set(event.added)
        if removed:
            self.delete_plots(removed)

    @on_trait_change("contained_plots:visible", post_init=True)
    def show_hide_plot(self, plot_desc, attr_name, old, visible):
        key = self.canvas_manager.build_container_key(plot_desc)
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if visible:
            container.show_plot(key)
        else:
            container.hide_plot(key)

    @on_trait_change("contained_plots:plot_title", post_init=True)
    def update_plot_title(self, plot_desc, attr_name, old, new_title):
        plot = self._get_overlay_plot_cont_from_desc(plot_desc)
        plot.title.text = new_title
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        container.refresh_container()

    @on_trait_change("contained_plots:x_axis_title", post_init=True)
    def update_plot_x_title(self, plot_desc, attr_name, old, new_title):
        plot = self._get_overlay_plot_cont_from_desc(plot_desc)
        plot.x_axis.title = new_title
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        container.refresh_container()

    @on_trait_change("contained_plots:y_axis_title", post_init=True)
    def update_plot_y_title(self, plot_desc, attr_name, old, new_title):
        plot = self._get_overlay_plot_cont_from_desc(plot_desc)
        plot.y_axis.title = new_title
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        container.refresh_container()

    @on_trait_change("contained_plots:secondary_y_axis_title", post_init=True)
    def update_plot_second_y_title(self, plot_desc, attr_name, old, new_title):
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        plot = self._get_overlay_plot_cont_from_desc(plot_desc)

        if not hasattr(plot, "second_y_axis"):
            return

        plot.second_y_axis.title = new_title
        container.refresh_container()

    @on_trait_change("contained_plots:z_axis_title", post_init=True)
    def update_plot_z_title(self, plot_desc, attr_name, old, new_title):
        container = self.canvas_manager.get_container_for_plot(plot_desc)
        if plot_desc.plot_type in CMAP_PLOT_TYPES:
            # Change the plot's colorbar:
            plot_desc.plot.components[1]._axis.title = new_title
        else:
            plot_desc.plot_factory.legend.title = new_title

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

    # Private interface methods -----------------------------------------------

    def _get_desc_for_menu_manager(self, manager) -> PlotDescriptor:
        desc = None
        for desc in self.contained_plots:
            if desc.plot_factory is None:
                # Raw plot with no factory: no context menu defined for it.
                continue
            if desc.plot_factory.context_menu_manager is manager:
                break
        if desc is None:
            msg = f"Matching {type(manager)} not found in contained plots."
            logger.exception(msg=msg)
            raise RuntimeError(msg)
        return desc

    def _get_source_analyzer_id(self):
        return self.source_analyzer.uuid

    def _get_overlay_plot_cont_from_desc(self, plot_desc):
        """ Extract OverlayPlotContainer corresponding to provided descriptor.
        """
        if plot_desc.plot_type in CMAP_PLOT_TYPES:
            # Unpack it from the HPlotContainer it's in:
            return plot_desc.plot.components[0]
        else:
            return plot_desc.plot

    def _request_template_name_with_desc(self, desc: PlotDescriptor) -> \
            Optional[str]:
        """ Request the template name from the user.

        Parameters
        ----------
        desc : PlotDescriptor
            A PlotDescriptor that contains a `plot_config`

        Returns
        -------
        Optional[str]:
            If user cancels the process, returns None. If user selects a
            name or makes a new one, returns that name as a str.
        """
        options = list(self.custom_configs.keys())
        template_name = desc.plot_title
        select = TemplatePlotNameSelector(
            new_name=template_name,
            plot_types=options,
            model=self.template_manager,
        )

        basis = desc.plot_config.source_template
        if basis != "":
            if basis not in options:
                logger.warning(f'"{basis}" is a template, but does '
                               f'not exist in the current template set')
                select.new_name = basis
            else:
                select.new_name = ""
                select.selected_string = basis
                select.replace_old_template = True

        make_template = select.edit_traits(kind="livemodal")

        if not make_template.result:
            return None

        if select.replace_old_template:
            template_name = select.selected_string
        else:
            template_name = select.new_name

        return template_name

    # Traits initialization methods -------------------------------------------

    def _plot_factories_default(self):
        return DEFAULT_FACTORIES

    def _name_default(self):
        return "Data plotter"

    def _template_manager_default(self):
        return PlotTemplateManager(interactor=self.template_interactor)

    def _default_configs_default(self):
        return dict([
            (HIST_PLOT_TYPE, HistogramPlotConfigurator),
            (MULTI_HIST_PLOT_TYPE, MultiHistogramPlotConfigurator),
            (BAR_PLOT_TYPE, BarPlotConfigurator),
            (LINE_PLOT_TYPE, LinePlotConfigurator),
            (MULTI_LINE_PLOT_TYPE, MultiLinePlotConfigurator),
            (SCATTER_PLOT_TYPE, ScatterPlotConfigurator),
            (HEATMAP_PLOT_TYPE, HeatmapPlotConfigurator)
        ])


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
        msg = "Automatically embedding {} isn't supported.".format(type(plot))
        logger.exception(msg)
        raise ValueError(msg)

    return desc


def plot_from_config(config, factory_map=DEFAULT_FACTORIES):
    """ Build plot factory capable of building a plot described by config.
    """
    plot_type = config.plot_type
    plot_factory_klass = factory_map[plot_type]
    factory = plot_factory_klass(**config.to_dict())
    desc = factory.generate_plot()
    plot = desc["plot"]
    return plot, factory, desc
